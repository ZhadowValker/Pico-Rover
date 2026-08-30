# Pico Rover API Testing Guide

## Overview

This guide covers all methods to test the Pico W REST API without the rover hardware connected.

---

## 🧪 Test Environment Setup

### Prerequisites

```bash
# Python 3.8+
python --version

# Install required tools
pip install requests  # For Python HTTP client
pip install httpx     # Alternative HTTP client

# Optional: Install Postman for GUI testing
# Download from: https://www.postman.com/downloads/
```

---

## 📍 API Endpoints Quick Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Server status |
| GET | `/status` | Rover telemetry |
| POST | `/motor` | Control motors |
| POST | `/motor/stop` | Emergency stop |
| GET | `/api/scan` | Scan WiFi networks |
| POST | `/api/connect` | Connect to WiFi |

---

## 🔬 Method 1: Test with REPL (Simplest)

### Step 1: Set up Pico W

```bash
# Flash MicroPython to Pico W (see SETUP.md)
# Connect via USB
# Open REPL (Thonny, ampy, or minicom)
```

### Step 2: Test Motors Manually

```python
# In REPL
from firmware.motor_control import Motor, Rover
from machine import Pin, PWM

# Initialize motors
motor_a = Motor(in1_pin=19, in2_pin=18, pwm_pin=14)
motor_b = Motor(in1_pin=17, in2_pin=16, pwm_pin=15)
rover = Rover(motor_a, motor_b)

# Test forward
rover.drive(100, 100)  # Full speed forward
import time
time.sleep(1)

# Test backward
rover.drive(-100, -100)  # Full speed backward
time.sleep(1)

# Test turn left
rover.drive(50, -50)  # Left motor forward, right motor backward
time.sleep(1)

# Stop
rover.stop()
print("✓ Motor control works!")
```

### Step 3: Test WiFi Manager

```python
from firmware.wifi_manager import WiFiManager

wifi = WiFiManager()

# Scan networks
networks = wifi.scan_networks()
print("Available networks:")
for net in networks:
    print(f"  {net['ssid']} ({net['rssi']} dBm)")

# Start AP mode
wifi.start_ap("RoverSetup", "rover1234")
print("✓ AP mode started on 192.168.4.1")
```

### Step 4: Test API Server

```python
from firmware.api_server import APIServer
from firmware.motor_control import Motor, Rover

# Create rover instance
motor_a = Motor(19, 18, 14)
motor_b = Motor(17, 16, 15)
rover = Rover(motor_a, motor_b)

# Start API server
server = APIServer(rover, port=8000)
print("✓ API server running on 192.168.4.1:8000")

# In another terminal/device, test endpoints
```

---

## 🧪 Method 2: cURL Testing (Command Line)

### Prerequisites

```bash
# macOS
brew install curl

# Linux (already included)
curl --version

# Windows (already included in PowerShell)
```

### Test Endpoints

**Assuming Pico is at `192.168.4.1:8000` (AP mode)**

#### 1. **Test Server Status**

```bash
curl -X GET http://192.168.4.1:8000/
```

Expected response:
```json
{"status": "online", "uptime": 12345}
```

#### 2. **Get Rover Telemetry**

```bash
curl -X GET http://192.168.4.1:8000/status
```

Expected response:
```json
{
  "battery_voltage": 7.2,
  "uptime_ms": 5432,
  "motor_a_speed": 0,
  "motor_b_speed": 0,
  "latency_ms": 15
}
```

#### 3. **Control Motors (Move Forward)**

```bash
curl -X POST http://192.168.4.1:8000/motor \
  -H "Content-Type: application/json" \
  -d '{"a": 100, "b": 100}'
```

**Parameters:**
- `a`: Motor A speed (-100 to 100)
- `b`: Motor B speed (-100 to 100)

**Examples:**

```bash
# Forward
curl -X POST http://192.168.4.1:8000/motor \
  -d '{"a": 100, "b": 100}'

# Backward
curl -X POST http://192.168.4.1:8000/motor \
  -d '{"a": -100, "b": -100}'

# Turn left
curl -X POST http://192.168.4.1:8000/motor \
  -d '{"a": 100, "b": -100}'

# Turn right
curl -X POST http://192.168.4.1:8000/motor \
  -d '{"a": -100, "b": 100}'

# Half speed
curl -X POST http://192.168.4.1:8000/motor \
  -d '{"a": 50, "b": 50}'
```

#### 4. **Emergency Stop**

```bash
curl -X POST http://192.168.4.1:8000/motor/stop
```

#### 5. **Scan WiFi Networks**

```bash
curl -X GET http://192.168.4.1:8000/api/scan
```

Expected response:
```json
{
  "networks": [
    {"ssid": "MyHome", "rssi": -45, "channel": 6, "security": 3},
    {"ssid": "Guest", "rssi": -62, "channel": 11, "security": 3}
  ]
}
```

#### 6. **Connect to WiFi**

```bash
curl -X POST http://192.168.4.1:8000/api/connect \
  -H "Content-Type: application/json" \
  -d '{"ssid": "MyHome", "password": "mypassword"}'
```

---

