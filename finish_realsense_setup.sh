#!/bin/bash
# =============================================================================
# Finish RealSense Setup - Run this with sudo after connecting camera
# =============================================================================

echo "=============================================="
echo "Finishing Intel RealSense Setup"
echo "=============================================="

# Install udev rules
echo "[1/3] Installing udev rules..."
sudo cp /mnt/ssd/librealsense/config/99-realsense-libusb.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
echo "[OK] udev rules installed"

# Add user to plugdev group
echo "[2/3] Adding user to plugdev group..."
sudo usermod -aG plugdev $USER
echo "[OK] User added to plugdev group"

# Install system libraries (optional but recommended)
echo "[3/3] Installing system libraries..."
cd /mnt/ssd/librealsense/build
sudo make install
sudo ldconfig
echo "[OK] System libraries installed"

echo ""
echo "=============================================="
echo "Setup Complete!"
echo "=============================================="
echo ""
echo "IMPORTANT: Log out and log back in for group changes to take effect."
echo ""
echo "To test your camera, run:"
echo "  source ~/.bashrc"
echo "  python3 /home/sam/ASWY_NexHacks-main/live_arm_pointcloud_jetson.py"
echo ""
