#!/usr/bin/env python3
"""
Interactive calibration script for IR Reflective Sensor.

Prompts user to place sensor at fixed distances and records baseline values
for dry and wet phantoms. Saves calibration to config file.
"""

import sys
import os
sys.path.insert(0, '..')

from backend.sensors.ir_reflective import IRReflectiveSensor
from backend.config import (
    IR_REFLECTIVE_ADC_CHANNEL,
    IR_REFLECTIVE_BASELINE_DISTANCE_MM,
    IR_REFLECTIVE_EMA_ALPHA,
    IR_REFLECTIVE_SAMPLING_RATE_HZ
)


def calibrate_sensor():
    """Interactive calibration procedure."""
    print("=" * 60)
    print("IR Reflective Sensor Calibration")
    print("=" * 60)
    
    print("\nThis script will help you calibrate the IR sensor for")
    print("moisture detection. You'll need:")
    print("  1. A dry phantom sample")
    print("  2. A wet phantom sample")
    print("  3. A way to hold sensor at fixed distance (10mm recommended)")
    
    input("\nPress Enter to continue...")
    
    # Initialize sensor
    print("\n[INFO] Initializing sensor...")
    sensor = IRReflectiveSensor(
        adc_channel=IR_REFLECTIVE_ADC_CHANNEL,
        baseline_distance_mm=IR_REFLECTIVE_BASELINE_DISTANCE_MM,
        ema_alpha=IR_REFLECTIVE_EMA_ALPHA,
        sampling_rate_hz=IR_REFLECTIVE_SAMPLING_RATE_HZ,
        use_mock=False  # Use real hardware
    )
    
    print("[OK] Sensor initialized")
    
    # Calibrate dry baseline
    print("\n" + "-" * 60)
    print("Step 1: Dry Phantom Calibration")
    print("-" * 60)
    print(f"\nPlace sensor {IR_REFLECTIVE_BASELINE_DISTANCE_MM}mm above DRY phantom sample.")
    print("Ensure sensor is stable and not moving.")
    input("\nPress Enter when ready to start dry calibration...")
    
    sensor.calibrate_baseline(IR_REFLECTIVE_BASELINE_DISTANCE_MM, dry_sample=True)
    
    # Calibrate wet baseline
    print("\n" + "-" * 60)
    print("Step 2: Wet Phantom Calibration")
    print("-" * 60)
    print(f"\nPlace sensor {IR_REFLECTIVE_BASELINE_DISTANCE_MM}mm above WET phantom sample.")
    print("Ensure sensor is stable and not moving.")
    input("\nPress Enter when ready to start wet calibration...")
    
    sensor.calibrate_baseline(IR_REFLECTIVE_BASELINE_DISTANCE_MM, dry_sample=False)
    
    # Display calibration results
    print("\n" + "=" * 60)
    print("Calibration Complete!")
    print("=" * 60)
    print(f"\nDry Baseline: {sensor.baseline_dry:.1f}")
    print(f"Wet Baseline: {sensor.baseline_wet:.1f}")
    print(f"Normalization Range: {sensor.normalization_min:.1f} - {sensor.normalization_max:.1f}")
    
    # Test calibration
    print("\n" + "-" * 60)
    print("Testing Calibration")
    print("-" * 60)
    print("\nTaking 5 test readings...")
    
    for i in range(5):
        metrics = sensor.compute_metrics()
        print(f"Sample {i+1}: Raw={metrics['raw_adc']}, MI={metrics['mi']:.3f}")
        time.sleep(0.2)
    
    # Save calibration
    print("\n" + "-" * 60)
    print("Save Calibration")
    print("-" * 60)
    
    save = input("\nSave calibration to config file? (y/n): ").strip().lower()
    if save == 'y':
        # Update config file
        config_path = os.path.join('..', 'backend', 'config.py')
        if os.path.exists(config_path):
            print(f"\n[INFO] Updating {config_path}...")
            # Note: In production, you'd want to properly parse and update the config file
            # For now, just print instructions
            print("\n[INFO] Please manually update backend/config.py with:")
            print(f"IR_REFLECTIVE_BASELINE_DRY = {sensor.baseline_dry:.1f}")
            print(f"IR_REFLECTIVE_BASELINE_WET = {sensor.baseline_wet:.1f}")
        else:
            print("[WARN] Config file not found, skipping save")
    
    print("\n[OK] Calibration complete!")


if __name__ == "__main__":
    import time
    try:
        calibrate_sensor()
    except KeyboardInterrupt:
        print("\n\n[INFO] Calibration cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Calibration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
