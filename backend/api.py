"""FastAPI server for Cold Plasma Robot Arm control system."""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.config import (
    API_HOST,
    API_PORT,
    CORS_ORIGINS,
    REALSENSE_CAPTURE_DIR,
)
from backend.sensors.mlx90640 import MLX90640Sensor
from backend.sensors.ir_obstacle import IRObstacleSensor
from backend.sensors.ir_reflective import IRReflectiveSensor

# Optional RealSense support (not available on all platforms)
try:
    from backend.sensors.realsense import RealSenseCapture
    REALSENSE_AVAILABLE = True
except ImportError:
    RealSenseCapture = None
    REALSENSE_AVAILABLE = False
    print("[WARN] RealSense libraries not available. 3D scanning disabled.")

from backend.executor import ExecutionEngine

app = FastAPI(title="Cold Plasma Robot Arm API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global sensor instances
mlx_sensor: Optional[MLX90640Sensor] = None
ir_sensor: Optional[IRObstacleSensor] = None
ir_reflective_sensor: Optional[IRReflectiveSensor] = None
executor: Optional[ExecutionEngine] = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(data)
            except Exception:
                pass  # Connection may be closed

manager = ConnectionManager()


# Request/Response models
class ScanResponse(BaseModel):
    ply_path: str
    points: int
    timestamp: str


class PathConfig(BaseModel):
    standoff_distance: float = 5.0
    line_spacing: float = 3.0
    feed_rate: float = 50.0
    rapid_rate: float = 200.0
    use_bidirectional: bool = True
    points_per_line: int = 80


class PathResponse(BaseModel):
    gcode_path: str
    toolpath: list
    num_points: int
    treatment_length_mm: float


class StatusResponse(BaseModel):
    status: str
    system_status: str
    executor_state: str
    current_position: Optional[dict] = None


@app.on_event("startup")
async def startup_event():
    """Initialize sensors on startup."""
    global mlx_sensor, ir_sensor, ir_reflective_sensor, executor
    
    try:
        mlx_sensor = MLX90640Sensor()
        print("[OK] MLX90640 initialized")
    except Exception as e:
        print(f"[WARN] MLX90640 initialization failed: {e}")
        mlx_sensor = None
    
    try:
        ir_sensor = IRObstacleSensor()
        print("[OK] IR Obstacle sensor initialized")
    except Exception as e:
        print(f"[WARN] IR Obstacle sensor initialization failed: {e}")
        ir_sensor = None
    
    try:
        from backend.config import (
            IR_REFLECTIVE_GPIO_PIN,
            IR_REFLECTIVE_BASELINE_DISTANCE_MM,
            IR_REFLECTIVE_EMA_ALPHA,
            IR_REFLECTIVE_SAMPLING_RATE_HZ
        )
        ir_reflective_sensor = IRReflectiveSensor(
            gpio_pin=IR_REFLECTIVE_GPIO_PIN,
            baseline_distance_mm=IR_REFLECTIVE_BASELINE_DISTANCE_MM,
            ema_alpha=IR_REFLECTIVE_EMA_ALPHA,
            sampling_rate_hz=IR_REFLECTIVE_SAMPLING_RATE_HZ,
            use_mock=False  # Use real hardware
        )
        print("[OK] IR Reflective sensor initialized")
    except Exception as e:
        print(f"[WARN] IR Reflective sensor initialization failed: {e}")
        print("[INFO] Falling back to mock mode for testing")
        try:
            ir_reflective_sensor = IRReflectiveSensor(use_mock=True)
            print("[OK] IR Reflective sensor initialized (mock mode)")
        except Exception as mock_e:
            print(f"[WARN] Mock mode also failed: {mock_e}")
            ir_reflective_sensor = None
    
    executor = ExecutionEngine()
    print("[OK] Execution engine initialized")
    
    # Create capture directory
    Path(REALSENSE_CAPTURE_DIR).mkdir(exist_ok=True)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global mlx_sensor, ir_sensor, ir_reflective_sensor, executor
    
    if mlx_sensor:
        mlx_sensor.close()
    if ir_sensor:
        ir_sensor.close()
    if ir_reflective_sensor:
        ir_reflective_sensor.close()
    if executor:
        executor.stop()


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mlx90640": mlx_sensor is not None,
        "ir_obstacle": ir_sensor is not None,
        "ir_reflective": ir_reflective_sensor is not None,
        "executor": executor is not None,
        "realsense": REALSENSE_AVAILABLE,
    }


