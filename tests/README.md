# Sensor Test Scripts

This directory contains standalone test scripts for verifying hardware connectivity and basic functionality of the sensors before integration into the main system.

## Prerequisites

### Hardware Setup

Before running the tests, ensure your sensors are properly connected to the Raspberry Pi:

#### MLX90640 Thermal Camera

| MLX90640 Pin | Raspberry Pi Connection |
|--------------|------------------------|
| VCC          | 3.3V (Pin 1)           |
| GND          | GND (Pin 6)            |
| SDA          | SDA1 / GPIO2 (Pin 3)   |
| SCL          | SCL1 / GPIO3 (Pin 5)    |

**Note:** The MLX90640 uses I2C communication. Ensure I2C is enabled on your Raspberry Pi:
```bash
sudo raspi-config
# Navigate to: Interface Options → I2C → Enable
```

#### IR Reflective Obstacle Sensor

| IR Sensor Pin | Raspberry Pi Connection |
|---------------|-------------------------|
| VCC           | 5V or 3.3V (check sensor spec) |
| GND           | GND                     |
| OUT           | GPIO 17 (Pin 11)        |

**Note:** The default GPIO pin is 17, but you can change it using the `--pin` argument.

### Software Dependencies

Install required Python packages:

```bash
# From project root directory
pip install -r backend/requirements.txt

# Or install individually:
pip install adafruit-circuitpython-mlx90640 adafruit-blinka numpy RPi.GPIO

# For GUI visualization (optional):
pip install matplotlib
```

### GPIO Permissions

For the IR sensor test, you may need GPIO access permissions:

**Option 1: Run with sudo** (simplest for testing)
```bash
sudo python3 tests/test_ir_sensor.py
```

**Option 2: Add user to gpio group** (recommended for development)
```bash
sudo usermod -a -G gpio $USER
# Log out and back in for changes to take effect
```

## Running the Tests

### MLX90640 Thermal Camera Test

There are two versions available: **ASCII terminal version** and **GUI version** with colored heatmap.

#### ASCII Terminal Version

Test the thermal camera with ASCII visualization (works over SSH without X11):

```bash
# From project root directory
python3 -m tests.test_mlx90640
# Or: PYTHONPATH=. python3 tests/test_mlx90640.py
```

**What it does:**
- Initializes I2C bus and detects MLX90640 sensor
- Continuously captures thermal frames at 4 Hz
- Displays temperature statistics (min/max/mean)
- Shows ASCII heatmap visualization (32x24 array)
- Runs until Ctrl+C is pressed

**Expected Output:**
```
============================================================
MLX90640 Thermal Camera Test - Frame #42
Time: 14:23:15
============================================================

Temperature Statistics:
  Min:   22.45 °C
  Max:   25.67 °C
  Mean:  23.89 °C
  Range:   3.22 °C

Performance:
  Frame Rate: 2.00 Hz
  Elapsed Time: 21.0 s

Thermal Heatmap (32x24):
  ----------------------------------------
  . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
  ...
```

#### GUI Version (Colored Heatmap)

Test the thermal camera with a graphical window showing a colored heatmap:

```bash
# From project root directory
python3 -m tests.test_mlx90640_gui
# Or: PYTHONPATH=. python3 tests/test_mlx90640_gui.py
```

**Requirements:**
- Matplotlib installed: `pip install matplotlib`
- Display available (desktop environment or X11 forwarding for SSH)

**What it does:**
- Initializes I2C bus and detects MLX90640 sensor
- Opens a matplotlib window with real-time colored heatmap
- Uses Jet colormap (blue → green → yellow → red)
- Displays live temperature statistics overlay
- Shows color bar with temperature scale
- Updates at 4 Hz refresh rate
- Runs until window is closed or Ctrl+C is pressed

**Features:**
- Real-time colored thermal visualization (32x24 pixels, interpolated)
- Temperature color bar on the right side
- Statistics text overlay (top-left corner)
- Frame rate and elapsed time display
- Visual warnings when temperature exceeds thresholds (38°C and 40°C)

**For SSH with X11 Forwarding:**
```bash
# Connect with X11 forwarding enabled
ssh -X pi@raspberrypi.local

# Then run the GUI test
python3 -m tests.test_mlx90640_gui
```

**Note:** The GUI version provides much better visualization than ASCII, but requires a display. Use the ASCII version for headless systems or SSH without X11.

### IR Reflective Obstacle Sensor Test

Test the IR obstacle sensor with real-time state monitoring:

```bash
# From project root directory
python3 tests/test_ir_sensor.py

# Or with custom GPIO pin:
python3 tests/test_ir_sensor.py --pin 18

# Or with custom polling rate:
python3 tests/test_ir_sensor.py --rate 20.0
```

**Command-line options:**
- `--pin PIN`: GPIO pin number (default: 17)
- `--rate RATE`: Polling rate in Hz (default: 10.0)

