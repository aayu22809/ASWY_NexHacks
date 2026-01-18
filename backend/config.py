"""Configuration constants for the backend."""

# Server configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]

# Sensor configuration
MLX90640_I2C_ADDRESS = 0x33  # Default I2C address for MLX90640
MLX90640_REFRESH_RATE = 4.0  # Hz
IR_OBSTACLE_GPIO_PIN = 18  # GPIO pin for IR obstacle sensor (adjust as needed)

# IR Reflective Sensor (Analog) configuration
IR_REFLECTIVE_ADC_CHANNEL = 0  # ADC channel (0-7 for Jetson)
IR_REFLECTIVE_BASELINE_DISTANCE_MM = 10.0  # Reference distance for calibration
IR_REFLECTIVE_EMA_ALPHA = 0.3  # EMA smoothing factor (0-1)
IR_REFLECTIVE_SAMPLING_RATE_HZ = 20.0  # Target sampling rate (10-30 Hz)
IR_REFLECTIVE_ADC_RESOLUTION_BITS = 12  # ADC resolution (12-bit = 4096 levels)
IR_REFLECTIVE_ADC_MAX_VOLTAGE = 3.3  # Maximum ADC voltage (V)
IR_REFLECTIVE_OVERDRYING_THRESHOLD = -0.05  # Drying rate threshold (per second)
IR_REFLECTIVE_CONTACT_DROP_THRESHOLD = 0.3  # MI drop threshold for contact detection

# Thermal safety thresholds
THERMAL_MAX_SAFE_TEMP = 40.0  # Celsius
THERMAL_WARNING_TEMP = 38.0  # Celsius

# RealSense configuration
REALSENSE_DEPTH_MIN = 0.20  # meters
REALSENSE_DEPTH_MAX = 0.90  # meters
REALSENSE_CAPTURE_DIR = "captures"  # Directory for saved PLY files

# Execution configuration
EXECUTION_DEFAULT_FEED_RATE = 50.0  # mm/s
EXECUTION_RAPID_RATE = 200.0  # mm/s
