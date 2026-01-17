import numpy as np
from scipy.interpolate import RBFInterpolator
from dataclasses import dataclass
from typing import List
import json
import pickle
import os
from datetime import datetime

NOISE_GEN = False

@dataclass
class ToolpathConfig:
    standoff_distance: float = 5.0
    line_spacing: float = 3.0
    feed_rate: float = 50.0
    rapid_rate: float = 200.0
    use_bidirectional: bool = True
    points_per_line: int = 80
    name: str = "default"


@dataclass
class ToolpathPoint:
    position: np.ndarray
    normal: np.ndarray
    feed_rate: float
    is_rapid: bool = False
    
    def to_dict(self):
        return {
            'position': self.position.tolist(),
            'normal': self.normal.tolist(),
            'feed_rate': self.feed_rate,
            'is_rapid': self.is_rapid
        }


class SimpleSurfaces:
    """Generate simple surfaces for testing"""
    
    @staticmethod
    def gentle_curve(length=150, width=100, samples=2000):
        """
        Gentle curved surface like a bent sheet of paper
        Perfect for seeing clean raster lines
        """
        print("  Creating gentle curved surface (sinusoidal wave)...")
        
        # Create regular grid
        x = np.random.uniform(-width/2, width/2, samples)
        z = np.random.uniform(0, length, samples)
        
        # Gentle sine wave in Y direction
        y = 10 * np.sin(x / 30) + 5 * np.sin(z / 40)
        
        # Very small noise for realism
        if NOISE_GEN:
            y += np.random.normal(0, 0.1, samples)
        
        points = np.column_stack([x, y, z])
        return points
    
    @staticmethod
    def cylinder(radius=40, length=150, samples=2000):
        """
        Simple cylinder (like an arm or pipe)
        """
        print("  Creating cylindrical surface...")
        
        # Only top half of cylinder (0 to π)
        theta = np.random.uniform(0, np.pi, samples)
        z = np.random.uniform(0, length, samples)
        
        x = radius * np.cos(theta)
        y = radius * np.sin(theta)
        
        # Tiny noise
        if NOISE_GEN:
            x += np.random.normal(0, 0.1, samples)
            y += np.random.normal(0, 0.1, samples)
            z += np.random.normal(0, 0.1, samples)
        
        points = np.column_stack([x, y, z])
        return points
    
    @staticmethod
    def saddle(width=100, length=150, samples=2000):
        """
        Saddle surface (hyperbolic paraboloid)
        Curves up in one direction, down in the other
        """
        print("  Creating saddle surface (doubly-curved)...")
        
        x = np.random.uniform(-width/2, width/2, samples)
        z = np.random.uniform(0, length, samples)
        
        # Saddle equation: y = x² - z²
        y = 0.01 * (x**2 - (z - length/2)**2)
        
        # Shift up so minimum is at y=0
        y = y - y.min() + 5
        
        # Tiny noise
        if NOISE_GEN:
            y += np.random.normal(0, 0.1, samples)
        
        points = np.column_stack([x, y, z])
        return points
    
    @staticmethod
    def sphere_section(radius=60, samples=2000):
        """
        Section of a sphere (highly curved)
        """
        print("  Creating spherical surface section...")
        
        # Spherical coordinates
        theta = np.random.uniform(0, np.pi*0.6, samples)  # Partial sphere
        phi = np.random.uniform(0, np.pi*0.8, samples)
        
        x = radius * np.sin(theta) * np.cos(phi)
        y = radius * np.sin(theta) * np.sin(phi)
        z = radius * np.cos(theta) + radius  # Shift to positive Z
        
        # Filter to only keep reasonable range
        mask = (z > 20) & (z < 100) & (y > 0)
        
        points = np.column_stack([x, y, z])[mask]
        
        # Add tiny noise
        if NOISE_GEN:
            points += np.random.normal(0, 0.1, points.shape)
        
        return points