**What it does:**
- Initializes GPIO pin 17 as input
- Continuously polls sensor state (10 Hz default)
- Detects state changes (CLEAR ↔ BLOCKED)
- Displays real-time status with timestamps
- Logs events when obstacles are detected/cleared
- Runs until Ctrl+C is pressed

**Expected Output:**
```
============================================================
IR Obstacle Sensor Test - GPIO 17
Time: 14:23:15
============================================================

Current Status:
  ✓ CLEAR
  State: PATH CLEAR

Statistics:
  Total Polls: 1250
  State Changes: 3
  Elapsed Time: 125.0 s
  Poll Rate: 10.0 Hz

Recent Events (last 5):
  14:22:10.123: CLEAR → BLOCKED
  14:22:11.456: BLOCKED → CLEAR
  14:22:15.789: CLEAR → BLOCKED
```

## Troubleshooting

### MLX90640 Issues

**Problem: "Failed to initialize sensor" or "I2C not detected"**

Solutions:
1. **Check I2C is enabled:**
   ```bash
   sudo raspi-config
   # Interface Options → I2C → Enable
   sudo reboot
   ```

2. **Verify I2C bus is working:**
   ```bash
   sudo i2cdetect -y 1
   # Should show 0x33 in the output (MLX90640 address)
   ```

3. **Check wiring connections:**
   - Verify VCC is connected to 3.3V (not 5V!)
   - Ensure GND is properly connected
   - Check SDA/SCL are not swapped

4. **Verify sensor power:**
   - MLX90640 requires 3.3V power supply
   - Check voltage with multimeter if possible

**Problem: "Failed to read frame" errors**

Solutions:
- Ensure sensor is stable (wait a few seconds after power-on)
- Check I2C bus speed (may need to reduce refresh rate)
- Verify no loose connections

**Problem: GUI version shows "No module named 'backend'"**

Solutions:
1. **Run as a module from project root:**
   ```bash
   python3 -m tests.test_mlx90640_gui
   ```

2. **Or set PYTHONPATH:**
   ```bash
   PYTHONPATH=. python3 tests/test_mlx90640_gui.py
   ```

3. **Verify you're in the project root directory:**
   ```bash
   pwd
   # Should show: /path/to/ASWY_NexHacks
   ```

**Problem: GUI window doesn't appear (SSH)**

Solutions:
- Enable X11 forwarding: `ssh -X pi@raspberrypi.local`
- Check DISPLAY variable: `echo $DISPLAY` (should not be empty)
- Install X11 server on your local machine (XQuartz for Mac, Xming for Windows)
- For headless systems, use the ASCII version instead: `test_mlx90640.py`

### IR Sensor Issues

**Problem: "Permission denied" or "GPIO library not available"**

Solutions:
1. **Run with sudo:**
   ```bash
   sudo python3 tests/test_ir_sensor.py
   ```

2. **Add user to gpio group:**
   ```bash
   sudo usermod -a -G gpio $USER
   # Log out and back in
   ```

3. **Verify RPi.GPIO is installed:**
   ```bash
   pip install RPi.GPIO
   ```

**Problem: Sensor always shows BLOCKED or always shows CLEAR**

Solutions:
1. **Check wiring:**
   - Verify OUT pin is connected to correct GPIO pin
   - Check power supply (5V or 3.3V depending on sensor)
   - Ensure GND is connected

2. **Test GPIO manually:**
   ```bash
   # Using wiringPi (if installed):
   gpio readall
   
   # Or check GPIO state:
   gpio -g mode 17 in
   gpio -g read 17
   ```

3. **Verify sensor logic:**
   - Some sensors are active LOW (LOW = blocked)
   - Some sensors are active HIGH (HIGH = blocked)
   - Check sensor datasheet for logic level

**Problem: No state changes detected**

Solutions:
- Wave hand slowly in front of sensor
- Check sensor detection range (usually 2-30cm)
- Verify sensor is powered and LED is on (if applicable)
- Test with different objects/materials

## Integration Notes

These test scripts are designed to be standalone for hardware verification. Once sensors are confirmed working:

1. **MLX90640:** The driver is already integrated in `backend/sensors/mlx90640.py` and used by the FastAPI backend.

2. **IR Sensor:** The driver is already integrated in `backend/sensors/ir_obstacle.py` and used by the FastAPI backend.

3. **Backend Integration:** Both sensors are initialized in `backend/api.py` and stream data via WebSocket at `/ws/sensors`.

## File Structure

```
tests/
├── README.md                  # This file
├── test_mlx90640.py           # MLX90640 thermal camera test (ASCII)
├── test_mlx90640_gui.py       # MLX90640 thermal camera test (GUI)
└── test_ir_sensor.py          # IR obstacle sensor test
```

## Next Steps

After verifying sensors work correctly:

1. Test sensors individually using these scripts
2. Verify sensors appear in backend WebSocket stream
3. Check frontend displays sensor data correctly
4. Test safety integration (thermal thresholds, obstacle detection)

For full system testing, refer to the main project README.
