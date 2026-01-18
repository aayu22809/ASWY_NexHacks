#!/usr/bin/env python3
"""
Simple RealSense Test - Just get it working!
"""
import sys
import os

# Set up paths
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib:' + os.environ.get('LD_LIBRARY_PATH', '')
sys.path.insert(0, '/usr/lib/python3.8/site-packages')

print("=" * 60)
print("RealSense Simple Test")
print("=" * 60)
print()

# Test import
print("[1] Testing import...")
try:
    import pyrealsense2 as rs
    print("  ✓ pyrealsense2 imported")
except Exception as e:
    print(f"  ✗ Import failed: {e}")
    sys.exit(1)

# Test context
print("\n[2] Testing context...")
try:
    ctx = rs.context()
    print("  ✓ Context created")
except Exception as e:
    print(f"  ✗ Context failed: {e}")
    sys.exit(1)

# Test device detection
print("\n[3] Testing device detection...")
try:
    devices = ctx.query_devices()
    print(f"  Found {len(devices)} device(s)")
    
    if len(devices) == 0:
        print("\n  ⚠ No camera detected")
        print("\n  To fix:")
        print("    1. Connect RealSense to USB 3.0 port")
        print("    2. Check: lsusb | grep -i intel")
        print("    3. Run: sudo ./finish_realsense_setup.sh")
        print("    4. Log out and log back in")
    else:
        print("\n  ✓ Camera detected!")
        for i, dev in enumerate(devices):
            try:
                name = dev.get_info(rs.camera_info.name)
                serial = dev.get_info(rs.camera_info.serial_number)
                print(f"\n     Camera {i+1}:")
                print(f"       Name: {name}")
                print(f"       Serial: {serial}")
                
                # Try to start pipeline
                print("\n[4] Testing pipeline...")
                pipeline = rs.pipeline()
                config = rs.config()
                config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
                config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
                
                profile = pipeline.start(config)
                print("  ✓ Pipeline started")
                
                frames = pipeline.wait_for_frames(timeout_ms=5000)
                if frames:
                    depth = frames.get_depth_frame()
                    color = frames.get_color_frame()
                    if depth:
                        print(f"  ✓ Depth: {depth.get_width()}x{depth.get_height()}")
                    if color:
                        print(f"  ✓ Color: {color.get_width()}x{color.get_height()}")
                    
                    pipeline.stop()
                    print("\n" + "=" * 60)
                    print("🎉 SUCCESS! Camera is working!")
                    print("=" * 60)
                    print("\nRun: python3 live_arm_pointcloud_jetson.py")
                    sys.exit(0)
                else:
                    print("  ⚠ No frames (camera may need time)")
                    pipeline.stop()
                    
            except Exception as e:
                print(f"  Error with camera {i+1}: {e}")
                import traceback
                traceback.print_exc()
                
except Exception as e:
    print(f"  ✗ Device detection failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test complete - Library is working!")
if len(devices) == 0:
    print("Connect camera to continue.")
print("=" * 60)
