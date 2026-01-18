"""Configuration constants for the backend."""

# Server configuration
API_HOST = "0.0.0.0"
API_PORT = 8000
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]

# Sensor configuration
MLX90640_I2C_ADDRESS = 0x33  # Default I2C address for MLX90640
MLX90640_REFRESH_RATE = 4.0  # Hz
IR_OBSTACLE_GPIO_PIN = 18  # GPIO pin for IR obstacle sensor (adjust as needed)

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
