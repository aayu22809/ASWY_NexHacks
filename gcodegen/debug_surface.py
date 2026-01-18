#!/usr/bin/env python3
"""
Debug script to visualize what SurfaceModel is actually creating
"""

import numpy as np
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from main import HandModelLoader, SurfaceModel

try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    OPEN3D_AVAILABLE = False
    print("[WARN] open3d not available")

try:
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def visualize_surface_model():
    """Load hand and show what SurfaceModel creates"""
    
    print("=" * 70)
    print("DEBUGGING SURFACE MODEL")
    print("=" * 70)
    
    # Load hand model
    print("\n[1] Loading hand model...")
    hand_points = HandModelLoader.load_hand_mesh("Rigged Hand1.obj", samples=8000)
    print(f"  Loaded {len(hand_points)} points")
    print(f"  Original bounds: X[{hand_points[:, 0].min():.1f}, {hand_points[:, 0].max():.1f}], "
          f"Y[{hand_points[:, 1].min():.1f}, {hand_points[:, 1].max():.1f}], "
          f"Z[{hand_points[:, 1].min():.1f}, {hand_points[:, 2].max():.1f}]")
    
    # Create surface model
    print("\n[2] Creating SurfaceModel...")
    surface = SurfaceModel(hand_points, "Hand Model")
    
    # Sample points from the RBF interpolator
    print("\n[3] Sampling from RBF interpolator...")
    x_min, x_max = hand_points[:, 0].min(), hand_points[:, 0].max()
    z_min, z_max = hand_points[:, 2].min(), hand_points[:, 2].max()
    
    # Create a grid
    x_samples = np.linspace(x_min, x_max, 50)
    z_samples = np.linspace(z_min, z_max, 50)
    X_grid, Z_grid = np.meshgrid(x_samples, z_samples)
    
    # Get interpolated Y values
    Y_interpolated = np.zeros_like(X_grid)
    for i in range(X_grid.shape[0]):
        for j in range(X_grid.shape[1]):
            try:
                Y_interpolated[i, j] = surface.get_height(X_grid[i, j], Z_grid[i, j])
            except:
                Y_interpolated[i, j] = np.nan
    
    # Create interpolated points
    interpolated_points = []
    for i in range(X_grid.shape[0]):
        for j in range(X_grid.shape[1]):
            if not np.isnan(Y_interpolated[i, j]):
                interpolated_points.append([X_grid[i, j], Y_interpolated[i, j], Z_grid[i, j]])
    interpolated_points = np.array(interpolated_points)
    
    print(f"  Interpolated {len(interpolated_points)} points")
    
    # Visualize
    if OPEN3D_AVAILABLE:
        print("\n[4] Visualizing with Open3D...")
        
        # Original points
        pcd_original = o3d.geometry.PointCloud()
        pcd_original.points = o3d.utility.Vector3dVector(hand_points)
        pcd_original.paint_uniform_color([1, 0, 0])  # Red
        
        # Interpolated points
        pcd_interpolated = o3d.geometry.PointCloud()
        pcd_interpolated.points = o3d.utility.Vector3dVector(interpolated_points)
        pcd_interpolated.paint_uniform_color([0, 0, 1])  # Blue
        
        print("\n  Red = Original hand points")
        print("  Blue = RBF interpolated surface")
        print("  Close window to exit")
        
        o3d.visualization.draw_geometries([pcd_original, pcd_interpolated],
                                          window_name="Surface Model Debug",
                                          width=1024, height=768)
    
    if MATPLOTLIB_AVAILABLE:
        print("\n[4] Visualizing with matplotlib...")
        fig = plt.figure(figsize=(15, 5))
        
        # Original points
        ax1 = fig.add_subplot(131, projection='3d')
        ax1.scatter(hand_points[:, 0], hand_points[:, 1], hand_points[:, 2], 
                   c='red', s=1, alpha=0.5, label='Original')
        ax1.set_title('Original Hand Points')
        ax1.set_xlabel('X')
        ax1.set_ylabel('Y')
        ax1.set_zlabel('Z')
        
        # Interpolated surface
        ax2 = fig.add_subplot(132, projection='3d')
        ax2.scatter(interpolated_points[:, 0], interpolated_points[:, 1], interpolated_points[:, 2],
                   c='blue', s=1, alpha=0.5, label='Interpolated')
        ax2.set_title('RBF Interpolated Surface')
        ax2.set_xlabel('X')
        ax2.set_ylabel('Y')
        ax2.set_zlabel('Z')
        
        # Side by side
        ax3 = fig.add_subplot(133, projection='3d')
        ax3.scatter(hand_points[:, 0], hand_points[:, 1], hand_points[:, 2], 
                   c='red', s=1, alpha=0.3, label='Original')
        ax3.scatter(interpolated_points[:, 0], interpolated_points[:, 1], interpolated_points[:, 2],
                   c='blue', s=1, alpha=0.3, label='Interpolated')
        ax3.set_title('Comparison')
        ax3.set_xlabel('X')
        ax3.set_ylabel('Y')
        ax3.set_zlabel('Z')
        ax3.legend()
        
        plt.tight_layout()
        plt.show()
    
    print("\n" + "=" * 70)
    print("Analysis:")
    print("=" * 70)
    print("The RBF interpolator assumes y = f(x, z), meaning for each (x, z)")
    print("there is only ONE y value. But a hand is a 3D object with multiple")
    print("y values at the same (x, z) position (top and bottom of hand).")
    print("\nThis is why the surface doesn't look like a hand!")
    print("=" * 70)


if __name__ == "__main__":
    visualize_surface_model()
