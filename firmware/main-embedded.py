"""
Pico Rover Main Boot Sequence
Sets up AP mode, motors, and web server for embedded webpage
"""

import time
from machine import Pin, PWM
from motor_control import Motor, Rover
from wifi_manager import WiFiManager
from api_server import APIServer

def main():
    print("\n" + "="*60)
    print("🚗 PICO ROVER BOOT SEQUENCE")
    print("="*60)
    
    # ==================== Initialize Motors ====================
    print("\n[BOOT] Initializing motors...")
    try:
        motor_a = Motor(in1_pin=19, in2_pin=18, pwm_pin=14)
        motor_b = Motor(in1_pin=17, in2_pin=16, pwm_pin=15)
        rover = Rover(motor_a, motor_b)
        print("[BOOT] ✓ Motors initialized")
    except Exception as e:
        print(f"[BOOT] ✗ Motor initialization failed: {e}")
        return False
    
    # ==================== Initialize WiFi ====================
    print("\n[BOOT] Initializing WiFi...")
    try:
        wifi = WiFiManager()
        print("[BOOT] ✓ WiFi manager initialized")
    except Exception as e:
        print(f"[BOOT] ✗ WiFi initialization failed: {e}")
        return False
    
    # ==================== Start Access Point ====================
    print("\n[BOOT] Starting Access Point mode...")
    try:
        wifi.start_ap("RoverSetup", "rover1234")
        print("[BOOT] ✓ Access Point started")
        print("[BOOT] SSID: RoverSetup")
        print("[BOOT] Password: rover1234")
        print("[BOOT] IP: 192.168.4.1")
    except Exception as e:
        print(f"[BOOT] ✗ AP startup failed: {e}")
        return False
    
    # ==================== Start API Server ====================
    print("\n[BOOT] Starting API Server...")
    try:
        server = APIServer(rover, port=8000)
        print("[BOOT] ✓ API Server created")
        print("[BOOT] Starting server...")
        
        # Server runs blocking, so this starts it
        server.start()
        
    except Exception as e:
        print(f"[BOOT] ✗ API Server startup failed: {e}")
        return False
    
    return True


def test_motors():
    """Quick motor test (optional)"""
    print("\n[TEST] Running motor tests...")
    
    motor_a = Motor(in1_pin=19, in2_pin=18, pwm_pin=14)
    motor_b = Motor(in1_pin=17, in2_pin=16, pwm_pin=15)
    rover = Rover(motor_a, motor_b)
    
    # Test forward
    print("  → Moving forward...")
    rover.drive(100, 100)
    time.sleep(1)
    
    # Test backward
    print("  → Moving backward...")
    rover.drive(-100, -100)
    time.sleep(1)
    
    # Test turn
    print("  → Turning left...")
    rover.drive(100, -100)
    time.sleep(1)
    
    # Stop
    print("  → Stopping...")
    rover.stop()
    
    print("[TEST] ✓ Motor test complete!")


if __name__ == '__main__':
    try:
        # Optional: Run motor test first
        # test_motors()
        
        # Start boot sequence
        success = main()
        
        if not success:
            print("\n[BOOT] ✗ Boot sequence failed!")
            print("[BOOT] Check errors above and try again")
    
    except KeyboardInterrupt:
        print("\n\n[BOOT] Interrupted by user")
    except Exception as e:
        print(f"\n[BOOT] Fatal error: {e}")
        import traceback
        traceback.print_exc()
