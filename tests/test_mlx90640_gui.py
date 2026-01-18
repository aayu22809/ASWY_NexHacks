#!/usr/bin/env python3
"""
MLX90640 Thermal Camera GUI Test Script

Hardware Connections:
- VCC → Pi 3.3V (Pin 1)
- GND → Pi GND (Pin 6)
- SDA → Pi SDA1 (GPIO2, Pin 3)
- SCL → Pi SCL1 (GPIO3, Pin 5)

This script tests the MLX90640 thermal camera with a graphical GUI:
- Real-time colored heatmap visualization (Jet colormap)
- Live temperature statistics overlay
- Color bar showing temperature scale
- Frame rate and elapsed time display
- Safety threshold warnings
- Runs until window is closed or Ctrl+C is pressed
"""

import sys
import time
import signal
import numpy as np
from datetime import datetime

# Add parent directory to path to import backend modules
sys.path.insert(0, '..')

try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from matplotlib.colors import Normalize
    _HAVE_MATPLOTLIB = True
except ImportError:
    _HAVE_MATPLOTLIB = False
    print("[ERROR] Matplotlib not installed. Install with: pip install matplotlib")
    sys.exit(1)

try:
    from backend.sensors.mlx90640 import MLX90640Sensor
except ImportError as e:
    print(f"[ERROR] Failed to import MLX90640Sensor: {e}")
    print("\nMake sure you're running from the project root and dependencies are installed:")
    print("  pip install adafruit-circuitpython-mlx90640 adafruit-blinka numpy matplotlib")
    sys.exit(1)


