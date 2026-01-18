"""IR reflective obstacle sensor driver."""

from typing import Optional

try:
    # Try Jetson GPIO first (for Jetson Orin Nano)
    import Jetson.GPIO as GPIO
    _GPIO_LIB = "Jetson"
except ImportError:
    try:
        # Fall back to RPi.GPIO (for Raspberry Pi)
        import RPi.GPIO as GPIO
        _GPIO_LIB = "RPi"
    except ImportError:
        GPIO = None
        _GPIO_LIB = None

from backend.config import IR_OBSTACLE_GPIO_PIN


class IRObstacleSensor:
    """Driver for IR photoelectric obstacle sensor."""
    
    def __init__(self, gpio_pin: int = IR_OBSTACLE_GPIO_PIN):
        """
        Initialize IR obstacle sensor.
        
        Args:
            gpio_pin: GPIO pin number for the sensor input
        """
        if GPIO is None:
            raise ImportError(
                "GPIO library not available. Install with: "
                "pip install Jetson.GPIO (for Jetson) or RPi.GPIO (for Raspberry Pi)"
            )
        
        self.gpio_pin = gpio_pin
        self._initialized = False
        
        try:
            # Set GPIO mode
            GPIO.setmode(GPIO.BCM)
            
            # Configure pin as input with pull-up resistor
            # Sensor typically outputs LOW when obstacle detected
            GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            self._initialized = True
            print(f"[OK] IR Obstacle sensor initialized on GPIO {self.gpio_pin} ({_GPIO_LIB})")
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize IR obstacle sensor: {e}")
    
    def is_blocked(self) -> bool:
        """
        Check if obstacle is detected.
        
        Returns:
            True if obstacle detected (beam broken), False if clear
        """
        if not self._initialized:
            return False
        
        try:
            # Read GPIO pin
            # LOW = obstacle detected (beam broken)
            # HIGH = clear (beam intact)
            pin_state = GPIO.input(self.gpio_pin)
            
            # Return True if pin is LOW (obstacle detected)
            return pin_state == GPIO.LOW
            
        except Exception as e:
            print(f"[WARN] Failed to read IR obstacle sensor: {e}")
            return False
    
    def close(self):
        """Cleanup GPIO resources."""
        if self._initialized and GPIO:
            try:
                GPIO.cleanup(self.gpio_pin)
                self._initialized = False
            except Exception:
                pass
