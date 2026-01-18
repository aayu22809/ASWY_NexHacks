# MLX90640 HTTP Server - Complete Guide

## ✅ Installation Complete!

All dependencies have been successfully installed on your Raspberry Pi.

## What's New

### HTTP Server (`tests/test_mlx90640_http.py`)
A Flask-based server that streams MLX90640 thermal camera data over WiFi network:

- **WebSocket streaming** at `/ws/stream` (4 Hz real-time data)
- **REST API endpoints** for health checks and single frame captures
- **Built-in HTML test page** with live thermal heatmap visualization
- **CORS enabled** for cross-origin browser access
- **Auto IP detection** displays connection URLs on startup

### Your Existing React Webapp Works!
The `plasma-path-planner` webapp already has complete thermal visualization built in - just needs Pi's IP address.

## Quick Start

### 1. Start the Server on Pi

**Important:** Always run from the project root directory!

```bash
cd /home/aayushya/ASWY_NexHacks
python3 tests/test_mlx90640_http.py
```

> **Note:** The script must be run from the project root (`/home/aayushya/ASWY_NexHacks`) so it can properly import the `backend` module.

**Expected output:**
```
======================================================================
MLX90640 Thermal Camera HTTP Server
======================================================================

[OK] MLX90640 sensor initialized successfully!
[OK] Server is running!

🌐 Access from other devices on the same network:
   http://192.168.1.100:5000/

🔌 WebSocket endpoint:
   ws://192.168.1.100:5000/ws/stream
======================================================================
```

### 2. Test from Browser

Open on any device (laptop/phone/tablet) on same WiFi:
```
http://192.168.1.100:5000/
```
(Replace with your actual Pi IP)

You'll see:
- Live thermal heatmap (color-coded)
- Temperature statistics
- Frame rate counter
- Connection status

### 3. Connect React Webapp (Optional)

The full webapp has more features. To connect it:

```bash
cd plasma-path-planner

# Create config file (replace IP with your Pi's IP)
cat > .env.local << 'EOF'
VITE_WS_URL=ws://192.168.1.100:5000
VITE_API_URL=http://192.168.1.100:5000
EOF

# Start webapp
npm run dev

# Open: http://localhost:5173
# Go to "Thermal Monitor" page
```

## Architecture

```
Raspberry Pi (192.168.1.100)
├── MLX90640 Sensor (I2C)
└── HTTP Server (Port 5000)
    ├── GET  /                    → Built-in test page
    ├── GET  /api/health          → Health check
    ├── GET  /api/thermal         → Single thermal frame
    ├── GET  /api/thermal/stats   → Temperature statistics
    └── WS   /ws/stream           → Real-time streaming
         ↓
    WiFi Network
         ↓
Laptop/Phone Browser
├── Built-in HTML page (http://pi-ip:5000/)
└── React Webapp (http://localhost:5173)
```

## WebSocket Data Format

```json
{
  "thermal": [22.5, 22.7, 23.1, ...],  // 768 temperatures (24×32 grid)
  "max_temp": 28.5,
  "min_temp": 22.1,
  "mean_temp": 24.3,
  "obstacle": false,
  "timestamp": "2026-01-18T10:30:45.123Z"
}
```

Sent every 250ms (4 Hz refresh rate).

## API Examples

### Health Check
```bash
curl http://192.168.1.100:5000/api/health
```

Response:
```json
{
  "status": "healthy",
  "sensor_initialized": true,
  "uptime_seconds": 45.2,
  "frames_sent": 180,
  "frame_rate": 4.0,
  "active_connections": 2
}
```

### Get Thermal Frame
```bash
curl http://192.168.1.100:5000/api/thermal
```

### Get Statistics Only
```bash
curl http://192.168.1.100:5000/api/thermal/stats
```

### WebSocket (JavaScript)
```javascript
const ws = new WebSocket('ws://192.168.1.100:5000/ws/stream');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Max temp:', data.max_temp);
  console.log('Thermal array:', data.thermal); // 768 values
};

ws.onerror = (error) => console.error('WebSocket error:', error);
```

