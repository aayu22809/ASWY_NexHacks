# Debug and Fix RealSense Camera

## 🚀 Quick Fix - Run This First

```bash
cd /home/sam/ASWY_NexHacks-main
python3 run_all_tests.py
```

This will:
- ✓ Test pyrealsense2 import
- ✓ Check USB devices
- ✓ Check udev rules
- ✓ Check user groups
- ✓ Detect cameras
- ✓ Test frame capture

## 📋 Step-by-Step Debugging

### Step 1: Run Comprehensive Test
```bash
cd /home/sam/ASWY_NexHacks-main
python3 run_all_tests.py
```

### Step 2: If Camera Not Detected

**Check USB:**
```bash
lsusb | grep -i intel
```

**Check udev rules:**
```bash
ls -la /etc/udev/rules.d/99-realsense-libusb.rules
```

If missing, install:
```bash
sudo cp /mnt/ssd/librealsense/config/99-realsense-libusb.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

**Check groups:**
```bash
groups | grep plugdev
```

If not in group:
```bash
sudo usermod -aG plugdev $USER
# Then log out and log back in
```

### Step 3: Run Debug Script
```bash
python3 debug_camera.py
```

This shows detailed diagnostics.

### Step 4: Try Simple Test
```bash
python3 simple_test.py
```

## 🔧 All Available Test Scripts

1. **`run_all_tests.py`** - Complete test (RECOMMENDED)
2. **`debug_camera.py`** - Detailed diagnostics
3. **`simple_test.py`** - Quick test
4. **`comprehensive_test.py`** - Full test suite
5. **`test_realsense.py`** - Basic test

## ✅ When Camera is Detected

Run the visualizer:
```bash
python3 live_arm_pointcloud_jetson.py
```

## 🐛 Common Issues

### Issue: "No cameras detected"
**Solutions:**
1. Connect camera to USB 3.0 port (blue)
2. Unplug and replug camera
3. Check udev rules are installed
4. Check user is in plugdev group
5. Log out and log back in if group was just added

### Issue: "Permission denied"
**Solution:**
```bash
sudo usermod -aG plugdev $USER
# Log out and log back in
```

### Issue: "Import error"
**Solution:**
```bash
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
export PYTHONPATH=/usr/lib/python3.8/site-packages:$PYTHONPATH
python3 run_all_tests.py
```

## 📝 Master Script (Bash)

If Python tests work, you can also run:
```bash
./fix_and_test_all.sh
```

This does everything automatically (requires sudo for some steps).
