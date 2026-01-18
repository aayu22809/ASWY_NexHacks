#!/usr/bin/env python3
"""
Unified Industrial Demo Server for Cold Plasma Treatment System

Single FastAPI server combining:
- Thermal camera streaming (MLX90640)
- 3D model upload and conversion
- Toolpath generation (gcodegen)
- Embedded HTML interface
"""

# region agent log
import json
from datetime import datetime
LOG_PATH = '/Users/aayu/Workspace/developer/ASWY_NexHacks/.cursor/debug.log'
def log_debug(location, message, data=None, hypothesis_id=None):
    try:
        with open(LOG_PATH, 'a') as f:
            entry = {'location': location, 'message': message, 'data': data or {}, 'timestamp': datetime.now().isoformat(), 'sessionId': 'debug-session', 'hypothesisId': hypothesis_id}
            f.write(json.dumps(entry) + '\n')
    except: pass
log_debug('demo_server.py:1', 'Script started', {}, 'H1,H2,H4')
# endregion

import asyncio
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from threading import Lock

# region agent log
log_debug('demo_server.py:20', 'Standard imports successful', {}, 'H1,H2')
# endregion

import numpy as np

# region agent log
log_debug('demo_server.py:23', 'About to import FastAPI', {}, 'H2')
# endregion

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel

# region agent log
log_debug('demo_server.py:30', 'FastAPI imported successfully', {}, 'H2')
log_debug('demo_server.py:31', 'About to import backend modules', {}, 'H1,H4')
# endregion

# Import backend modules
from backend.model_storage import save_uploaded_model, get_model, cleanup_old_files

# region agent log
log_debug('demo_server.py:35', 'Backend modules imported successfully', {}, 'H1,H4')
# endregion

# Import sensor
try:
    from backend.sensors.mlx90640 import MLX90640Sensor
    MLX_AVAILABLE = True
    # region agent log
    log_debug('demo_server.py:40', 'MLX90640 sensor available', {}, 'H1')
    # endregion
except ImportError as e:
    MLX90640Sensor = None
    MLX_AVAILABLE = False
    # region agent log
    log_debug('demo_server.py:42', 'MLX90640 sensor not available', {'error': str(e)}, 'H1')
    # endregion
    print("[WARN] MLX90640 sensor not available")

# Import HTML template
try:
    # region agent log
    log_debug('demo_server.py:45', 'About to import HTML template', {}, 'H1,H5')
    # endregion
    from demo_server_html import HTML_TEMPLATE
    # region agent log
    log_debug('demo_server.py:47', 'HTML template imported successfully', {'template_length': len(HTML_TEMPLATE)}, 'H1,H5')
    # endregion
except ImportError as e:
    # region agent log
    log_debug('demo_server.py:49', 'HTML template import failed', {'error': str(e)}, 'H1,H5')
    # endregion
    HTML_TEMPLATE = "<html><body><h1>Error: HTML template not found</h1></body></html>"

