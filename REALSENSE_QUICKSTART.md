# Intel RealSense Quick Start Guide

## ✅ Current Status
- **librealsense 2.57.5**: Built and installed ✓
- **pyrealsense2**: Working ✓
- **Library path**: Configured in ~/.bashrc ✓

## 🚀 How to Run

### Step 1: Connect Your Camera
Connect your Intel RealSense camera to a **USB 3.0 port** (blue connector).

### Step 2: Setup USB Permissions (One-time, requires sudo)
```bash
sudo /home/sam/ASWY_NexHacks-main/finish_realsense_setup.sh
```

Then **log out and log back in** (or run `newgrp plugdev`).

### Step 3: Test the Camera
```bash
cd /home/sam/ASWY_NexHacks-main
source ~/.bashrc  # Load library path
python3 test_realsense.py
```

This will show you if the camera is detected.

### Step 4: Run the Visualizer

**Option A: Jetson-optimized visualizer (recommended)**
```bash
cd /home/sam/ASWY_NexHacks-main
source ~/.bashrc
python3 live_arm_pointcloud_jetson.py
```

**Controls:**
- `Q` or `ESC`: Quit
- `S`: Save point cloud to .ply file
- `D`: Toggle depth colormap
- `+/-`: Adjust depth range

**Option B: Original visualizer (requires Open3D)**
```bash
cd /home/sam/ASWY_NexHacks-main
source ~/.bashrc
python3 live_arm_pointcloud.py
```

## 📝 Troubleshooting

### "No cameras detected"
1. Make sure camera is connected to USB 3.0 port
2. Run the finish setup script with sudo
3. Log out and log back in
4. Try unplugging and replugging the camera

### "Module not found: pyrealsense2"
```bash
source ~/.bashrc
export LD_LIBRARY_PATH=$HOME/.local/lib:$LD_LIBRARY_PATH
```

### "Permission denied" errors
Make sure you ran the finish setup script and logged out/in:
```bash
sudo /home/sam/ASWY_NexHacks-main/finish_realsense_setup.sh
# Then log out and log back in
```

## 📁 Files
- `live_arm_pointcloud_jetson.py` - Jetson visualizer (works with OpenCV)
- `live_arm_pointcloud.py` - Original visualizer (requires Open3D)
- `test_realsense.py` - Quick test script
- `finish_realsense_setup.sh` - Setup script (run with sudo)
