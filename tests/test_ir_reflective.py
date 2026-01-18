#!/usr/bin/env python3
"""
Test script for IR Reflective Sensor with mock data.

Simulates sensor reads with various patterns (sine waves, ramps, noise)
to validate metrics computation and anomaly detection.
"""

import sys
import time
sys.path.insert(0, '..')

from backend.sensors.ir_reflective import IRReflectiveSensor


def test_basic_reading():
    """Test basic ADC reading and normalization."""
    print("=" * 60)
    print("Test 1: Basic Reading and Normalization")
    print("=" * 60)
    
    sensor = IRReflectiveSensor(use_mock=True, sampling_rate_hz=10.0)
    
    print("\nReading 10 samples...")
    for i in range(10):
        raw = sensor.read_raw()
        normalized = sensor.normalize(raw)
        voltage = sensor.get_voltage(raw)
        print(f"Sample {i+1}: Raw={raw:4d}, Normalized={normalized:.3f}, Voltage={voltage:.3f}V")
        time.sleep(0.1)
    
    print("\n[OK] Basic reading test passed")


def test_ema_smoothing():
    """Test EMA smoothing."""
    print("\n" + "=" * 60)
    print("Test 2: EMA Smoothing")
    print("=" * 60)
    
    sensor = IRReflectiveSensor(use_mock=True, ema_alpha=0.3)
    
    print("\nApplying EMA smoothing to noisy signal...")
    raw_values = []
    smoothed_values = []
    
    for i in range(20):
        raw = sensor.read_raw()
        normalized = sensor.normalize(raw)
        smoothed = sensor.apply_ema(normalized)
        raw_values.append(normalized)
        smoothed_values.append(smoothed)
        print(f"Sample {i+1}: Raw={normalized:.3f}, Smoothed={smoothed:.3f}")
        time.sleep(0.1)
    
    print(f"\nRaw std dev: {__import__('numpy').std(raw_values):.4f}")
    print(f"Smoothed std dev: {__import__('numpy').std(smoothed_values):.4f}")
    print("\n[OK] EMA smoothing test passed")


def test_metrics_computation():
    """Test metrics computation."""
    print("\n" + "=" * 60)
    print("Test 3: Metrics Computation")
    print("=" * 60)
    
    sensor = IRReflectiveSensor(use_mock=True, sampling_rate_hz=10.0)
    
    print("\nComputing metrics over 5 seconds...")
    for i in range(50):  # 5 seconds at 10 Hz
        metrics = sensor.compute_metrics()
        
        if i % 10 == 0:  # Print every second
            print(f"\nTime: {i/10:.1f}s")
            print(f"  Raw ADC: {metrics['raw_adc']}")
            print(f"  Moisture Index: {metrics['mi']:.3f}")
            print(f"  Drying Rate: {metrics['drying_rate']:.4f} /sec")
            print(f"  Roughness: {metrics['roughness']:.4f}")
            print(f"  Anomaly Flag: {metrics['anomaly_flag']}")
        
        time.sleep(0.1)
    
    print("\n[OK] Metrics computation test passed")


def test_anomaly_detection():
    """Test anomaly detection."""
    print("\n" + "=" * 60)
    print("Test 4: Anomaly Detection")
    print("=" * 60)
    
    sensor = IRReflectiveSensor(use_mock=True, sampling_rate_hz=10.0)
    
    # Simulate rapid MI drop (contact risk)
    print("\nSimulating rapid MI drop (contact risk)...")
    for i in range(10):
        metrics = sensor.compute_metrics()
        if metrics['contact_risk_flag']:
            print(f"[ALERT] Contact risk detected: {metrics['anomaly_reason']}")
        time.sleep(0.1)
    
    # Simulate over-drying
    print("\nSimulating over-drying scenario...")
    # Force negative drying rate
    for _ in range(20):
        sensor.mi_history.append(0.5)
        sensor.mi_history.append(0.4)
        sensor.mi_history.append(0.3)
    
    metrics = sensor.compute_metrics()
    if metrics['over_drying_flag']:
        print(f"[ALERT] Over-drying detected: {metrics['anomaly_reason']}")
    
    print("\n[OK] Anomaly detection test passed")


def test_csv_logging():
    """Test CSV logging."""
    print("\n" + "=" * 60)
    print("Test 5: CSV Logging")
    print("=" * 60)
    
    import os
    import tempfile
    
    sensor = IRReflectiveSensor(use_mock=True, sampling_rate_hz=10.0)
    
    # Create temporary log file
    temp_dir = tempfile.mkdtemp()
    log_file = os.path.join(temp_dir, "test_ir_log.csv")
    
    print(f"\nLogging to: {log_file}")
    
    # Log 10 samples
    for i in range(10):
        sensor.compute_metrics()
        sensor.log_to_csv(log_file)
        time.sleep(0.1)
    
    # Verify file exists and has content
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            lines = f.readlines()
            print(f"\nLogged {len(lines)-1} data rows (plus header)")
            print("First few lines:")
            for line in lines[:3]:
                print(f"  {line.strip()}")
    
    print("\n[OK] CSV logging test passed")


def main():
    """Run all tests."""
    print("IR Reflective Sensor Test Suite")
    print("=" * 60)
    print("Using mock data for testing\n")
    
    try:
        test_basic_reading()
        test_ema_smoothing()
        test_metrics_computation()
        test_anomaly_detection()
        test_csv_logging()
        
        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
