#!/usr/bin/env python3
"""
MLX90640 Thermal Camera HTTP Server Test Script

This script creates an HTTP server that streams MLX90640 thermal camera data
over WebSocket and REST API, accessible from any device on the same WiFi network.

Hardware Connections:
- VCC → Pi 3.3V (Pin 1)
- GND → Pi GND (Pin 6)
- SDA → Pi SDA1 (GPIO2, Pin 3)
- SCL → Pi SCL1 (GPIO3, Pin 5)

Usage:
    python3 tests/test_mlx90640_http.py
    python3 tests/test_mlx90640_http.py --host 0.0.0.0 --port 5000

Access:
    From Pi: http://localhost:5000
    From network: http://<pi-ip-address>:5000
    
Find Pi's IP: hostname -I

Dependencies:
    sudo apt-get install python3-flask python3-flask-cors
"""

import sys
import time
import json
import socket
import argparse
from datetime import datetime
from threading import Lock
from pathlib import Path

# Add project root to path to import backend modules
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

try:
    from flask import Flask, jsonify, render_template_string, request
    from flask_cors import CORS
except ImportError as e:
    print(f"[ERROR] Failed to import Flask dependencies: {e}")
    print("\nInstall required packages:")
    print("  sudo apt-get install python3-flask python3-flask-cors")
    sys.exit(1)

try:
    from backend.sensors.mlx90640 import MLX90640Sensor
except ImportError as e:
    print(f"[ERROR] Failed to import MLX90640Sensor: {e}")
    print("\nMake sure you're running from the project root and dependencies are installed:")
    print("  pip install adafruit-circuitpython-mlx90640 adafruit-blinka numpy")
    sys.exit(1)

# Global sensor instance
mlx_sensor = None
sensor_lock = Lock()
sensor_error = None

# Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Statistics
stats = {
    'frames_sent': 0,
    'start_time': time.time(),
    'last_frame_time': None,
    'connections': 0,
}


def get_local_ip():
    """Get local IP address of the Pi."""
    try:
        # Connect to external server to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


def initialize_sensor():
    """Initialize the MLX90640 sensor."""
    global mlx_sensor, sensor_error
    
    print("[INFO] Initializing MLX90640 sensor...")
    
    try:
        mlx_sensor = MLX90640Sensor()
        sensor_error = None
        print("[OK] MLX90640 sensor initialized successfully!")
        return True
    except Exception as e:
        sensor_error = str(e)
        print(f"[ERROR] Failed to initialize sensor: {e}")
        print("\nTroubleshooting:")
        print("  1. Check I2C is enabled: sudo raspi-config → Interface Options → I2C")
        print("  2. Verify wiring connections")
        print("  3. Check sensor is powered (3.3V)")
        print("  4. Verify I2C address: sudo i2cdetect -y 1")
        return False


def read_thermal_data():
    """Read thermal data from sensor with error handling."""
    global mlx_sensor, sensor_error
    
    if mlx_sensor is None:
        return None, "Sensor not initialized"
    
    try:
        with sensor_lock:
            frame = mlx_sensor.read_frame()
            max_temp = mlx_sensor.get_max_temp()
            min_temp = float(frame.min())
            mean_temp = float(frame.mean())
            
        return {
            'thermal': frame.tolist(),
            'max_temp': float(max_temp),
            'min_temp': min_temp,
            'mean_temp': mean_temp,
            'obstacle': False,  # Not using IR sensor in this test
            'timestamp': datetime.now().isoformat(),
        }, None
        
    except Exception as e:
        error_msg = f"Failed to read sensor: {str(e)}"
        sensor_error = error_msg
        return None, error_msg


# ============================================================================
# REST API Endpoints
# ============================================================================

@app.route('/')
def index():
    """Serve built-in HTML test page."""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/health')
def health():
    """Health check endpoint."""
    elapsed = time.time() - stats['start_time']
    frame_rate = stats['frames_sent'] / elapsed if elapsed > 0 else 0
    
    return jsonify({
        'status': 'healthy' if mlx_sensor is not None else 'error',
        'sensor_initialized': mlx_sensor is not None,
        'sensor_error': sensor_error,
        'uptime_seconds': elapsed,
        'frames_sent': stats['frames_sent'],
        'frame_rate': round(frame_rate, 2),
        'active_connections': stats['connections'],
    })


