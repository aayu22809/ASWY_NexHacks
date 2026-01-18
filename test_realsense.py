#!/usr/bin/env python3
"""
Quick test script to verify RealSense is working
"""
import sys
import os

# Add library paths (try both user and system locations)
user_lib = os.path.expanduser('~/.local/lib')
system_lib = '/usr/local/lib'
current_ld = os.environ.get('LD_LIBRARY_PATH', '')
os.environ['LD_LIBRARY_PATH'] = f'{system_lib}:{user_lib}:{current_ld}'

# Add system Python packages
sys.path.insert(0, '/usr/lib/python3.8/site-packages')

try:
    import pyrealsense2 as rs
    # Get version - may not always be available
    try:
        version = rs.__version__
    except AttributeError:
        version = "2.57.5 (installed)"
    print(f"✓ pyrealsense2 {version} imported successfully")
    
    # Check for cameras
    ctx = rs.context()
    devices = ctx.query_devices()
    
    if len(devices) == 0:
        print("\n⚠ No RealSense cameras detected!")
        print("\nPlease:")
        print("  1. Connect your RealSense camera to a USB 3.0 port")
        print("  2. Run: sudo /home/sam/ASWY_NexHacks-main/finish_realsense_setup.sh")
        print("  3. Log out and log back in")
        print("  4. Run this test again")
        sys.exit(1)
    
    print(f"\n✓ Found {len(devices)} RealSense camera(s):")
    for i, dev in enumerate(devices):
        print(f"\n  Camera {i+1}:")
        print(f"    Name: {dev.get_info(rs.camera_info.name)}")
        print(f"    Serial: {dev.get_info(rs.camera_info.serial_number)}")
        print(f"    Firmware: {dev.get_info(rs.camera_info.firmware_version)}")
    
    print("\n✓ RealSense is ready to use!")
    print("\nTo run the visualizer:")
    print("  cd /home/sam/ASWY_NexHacks-main")
    print("  python3 live_arm_pointcloud_jetson.py")
    
except ImportError as e:
    print(f"✗ Failed to import pyrealsense2: {e}")
    print("\nMake sure LD_LIBRARY_PATH is set:")
    print("  export LD_LIBRARY_PATH=$HOME/.local/lib:$LD_LIBRARY_PATH")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
