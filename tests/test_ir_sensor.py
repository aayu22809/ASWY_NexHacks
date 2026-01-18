#!/usr/bin/env python3
"""
IR Reflective Obstacle Sensor Test Script

Hardware Connections:
- VCC → Pi 5V or 3.3V (check sensor specification)
- GND → Pi GND
- OUT → Pi GPIO 17 (Pin 11)

This script tests the IR reflective obstacle sensor by:
- Initializing GPIO pin 17 as input
- Continuously polling the sensor state
- Detecting state changes (CLEAR ↔ BLOCKED)
- Displaying real-time status with timestamps
- Logging events when obstacles are detected/cleared
- Running until Ctrl+C is pressed
"""

import sys
import time
import signal
from datetime import datetime

# Add parent directory to path to import backend modules
sys.path.insert(0, '..')

try:
    from backend.sensors.ir_obstacle import IRObstacleSensor
except ImportError as e:
    print(f"[ERROR] Failed to import IRObstacleSensor: {e}")
    print("\nMake sure you're running from the project root and dependencies are installed:")
    print("  For Raspberry Pi 5: sudo apt-get install python3-lgpio")
    print("  For Raspberry Pi 4/earlier: pip install RPi.GPIO")
    print("  Or use pip: pip install rpi-lgpio")
    print("\nNote: GPIO access may require root privileges or GPIO group membership")
    sys.exit(1)