class ThermalGUITest:
    """GUI test harness for MLX90640 thermal camera."""
    
    def __init__(self):
        self.sensor = None
        self.running = True
        self.frame_count = 0
        self.start_time = None
        
        # Matplotlib figure and axes
        self.fig = None
        self.ax = None
        self.im = None
        self.cbar = None
        self.stats_text = None
        
        # Temperature data
        self.current_frame = None
        self.min_temp = None
        self.max_temp = None
        self.mean_temp = None
        
        # Register signal handler for clean exit
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n[INFO] Shutting down...")
        self.running = False
        if self.fig:
            plt.close(self.fig)
    
    def initialize(self):
        """Initialize the MLX90640 sensor and GUI."""
        print("=" * 60)
        print("MLX90640 Thermal Camera GUI Test")
        print("=" * 60)
        print("\n[INFO] Initializing sensor...")
        
        try:
            self.sensor = MLX90640Sensor()
            print("[OK] Sensor initialized successfully!")
            print(f"[INFO] I2C Address: 0x33")
            print(f"[INFO] Refresh Rate: 4 Hz")
            
            # Initialize matplotlib figure
            self.fig, self.ax = plt.subplots(figsize=(10, 7.5))
            self.fig.canvas.manager.set_window_title('MLX90640 Thermal Camera')
            
            # Create initial empty image (24x32)
            self.current_frame = np.zeros((24, 32))
            self.im = self.ax.imshow(
                self.current_frame,
                cmap='jet',
                interpolation='bilinear',
                aspect='auto',
                origin='upper'
            )
            
            # Add color bar
            self.cbar = self.fig.colorbar(self.im, ax=self.ax, label='Temperature (°C)')
            
            # Add statistics text overlay
            self.stats_text = self.ax.text(
                0.02, 0.98,
                'Initializing...',
                transform=self.ax.transAxes,
                fontsize=10,
                verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='black', alpha=0.7),
                color='white',
                family='monospace'
            )
            
            # Set labels and title
            self.ax.set_xlabel('Width (32 pixels)', fontsize=10)
            self.ax.set_ylabel('Height (24 pixels)', fontsize=10)
            self.ax.set_title('MLX90640 Thermal Camera - Real-time Heatmap', fontsize=12, fontweight='bold')
            
            print("\n[INFO] GUI window opening... (Close window or Press Ctrl+C to stop)")
            print("-" * 60)
            
            # Small delay to let sensor stabilize
            time.sleep(0.5)
            self.start_time = time.time()
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize: {e}")
            print("\nTroubleshooting:")
            print("  1. Check I2C is enabled: sudo raspi-config → Interface Options → I2C")
            print("  2. Verify wiring connections")
            print("  3. Check sensor is powered (3.3V)")
            print("  4. Verify I2C address: sudo i2cdetect -y 1")
            print("  5. For SSH: Enable X11 forwarding with -X flag")
            return False
    
    def update_frame(self, frame):
        """Update the GUI with new thermal frame data."""
        if not self.running or self.fig is None:
            return
        
        try:
            # Reshape to 24x32
            frame_2d = frame.reshape((24, 32))
            
            # Calculate statistics
            self.min_temp = float(np.min(frame_2d))
            self.max_temp = float(np.max(frame_2d))
            self.mean_temp = float(np.mean(frame_2d))
            
            # Update image data
            self.im.set_array(frame_2d)
            
            # Update color scale to match current frame range
            self.im.set_norm(Normalize(vmin=self.min_temp, vmax=self.max_temp))
            
            # Update color bar
            if self.cbar:
                self.cbar.update_normal(self.im)
                self.cbar.set_label(f'Temperature (°C) [{self.min_temp:.1f} - {self.max_temp:.1f}]', fontsize=9)
            
            # Calculate frame rate
            self.frame_count += 1
            elapsed = time.time() - self.start_time if self.start_time else 0
            frame_rate = self.frame_count / elapsed if elapsed > 0 else 0
            
            # Build statistics text
            stats_lines = [
                f"Frame: #{self.frame_count}",
                f"Time: {datetime.now().strftime('%H:%M:%S')}",
                "",
                f"Min:  {self.min_temp:6.2f} °C",
                f"Max:  {self.max_temp:6.2f} °C",
                f"Mean: {self.mean_temp:6.2f} °C",
                f"Range: {self.max_temp - self.min_temp:6.2f} °C",
                "",
                f"Rate: {frame_rate:.2f} Hz",
                f"Elapsed: {elapsed:.1f} s"
            ]
            
            # Add warning if temperature is high
            if self.max_temp > 40.0:
                stats_lines.append("")
                stats_lines.append("⚠️  WARNING: Temp > 40°C")
            elif self.max_temp > 38.0:
                stats_lines.append("")
                stats_lines.append("⚠️  Approaching threshold")
            
            self.stats_text.set_text('\n'.join(stats_lines))
            
            # Redraw
            self.fig.canvas.draw_idle()
            
        except Exception as e:
            print(f"[ERROR] Failed to update frame: {e}")
    
    def animate(self, frame_num):
        """Animation callback for matplotlib FuncAnimation."""
        if not self.running:
            return
        
        try:
            # Read thermal frame
            frame_flat = self.sensor.read_frame()
            self.update_frame(frame_flat)
            
        except Exception as e:
            print(f"[ERROR] Failed to read frame: {e}")
            # Continue trying
    
    def run(self):
        """Main test loop."""
        if not self.initialize():
            return
        
        try:
            # Use FuncAnimation for real-time updates
            # Interval in milliseconds (250ms = 4 Hz)
            self.ani = animation.FuncAnimation(
                self.fig,
                self.animate,
                interval=250,  # 4 Hz refresh rate
                blit=False,
                cache_frame_data=False
            )
            
            # Show GUI (blocks until window is closed)
            plt.tight_layout()
            plt.show()
            
        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"[ERROR] GUI error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources."""
        self.running = False
        
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
        
        if self.fig:
            try:
                plt.close(self.fig)
            except Exception:
                pass
        
        print("\n[INFO] Test completed!")


def main():
    """Main entry point."""
    if not _HAVE_MATPLOTLIB:
        print("[ERROR] Matplotlib is required for GUI visualization.")
        print("Install with: pip install matplotlib")
        sys.exit(1)
    
    test = ThermalGUITest()
    test.run()


if __name__ == "__main__":
    main()
