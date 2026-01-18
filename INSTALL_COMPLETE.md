# ✅ Installation Complete!

All dependencies for the MLX90640 HTTP server are now installed.

## What Was Installed

### System Packages (via apt)
- ✅ python3-flask
- ✅ python3-flask-cors
- ✅ python3-gevent
- ✅ python3-gevent-websocket

### Python Packages (via pip --break-system-packages)
- ✅ adafruit-circuitpython-mlx90640
- ✅ adafruit-blinka
- ✅ numpy (already installed)
- ✅ All related dependencies

## Ready to Run!

Start the HTTP server:

```bash
cd /home/aayushya/ASWY_NexHacks
python3 tests/test_mlx90640_http.py
```

The server will:
1. Initialize the MLX90640 thermal camera
2. Start HTTP server on port 5000
3. Display your Pi's IP address
4. Stream thermal data via WebSocket

## Access the Stream

### Quick Test (Built-in Page)
```
http://<pi-ip-address>:5000/
```

### React Webapp
1. Configure webapp (one-time):
   ```bash
   cd plasma-path-planner
   # Edit this file and replace with your Pi's IP:
   nano .env.local
   ```
   
   Add:
   ```
   VITE_WS_URL=ws://192.168.1.100:5000
   VITE_API_URL=http://192.168.1.100:5000
   ```

2. Start webapp:
   ```bash
   npm run dev
   ```

3. Open `http://localhost:5173` → Thermal Monitor page

## Troubleshooting

If the server fails to start, check:

1. **I2C enabled?**
   ```bash
   sudo raspi-config
   # Interface Options → I2C → Enable
   ```

2. **Sensor connected?**
   ```bash
   sudo i2cdetect -y 1
   # Should show 0x33
   ```

3. **Wiring correct?**
   - VCC → 3.3V (Pin 1)
   - GND → GND (Pin 6)
   - SDA → GPIO2 (Pin 3)
   - SCL → GPIO3 (Pin 5)

## Next Steps

See complete guides:
- `THERMAL_QUICKSTART.md` - Quick start guide
- `plasma-path-planner/WIFI_SETUP.md` - Webapp configuration
- `tests/README.md` - All test scripts
- `INSTALLATION_FIX.md` - Details about the installation method

Happy thermal imaging! 🔥📷

