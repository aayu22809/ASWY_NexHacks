"""Surface modeling and representation for path planning."""

import numpy as np
from scipy.interpolate import RBFInterpolator
from dataclasses import dataclass
from typing import List
import pickle
from datetime import datetime


NOISE_GEN = False


@dataclass
class ToolpathConfig:
    """Configuration parameters for toolpath generation."""
    standoff_distance: float = 5.0
    line_spacing: float = 3.0
    feed_rate: float = 50.0
    rapid_rate: float = 200.0
    use_bidirectional: bool = True
    points_per_line: int = 80
    name: str = "default"


@dataclass
class ToolpathPoint:
    """Represents a single point in the toolpath."""
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
    """Smooth surface representation using RBF interpolation."""
    
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
        """Get surface height at given (x, z) coordinates."""
        xz_query = np.column_stack([np.atleast_1d(x), np.atleast_1d(z)])
        heights = self.interpolator(xz_query)
        return heights if len(heights) > 1 else heights[0]
    
    def get_normal(self, x, z, delta=1.0):
        """Calculate surface normal at given (x, z) coordinates."""
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
            filename = f"data/surfaces/surface_{self.surface_name}_{timestamp}.pkl"
        
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

