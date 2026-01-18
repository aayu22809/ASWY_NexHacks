#!/usr/bin/env python3
"""
All-in-One RealSense Test & Fix Script
Run this to test and debug everything
"""
import sys
import os
import subprocess

# Setup paths
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib:' + os.environ.get('LD_LIBRARY_PATH', '')
sys.path.insert(0, '/usr/lib/python3.8/site-packages')

print("=" * 70)
print("RealSense Complete Test & Debug")
print("=" * 70)
print()

# Test 1: Import
print("[TEST 1] Importing pyrealsense2...")
try:
    import pyrealsense2 as rs
    version = getattr(rs, '__version__', '2.57.5 (installed)')
    print(f"  ✓ SUCCESS: pyrealsense2 {version}")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 2: Context
print("\n[TEST 2] Creating context...")
try:
    ctx = rs.context()
    print("  ✓ SUCCESS: Context created")
except Exception as e:
    print(f"  ✗ FAILED: {e}")
    sys.exit(1)

# Test 3: USB Check
print("\n[TEST 3] Checking USB devices...")
try:
    result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
    intel_devs = [l for l in result.stdout.split('\n') if 'intel' in l.lower() or '8086' in l.lower()]
    if intel_devs:
        print("  ✓ Intel USB device(s) found:")
        for dev in intel_devs:
            print(f"    {dev}")
    else:
        print("  ⚠ No Intel USB devices found")
        print("  → Connect RealSense camera to USB 3.0 port")
except:
    print("  ⚠ Could not check USB")

# Test 4: udev rules
print("\n[TEST 4] Checking udev rules...")
if os.path.exists('/etc/udev/rules.d/99-realsense-libusb.rules'):
    print("  ✓ udev rules exist")
else:
    print("  ⚠ udev rules missing")
    if os.path.exists('/mnt/ssd/librealsense/config/99-realsense-libusb.rules'):
        print("  → Run: sudo cp /mnt/ssd/librealsense/config/99-realsense-libusb.rules /etc/udev/rules.d/")
        print("  → Then: sudo udevadm control --reload-rules && sudo udevadm trigger")

# Test 5: Groups
print("\n[TEST 5] Checking user groups...")
try:
    result = subprocess.run(['groups'], capture_output=True, text=True, timeout=5)
    if 'plugdev' in result.stdout:
        print("  ✓ User is in plugdev group")
    else:
        print("  ⚠ User NOT in plugdev group")
        print("  → Run: sudo usermod -aG plugdev $USER")
        print("  → Then: log out and log back in")
except:
    print("  ⚠ Could not check groups")

# Test 6: Device detection
print("\n[TEST 6] Detecting cameras...")
try:
    devices = ctx.query_devices()
    print(f"  Found {len(devices)} device(s)")
    
    if len(devices) == 0:
        print("\n  ⚠ NO CAMERAS DETECTED")
        print("\n  Troubleshooting checklist:")
        print("    [ ] Camera connected to USB 3.0 port (blue)")
        print("    [ ] Camera powered on")
        print("    [ ] udev rules installed (see TEST 4)")
        print("    [ ] User in plugdev group (see TEST 5)")
        print("    [ ] Tried unplugging and replugging")
        print("    [ ] Checked: lsusb | grep -i intel")
        print("\n  Try:")
        print("    1. Unplug camera, wait 5 seconds, plug back in")
        print("    2. Try different USB port")
        print("    3. If you were just added to plugdev, log out/in")
        print("    4. Run: sudo udevadm control --reload-rules")
        print("    5. Check: dmesg | tail -20")
    else:
        print("\n  ✓ CAMERAS DETECTED!")
        for i, dev in enumerate(devices):
            try:
                name = dev.get_info(rs.camera_info.name)
                serial = dev.get_info(rs.camera_info.serial_number)
                firmware = dev.get_info(rs.camera_info.firmware_version)
                print(f"\n    Camera {i+1}:")
                print(f"      Name: {name}")
                print(f"      Serial: {serial}")
                print(f"      Firmware: {firmware}")
                
                # Test 7: Pipeline
                print("\n[TEST 7] Testing pipeline...")
                pipeline = rs.pipeline()
                config = rs.config()
                config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
                config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
                
                print("  Starting pipeline...")
                profile = pipeline.start(config)
                print("  ✓ Pipeline started")
                
                print("  Waiting for frames (5s timeout)...")
                frames = pipeline.wait_for_frames(timeout_ms=5000)
                
                if frames:
                    depth = frames.get_depth_frame()
                    color = frames.get_color_frame()
                    
                    if depth:
                        w, h = depth.get_width(), depth.get_height()
                        print(f"  ✓ Depth frame: {w}x{h}")
                    if color:
                        w, h = color.get_width(), color.get_height()
                        print(f"  ✓ Color frame: {w}x{h}")
                    
                    pipeline.stop()
                    
                    print("\n" + "=" * 70)
                    print("🎉🎉🎉 SUCCESS! CAMERA IS FULLY WORKING! 🎉🎉🎉")
                    print("=" * 70)
                    print("\nYou can now run the visualizer:")
                    print("  python3 live_arm_pointcloud_jetson.py")
                    print("=" * 70)
                    sys.exit(0)
                else:
                    print("  ⚠ No frames received (timeout)")
                    print("  Camera may need more time to initialize")
                    pipeline.stop()
                    
            except Exception as e:
                print(f"  ✗ Error with camera {i+1}: {e}")
                import traceback
                traceback.print_exc()
                
except Exception as e:
    print(f"  ✗ Device detection failed: {e}")
    import traceback
    traceback.print_exc()

# Final summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print("✓ pyrealsense2 library: WORKING")
print("✓ Context creation: WORKING")
if len(devices) > 0:
    print("✓ Camera detection: WORKING")
    print("⚠ Frame capture: Needs retry or camera initialization")
    print("\nStatus: CAMERA DETECTED - Try running visualizer")
    print("  python3 live_arm_pointcloud_jetson.py")
else:
    print("⚠ Camera detection: NO CAMERA FOUND")
    print("\nStatus: LIBRARY READY - Connect camera to continue")
    print("\nNext steps:")
    print("  1. Connect RealSense to USB 3.0 port")
    print("  2. Fix any issues shown in tests above")
    print("  3. Run this test again: python3 run_all_tests.py")
print("=" * 70)
