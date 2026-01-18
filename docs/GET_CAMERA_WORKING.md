# Get Your RealSense Camera Working - Quick Guide

## ✅ Good News: RealSense is Already Installed!

Your installation is complete (see terminal lines 270-319). The error you saw was from trying to rebuild unnecessarily.

## 🚀 Quick Steps to Get Camera Working

### Step 1: Run the Diagnostic Script
```bash
cd /home/sam/ASWY_NexHacks-main
./fix_and_test_realsense.sh
```

This script will:
- ✓ Check if pyrealsense2 is installed
- ✓ Check USB devices
- ✓ Install udev rules if needed
- ✓ Add you to plugdev group if needed
- ✓ Test camera detection

### Step 2: Connect Your Camera
1. Connect your Intel RealSense camera to a **USB 3.0 port** (blue connector)
2. Wait a few seconds for it to initialize

### Step 3: Test Again
```bash
./fix_and_test_realsense.sh
```

If it says "Camera not detected":
- Try unplugging and replugging the camera
- If you were just added to `plugdev` group, **log out and log back in**
- Or run: `newgrp plugdev` in a new terminal

### Step 4: Run the Visualizer
Once camera is detected:
```bash
source ~/.bashrc
python3 live_arm_pointcloud_jetson.py
```

## 🔧 About the Setup Script Error

The error you saw (lines 426-436) was because:
- CMake found Python 2.7.18 instead of Python 3.8
- This happens when running the setup script again

**You don't need to rebuild!** Everything is already installed.

However, I've **fixed the script** so if you ever need to rebuild, it will work correctly.

## 📝 Manual Troubleshooting

If the diagnostic script doesn't work, try these manually:

### Check if camera is connected:
```bash
lsusb | grep -i intel
```

### Check udev rules:
```bash
ls -la /etc/udev/rules.d/99-realsense-libusb.rules
```

If missing, install them:
```bash
sudo cp /mnt/ssd/librealsense/config/99-realsense-libusb.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Check your groups:
```bash
groups | grep plugdev
```

If not in group:
```bash
sudo usermod -aG plugdev $USER
# Then log out and log back in
```

### Test camera detection:
```bash
source ~/.bashrc
python3 test_realsense.py
```

## 🎯 Summary

1. **Run**: `./fix_and_test_realsense.sh`
2. **Connect** camera to USB 3.0
3. **Log out/in** if you were added to plugdev group
4. **Run visualizer**: `python3 live_arm_pointcloud_jetson.py`

That's it! 🎉
