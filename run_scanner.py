#!/usr/bin/env python3
"""
Entry point for running the 3D arm scanner.

Usage:
    python run_scanner.py              # Start live scanning
    python run_scanner.py --test       # Test camera connection
"""

import argparse
import sys
from backend.scanning.arm_scanner import main as scanner_main


def main():
    parser = argparse.ArgumentParser(
        description="Intel RealSense L515 - Live Arm Point Cloud Capture"
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test camera connection and exit'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/scans',
        help='Output directory for point clouds (default: data/scans)'
    )
    
    args = parser.parse_args()
    
    if args.test:
        print("Testing RealSense camera connection...")
        try:
            import pyrealsense2 as rs
            ctx = rs.context()
            devices = ctx.query_devices()
            
            if len(devices) == 0:
                print("[ERROR] No RealSense devices found!")
                return 1
            
            for dev in devices:
                print(f"[OK] Found device: {dev.get_info(rs.camera_info.name)}")
                print(f"     Serial: {dev.get_info(rs.camera_info.serial_number)}")
                print(f"     Firmware: {dev.get_info(rs.camera_info.firmware_version)}")
            
            return 0
        except Exception as e:
            print(f"[ERROR] {e}")
            return 1
    
    # Run scanner
    try:
        scanner_main()
        return 0
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
        return 0
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

