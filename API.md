# Pico Rover API Reference

## Base URL
```
http://{rover_ip}:8000
```

### Auto-Discovery
The web frontend tries these endpoints in order:
1. `http://192.168.1.100:8000` (most common home WiFi)
2. `http://192.168.0.100:8000` (alternative home WiFi)
3. `http://192.168.4.1:8000` (AP setup mode)
4. `http://rover.local:8000` (mDNS, if enabled)

---

## REST Endpoints

### `GET /`
Returns landing page (JSON info).

**Response:**
```json
{
  "name": "Pico Rover",
  "version": "1.0.0",
  "status": "ready"
}
```

**Status:** 200 OK

---

### `GET /status`
Real-time rover telemetry.

**Response:**
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

**Status:** 200 OK

---

### `POST /motor`
Set motor speeds.

**Query Parameters:**
- `a` (int): Motor A speed, -100 to 100
- `b` (int): Motor B speed, -100 to 100

**Example:**
```
POST http://192.168.1.100:8000/motor?a=50&b=-30
```

**Response:**
```json
{
  "motor_a": 50,
  "motor_b": -30,
  "status": "ok"
}
```

**Status:** 200 OK

**Error Response:**
```json
{
  "error": "Invalid speed value",
  "status": "error"
}
```

**Status:** 400 Bad Request

---

### `POST /motor/stop`
Emergency stop (immediately cuts all motor power).

**Example:**
```
POST http://192.168.1.100:8000/motor/stop
```

**Response:**
```json
{
  "motor_a": 0,
  "motor_b": 0,
  "status": "stopped"
}
```

**Status:** 200 OK

---

### `GET /api/scan`
Scan available WiFi networks (AP mode only).

**Response:**
```json
{
  "networks": [
    {
      "ssid": "MyNetwork",
      "channel": 6,
      "signal_strength": -45,
      "security": "WPA2"
    },
    {
      "ssid": "GuestNetwork",
      "channel": 11,
      "signal_strength": -72,
      "security": "WPA2"
    }
  ],
  "status": "ok"
}
```

**Status:** 200 OK

---

### `POST /api/connect`
Connect to a WiFi network (AP mode only).

**Request Body (JSON):**
```json
{
  "ssid": "MyNetwork",
  "password": "mypassword"
}
```

**Response:**
```json
{
  "status": "connecting",
  "message": "Connecting to MyNetwork. Rover will reboot."
}
```

**Status:** 200 OK

**Note:** Pico will reboot and attempt connection. If successful, it will not broadcast AP anymore.

---

### `GET /api/config`
Get current configuration (if supported).

**Response:**
```json
{
  "ap_ssid": "RoverSetup",
  "ap_password": "rover1234",
  "api_port": 8000,
  "pwm_frequency": 5000,
  "motor_pins": {
    "motor_a": {
      "in1": 19,
      "in2": 18,
      "pwm": 14
    },
    "motor_b": {
      "in1": 17,
      "in2": 16,
      "pwm": 15
    }
  }
}
```

**Status:** 200 OK

---

## Control Modes

### Speed Range
All motor commands use a normalized speed range:
- **-100:** Full reverse
- **0:** Stop
- **100:** Full forward

### Differential Steering
To turn the rover:
- **Left turn:** `a=50, b=75` (right motor faster)
- **Right turn:** `a=75, b=50` (left motor faster)
- **Spin left:** `a=50, b=-50` (opposite directions)

### Response Time
- **Target latency:** <200ms (typical LAN)
- **Motor update rate:** ~10 Hz (100ms control loop)
- **Telemetry rate:** ~1 Hz (1000ms status updates)

---

## CORS Support

All endpoints include CORS headers:
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

This allows the web frontend to make requests from `github.io` domain.

---

## Error Handling

### Common Error Codes

| Status | Error | Solution |
|--------|-------|----------|
| 400 | Invalid speed value | Ensure speed is -100 to 100 |
| 404 | Endpoint not found | Check URL spelling |
| 500 | Internal server error | Check Pico REPL for exceptions |
| Timeout | No response | Verify WiFi connection |

### Debug Mode

Check the Pico's REPL serial output (115200 baud) for detailed logs:
```
[API] POST /motor received: a=50, b=-30
[Motor] Setting Motor A to 50
[Motor] Setting Motor B to -30
```

---

## Rate Limiting

No hard rate limiting is enforced, but:
- **Recommended control rate:** 10 Hz (100ms between commands)
- **Recommended telemetry rate:** 1 Hz (1000ms between status polls)
- **Motor update latency:** ~10-20ms

Faster rates may cause Pico WiFi stack congestion.

---

## Connection States

### AP Mode (Initial Setup)
- SSID: `RoverSetup`
- Password: `rover1234`
- IP: `192.168.4.1`
- Used for WiFi pairing only

### Station Mode (Normal Operation)
- Connects to user's home WiFi
- IP assigned by DHCP (typically `192.168.1.x` or `192.168.0.x`)
- Frontend auto-discovers via IP scanning

---

## Example: Controlling Rover with cURL

### Test connectivity:
```bash
curl http://192.168.1.100:8000/
```

### Get status:
```bash
curl http://192.168.1.100:8000/status | jq .
```

### Drive forward:
```bash
curl -X POST "http://192.168.1.100:8000/motor?a=75&b=75"
```

### Stop:
```bash
curl -X POST http://192.168.1.100:8000/motor/stop
```

### Scan WiFi (AP mode):
```bash
curl http://192.168.4.1:8000/api/scan | jq .
```

### Connect to WiFi (AP mode):
```bash
curl -X POST http://192.168.4.1:8000/api/connect \
  -H "Content-Type: application/json" \
  -d '{"ssid":"MyNetwork","password":"mypassword"}'
```

---

## WebSocket Support (Future)

A WebSocket endpoint is planned for Phase 4:
```
ws://{rover_ip}:8000/ws/telemetry
```

This will provide real-time telemetry streaming without polling.
