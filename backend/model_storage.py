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
    
    Args:
        obj_path: Path to OBJ file
        model_id: Model ID for naming output file
    
    Returns:
        Path to created PLY file
    """
    ply_path = UPLOAD_DIR / f"{model_id}.ply"
    
    try:
        # Try reading as mesh first
        mesh = o3d.io.read_triangle_mesh(obj_path)
        
        if len(mesh.vertices) > 0:
            # Save as PLY mesh
            o3d.io.write_triangle_mesh(str(ply_path), mesh)
        else:
            # Try as point cloud
            pcd = o3d.io.read_point_cloud(obj_path)
            if len(pcd.points) > 0:
                o3d.io.write_point_cloud(str(ply_path), pcd)
            else:
                raise ValueError("OBJ file contains no vertices or points")
        
        return ply_path
        
    except Exception as e:
        raise ValueError(f"Failed to convert OBJ to PLY: {str(e)}")


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