@app.post("/scan", response_model=ScanResponse)
async def scan_arm():
    """Trigger RealSense capture and return PLY file path."""
    if not REALSENSE_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="RealSense camera not available on this platform"
        )
    
    try:
        capture = RealSenseCapture()
        ply_path, num_points = await capture.single_capture()
        
        return ScanResponse(
            ply_path=ply_path,
            points=num_points,
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@app.post("/generate-path", response_model=PathResponse)
async def generate_path(mesh_path: str, config: PathConfig):
    """Generate toolpath from mesh file."""
    try:
        from main import SurfaceModel, RasterGenerator, ToolpathConfig, ResultsManager
        
        # Load mesh or point cloud
        import open3d as o3d
        
        # Try loading as PLY (could be mesh or point cloud)
        try:
            pcd = o3d.io.read_point_cloud(mesh_path)
            if len(pcd.points) == 0:
                # Try as mesh
                mesh = o3d.io.read_triangle_mesh(mesh_path)
                if not mesh.has_vertices():
                    raise ValueError("Invalid mesh file")
                pcd = mesh.sample_points_uniformly(number_of_points=2000)
        except Exception:
            # Fallback: try as mesh
            mesh = o3d.io.read_triangle_mesh(mesh_path)
            if not mesh.has_vertices():
                raise ValueError("Invalid mesh file")
            pcd = mesh.sample_points_uniformly(number_of_points=2000)
        
        points = np.asarray(pcd.points)
        
        # Create surface model
        surface = SurfaceModel(points, "scanned_arm")
        
        # Create toolpath config
        toolpath_config = ToolpathConfig(
            standoff_distance=config.standoff_distance,
            line_spacing=config.line_spacing,
            feed_rate=config.feed_rate,
            rapid_rate=config.rapid_rate,
            use_bidirectional=config.use_bidirectional,
            points_per_line=config.points_per_line,
            name="generated_path",
        )
        
        # Generate toolpath
        generator = RasterGenerator(surface, toolpath_config)
        toolpath = generator.generate()
        
        # Export G-code
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        gcode_path = f"toolpath_{timestamp}.gcode"
        ResultsManager.export_gcode(toolpath, gcode_path)
        
        # Calculate treatment length
        treatment_points = [pt for pt in toolpath if not pt.is_rapid]
        length = sum(
            np.linalg.norm(treatment_points[i+1].position - treatment_points[i].position)
            for i in range(len(treatment_points) - 1)
        )
        
        # Convert toolpath to JSON-serializable format
        toolpath_data = [pt.to_dict() for pt in toolpath]
        
        return PathResponse(
            gcode_path=gcode_path,
            toolpath=toolpath_data,
            num_points=len(toolpath),
            treatment_length_mm=float(length),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Path generation failed: {str(e)}")


@app.post("/start")
async def start_execution(gcode_path: str):
    """Start execution of G-code with safety monitoring."""
    if not executor:
        raise HTTPException(status_code=500, detail="Executor not initialized")
    
    try:
        executor.start(gcode_path, mlx_sensor, ir_sensor, manager)
        return {"status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Start failed: {str(e)}")


@app.post("/stop")
async def stop_execution():
    """Emergency stop execution."""
    if not executor:
        raise HTTPException(status_code=500, detail="Executor not initialized")
    
    executor.stop()
    return {"status": "stopped"}


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get current system status."""
    if not executor:
        return StatusResponse(
            status="idle",
            system_status="SAFE",
            executor_state="IDLE",
        )
    
    state = executor.get_state()
    position = executor.get_current_position()
    
    return StatusResponse(
        status="running" if state == "RUNNING" else "idle",
        system_status=executor.get_system_status(),
        executor_state=state,
        current_position=position,
    )


@app.websocket("/ws/sensors")
async def websocket_sensors(websocket: WebSocket):
    """WebSocket endpoint for real-time sensor streaming."""
    await manager.connect(websocket)
    
    try:
        while True:
            # Read sensor data
            thermal_frame = None
            max_temp = None
            obstacle_detected = False
            
            if mlx_sensor:
                try:
                    thermal_frame = mlx_sensor.read_frame()
                    max_temp = mlx_sensor.get_max_temp()
                except Exception:
                    pass
            
            if ir_sensor:
                try:
                    obstacle_detected = ir_sensor.is_blocked()
                except Exception:
                    pass
            
            # Read IR reflective sensor metrics
            ir_metrics = None
            if ir_reflective_sensor:
                try:
                    ir_metrics = ir_reflective_sensor.get_ir_metrics()
                except Exception:
                    pass
            
            # Send data
            await websocket.send_json({
                "thermal": thermal_frame.tolist() if thermal_frame is not None else None,
                "max_temp": float(max_temp) if max_temp is not None else None,
                "obstacle": obstacle_detected,
                "ir_metrics": ir_metrics,
                "timestamp": datetime.now().isoformat(),
            })
            
            # Stream at ~5Hz
            await asyncio.sleep(0.2)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)