class SurfaceModel:
    """Smooth surface representation"""
    
    def __init__(self, points, surface_name="surface"):
        self.points = points
        self.xz = points[:, [0, 2]]
        self.y = points[:, 1]
        self.surface_name = surface_name
        
        print("  Building RBF interpolator...")
        self.interpolator = RBFInterpolator(
            self.xz, 
            self.y,
            kernel='thin_plate_spline',
            smoothing=0.5
        )
        print("  Surface model ready!")
    
    def get_height(self, x, z):
        xz_query = np.column_stack([np.atleast_1d(x), np.atleast_1d(z)])
        heights = self.interpolator(xz_query)
        return heights if len(heights) > 1 else heights[0]
    
    def get_normal(self, x, z, delta=1.0):
        y_center = self.get_height(x, z)
        y_px = self.get_height(x + delta, z)
        y_mx = self.get_height(x - delta, z)
        y_pz = self.get_height(x, z + delta)
        y_mz = self.get_height(x, z - delta)
        
        dy_dx = (y_px - y_mx) / (2 * delta)
        dy_dz = (y_pz - y_mz) / (2 * delta)
        
        normal = np.array([-dy_dx, 1.0, -dy_dz])
        normal = normal / np.linalg.norm(normal)
        
        return normal
    
    def save(self, filename=None):
        """Save surface model to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"surface_{self.surface_name}_{timestamp}.pkl"
        
        data = {
            'points': self.points,
            'surface_name': self.surface_name,
            'xz': self.xz,
            'y': self.y
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"  Surface saved to: {filename}")
        return filename
    
    @staticmethod
    def load(filename):
        """Load surface model from file"""
        with open(filename, 'rb') as f:
            data = pickle.load(f)
        
        surface = SurfaceModel(data['points'], data['surface_name'])
        return surface


class RasterGenerator:
    """Generate raster toolpath"""
    
    def __init__(self, surface: SurfaceModel, config: ToolpathConfig):
        self.surface = surface
        self.config = config
        
        points = surface.points
        self.min_bounds = points.min(axis=0)
        self.max_bounds = points.max(axis=0)
    
    def generate(self) -> List[ToolpathPoint]:
        margin = 2.0
        x_min = self.min_bounds[0] + margin
        x_max = self.max_bounds[0] - margin
        z_min = self.min_bounds[2] + margin
        z_max = self.max_bounds[2] - margin
        
        num_lines = int((x_max - x_min) / self.config.line_spacing) + 1
        print(f"  Generating {num_lines} raster lines...")
        
        toolpath = []
        
        for line_idx in range(num_lines):
            x_line = x_min + line_idx * self.config.line_spacing
            z_samples = np.linspace(z_min, z_max, self.config.points_per_line)
            
            line_points = []
            
            for z_sample in z_samples:
                y_surface = self.surface.get_height(x_line, z_sample)
                normal = self.surface.get_normal(x_line, z_sample)
                
                if normal[1] < 0:
                    normal = -normal
                
                surface_pt = np.array([x_line, y_surface, z_sample])
                toolpath_pt = surface_pt + normal * self.config.standoff_distance
                
                point = ToolpathPoint(
                    position=toolpath_pt,
                    normal=normal,
                    feed_rate=self.config.feed_rate,
                    is_rapid=False
                )
                line_points.append(point)
            
            if self.config.use_bidirectional and line_idx % 2 == 1:
                line_points.reverse()
            
            if toolpath and line_points:
                rapid = ToolpathPoint(
                    position=line_points[0].position,
                    normal=line_points[0].normal,
                    feed_rate=self.config.rapid_rate,
                    is_rapid=True
                )
                toolpath.append(rapid)
            
            toolpath.extend(line_points)
        
        print(f"  Generated {len(toolpath)} points")
        return toolpath


class ResultsManager:
    """Manage saving and loading of results"""
    
    @staticmethod
    def save_results(surface, toolpath, config, filename=None):
        """Save complete results to a JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"results_{surface.surface_name}_{timestamp}.json"
        
        # Convert toolpath to serializable format
        toolpath_data = [pt.to_dict() for pt in toolpath]
        
        # Create results dictionary
        results = {
            'metadata': {
                'surface_name': surface.surface_name,
                'timestamp': datetime.now().isoformat(),
                'num_points': len(toolpath),
                'num_treatment_points': len([pt for pt in toolpath if not pt.is_rapid]),
                'num_rapid_points': len([pt for pt in toolpath if pt.is_rapid])
            },
            'config': {
                'standoff_distance': config.standoff_distance,
                'line_spacing': config.line_spacing,
                'feed_rate': config.feed_rate,
                'rapid_rate': config.rapid_rate,
                'use_bidirectional': config.use_bidirectional,
                'points_per_line': config.points_per_line,
                'name': config.name
            },
            'surface_bounds': {
                'min': surface.points.min(axis=0).tolist(),
                'max': surface.points.max(axis=0).tolist(),
                'center': surface.points.mean(axis=0).tolist()
            },
            'toolpath': toolpath_data,
            'surface_sample': surface.points.tolist()[:1000]  # Save subset for visualization
        }
        
        # Calculate path length
        treatment_points = [pt for pt in toolpath if not pt.is_rapid]
        length = sum(np.linalg.norm(treatment_points[i+1].position - treatment_points[i].position) 
                    for i in range(len(treatment_points)-1))
        results['metadata']['treatment_length_mm'] = float(length)
        
        # Save to JSON
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"  Results saved to: {filename}")
        return filename
    
    @staticmethod
    def load_results(filename):
        """Load results from JSON file"""
        with open(filename, 'r') as f:
            results = json.load(f)
        
        print(f"  Loaded results: {results['metadata']['surface_name']}")
        print(f"  Treatment length: {results['metadata']['treatment_length_mm']:.1f} mm")
        
        return results
    
    @staticmethod
    def export_gcode(toolpath, filename=None):
        """Export toolpath to G-code format"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"toolpath_{timestamp}.gcode"
        
        gcode_lines = [
            "; G-code generated by Raster Toolpath Generator",
            "; " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "G90 ; Absolute positioning",
            "G21 ; Millimeter units",
            "G94 ; Units per minute feed rate",
            ""
        ]
        
        # Group points by feed rate
        current_feed = None
        
        for i, point in enumerate(toolpath):
            pos = point.position
            
            # Add feed rate command if changed
            if point.feed_rate != current_feed:
                gcode_lines.append(f"F{point.feed_rate:.1f}")
                current_feed = point.feed_rate
            
            # Add movement command
            cmd = "G0" if point.is_rapid else "G1"
            line = f"{cmd} X{pos[0]:.3f} Y{pos[1]:.3f} Z{pos[2]:.3f}"
            
            # Add comment for rapid moves
            if point.is_rapid:
                line += " ; Rapid move"
            
            gcode_lines.append(line)
        
        # End program
        gcode_lines.extend([
            "",
            "M30 ; Program end"
        ])
        
        # Write file
        with open(filename, 'w') as f:
            f.write('\n'.join(gcode_lines))
        
        print(f"  G-code exported to: {filename}")
        return filename
    
    @staticmethod
    def export_csv(toolpath, filename=None):
        """Export toolpath to CSV format"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"toolpath_{timestamp}.csv"
        
        import csv
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['X', 'Y', 'Z', 'Normal_X', 'Normal_Y', 'Normal_Z', 
                           'Feed_Rate', 'Is_Rapid'])
            
            for point in toolpath:
                writer.writerow([
                    f"{point.position[0]:.6f}",
                    f"{point.position[1]:.6f}",
                    f"{point.position[2]:.6f}",
                    f"{point.normal[0]:.6f}",
                    f"{point.normal[1]:.6f}",
                    f"{point.normal[2]:.6f}",
                    f"{point.feed_rate:.2f}",
                    str(point.is_rapid)
                ])
        
        print(f"  CSV exported to: {filename}")
        return filename


