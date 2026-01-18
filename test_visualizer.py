#!/usr/bin/env python3
"""
Test the live arm pointcloud visualizer
"""
import sys
import os

# Setup paths
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib:' + os.environ.get('LD_LIBRARY_PATH', '')
sys.path.insert(0, '/usr/lib/python3.8/site-packages')

print("=" * 70)
print("Testing Live Arm Pointcloud Visualizer")
print("=" * 70)
print()

# Test imports
print("[1] Testing imports...")
try:
    import pyrealsense2 as rs
    print("  ✓ pyrealsense2")
except Exception as e:
    print(f"  ✗ pyrealsense2: {e}")
    sys.exit(1)

try:
    import cv2
    print(f"  ✓ OpenCV {cv2.__version__}")
except Exception as e:
    print(f"  ✗ OpenCV: {e}")
    print("  Installing OpenCV...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "opencv-python", "-q"])
    import cv2
    print(f"  ✓ OpenCV {cv2.__version__} installed")

try:
    import numpy as np
    print(f"  ✓ NumPy {np.__version__}")
except Exception as e:
    print(f"  ✗ NumPy: {e}")
    sys.exit(1)

# Test camera detection
print("\n[2] Testing camera detection...")
try:
    ctx = rs.context()
    devices = ctx.query_devices()
    print(f"  Found {len(devices)} camera(s)")
    
    if len(devices) == 0:
        print("\n  ⚠ No camera detected")
        print("\n  The visualizer will show an error message.")
        print("  To test with camera:")
        print("    1. Connect RealSense to USB 3.0 port")
        print("    2. Run: python3 live_arm_pointcloud_jetson.py")
    else:
        print("\n  ✓ Camera detected!")
        for i, dev in enumerate(devices):
            name = dev.get_info(rs.camera_info.name)
            serial = dev.get_info(rs.camera_info.serial_number)
            print(f"    Camera {i+1}: {name} (Serial: {serial})")
        print("\n  ✓ Ready to run visualizer!")
        print("  Run: python3 live_arm_pointcloud_jetson.py")
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# Test if we can import the visualizer module
print("\n[3] Testing visualizer code...")
print("  Checking live_arm_pointcloud_jetson.py...")
if os.path.exists('live_arm_pointcloud_jetson.py'):
    print("  ✓ File exists")
    
    # Try to compile it
    try:
        with open('live_arm_pointcloud_jetson.py', 'r') as f:
            code = f.read()
        compile(code, 'live_arm_pointcloud_jetson.py', 'exec')
        print("  ✓ Code compiles successfully")
    except SyntaxError as e:
        print(f"  ✗ Syntax error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"  ⚠ Warning: {e}")
else:
    print("  ✗ File not found")
    sys.exit(1)

print("\n" + "=" * 70)
print("Test Summary")
print("=" * 70)
print("✓ All imports working")
print("✓ Visualizer code is valid")

if len(devices) > 0:
    print("✓ Camera detected - Ready to run!")
    print("\nTo start the visualizer:")
    print("  python3 live_arm_pointcloud_jetson.py")
else:
    print("⚠ No camera detected")
    print("\nThe visualizer will run but show 'No cameras detected' error.")
    print("Connect camera and run: python3 live_arm_pointcloud_jetson.py")

print("=" * 70)
print("\nTo test the visualizer now (even without camera):")
print("  python3 live_arm_pointcloud_jetson.py")
print("\nIt will show an error message if no camera, but code will run.")
