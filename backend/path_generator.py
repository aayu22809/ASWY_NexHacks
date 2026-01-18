"""Path generation module extracted from gcodegen for backend API."""

import numpy as np
from typing import Callable, Optional
import sys
import os

# Add parent directory to path to import from gcodegen
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import classes from gcodegen
from gcodegen.main import SurfaceModel, RasterGenerator, ToolpathConfig, ToolpathPoint


def filter_points_by_bounds(points: np.ndarray, bounds: dict) -> np.ndarray:
    """
    Filter point cloud to only include points within specified bounds.
    
    Args:
        points: Nx3 numpy array of points
        bounds: Dict with keys 'x_min', 'x_max', 'z_min', 'z_max'
    
    Returns:
        Filtered points array
    """
    mask = (
        (points[:, 0] >= bounds['x_min']) & (points[:, 0] <= bounds['x_max']) &
        (points[:, 2] >= bounds['z_min']) & (points[:, 2] <= bounds['z_max'])
    )
    return points[mask]


def generate_toolpath(
    points: np.ndarray,
    bounds: dict,
    config: dict,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> dict:
    """
    Generate toolpath from point cloud with specified bounds and config.
    
    Args:
        points: Nx3 numpy array of points (already filtered or full model)
        bounds: Dict with 'x_min', 'x_max', 'z_min', 'z_max' for path generation area
        config: Dict with toolpath configuration (standoff_distance, line_spacing, etc.)
        progress_callback: Optional callback(progress: int, status: str) for updates
    
    Returns:
        Dict with 'toolpath' (list of point dicts), 'stats' (metadata)
    """
    if progress_callback:
        progress_callback(10, "Filtering points by bounds...")
    
    # Filter points to selected bounds
    filtered_points = filter_points_by_bounds(points, bounds)
    
    if len(filtered_points) < 100:
        raise ValueError(f"Too few points in selected area: {len(filtered_points)}. Please select a larger area.")
    
    if progress_callback:
        progress_callback(30, "Building surface model...")
    
    # Create surface model
    surface_name = config.get('name', 'uploaded_model')
    surface = SurfaceModel(filtered_points, surface_name)
    
    if progress_callback:
        progress_callback(50, "Creating toolpath config...")
    
    # Create toolpath config
    toolpath_config = ToolpathConfig(
        standoff_distance=config.get('standoff_distance', 5.0),
        line_spacing=config.get('line_spacing', 3.0),
        feed_rate=config.get('feed_rate', 50.0),
        rapid_rate=config.get('rapid_rate', 200.0),
        use_bidirectional=config.get('use_bidirectional', True),
        points_per_line=config.get('points_per_line', 80),
        name=surface_name
    )
    
    if progress_callback:
        progress_callback(60, "Generating raster toolpath...")
    
    # Generate toolpath
    generator = RasterGenerator(surface, toolpath_config)
    toolpath = generator.generate()
    
    if progress_callback:
        progress_callback(90, "Finalizing results...")
    
    # Convert to serializable format
    toolpath_data = [pt.to_dict() for pt in toolpath]
    
    # Calculate stats
    treatment_points = [pt for pt in toolpath if not pt.is_rapid]
    length = sum(
        np.linalg.norm(treatment_points[i+1].position - treatment_points[i].position)
        for i in range(len(treatment_points) - 1)
    )
    
    stats = {
        'num_points': len(toolpath),
        'num_treatment_points': len(treatment_points),
        'num_rapid_points': len(toolpath) - len(treatment_points),
        'treatment_length_mm': float(length),
        'bounds': bounds,
        'config': {
            'standoff_distance': toolpath_config.standoff_distance,
            'line_spacing': toolpath_config.line_spacing,
            'feed_rate': toolpath_config.feed_rate,
            'rapid_rate': toolpath_config.rapid_rate,
            'use_bidirectional': toolpath_config.use_bidirectional,
            'points_per_line': toolpath_config.points_per_line,
        }
    }
    
    if progress_callback:
        progress_callback(100, "Complete!")
    
    return {
        'toolpath': toolpath_data,
        'stats': stats
    }
