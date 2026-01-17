"""Raster toolpath generation for plasma jet path planning."""

import numpy as np
from typing import List
from .surface_model import SurfaceModel, ToolpathConfig, ToolpathPoint


class RasterGenerator:
    """Generate raster toolpath for plasma jet treatment."""
    
    def __init__(self, surface: SurfaceModel, config: ToolpathConfig):
        self.surface = surface
        self.config = config
        
        points = surface.points
        self.min_bounds = points.min(axis=0)
        self.max_bounds = points.max(axis=0)
    
    def generate(self) -> List[ToolpathPoint]:
        """
        Generate a raster (zigzag) toolpath over the surface.
        
        Returns:
            List of ToolpathPoint objects representing the complete toolpath
        """
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
                
                # Ensure normal points upward
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
            
            # Bidirectional raster: reverse every other line
            if self.config.use_bidirectional and line_idx % 2 == 1:
                line_points.reverse()
            
            # Add rapid move to start of line
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


def test_surface(surface_points, surface_name, save_results=True):
    """
    Test toolpath generation on a surface.
    
    Args:
        surface_points: Numpy array of 3D points
        surface_name: Name identifier for the surface
        save_results: Whether to save results to files
    
    Returns:
        Tuple of (surface, toolpath, config)
    """
    from ..utils.file_io import ResultsManager
    
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

