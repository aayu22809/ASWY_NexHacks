# MLX90640 Thermal Monitor - Implementation Complete ✓

## 🎉 What's Been Implemented

The thermal heatmap visualization is now fully integrated into your webapp! Here's what was created:

### New Components & Files

1. **Type Definitions** (`src/types/thermal.ts`)
   - TypeScript interfaces for thermal data, statistics, and WebSocket state

2. **API Configuration** (`src/config/api.ts`)
   - Centralized configuration for WebSocket connections
   - Auto-reconnection settings
   - Environment variable support

3. **WebSocket Hook** (`src/hooks/useThermalWebSocket.ts`)
   - Custom React hook for managing WebSocket connections
   - Automatic reconnection with exponential backoff
   - Real-time statistics computation (min/max/mean temps, frame rate)
   - Connection state management

4. **Thermal Heatmap Component** (`src/components/ThermalHeatmap.tsx`)
   - Canvas-based rendering of 24×32 thermal array
   - Jet colormap (blue → cyan → green → yellow → red)
   - Smooth interpolation for better visualization
   - Dynamic color scaling
   - Integrated colorbar legend

5. **Statistics Component** (`src/components/ThermalStats.tsx`)
   - Real-time temperature display (min/max/mean/range)
   - Safety status indicators (green/yellow/red)
   - Frame rate monitoring
   - Connection status badges
   - Warning alerts at 38°C and 40°C thresholds

6. **Thermal Monitor Page** (`src/pages/ThermalMonitor.tsx`)
   - Complete monitoring interface
   - Connection controls (connect/disconnect/reconnect)
   - Custom WebSocket URL input
   - SSH tunnel setup instructions
   - Backend information panel

7. **Updated Navigation** (`src/components/TopNav.tsx`, `src/App.tsx`)
   - New "Thermal Monitor" navigation button
   - Route added at `/thermal`
   - Smooth navigation between Path Planning and Thermal Monitor

---

## 🚀 How to Use

### Step 1: Set Up Environment Variables

Create a `.env.local` file in the `plasma-path-planner` directory:

```bash
cd plasma-path-planner
cat > .env.local << 'EOF'
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
EOF
```

### Step 2: Start the Backend on Raspberry Pi

On your Raspberry Pi, make sure the backend is running:

```bash
cd ~/ASWY_NexHacks
source venv/bin/activate
uvicorn backend.api:app --host 0.0.0.0 --port 8000
```

Verify the MLX90640 sensor is working:
```bash
python3 -m tests.test_mlx90640
```

### Step 3: Establish SSH Tunnel

On your development machine, create an SSH tunnel to forward the Pi's backend port:

```bash
ssh -L 8000:localhost:8000 pi@raspberrypi.local
```

This command forwards port 8000 from the Pi to your local machine. Keep this terminal window open!

### Step 4: Start the Webapp

In a new terminal on your development machine:

```bash
cd plasma-path-planner
npm install  # If you haven't already
npm run dev
```

### Step 5: Access Thermal Monitor

1. Open your browser to `http://localhost:5173` (or the port Vite provides)
2. Click the **"Thermal Monitor"** button in the top navigation
3. The webapp will automatically attempt to connect to the WebSocket
4. You should see the thermal heatmap updating in real-time at ~4-5 FPS!

---

## 🎨 Features

### Real-Time Heatmap
- **Resolution**: 24×32 pixels (768 temperature readings)
- **Update Rate**: ~4-5 Hz (matches backend stream)
- **Colormap**: Jet (blue for cold, red for hot)
- **Auto-Scaling**: Color range automatically adjusts to frame min/max temperatures

### Live Statistics
- **Maximum Temperature**: Displayed in red
- **Minimum Temperature**: Displayed in blue
- **Mean Temperature**: Average of all readings
- **Temperature Range**: Difference between max and min
- **Frame Rate**: Real-time FPS monitoring
- **Frame Count**: Total frames received

### Safety Monitoring
- **Safe**: Green indicator (< 38°C)
- **Warning**: Yellow indicator (38-40°C)
- **Critical**: Red indicator (> 40°C)
- Automatic alerts when thresholds are exceeded

### Connection Management
- **Auto-Connect**: Automatically connects on page load
- **Manual Controls**: Connect, disconnect, and reconnect buttons
- **Custom URL**: Option to specify different WebSocket endpoints
- **Reconnection**: Automatic reconnection with exponential backoff (up to 5 attempts)
- **Status Indicators**: Clear visual feedback of connection state

---

## 🔧 Troubleshooting

### "Connection failed" Error

**Problem**: Webapp cannot connect to the backend

**Solutions**:
1. Verify SSH tunnel is active:
   ```bash
   # Test the tunnel
   curl http://localhost:8000/health
   ```
   
2. Check backend is running on Pi:
   ```bash
   ssh pi@raspberrypi.local
   ps aux | grep uvicorn
   ```

3. Verify WebSocket endpoint:
   - Open browser console (F12)
   - Look for WebSocket connection logs
   - Should connect to `ws://localhost:8000/ws/sensors`

### "No Thermal Data" Message

**Problem**: Connected but no heatmap displayed

**Solutions**:
1. Check MLX90640 sensor on Pi:
   ```bash
   cd ~/ASWY_NexHacks
   python3 -m tests.test_mlx90640
   ```

