# config.py - Pico W Rover Configuration

# ============ Motor Pins (DRV8833) ============
# Motor A (Left)
MOTOR_A_IN1 = 19
MOTOR_A_IN2 = 18
MOTOR_A_PWM = 14

# Motor B (Right)
MOTOR_B_IN1 = 17
MOTOR_B_IN2 = 16
MOTOR_B_PWM = 15

# PWM frequency
PWM_FREQ = 5000

# ============ Sensor Pins ============
BATTERY_ADC = 26  # ADC0
BATTERY_SCALE = 3.3 / 65535  # Convert ADC to voltage

# ============ WiFi Settings ============
AP_SSID = 'RoverSetup'
AP_PASSWORD = 'rover1234'
AP_IP = '192.168.4.1'
AP_SUBNET = '255.255.255.0'

# ============ Server Settings ============
SERVER_PORT = 8000
MAX_SPEED = 100

# ============ Telemetry ============
TELEMETRY_INTERVAL = 1000  # ms
STATUS_UPDATE_RATE = 10  # Hz
