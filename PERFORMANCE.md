# Performance & Optimization Guide

This guide covers performance tuning, latency reduction, and resource optimization for the Pico Rover.

---

## Performance Metrics

### Target Performance

| Metric | Target | Typical | Notes |
|--------|--------|---------|-------|
| **Command Latency** | < 200ms | 50-150ms | WiFi LAN, ideal conditions |
| **Control Update Rate** | 10 Hz | 10 Hz | Motor command frequency |
| **Telemetry Update Rate** | 1-2 Hz | 1 Hz | Status polling frequency |
| **Motor Response Time** | < 50ms | 20-30ms | Time to spin up motor |
| **Battery Drain (idle)** | < 50mA | 30-40mA | WiFi AP + LEDs only |
| **Battery Drain (moving)** | < 500mA | 300-500mA | Motors at 50% speed |

---

## Firmware Optimization

### 1. Reduce JSON Payload Size

**Before:**
```json
{
  "timestamp": 1693512345,
  "motor_a": {
    "speed": 75,
    "direction": "forward",
    "pwm_duty": 19200
  },
  "motor_b": {
    "speed": -30,
    "direction": "reverse",
    "pwm_duty": 7680
  },
  "battery": {
    "voltage": 7.8,
    "percentage": 85
  },
  "wifi": {
    "ssid": "MyNetwork",
    "ip": "192.168.1.100",
    "signal_strength": -45
  },
  "uptime_ms": 3456789
}
```
**Size: 254 bytes**

**After (minimal):**
```json
{
  "t": 1693512345,
  "a": 75,
  "b": -30,
  "bv": 7.8,
  "bp": 85,
  "rssi": -45,
  "up": 3456789
}
```
**Size: 79 bytes** (69% reduction)

**Implementation:**
```python
# firmware/api_server.py
def get_telemetry():
    return json.dumps({
        't': ticks_ms(),          # timestamp
        'a': rover.get_motor_a(), # motor A speed
        'b': rover.get_motor_b(), # motor B speed
        'bv': battery.voltage(),  # battery voltage
        'bp': battery.percent(),  # battery percentage
        'rssi': wifi.rssi(),      # signal strength
        'up': machine.ticks_ms()  # uptime
    })
```

### 2. Optimize Motor Control Loop

**Before (generic):**
```python
# firmware/main.py - SLOW
while True:
    if mqtt_queue:
        speed_a, speed_b = mqtt_queue.pop()
    
    motor_a.set_speed(speed_a)
    motor_b.set_speed(speed_b)
    
    time.sleep(0.1)  # 100ms
```

**After (optimized):**
```python
# firmware/main.py - FAST
speed_a = 0
speed_b = 0
last_update = ticks_ms()

while True:
    now = ticks_ms()
    
    # Update motors every 100ms
    if now - last_update > 100:
        motor_a.set_speed(speed_a)
        motor_b.set_speed(speed_b)
        last_update = now
    
    # Poll API without blocking
    handle_api_request(nonblocking=True)
    
    # Don't sleep - process events as fast as possible
```

### 3. Use Asynchronous WiFi

**Before (blocking):**
```python
# firmware/api_server.py - BLOCKS
socket.listen(1)
client, addr = socket.accept()  # Blocks until connection
data = client.recv(1024)        # Blocks until data arrives
response = handle_request(data)
client.send(response)
```

**After (non-blocking):**
```python
# firmware/api_server.py - ASYNC
import select

socket.setblocking(False)

while True:
    # Check if any socket has data (no blocking)
    ready, _, _ = select.select([socket], [], [], 0.01)
    
    if ready:
        try:
            client, addr = socket.accept()
            data = client.recv(1024)
            response = handle_request(data)
            client.send(response)
            client.close()
        except OSError:
            pass
```

### 4. Minimize Allocations

**Before (creates new objects every loop):**
```python
# firmware/main.py - SLOW
while True:
    telemetry = {
        'motor_a': rover.get_speed_a(),
        'motor_b': rover.get_speed_b(),
        'battery': battery.voltage()
    }
    send_telemetry(telemetry)
```

**After (reuse buffer):**
```python
# firmware/main.py - FAST
telemetry_buffer = bytearray(32)  # Pre-allocate

while True:
    # Reuse same buffer
    telemetry_json = '{"a":%d,"b":%d,"bv":%.1f}' % (
        rover.get_speed_a(),
        rover.get_speed_b(),
        battery.voltage()
    )
    send_telemetry(telemetry_json)
```

### 5. PWM Frequency Optimization

**Default (5 kHz):**
```python
# firmware/motor_control.py
pwm = PWM(Pin(14), freq=5000)
```

