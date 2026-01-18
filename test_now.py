#!/usr/bin/env python3
"""Quick test - run this now"""
import sys, os
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib:' + os.environ.get('LD_LIBRARY_PATH', '')
sys.path.insert(0, '/usr/lib/python3.8/site-packages')

print("="*60)
print("RealSense Test - Running Now")
print("="*60)

try:
    import pyrealsense2 as rs
    print("✓ pyrealsense2 imported")
    
    ctx = rs.context()
    devices = ctx.query_devices()
    print(f"✓ Found {len(devices)} camera(s)")
    
    if len(devices) > 0:
        for i, dev in enumerate(devices):
            name = dev.get_info(rs.camera_info.name)
            serial = dev.get_info(rs.camera_info.serial_number)
            print(f"\n  Camera {i+1}: {name}")
            print(f"  Serial: {serial}")
            
            # Test pipeline
            pipeline = rs.pipeline()
            config = rs.config()
            config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
            config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
            profile = pipeline.start(config)
            frames = pipeline.wait_for_frames(timeout_ms=5000)
            if frames:
                print("  ✓ Frames captured - CAMERA WORKING!")
                pipeline.stop()
                print("\n" + "="*60)
                print("SUCCESS! Run: python3 live_arm_pointcloud_jetson.py")
                print("="*60)
                sys.exit(0)
            pipeline.stop()
    else:
        print("\n⚠ No camera detected")
        print("Connect camera to USB 3.0 and run again")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
