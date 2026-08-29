# System Architecture

Comprehensive technical documentation of the Pico Rover's hardware, firmware, and software architecture.

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Hardware Architecture](#hardware-architecture)
3. [Firmware Architecture](#firmware-architecture)
4. [Frontend Architecture](#frontend-architecture)
5. [Communication Protocols](#communication-protocols)
6. [Data Flow](#data-flow)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Pico Rover System                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Hardware Layer                                            │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ • Raspberry Pi Pico W (RP2040 + WiFi)                    │   │
│  │ • DRV8833 Motor Driver (2x DC motors)                    │   │
│  │ • Battery (7.2-8.4V, 2S LiPo)                            │   │
│  │ • USB-C Power Management                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Firmware Layer (MicroPython)                              │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ • Motor Control (PWM, speed mapping)                     │   │
│  │ • WiFi Manager (AP + Station mode)                       │   │
│  │ • REST API Server (port 8000)                            │   │
│  │ • Battery Monitoring (ADC)                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓ (HTTP)                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Network Layer                                             │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ • WiFi LAN (802.11 b/g/n 2.4 GHz)                        │   │
│  │ • REST API (JSON)                                        │   │
│  │ • CORS-enabled                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Frontend Layer (Web)                                      │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │ • Control Modes (Gyro, Joystick, Keyboard)               │   │
│  │ • Telemetry Display (Battery, Speed, Signal)             │   │
│  │ • Auto-Discovery (IP scanning)                           │   │
│  │ • Deployment: GitHub Pages                               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Hardware Architecture

### Electrical Schematic

```
┌─────────────────────────────────┐
│      Battery (7.2-8.4V)          │
│     2S LiPo / 4xAA              │
│                                  │
│  [+] ────────────┬──────────┐   │
│                  │          │   │
│              ┌───┴──┐    ┌──┴─┐ │
│              │      │    │    │ │
│            [USB]  [5V]  [GND]  │
│              │      │    │    │ │
│  Pico W  ────┴──┬───┴────┴────┘ │
│                 │                │
│         VBUS,GND,GPIO26          │
│                 │                │
└─────────────────┼────────────────┘
                  │
                  └──→ ADC (Battery monitoring)
                     GPIO 26 ← 10k ← Battery+
                               10k ← GND


       ┌─────────────────────────────┐
       │     Pico W (RP2040)          │
       │                              │
       │  GPIO 19 ──────→ IN1        │
       │  GPIO 18 ──────→ IN2        │  DRV8833
       │  GPIO 14 ──────→ PWM-A      │  Motor A
       │                              │
       │  GPIO 17 ──────→ IN3        │
       │  GPIO 16 ──────→ IN4        │
       │  GPIO 15 ──────→ PWM-B      │
       │                              │
       │  GPIO 3  ──────→ Trig       │  HC-SR04
       │  GPIO 4  ──────→ Echo       │  (optional)
       │                              │
       │  GPIO 25 ──────→ LED (indicator)
       └─────────────────────────────┘
```

### Pin Mapping Summary

| GPIO | Function | Direction | Notes |
|------|----------|-----------|-------|
| 14 | Motor A PWM | OUT | PWM 5 kHz |
| 15 | Motor B PWM | OUT | PWM 5 kHz |
| 16 | Motor B IN4 | OUT | Direction control |
| 17 | Motor B IN3 | OUT | Direction control |
| 18 | Motor A IN2 | OUT | Direction control |
| 19 | Motor A IN1 | OUT | Direction control |
| 25 | LED (status) | OUT | Built-in Pico LED |
| 26 | Battery ADC | IN | Voltage sense |

### Power Budget

**Supply: 2S LiPo (7.2-8.4V nominal, 2000 mAh)**

| Component | Typical | Max | Notes |
|-----------|---------|-----|-------|
| Pico W (idle) | 20 mA | 40 mA | WiFi active |
| Motors (moving) | 250 mA | 500 mA | Depends on load |
| DRV8833 (no load) | 5 mA | 10 mA | Quiescent |
| LED/misc | 5 mA | 20 mA | Status indicator |
| **Total (light)** | **280 mA** | **500 mA** | Typical operation |
| **Total (idle)** | **30 mA** | **60 mA** | WiFi AP only |

**Expected Runtime:**
- Light use (10% throttle): ~7 hours
- Normal use (50% throttle): ~4 hours
- Heavy use (100% throttle): ~2 hours

---

## Firmware Architecture

### Module Organization

```
firmware/
├── main.py              # Entry point, initialization
├── config.py            # Constants, pin definitions
├── motor_control.py     # Motor + Rover classes
├── wifi_manager.py      # WiFi AP/Station management
├── api_server.py        # REST HTTP server
└── (optional extensions)
    ├── dht_sensor.py    # Temperature/humidity
    ├── distance_sensor.py
    └── line_follower.py
```

### Boot Sequence

```
┌─────────────────────────────┐
│ main.py                      │
│ 1. Import modules            │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ config.py                    │
│ 2. Load pin config           │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ motor_control.py             │
│ 3. Initialize motors         │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ wifi_manager.py              │
│ 4. WiFi setup                │
│    a. Try to connect station │
│    b. If fail, start AP      │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ api_server.py                │
│ 5. Start REST API (port 8000)│
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ RUNNING                      │
│ • Accept API requests        │
│ • Process motor commands     │
│ • Serve telemetry            │
└─────────────────────────────┘
```

### Motor Control State Machine

```
┌────────────────────┐
│ Motor.set_speed(s) │
└─────────┬──────────┘
          ↓
    ┌─────────────┐
    │ s in [-100..100]? │
    └──┬──────────┬──┘
       YES      NO → Error
       ↓
    ┌──────────────────┐
    │ Convert speed → PWM
    │ s=50 → 19200/65535 │
    └──┬───────────────┘
       ↓
    ┌──────────────────┐
    │ Set direction    │
    │ s>0: IN1=1, IN2=0│
    │ s<0: IN1=0, IN2=1│
    │ s=0: both low    │
    └──┬───────────────┘
       ↓
    ┌──────────────────┐
    │ Set PWM duty     │
    │ pwm.duty_u16()   │
    └──┬───────────────┘
       ↓
    [Motor spinning]
```

### WiFi Connection Flow

```
POWER ON
   ↓
WiFi.auto_connect()
   ↓
   ├─ YES → Connected to home network
   │         IP: DHCP assigned
   │         MODE: Station (normal)
   │         
   └─ NO → Start AP
           SSID: "RoverSetup"
           IP: 192.168.4.1
           MODE: Access Point (setup)

             ↓
          User phone
          connects to AP
             ↓
          Opens http://192.168.4.1
             ↓
          Scans networks
             ↓
          Enters WiFi password
             ↓
          POST /api/connect
             ↓
          Pico saves to LittleFS
             ↓
          Pico reboots
             ↓
          WiFi.auto_connect() succeeds
             ↓
          Back to Station mode
```

### API Request Handler

```
HTTP Request (port 8000)
   ↓
socket.accept()
   ↓
Parse HTTP headers
   ↓
   ├─ GET /                → JSON: {name, version}
   │
   ├─ GET /status          → JSON: {motor_a, motor_b, battery, ...}
   │
   ├─ POST /motor?a=X&b=Y  → Call rover.drive(X, Y)
   │                          Return: {motor_a, motor_b}
   │
   ├─ POST /motor/stop     → Call rover.stop()
   │
   ├─ GET /api/scan        → WiFi scan (AP mode only)
   │
   ├─ POST /api/connect    → Save WiFi config + reboot
   │
   └─ 404                  → Error response

   ↓
Send response (JSON)
   ↓
Add CORS headers
   ↓
Close connection
```

### Telemetry Update Loop

```
┌──────────────────────────┐
│ Main loop (continuous)    │
└──────────┬───────────────┘
           ↓
    ┌─────────────────────┐
    │ Check time >= 1000ms?│ (telemetry rate)
    └─┬──────────────────┬┘
      NO              YES
      ↓                ↓
   Continue      ┌────────────────┐
                 │ Read sensors   │
                 │ • Motor speeds │
                 │ • Battery V    │
                 │ • WiFi RSSI    │
                 └────┬───────────┘
                      ↓
                 ┌────────────────┐
                 │ Build JSON     │
                 │ (minimal)      │
                 └────┬───────────┘
                      ↓
                 [Cached for API]
                      ↓
                 Reset timer
```

---

## Frontend Architecture

### Module Organization

```
frontend/
├── index.html           # Main UI
├── css/
│   └── style.css        # Styling + responsive layout
├── js/
│   ├── app.js           # Main orchestration + 10Hz loop
│   ├── api.js           # HTTP client + auto-discovery
│   ├── control.js       # Input mode mapping
│   ├── gyro.js          # DeviceOrientation handler
│   ├── joystick.js      # Virtual joystick wrapper
│   └── ui.js            # DOM updates + notifications
└── libs/
    └── nipple.js        # Joystick library (minimal)
```

### Control Loop Architecture

```
10Hz Timer (100ms)
   ↓
controlLoop()
   ↓
┌────────────────────────────┐
│ 1. Read Input              │
│    • Gyroscope (pitch/roll)│
│    • Joystick (x/y)        │
│    • Keyboard (arrows)     │
│                            │
│    → controlMode determines│
│       which input is used  │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│ 2. Map to Motor Speeds     │
│    • Input range: [-1, 1]  │
│    • Output range: [-100, 100]
│                            │
│    • Differential steering │
│      - Forward: a=100, b=100│
│      - Left turn: a=75, b=100│
│      - Spin: a=100, b=-100 │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│ 3. Send API Request        │
│    POST /motor?a=X&b=Y     │
│                            │
│    (async, ~100-150ms RTT) │
└─────────────┬──────────────┘
              ↓
┌────────────────────────────┐
│ 4. Update UI               │
│    • Speed indicators      │
│    • Control mode display  │
│    • Connection status     │
└────────────────────────────┘

Parallel: 1Hz Telemetry Poll
   ↓
GET /status
   ↓
Parse JSON
   ↓
Update battery/latency/signal
   ↓
Render on UI
```

### State Management

```
┌─────────────────────────────┐
│ AppState                     │
├─────────────────────────────┤
│ • roverIP: "192.168.1.100"  │
│ • motorA: 50                 │
│ • motorB: -30                │
│ • controlMode: "gyro"        │
│ • battery: 85                │
│ • isConnected: true          │
│ • latency: 145               │
│ • signal: -52                │
│ • uptime: 3456               │
└─────────────────────────────┘
```

### Auto-Discovery Flow

```
App starts
   ↓
Load lastIP from localStorage
   ↓
Try: http://lastIP:8000/status
   ├─ Success → Use this IP
   │
   └─ Fail → Discovery mode
              ↓
         Try IPs in order:
         1. 192.168.1.100
         2. 192.168.0.100
         3. 192.168.4.1 (AP)
         4. rover.local (mDNS)
              ↓
         Try: GET http://IP:8000/status
              ├─ Success → Use IP
              │           Save to localStorage
              │
              └─ Fail → Next IP
                        ↓
                   [All failed]
                   Show "No rover found"
```

---

## Communication Protocols

### HTTP/REST API

**Protocol:** HTTP/1.1 (simple text)

**Example Request:**
```
POST /motor?a=75&b=-30 HTTP/1.1
Host: 192.168.1.100:8000
Content-Length: 0
Connection: close

```

**Example Response:**
```
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 45
Access-Control-Allow-Origin: *

{"motor_a":75,"motor_b":-30,"status":"ok"}
```

**CORS Headers (all endpoints):**
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

### JSON Telemetry Format

**Standard (full):**
```json
{
  "timestamp": 1693512345,
  "motor_a": 75,
  "motor_b": -30,
  "battery_voltage": 7.8,
  "battery_percent": 85,
  "signal_strength": -45,
  "uptime_ms": 3456789
}
```

**Minimal (optimized):**
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

---

## Data Flow

### Command Flow (Gyro → Motor)

```
User tilts phone
   ↓ (Every 100ms)
[Gyroscope Event]
   orientation.beta (pitch)
   orientation.gamma (roll)
   ↓
gyro.js
   Convert angles to normalized values [-1, 1]
   beta: -90° → 0 (back)
   beta: 0° → 0 (level)
   beta: 90° → 1 (forward)
   ↓
control.js
   Map gyro [-1, 1] → motors [-100, 100]
   
   Forward 50% tilt:
     speedA = 50, speedB = 50
   
   Right 20° roll:
     speedA = 60, speedB = 40 (differential)
   ↓
api.js
   POST http://192.168.1.100:8000/motor?a=50&b=50
   ↓ (WiFi: ~100ms latency)
   ↓
[Pico Rover]
   API handler receives POST
   Parses ?a=50&b=50
   Calls rover.drive(50, 50)
   ↓
motor_control.py
   Motor A: set_speed(50)
     PWM duty = 50% → 32768/65535
     IN1=HIGH, IN2=LOW (forward)
   
   Motor B: set_speed(50)
     PWM duty = 50% → 32768/65535
     IN1=HIGH, IN2=LOW (forward)
   ↓ (~20ms)
[Motors spin]
   Both wheels at ~50% speed
   ↓
Rover moves forward
```

### Telemetry Flow (Rover → UI)

```
Every 1000ms (1 Hz telemetry rate)
   ↓ (Frontend)
ui.js
   GET http://192.168.1.100:8000/status
   ↓ (WiFi: ~100ms latency)
   ↓
[Pico Rover]
   API handler receives GET /status
   
   Reads:
     - motor_a.get_speed() → 50
     - motor_b.get_speed() → 50
     - battery_adc.read() → 7.8V
     - uptime_ticks() → 3456789ms
   
   Builds JSON (minimal format)
   Returns: {...}
   ↓ (~100ms total)
   ↓
[Frontend]
   Receives JSON response
   Parses: a=50, b=50, bv=7.8, bp=85
   ↓
ui.js
   Updates DOM:
     - Battery bar: 85%
     - Speed display: "50 km/h"
     - Signal indicator: -45 dBm
   ↓
User sees live telemetry
```

---

## System Constraints

### Pico W Limitations

| Constraint | Value | Impact |
|-----------|-------|--------|
| RAM | 264 KB | Can't cache large images |
| Flash | 2 MB | ~1000 KB available after MicroPython |
| WiFi | 802.11n 2.4 GHz only | No 5 GHz, <200 Mbps throughput |
| Crypto | Software only | No hardware AES |
| Floating point | Software | Slower than fixed-point |
| GPIO | 30 total | 26 available |
| ADC channels | 5 (GPIO 26-29 + temp) | Limited sensor inputs |

### Network Constraints

| Constraint | Value | Impact |
|-----------|-------|--------|
| LAN latency | 50-200ms | RTT for each API call |
| Bandwidth | ~5-10 Mbps (typical LAN) | Can sustain 10 Hz control |
| Packet loss | <1% | Rare resets/disconnects |
| Jitter | 10-50ms | Smooth motor control still possible |

### Software Constraints

| Constraint | Value | Impact |
|-----------|-------|--------|
| MicroPython version | 1.21+ | Limited stdlib, no asyncio |
| JSON library | ujson (built-in) | Fast, ~10KB code |
| HTTP server | Raw sockets | No fancy routing, but lightweight |
| Control rate | 10 Hz (100ms) | Motor updates every 100ms |

---

## Extensibility Points

### Adding New Sensors

1. Create module: `firmware/sensor_name.py`
2. Add to main.py: `from sensor_name import Sensor`
3. Add API endpoint: `/api/sensor_name`
4. Update frontend: `ui.js` display handler

### Adding New Control Modes

1. Create mode handler: `frontend/js/mode_name.js`
2. Implement: `getMotorSpeeds()` → returns {a, b}
3. Register in app.js: `controlModes['mode_name'] = new ModeController()`
4. Add UI button: `<button id="modeBtn">Mode Name</button>`

### Adding New Behaviors

1. Create: `firmware/behavior_name.py`
2. Instantiate in main.py
3. Call behavior in control loop or API handler
4. Add API endpoints for behavior control

---

## Deployment Architecture

```
Development (Local)
   Pico W on USB (REPL access)
   Frontend: http://localhost:8000
   Editing: Raw files

       ↓ (Deploy)

Staging (Home WiFi)
   Pico W on LAN (192.168.1.x)
   Frontend: http://localhost:8000
   Testing: Full integration

       ↓ (Push)

Production (GitHub)
   Firmware: ZhadowValker/Pico-Rover (private, for you)
   Frontend: GitHub Pages (public)
   URL: https://zhadowvalker.github.io/Pico-Rover/
   
   CI/CD: GitHub Actions
   - Lint firmware (.py)
   - Lint frontend (.js)
   - Validate JSON config
   - Deploy Pages automatically
```

---

## Future Scalability

### Single Rover (Current)
- 1x Pico W + 1x Frontend
- Auto-discovery via IP scan
- Deployment: GitHub Pages

### Multiple Rovers (Phase 5+)
```
Potential architecture:

Central Control Server (Pi 4/PC)
   ├─ Rover Registry
   ├─ Command Queue
   └─ Telemetry Storage
       ↓
   Multiple Pico W (fleet)
       └─ Each reports to server
```

### Cloud Integration (Phase 6+)
```
AWS Lambda (REST API)
   ↓
DynamoDB (Telemetry storage)
   ↓
Web Dashboard
   ├─ Fleet monitoring
   ├─ Remote control
   └─ Analytics
```

---

## References

- [Pico W Datasheet](https://datasheets.raspberrypi.org/rp2040/rp2040-datasheet.pdf)
- [DRV8833 Motor Driver](https://www.ti.com/lit/ds/symlink/drv8833.pdf)
- [MicroPython Documentation](https://docs.micropython.org/)
- [HTTP/1.1 Spec](https://tools.ietf.org/html/rfc7230)
- [802.11 WiFi Standard](https://en.wikipedia.org/wiki/IEEE_802.11)
