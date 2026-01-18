"""MLX90640 thermal camera driver (32x24 array)."""

import os
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


def _detect_platform():
    """Detect if running on Jetson or Raspberry Pi."""
    # Check for Jetson-specific files
    if os.path.exists('/proc/device-tree/model'):
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read().strip()
            if 'jetson' in model.lower() or 'orin' in model.lower():
                return 'jetson'
    # Check for Raspberry Pi
    if os.path.exists('/proc/cpuinfo'):
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'raspberry pi' in cpuinfo.lower():
                return 'raspberry_pi'
    return 'unknown'


def _get_jetson_i2c_buses():
    """Get list of available I2C buses on Jetson."""
    buses = []
    # Jetson Orin Nano typically has buses 0, 1, 7, 8
    # Bus 1 is most common (pins 3/5 on 40-pin header)
    for bus_num in [1, 8, 0, 7]:
        bus_path = f'/dev/i2c-{bus_num}'
        if os.path.exists(bus_path):
            buses.append(bus_num)
    return buses


def _create_i2c_bus_jetson():
    """Create I2C bus on Jetson with explicit bus selection."""
    try:
        from backend.config import JETSON_I2C_BUSES
        buses_to_try = JETSON_I2C_BUSES
    except ImportError:
        buses_to_try = _get_jetson_i2c_buses()
    
    # Set environment variable for Blinka to recognize Jetson
    os.environ['BLINKA_FORCEBOARD'] = 'JETSON_NX'
    
    # Blinka's board.I2C() should auto-detect Jetson I2C buses
    # We'll try to create the bus and let Blinka handle detection
    try:
        i2c = board.I2C()
        # Verify bus is working by scanning
        devices = i2c.scan()
        if devices:
            print(f"[INFO] I2C bus found with {len(devices)} device(s)")
        return i2c
    except Exception as e:
        raise RuntimeError(
            f"Failed to initialize I2C on Jetson. "
            f"Error: {e}. "
            f"Ensure I2C is enabled and sensor is connected to SDA1/SCL1 (pins 3/5). "
            f"Try: sudo i2cdetect -y 1"
        )


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
        
        # Detect platform
        platform = _detect_platform()
        self.platform = platform
        
        try:
            # Create I2C bus (platform-specific)
            if platform == 'jetson':
                i2c = _create_i2c_bus_jetson()
                print(f"[INFO] Using Jetson I2C bus")
            else:
                # Default for Raspberry Pi or unknown platforms
                i2c = board.I2C()
                if platform == 'raspberry_pi':
                    print(f"[INFO] Using Raspberry Pi I2C bus")
            
            # Initialize MLX90640
            self._mlx = adafruit_mlx90640.MLX90640(i2c, address=i2c_address)
            
            # Set refresh rate (0-7, where 7 is fastest ~64Hz)
            # 4Hz refresh rate for better real-time visualization
            self._mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ
            
            print(f"[OK] MLX90640 initialized at address {hex(i2c_address)} on {platform}")
            
            # Jetson-specific: MLX90640 requires 400kHz I2C speed
            if platform == 'jetson':
                print("[INFO] Note: Ensure I2C speed is set to 400kHz for MLX90640")
                print("[INFO] Jetson pinout: SDA→Pin 3, SCL→Pin 5 (I2C Bus 1)")
            
        except Exception as e:
            error_msg = f"Failed to initialize MLX90640: {e}"
            if platform == 'jetson':
                error_msg += (
                    "\n\nJetson troubleshooting:"
                    "\n  1. Verify I2C is enabled: sudo apt-get install i2c-tools"
                    "\n  2. Check sensor connection: sudo i2cdetect -y 1"
                    "\n  3. Ensure sensor is on I2C Bus 1 (pins 3/5)"
                    "\n  4. Verify 3.3V power and GND connections"
                    "\n  5. Check I2C speed: dmesg | grep i2c"
                )
            raise RuntimeError(error_msg)
    
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
