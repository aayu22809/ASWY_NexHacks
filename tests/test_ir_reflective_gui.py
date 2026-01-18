#!/usr/bin/env python3
"""
GUI test script for IR Reflective Sensor with live visualization.

Tests matplotlib dashboard performance and validates anomaly detection UI.
"""

import sys
import time
import signal
sys.path.insert(0, '..')

from backend.sensors.ir_reflective import IRReflectiveSensor


class IRGUITest:
    """Test harness for IR sensor GUI."""
    
    def __init__(self):
        self.sensor = None
        self.running = True
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully."""
        print("\n[INFO] Shutting down...")
        self.running = False
    
    def run(self):
        """Run GUI test."""
        print("=" * 60)
        print("IR Reflective Sensor GUI Test")
        print("=" * 60)
        print("\n[INFO] Initializing sensor with mock data...")
        
        self.sensor = IRReflectiveSensor(
            use_mock=True,
            sampling_rate_hz=20.0,
            ema_alpha=0.3
        )
        
        print("[OK] Sensor initialized")
        print("[INFO] Starting live visualization...")
        print("[INFO] Press Ctrl+C to stop\n")
        
        # Start visualization
        self.sensor.start_visualization()
        
        # Main loop: compute metrics and update plots
        try:
            while self.running:
                metrics = self.sensor.compute_metrics()
                
                # Print metrics every second
                if len(self.sensor.timestamp_history) % 20 == 0:  # ~1 second at 20 Hz
                    print(f"\nMetrics:")
                    print(f"  MI: {metrics['mi']:.3f}")
                    print(f"  Drying Rate: {metrics['drying_rate']:.4f} /sec")
                    print(f"  Roughness: {metrics['roughness']:.4f}")
                    if metrics['anomaly_flag']:
                        print(f"  [ALERT] {metrics['anomaly_reason']}")
                
                time.sleep(self.sensor.sample_interval)
        
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources."""
        if self.sensor:
            self.sensor.close()
        print("\n[INFO] Test completed")


def main():
    """Main entry point."""
    test = IRGUITest()
    test.run()


if __name__ == "__main__":
    main()
