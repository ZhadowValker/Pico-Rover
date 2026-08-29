# Customization Guide

This guide explains how to extend and modify the Pico Rover to add new features, sensors, and capabilities.

---

## Table of Contents
1. [Adding Sensors](#adding-sensors)
2. [Changing Motor Configuration](#changing-motor-configuration)
3. [Modifying Control Modes](#modifying-control-modes)
4. [Custom Behaviors](#custom-behaviors)
5. [Web Frontend Customization](#web-frontend-customization)

---

## Adding Sensors

### Temperature Sensor (DHT22)

**Hardware:**
- DHT22 temperature/humidity sensor
- Data pin → GPIO 2

**Firmware Steps:**

1. **Update config.py:**
```python
# config.py
DHT_PIN = 2
```

2. **Create dht_sensor.py:**
```python
# firmware/dht_sensor.py
from machine import Pin
import dht

class TemperatureSensor:
    def __init__(self, pin_num):
        self.sensor = dht.DHT22(Pin(pin_num))
    
    def read(self):
        try:
            self.sensor.measure()
            return {
                'temperature': self.sensor.temperature(),
                'humidity': self.sensor.humidity()
            }
        except Exception as e:
            print(f"[DHT] Error: {e}")
            return {'temperature': 0, 'humidity': 0}
```

3. **Update api_server.py:**
```python
# firmware/api_server.py
from dht_sensor import TemperatureSensor

temp_sensor = TemperatureSensor(DHT_PIN)

def handle_request(request):
    if request.path == '/api/temperature':
        data = temp_sensor.read()
        response = {
            'temperature': data['temperature'],
            'humidity': data['humidity'],
            'status': 'ok'
        }
        return json.dumps(response)
```

4. **Update frontend UI** (`frontend/js/ui.js`):
```javascript
// Add to telemetry display
function updateTelemetry(data) {
    if (data.temperature !== undefined) {
        document.getElementById('temp').textContent = 
            `${data.temperature.toFixed(1)}°C`;
    }
}
```

### Distance Sensor (HC-SR04 Ultrasonic)

**Hardware:**
- HC-SR04 ultrasonic sensor
- Trig → GPIO 3
- Echo → GPIO 4

**Firmware:**
```python
# firmware/distance_sensor.py
from machine import Pin, time_pulse_us
import time

class DistanceSensor:
    def __init__(self, trig_pin, echo_pin):
        self.trig = Pin(trig_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)
    
    def distance_cm(self):
        self.trig.off()
        time.sleep_us(2)
        self.trig.on()
        time.sleep_us(10)
        self.trig.off()
        
        pulse_time = time_pulse_us(self.echo, 1, 30000)
        if pulse_time < 0:
            return None
        
        distance = (pulse_time / 2) / 29.1
        return distance
```

### Camera (OV2640 via USB)

Not directly supported on Pico W (no CSI connector), but you can:
1. Use external USB camera + Pico as relay
2. Send images to separate server
3. Use Pico as motion detector (via HC-SR04)

---

## Changing Motor Configuration

### Using Different Motor Driver (L298N)

**Hardware Differences:**
- L298N has different pin layout
- No PWM input - just IN pins
- Separate Enable pins for speed control

**Update config.py:**
```python
# config.py - L298N configuration
MOTOR_A = {
    'IN1': 19,  # Direction control
    'IN2': 18,
    'ENA': 14   # Enable (PWM)
}
MOTOR_B = {
    'IN1': 17,
    'IN2': 16,
    'ENB': 15
}
MOTOR_DRIVER = 'L298N'
```

**Update motor_control.py:**
```python
# firmware/motor_control.py
if MOTOR_DRIVER == 'L298N':
    class Motor:
        def __init__(self, in1, in2, ena):
            self.in1 = Pin(in1, Pin.OUT)
            self.in2 = Pin(in2, Pin.OUT)
            self.pwm = PWM(Pin(ena), freq=5000)
        
        def set_speed(self, speed):  # -100 to 100
            duty = int(abs(speed) * 655.35)  # Convert to u16
            self.pwm.duty_u16(duty)
            
            if speed > 0:
                self.in1.on()
                self.in2.off()
            elif speed < 0:
                self.in1.off()
                self.in2.on()
            else:
                self.in1.off()
                self.in2.off()
```

### Using 4-Motor Configuration (Tank-style)

**Hardware:**
- Motors on each side of tank
- Left (motors A+B) vs Right (motors C+D)

**Update config.py:**
```python
# config.py
MOTOR_CONFIG = 'TANK'  # or 'DIFFERENTIAL' (default)

MOTOR_LEFT = {
    'MOTORS': ['A', 'B'],  # Parallel drive
    'PWM': 14
}
MOTOR_RIGHT = {
    'MOTORS': ['C', 'D'],
    'PWM': 15
}
```

**Update motor_control.py:**
```python
# firmware/motor_control.py
if MOTOR_CONFIG == 'TANK':
    class Rover:
        def __init__(self):
            self.motor_a = Motor(19, 18, 14)
            self.motor_b = Motor(...)
            self.motor_c = Motor(...)
            self.motor_d = Motor(...)
        
        def drive(self, left_speed, right_speed):
            # Both left motors same speed
            self.motor_a.set_speed(left_speed)
            self.motor_b.set_speed(left_speed)
            # Both right motors same speed
            self.motor_c.set_speed(right_speed)
            self.motor_d.set_speed(right_speed)
```

---

## Modifying Control Modes

### Adding Obstacle Avoidance

**Firmware:**
```python
# firmware/behaviors.py
from distance_sensor import DistanceSensor

class ObstacleAvoidance:
    def __init__(self, rover, sensor):
        self.rover = rover
        self.sensor = sensor
        self.threshold = 20  # cm
    
    def update(self):
        distance = self.sensor.distance_cm()
        
        if distance < self.threshold:
            # Back up and turn
            self.rover.drive(-50, -50)
            import time
            time.sleep(0.3)
            self.rover.drive(-30, 50)  # Right turn
        else:
            # Normal drive (set by user input)
            pass
```

**Update api_server.py:**
```python
from behaviors import ObstacleAvoidance

obstacle_avoid = ObstacleAvoidance(rover, distance_sensor)

def handle_request(request):
    if request.path == '/behavior/avoid' and method == 'POST':
        obstacle_avoid.enable = True
        return json.dumps({'status': 'obstacle avoidance enabled'})
```

### Adding Line-Following

**Hardware:**
- 3x IR reflectance sensors on GPIO 5, 6, 7

**Firmware:**
```python
# firmware/line_follower.py
from machine import Pin, ADC

class LineFollower:
    def __init__(self, left_pin, center_pin, right_pin):
        self.sensors = [ADC(Pin(p)) for p in [left_pin, center_pin, right_pin]]
        self.threshold = 40000  # Adjust based on your sensors
    
    def read(self):
        readings = [s.read_u16() for s in self.sensors]
        return [r > self.threshold for r in readings]
    
    def get_steering(self):
        # Returns -1 (left), 0 (center), 1 (right)
        left, center, right = self.read()
        
        if center:
            return 0  # On line
        elif left:
            return -1  # Adjust left
        elif right:
            return 1  # Adjust right
        else:
            return 0  # Lost line
```

**Update api_server.py:**
```python
line_follower = LineFollower(5, 6, 7)

if request.path == '/behavior/follow' and method == 'POST':
    steering = line_follower.get_steering()
    # Apply to motor speed differential
    return json.dumps({'steering': steering})
```

### Adding Voice Commands

**Frontend:**
```javascript
// frontend/js/voice.js
class VoiceController {
    constructor(roverAPI) {
        this.api = roverAPI;
        this.recognition = new webkitSpeechRecognition();
    }
    
    start() {
        this.recognition.onresult = (event) => {
            const command = event.results[0][0].transcript.toLowerCase();
            
            if (command.includes('forward')) {
                this.api.sendMotor(100, 100);
            } else if (command.includes('stop')) {
                this.api.sendMotor(0, 0);
            }
        };
        this.recognition.start();
    }
}
```

---

## Custom Behaviors

### Recording & Playback (Autonomous Paths)

**Firmware:**
```python
# firmware/behavior_recorder.py
class PathRecorder:
    def __init__(self):
        self.path = []  # List of (motor_a, motor_b, duration_ms)
    
    def record(self, motor_a, motor_b):
        self.path.append((motor_a, motor_b, 100))  # 100ms step
    
    def playback(self, rover):
        for a, b, duration in self.path:
            rover.drive(a, b)
            time.sleep_ms(duration)
        rover.stop()
    
    def save(self, filename):
        import json
        with open(filename, 'w') as f:
            json.dump(self.path, f)
    
    def load(self, filename):
        import json
        with open(filename, 'r') as f:
            self.path = json.load(f)
```

**API Endpoint:**
```python
recorder = PathRecorder()
recording = False

if request.path == '/behavior/record/start':
    recording = True
    recorder.path = []
    return json.dumps({'status': 'recording started'})

elif request.path == '/behavior/record/stop':
    recording = False
    recorder.save('path.json')
    return json.dumps({'status': 'recording saved'})

elif request.path == '/behavior/playback':
    recorder.playback(rover)
    return json.dumps({'status': 'playback complete'})
```

### LED Status Indicator

**Hardware:**
- LED on GPIO 25 (built-in on Pico W)

**Firmware:**
```python
# firmware/led_status.py
from machine import Pin

class LEDStatus:
    def __init__(self):
        self.led = Pin(25, Pin.OUT)
        self.state = 'idle'
    
    def set_state(self, state):
        states = {
            'idle': (1, 0, 0),      # On
            'connecting': (0.5, 0.5, 0),  # Blink
            'connected': (0, 1, 0),  # Fast blink
            'error': (0.1, 0.1, 0)  # Fast blink
        }
        
        if state in states:
            self.state = state
```

---

## Web Frontend Customization

### Changing Control Layout

**Edit frontend/index.html:**
```html
<!-- Add new control section -->
<div class="control-section">
    <button id="autonomousBtn">🤖 Autonomous</button>
    <button id="lineFollowBtn">➡️ Follow Line</button>
</div>
```

**Edit frontend/js/app.js:**
```javascript
document.getElementById('autonomousBtn').addEventListener('click', async () => {
    await roverAPI.sendRequest('/behavior/avoid', 'POST');
    showNotification('Obstacle avoidance enabled');
});
```

### Dark/Light Theme Toggle

**Edit frontend/css/style.css:**
```css
:root {
    --bg-dark: #121212;
    --bg-light: #ffffff;
    --text-dark: #ffffff;
    --text-light: #000000;
}

body.light-theme {
    --bg-color: var(--bg-light);
    --text-color: var(--text-light);
}

body.dark-theme {
    --bg-color: var(--bg-dark);
    --text-color: var(--text-dark);
}
```

**Edit frontend/js/ui.js:**
```javascript
function toggleTheme() {
    document.body.classList.toggle('light-theme');
    localStorage.setItem('theme', 
        document.body.classList.contains('light-theme') ? 'light' : 'dark');
}
```

### Adding Real-time Graphing

**Use Chart.js** (add to frontend/index.html):
```html
<canvas id="batteryChart"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

**frontend/js/ui.js:**
```javascript
const ctx = document.getElementById('batteryChart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [{
            label: 'Battery %',
            data: []
        }]
    }
});

function updateChart(voltage) {
    chart.data.labels.push(new Date().toLocaleTimeString());
    chart.data.datasets[0].data.push(voltage);
    
    if (chart.data.labels.length > 60) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    chart.update();
}
```

### Adding Settings Panel

**frontend/index.html:**
```html
<div id="settingsPanel" class="hidden">
    <label>Control Rate (Hz):
        <input type="number" id="controlRate" min="1" max="20" value="10">
    </label>
    <label>Telemetry Rate (Hz):
        <input type="number" id="telemetryRate" min="1" max="10" value="1">
    </label>
    <button onclick="saveSettings()">Save</button>
</div>
```

**frontend/js/app.js:**
```javascript
function saveSettings() {
    const controlRate = document.getElementById('controlRate').value;
    const telemetryRate = document.getElementById('telemetryRate').value;
    
    controlIntervalMs = 1000 / controlRate;
    telemetryIntervalMs = 1000 / telemetryRate;
    
    localStorage.setItem('settings', JSON.stringify({
        controlRate, telemetryRate
    }));
}
```

---

## Advanced: Custom MicroPython Modules

### Creating Reusable Library

**firmware/rover_lib.py:**
```python
# Generic rover library
class RoverBase:
    def __init__(self, motor_pins, pwm_pins):
        self.motors = [Motor(*pins) for pins in motor_pins]
        self.pwm_freq = 5000
    
    def drive(self, speeds):
        """speeds: list of motor speeds [-100, 100]"""
        for motor, speed in zip(self.motors, speeds):
            motor.set_speed(speed)
    
    def stop(self):
        """Stop all motors"""
        for motor in self.motors:
            motor.set_speed(0)
```

**Use in firmware/main.py:**
```python
from rover_lib import RoverBase

rover = RoverBase(
    motor_pins=[(19, 18), (17, 16)],
    pwm_pins=[14, 15]
)
```

---

## Testing Custom Code

### Unit Tests (on Pico REPL)

```python
from motor_control import Motor
from machine import Pin, PWM

# Test Motor class
motor_a = Motor(Pin(19), Pin(18), PWM(Pin(14), freq=5000))
motor_a.set_speed(50)
assert motor_a.get_speed() == 50, "Speed mismatch"
print("✓ Motor speed test passed")
```

### Integration Tests

```python
from api_server import handle_request
from motor_control import Rover

# Mock request
class MockRequest:
    path = '/motor?a=50&b=75'
    method = 'POST'

rover = Rover()
response = handle_request(MockRequest())
print(response)  # Should be JSON with motor speeds
```

---

## Performance Optimization Tips

1. **Reduce JSON payload** - remove unused telemetry fields
2. **Increase control loop interval** - 100ms → 150ms if latency-tolerant
3. **Use fixed-point math** - avoid floating point in tight loops
4. **Cache DNS** - store rover IP in localStorage
5. **Minimize WiFi transmissions** - batch commands

---

## Next Steps

- Explore [MicroPython docs](https://docs.micropython.org/)
- Join [Pico community](https://github.com/raspberrypi/pico)
- Check [Wokwi simulator](https://wokwi.com) for hardware prototyping
- Review [RP2040 datasheet](https://datasheets.raspberrypi.org/rp2040/rp2040-datasheet.pdf) for low-level details