## Command Reference

### Start Server
```bash
python3 tests/test_mlx90640_http.py
```

### Start Server on Different Port
```bash
python3 tests/test_mlx90640_http.py --port 8080
```

### Find Pi's IP Address
```bash
hostname -I
```

### Check I2C Devices
```bash
sudo i2cdetect -y 1
# Should show 0x33 for MLX90640
```

### Test Sensor Manually
```bash
python3 tests/test_mlx90640.py  # ASCII version
python3 tests/test_mlx90640_gui.py  # GUI version (needs display)
```

## Troubleshooting

### "Cannot connect" from browser

1. **Check same WiFi network**
   ```bash
   # On Pi:
   ip addr show wlan0 | grep "inet "
   ```

2. **Ping Pi from laptop**
   ```bash
   ping 192.168.1.100
   ```

3. **Check firewall**
   ```bash
   sudo ufw allow 5000/tcp
   sudo ufw status
   ```

4. **Test REST API**
   ```bash
   curl http://192.168.1.100:5000/api/health
   ```

### "Sensor initialization failed"

1. **Enable I2C**
   ```bash
   sudo raspi-config
   # Interface Options → I2C → Enable
   sudo reboot
   ```

2. **Check sensor detected**
   ```bash
   sudo i2cdetect -y 1
   # Should show 0x33
   ```

3. **Verify wiring**
   - VCC → 3.3V (Pin 1)
   - GND → GND (Pin 6)
   - SDA → GPIO2 (Pin 3)
   - SCL → GPIO3 (Pin 5)

### CORS errors in browser console

- Server has CORS enabled by default
- Clear browser cache
- Try different browser
- Check browser dev console for details

### "Module not found" errors

All dependencies should be installed. If you see import errors:

```bash
# Reinstall Flask packages
sudo apt-get install --reinstall python3-flask python3-flask-cors python3-flask-sockets

# Reinstall sensor packages
pip3 install --break-system-packages --force-reinstall adafruit-circuitpython-mlx90640
```

## Files Created

1. **`tests/test_mlx90640_http.py`** - Main HTTP server script
2. **`THERMAL_QUICKSTART.md`** - Quick start guide
3. **`INSTALLATION_FIX.md`** - Fix for installation issues
4. **`INSTALL_COMPLETE.md`** - Installation summary
5. **`plasma-path-planner/WIFI_SETUP.md`** - Webapp configuration
6. **Updated `tests/README.md`** - Documentation

## Dependencies Installed

### System Packages (apt)
- python3-flask
- python3-flask-cors
- python3-gevent
- python3-gevent-websocket

### Python Packages (pip)
- adafruit-circuitpython-mlx90640
- adafruit-blinka
- numpy

## Advanced Usage

### Multiple Devices
Connect from multiple browsers simultaneously - all will receive the same thermal stream.

### Custom Integration
Use the WebSocket endpoint in your own applications:
- Mobile apps
- Desktop applications
- Other web services
- Data logging systems

### mDNS Support
If your network supports mDNS (most do):
```
http://raspberrypi.local:5000/
ws://raspberrypi.local:5000/ws/stream
```

No need to find IP address!

## More Documentation

- **`THERMAL_QUICKSTART.md`** - 5-minute setup guide
- **`tests/README.md`** - All test scripts documentation
- **`plasma-path-planner/WIFI_SETUP.md`** - Detailed webapp setup
- **`INSTALLATION_FIX.md`** - Understanding the installation process
- **`SETUP_INSTRUCTIONS.md`** - Hardware setup

## Support

If you encounter issues:
1. Check the troubleshooting sections above
2. Review the detailed documentation files
3. Check sensor wiring and I2C configuration
4. Verify both devices are on same WiFi network

---

**Ready to go!** 🚀 Start the server and access from any browser on your network!