class IRSensorTest:
    """Test harness for IR reflective obstacle sensor."""
    
    def __init__(self, gpio_pin=17, poll_rate=10):
        """
        Initialize test harness.
        
        Args:
            gpio_pin: GPIO pin number (default 17)
            poll_rate: Polling rate in Hz (default 10 Hz)
        """
        self.gpio_pin = gpio_pin
        self.poll_interval = 1.0 / poll_rate
        self.sensor = None
        self.running = True
        self.current_state = None
        self.state_changes = []
        self.poll_count = 0
        self.start_time = None
        
        # Register signal handler for clean exit
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n\n[INFO] Shutting down...")
        self.running = False
    
    def initialize(self):
        """Initialize the IR obstacle sensor."""
        print("=" * 60)
        print("IR Reflective Obstacle Sensor Test")
        print("=" * 60)
        print(f"\n[INFO] Initializing sensor on GPIO {self.gpio_pin}...")
        
        try:
            self.sensor = IRObstacleSensor(gpio_pin=self.gpio_pin)
            print("[OK] Sensor initialized successfully!")
            print(f"[INFO] GPIO Pin: {self.gpio_pin} (BCM numbering)")
            print(f"[INFO] Poll Rate: {1.0/self.poll_interval:.1f} Hz")
            print("\n[INFO] Starting monitoring... (Press Ctrl+C to stop)")
            print("[INFO] Wave your hand or place an object in front of the sensor")
            print("-" * 60)
            
            # Small delay to stabilize
            time.sleep(0.2)
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to initialize sensor: {e}")
            print("\nTroubleshooting:")
            print("  1. Install GPIO library:")
            print("     - For Raspberry Pi 5: sudo apt-get install python3-lgpio")
            print("     - For Raspberry Pi 4/earlier: pip install RPi.GPIO")
            print("     - Or use pip: pip install rpi-lgpio")
            print("  2. Check GPIO permissions:")
            print("     - Run with sudo: sudo python3 test_ir_sensor.py")
            print("     - Or add user to gpio group: sudo usermod -a -G gpio $USER")
            print("  3. Verify wiring connections")
            print("  4. Check sensor power supply (5V or 3.3V)")
            print("  5. Verify GPIO pin number matches your wiring")
            print("  6. Test GPIO manually: gpio readall (wiringPi) or gpioinfo")
            return False
    
    def get_status_symbol(self, is_blocked):
        """Get visual symbol for sensor state."""
        if is_blocked:
            return "✗ BLOCKED"
        else:
            return "✓ CLEAR"
    
    def get_status_color_code(self, is_blocked):
        """Get ANSI color code for status."""
        if is_blocked:
            return "\033[91m"  # Red
        else:
            return "\033[92m"  # Green
    
    def log_state_change(self, old_state, new_state, timestamp):
        """Log a state change event."""
        event = {
            'timestamp': timestamp,
            'old_state': old_state,
            'new_state': new_state
        }
        self.state_changes.append(event)
        
        # Print event
        old_str = "BLOCKED" if old_state else "CLEAR"
        new_str = "BLOCKED" if new_state else "CLEAR"
        print(f"\n[EVENT] State changed: {old_str} → {new_str} at {timestamp.strftime('%H:%M:%S.%f')[:-3]}")
    
    def run(self):
        """Main test loop."""
        if not self.initialize():
            return
        
        self.start_time = time.time()
        last_display_time = time.time()
        display_interval = 0.1  # Update display every 100ms
        
        try:
            while self.running:
                # Read sensor state
                try:
                    is_blocked = self.sensor.is_blocked()
                    current_time = datetime.now()
                    
                    # Detect state change
                    if self.current_state is not None and self.current_state != is_blocked:
                        self.log_state_change(self.current_state, is_blocked, current_time)
                    
                    self.current_state = is_blocked
                    self.poll_count += 1
                    
                    # Update display periodically
                    if time.time() - last_display_time >= display_interval:
                        elapsed = time.time() - self.start_time
                        poll_rate = self.poll_count / elapsed if elapsed > 0 else 0
                        
                        # Clear screen and display status
                        print("\033[2J\033[H", end="")
                        
                        print("=" * 60)
                        print(f"IR Obstacle Sensor Test - GPIO {self.gpio_pin}")
                        print(f"Time: {current_time.strftime('%H:%M:%S')}")
                        print("=" * 60)
                        
                        # Display current status
                        color_code = self.get_status_color_code(is_blocked)
                        reset_code = "\033[0m"
                        symbol = self.get_status_symbol(is_blocked)
                        
                        print(f"\nCurrent Status:")
                        print(f"  {color_code}{symbol}{reset_code}")
                        print(f"  State: {'OBSTACLE DETECTED' if is_blocked else 'PATH CLEAR'}")
                        
                        # Display statistics
                        print(f"\nStatistics:")
                        print(f"  Total Polls: {self.poll_count}")
                        print(f"  State Changes: {len(self.state_changes)}")
                        print(f"  Elapsed Time: {elapsed:.1f} s")
                        print(f"  Poll Rate: {poll_rate:.1f} Hz")
                        
                        # Display recent events
                        if self.state_changes:
                            print(f"\nRecent Events (last 5):")
                            for event in self.state_changes[-5:]:
                                old_str = "BLOCKED" if event['old_state'] else "CLEAR"
                                new_str = "BLOCKED" if event['new_state'] else "CLEAR"
                                ts = event['timestamp'].strftime('%H:%M:%S.%f')[:-3]
                                print(f"  {ts}: {old_str} → {new_str}")
                        
                        print("\n" + "-" * 60)
                        print("Press Ctrl+C to stop")
                        print("Wave hand or place object in front of sensor to test")
                        
                        last_display_time = time.time()
                    
                    # Sleep for polling interval
                    time.sleep(self.poll_interval)
                    
                except Exception as e:
                    print(f"\n[ERROR] Failed to read sensor: {e}")
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
        
        if self.start_time:
            elapsed = time.time() - self.start_time
            poll_rate = self.poll_count / elapsed if elapsed > 0 else 0
            print(f"Total Polls: {self.poll_count}")
            print(f"Total Time: {elapsed:.1f} seconds")
            print(f"Average Poll Rate: {poll_rate:.2f} Hz")
            print(f"State Changes Detected: {len(self.state_changes)}")
        
        if self.sensor:
            try:
                self.sensor.close()
                print("[OK] Sensor closed successfully")
            except Exception:
                pass
        
        print("\n[INFO] Test completed!")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test IR reflective obstacle sensor')
    parser.add_argument('--pin', type=int, default=17,
                       help='GPIO pin number (default: 17)')
    parser.add_argument('--rate', type=float, default=10.0,
                       help='Polling rate in Hz (default: 10.0)')
    
    args = parser.parse_args()
    
    test = IRSensorTest(gpio_pin=args.pin, poll_rate=args.rate)
    test.run()


if __name__ == "__main__":
    main()
