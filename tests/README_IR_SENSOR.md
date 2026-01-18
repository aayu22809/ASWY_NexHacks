# IR Reflective Sensor Documentation

## Overview

The IR Reflective Sensor system provides continuous moisture detection, drying trend analysis, and surface roughness metrics for AI-driven CAP (Cold Atmospheric Plasma) wound treatment decisions. It uses analog reflectance measurements to track hydration levels and surface conditions in real-time.

## Hardware Setup

### Wiring to Jetson Orin Nano (Digital GPIO Mode)

**Note:** Jetson Orin Nano does NOT have native ADC on the GPIO header. The sensor operates in **digital GPIO mode**.

| IR Sensor Pin | Jetson Connection | Pin Number |
|---------------|-------------------|------------|
| VCC           | 3.3V              | Pin 1 or 17|
| GND           | GND               | Pin 6      |
| DO (Digital Out) | GPIO17        | Pin 11     |

**Digital Mode Operation:**
- **LOW (0):** Wet/detected (high moisture)
- **HIGH (1):** Dry/clear (low moisture)
- Sensor outputs digital signal based on reflectance threshold

### Wiring to Raspberry Pi

Raspberry Pi can use either GPIO digital mode (same as Jetson) or ADC if available:

**Digital GPIO Mode (Recommended):**
| IR Sensor Pin | Pi Connection | Pin Number |
|---------------|---------------|------------|
| VCC           | 3.3V          | Pin 1 or 17|
| GND           | GND           | Pin 6      |
| DO            | GPIO17        | Pin 11     |

**ADC Mode (Future - requires ADS1115):**
- Connect analog out → ADS1115 analog input
- Connect ADS1115 I2C → Pi I2C bus
- Requires ADS1115 I2C ADC module

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install numpy scipy matplotlib

# Or from project root
pip install -r backend/requirements.txt
```

### 2. Basic Usage

```python
from backend.sensors.ir_reflective import IRReflectiveSensor

# Initialize sensor (uses mock data if hardware not available)
# For Jetson: Uses GPIO digital mode automatically
# For Raspberry Pi: Uses GPIO digital mode (can be extended for ADC)
sensor = IRReflectiveSensor(
    gpio_pin=17,  # GPIO17 (BCM numbering)
    baseline_distance_mm=10.0,
    sampling_rate_hz=20.0
)

