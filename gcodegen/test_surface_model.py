#!/usr/bin/env python3
"""Test what SurfaceModel actually produces"""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from main import HandModelLoader, SurfaceModel

try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    OPEN3D_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def test_surface_model():
    print("=" * 70)
    print("TESTING SURFACE MODEL")
    print("=" * 70)
    
    # Load hand
    print("\n[1] Loading hand model...")
    hand_points = HandModelLoader.load_hand_mesh("Rigged Hand1.obj", samples=8000)
    
    # Create surface model
    print("\n[2] Creating SurfaceModel...")
    surface = SurfaceModel(hand_points, "Hand Model")
    print(f"  Using mesh direct: {surface.use_mesh_direct}")
    
    # Sample a grid of points from the surface model
    print("\n[3] Sampling grid from SurfaceModel...")
    x_min, x_max = hand_points[:, 0].min(), hand_points[:, 0].max()
    z_min, z_max = hand_points[:, 2].min(), hand_points[:, 2].max()
    
    # Create grid
    x_samples = np.linspace(x_min, x_max, 40)
    z_samples = np.linspace(z_min, z_max, 40)
    X_grid, Z_grid = np.meshgrid(x_samples, z_samples)
    
    # Get interpolated Y values
    Y_interpolated = np.zeros_like(X_grid)
    valid_mask = np.zeros_like(X_grid, dtype=bool)
    
    print("  Querying surface model...")
    for i in range(X_grid.shape[0]):
        for j in range(X_grid.shape[1]):
            try:
                y_val = surface.get_height(X_grid[i, j], Z_grid[i, j])
                if not np.isnan(y_val) and not np.isinf(y_val):
                    Y_interpolated[i, j] = y_val
                    valid_mask[i, j] = True
            except:
                pass
    
    # Create points from grid
    grid_points = []
    for i in range(X_grid.shape[0]):
        for j in range(X_grid.shape[1]):
            if valid_mask[i, j]:
                grid_points.append([X_grid[i, j], Y_interpolated[i, j], Z_grid[i, j]])
    grid_points = np.array(grid_points)
    
    print(f"  Generated {len(grid_points)} valid points")
    
    # Visualize
    if OPEN3D_AVAILABLE:
        print("\n[4] Visualizing with Open3D...")
        
        # Original hand points
        pcd_original = o3d.geometry.PointCloud()
        pcd_original.points = o3d.utility.Vector3dVector(hand_points)
        pcd_original.paint_uniform_color([1, 0, 0])  # Red
        
        # Grid points from SurfaceModel
        pcd_grid = o3d.geometry.PointCloud()
        pcd_grid.points = o3d.utility.Vector3dVector(grid_points)
        pcd_grid.paint_uniform_color([0, 0, 1])  # Blue
        
        print("\n  Red = Original hand points")
        print("  Blue = SurfaceModel.get_height() results")
        print("  Close window to exit")
        
        o3d.visualization.draw_geometries([pcd_original, pcd_grid],
                                          window_name="Surface Model Test",
                                          width=1024, height=768)
    
    if MATPLOTLIB_AVAILABLE:
        print("\n[4] Visualizing with matplotlib...")
        fig = plt.figure(figsize=(15, 5))
        
        # Original
        ax1 = fig.add_subplot(131, projection='3d')
        ax1.scatter(hand_points[:, 0], hand_points[:, 1], hand_points[:, 2],
                   c='red', s=1, alpha=0.5)
        ax1.set_title('Original Hand Points')
        
        # SurfaceModel output
        ax2 = fig.add_subplot(132, projection='3d')
        ax2.scatter(grid_points[:, 0], grid_points[:, 1], grid_points[:, 2],
                   c='blue', s=1, alpha=0.5)
        ax2.set_title('SurfaceModel.get_height() Output')
        
        # Comparison
        ax3 = fig.add_subplot(133, projection='3d')
        ax3.scatter(hand_points[:, 0], hand_points[:, 1], hand_points[:, 2],
                   c='red', s=1, alpha=0.2, label='Original')
        ax3.scatter(grid_points[:, 0], grid_points[:, 1], grid_points[:, 2],
                   c='blue', s=1, alpha=0.5, label='SurfaceModel')
        ax3.set_title('Comparison')
        ax3.legend()
        
        plt.tight_layout()
        plt.show()
    
    print("\n" + "=" * 70)
    print("If the blue points don't look like a hand, SurfaceModel is broken.")
    print("=" * 70)


if __name__ == "__main__":
    test_surface_model()