## 🧪 Method 3: Python Testing Script

### Create Test Script

**File:** `test_api.py`

```python
#!/usr/bin/env python3
"""
Pico Rover API Testing Script
Tests all endpoints with detailed output
"""

import requests
import json
import time
from typing import Dict, Any

class RoverAPITester:
    def __init__(self, base_url: str = "http://192.168.4.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_connection(self) -> bool:
        """Test if rover is reachable"""
        try:
            response = self.session.get(f"{self.base_url}/", timeout=2)
            print("✓ Rover is reachable")
            return True
        except requests.exceptions.ConnectionError:
            print("✗ Cannot connect to rover")
            return False
    
    def test_status(self) -> Dict[str, Any]:
        """Get rover status"""
        try:
            response = self.session.get(f"{self.base_url}/status")
            data = response.json()
            print("✓ Status endpoint works")
            print(f"  Battery: {data.get('battery_voltage', 'N/A')}V")
            print(f"  Uptime: {data.get('uptime_ms', 'N/A')}ms")
            print(f"  Motor A: {data.get('motor_a_speed', 'N/A')}")
            print(f"  Motor B: {data.get('motor_b_speed', 'N/A')}")
            return data
        except Exception as e:
            print(f"✗ Status failed: {e}")
            return {}
    
    def test_motor_control(self) -> bool:
        """Test motor control"""
        try:
            print("Testing motor control...")
            
            # Forward
            print("  → Moving forward (2s)")
            self.session.post(f"{self.base_url}/motor", 
                            json={"a": 100, "b": 100})
            time.sleep(2)
            
            # Turn left
            print("  → Turning left (2s)")
            self.session.post(f"{self.base_url}/motor", 
                            json={"a": 100, "b": -100})
            time.sleep(2)
            
            # Stop
            print("  → Stopping")
            self.session.post(f"{self.base_url}/motor/stop")
            
            print("✓ Motor control works")
            return True
        except Exception as e:
            print(f"✗ Motor control failed: {e}")
            return False
    
    def test_wifi_scan(self) -> Dict[str, Any]:
        """Scan WiFi networks"""
        try:
            response = self.session.get(f"{self.base_url}/api/scan")
            data = response.json()
            print("✓ WiFi scan works")
            networks = data.get('networks', [])
            print(f"  Found {len(networks)} networks:")
            for net in networks[:5]:  # Show first 5
                print(f"    - {net['ssid']} ({net['rssi']} dBm)")
            return data
        except Exception as e:
            print(f"✗ WiFi scan failed: {e}")
            return {}
    
    def test_wifi_connect(self, ssid: str, password: str) -> bool:
        """Connect to WiFi"""
        try:
            print(f"Connecting to {ssid}...")
            response = self.session.post(f"{self.base_url}/api/connect",
                                       json={"ssid": ssid, "password": password})
            data = response.json()
            
            if data.get('success'):
                print(f"✓ Connected to {ssid}")
                print(f"  IP: {data.get('ip', 'N/A')}")
                return True
            else:
                print(f"✗ Failed to connect: {data.get('error', 'Unknown')}")
                return False
        except Exception as e:
            print(f"✗ WiFi connect failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 60)
        print("Pico Rover API Test Suite")
        print("=" * 60)
        print(f"Target: {self.base_url}\n")
        
        # Test 1: Connection
        if not self.test_connection():
            print("\n✗ Cannot proceed - rover unreachable")
            return
        print()
        
        # Test 2: Status
        self.test_status()
        print()
        
        # Test 3: Motor control
        self.test_motor_control()
        print()
        
        # Test 4: WiFi scan
        self.test_wifi_scan()
        print()
        
        print("=" * 60)
        print("Test suite completed!")
        print("=" * 60)


if __name__ == "__main__":
    import sys
    
    # Optional: specify custom IP
    ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.4.1"
    
    tester = RoverAPITester(f"http://{ip}:8000")
    tester.run_all_tests()
```

### Run Test Script

```bash
# Test default IP (192.168.4.1)
python test_api.py

# Test custom IP
python test_api.py 192.168.1.100

# Run with verbose output
python test_api.py 192.168.1.100 -v
```

---

## 🧪 Method 4: Postman GUI Testing

### Step 1: Import API Collection

**File:** `postman_collection.json`

```json
{
  "info": {
    "name": "Pico Rover API",
    "version": "1.0.0"
  },
  "item": [
    {
      "name": "Server Status",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/"
      }
    },
    {
      "name": "Get Status",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/status"
      }
    },
    {
      "name": "Move Forward",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/motor",
        "body": {
          "mode": "raw",
          "raw": "{\"a\": 100, \"b\": 100}"
        }
      }
    },
    {
      "name": "Move Backward",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/motor",
        "body": {
          "mode": "raw",
          "raw": "{\"a\": -100, \"b\": -100}"
        }
      }
    },
    {
      "name": "Turn Left",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/motor",
        "body": {
          "mode": "raw",
          "raw": "{\"a\": 100, \"b\": -100}"
        }
      }
    },
    {
      "name": "Stop",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/motor/stop"
      }
    },
    {
      "name": "Scan WiFi",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/api/scan"
      }
    },
    {
      "name": "Connect WiFi",
      "request": {
        "method": "POST",
        "url": "{{base_url}}/api/connect",
        "body": {
          "mode": "raw",
          "raw": "{\"ssid\": \"MyNetwork\", \"password\": \"password123\"}"
        }
      }
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://192.168.4.1:8000"
    }
  ]
}
```