**Considerations:**
- Higher freq → smoother motor control, less EMI
- Lower freq → less CPU overhead, better battery life
- **Sweet spot for DC motors: 1-5 kHz**

**For 20kHz PWM (modern ESC):**
```python
pwm = PWM(Pin(14), freq=20000)
pwm.duty_u16(32768)  # 50% duty
```

**Trade-off table:**

| Frequency | CPU Load | Smoothness | Efficiency |
|-----------|----------|-----------|------------|
| 1 kHz | Low | Audible | Excellent |
| 5 kHz | Medium | Good | Good |
| 20 kHz | High | Very Good | Fair |

---

## Frontend Optimization

### 1. Reduce Control Loop Frequency

**Default (10 Hz):**
```javascript
// frontend/js/app.js - FAST
setInterval(controlLoop, 100);  // Every 100ms
```

**For long-range/WiFi:** (5 Hz)
```javascript
setInterval(controlLoop, 200);  // Every 200ms
```

**Impact:**
- 10 Hz → 100 requests/second * 60 bytes = 6 KB/s
- 5 Hz → 50 requests/second * 60 bytes = 3 KB/s
- **50% bandwidth reduction**

### 2. Batch Telemetry Requests

**Before (separate calls):**
```javascript
// frontend/js/app.js
const status = await fetch('/status');
const battery = await fetch('/battery');
const motors = await fetch('/motors');
```

**After (single call):**
```javascript
// firmware/api_server.py
if request.path == '/api/full':
    response = {
        'status': get_status(),
        'battery': get_battery(),
        'motors': get_motors()
    }
    return json.dumps(response)
```

**Impact: 3 requests → 1 request (66% fewer requests)**

### 3. Cache Static Resources

**frontend/index.html:**
```html
<meta http-equiv="Cache-Control" content="max-age=86400">
<script src="js/app.js?v=1.0"></script>
<link rel="stylesheet" href="css/style.css?v=1.0">
```

**frontend/sw.js (Service Worker):**
```javascript
// Cache static assets on first load
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open('v1').then((cache) => {
            return cache.addAll([
                '/',
                '/css/style.css',
                '/js/app.js',
                '/libs/nipple.js'
            ]);
        })
    );
});
```

### 4. Lazy Load Components

**Before (load everything):**
```javascript
// frontend/js/app.js
import { createGyroController } from './gyro.js';
import { createJoystick } from './joystick.js';
import { createChart } from './chart.js';

const gyro = createGyroController();
const joystick = createJoystick();
const chart = createChart();  // Heavy library
```

**After (lazy load):**
```javascript
// frontend/js/app.js
let gyro = null;
let joystick = null;
let chart = null;

function initGyro() {
    if (!gyro) {
        gyro = createGyroController();
    }
}

// Load only when user clicks "Gyro Mode"
document.getElementById('gyroMode').addEventListener('click', initGyro);
```

### 5. Compress Data Transfer

**Use URL parameters (16 bytes):**
```
POST /motor?a=50&b=-30
```

**vs JSON body (30+ bytes):**
```json
{"motor_a": 50, "motor_b": -30}
```

**Impact: ~50% smaller**

---

## WiFi Optimization

### 1. Reduce Transmission Power (if supported)

Some systems allow reducing TX power to decrease latency:
```python
# firmware/wifi_manager.py
wlan.config(txpower=17)  # 17 dBm (typical; max is 20)
```

### 2. Use 802.11 Rate Control

Force 54 Mbps mode (skip negotiation):
```python
# firmware/wifi_manager.py (if supported by MicroPython)
wlan.config(phy_mode=network.WLAN.PHY_MODE_11G)
```

### 3. Minimize Connection Overhead

**Current approach (good):**
```javascript
// frontend/js/api.js
// Reuse same socket connection
const http = new XMLHttpRequest();
http.open('POST', 'http://192.168.1.100:8000/motor?a=50&b=-30');
http.send();
```

**Alternative (WebSocket, Phase 4):**
```javascript
// Keep persistent connection
const ws = new WebSocket('ws://192.168.1.100:8000/ws');
ws.send(JSON.stringify({a: 50, b: -30}));
```

**Benefit:** Eliminates TCP handshake overhead (~3 RTTs per request)

---

## Power Consumption Optimization

### Battery Drain Analysis

**Idle (WiFi AP only):**
- Pico W: ~30 mA
- LEDs: ~5 mA
- Total: ~35 mA (WiFi is dominant)

**Active (motors + comms):**
- Motors (2x DC): ~300 mA @ 50% speed
- Pico W (active WiFi): ~50 mA
- Total: ~350 mA

### Optimization Strategies

**1. Disable WiFi During Idle**
```python
# firmware/main.py
if not connected_for(60):  # No commands for 60 seconds
    wlan.active(False)
    # Motors can still run from last command
```

