# 🚀 Pico W Rover - Quick Start Guide

## Hardware Setup

### Components
- **MCU:** Raspberry Pi Pico W
- **Motor Driver:** DRV8833 Dual Brushed DC Motor Driver
- **Motors:** 2x 6V DC Motors (with wheels)
- **Battery:** 4x AA Battery Holder (6V) or similar
- **USB Cable:** Micro-USB for programming

### Wiring

#### Motor Connections (DRV8833)
```
Motor A (Left):
- IN1 → GPIO 19
- IN2 → GPIO 18
- PWM → GPIO 14

Motor B (Right):
- IN1 → GPIO 17
- IN2 → GPIO 16
- PWM → GPIO 15

Power:
- GND → Pico GND + Battery GND
- VM → Battery +6V
- GND → Pico GND
```

#### Battery (ADC)
```
- Battery voltage to GPIO 26 (ADC0) via voltage divider
- Optional: voltage divider (e.g., 47k/22k for 6V → 3.3V)
```

## Firmware Installation

### 1. Download MicroPython
Download the latest MicroPython UF2 for Pico W from https://micropython.org/download/rp2-pico-w/

### 2. Flash MicroPython
1. Connect Pico W to computer via USB
2. Hold BOOTSEL button while plugging in USB
3. Drag `uf2` file to `RPI-RP2` drive
4. Pico will reboot with MicroPython installed

### 3. Upload Firmware Files
Use Thonny IDE or `ampy`:

```bash
# Using ampy
ampy --port /dev/ttyACM0 put firmware/config.py
ampy --port /dev/ttyACM0 put firmware/motor_control.py
ampy --port /dev/ttyACM0 put firmware/wifi_manager.py
ampy --port /dev/ttyACM0 put firmware/api_server.py
ampy --port /dev/ttyACM0 put firmware/main.py
```

Or with Thonny:
1. Open all `.py` files
2. Run each from Thonny's file browser
3. Save `main.py` to `/main.py` on Pico

### 4. Boot
Pico will start automatically on power-up.

## WiFi Setup

### First Boot
1. Rover starts WiFi AP "RoverSetup"
2. Connect phone to "RoverSetup" (password: `rover1234`)
3. Open browser → `http://192.168.4.1/setup`
4. Select your home WiFi network
5. Enter password and submit
6. Rover connects to home WiFi

### Auto-Connect
Once configured, rover will:
1. Try to auto-connect to saved WiFi on boot
2. If it fails, fall back to AP mode for manual setup

## Web Remote Control

### Access
1. Once rover is connected to home WiFi
2. Open https://zhadowvalker.github.io/Pico-Rover/
3. Click "📱 Request Permission" (for gyro)
4. Tilt phone to control rover!

### Control Modes
- **📱 Gyroscope:** Tilt phone forward/backward and left/right
- **🕹️ Joystick:** Virtual on-screen joystick
- **⌨️ Keyboard:** Arrow keys or WASD

### Speed Control
Adjust speed slider 10%-100% for safety

## Troubleshooting

### Rover doesn't appear in web app
1. Check rover is connected to WiFi (check router)
2. Verify rover IP in Settings (click ⚙️)
3. Try reconnect button (🔄)
4. Check firewall isn't blocking port 8000

### Motors don't respond
1. Verify DRV8833 is powered (VM pin)
2. Check pin connections match `config.py`
3. Test via API: `GET http://{rover-ip}:8000/motor?a=50&b=50`

### WiFi connection fails
1. Check SSID and password are correct
2. Try 2.4GHz network (Pico W doesn't support 5GHz)
3. Power cycle router and rover

### API Returns 404
1. Verify rover is at correct IP
2. Check port 8000 is accessible
3. Try from another device on same network

## API Endpoints

```
GET  http://rover-ip:8000/              # Status page
GET  http://rover-ip:8000/status        # Get telemetry
POST http://rover-ip:8000/motor?a=50&b=-30  # Set motors
GET  http://rover-ip:8000/api/scan      # Scan WiFi
POST http://rover-ip:8000/api/connect   # Connect WiFi
```

## Battery Information

- **Voltage Range:** 3.0V - 4.2V (LiPo) or equivalent
- **Monitor:** Via ADC on GPIO 26
- **Display:** Battery percentage in web UI

## Debug Mode

Enable debug logging:
1. Open web UI
2. Press Ctrl+D to toggle debug mode
3. Check browser console for logs

## Safety

⚠️ **Emergency Stop:** Large red 🛑 button in web UI
- Immediately stops all motors
- Always accessible

## Next Steps

- Customize motor speed limits in `config.py`
- Modify pin assignments for different layouts
- Add sensors (distance, temperature, etc.)
- Implement autonomous navigation

Enjoy your rover! 🚀
