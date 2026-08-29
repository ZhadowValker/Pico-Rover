# main.py - Boot sequence for Pico W Rover

import time
import sys

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
    server = APIServer(rover, wifi, port=8000)
    print("✅ API server ready")
    
    # Start server in a thread-like manner (blocking call)
    print("\n" + "="*50)
    print("✅ Rover is READY!")
    print("="*50)
    print(f"AP SSID: RoverSetup")
    print(f"AP IP: 192.168.4.1")
    print(f"Setup: http://192.168.4.1/setup")
    print("="*50 + "\n")
    
    server.start()  # This blocks
    
except Exception as e:
    print(f"❌ API server failed: {e}")
    sys.exit(1)