# Read metrics
metrics = sensor.compute_metrics()
print(f"Moisture Index: {metrics['mi']:.3f}")
print(f"Drying Rate: {metrics['drying_rate']:.4f} /sec")
print(f"Roughness: {metrics['roughness']:.4f}")
print(f"Digital Value: {metrics['raw_digital']} (0=wet, 1=dry)")
```

### 3. Calibration

Before using the sensor, calibrate it with dry and wet phantom samples:

```bash
python3 -m tests.calibrate_ir
```

The calibration script will:
1. Prompt you to place sensor 10mm above dry phantom
2. Record baseline dry value (should be HIGH/1 in digital mode)
3. Prompt you to place sensor 10mm above wet phantom
4. Record baseline wet value (should be LOW/0 in digital mode)
5. Verify digital thresholds

**Digital Mode Notes:**
- Dry surface should read HIGH (1)
- Wet surface should read LOW (0)
- If readings are inverted, check sensor wiring or adjust threshold

### 4. Live Visualization

Start the live matplotlib dashboard:

```bash
# For Jetson: Ensure DISPLAY is set or use VNC
export DISPLAY=:0  # Or use VNC/remote desktop
python3 -m tests.test_ir_reflective_gui
```

**Jetson Matplotlib Setup:**
- Backend is automatically set to `TkAgg` for compatibility
- If GUI doesn't appear, check DISPLAY variable
- For SSH: Use X11 forwarding: `ssh -X user@jetson`
- Alternative: Use VNC or remote desktop

This displays:
- Raw digital value over time (0=wet, 1=dry)
- Moisture Index trend
- Drying rate with threshold markers
- Roughness index

## Metrics Explained

### Moisture Index (MI)

**Range:** 0.0 (dry) to 1.0 (wet)

**Formula:** `MI = 1 - normalized_reflectance`

**Interpretation:**
- **0.0 - 0.3:** Dry surface (safe zone, green)
- **0.3 - 0.7:** Moderate moisture (caution zone, yellow)
- **0.7 - 1.0:** Wet surface (risk zone, red)

**Usage:** Tracks surface hydration level in real-time. Higher MI indicates wetter surface.

### Drying Rate

**Units:** Per second (d_MI/dt)

**Formula:** Linear regression slope of MI over 3-second rolling window

**Interpretation:**
- **Negative values:** Surface is drying (expected during treatment)
- **Positive values:** Surface is wetting (unusual, may indicate condensation)
- **Threshold:** < -0.05 /sec indicates over-drying risk

**Usage:** Detects rapid drying that could damage tissue.

### Roughness Index

**Range:** 0.0 (smooth) to higher values (rough)

**Formula:** Standard deviation of reflectance across spatial samples

**Interpretation:**
- **Low (< 0.1):** Smooth, homogeneous surface
- **Medium (0.1 - 0.3):** Moderate texture variation
- **High (> 0.3):** Rough, heterogeneous surface

**Usage:** Identifies surface texture variations that may affect treatment uniformity.

## Anomaly Detection

The sensor automatically detects three types of anomalies:

### 1. Contact/Occlusion Risk

**Trigger:** MI drops by >0.3 in <1 second

**Reason:** Possible sensor contact with surface or occlusion

**Action:** Check sensor position, ensure proper standoff distance

### 2. Over-Drying Risk

**Trigger:** Drying rate < -0.05 /sec

**Reason:** Excessive plasma exposure causing rapid drying

**Action:** Reduce treatment intensity or increase standoff distance

### 3. Sensor Failure

**Trigger:** Constant zero or saturation for >2 seconds

**Reason:** Hardware disconnection or short circuit

**Action:** Check wiring, verify ADC connection, restart sensor

## API Reference

### IRReflectiveSensor Class

#### Constructor

```python
IRReflectiveSensor(
    adc_channel=0,
    baseline_distance_mm=10.0,
    ema_alpha=0.3,
    sampling_rate_hz=20.0,
    adc_resolution_bits=12,
    adc_max_voltage=3.3,
    use_mock=False
)
```

**Parameters:**
- `adc_channel`: ADC channel number (0-7)
- `baseline_distance_mm`: Reference distance for calibration
- `ema_alpha`: EMA smoothing factor (0-1, higher = less smoothing)
- `sampling_rate_hz`: Target sampling rate (10-30 Hz)
- `adc_resolution_bits`: ADC resolution (12-bit = 4096 levels)
- `adc_max_voltage`: Maximum ADC voltage (typically 3.3V)
- `use_mock`: Use mock data instead of real ADC (for testing)

#### Key Methods

**`read_raw() -> int`**
- Read raw ADC value (0 to adc_max_value)
- Returns last known value on error

**`normalize(raw_value: int) -> float`**
- Normalize raw ADC to 0-1 range
- Uses calibration baselines if available

**`compute_metrics() -> Dict`**
- Compute all metrics and detect anomalies
- Returns dict with MI, drying_rate, roughness, flags

**`calibrate_baseline(distance_mm: float, dry_sample: bool)`**
- Calibrate baseline for dry or wet sample
- Takes 10 samples and computes mean

**`log_to_csv(filepath: Optional[str])`**
- Log latest metrics to CSV file
- Auto-creates log directory if needed
- Thread-safe writes

**`get_ir_metrics() -> Dict`**
- Get metrics dict for sensor fusion
- Returns: `{mi, drying_rate, roughness, anomaly_flag, anomaly_reason}`

**`start_visualization()`**
- Start live matplotlib dashboard
- Updates at 1 Hz
- Non-blocking display

## CSV Log Format

```csv
timestamp,raw_adc,mi,drying_rate_per_sec,roughness_index,contact_risk_flag,over_drying_flag
2026-01-17T23:14:00.123,512,0.45,-0.02,0.18,False,True
```

**Fields:**
- `timestamp`: ISO format timestamp
- `raw_adc`: Raw ADC reading (0-4095)
- `mi`: Moisture Index (0-1)
- `drying_rate_per_sec`: Drying rate (per second)
- `roughness_index`: Roughness metric
- `contact_risk_flag`: Boolean flag
- `over_drying_flag`: Boolean flag

## Integration with Sensor Fusion

The IR sensor is integrated into the backend API and streams metrics via WebSocket:

```python
# In backend/api.py
ir_metrics = ir_reflective_sensor.get_ir_metrics()

