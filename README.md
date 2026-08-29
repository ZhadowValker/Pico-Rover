# 🤖 Pico W Rover - Remote Control

A WiFi-controlled two-wheeled rover using Raspberry Pi Pico W and DRV8833 motor driver. Control with gyroscope, joystick, or keyboard via GitHub Pages web app.

## Features

✨ **Control Methods**
- 📱 Device gyroscope tilt control (primary)
- 🕹️ Virtual joystick (fallback)
- ⌨️ Keyboard / D-pad buttons
- 📊 Real-time telemetry display

🔌 **Hardware**
- Raspberry Pi Pico W (WiFi-enabled)
- DRV8833 dual DC motor driver
- Differential steering (independent motor control)
- Battery voltage monitoring
- PWM speed control (0-100%)

📡 **Connectivity**
- WiFi AP mode for initial setup (SSID: `RoverSetup`)
- Auto-connect to saved home WiFi
- LAN-only control (<200ms latency)
- REST API over HTTP + optional WebSocket telemetry

🌐 **Web Remote**
- Single-page app (runs offline after first load)
- GitHub Pages hosted (https://zhadowvalker.github.io/Pico-Rover/)
- Mobile-optimized dark theme
- Auto-discovery of rover IP
- Settings/configuration panel

## Quick Start

### 1. Hardware Assembly
See [SETUP.md](SETUP.md) for detailed wiring and component list.

### 2. Firmware Installation
```bash
# Flash MicroPython to Pico W, then upload:
# - config.py
# - motor_control.py
# - wifi_manager.py
# - api_server.py
# - main.py
```

### 3. WiFi Setup
1. Connect to `RoverSetup` AP (password: `rover1234`)
2. Open `http://192.168.4.1/setup`
3. Select home WiFi and enter password

### 4. Launch Remote
Open https://zhadowvalker.github.io/Pico-Rover/ on your phone

## Project Structure

```
Pico-Rover/
├── firmware/
│   ├── main.py              # Boot sequence
│   ├── config.py            # Pin configuration
│   ├── motor_control.py     # DRV8833 PWM control
│   ├── wifi_manager.py      # AP + station WiFi
│   └── api_server.py        # REST API server
│
├── frontend/
│   ├── index.html           # Main control UI
│   ├── setup.html           # WiFi setup wizard
│   ├── css/style.css        # Mobile-first styling
│   ├── js/
│   │   ├── app.js           # Main orchestration
│   │   ├── api.js           # HTTP client
│   │   ├── gyro.js          # DeviceOrientation API
│   │   ├── joystick.js      # Virtual joystick
│   │   ├── control.js       # Motor mapping
│   │   └── ui.js            # DOM helpers
│   └── libs/nipple.js       # Joystick library
│
└── docs/
    ├── API.md               # REST endpoints
    ├── PINOUT.md            # Hardware pinout
    └── TROUBLESHOOTING.md   # Common issues
```

## Architecture

### Motor Control
- **Dual motors** with differential steering
- **PWM-based speed** (0-65535 u16 values)
- **Direction control** via GPIO pins
- **Speed range** -100% (reverse) to +100% (forward)

### Connectivity Flow
1. **Pico boots** → checks for saved WiFi config
2. **If no config** → starts AP "RoverSetup" (192.168.4.1)
3. **Setup page** → scan networks, save credentials, reboot
4. **Auto-connect** → connects to home WiFi
5. **Web app** → discovers Pico IP, starts control loop

### Control Loop (10Hz)
```
Read sensor (gyro/joystick/keyboard)
  ↓
Map to motor speeds (-100 to +100)
  ↓
POST /motor?a=50&b=-30
  ↓
Update display with actual speeds
```

### Telemetry Loop (1Hz)
```
GET /status
  ↓
Parse: battery, uptime, motor speeds
  ↓
Update UI gauges and indicators
```

## API Endpoints

### GET /status
Returns rover telemetry:
```json
{
  "status": "ok",
  "connected": true,
  "uptime": 1234,
  "battery": 4.15,
  "motors": {"a": 50, "b": 50},
  "wifi": { "connected": true, ... }
}
```

### POST /motor
Set motor speeds:
```
POST /motor?a=50&b=-30
Response: { "status": "ok", "a": 50, "b": -30, ... }
```

### GET /api/scan
Scan available WiFi networks:
```json
{
  "status": "ok",
  "networks": [
    {
      "ssid": "MyWiFi",
      "channel": 6,
      "rssi": -45,
      "sec": 4
    }
  ]
}
```

### POST /api/connect
Connect to WiFi:
```json
{
  "ssid": "MyWiFi",
  "password": "secret123"
}
```

## Control Mapping

### Gyroscope
- **Pitch (X):** Forward/backward
- **Roll (Y):** Left/right differential steering
- **Mapping:** -90° to +90° → -100% to +100% speed

### Joystick
- **Angle:** Direction of movement
- **Distance:** Speed magnitude (0-1.0)
- **Differential steering** applied for turning

### Keyboard
```
↑ / W     → Forward
↓ / S     → Backward
← / A     → Turn left
→ / D     → Turn right
Space     → Stop
```

## Safety Features

🛑 **Emergency Stop**
- Red button in UI stops all motors immediately
- Send zero speed command to Pico

⚡ **Speed Limiter**
- Max speed adjustable 10%-100%
- Prevent overspeed accidents

🔄 **Auto-Reconnect**
- Periodic connection checks
- Fallback to discovery on disconnect

## Specifications

| Parameter | Value |
|-----------|-------|
| **Latency** | <200ms (LAN only) |
| **Control Rate** | 10 Hz |
| **Telemetry Rate** | 1 Hz |
| **Battery Range** | 3.0-4.2V |
| **Max Motor Speed** | 100 PWM (full speed) |
| **WiFi Standards** | 802.11 b/g/n (2.4GHz only) |

## Troubleshooting

See [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for common issues and solutions.

## Performance Notes

- **Latency:** ~50-150ms typical (WiFi dependent)
- **Battery Life:** ~2-4 hours (depending on motor usage)
- **WiFi Range:** 30-50m typical (line of sight)

## Future Enhancements

- [ ] WebSocket telemetry (lower latency)
- [ ] Autonomous obstacle avoidance
- [ ] Multiple sensor fusion
- [ ] Recording and replay mode
- [ ] Multi-rover swarm control
- [ ] Custom mission scripting

## License

MIT License - See LICENSE file

## Author

**SoundMind** - Embedded Systems & Full-Stack Developer  
GitHub: [@ZhadowValker](https://github.com/ZhadowValker)

---

**Repository:** https://github.com/ZhadowValker/Pico-Rover  
**Web Remote:** https://zhadowvalker.github.io/Pico-Rover/

Enjoy! 🚀
