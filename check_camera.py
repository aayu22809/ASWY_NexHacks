#!/usr/bin/env python3
"""
Quick diagnostic script to detect RealSense cameras
"""
import pyrealsense2 as rs
import sys

print("="*60)
print("RealSense Camera Detection")
print("="*60)

try:
    ctx = rs.context()
    devices = ctx.query_devices()
    
    if len(devices) == 0:
        print("\n[ERROR] No RealSense devices found!")
        print("\nTroubleshooting:")
        print("  1. Ensure camera is plugged into USB 3.0 port (blue connector)")
        print("  2. Try a different USB port")
        print("  3. Check Windows Device Manager:")
        print("     - Look for 'Intel RealSense' devices")
        print("     - Check if any have warning icons")
        print("  4. Install/update drivers:")
        print("     - Download Intel RealSense SDK from:")
        print("       https://github.com/IntelRealSense/librealsense/releases")
        print("  5. Restart computer after driver installation")
        sys.exit(1)
    
    print(f"\n[OK] Found {len(devices)} RealSense device(s)!\n")
    
    for i, dev in enumerate(devices):
        print(f"Device {i+1}:")
        print(f"  Name: {dev.get_info(rs.camera_info.name)}")
        print(f"  Serial: {dev.get_info(rs.camera_info.serial_number)}")
        print(f"  Firmware: {dev.get_info(rs.camera_info.firmware_version)}")
        print(f"  USB Type: {dev.get_info(rs.camera_info.usb_type_descriptor)}")
        print(f"  Product Line: {dev.get_info(rs.camera_info.product_line)}")
        
        # Check available sensors
        sensors = dev.query_sensors()
        print(f"  Sensors ({len(sensors)}):")
        for sensor in sensors:
            print(f"    - {sensor.get_info(rs.camera_info.name)}")
        print()
    
    print("="*60)
    print("[SUCCESS] Camera is ready to use!")
    print("="*60)
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

