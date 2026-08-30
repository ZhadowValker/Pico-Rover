#!/usr/bin/env python3
"""
Pico Rover API Testing Script
Tests all endpoints with detailed output

Usage:
    python test_api.py                  # Test default IP (192.168.4.1)
    python test_api.py 192.168.1.100   # Test custom IP
"""

import requests
import json
import time
import sys
from typing import Dict, Any

class RoverAPITester:
    def __init__(self, base_url: str = "http://192.168.4.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.results = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with level indicator"""
        indicators = {
            "INFO": "ℹ",
            "OK": "✓",
            "FAIL": "✗",
            "WARN": "⚠",
            "TEST": "→"
        }
        indicator = indicators.get(level, "•")
        print(f"{indicator} {message}")
        self.results.append((level, message))
    
    def test_connection(self) -> bool:
        """Test if rover is reachable"""
        try:
            print("\n" + "="*60)
            print("TEST 1: Connection Check")
            print("="*60)
            response = self.session.get(f"{self.base_url}/", timeout=2)
            self.log("Rover is reachable", "OK")
            return True
        except requests.exceptions.ConnectionError:
            self.log(f"Cannot connect to {self.base_url}", "FAIL")
            self.log("Make sure Pico is powered and AP is enabled", "INFO")
            return False
        except Exception as e:
            self.log(f"Connection error: {e}", "FAIL")
            return False
    
    def test_status(self) -> Dict[str, Any]:
        """Get rover status"""
        print("\n" + "="*60)
        print("TEST 2: Get Rover Status")
        print("="*60)
        try:
            response = self.session.get(f"{self.base_url}/status")
            data = response.json()
            self.log("Status endpoint works", "OK")
            
            # Display status data
            print("\n📊 Rover Status:")
            if 'battery_voltage' in data:
                print(f"   Battery: {data['battery_voltage']}V")
            if 'uptime_ms' in data:
                print(f"   Uptime: {data['uptime_ms']}ms")
            if 'motor_a_speed' in data:
                print(f"   Motor A: {data['motor_a_speed']}%")
            if 'motor_b_speed' in data:
                print(f"   Motor B: {data['motor_b_speed']}%")
            if 'latency_ms' in data:
                print(f"   Latency: {data['latency_ms']}ms")
            
            return data
        except requests.exceptions.Timeout:
            self.log("Status request timed out", "FAIL")
            return {}
        except Exception as e:
            self.log(f"Status failed: {e}", "FAIL")
            return {}
    
    def test_motor_control(self) -> bool:
        """Test motor control with movements"""
        print("\n" + "="*60)
        print("TEST 3: Motor Control")
        print("="*60)
        
        try:
            # Test 1: Forward
            print("\n🚗 Movement Test Sequence:")
            self.log("Moving forward (50% speed, 2 seconds)", "TEST")
            response = self.session.post(
                f"{self.base_url}/motor",
                json={"a": 50, "b": 50},
                timeout=2
            )
            if response.status_code == 200:
                self.log("Forward command accepted", "OK")
            time.sleep(2)
            
            # Test 2: Turn left
            self.log("Turning left (50% differential, 2 seconds)", "TEST")
            response = self.session.post(
                f"{self.base_url}/motor",
                json={"a": 50, "b": -50},
                timeout=2
            )
            if response.status_code == 200:
                self.log("Turn command accepted", "OK")
            time.sleep(2)
            
            # Test 3: Backward
            self.log("Moving backward (50% speed, 2 seconds)", "TEST")
            response = self.session.post(
                f"{self.base_url}/motor",
                json={"a": -50, "b": -50},
                timeout=2
            )
            if response.status_code == 200:
                self.log("Backward command accepted", "OK")
            time.sleep(2)
            
            # Test 4: Stop
            self.log("Stopping motors", "TEST")
            response = self.session.post(
                f"{self.base_url}/motor/stop",
                timeout=2
            )
            if response.status_code == 200:
                self.log("Stop command accepted", "OK")
            
            self.log("Motor control sequence completed", "OK")
            return True
            
        except Exception as e:
            self.log(f"Motor control failed: {e}", "FAIL")
            return False
    
    def test_motor_speeds(self) -> bool:
        """Test various motor speed levels"""
        print("\n" + "="*60)
        print("TEST 4: Motor Speed Levels")
        print("="*60)
        
        speeds = [
            (25, "Low (25%)"),
            (50, "Medium (50%)"),
            (75, "High (75%)"),
            (100, "Full (100%)")
        ]
        
        try:
            for speed, label in speeds:
                self.log(f"Testing {label}", "TEST")
                response = self.session.post(
                    f"{self.base_url}/motor",
                    json={"a": speed, "b": speed},
                    timeout=2
                )
                if response.status_code == 200:
                    self.log(f"{label} - OK", "OK")
                time.sleep(1)
            
            # Stop at end
            self.session.post(f"{self.base_url}/motor/stop")
            self.log("Speed level tests completed", "OK")
            return True
            
        except Exception as e:
            self.log(f"Speed level test failed: {e}", "FAIL")
            return False
    
    def test_wifi_scan(self) -> Dict[str, Any]:
        """Scan available WiFi networks"""
        print("\n" + "="*60)
        print("TEST 5: WiFi Network Scan")
        print("="*60)
        try:
            self.log("Scanning for WiFi networks...", "TEST")
            response = self.session.get(f"{self.base_url}/api/scan", timeout=5)
            data = response.json()
            self.log("WiFi scan completed", "OK")
            
            networks = data.get('networks', [])
            print(f"\n📡 Found {len(networks)} networks:")
            for i, net in enumerate(networks[:10], 1):
                ssid = net.get('ssid', 'Unknown')
                rssi = net.get('rssi', 'N/A')
                channel = net.get('channel', 'N/A')
                security = net.get('security', 'N/A')
                print(f"   {i}. {ssid} (Ch:{channel}, RSSI:{rssi}dBm, Sec:{security})")
            
            if len(networks) > 10:
                print(f"   ... and {len(networks)-10} more")
            
            return data
        except Exception as e:
            self.log(f"WiFi scan failed: {e}", "FAIL")
            return {}
    
    def test_wifi_connect(self, ssid: str, password: str) -> bool:
        """Connect to a WiFi network"""
        print("\n" + "="*60)
        print("TEST 6: WiFi Connection")
        print("="*60)
        try:
            self.log(f"Attempting to connect to '{ssid}'...", "TEST")
            response = self.session.post(
                f"{self.base_url}/api/connect",
                json={"ssid": ssid, "password": password},
                timeout=10
            )
            data = response.json()
            
            if data.get('success'):
                self.log(f"Connected to {ssid}", "OK")
                if 'ip' in data:
                    print(f"   IP Address: {data['ip']}")
                return True
            else:
                error = data.get('error', 'Unknown error')
                self.log(f"Failed to connect: {error}", "FAIL")
                return False
        except Exception as e:
            self.log(f"WiFi connect failed: {e}", "FAIL")
            return False
    
    def run_all_tests(self, skip_wifi_connect: bool = True):
        """Run complete test suite"""
        print("\n" + "╔" + "="*58 + "╗")
        print("║" + " "*15 + "PICO ROVER API TEST SUITE" + " "*17 + "║")
        print("╚" + "="*58 + "╝")
        print(f"\nTarget: {self.base_url}\n")
        
        # Test 1: Connection
        if not self.test_connection():
            self.log("Cannot proceed - rover unreachable", "FAIL")
            self.print_summary()
            return
        
        # Test 2: Status
        self.test_status()
        
        # Test 3: Motor Control
        self.test_motor_control()
        
        # Test 4: Motor Speeds
        self.test_motor_speeds()
        
        # Test 5: WiFi Scan
        self.test_wifi_scan()
        
        # Test 6: WiFi Connect (optional)
        if not skip_wifi_connect:
            ssid = input("\nEnter WiFi SSID to connect to: ")
            password = input("Enter WiFi password: ")
            self.test_wifi_connect(ssid, password)
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        passed = len([r for r in self.results if r[0] == "OK"])
        failed = len([r for r in self.results if r[0] == "FAIL"])
        total = passed + failed
        
        if total > 0:
            pass_rate = (passed / total) * 100
            print(f"\nResults: {passed}/{total} tests passed ({pass_rate:.1f}%)")
            
            if failed > 0:
                print(f"\n⚠️  {failed} test(s) failed:")
                for level, msg in self.results:
                    if level == "FAIL":
                        print(f"   • {msg}")
        
        print("\n" + "="*60)
        print("✅ Test suite completed!" if failed == 0 else "❌ Some tests failed")
        print("="*60 + "\n")


def main():
    """Main entry point"""
    # Parse arguments
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = "192.168.4.1"
    
    # Create tester
    url = f"http://{ip}:8000"
    tester = RoverAPITester(url)
    
    # Run tests
    try:
        tester.run_all_tests(skip_wifi_connect=True)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        tester.print_summary()


if __name__ == "__main__":
    main()
