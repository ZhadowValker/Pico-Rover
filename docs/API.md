# 🔌 Pico Rover API Documentation

Complete REST API reference for controlling the Pico W rover.

## Base URL

```
http://{rover-ip}:8000
```

Replace `{rover-ip}` with the rover's IP address on your network (e.g., `192.168.1.100`).

---

## Authentication

No authentication required (LAN-only access).

---

## Response Format

All endpoints return JSON with this structure:

```json
{
  "status": "ok|error",
  "message": "Optional error message"
  // ... endpoint-specific data
}
```

---

## Endpoints

### GET /

**Description:** Root status page (HTML)

**Response:** HTML page with API documentation

```bash
curl http://192.168.1.100:8000/
```

---

### GET /status

**Description:** Get rover telemetry data

**Response:**
```json
{
  "status": "ok",
  "connected": true,
  "uptime": 1234,
  "battery": 4.15,
  "motors": {
    "a": 50,
    "b": -30
  },
  "wifi": {
    "connected": true,
    "mode": "AP+STA",
    "ap": {
      "ssid": "RoverSetup",
      "ip": "192.168.4.1",
      "stations": 1
    },
    "sta": {
      "ssid": "MyWiFi",
      "ip": "192.168.1.100",
      "rssi": -42
    }
  }
}
```

**Example:**
```bash
curl http://192.168.1.100:8000/status | jq
```

---

### POST /motor

**Description:** Set motor speeds for rover movement

**Parameters (Query String):**
- `a` (integer, -100 to 100): Left motor speed
  - -100 = full reverse
  - 0 = stop
  - 100 = full forward
- `b` (integer, -100 to 100): Right motor speed

**Response:**
```json
{
  "status": "ok",
  "a": 50,
  "b": -30,
  "speeds": {
    "a": 50,
    "b": -30
  }
}
```

**Examples:**

Forward:
```bash
curl -X POST "http://192.168.1.100:8000/motor?a=75&b=75"
```

Turn left:
```bash
curl -X POST "http://192.168.1.100:8000/motor?a=-50&b=75"
```

Reverse:
```bash
curl -X POST "http://192.168.1.100:8000/motor?a=-100&b=-100"
```

Stop:
```bash
curl -X POST "http://192.168.1.100:8000/motor?a=0&b=0"
```

---

### GET /api/scan

**Description:** Scan available WiFi networks

**Response:**
```json
{
  "status": "ok",
  "networks": [
    {
      "ssid": "MyWiFi",
      "bssid": "aa:bb:cc:dd:ee:ff",
      "channel": 6,
      "rssi": -45,
      "sec": 4,
      "hidden": false
    },
    {
      "ssid": "GuestNetwork",
      "bssid": "11:22:33:44:55:66",
      "channel": 11,
      "rssi": -62,
      "sec": 4,
      "hidden": false
    }
  ]
}
```

**Example:**
```bash
curl http://192.168.1.100:8000/api/scan | jq .networks[].ssid
```

**Security Levels:**
- `0` = Open
- `1` = WEP
- `2` = WPA-Personal
- `3` = WPA2-Personal
- `4` = WPA/WPA2-Personal

---

### POST /api/connect

**Description:** Connect rover to a WiFi network

**Request Body (JSON):**
```json
{
  "ssid": "MyWiFi",
  "password": "secret123"
}
```

**Response:**
```json
{
  "status": "ok",
  "success": true,
  "ssid": "MyWiFi"
}
```

**Example:**
```bash
curl -X POST http://192.168.1.100:8000/api/connect \
  -H "Content-Type: application/json" \
  -d '{"ssid":"MyWiFi","password":"secret123"}'
```

---

## Motor Control Guide

### Differential Steering Formula

```
motorA = forward - turn
motorB = forward + turn

Where:
  forward = desired forward speed (-100 to 100)
  turn = desired turn magnitude (-100 to 100)
```

### Movement Patterns

