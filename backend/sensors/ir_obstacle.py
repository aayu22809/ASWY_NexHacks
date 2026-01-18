"""IR reflective obstacle sensor driver."""

import os
from typing import Optional

# Try lgpio first (for Raspberry Pi 5 and modern Pis)
try:
    import lgpio
    _HAVE_LGPIO = True
except ImportError:
    lgpio = None
    _HAVE_LGPIO = False

# Fall back to RPi.GPIO (for older Raspberry Pi models)
try:
    import RPi.GPIO as GPIO
    _HAVE_RPI_GPIO = True
except ImportError:
    GPIO = None
    _HAVE_RPI_GPIO = False

# Fall back to Jetson.GPIO (for Jetson Orin Nano)
try:
    import Jetson.GPIO as JetsonGPIO
    _HAVE_JETSON_GPIO = True
except ImportError:
    JetsonGPIO = None
    _HAVE_JETSON_GPIO = False

from backend.config import IR_OBSTACLE_GPIO_PIN


def _detect_gpiochip() -> Optional[int]:
    """
    Detect which gpiochip to use.
    
    Returns:
        gpiochip number (4 for Pi 5, 0 for Pi 4 and earlier), or None if not found
    """
    # Check for gpiochip4 (Raspberry Pi 5)
    if os.path.exists('/dev/gpiochip4'):
        return 4
    # Check for gpiochip0 (Raspberry Pi 4 and earlier)
    elif os.path.exists('/dev/gpiochip0'):
        return 0
    return None


class IRObstacleSensor:
    """Driver for IR photoelectric obstacle sensor."""
    
    def __init__(self, gpio_pin: int = IR_OBSTACLE_GPIO_PIN):
        """
        Initialize IR obstacle sensor.
        
        Args:
            gpio_pin: GPIO pin number for the sensor input (BCM numbering)
        """
        self.gpio_pin = gpio_pin
        self._initialized = False
        self._gpio_lib = None
        self._chip = None  # For lgpio
        self._gpiochip_num = None  # For lgpio
        
        # Try lgpio first (Pi 5 compatible)
        if _HAVE_LGPIO:
            try:
                self._gpiochip_num = _detect_gpiochip()
                if self._gpiochip_num is not None:
                    self._chip = lgpio.gpiochip_open(self._gpiochip_num)
                    # Configure pin as input with pull-up resistor
                    # Sensor typically outputs LOW when obstacle detected
                    lgpio.gpio_claim_input(self._chip, self.gpio_pin, lgpio.SET_PULL_UP)
                    self._gpio_lib = "lgpio"
                    self._initialized = True
                    print(f"[OK] IR Obstacle sensor initialized on GPIO {self.gpio_pin} (lgpio, gpiochip{self._gpiochip_num})")
                    return
                else:
                    print("[WARN] lgpio available but no gpiochip found, trying fallback...")
            except Exception as e:
                print(f"[WARN] lgpio initialization failed: {e}, trying fallback...")
        
        # Fall back to RPi.GPIO (older Raspberry Pi models)
        if _HAVE_RPI_GPIO:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                self._gpio_lib = "RPi"
                self._initialized = True
                print(f"[OK] IR Obstacle sensor initialized on GPIO {self.gpio_pin} (RPi.GPIO)")
                return
            except Exception as e:
                print(f"[WARN] RPi.GPIO initialization failed: {e}, trying fallback...")
        
        # Fall back to Jetson.GPIO (Jetson Orin Nano)
        if _HAVE_JETSON_GPIO:
            try:
                JetsonGPIO.setmode(JetsonGPIO.BCM)
                JetsonGPIO.setup(self.gpio_pin, JetsonGPIO.IN, pull_up_down=JetsonGPIO.PUD_UP)
                self._gpio_lib = "Jetson"
                self._initialized = True
                print(f"[OK] IR Obstacle sensor initialized on GPIO {self.gpio_pin} (Jetson.GPIO)")
                return
            except Exception as e:
                print(f"[WARN] Jetson.GPIO initialization failed: {e}")
        
        # If we get here, no GPIO library worked
        raise ImportError(
            "No GPIO library available or all failed to initialize.\n"
            "For Raspberry Pi 5: sudo apt-get install python3-lgpio\n"
            "For Raspberry Pi 4/earlier: pip install RPi.GPIO\n"
            "For Jetson: pip install Jetson.GPIO"
        )
    
    def is_blocked(self) -> bool:
        """
        Check if obstacle is detected.
        
        Returns:
            True if obstacle detected (beam broken), False if clear
        """
        if not self._initialized:
            return False
        
        try:
            if self._gpio_lib == "lgpio":
                # Read GPIO pin using lgpio
                # lgpio returns 0 for LOW, 1 for HIGH
                pin_state = lgpio.gpio_read(self._chip, self.gpio_pin)
                # Return True if pin is LOW (0) - obstacle detected
                return pin_state == 0
                
            elif self._gpio_lib == "RPi":
                # Read GPIO pin using RPi.GPIO
                pin_state = GPIO.input(self.gpio_pin)
                # Return True if pin is LOW - obstacle detected
                return pin_state == GPIO.LOW
                
            elif self._gpio_lib == "Jetson":
                # Read GPIO pin using Jetson.GPIO
                pin_state = JetsonGPIO.input(self.gpio_pin)
                # Return True if pin is LOW - obstacle detected
                return pin_state == JetsonGPIO.LOW
                
        except Exception as e:
            print(f"[WARN] Failed to read IR obstacle sensor: {e}")
            return False
        
        return False
    
    def close(self):
        """Cleanup GPIO resources."""
        if not self._initialized:
            return
        
        try:
            if self._gpio_lib == "lgpio" and self._chip is not None:
                lgpio.gpiochip_close(self._chip)
                self._chip = None
            elif self._gpio_lib == "RPi" and GPIO:
                GPIO.cleanup(self.gpio_pin)
            elif self._gpio_lib == "Jetson" and JetsonGPIO:
                JetsonGPIO.cleanup(self.gpio_pin)
            
            self._initialized = False
        except Exception as e:
            print(f"[WARN] Error during GPIO cleanup: {e}")
