#!/usr/bin/env python3
"""
Debug RealSense Camera - Find out what's wrong
"""
import sys
import os
import subprocess

print("=" * 70)
print("RealSense Camera Debug Tool")
print("=" * 70)
print()

# Check 1: Library paths
print("[CHECK 1] Library paths...")
ld_path = os.environ.get('LD_LIBRARY_PATH', '')
print(f"  LD_LIBRARY_PATH: {ld_path}")
if '/usr/local/lib' not in ld_path:
    os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib:' + ld_path
    print("  ✓ Added /usr/local/lib")

# Check 2: Python path
print("\n[CHECK 2] Python paths...")
sys.path.insert(0, '/usr/lib/python3.8/site-packages')
print(f"  sys.path includes: {sys.path[:3]}")

# Check 3: Import
print("\n[CHECK 3] Importing pyrealsense2...")
try:
    import pyrealsense2 as rs
    print("  ✓ Import successful")
    print(f"  Module location: {getattr(rs, '__file__', 'built-in')}")
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check 4: USB devices
print("\n[CHECK 4] USB devices...")
try:
    result = subprocess.run(['lsusb'], capture_output=True, text=True, timeout=5)
    lines = result.stdout.strip().split('\n')
    intel_devices = [l for l in lines if 'intel' in l.lower() or '8086' in l.lower()]
    if intel_devices:
        print("  ✓ Intel devices found:")
        for dev in intel_devices:
            print(f"    {dev}")
    else:
        print("  ⚠ No Intel devices found")
        print("  All USB devices:")
        for l in lines[:5]:
            print(f"    {l}")
except Exception as e:
    print(f"  ⚠ Could not check USB: {e}")

# Check 5: udev rules
print("\n[CHECK 5] udev rules...")
if os.path.exists('/etc/udev/rules.d/99-realsense-libusb.rules'):
    print("  ✓ udev rules exist")
else:
    print("  ⚠ udev rules missing")
    if os.path.exists('/mnt/ssd/librealsense/config/99-realsense-libusb.rules'):
        print("  ℹ Found source rules - need to install")
        print("  Run: sudo cp /mnt/ssd/librealsense/config/99-realsense-libusb.rules /etc/udev/rules.d/")
        print("  Then: sudo udevadm control --reload-rules && sudo udevadm trigger")

# Check 6: Groups
print("\n[CHECK 6] User groups...")
try:
    result = subprocess.run(['groups'], capture_output=True, text=True, timeout=5)
    groups = result.stdout.strip().split()
    if 'plugdev' in groups:
        print("  ✓ User is in plugdev group")
    else:
        print("  ⚠ User NOT in plugdev group")
        print("  Run: sudo usermod -aG plugdev $USER")
        print("  Then: log out and log back in")
except Exception as e:
    print(f"  ⚠ Could not check groups: {e}")

# Check 7: Context and devices
print("\n[CHECK 7] RealSense context...")
try:
    ctx = rs.context()
    print("  ✓ Context created")
    
    devices = ctx.query_devices()
    print(f"  Found {len(devices)} device(s)")
    
    if len(devices) == 0:
        print("\n  ⚠ NO CAMERAS DETECTED")
        print("\n  Possible causes:")
        print("    1. Camera not connected")
        print("    2. Wrong USB port (need USB 3.0)")
        print("    3. Missing udev rules")
        print("    4. User not in plugdev group")
        print("    5. Camera needs firmware update")
        print("\n  Try these:")
        print("    - Unplug and replug camera")
        print("    - Try different USB port")
        print("    - Check: dmesg | tail -20")
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
                
                # Try pipeline
                print("\n  Testing pipeline...")
                pipeline = rs.pipeline()
                config = rs.config()
                config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
                config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
                
                profile = pipeline.start(config)
                print("    ✓ Pipeline started")
                
                frames = pipeline.wait_for_frames(timeout_ms=5000)
                if frames:
                    print("    ✓ Frames received")
                    depth = frames.get_depth_frame()
                    color = frames.get_color_frame()
                    if depth:
                        print(f"    ✓ Depth: {depth.get_width()}x{depth.get_height()}")
                    if color:
                        print(f"    ✓ Color: {color.get_width()}x{color.get_height()}")
                    
                    pipeline.stop()
                    print("\n" + "=" * 70)
                    print("🎉🎉🎉 CAMERA IS FULLY WORKING! 🎉🎉🎉")
                    print("=" * 70)
                    sys.exit(0)
                else:
                    print("    ⚠ No frames (timeout)")
                    pipeline.stop()
                    
            except Exception as e:
                print(f"    Error: {e}")
                import traceback
                traceback.print_exc()
                
except Exception as e:
    print(f"  ✗ Context/device error: {e}")
    import traceback
    traceback.print_exc()

# Check 8: System messages
print("\n[CHECK 8] Recent system messages...")
try:
    result = subprocess.run(['dmesg'], capture_output=True, text=True, timeout=5)
    lines = result.stdout.strip().split('\n')
    realsense_lines = [l for l in lines[-20:] if 'realsense' in l.lower() or 'intel' in l.lower() or 'usb' in l.lower()]
    if realsense_lines:
        print("  Recent relevant messages:")
        for l in realsense_lines[-5:]:
            print(f"    {l}")
    else:
        print("  No recent RealSense messages")
except:
    print("  Could not check dmesg")

print("\n" + "=" * 70)
print("Debug complete")
print("=" * 70)
