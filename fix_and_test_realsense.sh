#!/bin/bash
# =============================================================================
# Fix RealSense Setup and Test Camera
# =============================================================================

set -e

echo "=============================================="
echo "RealSense Diagnostic & Fix Script"
echo "=============================================="
echo ""

# Step 1: Verify pyrealsense2 is installed
echo "[1/5] Checking pyrealsense2 installation..."
if python3 -c "import pyrealsense2 as rs; print(f'✓ pyrealsense2 {rs.__version__} found')" 2>/dev/null; then
    echo "[OK] pyrealsense2 is installed"
else
    echo "[ERROR] pyrealsense2 not found!"
    echo "Checking if it's in system packages..."
    if [ -d "/usr/lib/python3.8/site-packages/pyrealsense2" ]; then
        echo "[INFO] Found in /usr/lib/python3.8/site-packages/pyrealsense2"
        echo "[INFO] Trying to import..."
        PYTHONPATH=/usr/lib/python3.8/site-packages:$PYTHONPATH python3 -c "import pyrealsense2 as rs; print(f'✓ pyrealsense2 {rs.__version__} found')" || {
            echo "[ERROR] Import failed. May need to rebuild."
            exit 1
        }
    else
        echo "[ERROR] pyrealsense2 not found. Need to install."
        exit 1
    fi
fi

# Step 2: Check USB devices
echo ""
echo "[2/5] Checking USB devices..."
USB_DEVICES=$(lsusb 2>/dev/null | grep -i "intel\|8086" || echo "")
if [ -n "$USB_DEVICES" ]; then
    echo "[OK] Found Intel USB device(s):"
    echo "$USB_DEVICES"
else
    echo "[WARN] No Intel/RealSense USB devices found"
    echo "       Please connect your RealSense camera to a USB 3.0 port"
fi

# Step 3: Check udev rules
echo ""
echo "[3/5] Checking udev rules..."
if [ -f "/etc/udev/rules.d/99-realsense-libusb.rules" ]; then
    echo "[OK] udev rules file exists"
else
    echo "[WARN] udev rules not found"
    if [ -f "/mnt/ssd/librealsense/config/99-realsense-libusb.rules" ]; then
        echo "[INFO] Found rules in librealsense source, installing..."
        sudo cp /mnt/ssd/librealsense/config/99-realsense-libusb.rules /etc/udev/rules.d/
        sudo udevadm control --reload-rules
        sudo udevadm trigger
        echo "[OK] udev rules installed"
    else
        echo "[ERROR] Cannot find udev rules file"
    fi
fi

# Step 4: Check user groups
echo ""
echo "[4/5] Checking user permissions..."
if groups | grep -q plugdev; then
    echo "[OK] User is in plugdev group"
else
    echo "[WARN] User not in plugdev group"
    echo "[INFO] Adding user to plugdev group..."
    sudo usermod -aG plugdev $USER
    echo "[OK] User added to plugdev group"
    echo "[WARN] You need to log out and log back in for this to take effect"
    echo "       Or run: newgrp plugdev"
fi

# Step 5: Test camera detection
echo ""
echo "[5/5] Testing camera detection..."
export PYTHONPATH=/usr/lib/python3.8/site-packages:$PYTHONPATH

python3 << 'PYTHON_SCRIPT'
import sys
import os

# Add library paths
os.environ['LD_LIBRARY_PATH'] = '/usr/local/lib:' + os.environ.get('LD_LIBRARY_PATH', '')

try:
    import pyrealsense2 as rs
    print(f"[OK] pyrealsense2 {rs.__version__} imported")
    
    ctx = rs.context()
    devices = ctx.query_devices()
    
    if len(devices) == 0:
        print("[WARN] No cameras detected")
        print("")
        print("Troubleshooting steps:")
        print("  1. Ensure camera is connected to USB 3.0 port (blue)")
        print("  2. Try unplugging and replugging the camera")
        print("  3. Check: lsusb | grep -i intel")
        print("  4. If you just added yourself to plugdev group, log out/in")
        print("  5. Try: sudo udevadm control --reload-rules && sudo udevadm trigger")
        sys.exit(1)
    else:
        print(f"[OK] Found {len(devices)} camera(s):")
        for i, dev in enumerate(devices):
            print(f"  Camera {i+1}:")
            print(f"    Name: {dev.get_info(rs.camera_info.name)}")
            print(f"    Serial: {dev.get_info(rs.camera_info.serial_number)}")
            print(f"    Firmware: {dev.get_info(rs.camera_info.firmware_version)}")
        print("")
        print("[SUCCESS] Camera is working!")
        sys.exit(0)
        
except ImportError as e:
    print(f"[ERROR] Failed to import pyrealsense2: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Error detecting camera: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT

EXIT_CODE=$?

echo ""
echo "=============================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ RealSense is working!"
    echo ""
    echo "To run the visualizer:"
    echo "  cd /home/sam/ASWY_NexHacks-main"
    echo "  source ~/.bashrc"
    echo "  python3 live_arm_pointcloud_jetson.py"
else
    echo "⚠ Camera not detected yet"
    echo ""
    echo "Next steps:"
    echo "  1. Connect RealSense camera to USB 3.0 port"
    echo "  2. If you were just added to plugdev group, log out and log back in"
    echo "  3. Run this script again: ./fix_and_test_realsense.sh"
fi
echo "=============================================="
