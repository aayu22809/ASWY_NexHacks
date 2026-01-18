"""MLX90640 thermal camera driver (32x24 array)."""

import numpy as np
from typing import Optional

try:
    import board
    import busio
    import adafruit_mlx90640
    _HAVE_MLX = True
except ImportError:
    board = None
    busio = None
    adafruit_mlx90640 = None
    _HAVE_MLX = False

from backend.config import MLX90640_I2C_ADDRESS


class MLX90640Sensor:
    """Driver for MLX90640 32x24 thermal array sensor."""
    
    def __init__(self, i2c_address: int = MLX90640_I2C_ADDRESS):
        """
        Initialize MLX90640 sensor.
        
        Args:
            i2c_address: I2C address (default 0x33 for MLX90640)
        """
        if not _HAVE_MLX:
            raise ImportError(
                "MLX90640 libraries not available. Install with: "
                "pip install adafruit-circuitpython-mlx90640 adafruit-blinka"
            )
        
        try:
            # Create I2C bus
            i2c = board.I2C()
            
            # Initialize MLX90640
            self._mlx = adafruit_mlx90640.MLX90640(i2c, address=i2c_address)
            
            # Set refresh rate (0-7, where 7 is fastest ~64Hz)
            # 2Hz refresh rate = setting 3
            self._mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
            
            print(f"[OK] MLX90640 initialized at address {hex(i2c_address)}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize MLX90640: {e}")
    
    def read_frame(self) -> np.ndarray:
        """
        Read a complete thermal frame.
        
        Returns:
            768-element numpy array (32x24 temperatures in Celsius)
            Shape: (768,) - can be reshaped to (24, 32) for visualization
        """
        try:
            frame = np.zeros((24 * 32,))
            self._mlx.getFrame(frame)
            
            # Reshape to 24x32 (height x width)
            frame_2d = frame.reshape((24, 32))
            
            return frame_2d.flatten()  # Return as flat array for JSON serialization
            
        except Exception as e:
            raise RuntimeError(f"Failed to read MLX90640 frame: {e}")
    
    def get_max_temp(self) -> float:
        """
        Get the maximum temperature in the current frame.
        
        Returns:
            Maximum temperature in Celsius
        """
        frame = self.read_frame()
        return float(np.max(frame))
    
    def get_min_temp(self) -> float:
        """
        Get the minimum temperature in the current frame.
        
        Returns:
            Minimum temperature in Celsius
        """
        frame = self.read_frame()
        return float(np.min(frame))
    
    def get_mean_temp(self) -> float:
        """
        Get the mean temperature in the current frame.
        
        Returns:
            Mean temperature in Celsius
        """
        frame = self.read_frame()
        return float(np.mean(frame))
    
    def close(self):
        """Cleanup resources."""
        # MLX90640 doesn't need explicit cleanup, but we can mark it
        self._mlx = None
