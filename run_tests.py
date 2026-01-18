#!/usr/bin/env python3
"""
Comprehensive RealSense Test Script
Tests installation and camera detection
"""
import sys
import os
import subprocess

print("=" * 60)
print("Intel RealSense Installation Test")
print("=" * 60)
print()

# Test 1: Check pyrealsense2 import
print("[1/5] Testing pyrealsense2 import...")
try:
    import pyrealsense2 as rs
    print(f"  ✓ pyrealsense2 {rs.__version__} imported successfully")
except ImportError as e:
    print(f"  ✗ Failed to import pyrealsense2: {e}")
    print("\n  Trying system-wide installation...")
    sys.path.insert(0, '/usr/lib/python3.8/site-packages')
    try:
        import pyrealsense2 as rs
        print(f"  ✓ pyrealsense2 {rs.__version__} found in system packages")
    except ImportError:
        print("  ✗ pyrealsense2 not found anywhere")
        sys.exit(1)

# Test 2: Check library path
print("\n[2/5] Checking library paths...")
ld_path = os.environ.get('LD_LIBRARY_PATH', '')
if '/usr/local/lib' in ld_path or os.path.exists('/usr/local/lib/librealsense2.so'):
    print("  ✓ librealsense2 library found")
else:
    print("  ⚠ Setting LD_LIBRARY_PATH...")
    os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib:' + ld_path
    print("  ✓ LD_LIBRARY_PATH set")

# Test 3: Check USB devices
print("\n[3/5] Checking USB devices...")
try:
    result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
    usb_output = result.stdout.lower()
    if 'intel' in usb_output or '8086' in usb_output:
        print("  ✓ Intel USB device(s) found:")
        for line in result.stdout.split('\n'):
            if 'intel' in line.lower() or '8086' in line.lower():
                print(f"    {line}")
    else:
        print("  ⚠ No Intel/RealSense USB devices found")
        print("    Please connect your RealSense camera to a USB 3.0 port")
except Exception as e:
    print(f"  ⚠ Could not check USB devices: {e}")

# Test 4: Check udev rules
print("\n[4/5] Checking udev rules...")
if os.path.exists('/etc/udev/rules.d/99-realsense-libusb.rules'):
    print("  ✓ udev rules file exists")
else:
    print("  ⚠ udev rules not found")
    if os.path.exists('/mnt/ssd/librealsense/config/99-realsense-libusb.rules'):
        print("  ℹ Found rules in librealsense source")
        print("  Run: sudo cp /mnt/ssd/librealsense/config/99-realsense-libusb.rules /etc/udev/rules.d/")
        print("  Then: sudo udevadm control --reload-rules && sudo udevadm trigger")

# Test 5: Test camera detection
print("\n[5/5] Testing camera detection...")
try:
    ctx = rs.context()
    devices = ctx.query_devices()
    
    if len(devices) == 0:
        print("  ⚠ No cameras detected")
        print("\n  Troubleshooting:")
        print("    1. Connect RealSense camera to USB 3.0 port (blue)")
        print("    2. Check: lsusb | grep -i intel")
        print("    3. If udev rules missing, install them (see step 4)")
        print("    4. If you were just added to plugdev group, log out/in")
        print("    5. Try: sudo udevadm control --reload-rules && sudo udevadm trigger")
    else:
        print(f"  ✓ Found {len(devices)} camera(s):")
        for i, dev in enumerate(devices):
            try:
                name = dev.get_info(rs.camera_info.name)
                serial = dev.get_info(rs.camera_info.serial_number)
                firmware = dev.get_info(rs.camera_info.firmware_version)
                print(f"\n    Camera {i+1}:")
                print(f"      Name: {name}")
                print(f"      Serial: {serial}")
                print(f"      Firmware: {firmware}")
            except Exception as e:
                print(f"    Camera {i+1}: Error getting info - {e}")
        
        # Try to get a frame (quick test)
        print("\n  Testing frame capture...")
        try:
            pipeline = rs.pipeline()
            config = rs.config()
            config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
            config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            
            profile = pipeline.start(config)
            print("  ✓ Pipeline started")
            
            # Wait for a frame
            frames = pipeline.wait_for_frames(timeout_ms=5000)
            if frames:
                print("  ✓ Frame captured successfully")
                pipeline.stop()
                print("\n" + "=" * 60)
                print("✓✓✓ ALL TESTS PASSED - CAMERA IS WORKING! ✓✓✓")
                print("=" * 60)
                print("\nYou can now run the visualizer:")
                print("  python3 live_arm_pointcloud_jetson.py")
                sys.exit(0)
            else:
                print("  ⚠ No frames received (camera may need time to initialize)")
                pipeline.stop()
        except Exception as e:
            print(f"  ⚠ Frame capture test failed: {e}")
            print("  Camera detected but may need configuration")
            
except Exception as e:
    print(f"  ✗ Error detecting cameras: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test Summary")
print("=" * 60)
print("✓ pyrealsense2 is installed and working")
if len(devices) > 0:
    print("✓ Camera hardware detected")
    print("⚠ Some tests had warnings - camera may still work")
else:
    print("⚠ Camera not detected - connect camera and check USB/udev rules")
print("=" * 60)
