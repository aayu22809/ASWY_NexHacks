"""G-code execution engine with safety monitoring."""

import asyncio
import re
import time
from enum import Enum
from typing import Optional, Callable, Dict, Any

from backend.config import THERMAL_MAX_SAFE_TEMP
from backend.sensors.mlx90640 import MLX90640Sensor
from backend.sensors.ir_obstacle import IRObstacleSensor


class ExecutionState(Enum):
    """Execution state machine states."""
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class ExecutionEngine:
    """G-code execution engine with safety monitoring."""
    
    def __init__(self):
        """Initialize execution engine."""
        self.state = ExecutionState.IDLE
        self.current_position = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.system_status = "SAFE"
        self._gcode_lines = []
        self._current_line_index = 0
        self._task: Optional[asyncio.Task] = None
        self._position_callback: Optional[Callable] = None
        self._status_callback: Optional[Callable] = None
    
    def get_state(self) -> str:
        """Get current execution state."""
        return self.state.value
    
    def get_system_status(self) -> str:
        """Get current system safety status."""
        return self.system_status
    
    def get_current_position(self) -> Optional[Dict[str, float]]:
        """Get current robot position."""
        if self.state == ExecutionState.IDLE:
            return None
        return self.current_position.copy()
    
    def set_position_callback(self, callback: Callable):
        """Set callback for position updates."""
        self._position_callback = callback
    
    def set_status_callback(self, callback: Callable):
        """Set callback for status updates."""
        self._status_callback = callback
    
    def start(
        self,
        gcode_path: str,
        mlx_sensor: Optional[MLX90640Sensor],
        ir_sensor: Optional[IRObstacleSensor],
        websocket_manager,
    ):
        """
        Start execution of G-code file.
        
        Args:
            gcode_path: Path to G-code file
            mlx_sensor: MLX90640 thermal sensor instance
            ir_sensor: IR obstacle sensor instance
            websocket_manager: WebSocket connection manager for broadcasting
        """
        if self.state != ExecutionState.IDLE:
            raise RuntimeError(f"Cannot start: current state is {self.state.value}")
        
        # Load G-code
        try:
            with open(gcode_path, 'r') as f:
                self._gcode_lines = [line.strip() for line in f if line.strip() and not line.strip().startswith(';')]
        except Exception as e:
            raise RuntimeError(f"Failed to load G-code: {e}")
        
        self._current_line_index = 0
        self.state = ExecutionState.RUNNING
        self.system_status = "SAFE"
        
        # Start execution task
        self._task = asyncio.create_task(
            self._execute_loop(mlx_sensor, ir_sensor, websocket_manager)
        )
    
    def pause(self):
        """Pause execution."""
        if self.state == ExecutionState.RUNNING:
            self.state = ExecutionState.PAUSED
            if self._status_callback:
                self._status_callback("PAUSED")
    
    def resume(self):
        """Resume execution."""
        if self.state == ExecutionState.PAUSED:
            self.state = ExecutionState.RUNNING
            if self._status_callback:
                self._status_callback("RUNNING")
    
    def stop(self):
        """Emergency stop execution."""
        self.state = ExecutionState.STOPPED
        self.system_status = "STOP"
        
        if self._task:
            self._task.cancel()
            self._task = None
        
        if self._status_callback:
            self._status_callback("STOPPED")
    
    async def _execute_loop(
        self,
        mlx_sensor: Optional[MLX90640Sensor],
        ir_sensor: Optional[IRObstacleSensor],
        websocket_manager,
    ):
        """Main execution loop."""
        try:
            while self._current_line_index < len(self._gcode_lines):
                # Check for stop
                if self.state == ExecutionState.STOPPED:
                    break
                
                # Wait if paused
                while self.state == ExecutionState.PAUSED:
                    await asyncio.sleep(0.1)
                    if self.state == ExecutionState.STOPPED:
                        return
                
                # Safety checks with ThermalSafetyAgent
                obstacle_detected = False
                thermal_action = "safe"
                
                if ir_sensor:
                    try:
                        obstacle_detected = ir_sensor.is_blocked()
                    except Exception:
                        pass
                
                # Use ThermalSafetyAgent if available
                if mlx_sensor:
                    try:
                        from software.thermal_predictor import ThermalSafetyAgent
                        
                        max_temp = mlx_sensor.get_max_temp()
                        
                        # Create safety agent state
                        state = {
                            "current_temp": float(max_temp),
                            "planned_speed": 50.0,  # Default feed rate
                            "plasma_power": 80.0,
                            "standoff_mm": 10.0,
                            "tissue_type": 0,
                            "timestamp_s": time.time(),
                        }
                        
                        # Get recommendation from safety agent
                        safety_agent = ThermalSafetyAgent(max_temp_c=THERMAL_MAX_SAFE_TEMP)
                        recommendation = safety_agent.recommend_action(state)
                        thermal_action = recommendation["action"]
                        
                        # Update system status based on action
                        if thermal_action == "stop":
                            self.system_status = "STOP"
                        elif thermal_action in ["slow", "cool", "backoff"]:
                            self.system_status = "SLOW"
                        else:
                            self.system_status = "SAFE"
                        
                    except Exception as e:
                        print(f"[WARN] Safety agent error: {e}")
                        # Fallback to simple threshold check
                        try:
                            max_temp = mlx_sensor.get_max_temp()
                            if max_temp > THERMAL_MAX_SAFE_TEMP:
                                thermal_action = "stop"
                                self.system_status = "STOP"
                        except Exception:
                            pass
                
                # Emergency stop conditions
                if obstacle_detected:
                    self.system_status = "STOP"
                    self.state = ExecutionState.STOPPED
                    await websocket_manager.broadcast({
                        "type": "safety",
                        "status": "STOP",
                        "reason": "Obstacle detected",
                    })
                    break
                
                if thermal_action == "stop":
                    self.system_status = "STOP"
                    self.state = ExecutionState.STOPPED
                    await websocket_manager.broadcast({
                        "type": "safety",
                        "status": "STOP",
                        "reason": f"Temperature safety threshold exceeded",
                    })
                    break
                
                # Slow down if recommended
                if thermal_action in ["slow", "cool", "backoff"]:
                    # Reduce feed rate by 50% for slow actions
                    # This would be applied to the next movement
                    pass
                
                # Parse and execute G-code line
                line = self._gcode_lines[self._current_line_index]
                await self._execute_line(line)
                
                # Update position callback
                if self._position_callback:
                    self._position_callback(self.current_position)
                
                # Broadcast position update
                await websocket_manager.broadcast({
                    "type": "position",
                    "position": self.current_position,
                    "line": self._current_line_index + 1,
                    "total": len(self._gcode_lines),
                })
                
                self._current_line_index += 1
                
                # Simulate movement delay (adjust based on feed rate)
                await asyncio.sleep(0.1)
            
            # Execution complete
            if self.state != ExecutionState.STOPPED:
                self.state = ExecutionState.IDLE
                self.system_status = "SAFE"
                if self._status_callback:
                    self._status_callback("IDLE")
        
        except asyncio.CancelledError:
            self.state = ExecutionState.STOPPED
        except Exception as e:
            self.state = ExecutionState.ERROR
            self.system_status = "STOP"
            print(f"[ERROR] Execution error: {e}")
    
    async def _execute_line(self, line: str):
        """Execute a single G-code line."""
        # Parse G-code commands
        # G0/G1: Linear move
        # F: Feed rate
        # X, Y, Z: Coordinates
        
        if line.startswith('G0') or line.startswith('G1'):
            # Extract coordinates
            x_match = re.search(r'X([\d.-]+)', line)
            y_match = re.search(r'Y([\d.-]+)', line)
            z_match = re.search(r'Z([\d.-]+)', line)
            
            if x_match:
                self.current_position["x"] = float(x_match.group(1))
            if y_match:
                self.current_position["y"] = float(y_match.group(1))
            if z_match:
                self.current_position["z"] = float(z_match.group(1))
        
        # Other commands (M30, etc.) are ignored for simulation
