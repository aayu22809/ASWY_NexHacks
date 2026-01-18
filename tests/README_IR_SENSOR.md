# IR Reflective Sensor Documentation

## Overview

The IR Reflective Sensor system provides continuous moisture detection, drying trend analysis, and surface roughness metrics for AI-driven CAP (Cold Atmospheric Plasma) wound treatment decisions. It uses analog reflectance measurements to track hydration levels and surface conditions in real-time.

## Hardware Setup

### Wiring to Jetson Orin Nano

| IR Sensor Pin | Jetson Connection |
|---------------|-------------------|
| VCC           | 3.3V or 5V rail (check sensor spec) |
| GND           | GND               |
| Analog Out    | ADC Channel 0 (or ADS1115 if no native ADC) |

### ADC Options

**Option 1: Native Jetson ADC (Recommended)**
- Jetson Orin Nano has built-in ADC accessible via `/sys/bus/iio/devices/iio:device0/`
- Default channel: 0
- Resolution: 12-bit (0-4095)
- Voltage range: 0-3.3V

**Option 2: ADS1115 I2C ADC Module**
- If Jetson lacks native ADC, use ADS1115 breakout board
- Connect analog out → ADS1115 analog input
- Connect ADS1115 I2C → Jetson I2C bus
- Update code to use ADS1115 library instead

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
sensor = IRReflectiveSensor(
    adc_channel=0,
    baseline_distance_mm=10.0,
    sampling_rate_hz=20.0
)

# Read metrics
metrics = sensor.compute_metrics()
print(f"Moisture Index: {metrics['mi']:.3f}")
print(f"Drying Rate: {metrics['drying_rate']:.4f} /sec")
print(f"Roughness: {metrics['roughness']:.4f}")
```

### 3. Calibration

Before using the sensor, calibrate it with dry and wet phantom samples:

```bash
python3 -m tests.calibrate_ir
```

The calibration script will:
1. Prompt you to place sensor 10mm above dry phantom
2. Record baseline dry value
3. Prompt you to place sensor 10mm above wet phantom
4. Record baseline wet value
5. Calculate normalization range

### 4. Live Visualization

Start the live matplotlib dashboard:

```bash
python3 -m tests.test_ir_reflective_gui
```

This displays:
- Raw IR intensity over time
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

### ADC Not Found

**Problem:** `[WARN] ADC path not found`

**Solutions:**
1. Check ADC channel number matches hardware
2. Verify `/sys/bus/iio/devices/iio:device0/` exists
3. Check permissions: `sudo chmod 666 /sys/bus/iio/devices/iio:device0/in_voltage*_raw`
4. Use ADS1115 I2C module as alternative

### Constant Zero Readings

**Problem:** Sensor always reads 0

**Solutions:**
1. Check wiring (VCC, GND, Analog Out)
2. Verify sensor power supply
3. Test ADC with multimeter
4. Check for loose connections

### Metrics Not Changing

**Problem:** MI, drying rate stay constant

**Solutions:**
1. Verify sensor is reading different values (check raw_adc)
2. Check EMA alpha value (may be too low)
3. Ensure sensor is moving or surface is changing
4. Verify calibration baselines are set

### Visualization Not Updating

**Problem:** Matplotlib dashboard frozen

**Solutions:**
1. Check matplotlib backend: `export MPLBACKEND=TkAgg`
2. Verify X11 forwarding if using SSH
3. Try non-GUI mode: `export DISPLAY=`
4. Use mock data to test: `use_mock=True`

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