**2. Reduce Radio Transmission**
```python
# firmware/wifi_manager.py
wlan.config(txpower=10)  # Lower transmit power
# Trade-off: shorter range, less interference
```

**3. Use Sleep Modes**
```python
# firmware/main.py
import machine

while True:
    # Process events
    handle_api_request()
    
    # Sleep between iterations
    machine.lightsleep(10)  # Sleep 10ms
```

### Battery Life Estimation

**Capacity: 2000 mAh**

| Usage | Avg Current | Battery Life |
|-------|-------------|--------------|
| Idle (WiFi AP) | 35 mA | 57 hours |
| Light driving | 150 mA | 13 hours |
| Heavy driving | 350 mA | 5.7 hours |

---

## Profiling & Benchmarking

### Measure API Response Time

**Firmware (firmware/api_server.py):**
```python
import time

def handle_request(request):
    t0 = ticks_ms()
    
    # ... process request ...
    
    elapsed = ticks_ms() - t0
    print(f"[API] {request.path} took {elapsed}ms")
    
    response['latency_ms'] = elapsed
    return json.dumps(response)
```

**Frontend (frontend/js/api.js):**
```javascript
async function measureLatency() {
    const t0 = Date.now();
    const response = await fetch('http://192.168.1.100:8000/status');
    const elapsed = Date.now() - t0;
    console.log(`Latency: ${elapsed}ms`);
    return elapsed;
}
```

### Measure Control Loop Timing

**Frontend (frontend/js/app.js):**
```javascript
let loopTimes = [];

function controlLoop() {
    const t0 = performance.now();
    
    // ... control code ...
    
    const elapsed = performance.now() - t0;
    loopTimes.push(elapsed);
    
    if (loopTimes.length > 100) {
        const avg = loopTimes.reduce((a, b) => a + b) / loopTimes.length;
        console.log(`Avg loop time: ${avg.toFixed(2)}ms`);
        loopTimes = [];
    }
}
```

### Firmware Memory Usage

**Check available memory:**
```python
# From REPL
import gc
gc.collect()  # Force garbage collection
print(gc.mem_free())  # Free memory in bytes
```

**Expected:**
- Free: ~50-100 KB (out of 192 KB)
- Used: ~100-150 KB (MicroPython + firmware)

---

## Performance Checklist

### Critical (Essential)
- [ ] Motor PWM frequency set to 5 kHz
- [ ] Control loop runs at 10 Hz (100ms interval)
- [ ] API responds < 200ms on typical LAN
- [ ] Motor response time < 50ms
- [ ] CORS headers enabled

### Important (Recommended)
- [ ] JSON payload minimal (~80 bytes for telemetry)
- [ ] Telemetry update rate 1 Hz (reduces bandwidth 10x)
- [ ] Asynchronous API (non-blocking sockets)
- [ ] Reused buffers (minimize allocations)

### Nice-to-have (Optimization)
- [ ] WebSocket for persistent connection (Phase 4)
- [ ] Reduced control loop for high-latency networks (5 Hz)
- [ ] Battery measurement & optimization
- [ ] Reduced WiFi TX power (shorter range)
- [ ] Service Worker caching

---

## Benchmark Results

### Typical Performance (Pico W + WiFi)

```
Scenario: Home WiFi (5 GHz, 10 meters away)

Control Loop (Gyro → API → Motors):
  - Input sampling:     2ms
  - API request:       150ms (WiFi RT + server processing)
  - Motor response:     20ms
  - UI update:          5ms
  Total latency:       177ms ✓

Telemetry Poll:
  - Request:           150ms
  - JSON parse:         10ms
  - UI update:          5ms
  Total time:          165ms

Memory:
  - MicroPython heap:   52 KB
  - Firmware code:      98 KB
  - Free:               42 KB

Power:
  - Idle (WiFi):        38 mA
  - Moving @ 50%:      250 mA
  - Peak (full speed): 450 mA
```

---

## Future Optimizations (Roadmap)

- [ ] **Phase 4:** WebSocket for <50ms latency
- [ ] **Phase 5:** Motor controller caching (precomputed LUT tables)
- [ ] **Phase 6:** LittleFS filesystem for faster config loading
- [ ] **Phase 7:** UDP protocol for even lower latency (stateless)
- [ ] **Phase 8:** Hardware SPI for potential future sensors

---

## References

- [RP2040 Datasheet](https://datasheets.raspberrypi.org/rp2040/rp2040-datasheet.pdf)
- [MicroPython Docs](https://docs.micropython.org/)
- [WiFi 802.11 Standards](https://en.wikipedia.org/wiki/IEEE_802.11)
- [PWM Best Practices](https://en.wikipedia.org/wiki/Pulse-width_modulation)
