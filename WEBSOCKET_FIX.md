# WebSocket Connection Fix

## What Was Wrong

The original implementation used `flask-sockets` which wasn't properly handling the WebSocket handshake with gevent-websocket, causing these errors:

```
werkzeug.routing.exceptions.WebsocketMismatch: 400 Bad Request
```

## What Was Fixed

1. **Removed `flask-sockets` dependency** - No longer needed
2. **Direct WebSocket access** - Now accessing WebSocket directly from WSGI environ
3. **Simplified implementation** - Using gevent-websocket's built-in integration
4. **Updated documentation** - Removed references to `flask-sockets`

## Changes Made

### Code Changes
- Removed `from flask_sockets import Sockets`
- Removed `sockets = Sockets(app)`
- Changed `@sockets.route('/ws/stream')` to `@app.route('/ws/stream')`
- WebSocket now accessed via `request.environ.get('wsgi.websocket')`

### Documentation Updates
- Updated all installation commands (no more `python3-flask-sockets`)
- Fixed dependency lists in README files

## How to Test

### 1. Start the Server

```bash
cd /home/aayushya/ASWY_NexHacks
python3 tests/test_mlx90640_http.py
```

You should see:
```
✅ [OK] MLX90640 sensor initialized successfully!
✅ [OK] Server is running!
🔌 WebSocket endpoint: ws://172.26.43.207:5000/ws/stream
```

### 2. Test REST API First

From another terminal or your laptop:

```bash
# Health check
curl http://172.26.43.207:5000/api/health

# Should return JSON with sensor status
```

### 3. Test Built-in HTML Page

Open browser on your laptop/phone:

```
http://172.26.43.207:5000/
```

This page has JavaScript that connects to the WebSocket. You should see:
- ✅ "Connected" status (green)
- ✅ Live thermal heatmap updating
- ✅ Temperature statistics changing
- ✅ Frame rate counter

### 4. Test React Webapp

```bash
cd plasma-path-planner

# Make sure .env.local exists with your Pi's IP
cat .env.local
# Should show:
# VITE_WS_URL=ws://172.26.43.207:5000
# VITE_API_URL=http://172.26.43.207:5000

# Start webapp
npm run dev

# Open http://localhost:5173
# Go to Thermal Monitor page
# Click "Connect"
```

You should see:
- ✅ Connection status shows "Connected"
- ✅ Live thermal heatmap
- ✅ Temperature statistics
- ✅ Frame rate display

## Expected Server Output

When WebSocket connects successfully:

```
[WebSocket] Client connected (total: 1)
```

When it disconnects:

```
[WebSocket] Client disconnected (remaining: 0)
```

## If It Still Doesn't Work

### Check Browser Console

Open browser Developer Tools (F12) → Console tab. Look for:

**Good (should see):**
```javascript
[ThermalWS] Connected to ws://172.26.43.207:5000/ws/stream
```

**Bad (shouldn't see):**
```javascript
WebSocket connection error
Failed to connect after multiple attempts
```

### Check Server Terminal

**Good (should see):**
```
[WebSocket] Client connected (total: 1)
```

**Bad (shouldn't see):**
```
WebsocketMismatch: 400 Bad Request
Traceback...
```

### Verify Dependencies

```bash
# Check gevent-websocket is installed
python3 -c "from geventwebsocket.handler import WebSocketHandler; print('✅ OK')"

# Check Flask is installed
python3 -c "from flask import Flask; print('✅ OK')"

# Check MLX90640 is installed
python3 -c "from backend.sensors.mlx90640 import MLX90640Sensor; print('✅ OK')"
```

All three should print `✅ OK`.

### Test WebSocket Manually

You can test the WebSocket connection using a simple script:

```python
from websocket import create_connection
import json

ws = create_connection("ws://172.26.43.207:5000/ws/stream")
print("✅ Connected!")

# Receive one frame
result = ws.recv()
data = json.loads(result)
print(f"Max temp: {data['max_temp']}°C")
print(f"Min temp: {data['min_temp']}°C")

ws.close()
```

Save as `test_ws.py` and run:
```bash
pip3 install --break-system-packages websocket-client
python3 test_ws.py
```

## Technical Details

### How It Works Now

1. **Server starts** with gevent pywsgi.WSGIServer
2. **WebSocketHandler** intercepts WebSocket upgrade requests
3. **WebSocket object** is placed in `environ['wsgi.websocket']`
4. **Flask route** `/ws/stream` accesses it and streams data
5. **Client** (browser/React) receives JSON data every 250ms

### Data Flow

```
Client Browser
  ↓ (WebSocket handshake)
gevent WebSocketHandler
  ↓ (creates WebSocket object)
WSGI environ['wsgi.websocket']
  ↓ (accessed by)
Flask route handler
  ↓ (reads from)
MLX90640 Sensor
  ↓ (sends JSON)
Client Browser (displays heatmap)
```

## Additional Notes

- WebSocket connections are persistent (stay open until closed)
- Multiple clients can connect simultaneously
- Each client gets the same data stream
- Connection automatically retries if it drops (webapp has auto-reconnect)
- Server sends data at ~4 Hz (matches sensor refresh rate)

## Still Having Issues?

1. Make sure you're running from project root: `/home/aayushya/ASWY_NexHacks`
2. Check both devices are on same WiFi network
3. Verify firewall isn't blocking port 5000
4. Try accessing the built-in HTML page first before the React webapp
5. Check browser console and server terminal for specific error messages

The fix should resolve the `WebsocketMismatch` errors and allow proper WebSocket connections!