def test_surface(surface_points, surface_name, save_results=True):
    """Test toolpath generation on a surface"""
    
    print(f"\n{'='*70}")
    print(f"TESTING: {surface_name}")
    print(f"{'='*70}")
    
    print(f"\n[1/3] Creating surface model...")
    surface = SurfaceModel(surface_points, surface_name)
    
    print(f"\n[2/3] Generating raster toolpath...")
    config = ToolpathConfig(
        standoff_distance=5.0,
        line_spacing=4.0,
        feed_rate=50.0,
        rapid_rate=200.0,
        use_bidirectional=True,
        points_per_line=60,
        name=surface_name
    )
    
    generator = RasterGenerator(surface, config)
    toolpath = generator.generate()
    
    if save_results:
        print(f"\n[3/3] Saving results...")
        # Save results
        results_file = ResultsManager.save_results(surface, toolpath, config)
        
        # Export to other formats
        ResultsManager.export_gcode(toolpath)
        ResultsManager.export_csv(toolpath)
        
        # Save surface model
        surface.save()
    
    # Stats
    treatment = [pt for pt in toolpath if not pt.is_rapid]
    length = sum(np.linalg.norm(treatment[i+1].position - treatment[i].position) 
                for i in range(len(treatment)-1))
    
    print(f"\n  RESULTS:")
    print(f"    Points: {len(toolpath)}")
    print(f"    Treatment length: {length:.1f} mm")
    print(f"    Raster lines: {len([pt for pt in toolpath if pt.is_rapid]) + 1}")
    
    return surface, toolpath, config


def main():
    print("=" * 70)
    print("RASTER PATTERN TEST - SIMPLE SMOOTH SURFACES")
    print("=" * 70)
    print("\nTesting toolpath generation on mathematically clean surfaces")
    print("to clearly demonstrate the raster/zig-zag pattern.\n")
    
    # Create results directory
    os.makedirs("results", exist_ok=True)
    
    # Test surfaces
    surfaces_to_test = [
        ("Gentle Curved Surface", SimpleSurfaces.gentle_curve()),
        ("Cylindrical Surface", SimpleSurfaces.cylinder()),
        ("Saddle Surface", SimpleSurfaces.saddle()),
        ("Spherical Section", SimpleSurfaces.sphere_section())
    ]
    
    results = []
    
    for surface_name, points in surfaces_to_test:
        surface, toolpath, config = test_surface(points, surface_name, save_results=True)
        results.append((surface, toolpath, config))
    
    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETE! ✓")
    print("=" * 70)
    print("\nGenerated files in 'results/' directory:")
    print("  • JSON files with complete results")
    print("  • G-code files for machine control")
    print("  • CSV files for data analysis")
    print("  • Pickle files with surface models")
    print("\nNow run 'visualizer.py' to interactively view and export results.")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    main()