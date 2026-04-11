# Cold Plasma Robot Arm - Wound Healing System

## Quick Start

```bash
./demo.sh                    # Full system (backend + frontend)
# Or manually:
source venv/bin/activate
python demo_server.py        # Backend on :8000
cd plasma-path-planner && npm run dev  # Frontend on :5173
```

## Architecture

- `backend/` - FastAPI server, sensor drivers (MLX90640 thermal, IR obstacle, RealSense depth)
- `gcodegen/` - Toolpath generation, G-code output, surface modeling
- `plasma-path-planner/` - React + TypeScript + Three.js frontend dashboard
- `demo_server.py` - Unified demo server (standalone, embeds HTML)
- `tests/` - Hardware validation scripts

## Key Commands

```bash
pip install -r requirements.txt          # All Python deps
python -m pytest tests/                  # Run tests
python backend/api.py                    # Start API server only
python gcodegen/main.py                  # Run path generation
```

## Gotchas

- Sensors auto-fallback to simulation mode when hardware not detected
- RealSense (`pyrealsense2`) is optional — imported with try/except
- Platform-specific GPIO: Jetson.GPIO vs rpi-lgpio vs RPi.GPIO
- Set `BLINKA_FORCEBOARD=JETSON_NX` on Jetson for adafruit-blinka
- Frontend expects backend on port 8000, dev server on 5173