2. Verify I2C is enabled:
   ```bash
   sudo raspi-config
   # Navigate to: Interface Options → I2C → Enable
   ```

3. Check sensor wiring:
   - VCC → Pi 3.3V (Pin 1)
   - GND → Pi GND (Pin 6)
   - SDA → Pi SDA1 (GPIO2, Pin 3)
   - SCL → Pi SCL1 (GPIO3, Pin 5)

### Low Frame Rate

**Problem**: Heatmap updates slowly

**Solutions**:
1. Check network latency between dev machine and Pi
2. Verify SSH tunnel isn't dropping packets
3. Consider direct connection if on same network:
   ```bash
   # In .env.local
   VITE_WS_URL=ws://raspberrypi.local:8000
   ```

### Reconnection Issues

**Problem**: Connection keeps dropping

**Solutions**:
1. Increase reconnection attempts in `src/config/api.ts`:
   ```typescript
   reconnect: {
     maxAttempts: 10,  // Increase from 5
     delayMs: 2000,
     backoffMultiplier: 1.5,
   }
   ```

2. Check backend logs for errors:
   ```bash
   # On Pi, check uvicorn output
   ```

---

## 🎯 Advanced Usage

### Custom WebSocket URL

In the Thermal Monitor page, you can specify a custom WebSocket URL:

1. Enter URL in the "Custom WebSocket URL" field
2. Format: `ws://hostname:port/ws/sensors`
3. Click "Connect"

Examples:
- Local tunnel: `ws://localhost:8000/ws/sensors`
- Direct Pi: `ws://raspberrypi.local:8000/ws/sensors`
- Custom IP: `ws://192.168.1.100:8000/ws/sensors`

### Fixed Temperature Scale

To use a fixed temperature range instead of auto-scaling, modify `ThermalHeatmap` usage in `ThermalMonitor.tsx`:

```tsx
<ThermalHeatmap
  thermalData={data?.thermal ?? null}
  width={640}
  height={480}
  minTemp={20}  // Fixed minimum
  maxTemp={45}  // Fixed maximum
  showColorbar={true}
/>
```

### Adjusting Update Rate

The backend streams at ~4-5 Hz. To change this, modify the sensor initialization on the Pi in `backend/sensors/mlx90640.py`:

```python
# Current: 4 Hz
self._mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ

# For faster updates (if sensor supports it):
self._mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_8_HZ
```

---

## 📊 Data Format

The WebSocket sends JSON data at each frame:

```json
{
  "thermal": [24.5, 24.6, 24.7, ..., 36.2],  // 768 values (24×32)
  "max_temp": 36.2,                          // Maximum temperature
  "obstacle": false,                         // IR obstacle sensor
  "timestamp": "2026-01-18T15:30:45.123Z"   // ISO timestamp
}
```

The thermal array is row-major ordered:
- Indices 0-31: Row 0 (top)
- Indices 32-63: Row 1
- ...
- Indices 736-767: Row 23 (bottom)

---

## 🎨 Customization

### Change Colormap

Edit `jetColormap()` function in `src/components/ThermalHeatmap.tsx` to use different colors:

```typescript
// Example: Red-Yellow-Green (inverted)
function customColormap(value: number): [number, number, number] {
  const v = Math.max(0, Math.min(1, value));
  
  if (v < 0.5) {
    // Green to yellow
    return [v * 2 * 255, 255, 0];
  } else {
    // Yellow to red
    return [255, (1 - (v - 0.5) * 2) * 255, 0];
  }
}
```

### Modify Safety Thresholds

Edit `getSafetyStatus()` in `src/components/ThermalStats.tsx`:

```typescript
if (temp >= 45.0) {  // Change critical threshold
  return { level: 'critical', ... };
} else if (temp >= 42.0) {  // Change warning threshold
  return { level: 'warning', ... };
}
```

---

## ✅ Testing Checklist

- [ ] Backend running on Pi (port 8000)
- [ ] SSH tunnel established (`ssh -L 8000:localhost:8000 pi@raspberrypi.local`)
- [ ] MLX90640 sensor connected and working
- [ ] Webapp running (`npm run dev`)
- [ ] Can navigate to Thermal Monitor page
- [ ] WebSocket connects automatically
- [ ] Heatmap displays and updates in real-time
- [ ] Statistics show correct values
- [ ] Frame rate is ~4-5 Hz
- [ ] Safety warnings appear at appropriate temperatures
- [ ] Reconnection works after disconnect

---

## 📝 Summary

Your thermal monitoring system is now complete! The integration includes:

✅ Real-time WebSocket streaming from MLX90640 sensor  
✅ Beautiful Canvas-based heatmap visualization  
✅ Live temperature statistics and safety monitoring  
✅ Automatic reconnection and error handling  
✅ Clean UI integrated with existing webapp  
✅ SSH tunnel support for remote development  

Navigate to the **Thermal Monitor** page in your webapp and start visualizing thermal data from your MLX90640 sensor!

---

## 🆘 Need Help?

If you encounter issues:

1. Check backend logs on Pi
2. Check browser console for errors (F12 → Console)
3. Verify network connectivity between dev machine and Pi
4. Test backend endpoint manually: `curl http://localhost:8000/health`
5. Review the troubleshooting section above

Happy thermal monitoring! 🌡️🔥


