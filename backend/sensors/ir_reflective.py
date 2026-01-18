"""
IR Reflective Sensor for Wound Hydration Analysis (Digital GPIO Mode)

Provides continuous moisture detection, drying trend analysis, and surface roughness
metrics for AI-driven CAP (Cold Atmospheric Plasma) treatment decisions.

On Jetson Orin Nano: Uses GPIO digital mode (no native ADC available)
On Raspberry Pi: Can use GPIO digital mode or ADC (if available)
"""

import os
import time
import csv
import threading
from collections import deque
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import numpy as np
from scipy import stats

# Try to import GPIO libraries
try:
    import Jetson.GPIO as JetsonGPIO
    _HAVE_JETSON_GPIO = True
except ImportError:
    JetsonGPIO = None
    _HAVE_JETSON_GPIO = False

try:
    import RPi.GPIO as RPiGPIO
    _HAVE_RPI_GPIO = True
except ImportError:
    RPiGPIO = None
    _HAVE_RPI_GPIO = False

try:
    import lgpio
    _HAVE_LGPIO = True
except ImportError:
    lgpio = None
    _HAVE_LGPIO = False

# Try to import matplotlib for visualization (optional)
try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    from matplotlib.colors import Normalize as MPLNormalize
    _HAVE_MATPLOTLIB = True
except ImportError:
    _HAVE_MATPLOTLIB = False