| Movement | Motor A | Motor B | Effect |
|----------|---------|---------|--------|
| Forward | 100 | 100 | Both motors forward |
| Backward | -100 | -100 | Both motors reverse |
| Turn Left | -50 | 100 | Left slower, right faster |
| Turn Right | 100 | -50 | Right slower, left faster |
| Spin Left | -100 | 100 | Left reverse, right forward |
| Spin Right | 100 | -100 | Right reverse, left forward |
| Stop | 0 | 0 | Both motors stop |

### Speed Ranges

- **0-25%:** Slow, precise movements
- **25-50%:** Moderate speed for learning
- **50-75%:** Standard operation
- **75-100%:** High speed (use with caution)

---

## Error Responses

### 400 Bad Request

Invalid parameters:
```json
{
  "status": "error",
  "error": "Missing SSID"
}
```

### 404 Not Found

Invalid endpoint:
```
HTTP/1.1 404 Not Found
404 Not Found
```

---

## CORS Headers

All responses include CORS headers for browser access:

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

---

## Rate Limiting

No rate limits. However:
- Control loop runs at **10Hz** (100ms updates)
- Telemetry updates at **1Hz** (1000ms intervals)
- Sending commands faster than 10Hz is unnecessary

---

## Battery Monitoring

**Voltage Range:** 3.0V - 4.2V (typical LiPo)

**Percentage Calculation:**
```
percentage = (voltage - 3.0) / (4.2 - 3.0) * 100
```

---

## Telemetry Fields

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `uptime` | integer | 0-∞ | Seconds since boot |
| `battery` | float | 3.0-4.2 | Battery voltage (V) |
| `motors.a` | integer | -100-100 | Left motor speed (%) |
| `motors.b` | integer | -100-100 | Right motor speed (%) |
| `connected` | boolean | true/false | WiFi connection status |
| `rssi` | integer | -120-0 | WiFi signal strength (dBm) |

---

## WebSocket Telemetry (Future)

Planned for Phase 4:

```
ws://rover-ip:8000/telemetry
```

Real-time streaming of sensor data at 10Hz without polling.

---

## Examples

### Python Client
```python
import requests
import json

ROVER_IP = "192.168.1.100"
BASE_URL = f"http://{ROVER_IP}:8000"

# Get status
response = requests.get(f"{BASE_URL}/status")
data = response.json()
print(f"Battery: {data['battery']}V")

# Drive forward
requests.post(f"{BASE_URL}/motor?a=75&b=75")

# Stop
requests.post(f"{BASE_URL}/motor?a=0&b=0")
```

### JavaScript/Browser
```javascript
const ROVER_IP = "192.168.1.100";
const BASE_URL = `http://${ROVER_IP}:8000`;

// Get status
fetch(`${BASE_URL}/status`)
  .then(r => r.json())
  .then(data => console.log(`Battery: ${data.battery}V`));

// Drive rover
fetch(`${BASE_URL}/motor?a=75&b=75`, { method: 'POST' });
```

### cURL Examples

Scan networks:
```bash
curl http://192.168.1.100:8000/api/scan | jq
```

Connect to WiFi:
```bash
curl -X POST http://192.168.1.100:8000/api/connect \
  -H "Content-Type: application/json" \
  -d '{"ssid":"MyNetwork","password":"mypass"}'
```

Drive forward at 80% speed:
```bash
curl -X POST "http://192.168.1.100:8000/motor?a=80&b=80"
```

Get continuous telemetry (bash):
```bash
while true; do
  curl -s http://192.168.1.100:8000/status | jq '.battery'
  sleep 1
done
```

---

## Debugging

Enable debug mode in web UI (**Ctrl+D**) for:
- Verbose API logging
- Motor speed feedback
- Network status updates
- Latency measurements

---

## Limitations & Notes

- **LAN Only:** No cloud relay or remote access
- **No SSL/TLS:** LAN-only, not encrypted
- **Single Connection:** Can handle one control client
- **Stateless:** No session management
- **No Persistence:** Settings reset on reboot (except WiFi config)

---

## Version

**API Version:** 1.0  
**Firmware Version:** See `/status` endpoint  
**Last Updated:** August 2026
