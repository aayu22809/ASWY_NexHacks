# Intel RealSense Camera Setup Instructions

## Current Status
✅ **Cameras Detected:**
- Intel RealSense 515 (L515)
- Intel RealSense Depth Camera 435i (D435i)

⚠️ **Issue:** Some devices show "Unknown" status - drivers need to be installed

---

## Installation Steps

### Option 1: Install Intel RealSense SDK (Recommended)

1. **Download the SDK:**
   - Go to: https://github.com/IntelRealSense/librealsense/releases/latest
   - Download: `Intel.RealSense.SDK-WIN10-*.exe` (latest version)

2. **Run the Installer:**
   - Double-click the downloaded `.exe` file
   - Follow installation wizard
   - **Important:** Choose "Install drivers" when prompted

3. **Restart Your Computer:**
   - This is crucial for drivers to load properly

4. **Verify Installation:**
   - Open "Intel RealSense Viewer" (installed with SDK)
   - Your cameras should appear and show live video

---

### Option 2: Quick Driver Fix (If SDK is already installed)

If you already have the SDK installed but drivers aren't working:

1. Open Device Manager (`devmgmt.msc`)
2. Look for devices with "Unknown" status under "Camera" or "USB devices"
3. Right-click each → "Update Driver"
4. Choose "Search automatically for drivers"
5. Restart computer

---

## After Driver Installation

Once drivers are installed, run:

```bash
# Activate the virtual environment
.venv\Scripts\activate

# Check if cameras are detected
python check_camera.py

# If successful, run the main script
python live_arm_pointcloud.py
```

---

## Controls When Script is Running

- **Q / ESC**: Quit application
- **S**: Save current point cloud to `.ply` file
- **M**: Generate mesh snapshot (Poisson reconstruction)

---

## Tips for Best Results

1. **Good Lighting:** Ensure the area is well-lit
2. **Clean Background:** White or plain background works best
3. **Distance:** Keep hand 20-90 cm from camera
4. **Avoid Reflections:** No shiny or reflective surfaces
5. **Steady Position:** Keep hand relatively still for cleaner scans

---

## Need Help?

If issues persist:
1. Check Device Manager for any devices with yellow warning icons
2. Try different USB 3.0 ports
3. Update Windows USB drivers
4. Visit: https://dev.intelrealsense.com/docs for detailed documentation

