import numpy as np
from scipy.interpolate import RBFInterpolator
from scipy.spatial.distance import cdist
from dataclasses import dataclass
from typing import List
import json
import pickle
import os
from datetime import datetime
import urllib.request
import tempfile

try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    OPEN3D_AVAILABLE = False
    print("[WARN] open3d not available. Install with: pip install open3d")

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


class HandModelLoader:
    """Load hand model from mesh file"""
    
    @staticmethod
    def download_hand_model(output_path="hand_model.obj"):
        """Download a free hand model if it doesn't exist"""
        if os.path.exists(output_path):
            print(f"  Hand model already exists: {output_path}")
            return output_path
        
        print(f"  Downloading hand model...")
        # Using a simple hand model from a public repository
        # This is a low-poly hand model suitable for testing
        url = "https://raw.githubusercontent.com/keeganwitt/3d-models/main/hand.obj"
        
        try:
            urllib.request.urlretrieve(url, output_path)
            print(f"  Downloaded hand model to: {output_path}")
            return output_path
        except Exception as e:
            print(f"  [WARN] Could not download hand model: {e}")
            print(f"  [INFO] Creating a simple hand-like shape instead...")
            # Create a simple hand-like shape programmatically
            return HandModelLoader.create_simple_hand(output_path)
    
    @staticmethod
    def create_simple_hand(output_path="hand_model.obj"):
        """Create a simple hand-like shape programmatically and save as OBJ"""
        print("  Generating simple hand-like surface...")
        
        # Generate points using the same method
        points = HandModelLoader.generate_hand_points(samples=8000)
        
        # Save as simple OBJ file (just vertices, no faces)
        with open(output_path, 'w') as f:
            f.write("# Simple hand model\n")
            f.write("# Generated programmatically\n")
            for pt in points:
                f.write(f"v {pt[0]:.6f} {pt[1]:.6f} {pt[2]:.6f}\n")
        
        print(f"  Created simple hand model: {output_path}")
        return output_path
    
    @staticmethod
    def parse_obj_file(obj_path):
        """Manually parse OBJ file to extract vertices and faces"""
        vertices = []
        faces = []
        try:
            with open(obj_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse vertex line: "v x y z"
                    if line.startswith('v ') and not line.startswith('vn ') and not line.startswith('vt '):
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                                vertices.append([x, y, z])
                            except ValueError:
                                continue
                    
                    # Parse face line: "f v1/vt1/vn1 v2/vt2/vn2 v3/vt3/vn3 [v4/vt4/vn4]"
                    elif line.startswith('f '):
                        parts = line.split()[1:]  # Skip 'f'
                        face_vertices = []
                        for part in parts:
                            # Handle format: "v", "v/vt", "v/vt/vn", or "v//vn"
                            vertex_idx = part.split('/')[0]
                            try:
                                # OBJ indices are 1-based, convert to 0-based
                                idx = int(vertex_idx) - 1
                                if 0 <= idx < len(vertices):
                                    face_vertices.append(idx)
                            except ValueError:
                                continue
                        
                        # Convert quads to triangles
                        if len(face_vertices) >= 3:
                            if len(face_vertices) == 3:
                                # Already a triangle
                                faces.append(face_vertices)
                            elif len(face_vertices) == 4:
                                # Quad: split into two triangles
                                # Triangle 1: v0, v1, v2
                                faces.append([face_vertices[0], face_vertices[1], face_vertices[2]])
                                # Triangle 2: v0, v2, v3
                                faces.append([face_vertices[0], face_vertices[2], face_vertices[3]])
                            else:
                                # Polygon with more than 4 vertices: fan triangulation
                                for i in range(1, len(face_vertices) - 1):
                                    faces.append([face_vertices[0], face_vertices[i], face_vertices[i+1]])
        except Exception as e:
            print(f"  [WARN] Error parsing OBJ file: {e}")
            import traceback
            traceback.print_exc()
        
        vertices_array = np.array(vertices) if vertices else None
        faces_array = np.array(faces, dtype=np.int32) if faces else None
        return vertices_array, faces_array
    
    @staticmethod
    def load_hand_mesh(mesh_path="Rigged Hand1.obj", samples=8000):
        """
        Load hand model from mesh file and extract point cloud
        
        Args:
            mesh_path: Path to mesh file (STL, OBJ, or PLY)
            samples: Number of points to sample from mesh surface
        
        Returns:
            numpy array of points (Nx3)
        """
        # First try manual OBJ parsing if it's an OBJ file
        if mesh_path.lower().endswith('.obj') and os.path.exists(mesh_path):
            print(f"  Parsing OBJ file manually: {mesh_path}")
            vertices, faces = HandModelLoader.parse_obj_file(mesh_path)
            
            if vertices is not None and len(vertices) > 0:
                print(f"  Extracted {len(vertices)} vertices and {len(faces) if faces is not None else 0} faces from OBJ file")
                
                # If we have open3d and faces, create mesh directly from faces
                if OPEN3D_AVAILABLE and faces is not None and len(faces) > 0:
                    try:
                        print(f"  Creating mesh from {len(faces)} triangles...")
                        # Create mesh directly from vertices and faces
                        mesh = o3d.geometry.TriangleMesh()
                        mesh.vertices = o3d.utility.Vector3dVector(vertices)
                        # Open3D expects integer indices (Vector3iVector), ensure int32
                        mesh.triangles = o3d.utility.Vector3iVector(faces.astype(np.int32))
                        
                        # Compute normals
                        mesh.compute_vertex_normals()
                        mesh.compute_triangle_normals()
                        
                        # Clean up mesh
                        mesh.remove_duplicated_vertices()
                        mesh.remove_duplicated_triangles()
                        mesh.remove_non_manifold_edges()
                        mesh.remove_degenerate_triangles()
                        
                        print(f"  Mesh created: {len(mesh.vertices)} vertices, {len(mesh.triangles)} triangles")
                        
                        # Sample points uniformly from mesh surface
                        print(f"  Sampling {samples} points from mesh surface...")
                        pcd_sampled = mesh.sample_points_uniformly(number_of_points=samples)
                        points = np.asarray(pcd_sampled.points)
                        
                    except Exception as e:
                        print(f"  [WARN] Mesh creation failed: {e}")
                        import traceback
                        traceback.print_exc()
                        print(f"  Falling back to using vertices directly...")
                        # Fallback: use vertices directly
                        points = vertices
                        if len(points) > samples:
                            indices = np.random.choice(len(points), samples, replace=False)
                            points = points[indices]
                else:
                    # No faces or no open3d, use vertices directly
                    print(f"  Using vertices directly (no faces or open3d unavailable)")
                    points = vertices
                    if len(points) > samples:
                        indices = np.random.choice(len(points), samples, replace=False)
                        points = points[indices]
                
                # Scale and center
                center = points.mean(axis=0)
                points = points - center
                max_dim = np.abs(points).max()
                if max_dim > 0:
                    # Scale to reasonable size (hand is typically ~180mm long)
                    scale_factor = 150.0 / max_dim
                    points = points * scale_factor
                
                print(f"  Processed {len(points)} points from hand model")
                print(f"  Bounds: X[{points[:, 0].min():.1f}, {points[:, 0].max():.1f}], "
                      f"Y[{points[:, 1].min():.1f}, {points[:, 1].max():.1f}], "
                      f"Z[{points[:, 2].min():.1f}, {points[:, 2].max():.1f}]")
                
                return points
        
        # Try to load from file if it exists and open3d is available
        if OPEN3D_AVAILABLE and os.path.exists(mesh_path):
            try:
                print(f"  Loading hand model from: {mesh_path}")
                
                # Try reading as triangle mesh first
                mesh = o3d.io.read_triangle_mesh(mesh_path, enable_post_processing=True)
                
                # If mesh has no triangles but has vertices, try triangulating
                if len(mesh.triangles) == 0 and len(mesh.vertices) > 0:
                    print(f"  Mesh has {len(mesh.vertices)} vertices but no triangles, attempting triangulation...")
                    # Try reading as general mesh and converting
                    try:
                        # Read using legacy format which handles quads better
                        mesh = o3d.io.read_triangle_mesh(mesh_path, enable_post_processing=False)
                        # Force triangulation
                        mesh.remove_duplicated_vertices()
                        mesh.remove_duplicated_triangles()
                        mesh.remove_non_manifold_edges()
                    except:
                        pass
                
                # Alternative: try reading point cloud directly if mesh fails
                if len(mesh.vertices) == 0:
                    print(f"  Trying alternative loading method...")
                    try:
                        # Try reading as point cloud first
                        pcd = o3d.io.read_point_cloud(mesh_path)
                        if len(pcd.points) > 0:
                            points = np.asarray(pcd.points)
                            # Scale and center
                            center = points.mean(axis=0)
                            points = points - center
                            max_dim = np.abs(points).max()
                            if max_dim > 0:
                                scale_factor = 150.0 / max_dim
                                points = points * scale_factor
                            print(f"  Loaded as point cloud: {len(points)} points")
                            return points
                    except:
                        pass
                
                if len(mesh.vertices) > 0:
                    print(f"  Mesh loaded: {len(mesh.vertices)} vertices, {len(mesh.triangles)} triangles")
                    
                    # Compute normals for better surface representation
                    if not mesh.has_vertex_normals():
                        mesh.compute_vertex_normals()
                    
                    # If we have triangles, sample from surface
                    if len(mesh.triangles) > 0:
                        # Sample points uniformly from mesh surface
                        pcd = mesh.sample_points_uniformly(number_of_points=samples)
                        points = np.asarray(pcd.points)
                    else:
                        # If no triangles, use vertices directly
                        print(f"  No triangles found, using vertices directly...")
                        points = np.asarray(mesh.vertices)
                        # Subsample if too many points
                        if len(points) > samples:
                            indices = np.random.choice(len(points), samples, replace=False)
                            points = points[indices]
                    
                    # Scale and center
                    center = points.mean(axis=0)
                    points = points - center
                    max_dim = np.abs(points).max()
                    if max_dim > 0:
                        # Scale to reasonable size (hand is typically ~180mm long)
                        scale_factor = 150.0 / max_dim
                        points = points * scale_factor
                    
                    print(f"  Extracted {len(points)} points from hand model")
                    print(f"  Bounds: X[{points[:, 0].min():.1f}, {points[:, 0].max():.1f}], "
                          f"Y[{points[:, 1].min():.1f}, {points[:, 1].max():.1f}], "
                          f"Z[{points[:, 2].min():.1f}, {points[:, 2].max():.1f}]")
                    
                    return points
                else:
                    print(f"  [WARN] Mesh file has no vertices: {mesh_path}")
            except Exception as e:
                print(f"  [WARN] Failed to load mesh file: {e}")
                import traceback
                traceback.print_exc()
                print(f"  Falling back to programmatic hand generation...")
        else:
            if not OPEN3D_AVAILABLE:
                print(f"  [WARN] open3d not available, cannot load mesh file")
            elif not os.path.exists(mesh_path):
                print(f"  [WARN] Mesh file not found: {mesh_path}")
            print(f"  Falling back to programmatic hand generation...")
        
        # If open3d is available, try to download
        if OPEN3D_AVAILABLE:
            try:
                mesh_path = HandModelLoader.download_hand_model(mesh_path)
                if os.path.exists(mesh_path):
                    mesh = o3d.io.read_triangle_mesh(mesh_path)
                    if len(mesh.vertices) > 0:
                        pcd = mesh.sample_points_uniformly(number_of_points=samples)
                        points = np.asarray(pcd.points)
                        center = points.mean(axis=0)
                        points = points - center
                        max_dim = np.abs(points).max()
                        if max_dim > 0:
                            scale_factor = 150.0 / max_dim
                            points = points * scale_factor
                        return points
            except Exception as e:
                print(f"  [WARN] Download failed: {e}")
        
        # Fallback: generate hand programmatically
        print("  Generating hand-like surface programmatically...")
        return HandModelLoader.generate_hand_points(samples)
    
    @staticmethod
    def generate_hand_points(samples=8000):
        """Generate a realistic hand-like point cloud programmatically"""
        points = []
        
        # Use structured grid for smoother, more realistic surface
        # Palm dimensions (more realistic proportions)
        palm_width = 45  # mm
        palm_length = 70  # mm
        palm_res_x = 25  # grid resolution
        palm_res_z = 35
        
        # Generate palm with structured grid
        for i in range(palm_res_x):
            for j in range(palm_res_z):
                u = i / (palm_res_x - 1) if palm_res_x > 1 else 0.5
                v = j / (palm_res_z - 1) if palm_res_z > 1 else 0.5
                
                # Palm shape: wider at base, narrower at fingers
                width_factor = 1.0 - 0.3 * v  # Narrower towards fingers
                x = (u - 0.5) * palm_width * width_factor
                z = v * palm_length
                
                # Palm has natural dome shape (higher in center, lower at edges)
                center_dist = np.sqrt((u - 0.5)**2 + (v - 0.5)**2)
                y = 3 + 4 * (1 - center_dist) * np.exp(-center_dist * 2)
                
                points.append([x, y, z])
        
        # Thumb (more realistic curved shape)
        thumb_res = 20
        thumb_base_x, thumb_base_z = -18, 20
        
        for i in range(thumb_res):
            t = i / (thumb_res - 1) if thumb_res > 1 else 0.5
            # Curved thumb - starts pointing inward, curves outward
            angle = -np.pi/2.5 + t * np.pi/2.2
            length = 30 * t
            x = thumb_base_x + length * np.cos(angle)
            z = thumb_base_z + length * np.sin(angle)
            
            # Thumb height profile
            y = 5 + t * 6 + 1.5 * np.sin(t * np.pi)
            
            # Add width (thumb is thicker at base)
            width = 3 * (1 - t * 0.5)
            for w_offset in np.linspace(-width/2, width/2, 3):
                points.append([x + w_offset, y, z])
        
        # Four fingers with realistic proportions
        finger_lengths = [50, 55, 50, 45]  # index, middle, ring, pinky
        finger_widths = [4, 4.5, 4, 3.5]
        finger_x_positions = [-10, -2, 6, 13]
        finger_z_start = 65
        
        for finger_idx in range(4):
            finger_length = finger_lengths[finger_idx]
            finger_width = finger_widths[finger_idx]
            finger_x_base = finger_x_positions[finger_idx]
            finger_res = 30  # points along finger length
            
            for i in range(finger_res):
                t = i / (finger_res - 1) if finger_res > 1 else 0.5
                z = finger_z_start + t * finger_length
                
                # Natural finger curve (slight forward curve)
                x_curve = 1.5 * np.sin(t * np.pi * 0.8)
                x = finger_x_base + x_curve
                
                # Finger height profile (tapers from base to tip)
                y_base = 4
                y_tip = 2
                y_curve = 3 * np.sin(t * np.pi * 0.6)  # Natural finger curve
                y = y_base + t * (y_tip - y_base) + y_curve
                
                # Add width (fingers are cylindrical)
                width = finger_width * (1 - t * 0.6)  # Taper towards tip
                for w_offset in np.linspace(-width/2, width/2, 3):
                    points.append([x + w_offset, y, z])
        
        # Convert to numpy array
        points = np.array(points)
        
        # Remove any duplicate or very close points for cleaner surface
        if len(points) > 1000:  # Only deduplicate if we have many points
            try:
                from scipy.spatial.distance import cdist
                # Simple deduplication: remove points that are too close
                # Sample a subset for distance calculation to avoid memory issues
                sample_indices = np.random.choice(len(points), min(2000, len(points)), replace=False)
                sample_points = points[sample_indices]
                distances = cdist(sample_points, sample_points)
                # Keep only points that are at least 0.8mm apart
                keep_mask = np.ones(len(sample_points), dtype=bool)
                for i in range(len(sample_points)):
                    if not keep_mask[i]:
                        continue
                    too_close = (distances[i] < 0.8) & (distances[i] > 0)
                    keep_mask[too_close] = False
                    keep_mask[i] = True
                points = sample_points[keep_mask]
            except Exception as e:
                print(f"  [INFO] Deduplication skipped: {e}")
                pass
        
        print(f"  Generated {len(points)} hand-like points")
        print(f"  Bounds: X[{points[:, 0].min():.1f}, {points[:, 0].max():.1f}], "
              f"Y[{points[:, 1].min():.1f}, {points[:, 1].max():.1f}], "
              f"Z[{points[:, 2].min():.1f}, {points[:, 2].max():.1f}]")
        
        return points


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
    
    def __init__(self, points, surface_name="surface", use_mesh_direct=False):
        self.points = points
        self.surface_name = surface_name
        # For hand models, use mesh-based lookup to preserve 3D shape
        self.use_mesh_direct = use_mesh_direct or ("hand" in surface_name.lower() or "Hand" in surface_name)
        
        if self.use_mesh_direct:
            # For 3D objects like hands, use nearest neighbor search on actual points
            print("  Building mesh-based surface model (preserves 3D shape)...")
            from scipy.spatial import cKDTree
            self.tree = cKDTree(points)
            self.points_array = points
            print("  Surface model ready! (using direct mesh lookup)")
        else:
            # For simple surfaces, use RBF interpolation
            self.xz = points[:, [0, 2]]
            self.y = points[:, 1]
            print("  Building RBF interpolator...")
            smoothing = 0.5
            self.interpolator = RBFInterpolator(
                self.xz, 
                self.y,
                kernel='thin_plate_spline',
                smoothing=smoothing
            )
            print(f"  Surface model ready! (smoothing={smoothing})")
    
    def get_height(self, x, z):
        """Get Y coordinate for given X, Z - returns top surface for 3D objects"""
        if self.use_mesh_direct:
            # Find nearest points on mesh surface
            # Use a query point at the center Y to find points in the XZ plane
            y_center = self.points_array[:, 1].mean()
            query_point = np.array([x, y_center, z])
            
            # Find more neighbors to get better coverage
            k = min(50, len(self.points_array))
            distances, indices = self.tree.query(query_point, k=k)
            
            if k == 1:
                nearest_idx = indices
                return self.points_array[nearest_idx][1]
            
            # Get all candidate points
            candidates = self.points_array[indices]
            
            # Filter points that are close in XZ plane (within reasonable distance)
            xz_distances = np.sqrt((candidates[:, 0] - x)**2 + (candidates[:, 2] - z)**2)
            
            # Use points within 2x the median XZ distance (captures nearby surface)
            xz_threshold = np.median(xz_distances) * 2.5
            close_mask = xz_distances <= xz_threshold
            
            if np.any(close_mask):
                close_candidates = candidates[close_mask]
                # For hand/top surface, prefer highest Y (top of hand)
                # This ensures we get the top surface, not the bottom
                return close_candidates[:, 1].max()
            else:
                # Fallback: use the point closest in XZ plane
                best_idx = np.argmin(xz_distances)
                return candidates[best_idx][1]
        else:
            xz_query = np.column_stack([np.atleast_1d(x), np.atleast_1d(z)])
            heights = self.interpolator(xz_query)
            return heights if len(heights) > 1 else heights[0]
    
    def get_normal(self, x, z, delta=1.0):
        """Get surface normal at given X, Z"""
        if self.use_mesh_direct:
            # Get surface point
            y_surface = self.get_height(x, z)
            surface_point = np.array([x, y_surface, z])
            
            # Find nearby points to estimate normal
            k = min(20, len(self.points_array))
            distances, indices = self.tree.query(surface_point, k=k)
            
            if len(indices) < 3:
                # Fallback to default normal
                return np.array([0.0, 1.0, 0.0])
            
            # Get nearby points
            nearby_points = self.points_array[indices]
            
            # Compute normal using PCA on nearby points
            centered = nearby_points - nearby_points.mean(axis=0)
            cov = np.cov(centered.T)
            eigenvalues, eigenvectors = np.linalg.eigh(cov)
            
            # Normal is the eigenvector with smallest eigenvalue (perpendicular to surface)
            normal = eigenvectors[:, 0]
            
            # Ensure normal points upward (positive Y)
            if normal[1] < 0:
                normal = -normal
            
            normal = normal / np.linalg.norm(normal)
            return normal
        else:
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
            'use_mesh_direct': self.use_mesh_direct
        }
        
        # Only save xz/y if using RBF interpolation
        if not self.use_mesh_direct:
            data['xz'] = self.xz
            data['y'] = self.y
        
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"  Surface saved to: {filename}")
        return filename
    
    @staticmethod
    def load(filename):
        """Load surface model from file"""
        with open(filename, 'rb') as f:
            data = pickle.load(f)
        
        # Handle old format without use_mesh_direct
        use_mesh_direct = data.get('use_mesh_direct', False)
        surface = SurfaceModel(data['points'], data['surface_name'], use_mesh_direct=use_mesh_direct)
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
                try:
                    y_surface = self.surface.get_height(x_line, z_sample)
                    normal = self.surface.get_normal(x_line, z_sample)
                    
                    # Skip if normal is invalid (NaN or zero)
                    if np.any(np.isnan(normal)) or np.linalg.norm(normal) < 0.1:
                        continue
                    
                    if normal[1] < 0:
                        normal = -normal
                    
                    # Normalize normal vector
                    normal = normal / np.linalg.norm(normal)
                    
                    surface_pt = np.array([x_line, y_surface, z_sample])
                    toolpath_pt = surface_pt + normal * self.config.standoff_distance
                    
                    # Skip if point is invalid
                    if np.any(np.isnan(toolpath_pt)) or np.any(np.isinf(toolpath_pt)):
                        continue
                    
                    point = ToolpathPoint(
                        position=toolpath_pt,
                        normal=normal,
                        feed_rate=self.config.feed_rate,
                        is_rapid=False
                    )
                    line_points.append(point)
                except Exception as e:
                    # Skip invalid points
                    continue
            
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
    print("RASTER PATTERN TEST - HAND MODEL")
    print("=" * 70)
    print("\nGenerating toolpath on hand model surface.\n")
    
    # Create results directory
    os.makedirs("results", exist_ok=True)
    
    # Load hand model
    try:
        print("\n[Loading Hand Model]")
        # Try Rigged Hand1.obj first, then fallback to hand_model.obj
        hand_model_path = "Rigged Hand1.obj"
        if not os.path.exists(hand_model_path):
            hand_model_path = "hand_model.obj"
        hand_points = HandModelLoader.load_hand_mesh(hand_model_path, samples=8000)
        
        # Test on hand model
        surface, toolpath, config = test_surface(hand_points, "Hand Model", save_results=True)
        
        print("\n" + "=" * 70)
        print("HAND MODEL TEST COMPLETE! ✓")
        print("=" * 70)
        print("\nGenerated files in 'results/' directory:")
        print("  • JSON files with complete results")
        print("  • G-code files for machine control")
        print("  • CSV files for data analysis")
        print("  • Pickle files with surface models")
        print("\nNow run 'visualizer.py' to interactively view and export results.")
        print("=" * 70)
        
        return [(surface, toolpath, config)]
        
    except Exception as e:
        print(f"\n[ERROR] Failed to load hand model: {e}")
        print("\nFalling back to simulated surfaces...")
        
        # Fallback to original surfaces
        surfaces_to_test = [
            ("Gentle Curved Surface", SimpleSurfaces.gentle_curve()),
        ]
        
        results = []
        for surface_name, points in surfaces_to_test:
            surface, toolpath, config = test_surface(points, surface_name, save_results=True)
            results.append((surface, toolpath, config))
        
        return results


if __name__ == "__main__":
    main()