# cURL Quick Reference for Pico Rover API

## Quick Setup

Assuming Pico is at `192.168.4.1:8000` (change as needed)

```bash
# For convenience, set as variable
export ROVER=192.168.4.1:8000
```

---

## Connection Tests

### Test Server is Online
```bash
curl -X GET http://$ROVER/
```

### Get Rover Status
```bash
curl -X GET http://$ROVER/status
```

Expected output:
```json
{
  "battery_voltage": 7.2,
  "uptime_ms": 12345,
  "motor_a_speed": 0,
  "motor_b_speed": 0,
  "latency_ms": 15
}
```

---

## Motor Control

### Move Forward (Full Speed)
```bash
curl -X POST http://$ROVER/motor \
  -H "Content-Type: application/json" \
  -d '{"a": 100, "b": 100}'
```

### Move Forward (Half Speed)
```bash
curl -X POST http://$ROVER/motor \
  -d '{"a": 50, "b": 50}'
```

### Move Backward
```bash
curl -X POST http://$ROVER/motor \
  -d '{"a": -100, "b": -100}'
```

### Turn Left
```bash
curl -X POST http://$ROVER/motor \
  -d '{"a": 100, "b": -100}'
```

### Turn Right
```bash
curl -X POST http://$ROVER/motor \
  -d '{"a": -100, "b": 100}'
```

### Pivot (One Motor Only)
```bash
# Only Motor A
curl -X POST http://$ROVER/motor \
  -d '{"a": 100, "b": 0}'

# Only Motor B
curl -X POST http://$ROVER/motor \
  -d '{"a": 0, "b": 100}'
```

### Emergency Stop
```bash
curl -X POST http://$ROVER/motor/stop
```

---

## Motor Speed Reference

| Speed | Effect |
|-------|--------|
| 100 | Full speed forward |
| 75 | High speed forward |
| 50 | Medium speed forward |
| 25 | Low speed forward |
| 0 | No movement |
| -25 | Low speed backward |
| -50 | Medium speed backward |
| -75 | High speed backward |
| -100 | Full speed backward |

---

## WiFi Management

### Scan Available Networks
```bash
curl -X GET http://$ROVER/api/scan
```

Expected output:
```json
{
  "networks": [
    {
      "ssid": "MyHome",
      "rssi": -45,
      "channel": 6,
      "security": 3
    },
    {
      "ssid": "Guest",
      "rssi": -62,
      "channel": 11,
      "security": 3
    }
  ]
}
```

### Connect to WiFi
```bash
curl -X POST http://$ROVER/api/connect \
  -H "Content-Type: application/json" \
  -d '{
    "ssid": "MyNetwork",
    "password": "mypassword123"
  }'
```

Expected response:
```json
{
  "success": true,
  "ip": "192.168.1.100",
  "ssid": "MyNetwork"
}
```

---

## Practical Movement Sequences

### Drive in Square (using bash)

```bash
#!/bin/bash

ROVER="192.168.4.1:8000"
DELAY=3  # seconds

echo "Driving in square..."

echo "→ Forward"
curl -s -X POST http://$ROVER/motor -d '{"a": 100, "b": 100}' > /dev/null
sleep $DELAY

echo "→ Turn left"
curl -s -X POST http://$ROVER/motor -d '{"a": 100, "b": -100}' > /dev/null
sleep $DELAY

echo "→ Forward"
curl -s -X POST http://$ROVER/motor -d '{"a": 100, "b": 100}' > /dev/null
sleep $DELAY

echo "→ Turn left"
curl -s -X POST http://$ROVER/motor -d '{"a": 100, "b": -100}' > /dev/null
sleep $DELAY

# Repeat for complete square...

echo "✓ Done!"
curl -s -X POST http://$ROVER/motor/stop > /dev/null
```

### Zigzag Pattern

```bash
#!/bin/bash

ROVER="192.168.4.1:8000"
DELAY=2

for i in {1..5}; do
  echo "Zigzag $i"
  
  # Forward-left
  curl -s -X POST http://$ROVER/motor -d '{"a": 100, "b": 30}' > /dev/null
  sleep $DELAY
  
  # Forward-right
  curl -s -X POST http://$ROVER/motor -d '{"a": 30, "b": 100}' > /dev/null
  sleep $DELAY
done

curl -s -X POST http://$ROVER/motor/stop > /dev/null
echo "✓ Zigzag complete"
```

