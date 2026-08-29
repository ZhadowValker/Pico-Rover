# Troubleshooting Guide

## Common Issues

---

## 1. Pico Won't Boot

### Symptoms
- No LED blinks
- No serial output at 115200 baud
- Pico not detected in device manager

### Solutions

**Step 1: Check USB Cable**
- Try a different USB-C cable (data transfer, not charge-only)
- Verify cable is connected to Pico's USB port (not external GPIO USB)

**Step 2: Reset Pico**
```bash
# Hold BOOTSEL while pressing RESET button
# LED should go green (UF2 bootloader mode)
```

**Step 3: Reinstall MicroPython**
1. Download latest MicroPython UF2 for Pico W from [micropython.org](https://micropython.org/download/rp2-pico-w/)
2. Hold BOOTSEL, connect USB
3. Drag `.uf2` file to `/RPI-RP2` drive
4. Pico reboots

**Step 4: Check Serial Connection**
```bash
# Linux/Mac
screen /dev/ttyACM0 115200

# Windows (use PuTTY)
# COM port: COM3 (or your port number)
# Speed: 115200
```

Press CTRL+C to interrupt boot and get to REPL prompt.

---

## 2. WiFi Won't Connect

### Symptoms
- Pico starts AP but can't connect to home WiFi
- "Connection failed" error in startup logs

### Solutions

**Step 1: Verify Credentials**
- Check SSID spelling (case-sensitive)
- Ensure password is correct
- Test with phone first to confirm network works

**Step 2: Check Signal Strength**
```python
# From REPL
import network
wlan = network.WLAN(network.STA_IF)
networks = wlan.scan()
for net in networks:
    print(f"{net[0].decode()}: {net[3]} dBm")
```

If signal < -80 dBm, move Pico closer to router.

**Step 3: Try 2.4 GHz Only**
- Pico W only supports 2.4 GHz WiFi
- If your router broadcasts 5 GHz, create a separate 2.4 GHz network
- Some routers have "802.11 b/g/n only" setting

**Step 4: Clear Saved Credentials**
```python
# From REPL
import os
os.remove('wifi_config.json')  # Deletes saved credentials
# Press CTRL+D to reboot - will start AP again
```

**Step 5: Check WiFi Manager Logs**
```python
# Add debug prints to firmware/wifi_manager.py
print(f"[WiFi] Scanning networks...")
print(f"[WiFi] Connecting to: {ssid}")
print(f"[WiFi] Status: {wlan.status()}")  # 0=idle, 1=connecting, 2=wrong pass, 3=no ap, 4=connected
```

---

## 3. Cannot Reach API

### Symptoms
- Web frontend shows "Connection failed"
- Timeout when calling `http://192.168.1.100:8000/status`

### Solutions

**Step 1: Verify IP Address**
```python
# From REPL
import network
wlan = network.WLAN(network.STA_IF)
print(wlan.ifconfig())  # Shows (IP, subnet, gateway, DNS)
```

If IP starts with `192.168.4.x`, Pico is still in AP mode.

**Step 2: Test Local Connectivity**
```bash
# From computer on same WiFi
ping 192.168.1.100

# If ping works but HTTP times out, API server may not have started
# Check Pico REPL for startup errors
```

**Step 3: Check Firewall**
- Disable firewall temporarily to test
- If it works, add exception for port 8000:
  - **Windows:** Windows Defender → Firewall → Allow app through firewall
  - **Mac:** System Preferences → Security → Firewall Options
  - **Linux:** `sudo ufw allow 8000`

**Step 4: Verify API Server Started**
```python
# From REPL, manually start API server
from api_server import start_server
start_server()  # Should print "Server listening on 0.0.0.0:8000"
```

If error occurs, check for syntax errors in `firmware/api_server.py`.

**Step 5: Check Port 8000 Availability**
```python
# From REPL
import socket
s = socket.socket()
try:
    s.bind(('0.0.0.0', 8000))
    print("Port 8000 is free")
except OSError as e:
    print(f"Port 8000 in use: {e}")
```

---

## 4. Motors Don't Move

### Symptoms
- API responds correctly
- Motor speeds change in `/status`
- But wheels don't spin

### Solutions

**Step 1: Check Wiring**
- Verify DRV8833 pins match `config.py`:
  - IN1/IN2/IN3/IN4 → GPIO 19, 18, 17, 16
  - AO1/AO2 → Motor A | BO1/BO2 → Motor B
- Ensure PWM pins are correct (GPIO 14, 15)

**Step 2: Test Motor Directly**
```python
# From REPL - manually control Motor A
from motor_control import Motor
from machine import Pin, PWM

motor_a = Motor(
    Pin(19), Pin(18),  # IN1, IN2
    PWM(Pin(14), freq=5000)  # PWM
)

motor_a.set_speed(100)  # Should spin motor
print(motor_a.get_speed())  # Should print 100
```

**Step 3: Check Power Supply**
- Measure battery/PSU voltage with multimeter
- Should be > 6V (ideally 7.2-8.4V for 2S LiPo)
- Check voltage at DRV8833 VCC pin
- If voltage drops during motor spin, supply is underpowered

**Step 4: Test PWM Signal**
```python
# From REPL - generate 50% PWM on GPIO 14
from machine import Pin, PWM
pwm = PWM(Pin(14), freq=5000)
pwm.duty_u16(32768)  # 50% duty
# Connect oscilloscope to GPIO 14 - should see ~2.5V square wave
```

**Step 5: Check Motor Connections**
- Swap motor wires (A/B reversed)
- If motor spins in opposite direction, polarity was flipped
- Correct connections:
  - IN1 high, IN2 low → Forward
  - IN1 low, IN2 high → Reverse
  - Both high or both low → Stop (coasting)

---

## 5. High Latency / Lag

### Symptoms
- Command takes >500ms to execute
- Rover jerks/stutters
- Telemetry updates slowly

### Solutions

**Step 1: Check WiFi Signal**
```python
# From REPL
import network
wlan = network.WLAN(network.STA_IF)
print(f"Signal: {wlan.status()}")  # -50 to -80 is good, < -80 is poor
```

**Step 2: Reduce Control Rate**
- Frontend sends commands at 10 Hz by default
- If WiFi is congested, increase interval to 100ms → 50ms (20 Hz max)
- Edit `frontend/js/app.js`, line: `setInterval(controlLoop, 100);`

**Step 3: Check Network Congestion**
```bash
# From computer on same WiFi
# Run network speed test (ookla.com or fast.com)
# Pico bandwidth is ~5-10 Mbps
# If home network > 50 Mbps in use, move to 5 GHz devices
```

**Step 4: Optimize API Response**
```python
# firmware/api_server.py - ensure response is minimal
# Remove unnecessary JSON fields from /status
```

**Step 5: Use Local mDNS (if available)**
```bash
# Edit frontend/js/api.js discovery:
# Instead of IP scanning, try:
curl http://pico-rover.local:8000/status
```

---

## 6. Battery Voltage Always Shows 0%

### Symptoms
- Battery field in `/status` always 0V or 0%
- `voltage_raw` is 0

### Solutions

**Step 1: Check ADC Wiring**
- Battery ADC should be on GPIO 26
- Verify voltage divider is connected:
  - Battery+ → 10kΩ resistor → GPIO 26 → GND
  - Also connect Battery+ → GND (capacitor 100µF for noise filtering)

**Step 2: Test ADC Directly**
```python
# From REPL
from machine import ADC
adc = ADC(26)
for i in range(10):
    reading = adc.read_u16()
    voltage = (reading / 65535) * 3.3
    print(f"Raw: {reading}, Voltage (at GPIO): {voltage:.2f}V")
    
# With voltage divider (10k+10k):
# Actual battery voltage = voltage_at_gpio * 2
```

**Step 3: Calibrate Voltage Divider**
```python
# If using different resistors, update firmware:
# firmware/motor_control.py, Rover class:
VOLTAGE_SCALE = 2.0  # Change based on your resistor ratio
```

**Step 4: Add Low-Pass Filter**
```python
# In firmware/motor_control.py, get_battery_voltage():
# Take average of 5 readings to reduce noise
readings = [adc.read_u16() for _ in range(5)]
avg = sum(readings) / len(readings)
voltage = (avg / 65535) * 3.3 * VOLTAGE_SCALE
```

---

## 7. Frontend Page Blank or Won't Load

### Symptoms
- GitHub Pages shows blank page
- Browser console errors
- JS files not loading

### Solutions

**Step 1: Verify GitHub Pages is Enabled**
1. Go to https://github.com/ZhadowValker/Pico-Rover/settings/pages
2. Check:
   - Source: "Deploy from a branch"
   - Branch: "main"
   - Folder: "/frontend"
   - Click "Save" if changed

**Step 2: Check Build Status**
- Go to Actions tab
- Verify latest commit has green checkmark
- If red, click job to see error logs

**Step 3: Test Frontend Locally**
```bash
cd frontend
python -m http.server 8000
# Open http://localhost:8000
```

**Step 4: Check Console Errors**
```javascript
// Browser DevTools (F12) → Console tab
// Look for 404 errors on JS/CSS files
// Example: "Failed to load resource: 404 /frontend/js/app.js"
```

**Step 5: Verify File Structure**
```bash
cd /home/claude/Pico-Rover
tree -L 3 frontend/
```

Expected output:
```
frontend/
├── index.html
├── css/
│   └── style.css
├── js/
│   ├── app.js
│   ├── api.js
│   ├── control.js
│   ├── gyro.js
│   ├── joystick.js
│   └── ui.js
└── libs/
    └── nipple.js
```

---

## 8. Gyroscope Permission Not Requested (iOS)

### Symptoms
- "📍 Request Permission" button does nothing on iPhone
- Safari console: "DeviceOrientationEvent.requestPermission is not a function"

### Solutions

**Step 1: Use HTTPS**
- GitHub Pages is always HTTPS ✓
- Safari requires HTTPS for gyro access

**Step 2: Check Safari Settings**
- Settings → Safari → Motion & Orientation Access
- Ensure enabled for your site

**Step 3: Test in Safari**
- Not supported in Chrome/Firefox on iOS
- Must use Safari

**Step 4: Debug Permission Request**
```javascript
// frontend/js/gyro.js
DeviceOrientationEvent.requestPermission()
  .then(state => {
    console.log('Permission:', state);  // should be 'granted'
  })
  .catch(e => console.error('Error:', e));
```

---

## 9. GitHub Push Fails with PAT

### Symptoms
- `git push` says "fatal: Authentication failed"
- Or "Repository not found"

### Solutions

**Step 1: Regenerate PAT**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it `repo` scope (read + write)
4. Copy token (won't show again)

**Step 2: Update Remote URL**
```bash
cd /home/claude/Pico-Rover
git remote set-url origin "https://ZhadowValker:{NEW_PAT}@github.com/ZhadowValker/Pico-Rover.git"
git push -u origin main
```

**Step 3: Verify Remote**
```bash
git remote -v
# Should show new URL with PAT
```

**⚠️ Security Warning:**
- Never commit PAT to repository
- Never share PAT in chat/logs
- Treat like a password
- Regenerate if exposed

---

## 10. Serial/REPL Won't Connect

### Symptoms
- `screen` or `miniterm.py` hangs
- No prompt appears

### Solutions

**Step 1: List Serial Ports**
```bash
# Linux/Mac
ls /dev/tty.* /dev/cu.*

# Windows
# Device Manager → COM Ports

# Check python
python -m serial.tools.list_ports
```

**Step 2: Identify Pico Port**
```bash
# Linux - unplug Pico, run:
ls /dev/ttyACM*
# (note current list)

# Plug Pico in, run:
ls /dev/ttyACM*
# New entry is Pico
```

**Step 3: Connect with Correct Settings**
```bash
# Baud rate MUST be 115200
screen /dev/ttyACM0 115200

# Or use miniterm.py (recommended)
python -m serial.tools.miniterm /dev/ttyACM0 115200
```

**Step 4: Interrupt Boot and Get Prompt**
```
(wait for boot messages)
Press CTRL+C rapidly
>>>
```

If you see `>>>`, REPL is active.

---

## Getting Help

If issues persist:

1. **Check logs:** `screen /dev/ttyACM0 115200` and observe startup
2. **Inspect code:** Review error traceback in REPL
3. **Test in isolation:** Run individual components (Motor, WiFi, API)
4. **Check hardware:** Verify all connections with multimeter
5. **Review documentation:** Refer to README.md, SETUP.md, API.md

### Common Error Codes

| Error | Meaning | Solution |
|-------|---------|----------|
| `E_NOENT` | File not found | Ensure firmware files uploaded |
| `WantReadError` | WiFi SSL handshake failed | Check WiFi certificate |
| `EADDRINUSE` | Port already in use | Kill previous process on port 8000 |
| `ENOTCONN` | Not connected | Verify WiFi connection first |