# WebSocket message format:
{
    "ir_metrics": {
        "mi": 0.45,
        "drying_rate": -0.02,
        "roughness": 0.18,
        "anomaly_flag": True,
        "anomaly_reason": "over_drying_risk"
    }
}
```

## Testing

### Unit Tests

```bash
# Run basic tests with mock data
python3 -m tests.test_ir_reflective
```

Tests include:
- Basic reading and normalization
- EMA smoothing
- Metrics computation
- Anomaly detection
- CSV logging

### GUI Test

```bash
# Run GUI visualization test
python3 -m tests.test_ir_reflective_gui
```

### Calibration Test

```bash
# Run interactive calibration
python3 -m tests.calibrate_ir
```

## Troubleshooting

### GPIO Not Found (Jetson)

**Problem:** `[WARN] No GPIO library available`

**Solutions:**
1. Install Jetson.GPIO: `pip install Jetson.GPIO`
2. Verify GPIO pin number (default: GPIO17, Pin 11)
3. Check wiring: VCC→Pin 1, GND→Pin 6, DO→Pin 11
4. Verify sensor power: Check 3.3V with multimeter
5. Test GPIO manually: `python3 -c "import Jetson.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup(17, GPIO.IN); print(GPIO.input(17))"`

### GPIO Not Found (Raspberry Pi)

**Problem:** GPIO initialization fails

**Solutions:**
1. Install GPIO library: `pip install RPi.GPIO` or `pip install rpi-lgpio`
2. For Pi 5: Use `rpi-lgpio` instead of `RPi.GPIO`
3. Check permissions: May need `sudo` or add user to `gpio` group
4. Verify pin number matches BCM numbering

### Constant LOW Readings (Always Wet)

**Problem:** Sensor always reads LOW (0) - always detecting wet

**Solutions:**
1. Check wiring (VCC, GND, DO pin)
2. Verify sensor power supply (3.3V)
3. Test GPIO pin manually (see GPIO troubleshooting)
4. Check for loose connections
5. Verify sensor is not stuck/occluded
6. Check sensor threshold adjustment (if available)

### Constant HIGH Readings (Always Dry)

**Problem:** Sensor always reads HIGH (1) - never detecting wet

**Solutions:**
1. Verify sensor is working (test with wet surface)
2. Check sensor distance from surface
3. Verify DO pin connection
4. Test with known wet sample
5. Check sensor sensitivity adjustment

### Metrics Not Changing

**Problem:** MI, drying rate stay constant

**Solutions:**
1. Verify sensor is reading different values (check raw_adc)
2. Check EMA alpha value (may be too low)
3. Ensure sensor is moving or surface is changing
4. Verify calibration baselines are set

### Visualization Not Updating (Jetson)

**Problem:** Matplotlib dashboard frozen or not appearing

**Solutions:**
1. Check DISPLAY variable: `echo $DISPLAY` (should be `:0` or `:10.0`)
2. Set DISPLAY if missing: `export DISPLAY=:0`
3. For SSH: Use X11 forwarding: `ssh -X user@jetson`
4. Install X11 packages: `sudo apt-get install x11-apps`
5. Test X11: `xeyes` or `xclock` should work
6. Use VNC as alternative: `sudo apt-get install tigervnc-standalone-server`
7. Check matplotlib backend: Script automatically uses `TkAgg`
8. Try mock mode to test: `use_mock=True` in sensor initialization

### High Noise in Readings

**Problem:** Metrics fluctuate wildly

**Solutions:**
1. Increase EMA alpha (less smoothing): `ema_alpha=0.5`
2. Check sensor distance (too far = noisy)
3. Verify stable power supply
4. Add hardware filtering (capacitor on analog line)

## Performance Notes

- **Sampling Rate:** 10-30 Hz recommended
- **Latency:** <50 ms per reading
- **Visualization:** 1 Hz update rate (smooth on Jetson)
- **CSV Logging:** Thread-safe, minimal overhead
- **Memory:** Rolling windows limit memory usage

## Best Practices

1. **Calibrate regularly** - Baseline can drift over time
2. **Monitor anomalies** - Set up alerts for critical flags
3. **Log continuously** - CSV logs enable post-treatment analysis
4. **Check sensor position** - Maintain consistent standoff distance
5. **Validate with phantoms** - Test with known dry/wet samples

## References

- [Jetson ADC Documentation](https://docs.nvidia.com/jetson/)
- [ADS1115 Datasheet](https://www.ti.com/lit/ds/symlink/ads1115.pdf)
- [IR Reflective Sensor Theory](https://en.wikipedia.org/wiki/Infrared_reflectance)

## Support

For issues or questions:
1. Check this documentation
2. Review test scripts for examples
3. Check backend logs for error messages
4. Verify hardware connections
