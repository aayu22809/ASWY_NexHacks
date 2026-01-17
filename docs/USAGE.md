# Usage Guide

## Quick Start

### Running the Complete Pipeline

The easiest way to use the system is through the main pipeline script:

```bash
python run_full_pipeline.py --demo
```

This runs a complete demo with test data.

## Individual Components

### 1. 3D Scanning

Capture a 3D point cloud of an arm:

```bash
python run_scanner.py
```

**Controls:**
- `Q` or `ESC`: Quit
- `S`: Save current point cloud
- `M`: Generate and save mesh

**Output:**
- `data/scans/pcd_YYYYMMDD_HHMMSS.ply`: Point cloud file

**Configuration:**
Edit these parameters in `backend/scanning/arm_scanner.py`:
- `Z_MIN`, `Z_MAX`: Depth range (meters)
- `VOXEL_SIZE`: Point cloud resolution (meters)
- `ROI_*`: Region of interest settings

### 2. Path Planning

Generate a toolpath from a point cloud:

```bash
python run_planner.py --input data/scans/pcd_20260117_120000.ply
```

Or run with demo surfaces:

```bash
python run_planner.py --demo
```

**Outputs:**
- `data/results/results_*.json`: Complete results
- `data/toolpaths/toolpath_*.gcode`: G-code for robot
- `data/toolpaths/toolpath_*.csv`: CSV for analysis
- `data/surfaces/surface_*.pkl`: Surface model

**Parameters:**

Edit `config/path_planning_defaults.yaml` or pass command-line arguments:

```bash
python run_planner.py \
    --input my_scan.ply \
    --standoff 5.0 \
    --spacing 4.0 \
    --feed-rate 50.0
```

### 3. Visualization

View results interactively:

```bash
python run_visualizer.py
```

**GUI Controls:**
- **Load Data**: Load JSON results or surface models
- **Display Options**: Toggle surface, toolpath, normals, rapid moves
- **View**: Change camera angle (3D, Top, Side)
- **Export**: Save as PNG, PDF, G-code, or CSV

**Keyboard Shortcuts:**
- `Ctrl+O`: Open file
- `Ctrl+S`: Save image
- `Ctrl+Q`: Quit

### 4. Safety Prediction

Test thermal safety predictions:

```bash
python -m backend.safety.thermal_predictor --predict
```

**Sample prediction:**

```python
from backend.safety.thermal_predictor import ThermalSafetyAgent

agent = ThermalSafetyAgent()

state = {
    "current_temp": 36.5,
    "planned_speed": 60.0,
    "plasma_power": 80.0,
    "standoff_mm": 10.0,
    "tissue_type": 0
}

action = agent.recommend_action(state)
print(action)
# {'action': 'safe', 'reason': 'Within safe envelope', 'predicted_temp': 37.2}
```

## Frontend Web Interface

### Start the Frontend

```bash
cd frontend
npm run dev
```

Navigate to `http://localhost:5173`

### Features

- **3D Model Viewer**: Upload and view PLY files
- **Path Preview**: Visualize generated toolpaths
- **Session Status**: Monitor pipeline progress
- **Live Controls**: Adjust parameters in real-time

### Loading Data

1. Click "Load Model" → Upload `.ply` file
2. Click "Load Path Image" → Upload path visualization
3. Or click "Load Demo" for sample data

## Common Workflows

### Workflow 1: Scan → Plan → Visualize

```bash
# Step 1: Scan arm
python run_scanner.py
# Press 'S' to save when ready

# Step 2: Generate toolpath
python run_planner.py --input data/scans/pcd_YYYYMMDD_HHMMSS.ply

# Step 3: Visualize results
python run_visualizer.py
# Load the JSON file from data/results/
```

### Workflow 2: Test with Demo Surfaces

```bash
# Generate toolpaths for all demo surfaces
python run_planner.py --demo

# Visualize results
python run_visualizer.py
```

### Workflow 3: Export for Robot

```bash
# Plan with custom parameters
python run_planner.py \
    --input my_scan.ply \
    --standoff 7.0 \
    --spacing 3.0 \
    --output my_toolpath.gcode

# The G-code is ready for robot execution
```

## Configuration Files

### Camera Configuration

