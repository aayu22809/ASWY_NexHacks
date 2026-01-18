#!/usr/bin/env python3
"""Quick MLX90640 sensor test - reads one frame and displays stats."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

try:
    from backend.sensors.mlx90640 import MLX90640Sensor
    import numpy as np
except ImportError as e:
    print(f"[ERROR] Failed to import: {e}")
    sys.exit(1)

print("=" * 60)
print("MLX90640 Quick Sensor Test")
print("=" * 60)

try:
    print("\n[INFO] Initializing sensor...")
    sensor = MLX90640Sensor()
    print("[OK] Sensor initialized successfully!")
    
    print("\n[INFO] Reading thermal frame...")
    frame = sensor.read_frame()
    
    print("[OK] Frame captured!")
    print("\n📊 Thermal Data:")
    print(f"  Array shape: {frame.shape}")
    print(f"  Total pixels: {frame.size}")
    print(f"  Min temp:  {np.min(frame):.2f}°C")
    print(f"  Max temp:  {np.max(frame):.2f}°C")
    print(f"  Mean temp: {np.mean(frame):.2f}°C")
    print(f"  Range:     {np.max(frame) - np.min(frame):.2f}°C")
    
    print("\n✅ Sensor is working correctly!")
    
    sensor.close()
    print("[OK] Sensor closed")
    
except Exception as e:
    print(f"\n❌ [ERROR] {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


