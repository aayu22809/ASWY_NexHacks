# System Architecture

## Overview

The Plasma Jet Path Planner follows a modular, pipeline-based architecture that processes 3D data through multiple stages to generate safe, optimized toolpaths for plasma treatment.

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     USER INTERFACE                           │
│                  (React Frontend + CLI)                      │
└────────────────────────┬─────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
┌─────────▼─────────┐         ┌────────▼──────────┐
│   SCANNING        │         │  VISUALIZATION     │
│                   │         │                    │
│ • RealSense L515  │         │ • Open3D Viewer    │
│ • Point Cloud     │         │ • Web 3D View      │
│ • Filtering       │         │ • Real-time Status │
└─────────┬─────────┘         └────────────────────┘
          │                             ▲
          │ Point Cloud                 │
          │                             │
┌─────────▼─────────┐                   │
│  PATH PLANNING    │                   │
│                   │                   │
│ • Surface Model   │                   │
│ • Wound Detection │                   │
│ • Raster Gen      │                   │
│ • G-code Export   │                   │
└─────────┬─────────┘                   │
          │                             │
          │ Toolpath                    │
          │                             │
┌─────────▼─────────┐                   │
│     SAFETY        │                   │
│                   │                   │
│ • Thermal Predict │                   │
│ • Constraint Check│                   │
│ • Safety Control  │                   │
└─────────┬─────────┘                   │
          │                             │
          │ Validated Path              │
          │                             │
┌─────────▼─────────┐                   │
│ ROBOT CONTROL     │                   │
│                   │                   │
│ • Motion Planning │                   │
│ • G-code Execute  │───────────────────┘
│ • Status Monitor  │     Feedback
└───────────────────┘
```

## Module Details

### 1. Scanning Module (`backend/scanning/`)

**Purpose**: Capture 3D point cloud data from the RealSense camera.

**Components**:
- `arm_scanner.py`: Main scanning interface
- `camera_config.py`: Camera configuration management
- `point_cloud_processor.py`: Point cloud filtering and processing

**Key Functions**:
- Initialize RealSense L515
- Apply depth filters (spatial, temporal, hole-filling)
- Align depth to color
- Generate colored point cloud
- Apply ROI filtering
- Downsample for performance

**Outputs**:
- `.ply` files: Point cloud data
- Numpy arrays: For immediate processing

### 2. Path Planning Module (`backend/path_planning/`)

**Purpose**: Generate optimal toolpaths over the scanned surface.

**Components**:
- `surface_model.py`: Surface representation and interpolation
- `raster_generator.py`: Toolpath generation
- `wound_detector.py`: Wound region identification (future)
- `gcode_exporter.py`: G-code generation (integrated in file_io)

**Key Classes**:

**SurfaceModel**:
- Uses RBF (Radial Basis Function) interpolation
- Provides smooth surface representation
- Calculates surface normals
- Handles surface queries

**RasterGenerator**:
- Creates raster (zigzag) pattern
- Maintains standoff distance
- Generates bidirectional paths
- Optimizes rapid moves

**ToolpathConfig**:
- Standoff distance
- Line spacing
- Feed rates
- Pattern parameters

### 3. Safety Module (`backend/safety/`)

**Purpose**: Ensure thermal and operational safety during treatment.

**Components**:
- `thermal_predictor.py`: Predictive thermal model
- `safety_controller.py`: Safety decision engine

**ThermalSafetyAgent**:
- Predicts tissue temperature 5 seconds ahead
- Uses linear regression on thermal history
- Recommends speed adjustments or stops
- Prevents tissue damage before it occurs

**Safety Checks**:
- Temperature threshold (default: 40°C)
- Standoff distance validation
- Dwell time limits
- Emergency stop conditions

### 4. Visualization Module (`backend/visualization/`)

**Purpose**: Interactive visualization of data and results.

**Components**:
- `interactive_viewer.py`: Tkinter-based 3D viewer
- `mesh_renderer.py`: Rendering utilities (future)

**Features**:
- Real-time point cloud display
- Toolpath preview
- Normal vector visualization
- Multiple view angles
- Export capabilities

### 5. Utilities Module (`backend/utils/`)

**Purpose**: Shared functionality across modules.

**Components**:
- `file_io.py`: File operations (JSON, CSV, G-code, PLY)
- `geometry.py`: Geometric calculations (future)
- `logger.py`: Logging utilities (future)

**ResultsManager**:
- Save/load results in JSON format
- Export G-code for robot control
- Export CSV for analysis
- Manage data persistence

### 6. Robot Control Module (`backend/robot_control/`)

**Purpose**: Interface with robot arm for execution.

**Status**: Placeholder for future implementation

**Planned Features**:
- Robot arm communication
- Motion planning
- Real-time control
- Status monitoring

## Data Flow

### 1. Scanning Phase

```
RealSense Camera → Raw Frames → Filters → Point Cloud → .ply File
```

### 2. Planning Phase

```
Point Cloud → Surface Model → Toolpath Generation → Validation → G-code
```

### 3. Execution Phase

```
G-code → Robot Controller → Motion → Thermal Monitoring → Feedback
```

## Configuration Management

All modules read from centralized YAML configuration files:

- `config/camera_defaults.yaml`: Camera settings
- `config/path_planning_defaults.yaml`: Planning parameters
- `config/safety_thresholds.yaml`: Safety limits
- `config/robot_config.yaml`: Robot parameters

## Error Handling

Each module implements:
- Input validation
- Exception handling
- Graceful degradation
- Detailed error messages
- Recovery mechanisms

## Testing Strategy

- **Unit Tests**: Individual function testing
- **Integration Tests**: Module interaction testing
- **System Tests**: End-to-end pipeline testing
- **Hardware Tests**: RealSense camera integration

## Performance Considerations

- **Scanning**: 30 FPS point cloud capture
- **Planning**: < 5 seconds for typical arm surface
- **Safety**: < 100ms prediction latency
- **Visualization**: 10-30 FPS rendering

## Future Extensions

1. **AI Wound Detection**: Automatic wound identification
2. **Multi-camera Fusion**: 360° arm scanning
3. **Adaptive Path Planning**: Real-time path adjustment
4. **Cloud Integration**: Remote monitoring and control
5. **Machine Learning**: Optimized treatment patterns

## Technology Choices

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| 3D Scanning | Intel RealSense L515 | High-quality depth, pre-calibrated |
| Surface Model | RBF Interpolation | Smooth, handles irregular spacing |
| Safety | Linear Regression | Fast, interpretable, reliable |
| Visualization | Open3D | Python-native, powerful |
| Frontend | React + Three.js | Modern, responsive, 3D capable |
| Data Format | JSON, PLY, G-code | Standard, interoperable |

## Security Considerations

- Input validation on all external data
- File path sanitization
- Safety threshold enforcement
- Emergency stop mechanisms
- Audit logging (future)