`config/camera_defaults.yaml`:

```yaml
color:
  width: 640
  height: 480
  fps: 30

depth:
  width: 640
  height: 480
  fps: 30

filters:
  spatial_magnitude: 2
  spatial_alpha: 0.5
  temporal_alpha: 0.4
  temporal_delta: 20
  hole_filling_mode: 1

roi:
  enabled: true
  width_ratio: 0.6
  height_ratio: 0.6

depth_range:
  min: 0.20  # meters
  max: 0.90  # meters

voxel_size: 0.003  # meters (3mm)
```

### Path Planning Configuration

`config/path_planning_defaults.yaml`:

```yaml
standoff_distance: 5.0  # mm above surface
line_spacing: 4.0       # mm between raster lines
feed_rate: 50.0         # mm/min during treatment
rapid_rate: 200.0       # mm/min for positioning
bidirectional: true     # zigzag pattern
points_per_line: 60     # points per raster line
```

### Safety Configuration

`config/safety_thresholds.yaml`:

```yaml
thermal:
  max_temperature: 40.0      # °C
  warning_temperature: 38.0  # °C
  prediction_horizon: 5.0    # seconds

spatial:
  min_standoff: 5.0          # mm
  max_standoff: 15.0         # mm

temporal:
  max_dwell_time: 10.0       # seconds per point
  min_move_speed: 30.0       # mm/min
```

## File Formats

### Point Cloud (.ply)

Standard PLY format with XYZ coordinates and RGB colors:

```
ply
format ascii 1.0
element vertex 10000
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
0.123 0.456 0.789 255 128 64
...
```

### G-code (.gcode)

Standard G-code for CNC/robot control:

```gcode
; Plasma Jet Path Planner
G90 ; Absolute positioning
G21 ; Millimeter units
G94 ; Units per minute feed rate

F50.0
G1 X10.000 Y15.000 Z100.000
G1 X10.000 Y15.100 Z100.050
...

M30 ; Program end
```

### Results (.json)

Complete results in JSON format:

```json
{
  "metadata": {
    "surface_name": "arm_scan",
    "timestamp": "2026-01-17T12:00:00",
    "num_points": 1200,
    "treatment_length_mm": 450.5
  },
  "config": {...},
  "toolpath": [...],
  "surface_sample": [...]
}
```

## Tips and Best Practices

### Scanning Tips

1. **Lighting**: Use consistent, diffuse lighting
2. **Background**: White background works best
3. **Distance**: Keep arm 20-90cm from camera
4. **Stability**: Minimize movement during capture
5. **Coverage**: Ensure complete wound coverage

### Path Planning Tips

1. **Standoff**: 5-7mm is safe for most applications
2. **Line Spacing**: 3-4mm provides good coverage
3. **Feed Rate**: Start slow (30-50 mm/min) and optimize
4. **Bidirectional**: Enables faster coverage
5. **Margins**: 2mm margin prevents edge effects

### Safety Tips

1. **Always test** with phantoms before tissue
2. **Monitor temperature** continuously
3. **Use safety stop** if anything seems wrong
4. **Start with conservative parameters**
5. **Document all treatments** for analysis

## Troubleshooting

### Problem: Point cloud is noisy

**Solution**: 
- Increase `VOXEL_SIZE` for more downsampling
- Adjust filter parameters in camera config
- Improve lighting conditions

### Problem: Toolpath has gaps

**Solution**:
- Decrease `line_spacing`
- Increase `points_per_line`
- Check surface model quality

### Problem: Safety stops immediately

**Solution**:
- Check `max_temperature` threshold
- Verify thermal sensor calibration
- Reduce `feed_rate` or increase `standoff_distance`

### Problem: Visualization is slow

**Solution**:
- Reduce point cloud size (increase voxel size)
- Disable normal vector display
- Lower surface opacity

## Getting Help

- **Documentation**: See other docs in `docs/` folder
- **Issues**: Check existing issues or create new one
- **Examples**: See `examples/` directory (future)
- **Contact**: Reach out to ASWY NexHacks team

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system design
- Read [DEVELOPMENT.md](DEVELOPMENT.md) to contribute to the project
- Experiment with different surfaces and parameters
- Integrate with your robot arm