@app.route('/api/thermal')
def get_thermal():
    """Get single thermal frame via REST API."""
    data, error = read_thermal_data()
    
    if error:
        return jsonify({'error': error}), 500
    
    stats['frames_sent'] += 1
    stats['last_frame_time'] = time.time()
    
    return jsonify(data)


@app.route('/api/thermal/stats')
def get_thermal_stats():
    """Get temperature statistics only (no full frame)."""
    data, error = read_thermal_data()
    
    if error:
        return jsonify({'error': error}), 500
    
    # Return only statistics
    return jsonify({
        'max_temp': data['max_temp'],
        'min_temp': data['min_temp'],
        'mean_temp': data['mean_temp'],
        'timestamp': data['timestamp'],
    })


# ============================================================================
# WebSocket Handler Function
# ============================================================================

def handle_websocket(environ, start_response):
    """Handle WebSocket connections."""
    ws = environ.get('wsgi.websocket')
    
    if not ws:
        start_response('400 Bad Request', [('Content-Type', 'text/plain')])
        return [b'WebSocket connection required']
    
    stats['connections'] += 1
    print(f"[WebSocket] Client connected (total: {stats['connections']})")
    
    try:
        while True:
            # Read thermal data
            print(f"[WebSocket] Reading thermal data...")
            data, error = read_thermal_data()
            
            if error:
                # Send error message
                print(f"[WebSocket] Error reading sensor: {error}")
                ws.send(json.dumps({
                    'error': error,
                    'timestamp': datetime.now().isoformat(),
                }))
                time.sleep(1)
                continue
            
            # Send data
            print(f"[WebSocket] Sending thermal data (max_temp={data.get('max_temp', 'N/A')}°C)...")
            ws.send(json.dumps(data))
            stats['frames_sent'] += 1
            stats['last_frame_time'] = time.time()
            print(f"[WebSocket] Data sent successfully (frame #{stats['frames_sent']})")
            
            # Stream at ~4Hz (matches sensor refresh rate)
            time.sleep(0.25)
            
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        stats['connections'] -= 1
        print(f"[WebSocket] Client disconnected (remaining: {stats['connections']})")
    
    return []


# Middleware to route WebSocket requests
def websocket_app(environ, start_response):
    """WSGI middleware for WebSocket routing."""
    path = environ.get('PATH_INFO', '')
    
    # Handle WebSocket requests
    if path == '/ws/stream' and 'wsgi.websocket' in environ:
        return handle_websocket(environ, start_response)
    
    # Pass other requests to Flask
    return app(environ, start_response)


