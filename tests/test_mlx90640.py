#!/usr/bin/env python3
"""
MLX90640 Thermal Camera Test Script

Hardware Connections:
- VCC → Pi 3.3V (Pin 1)
- GND → Pi GND (Pin 6)
- SDA → Pi SDA1 (GPIO2, Pin 3)
- SCL → Pi SCL1 (GPIO3, Pin 5)

This script tests the MLX90640 thermal camera by:
- Initializing the I2C bus and sensor
- Continuously reading thermal frames
- Displaying temperature statistics (min/max/mean)
- Showing a simple ASCII heatmap visualization
- Running until Ctrl+C is pressed
"""

import sys
import time
import signal
import numpy as np
from datetime import datetime

# Add parent directory to path to import backend modules
sys.path.insert(0, '..')

try:
    from backend.sensors.mlx90640 import MLX90640Sensor
except ImportError as e:
    print(f"[ERROR] Failed to import MLX90640Sensor: {e}")
    print("\nMake sure you're running from the project root and dependencies are installed:")
    print("  pip install adafruit-circuitpython-mlx90640 adafruit-blinka numpy")
    sys.exit(1)


class ThermalTest:
    """Test harness for MLX90640 thermal camera."""
    
    def __init__(self):
        self.sensor = None
        self.running = True
        self.frame_count = 0
        self.start_time = None
        
        # Register signal handler for clean exit
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n\n[INFO] Shutting down...")
        self.running = False
    
    def initialize(self):
        """Initialize the MLX90640 sensor."""
        print("=" * 60)
        print("MLX90640 Thermal Camera Test")
        print("=" * 60)
        print("\n[INFO] Initializing sensor...")
        
        try:
            self.sensor = MLX90640Sensor()
            print("[OK] Sensor initialized successfully!")
            print(f"[INFO] I2C Address: 0x33")
            print(f"[INFO] Refresh Rate: 2 Hz")
            print("\n[INFO] Starting frame capture... (Press Ctrl+C to stop)")
            print("-" * 60)
            
            # Small delay to let sensor stabilize
            time.sleep(0.5)
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize sensor: {e}")
            print("\nTroubleshooting:")
            print("  1. Check I2C is enabled: sudo raspi-config → Interface Options → I2C")
            print("  2. Verify wiring connections")
            print("  3. Check sensor is powered (3.3V)")
            print("  4. Verify I2C address: sudo i2cdetect -y 1")
            return False
    
    def display_heatmap(self, frame_2d, min_temp, max_temp):
        """Display a simple ASCII heatmap of the thermal frame."""
        height, width = frame_2d.shape
        
        # Use a simple character gradient for visualization
        # Characters from coolest to hottest: . - : = + * # @
        chars = " .-:=+*#@"
        
        print("\nThermal Heatmap (32x24):")
        print("  " + "-" * 32)
        
        # Display every 2nd row to fit terminal (12 rows)
        for y in range(0, height, 2):
            row_str = "  "
            for x in range(width):
                temp = frame_2d[y, x]
                # Normalize temperature to character index
                if max_temp > min_temp:
                    normalized = (temp - min_temp) / (max_temp - min_temp)
                    char_idx = int(normalized * (len(chars) - 1))
                    char_idx = max(0, min(char_idx, len(chars) - 1))
                else:
                    char_idx = len(chars) // 2
                row_str += chars[char_idx]
            print(row_str)
        
        print("  " + "-" * 32)
        print("  Legend: . (coolest) → @ (hottest)")
    
    def run(self):
        """Main test loop."""
        if not self.initialize():
            return
        
        self.start_time = time.time()
        last_frame_time = time.time()
        
        try:
            while self.running:
                frame_start = time.time()
                
                # Read thermal frame
                try:
                    frame_flat = self.sensor.read_frame()
                    frame_2d = frame_flat.reshape((24, 32))
                    
                    # Calculate statistics
                    min_temp = float(np.min(frame_2d))
                    max_temp = float(np.max(frame_2d))
                    mean_temp = float(np.mean(frame_2d))
                    
                    self.frame_count += 1
                    elapsed = time.time() - self.start_time
                    frame_rate = self.frame_count / elapsed if elapsed > 0 else 0
                    
                    # Clear screen (ANSI escape code)
                    print("\033[2J\033[H", end="")
                    
                    # Display header
                    print("=" * 60)
                    print(f"MLX90640 Thermal Camera Test - Frame #{self.frame_count}")
                    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
                    print("=" * 60)
                    
                    # Display statistics
                    print(f"\nTemperature Statistics:")
                    print(f"  Min:  {min_temp:6.2f} °C")
                    print(f"  Max:  {max_temp:6.2f} °C")
                    print(f"  Mean: {mean_temp:6.2f} °C")
                    print(f"  Range: {max_temp - min_temp:6.2f} °C")
                    
                    # Display frame rate
                    print(f"\nPerformance:")
                    print(f"  Frame Rate: {frame_rate:.2f} Hz")
                    print(f"  Elapsed Time: {elapsed:.1f} s")
                    
                    # Display heatmap
                    self.display_heatmap(frame_2d, min_temp, max_temp)
                    
                    # Warning if temperature is high
                    if max_temp > 40.0:
                        print(f"\n[WARNING] Maximum temperature ({max_temp:.1f}°C) exceeds safety threshold!")
                    elif max_temp > 38.0:
                        print(f"\n[INFO] Temperature approaching threshold ({max_temp:.1f}°C)")
                    
                    print("\n" + "-" * 60)
                    print("Press Ctrl+C to stop")
                    
                    # Wait for next frame (2 Hz = 0.5s interval)
                    frame_duration = time.time() - frame_start
                    sleep_time = max(0, 0.5 - frame_duration)
                    time.sleep(sleep_time)
                    
                except Exception as e:
                    print(f"\n[ERROR] Failed to read frame: {e}")
                    print("[INFO] Retrying in 1 second...")
                    time.sleep(1)
        
        except KeyboardInterrupt:
            pass
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources."""
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        
        if self.frame_count > 0 and self.start_time:
            elapsed = time.time() - self.start_time
            avg_rate = self.frame_count / elapsed if elapsed > 0 else 0
            print(f"Total Frames Captured: {self.frame_count}")
            print(f"Total Time: {elapsed:.1f} seconds")
            print(f"Average Frame Rate: {avg_rate:.2f} Hz")
        
        if self.sensor:
            try:
                self.sensor.close()
                print("[OK] Sensor closed successfully")
            except Exception:
                pass
        
        print("\n[INFO] Test completed!")


def main():
    """Main entry point."""
    test = ThermalTest()
    test.run()


if __name__ == "__main__":
    main()
