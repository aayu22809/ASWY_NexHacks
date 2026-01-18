# MLX90640 Thermal Camera - Quick Start Guide

Get your thermal camera streaming to a web browser in 5 minutes!

## Step 1: Install Dependencies (First Time Only)

On your Raspberry Pi:

```bash
cd /home/aayushya/ASWY_NexHacks

# Install HTTP server dependencies (system packages)
sudo apt-get install python3-flask python3-flask-cors

# Install MLX90640 sensor dependencies
pip3 install --break-system-packages adafruit-circuitpython-mlx90640 adafruit-blinka numpy

# Or use a virtual environment (recommended for sensor libs):
# python3 -m venv venv
# source venv/bin/activate
# pip install adafruit-circuitpython-mlx90640 adafruit-blinka numpy
```

## Step 2: Find Your Pi's IP Address

On your Raspberry Pi:

```bash
hostname -I
```

Example output: `192.168.1.100` ← This is your Pi's IP address

## Step 3: Start the HTTP Server

On your Raspberry Pi (make sure you're in the project root):

```bash
cd /home/aayushya/ASWY_NexHacks
python3 tests/test_mlx90640_http.py
```

> **Important:** Always run from `/home/aayushya/ASWY_NexHacks` directory!

You'll see output like:

```
======================================================================
MLX90640 Thermal Camera HTTP Server
======================================================================

[OK] MLX90640 sensor initialized successfully!
[OK] Server is running!

📱 Access from this device:
   http://localhost:5000/

🌐 Access from other devices on the same network:
   http://192.168.1.100:5000/

🔌 WebSocket endpoint:
   ws://192.168.1.100:5000/ws/stream
======================================================================
```

**Keep this terminal open!** The server needs to keep running.

## Step 4: Access from Your Laptop/Phone

You have two options:

### Option A: Quick Test (Built-in HTML Page)

Just open a browser on any device on the same WiFi network:

```
http://192.168.1.100:5000/
```

(Replace `192.168.1.100` with your actual Pi IP)

You should see:
- Live thermal heatmap (color-coded)
- Temperature statistics (min/max/mean)
- Connection status
- Frame rate counter

✅ **If this works, your hardware and server are working perfectly!**

### Option B: Full React Webapp

For the complete interface with more features:

1. **Configure the webapp** (one-time setup):

   On your laptop, create a file `plasma-path-planner/.env.local`:

   ```bash
   cd /home/aayushya/ASWY_NexHacks/plasma-path-planner
   
   # Create config file with your Pi's IP
   cat > .env.local << EOF
   VITE_API_URL=http://192.168.1.100:5000
   VITE_WS_URL=ws://192.168.1.100:5000
   EOF
   ```

   **Replace `192.168.1.100` with your actual Pi IP!**

2. **Start the webapp**:

   ```bash
   cd plasma-path-planner
   npm run dev
   ```

3. **Open in browser**:

   ```
   http://localhost:5173
   ```

4. **Navigate to "Thermal Monitor" page**

5. Click **"Connect"** button

You should see the thermal camera stream with:
- High-quality thermal heatmap visualization
- Detailed statistics panel
- Connection controls
- Frame rate monitoring

## Troubleshooting

### "Cannot connect" or page won't load

1. **Verify same WiFi network:**
   - Pi and laptop must be on the same WiFi network
   - Check Pi: `ip addr show wlan0 | grep "inet "`
   - Check laptop network settings

2. **Test connectivity:**
   ```bash
   # From your laptop:
   ping 192.168.1.100
   
   # Test the API:
   curl http://192.168.1.100:5000/api/health
   ```

3. **Check firewall:**
   ```bash
   # On Pi:
   sudo ufw allow 5000/tcp
   ```

### "Sensor initialization failed"

1. **Check I2C is enabled:**
   ```bash
   sudo raspi-config
   # Interface Options → I2C → Enable
   sudo reboot
   ```

2. **Verify sensor is detected:**
   ```bash
   sudo i2cdetect -y 1
   # Should show 0x33
   ```

3. **Check wiring:**
   - VCC → 3.3V (Pin 1)
   - GND → GND (Pin 6)
   - SDA → GPIO2 (Pin 3)
   - SCL → GPIO3 (Pin 5)

### Server starts but no data

- Wait 5 seconds after starting for sensor to stabilize
- Check browser console for JavaScript errors
- Try refreshing the page
- Check the server terminal for error messages

## What Next?

Once it's working:

- ✅ Test the built-in HTML page first (easiest)
- ✅ Then try the React webapp (full features)
- ✅ Connect from multiple devices (phone, tablet, etc.)
- ✅ Use the custom URL input in webapp if you don't want to edit `.env.local`
- ✅ Check `plasma-path-planner/WIFI_SETUP.md` for advanced configuration

## API Reference

If you want to integrate the thermal data into your own application:

**WebSocket (recommended for real-time):**
```javascript
const ws = new WebSocket('ws://192.168.1.100:5000/ws/stream');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // data.thermal: array of 768 temperatures (24x32)
  // data.max_temp, data.min_temp, data.mean_temp
};
```

**REST API (polling):**
```bash
# Health check
curl http://192.168.1.100:5000/api/health

# Single thermal frame
curl http://192.168.1.100:5000/api/thermal

# Just statistics
curl http://192.168.1.100:5000/api/thermal/stats
```

## More Information

- Full test documentation: `tests/README.md`
- Webapp setup guide: `plasma-path-planner/WIFI_SETUP.md`
- Hardware setup: `SETUP_INSTRUCTIONS.md`

## Summary

```
Pi:     python3 tests/test_mlx90640_http.py
        ↓ WiFi Network
Laptop: Open http://192.168.1.100:5000/ in browser
        ✨ See live thermal camera! ✨
```

Enjoy your thermal imaging! 🔥📷

