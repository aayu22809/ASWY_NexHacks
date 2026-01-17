# Setup Instructions

## Prerequisites

### Hardware Requirements
- Intel RealSense L515 camera
- USB 3.0 port
- Python 3.10+ (3.12 recommended)
- 8GB+ RAM
- Windows/Linux/macOS

### Software Requirements
- Python 3.10, 3.11, or 3.12
- Node.js 18+ (for frontend)
- Git

## Backend Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd ASWY_NexHacks
```

### 2. Create Python Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Package (Development Mode)

```bash
pip install -e .
```

### 5. Verify Intel RealSense Camera

```bash
python -c "import pyrealsense2 as rs; print('RealSense SDK installed successfully')"
```

## Frontend Setup

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Node Dependencies

```bash
npm install
```

### 3. Start Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Configuration

### Camera Configuration

Edit `config/camera_defaults.yaml` to adjust camera settings:

```yaml
color:
  width: 640
  height: 480
  fps: 30

depth:
  width: 640
  height: 480
  fps: 30
```

### Path Planning Configuration

Edit `config/path_planning_defaults.yaml`:

```yaml
standoff_distance: 5.0  # mm
line_spacing: 4.0       # mm
feed_rate: 50.0         # mm/min
rapid_rate: 200.0       # mm/min
```

### Safety Configuration

Edit `config/safety_thresholds.yaml`:

```yaml
max_temperature: 40.0   # °C
max_dwell_time: 10.0    # seconds
min_standoff: 5.0       # mm
```

## Troubleshooting

### RealSense Camera Not Detected

**Windows:**
1. Check Device Manager for proper driver installation
2. Try different USB 3.0 ports
3. Update firmware using Intel RealSense Viewer

**Linux:**
1. Add user to plugdev group:
   ```bash
   sudo usermod -a -G plugdev $USER
   ```
2. Install udev rules:
   ```bash
   sudo cp config/99-realsense-libusb.rules /etc/udev/rules.d/
   sudo udevadm control --reload-rules && sudo udevadm trigger
   ```
3. Log out and log back in

### Python Import Errors

If you see import errors, make sure you've installed the package:

```bash
pip install -e .
```

### Open3D Visualization Issues

If Open3D visualization doesn't work:
- Make sure you're not in a headless environment
- Try updating graphics drivers
- On Linux, install: `sudo apt-get install libgl1-mesa-glx`

## Testing Installation

### Test Scanning Module

```bash
python run_scanner.py --test
```

### Test Path Planning

```bash
python run_planner.py --demo
```

### Test Visualization

```bash
python run_visualizer.py
```

### Run Full Pipeline

```bash
python run_full_pipeline.py --demo
```

## Next Steps

See [USAGE.md](USAGE.md) for how to use the system.

