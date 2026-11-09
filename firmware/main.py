# main.py - Boot sequence for Pico W Rover

import time
import sys

# The TLS handshake is the slow part (1-3 s at the default 125 MHz).
# Running the RP2040 at 250 MHz makes it roughly twice as fast.
try:
    import machine
    machine.freq(250_000_000)
except Exception as e:
    print("Overclock skipped:", e)

print("\n" + "="*50)
print("🤖 Pico W Rover Startup")
print("="*50)

# Import modules
print("📦 Loading modules...")
try:
    from motor_control import rover
    from wifi_manager import wifi
    from api_server import APIServer
    print("✅ Modules loaded")
except Exception as e:
    print(f"❌ Failed to load modules: {e}")
    sys.exit(1)

# Initialize motors
print("⚙️  Initializing motors...")
try:
    rover.stop()
    print("✅ Motors initialized")
except Exception as e:
    print(f"❌ Motor init failed: {e}")

# Initialize WiFi
print("📡 Initializing WiFi...")
try:
    # Start AP for setup
    wifi.start_ap()
    
    # Try to auto-connect to saved network
    if wifi.load_config():
        print("🔄 Attempting auto-connect...")
        wifi.auto_connect()
    else:
        print("⚠️  No saved WiFi config. Use RoverSetup AP to configure.")
    
    print("✅ WiFi initialized")
except Exception as e:
    print(f"❌ WiFi init failed: {e}")

# Start API server
print("🌐 Starting API server...")
try:
    server = APIServer(rover, port=443, use_tls=True, http_port=80)
    print("✅ API server ready")
    
    # Start server in a thread-like manner (blocking call)
    print("\n" + "="*50)
    print("✅ Rover is READY!")
    print("="*50)
    print(f"AP SSID: RoverSetup")
    print(f"AP IP: 192.168.4.1")
    print(f"Control page (reliable): http://192.168.4.1/")
    print(f"Gyro page (secure):      https://192.168.4.1/")
    print("="*50 + "\n")
    
    server.start()  # This blocks
    
except Exception as e:
    print(f"❌ API server failed: {e}")
    sys.exit(1)
