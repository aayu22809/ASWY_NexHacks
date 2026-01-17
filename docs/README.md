# Plasma Jet Path Planner

## Overview

This project implements an intelligent plasma jet path planning system for wound healing applications. The system combines 3D scanning, path planning, thermal safety monitoring, and visualization to safely apply cold atmospheric plasma (CAP) treatment to biological tissue.

## Key Features

- **3D Scanning**: Real-time arm scanning using Intel RealSense L515 camera
- **Path Planning**: Automatic toolpath generation with raster pattern coverage
- **Thermal Safety**: Predictive thermal monitoring to prevent tissue damage
- **Visualization**: Interactive 3D visualization of surfaces and toolpaths
- **G-code Export**: Export toolpaths for robot arm execution
- **Web Interface**: Modern React-based frontend for monitoring and control

## System Architecture

The system follows a modular architecture with clear separation of concerns:

```
┌─────────────┐
│   Scanning  │  ← Intel RealSense L515
└──────┬──────┘
       │ Point Cloud
┌──────▼──────┐
│ Path Planning│  ← Surface Modeling + Raster Generation
└──────┬──────┘
       │ Toolpath
┌──────▼──────┐
│   Safety    │  ← Thermal Prediction
└──────┬──────┘
       │ Validated Path
┌──────▼──────┐
│Robot Control│  ← G-code Execution
└──────┬──────┘
       │ Status
┌──────▼──────┐
│Visualization│  ← Live Monitoring
└─────────────┘
```

## Project Structure

```
ASWY_NexHacks/
├── backend/              # Python backend modules
│   ├── scanning/        # 3D scanning with RealSense
│   ├── path_planning/   # Toolpath generation
│   ├── safety/          # Thermal safety system
│   ├── visualization/   # Interactive visualization
│   ├── utils/           # Shared utilities
│   └── robot_control/   # Robot arm integration
├── frontend/            # React web interface
├── config/              # Configuration files
├── data/                # Generated data and outputs
│   ├── scans/          # Point cloud captures
│   ├── surfaces/       # Surface models
│   ├── toolpaths/      # G-code files
│   └── results/        # JSON results
├── docs/                # Documentation
└── tests/              # Test suites
```

## Quick Start

1. **Installation**: See [SETUP.md](SETUP.md)
2. **Usage**: See [USAGE.md](USAGE.md)
3. **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
4. **Development**: See [DEVELOPMENT.md](DEVELOPMENT.md)

## Workflow

1. **Scan**: Capture 3D point cloud of arm using RealSense camera
2. **Detect**: Identify wound region (manual or automatic)
3. **Plan**: Generate safe toolpath with optimal coverage
4. **Validate**: Check thermal safety constraints
5. **Execute**: Send G-code to robot arm
6. **Monitor**: Track progress and safety metrics in real-time

## Technology Stack

**Backend (Python):**
- NumPy, SciPy: Scientific computing
- Open3D: Point cloud processing
- pyrealsense2: Camera integration
- RBF interpolation: Surface modeling

**Frontend (TypeScript/React):**
- React + Vite: UI framework
- Three.js: 3D visualization
- shadcn/ui: Component library
- TailwindCSS: Styling

## Safety Features

- **Predictive thermal model**: Prevents overheating before it occurs
- **Standoff distance control**: Maintains safe plasma-to-tissue distance
- **Real-time monitoring**: Continuous safety checks during treatment
- **Emergency stop**: Immediate halt on safety violation

## License

Copyright © 2026 ASWY NexHacks Team

## Contact

For questions or collaboration, please contact the ASWY NexHacks team.