class IRReflectiveSensor:
    """
    IR reflective sensor driver with signal processing and analytics (Digital GPIO Mode).
    
    Reads digital values from GPIO pin, processes signal with EMA smoothing,
    computes moisture index, drying trends, and roughness metrics.
    
    On Jetson Orin Nano: Uses GPIO digital mode (no native ADC)
    Digital output: LOW = wet/detected, HIGH = dry/clear
    """
    
    def __init__(
        self,
        gpio_pin: Optional[int] = None,
        baseline_distance_mm: float = 10.0,
        ema_alpha: float = 0.3,
        sampling_rate_hz: float = 20.0,
        use_mock: bool = False
    ):
        """
        Initialize IR reflective sensor.
        
        Args:
            gpio_pin: GPIO pin number (BCM numbering). Defaults to config value.
            baseline_distance_mm: Reference distance for calibration (mm)
            ema_alpha: EMA smoothing factor (0-1, higher = less smoothing)
            sampling_rate_hz: Target sampling rate (10-30 Hz)
            use_mock: Use mock data instead of real GPIO (for testing)
        """
        from backend.config import IR_REFLECTIVE_GPIO_PIN
        
        self.gpio_pin = gpio_pin if gpio_pin is not None else IR_REFLECTIVE_GPIO_PIN
        self.baseline_distance_mm = baseline_distance_mm
        self.ema_alpha = ema_alpha
        self.sampling_rate_hz = sampling_rate_hz
        self.sample_interval = 1.0 / sampling_rate_hz
        self.use_mock = use_mock
        
        # Digital mode: 0 = LOW (wet/detected), 1 = HIGH (dry/clear)
        # For compatibility with analog metrics, we'll map:
        # LOW (0) → high moisture (MI = 1.0)
        # HIGH (1) → low moisture (MI = 0.0)
        self.digital_max_value = 1  # Binary: 0 or 1
        
        # GPIO state
        self._gpio_lib = None
        self._chip = None  # For lgpio
        self._gpiochip_num = None  # For lgpio
        self._initialized = False
        
        # Signal processing state
        self.ema_value = None
        self.last_raw_value = 0
        self.last_read_time = None
        
        # Baseline calibration
        self.baseline_dry = None
        self.baseline_wet = None
        self.normalization_min = 0.0
        self.normalization_max = 1.0
        
        # Metrics history (rolling windows)
        self.mi_history = deque(maxlen=int(sampling_rate_hz * 60))  # 60 seconds
        self.drying_rate_history = deque(maxlen=int(sampling_rate_hz * 30))  # 30 seconds
        self.raw_history = deque(maxlen=int(sampling_rate_hz * 60))  # 60 seconds
        self.timestamp_history = deque(maxlen=int(sampling_rate_hz * 60))
        
        # Patch tracking
        self.patch_history: Dict[str, Dict] = {}
        self.current_patch_id = None
        
        # Anomaly detection state
        self.last_mi_value = None
        self.last_mi_time = None
        self.zero_count = 0
        self.saturation_count = 0
        self.anomaly_flags = {
            'contact_risk': False,
            'over_drying': False,
            'sensor_failure': False
        }
        self.anomaly_reasons = []
        
        # CSV logging
        self.csv_filepath = None
        self.csv_writer = None
        self.csv_file = None
        self.log_lock = threading.Lock()
        
        # Visualization
        self.fig = None
        self.axes = None
        self.animation = None
        self.plot_data = {
            'time': deque(maxlen=int(sampling_rate_hz * 60)),
            'raw': deque(maxlen=int(sampling_rate_hz * 60)),
            'mi': deque(maxlen=int(sampling_rate_hz * 60)),
            'drying_rate': deque(maxlen=int(sampling_rate_hz * 30)),
        }
        
        # GPIO initialization
        if not use_mock:
            self._init_gpio()
        else:
            self._mock_time = time.time()
            print("[INFO] Using mock GPIO data for testing")
    
    def _init_gpio(self):
        """Initialize GPIO interface for digital reading."""
        # Try Jetson.GPIO first (for Jetson Orin Nano)
        if _HAVE_JETSON_GPIO:
            try:
                JetsonGPIO.setmode(JetsonGPIO.BCM)
                JetsonGPIO.setup(self.gpio_pin, JetsonGPIO.IN, pull_up_down=JetsonGPIO.PUD_UP)
                self._gpio_lib = "Jetson"
                self._initialized = True
                print(f"[OK] IR Reflective sensor initialized on GPIO {self.gpio_pin} (Jetson.GPIO)")
                return
            except Exception as e:
                print(f"[WARN] Jetson.GPIO initialization failed: {e}, trying fallback...")
        
        # Try RPi.GPIO (for Raspberry Pi)
        if _HAVE_RPI_GPIO:
            try:
                RPiGPIO.setmode(RPiGPIO.BCM)
                RPiGPIO.setup(self.gpio_pin, RPiGPIO.IN, pull_up_down=RPiGPIO.PUD_UP)
                self._gpio_lib = "RPi"
                self._initialized = True
                print(f"[OK] IR Reflective sensor initialized on GPIO {self.gpio_pin} (RPi.GPIO)")
                return
            except Exception as e:
                print(f"[WARN] RPi.GPIO initialization failed: {e}, trying fallback...")
        
        # Try lgpio (for Raspberry Pi 5)
        if _HAVE_LGPIO:
            try:
                # Detect gpiochip
                gpiochip_path = "/dev/gpiochip4" if os.path.exists("/dev/gpiochip4") else "/dev/gpiochip0"
                self._gpiochip_num = 4 if "gpiochip4" in gpiochip_path else 0
                self._chip = lgpio.gpiochip_open(self._gpiochip_num)
                lgpio.gpio_claim_input(self._chip, self.gpio_pin, lgpio.SET_PULL_UP)
                self._gpio_lib = "lgpio"
                self._initialized = True
                print(f"[OK] IR Reflective sensor initialized on GPIO {self.gpio_pin} (lgpio, chip={gpiochip_path})")
                return
            except Exception as e:
                print(f"[WARN] lgpio initialization failed: {e}")
        
        # If all GPIO libraries failed, fall back to mock mode
        print("[WARN] No GPIO library available or all failed. Falling back to mock mode.")
        self.use_mock = True
        self._mock_time = time.time()
    
    def read_raw(self) -> int:
        """
        Read raw digital GPIO value.
        
        Returns:
            Digital value: 0 (LOW/wet) or 1 (HIGH/dry)
        """
        if self.use_mock:
            # Generate mock data: simulate wet/dry transitions
            t = time.time() - self._mock_time
            # Simulate periodic wet/dry cycles
            cycle = np.sin(2 * np.pi * 0.05 * t)  # Slow cycle
            value = 0 if cycle > 0 else 1  # 0 = wet, 1 = dry
            return value
        
        if not self._initialized:
            return self.last_raw_value
        
        try:
            if self._gpio_lib == "Jetson":
                pin_state = JetsonGPIO.input(self.gpio_pin)
                # LOW = wet/detected (0), HIGH = dry/clear (1)
                return 0 if pin_state == JetsonGPIO.LOW else 1
            elif self._gpio_lib == "RPi":
                pin_state = RPiGPIO.input(self.gpio_pin)
                return 0 if pin_state == RPiGPIO.LOW else 1
            elif self._gpio_lib == "lgpio":
                pin_state = lgpio.gpio_read(self._chip, self.gpio_pin)
                return 0 if pin_state == 0 else 1
            else:
                return self.last_raw_value
        except Exception as e:
            print(f"[WARN] GPIO read failed: {e}, using last known value")
            return self.last_raw_value
    
    def normalize(self, raw_value: int) -> float:
        """
        Normalize raw digital value to 0-1 range.
        
        Args:
            raw_value: Raw digital reading (0 = LOW/wet, 1 = HIGH/dry)
            
        Returns:
            Normalized value (0.0 to 1.0)
            For digital mode: 0.0 = dry, 1.0 = wet (inverted from raw)
        """
        # Digital mode: invert so LOW (wet) = 1.0, HIGH (dry) = 0.0
        # This maintains compatibility with analog moisture index calculations
        return 1.0 - float(raw_value)
    
    def get_voltage(self, raw_value: int) -> float:
        """
        Convert raw digital value to voltage (for compatibility).
        
        Args:
            raw_value: Raw digital reading (0 or 1)
            
        Returns:
            Voltage in volts: 0.0V (LOW) or 3.3V (HIGH)
        """
        return 0.0 if raw_value == 0 else 3.3
    
    def apply_ema(self, value: float, alpha: Optional[float] = None) -> float:
        """
        Apply Exponential Moving Average smoothing.
        
        Args:
            value: New value to smooth
            alpha: Smoothing factor (uses instance default if None)
            
        Returns:
            EMA-smoothed value
        """
        if alpha is None:
            alpha = self.ema_alpha
        
        if self.ema_value is None:
            self.ema_value = value
        else:
            self.ema_value = alpha * value + (1 - alpha) * self.ema_value
        
        return self.ema_value
    
    def calibrate_baseline(self, distance_mm: float, dry_sample: bool = True):
        """
        Calibrate baseline for dry or wet sample (digital mode).
        
        Args:
            distance_mm: Sensor distance from surface (mm)
            dry_sample: True for dry phantom, False for wet phantom
        """
        print(f"[INFO] Calibrating {'dry' if dry_sample else 'wet'} baseline at {distance_mm}mm...")
        print("[INFO] Taking 10 samples...")
        
        samples = []
        for _ in range(10):
            raw = self.read_raw()
            samples.append(raw)
            time.sleep(0.1)
        
        baseline = np.mean(samples)
        std = np.std(samples)
        
        if dry_sample:
            self.baseline_dry = baseline
            print(f"[OK] Dry baseline: {baseline:.2f} ± {std:.2f} (digital: HIGH=1, LOW=0)")
        else:
            self.baseline_wet = baseline
            print(f"[OK] Wet baseline: {baseline:.2f} ± {std:.2f} (digital: HIGH=1, LOW=0)")
        
        # For digital mode, baselines should be close to 0 (wet) or 1 (dry)
        print(f"[INFO] Digital mode: LOW (0) = wet/detected, HIGH (1) = dry/clear")
    
    def compute_moisture_index(self, normalized_value: float) -> float:
        """
        Compute Moisture Index (MI).
        
        Formula: MI = 1 - raw_normalized
        Higher MI = wetter surface
        
        Args:
            normalized_value: Normalized reflectance (0-1)
            
        Returns:
            Moisture Index (0-1)
        """
        # MI = 1 - normalized (inverted: low reflectance = high moisture)
        mi = 1.0 - normalized_value
        return np.clip(mi, 0.0, 1.0)
    
    def compute_drying_rate(self, window_seconds: float = 3.0) -> float:
        """
        Compute drying rate (d_MI/dt) over rolling window.
        
        Args:
            window_seconds: Time window for rate calculation
            
        Returns:
            Drying rate (per second), negative = drying
        """
        if len(self.mi_history) < 2:
            return 0.0
        
        # Get recent MI values within window
        window_samples = int(window_seconds * self.sampling_rate_hz)
        if len(self.mi_history) < window_samples:
            window_samples = len(self.mi_history)
        
        mi_values = list(self.mi_history)[-window_samples:]
        timestamps = list(self.timestamp_history)[-window_samples:]
        
        if len(mi_values) < 2:
            return 0.0
        
        # Linear regression to compute rate
        times = np.array([(t - timestamps[0]).total_seconds() for t in timestamps])
        if len(times) > 1 and times[-1] > times[0]:
            slope, _, _, _, _ = stats.linregress(times, mi_values)
            return float(slope)
        
        return 0.0
    
    def compute_roughness(self, patch_data: List[float]) -> float:
        """
        Compute roughness index from spatial variance.
        
        Args:
            patch_data: List of reflectance values from adjacent positions
            
        Returns:
            Roughness index (standard deviation of reflectance)
        """
        if len(patch_data) < 2:
            return 0.0
        
        return float(np.std(patch_data))
    
    def detect_contact_risk(self) -> Tuple[bool, Optional[str]]:
        """
        Detect rapid MI drop indicating contact/occlusion.
        
        Returns:
            (is_risk, reason_string)
        """
        if self.last_mi_value is None or len(self.mi_history) < 2:
            return False, None
        
        current_mi = self.mi_history[-1]
        mi_drop = self.last_mi_value - current_mi
        
        if mi_drop > 0.3:  # Drop of >0.3 in one sample
            time_diff = (self.timestamp_history[-1] - self.last_mi_time).total_seconds()
            if time_diff < 1.0:  # Within 1 second
                return True, f"Rapid MI drop: {mi_drop:.2f} in {time_diff:.2f}s"
        
        return False, None
    
    def detect_overdrying(self, drying_rate: float) -> Tuple[bool, Optional[str]]:
        """
        Detect over-drying risk from excessive drying rate.
        
        Args:
            drying_rate: Current drying rate (per second)
            
        Returns:
            (is_risk, reason_string)
        """
        if drying_rate < -0.05:  # Drying faster than -0.05 /sec
            return True, f"Excessive drying rate: {drying_rate:.3f} /sec"
        return False, None
    
    def detect_sensor_failure(self, raw_value: int) -> Tuple[bool, Optional[str]]:
        """
        Detect sensor disconnection (constant LOW or HIGH).
        
        Args:
            raw_value: Current raw digital reading (0 or 1)
            
        Returns:
            (is_failure, reason_string)
        """
        # For digital mode, check if value is stuck (no transitions)
        # This is simpler than analog mode - just check for lack of variation
        if len(self.raw_history) > int(2.0 * self.sampling_rate_hz):
            recent_values = list(self.raw_history)[-int(2.0 * self.sampling_rate_hz):]
            if len(set(recent_values)) == 1:  # All same value
                stuck_value = recent_values[0]
                return True, f"Sensor stuck at {'LOW (wet)' if stuck_value == 0 else 'HIGH (dry)'} - possible disconnection"
        
        return False, None
    
    def get_anomaly_flags(self) -> Dict:
        """
        Get all anomaly flags and reasons.
        
        Returns:
            Dict with flags and reasons
        """
        return {
            'contact_risk': self.anomaly_flags['contact_risk'],
            'over_drying': self.anomaly_flags['over_drying'],
            'sensor_failure': self.anomaly_flags['sensor_failure'],
            'reasons': self.anomaly_reasons.copy()
        }
    
    def compute_metrics(self) -> Dict:
        """
        Compute all metrics and detect anomalies.
        
        Returns:
            Dict with MI, drying_rate, roughness, and anomaly flags
        """
        # Read raw value
        raw_value = self.read_raw()
        current_time = datetime.now()
        
        # Normalize and smooth
        normalized = self.normalize(raw_value)
        smoothed = self.apply_ema(normalized)
        
        # Compute Moisture Index
        mi = self.compute_moisture_index(smoothed)
        
        # Update history
        self.raw_history.append(raw_value)
        self.mi_history.append(mi)
        self.timestamp_history.append(current_time)
        
        # Compute drying rate
        drying_rate = self.compute_drying_rate(window_seconds=3.0)
        self.drying_rate_history.append(drying_rate)
        
        # Compute roughness (using recent variance)
        if len(self.mi_history) >= 10:
            recent_mi = list(self.mi_history)[-10:]
            roughness = self.compute_roughness(recent_mi)
        else:
            roughness = 0.0
        
        # Detect anomalies
        self.anomaly_reasons = []
        
        # Contact risk
        contact_risk, contact_reason = self.detect_contact_risk()
        self.anomaly_flags['contact_risk'] = contact_risk
        if contact_risk:
            self.anomaly_reasons.append(contact_reason)
        
        # Over-drying
        over_drying, overdry_reason = self.detect_overdrying(drying_rate)
        self.anomaly_flags['over_drying'] = over_drying
        if over_drying:
            self.anomaly_reasons.append(overdry_reason)
        
        # Sensor failure
        sensor_failure, failure_reason = self.detect_sensor_failure(raw_value)
        self.anomaly_flags['sensor_failure'] = sensor_failure
        if sensor_failure:
            self.anomaly_reasons.append(failure_reason)
        
        # Update state
        self.last_raw_value = raw_value
        self.last_mi_value = mi
        self.last_mi_time = current_time
        
        # Update plot data
        elapsed = (current_time - self.timestamp_history[0]).total_seconds() if self.timestamp_history else 0.0
        self.plot_data['time'].append(elapsed)
        self.plot_data['raw'].append(raw_value)
        self.plot_data['mi'].append(mi)
        self.plot_data['drying_rate'].append(drying_rate)
        
        return {
            'mi': mi,
            'drying_rate': drying_rate,
            'roughness': roughness,
            'raw_adc': raw_value,
            'normalized': smoothed,
            'voltage': self.get_voltage(raw_value),
            'anomaly_flag': any(self.anomaly_flags.values()),
            'anomaly_reason': '; '.join(self.anomaly_reasons) if self.anomaly_reasons else None,
            'contact_risk_flag': contact_risk,
            'over_drying_flag': over_drying,
            'sensor_failure_flag': sensor_failure,
            'timestamp': current_time.isoformat()
        }
    
    def log_to_csv(self, filepath: Optional[str] = None):
        """
        Log latest metrics to CSV file.
        
        Args:
            filepath: Path to CSV file (uses instance default if None)
        """
        if filepath:
            self.csv_filepath = filepath
        
        if not self.csv_filepath:
            # Create default log file
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            today = datetime.now().strftime("%Y-%m-%d")
            self.csv_filepath = os.path.join(log_dir, f"ir_sensor_{today}.csv")
        
        metrics = self.compute_metrics()
        
        with self.log_lock:
            # Check if file exists and write header if new
            file_exists = os.path.exists(self.csv_filepath)
            
            with open(self.csv_filepath, 'a', newline='') as f:
                writer = csv.writer(f)
                
                if not file_exists:
                    # Write header
                    writer.writerow([
                        'timestamp', 'raw_adc', 'mi', 'drying_rate_per_sec',
                        'roughness_index', 'contact_risk_flag', 'over_drying_flag'
                    ])
                
                # Write data row
                writer.writerow([
                    metrics['timestamp'],
                    metrics['raw_adc'],
                    f"{metrics['mi']:.4f}",
                    f"{metrics['drying_rate']:.4f}",
                    f"{metrics['roughness']:.4f}",
                    metrics['contact_risk_flag'],
                    metrics['over_drying_flag']
                ])
    
    def get_ir_metrics(self) -> Dict:
        """
        Get IR metrics dict for sensor fusion.
        
        Returns:
            Dict compatible with sensor fusion pipeline
        """
        metrics = self.compute_metrics()
        return {
            'mi': metrics['mi'],
            'drying_rate': metrics['drying_rate'],
            'roughness': metrics['roughness'],
            'anomaly_flag': metrics['anomaly_flag'],
            'anomaly_reason': metrics['anomaly_reason']
        }
    
    def to_json(self) -> Dict:
        """
        Serialize metrics to JSON-compatible dict.
        
        Returns:
            JSON-serializable dict
        """
        metrics = self.compute_metrics()
        return {
            'mi': float(metrics['mi']),
            'drying_rate': float(metrics['drying_rate']),
            'roughness': float(metrics['roughness']),
            'raw_adc': int(metrics['raw_adc']),
            'voltage': float(metrics['voltage']),
            'anomaly_flag': bool(metrics['anomaly_flag']),
            'anomaly_reason': metrics['anomaly_reason'],
            'contact_risk_flag': bool(metrics['contact_risk_flag']),
            'over_drying_flag': bool(metrics['over_drying_flag']),
            'sensor_failure_flag': bool(metrics['sensor_failure_flag']),
            'timestamp': metrics['timestamp']
        }
    
    def init_plots(self):
        """Initialize matplotlib figure and subplots."""
        if not _HAVE_MATPLOTLIB:
            print("[WARN] Matplotlib not available, skipping visualization")
            return
        
        self.fig, self.axes = plt.subplots(2, 2, figsize=(14, 10))
        self.fig.suptitle('IR Reflective Sensor - Live Dashboard', fontsize=16, fontweight='bold')
        
        # Subplot 1: Raw IR Intensity
        self.axes[0, 0].set_title('Raw IR Intensity')
        self.axes[0, 0].set_xlabel('Time (seconds)')
        self.axes[0, 0].set_ylabel('Raw ADC Value')
        self.axes[0, 0].grid(True, alpha=0.3)
        
        # Subplot 2: Moisture Index Trend
        self.axes[0, 1].set_title('Moisture Index Trend')
        self.axes[0, 1].set_xlabel('Time (seconds)')
        self.axes[0, 1].set_ylabel('MI (0=dry, 1=wet)')
        self.axes[0, 1].set_ylim(0, 1)
        self.axes[0, 1].axhspan(0, 0.3, alpha=0.2, color='green', label='Safe')
        self.axes[0, 1].axhspan(0.3, 0.7, alpha=0.2, color='yellow', label='Caution')
        self.axes[0, 1].axhspan(0.7, 1.0, alpha=0.2, color='red', label='Risk')
        self.axes[0, 1].grid(True, alpha=0.3)
        self.axes[0, 1].legend()
        
        # Subplot 3: Drying Rate
        self.axes[1, 0].set_title('Drying Rate (d_MI/dt)')
        self.axes[1, 0].set_xlabel('Time (seconds)')
        self.axes[1, 0].set_ylabel('Rate (per second)')
        self.axes[1, 0].axhline(-0.05, color='red', linestyle='--', label='Over-drying threshold')
        self.axes[1, 0].axhline(0, color='gray', linestyle='-', alpha=0.5)
        self.axes[1, 0].grid(True, alpha=0.3)
        self.axes[1, 0].legend()
        
        # Subplot 4: Roughness Heatmap (placeholder - will be spatial)
        self.axes[1, 1].set_title('Roughness Index (Recent Variance)')
        self.axes[1, 1].set_xlabel('Time (seconds)')
        self.axes[1, 1].set_ylabel('Roughness Index')
        self.axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
    
    def update_plots(self, frame):
        """Animation callback to update plots."""
        if not _HAVE_MATPLOTLIB or self.fig is None:
            return
        
        if len(self.plot_data['time']) < 2:
            return
        
        # Update subplot 1: Raw IR Intensity
        self.axes[0, 0].clear()
        self.axes[0, 0].plot(list(self.plot_data['time']), list(self.plot_data['raw']), 'b-', linewidth=1)
        self.axes[0, 0].set_title('Raw IR Intensity')
        self.axes[0, 0].set_xlabel('Time (seconds)')
        self.axes[0, 0].set_ylabel('Raw ADC Value')
        self.axes[0, 0].grid(True, alpha=0.3)
        
        # Update subplot 2: Moisture Index
        self.axes[0, 1].clear()
        mi_data = list(self.plot_data['mi'])
        time_data = list(self.plot_data['time'])
        self.axes[0, 1].plot(time_data, mi_data, 'g-', linewidth=2)
        self.axes[0, 1].axhspan(0, 0.3, alpha=0.2, color='green')
        self.axes[0, 1].axhspan(0.3, 0.7, alpha=0.2, color='yellow')
        self.axes[0, 1].axhspan(0.7, 1.0, alpha=0.2, color='red')
        self.axes[0, 1].set_title('Moisture Index Trend')
        self.axes[0, 1].set_xlabel('Time (seconds)')
        self.axes[0, 1].set_ylabel('MI (0=dry, 1=wet)')
        self.axes[0, 1].set_ylim(0, 1)
        self.axes[0, 1].grid(True, alpha=0.3)
        
        # Update subplot 3: Drying Rate
        self.axes[1, 0].clear()
        dr_data = list(self.plot_data['drying_rate'])
        dr_time = list(self.plot_data['time'])[-len(dr_data):]
        colors = ['red' if dr < -0.05 else 'blue' for dr in dr_data]
        self.axes[1, 0].scatter(dr_time, dr_data, c=colors, s=10, alpha=0.6)
        self.axes[1, 0].axhline(-0.05, color='red', linestyle='--', label='Over-drying threshold')
        self.axes[1, 0].axhline(0, color='gray', linestyle='-', alpha=0.5)
        self.axes[1, 0].set_title('Drying Rate (d_MI/dt)')
        self.axes[1, 0].set_xlabel('Time (seconds)')
        self.axes[1, 0].set_ylabel('Rate (per second)')
        self.axes[1, 0].grid(True, alpha=0.3)
        self.axes[1, 0].legend()
        
        # Update subplot 4: Roughness
        self.axes[1, 1].clear()
        if len(mi_data) >= 10:
            # Compute rolling roughness
            roughness_data = []
            for i in range(10, len(mi_data)):
                window = mi_data[i-10:i]
                roughness_data.append(np.std(window))
            if roughness_data:
                rough_time = time_data[10:]
                self.axes[1, 1].plot(rough_time, roughness_data, 'purple', linewidth=1)
        self.axes[1, 1].set_title('Roughness Index (Recent Variance)')
        self.axes[1, 1].set_xlabel('Time (seconds)')
        self.axes[1, 1].set_ylabel('Roughness Index')
        self.axes[1, 1].grid(True, alpha=0.3)
    
    def get_live_plot(self):
        """Get current matplotlib figure for display."""
        return self.fig
    
    def start_visualization(self):
        """Start live matplotlib dashboard."""
        if not _HAVE_MATPLOTLIB:
            print("[ERROR] Matplotlib not available")
            return
        
        self.init_plots()
        
        # Start animation at 1 Hz update rate
        self.animation = animation.FuncAnimation(
            self.fig,
            self.update_plots,
            interval=1000,  # 1 Hz
            blit=False
        )
        
        plt.ion()
        plt.show()
        print("[INFO] Live visualization started (1 Hz update rate)")
    
    def close(self):
        """Cleanup resources."""
        if self.csv_file:
            self.csv_file.close()
        
        if self.animation:
            self.animation.event_source.stop()
        
        if self.fig:
            plt.close(self.fig)
        
        # Cleanup GPIO
        if self._initialized:
            try:
                if self._gpio_lib == "Jetson" and JetsonGPIO:
                    JetsonGPIO.cleanup(self.gpio_pin)
                elif self._gpio_lib == "RPi" and RPiGPIO:
                    RPiGPIO.cleanup(self.gpio_pin)
                elif self._gpio_lib == "lgpio" and self._chip:
                    lgpio.gpiochip_close(self._chip)
                self._initialized = False
            except Exception as e:
                print(f"[WARN] Error during GPIO cleanup: {e}")