### Step 2: Import in Postman

1. Open Postman
2. Click "Import" (top left)
3. Paste the JSON above
4. Click "Import"

### Step 3: Set Environment Variable

1. Click "Environments" (left sidebar)
2. Create new environment "Pico Rover"
3. Add variable:
   - Key: `base_url`
   - Value: `http://192.168.4.1:8000`
4. Select this environment from dropdown

### Step 4: Run Requests

Click any request → Click "Send" → See response

---

## 🧪 Method 5: Browser Console Testing

Open DevTools in your browser and test from JavaScript:

```javascript
// Test server status
fetch('http://192.168.4.1:8000/')
  .then(r => r.json())
  .then(data => console.log('Status:', data))
  .catch(e => console.error('Error:', e));

// Move forward
fetch('http://192.168.4.1:8000/motor', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({a: 100, b: 100})
})
.then(r => r.json())
.then(data => console.log('Response:', data));

// Stop
fetch('http://192.168.4.1:8000/motor/stop', {
  method: 'POST'
})
.then(r => r.json())
.then(data => console.log('Stopped:', data));
```

---

## 📊 Test Checklist

### Phase 1: REPL Tests (No API Server)

- [ ] Motor A moves forward
- [ ] Motor A moves backward
- [ ] Motor B moves forward
- [ ] Motor B moves backward
- [ ] Rover drives forward (both motors)
- [ ] Rover drives backward
- [ ] Rover turns left
- [ ] Rover turns right
- [ ] Rover stops cleanly

### Phase 2: API Server Tests

- [ ] `GET /` returns status
- [ ] `GET /status` returns telemetry
- [ ] `POST /motor` with `a=100, b=100` works
- [ ] `POST /motor` with `a=-100, b=-100` works
- [ ] `POST /motor` with `a=100, b=-100` works
- [ ] `POST /motor/stop` stops rover
- [ ] `GET /api/scan` returns networks
- [ ] `POST /api/connect` connects to WiFi
- [ ] Response times < 200ms

### Phase 3: Integration Tests

- [ ] Frontend discovers Pico on LAN
- [ ] Frontend sends motor commands
- [ ] Gyro tilt controls rover
- [ ] Joystick fallback works
- [ ] Emergency stop responsive
- [ ] Telemetry updates at 1Hz

---

## 🚨 Common Issues & Solutions

### Issue: "Connection refused"

```
Error: Cannot connect to 192.168.4.1:8000
```

**Solution:**
- Verify Pico is powered on
- Check Pico's AP is broadcasting ("RoverSetup")
- Connect your computer to the AP
- Verify firewall isn't blocking

### Issue: "Motor not moving"

**Solution:**
- Check firmware flashed correctly
- Verify motor wiring (GPIO pins match config.py)
- Test motor directly in REPL
- Check DRV8833 connections

### Issue: "API returns 500 error"

**Solution:**
- Check firmware logs (REPL or serial)
- Verify JSON payload format
- Check memory (print free memory)
- Restart Pico

### Issue: "Timeout on requests"

**Solution:**
- Check network latency: `ping 192.168.4.1`
- Reduce API payload size
- Check Pico isn't overloaded
- Try requests from device on same network

---

## 📝 Test Results Template

```
Date: YYYY-MM-DD
Tester: [Name]
Pico IP: [IP Address]
Firmware Version: [Version]

REPL Tests:
  Motor Forward: [ ] Pass [ ] Fail
  Motor Backward: [ ] Pass [ ] Fail
  WiFi Scan: [ ] Pass [ ] Fail
  
API Tests:
  GET /: [ ] Pass [ ] Fail
  GET /status: [ ] Pass [ ] Fail
  POST /motor: [ ] Pass [ ] Fail
  POST /motor/stop: [ ] Pass [ ] Fail
  GET /api/scan: [ ] Pass [ ] Fail
  POST /api/connect: [ ] Pass [ ] Fail

Frontend Integration:
  Discovery: [ ] Pass [ ] Fail
  Motor Control: [ ] Pass [ ] Fail
  Telemetry: [ ] Pass [ ] Fail

Notes:
[Any issues found]
```

---

## 🎯 Next Steps

1. **Flash firmware** to Pico W (see SETUP.md)
2. **Connect via USB** and open REPL
3. **Run Phase 1 tests** (motor control)
4. **Start API server** in firmware
5. **Run Phase 2 tests** (API endpoints)
6. **Test frontend** with Pico on LAN
7. **Troubleshoot** as needed

---

## 📚 Related Documentation

- [SETUP.md](./SETUP.md) - Hardware setup & firmware flashing
- [API.md](./API.md) - Complete API reference
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues

---

**Ready to test? Start with Method 1 (REPL)!** 🧪
