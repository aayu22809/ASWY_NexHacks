#!/bin/bash
# Master script to fix and test RealSense

set -e

echo "=============================================="
echo "RealSense Fix & Test Master Script"
echo "=============================================="
echo ""

cd /home/sam/ASWY_NexHacks-main

# Step 1: Make all scripts executable
echo "[1/6] Making scripts executable..."
chmod +x *.py *.sh 2>/dev/null || true
echo "  ✓ Done"

# Step 2: Check and fix udev rules
echo ""
echo "[2/6] Checking udev rules..."
if [ ! -f "/etc/udev/rules.d/99-realsense-libusb.rules" ]; then
    echo "  ⚠ udev rules missing"
    if [ -f "/mnt/ssd/librealsense/config/99-realsense-libusb.rules" ]; then
        echo "  Installing udev rules..."
        sudo cp /mnt/ssd/librealsense/config/99-realsense-libusb.rules /etc/udev/rules.d/
        sudo udevadm control --reload-rules
        sudo udevadm trigger
        echo "  ✓ udev rules installed"
    else
        echo "  ⚠ Could not find udev rules source"
    fi
else
    echo "  ✓ udev rules exist"
fi

# Step 3: Check groups
echo ""
echo "[3/6] Checking user groups..."
if groups | grep -q plugdev; then
    echo "  ✓ User is in plugdev group"
else
    echo "  ⚠ User not in plugdev group"
    echo "  Adding user to plugdev group..."
    sudo usermod -aG plugdev $USER
    echo "  ✓ User added to plugdev group"
    echo "  ⚠ IMPORTANT: Log out and log back in for this to take effect"
    echo "  Or run: newgrp plugdev"
fi

# Step 4: Check USB devices
echo ""
echo "[4/6] Checking USB devices..."
USB_CHECK=$(lsusb 2>/dev/null | grep -i "intel\|8086" || echo "")
if [ -n "$USB_CHECK" ]; then
    echo "  ✓ Intel USB device(s) found:"
    echo "$USB_CHECK" | sed 's/^/    /'
else
    echo "  ⚠ No Intel/RealSense USB devices found"
    echo "  Please connect your RealSense camera to a USB 3.0 port"
fi

# Step 5: Run Python test
echo ""
echo "[5/6] Running Python test..."
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
export PYTHONPATH=/usr/lib/python3.8/site-packages:$PYTHONPATH

python3 << 'PYTHON_EOF'
import sys
import os

# Set paths
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib:' + os.environ.get('LD_LIBRARY_PATH', '')
sys.path.insert(0, '/usr/lib/python3.8/site-packages')

print("  Testing pyrealsense2...")
try:
    import pyrealsense2 as rs
    print("  ✓ pyrealsense2 imported")
    
    ctx = rs.context()
    devices = ctx.query_devices()
    
    print(f"  Found {len(devices)} device(s)")
    
    if len(devices) == 0:
        print("\n  ⚠ No cameras detected")
        print("  Troubleshooting:")
        print("    1. Connect camera to USB 3.0 port")
        print("    2. Unplug and replug camera")
        print("    3. If you were just added to plugdev, log out/in")
        print("    4. Check: lsusb | grep -i intel")
        sys.exit(1)
    else:
        print("\n  ✓ Camera detected!")
        for i, dev in enumerate(devices):
            try:
                name = dev.get_info(rs.camera_info.name)
                serial = dev.get_info(rs.camera_info.serial_number)
                firmware = dev.get_info(rs.camera_info.firmware_version)
                print(f"\n    Camera {i+1}:")
                print(f"      Name: {name}")
                print(f"      Serial: {serial}")
                print(f"      Firmware: {firmware}")
                
                # Test pipeline
                print("\n  Testing pipeline...")
                pipeline = rs.pipeline()
                config = rs.config()
                config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
                config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
                
                profile = pipeline.start(config)
                print("    ✓ Pipeline started")
                
                frames = pipeline.wait_for_frames(timeout_ms=5000)
                if frames:
                    depth = frames.get_depth_frame()
                    color = frames.get_color_frame()
                    if depth:
                        print(f"    ✓ Depth: {depth.get_width()}x{depth.get_height()}")
                    if color:
                        print(f"    ✓ Color: {color.get_width()}x{color.get_height()}")
                    
                    pipeline.stop()
                    print("\n" + "=" * 50)
                    print("🎉 SUCCESS! Camera is working!")
                    print("=" * 50)
                    sys.exit(0)
                else:
                    print("    ⚠ No frames (timeout)")
                    pipeline.stop()
                    
            except Exception as e:
                print(f"    Error: {e}")
                import traceback
                traceback.print_exc()
                
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_EOF

TEST_RESULT=$?

# Step 6: Summary
echo ""
echo "[6/6] Summary"
echo "=============================================="
if [ $TEST_RESULT -eq 0 ]; then
    echo "✓✓✓ ALL TESTS PASSED - CAMERA IS WORKING! ✓✓✓"
    echo ""
    echo "You can now run:"
    echo "  python3 live_arm_pointcloud_jetson.py"
else
    echo "⚠ Camera not detected yet"
    echo ""
    echo "Next steps:"
    echo "  1. Connect RealSense camera to USB 3.0 port"
    if ! groups | grep -q plugdev; then
        echo "  2. Log out and log back in (for plugdev group)"
    fi
    echo "  3. Run this script again: ./fix_and_test_all.sh"
    echo "  4. Or run debug: python3 debug_camera.py"
fi
echo "=============================================="