# ============================================================================
# Embedded HTML Test Page
# ============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MLX90640 Thermal Camera Stream</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #fff;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .subtitle {
            text-align: center;
            margin-bottom: 30px;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .grid {
            display: grid;
            grid-template-columns: 1fr 350px;
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            color: #333;
        }
        .heatmap-container {
            position: relative;
            background: #000;
            border-radius: 8px;
            overflow: hidden;
        }
        #heatmapCanvas {
            width: 100%;
            height: auto;
            display: block;
            image-rendering: auto;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
        }
        .stat-box {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .stat-label {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }
        .status {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
        }
        .status.connected {
            background: #10b981;
            color: white;
        }
        .status.disconnected {
            background: #ef4444;
            color: white;
        }
        .status.connecting {
            background: #f59e0b;
            color: white;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        button {
            flex: 1;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        button.primary {
            background: #667eea;
            color: white;
        }
        button.primary:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        button.secondary {
            background: #e5e7eb;
            color: #333;
        }
        button.secondary:hover {
            background: #d1d5db;
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none !important;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            opacity: 0.8;
        }
        .colorbar {
            position: absolute;
            top: 20px;
            right: 20px;
            width: 30px;
            height: 200px;
            border-radius: 4px;
            border: 2px solid rgba(255,255,255,0.5);
        }
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌡️ MLX90640 Thermal Camera</h1>
        <p class="subtitle">Real-time thermal imaging via WebSocket</p>
        
        <div class="grid">
            <!-- Heatmap Display -->
            <div class="card">
                <h2 style="margin-bottom: 15px;">Live Thermal Heatmap</h2>
                <div class="heatmap-container">
                    <canvas id="heatmapCanvas" width="640" height="480"></canvas>
                    <canvas id="colorbarCanvas" class="colorbar" width="30" height="200"></canvas>
                </div>
                <div style="margin-top: 10px; text-align: center; color: #666; font-size: 0.9em;">
                    Resolution: 24×32 pixels (768 thermal sensors)
                </div>
            </div>
            
            <!-- Statistics & Controls -->
            <div class="card">
                <h2 style="margin-bottom: 15px;">Statistics</h2>
                
                <div>
                    <strong>Connection Status:</strong>
                    <span id="status" class="status disconnected">Disconnected</span>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-box">
                        <div class="stat-label">Max Temp</div>
                        <div class="stat-value" id="maxTemp">--°C</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Min Temp</div>
                        <div class="stat-value" id="minTemp">--°C</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Mean Temp</div>
                        <div class="stat-value" id="meanTemp">--°C</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Frame Rate</div>
                        <div class="stat-value" id="frameRate">--Hz</div>
                    </div>
                </div>
                
                <div class="controls">
                    <button id="connectBtn" class="primary" onclick="connect()">Connect</button>
                    <button id="disconnectBtn" class="secondary" onclick="disconnect()" disabled>Disconnect</button>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 8px; font-size: 0.9em;">
                    <strong>Access from other devices:</strong><br>
                    <code style="background: #e5e7eb; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-top: 5px;">
                        ws://{{ local_ip }}:{{ port }}/ws/stream
                    </code>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>MLX90640 Thermal Camera Test Server</p>
            <p style="font-size: 0.9em; margin-top: 5px;">Flask + WebSocket + Canvas Visualization</p>
        </div>
    </div>
    
    <script>
        let ws = null;
        let frameCount = 0;
        let startTime = null;
        const canvas = document.getElementById('heatmapCanvas');
        const ctx = canvas.getContext('2d');
        const colorbarCanvas = document.getElementById('colorbarCanvas');
        const colorbarCtx = colorbarCanvas.getContext('2d');
        
        // Jet colormap function
        function jetColormap(value) {
            value = Math.max(0, Math.min(1, value));
            let r, g, b;
            
            if (value < 0.125) {
                r = 0; g = 0; b = 0.5 + (value / 0.125) * 0.5;
            } else if (value < 0.375) {
                r = 0; g = (value - 0.125) / 0.25; b = 1;
            } else if (value < 0.625) {
                r = (value - 0.375) / 0.25; g = 1; b = 1 - (value - 0.375) / 0.25;
            } else if (value < 0.875) {
                r = 1; g = 1 - (value - 0.625) / 0.25; b = 0;
            } else {
                r = 1 - (value - 0.875) / 0.125 * 0.5; g = 0; b = 0;
            }
            
            return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
        }
        
        // Draw colorbar
        function drawColorbar() {
            const gradient = colorbarCtx.createLinearGradient(0, colorbarCanvas.height, 0, 0);
            for (let i = 0; i <= 10; i++) {
                const value = i / 10;
                const [r, g, b] = jetColormap(value);
                gradient.addColorStop(value, `rgb(${r},${g},${b})`);
            }
            colorbarCtx.fillStyle = gradient;
            colorbarCtx.fillRect(0, 0, colorbarCanvas.width, colorbarCanvas.height);
        }
        
        drawColorbar();
        
        // Update status UI
        function updateStatus(status) {
            const statusEl = document.getElementById('status');
            const connectBtn = document.getElementById('connectBtn');
            const disconnectBtn = document.getElementById('disconnectBtn');
            
            statusEl.className = 'status ' + status;
            statusEl.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            
            connectBtn.disabled = (status === 'connected' || status === 'connecting');
            disconnectBtn.disabled = (status === 'disconnected');
        }
        
        // Connect to WebSocket
        function connect() {
            if (ws) return;
            
            updateStatus('connecting');
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/stream`;
            
            ws = new WebSocket(wsUrl);
            frameCount = 0;
            startTime = Date.now();
            
            ws.onopen = () => {
                console.log('Connected to thermal stream');
                updateStatus('connected');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                
                if (data.error) {
                    console.error('Sensor error:', data.error);
                    return;
                }
                
                // Update frame count
                frameCount++;
                const elapsed = (Date.now() - startTime) / 1000;
                const frameRate = frameCount / elapsed;
                
                // Update statistics
                document.getElementById('maxTemp').textContent = data.max_temp.toFixed(1) + '°C';
                document.getElementById('minTemp').textContent = data.min_temp.toFixed(1) + '°C';
                document.getElementById('meanTemp').textContent = data.mean_temp.toFixed(1) + '°C';
                document.getElementById('frameRate').textContent = frameRate.toFixed(1) + ' Hz';
                
                // Draw heatmap
                drawHeatmap(data.thermal, data.min_temp, data.max_temp);
            };
            
            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                updateStatus('disconnected');
            };
            
            ws.onclose = () => {
                console.log('Disconnected from thermal stream');
                ws = null;
                updateStatus('disconnected');
            };
        }
        
        // Disconnect from WebSocket
        function disconnect() {
            if (ws) {
                ws.close();
                ws = null;
            }
            updateStatus('disconnected');
        }
        
        // Draw thermal heatmap
        function drawHeatmap(thermalData, minTemp, maxTemp) {
            const width = 32;
            const height = 24;
            const tempRange = maxTemp - minTemp;
            
            // Create ImageData
            const imageData = ctx.createImageData(width, height);
            const data = imageData.data;
            
            for (let i = 0; i < thermalData.length; i++) {
                const temp = thermalData[i];
                const normalized = tempRange > 0 ? (temp - minTemp) / tempRange : 0.5;
                const [r, g, b] = jetColormap(normalized);
                
                const pixelIndex = i * 4;
                data[pixelIndex] = r;
                data[pixelIndex + 1] = g;
                data[pixelIndex + 2] = b;
                data[pixelIndex + 3] = 255;
            }
            
            // Draw to offscreen canvas first
            const offscreen = document.createElement('canvas');
            offscreen.width = width;
            offscreen.height = height;
            const offscreenCtx = offscreen.getContext('2d');
            offscreenCtx.putImageData(imageData, 0, 0);
            
            // Scale up with smooth interpolation
            ctx.imageSmoothingEnabled = true;
            ctx.imageSmoothingQuality = 'high';
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(offscreen, 0, 0, canvas.width, canvas.height);
        }
        
        // Auto-connect on page load
        window.addEventListener('load', () => {
            setTimeout(connect, 500);
        });
    </script>
</body>
</html>
"""


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='MLX90640 HTTP Server Test')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host to bind to (default: 0.0.0.0 for all interfaces)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to bind to (default: 5000)')
    
    args = parser.parse_args()
    
    # Banner
    print("=" * 70)
    print("MLX90640 Thermal Camera HTTP Server")
    print("=" * 70)
    
    # Initialize sensor
    if not initialize_sensor():
        print("\n[WARN] Sensor initialization failed, but server will start anyway.")
        print("[WARN] Check sensor connection and try accessing /api/health for details.")
    
    # Get local IP
    local_ip = get_local_ip()
    
    # Update HTML template with local IP
    global HTML_TEMPLATE
    HTML_TEMPLATE = HTML_TEMPLATE.replace('{{ local_ip }}', local_ip)
    HTML_TEMPLATE = HTML_TEMPLATE.replace('{{ port }}', str(args.port))
    
    # Server info
    print(f"\n[INFO] Starting server...")
    print(f"[INFO] Host: {args.host}")
    print(f"[INFO] Port: {args.port}")
    print(f"\n[OK] Server is running!")
    print(f"\n📱 Access from this device:")
    print(f"   http://localhost:{args.port}/")
    print(f"\n🌐 Access from other devices on the same network:")
    print(f"   http://{local_ip}:{args.port}/")
    print(f"\n🔌 WebSocket endpoint:")
    print(f"   ws://{local_ip}:{args.port}/ws/stream")
    print(f"\n📊 API endpoints:")
    print(f"   GET  http://{local_ip}:{args.port}/api/health")
    print(f"   GET  http://{local_ip}:{args.port}/api/thermal")
    print(f"   GET  http://{local_ip}:{args.port}/api/thermal/stats")
    print("\n" + "=" * 70)
    print("Press Ctrl+C to stop the server")
    print("=" * 70 + "\n")
    
    # Start Flask server with WebSocket support
    try:
        from gevent import pywsgi
        from geventwebsocket.handler import WebSocketHandler
        
        server = pywsgi.WSGIServer(
            (args.host, args.port),
            websocket_app,  # Use WebSocket middleware instead of Flask app directly
            handler_class=WebSocketHandler
        )
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n[INFO] Shutting down server...")
    finally:
        # Cleanup sensor
        if mlx_sensor:
            try:
                mlx_sensor.close()
                print("[OK] Sensor closed successfully")
            except Exception:
                pass
        print("[INFO] Server stopped")


if __name__ == "__main__":
    main()