---

## Performance Testing

### Measure Latency
```bash
time curl -X GET http://$ROVER/status > /dev/null
```

Look for response time (should be < 200ms)

### Continuous Polling (Status)
```bash
watch -n 1 "curl -s http://$ROVER/status | jq ."
```

Requires `jq` (JSON parser)

### Stress Test (100 requests)
```bash
for i in {1..100}; do
  curl -s -X POST http://$ROVER/motor -d '{"a": 50, "b": 50}' > /dev/null
  echo "Request $i"
done

curl -s -X POST http://$ROVER/motor/stop > /dev/null
echo "✓ Stress test complete"
```

---

## Useful Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Quick rover commands
alias rover-forward='curl -s -X POST http://192.168.4.1:8000/motor -d "{\"a\": 100, \"b\": 100}"'
alias rover-back='curl -s -X POST http://192.168.4.1:8000/motor -d "{\"a\": -100, \"b\": -100}"'
alias rover-left='curl -s -X POST http://192.168.4.1:8000/motor -d "{\"a\": 100, \"b\": -100}"'
alias rover-right='curl -s -X POST http://192.168.4.1:8000/motor -d "{\"a\": -100, \"b\": 100}"'
alias rover-stop='curl -s -X POST http://192.168.4.1:8000/motor/stop'
alias rover-status='curl -s http://192.168.4.1:8000/status | jq .'
alias rover-scan='curl -s http://192.168.4.1:8000/api/scan | jq .'
```

Then use:
```bash
rover-forward
rover-stop
rover-status
rover-scan
```

---

## With Pretty Output (jq)

### Pretty Print Status
```bash
curl -s http://$ROVER/status | jq .
```

### Pretty Print WiFi Networks
```bash
curl -s http://$ROVER/api/scan | jq '.networks[] | {ssid, rssi, channel}'
```

### Save Response to File
```bash
curl -s http://$ROVER/status > rover_status.json
```

---

## Troubleshooting cURL

### Connection Refused
```
curl: (7) Failed to connect to 192.168.4.1 port 8000: Connection refused
```

**Solutions:**
- Check Pico is powered on
- Verify you're connected to Pico's AP
- Check firewall settings

### Timeout
```
curl: (28) Operation timeout
```

**Solutions:**
- Pico may be overloaded
- Check network latency: `ping 192.168.4.1`
- Try again in a moment

### Invalid JSON Response
```
curl: (23) Failed writing body
```

**Solutions:**
- Check firmware is running API server
- Verify endpoint is correct
- Check Pico logs via REPL

---

## Windows PowerShell (Alternative to cURL)

If `curl` doesn't work, use `Invoke-WebRequest`:

```powershell
# Status
Invoke-WebRequest -Uri "http://192.168.4.1:8000/status" | ConvertTo-Json

# Move forward
$body = @{a=100; b=100} | ConvertTo-Json
Invoke-WebRequest -Uri "http://192.168.4.1:8000/motor" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body

# Stop
Invoke-WebRequest -Uri "http://192.168.4.1:8000/motor/stop" -Method POST
```

---

## Real-World Example: Control from Phone

```bash
# SSH into a server connected to same network as Pico

# Drive rover remotely
curl -X POST http://rover.local:8000/motor -d '{"a": 100, "b": 100}'

# Get status
curl http://rover.local:8000/status

# Stop when done
curl -X POST http://rover.local:8000/motor/stop
```

---

## Tips & Tricks

1. **Silent output:** Use `-s` flag
   ```bash
   curl -s http://$ROVER/status
   ```

2. **Show headers:** Use `-i` flag
   ```bash
   curl -i http://$ROVER/status
   ```

3. **Verbose output:** Use `-v` flag
   ```bash
   curl -v http://$ROVER/status
   ```

4. **Follow redirects:** Use `-L` flag (if needed)
   ```bash
   curl -L http://$ROVER/status
   ```

5. **Set timeout:** Use `--max-time` (seconds)
   ```bash
   curl --max-time 5 http://$ROVER/status
   ```

---

**Ready to test?** Pick an IP address and start sending commands! 🚀