app = FastAPI(title="Cold Plasma Treatment System", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
mlx_sensor: Optional[MLX90640Sensor] = None
sensor_lock = Lock()

# Thermal simulation state
_thermal_sim_time = 0.0


def generate_fake_thermal_data() -> dict:
    """
    Generate simulated thermal camera data for demo purposes.
    Creates a hand-shaped thermal pattern with a hotspot.
    
    Returns:
        Dict with thermal data matching MLX90640 format (768 values, 24x32)
    """
    global _thermal_sim_time
    _thermal_sim_time += 0.25  # Increment time for animation
    
    # MLX90640 is 24x32 (height x width)
    height, width = 24, 32
    thermal = np.zeros((height, width))
    
    # Base temperature (room temp)
    base_temp = 22.0
    
    # Create hand-shaped pattern
    center_x, center_y = width // 2, height // 2
    
    for y in range(height):
        for x in range(width):
            # Distance from center
            dx = (x - center_x) / width
            dy = (y - center_y) / height
            dist = np.sqrt(dx**2 + dy**2)
            
            # Hand shape: oval with fingers
            hand_shape = np.exp(-(dx**2 / 0.3**2 + dy**2 / 0.5**2))
            
            # Add hotspot (simulating wound area)
            hotspot_x = center_x + 3
            hotspot_y = center_y - 2
            hotspot_dist = np.sqrt((x - hotspot_x)**2 + (y - hotspot_y)**2)
            hotspot = np.exp(-hotspot_dist**2 / 4.0) * 8.0
            
            # Add some variation
            noise = np.random.normal(0, 0.5)
            
            # Temperature calculation
            temp = base_temp + hand_shape * 5.0 + hotspot + noise
            
            # Add time-varying component (simulates breathing/movement)
            temp += np.sin(_thermal_sim_time * 0.5) * 0.5
            
            thermal[y, x] = max(20.0, min(40.0, temp))  # Clamp to reasonable range
    
    # Flatten to 768-element array (row-major order)
    thermal_flat = thermal.flatten().tolist()
    
    return {
        "thermal": thermal_flat,
        "max_temp": float(np.max(thermal)),
        "min_temp": float(np.min(thermal)),
        "mean_temp": float(np.mean(thermal)),
        "timestamp": datetime.now().isoformat(),
    }

# WebSocket connection managers
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                pass

thermal_manager = ConnectionManager()


@app.on_event("startup")
async def startup_event():
    """Initialize sensors on startup."""
    global mlx_sensor
    
    if MLX_AVAILABLE:
        try:
            mlx_sensor = MLX90640Sensor()
            print("[OK] MLX90640 initialized")
        except Exception as e:
            print(f"[WARN] MLX90640 initialization failed: {e}")
            mlx_sensor = None
    else:
        print("[WARN] MLX90640 libraries not available")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global mlx_sensor
    if mlx_sensor:
        try:
            mlx_sensor.close()
        except Exception:
            pass


# ============================================================================
# HTML Interface
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main HTML interface."""
    return HTML_TEMPLATE


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mlx90640": mlx_sensor is not None,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/upload")
async def upload_model(file: UploadFile = File(...)):
    """Upload a 3D model file (PLY or OBJ) and get model metadata."""
    try:
        content = await file.read()
        model_id, metadata = save_uploaded_model(content, file.filename)
        cleanup_old_files()
        
        return {
            "model_id": model_id,
            "bounds": metadata["bounds"],
            "point_count": metadata["point_count"],
            "filename": metadata["filename"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")


@app.get("/api/models/{model_id}")
async def get_model_file(model_id: str):
    """Get model file (PLY format) by model_id."""
    model_path = get_model(model_id)
    if not model_path or not model_path.exists():
        raise HTTPException(status_code=404, detail="Model not found")
    
    return FileResponse(
        str(model_path),
        media_type="application/octet-stream",
        filename=f"{model_id}.ply"
    )


@app.get("/api/load-demo-hand")
async def load_demo_hand():
    """Load the demo hand model (Rigged Hand1.obj)."""
    demo_path = Path("gcodegen/Rigged Hand1.obj")
    
    if not demo_path.exists():
        raise HTTPException(status_code=404, detail="Demo hand file not found at gcodegen/Rigged Hand1.obj")
    
    try:
        with open(demo_path, 'rb') as f:
            content = f.read()
        
        model_id, metadata = save_uploaded_model(content, "Rigged Hand1.obj")
        
        return {
            "model_id": model_id,
            "bounds": metadata["bounds"],
            "point_count": metadata["point_count"],
            "filename": metadata["filename"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load demo hand: {str(e)}")


class RunGcodegenRequest(BaseModel):
    config: Optional[dict] = None


@app.post("/api/run-gcodegen")
async def run_gcodegen(request: RunGcodegenRequest):
    """Run gcodegen/main.py via subprocess."""
    try:
        # Change to gcodegen directory
        gcodegen_dir = Path(__file__).parent / "gcodegen"
        if not gcodegen_dir.exists():
            raise HTTPException(status_code=404, detail="gcodegen directory not found")
        
        # Build command
        python_cmd = sys.executable
        main_script = gcodegen_dir / "main.py"
        
        if not main_script.exists():
            raise HTTPException(status_code=404, detail="gcodegen/main.py not found")
        
        # Run in background (non-blocking)
        # Note: For a real implementation, you might want to stream output via WebSocket
        process = subprocess.Popen(
            [python_cmd, str(main_script)],
            cwd=str(gcodegen_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Don't wait for completion, return immediately
        return {
            "success": True,
            "message": f"G-code generation started (PID: {process.pid})",
            "pid": process.pid
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run gcodegen: {str(e)}")


@app.post("/api/open-visualizer")
async def open_visualizer():
    """Launch gcodegen/interactivevisualizer.py as separate window."""
    try:
        gcodegen_dir = Path(__file__).parent / "gcodegen"
        visualizer_script = gcodegen_dir / "interactivevisualizer.py"
        
        if not visualizer_script.exists():
            raise HTTPException(status_code=404, detail="gcodegen/interactivevisualizer.py not found")
        
        # Launch in separate process (detached on Unix, new console on Windows)
        python_cmd = sys.executable
        
        if sys.platform == "win32":
            # Windows: Create new console window
            subprocess.Popen(
                [python_cmd, str(visualizer_script)],
                cwd=str(gcodegen_dir),
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Unix: Detach from parent process
            subprocess.Popen(
                [python_cmd, str(visualizer_script)],
                cwd=str(gcodegen_dir),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        
        return {
            "success": True,
            "message": "Visualizer window opened"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open visualizer: {str(e)}")




# ============================================================================
# WebSocket Endpoints
# ============================================================================

@app.websocket("/ws/thermal")
async def websocket_thermal(websocket: WebSocket):
    """WebSocket endpoint for thermal camera streaming."""
    await thermal_manager.connect(websocket)
    
    try:
        while True:
            if mlx_sensor:
                try:
                    with sensor_lock:
                        frame = mlx_sensor.read_frame()
                        max_temp = mlx_sensor.get_max_temp()
                        min_temp = float(frame.min())
                        mean_temp = float(frame.mean())
                    
                    await websocket.send_json({
                        "thermal": frame.tolist(),
                        "max_temp": float(max_temp),
                        "min_temp": min_temp,
                        "mean_temp": mean_temp,
                        "timestamp": datetime.now().isoformat(),
                    })
                except Exception as e:
                    await websocket.send_json({
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    })
            else:
                # Use simulated thermal data for demo
                fake_data = generate_fake_thermal_data()
                await websocket.send_json(fake_data)
            
            # Stream at ~4Hz
            await asyncio.sleep(0.25)
    
    except WebSocketDisconnect:
        thermal_manager.disconnect(websocket)
    except Exception as e:
        print(f"Thermal WebSocket error: {e}")
        thermal_manager.disconnect(websocket)




# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # region agent log
    log_debug('demo_server.py:__main__', 'Main block reached', {}, 'H1,H2')
    # endregion
    
    print("=" * 70)
    print("Cold Plasma Treatment System - Unified Demo Server")
    print("=" * 70)
    print(f"\n[INFO] Starting server on http://0.0.0.0:8000")
    print(f"[INFO] Open http://localhost:8000 in your browser")
    print("\n" + "=" * 70)
    
    # region agent log
    log_debug('demo_server.py:__main__', 'About to start uvicorn', {'host': '0.0.0.0', 'port': 8000}, 'H3')
    # endregion
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        # region agent log
        log_debug('demo_server.py:__main__', 'Uvicorn start failed', {'error': str(e), 'error_type': type(e).__name__}, 'H3')
        # endregion
        print(f"[ERROR] Failed to start server: {e}")
        raise
