"""Model storage and conversion utilities."""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Tuple
import open3d as o3d
import numpy as np
from datetime import datetime, timedelta

# Storage directory
UPLOAD_DIR = Path("captures/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Cleanup old files after 24 hours
CLEANUP_TTL = timedelta(hours=24)


def parse_obj_file_manual(obj_path: str):
    """
    Manually parse OBJ file to extract vertices and faces.
    This is a fallback when Open3D fails to parse certain OBJ files.
    
    Args:
        obj_path: Path to OBJ file
    
    Returns:
        Tuple of (vertices_array, faces_array) as numpy arrays
    """
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
        print(f"  [WARN] Error parsing OBJ file manually: {e}")
        import traceback
        traceback.print_exc()
    
    vertices_array = np.array(vertices) if vertices else None
    faces_array = np.array(faces, dtype=np.int32) if faces else None
    return vertices_array, faces_array


def save_uploaded_model(file_content: bytes, filename: str) -> Tuple[str, dict]:
    """
    Save uploaded model file and return model_id and metadata.
    
    Args:
        file_content: File content as bytes
        filename: Original filename
    
    Returns:
        Tuple of (model_id, metadata dict with bounds, point_count, file_path)
    """
    model_id = str(uuid.uuid4())
    file_ext = Path(filename).suffix.lower()
    
    # Save original file
    original_path = UPLOAD_DIR / f"{model_id}{file_ext}"
    with open(original_path, 'wb') as f:
        f.write(file_content)
    
    # Convert to PLY if needed
    if file_ext == '.obj':
        ply_path = convert_obj_to_ply(str(original_path), model_id)
    elif file_ext == '.ply':
        ply_path = original_path
    else:
        raise ValueError(f"Unsupported file format: {file_ext}. Only .ply and .obj are supported.")
    
    # Load PLY to get metadata
    try:
        pcd = o3d.io.read_point_cloud(str(ply_path))
        if len(pcd.points) == 0:
            # Try as mesh
            mesh = o3d.io.read_triangle_mesh(str(ply_path))
            if len(mesh.vertices) == 0:
                raise ValueError("File contains no points or vertices")
            pcd = mesh.sample_points_uniformly(number_of_points=2000)
        
        points = np.asarray(pcd.points)
        
        # Calculate bounds
        min_bounds = points.min(axis=0).tolist()
        max_bounds = points.max(axis=0).tolist()
        
        metadata = {
            'model_id': model_id,
            'filename': filename,
            'point_count': len(points),
            'bounds': {
                'x_min': float(min_bounds[0]),
                'x_max': float(max_bounds[0]),
                'y_min': float(min_bounds[1]),
                'y_max': float(max_bounds[1]),
                'z_min': float(min_bounds[2]),
                'z_max': float(max_bounds[2]),
            },
            'file_path': str(ply_path),
            'uploaded_at': datetime.now().isoformat()
        }
        
        return model_id, metadata
        
    except Exception as e:
        # Clean up on error
        if original_path.exists():
            original_path.unlink()
        if ply_path.exists() and ply_path != original_path:
            ply_path.unlink()
        raise ValueError(f"Failed to process model file: {str(e)}")


def convert_obj_to_ply(obj_path: str, model_id: str) -> Path:
    """
    Convert OBJ file to PLY format.
    Uses manual parsing as fallback when Open3D fails.
    
    Args:
        obj_path: Path to OBJ file
        model_id: Model ID for naming output file
    
    Returns:
        Path to created PLY file
    """
    ply_path = UPLOAD_DIR / f"{model_id}.ply"
    
    try:
        # Try reading as mesh first with Open3D
        mesh = o3d.io.read_triangle_mesh(obj_path, enable_post_processing=True)
        
        if len(mesh.vertices) > 0 and len(mesh.triangles) > 0:
            # Save as PLY mesh
            o3d.io.write_triangle_mesh(str(ply_path), mesh)
            return ply_path
        elif len(mesh.vertices) > 0:
            # Has vertices but no triangles - try manual parsing
            print(f"  [INFO] Open3D found {len(mesh.vertices)} vertices but no triangles, trying manual parsing...")
            vertices, faces = parse_obj_file_manual(obj_path)
            
            if vertices is not None and len(vertices) > 0:
                # Create mesh from manually parsed data
                mesh = o3d.geometry.TriangleMesh()
                mesh.vertices = o3d.utility.Vector3dVector(vertices)
                if faces is not None and len(faces) > 0:
                    mesh.triangles = o3d.utility.Vector3iVector(faces.astype(np.int32))
                    mesh.compute_vertex_normals()
                    mesh.compute_triangle_normals()
                
                # Save as PLY
                o3d.io.write_triangle_mesh(str(ply_path), mesh)
                return ply_path
            else:
                # Fallback: use vertices as point cloud
                pcd = o3d.geometry.PointCloud()
                pcd.points = o3d.utility.Vector3dVector(vertices)
                o3d.io.write_point_cloud(str(ply_path), pcd)
                return ply_path
        else:
            # Try manual parsing as fallback
            print(f"  [INFO] Open3D failed to read OBJ, trying manual parsing...")
            vertices, faces = parse_obj_file_manual(obj_path)
            
            if vertices is not None and len(vertices) > 0:
                # Create mesh from manually parsed data
                mesh = o3d.geometry.TriangleMesh()
                mesh.vertices = o3d.utility.Vector3dVector(vertices)
                if faces is not None and len(faces) > 0:
                    mesh.triangles = o3d.utility.Vector3iVector(faces.astype(np.int32))
                    mesh.compute_vertex_normals()
                    mesh.compute_triangle_normals()
                    # Save as PLY mesh
                    o3d.io.write_triangle_mesh(str(ply_path), mesh)
                else:
                    # No faces, save as point cloud
                    pcd = o3d.geometry.PointCloud()
                    pcd.points = o3d.utility.Vector3dVector(vertices)
                    o3d.io.write_point_cloud(str(ply_path), pcd)
                return ply_path
            else:
                raise ValueError("OBJ file contains no vertices or points")
        
    except Exception as e:
        # Final fallback: try manual parsing
        print(f"  [WARN] Open3D conversion failed: {e}, trying manual parsing...")
        try:
            vertices, faces = parse_obj_file_manual(obj_path)
            
            if vertices is not None and len(vertices) > 0:
                # Create mesh from manually parsed data
                mesh = o3d.geometry.TriangleMesh()
                mesh.vertices = o3d.utility.Vector3dVector(vertices)
                if faces is not None and len(faces) > 0:
                    mesh.triangles = o3d.utility.Vector3iVector(faces.astype(np.int32))
                    mesh.compute_vertex_normals()
                    mesh.compute_triangle_normals()
                    o3d.io.write_triangle_mesh(str(ply_path), mesh)
                else:
                    # No faces, save as point cloud
                    pcd = o3d.geometry.PointCloud()
                    pcd.points = o3d.utility.Vector3dVector(vertices)
                    o3d.io.write_point_cloud(str(ply_path), pcd)
                return ply_path
            else:
                raise ValueError(f"Failed to parse OBJ file: {str(e)}")
        except Exception as e2:
            raise ValueError(f"Failed to convert OBJ to PLY: {str(e)} (manual parse also failed: {str(e2)})")


def get_model(model_id: str) -> Optional[Path]:
    """
    Get path to model file (PLY format).
    
    Args:
        model_id: Model ID
    
    Returns:
        Path to PLY file, or None if not found
    """
    ply_path = UPLOAD_DIR / f"{model_id}.ply"
    if ply_path.exists():
        return ply_path
    return None


def cleanup_old_files():
    """Remove files older than CLEANUP_TTL."""
    now = datetime.now()
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file():
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            if now - file_time > CLEANUP_TTL:
                file_path.unlink()
