# wifi_manager.py - WiFi AP and Station Management

import network
import json
import os
from config import *

class WiFiManager:
    """Handle WiFi AP for setup and station connection"""
    
    def __init__(self):
        self.ap = None
        self.sta = None
        self.config_file = 'wifi_config.json'
        self.connected = False
    
    def start_ap(self):
        """Start WiFi AP for initial setup"""
        print(f"📡 Starting AP: {AP_SSID}")
        
        self.ap = network.WLAN(network.AP_IF)
        self.ap.config(essid=AP_SSID, password=AP_PASSWORD)
        self.ap.config(dhcp_hostname='rover')
        self.ap.ifconfig((AP_IP, AP_SUBNET, AP_IP, AP_IP))
        self.ap.active(True)
        
        # Wait for AP to start
        import time
        time.sleep(1)
        
        status = self.ap.isconnected()
        if status:
            print(f"✅ AP active at {AP_IP}")
        else:
            print("❌ Failed to start AP")
        
        return status
    
    def stop_ap(self):
        """Stop WiFi AP"""
        if self.ap:
            self.ap.active(False)
            print("📡 AP stopped")
    
    def connect_station(self, ssid, password):
        """Connect to WiFi station"""
        print(f"🔗 Connecting to {ssid}...")
        
        self.sta = network.WLAN(network.STA_IF)
        self.sta.active(True)
        
        # Scan for network
        networks = self.sta.scan()
        ssid_found = any(net[0].decode() == ssid for net in networks)
        
        if not ssid_found:
            print(f"❌ Network '{ssid}' not found")
            return False
        
        # Connect
        self.sta.connect(ssid, password)
        
        # Wait for connection (max 10 seconds)
        import time
        for i in range(20):
            if self.sta.isconnected():
                print("✅ Connected!")
                print(f"IP: {self.sta.ifconfig()[0]}")
                self.connected = True
                self.save_config(ssid, password)
                return True
            time.sleep(0.5)
        
        print("❌ Connection timeout")
        return False
    
    def auto_connect(self):
        """Automatically connect using saved credentials"""
        config = self.load_config()
        if config:
            print(f"🔄 Auto-connecting to {config['ssid']}...")
            return self.connect_station(config['ssid'], config['password'])
        return False
    
    def save_config(self, ssid, password):
        """Save WiFi credentials"""
        config = {'ssid': ssid, 'password': password}
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
            print(f"💾 Config saved")
        except Exception as e:
            print(f"❌ Failed to save config: {e}")
    
    def load_config(self):
        """Load WiFi credentials"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except:
            return None
    
    def scan_networks(self):
        """Scan available WiFi networks"""
        if not self.sta:
            self.sta = network.WLAN(network.STA_IF)
            self.sta.active(True)
        
        print("📡 Scanning networks...")
        networks = self.sta.scan()
        
        result = []
        for net in networks:
            result.append({
                'ssid': net[0].decode(),
                'bssid': ':'.join(f'{b:02x}' for b in net[1]),
                'channel': net[2],
                'rssi': net[3],
                'sec': net[4],
                'hidden': net[5]
            })
        
        return result
    
    def get_status(self):
        """Get WiFi status"""
        status = {
            'connected': self.connected,
            'mode': 'AP+STA'
        }
        
        if self.ap and self.ap.isconnected():
            status['ap'] = {
                'ssid': AP_SSID,
                'ip': AP_IP,
                'stations': self.ap.status('stations')
            }
        
        if self.sta and self.sta.isconnected():
            ip, subnet, gw, dns = self.sta.ifconfig()
            status['sta'] = {
                'ssid': self.sta.config('essid').decode() if self.sta.config('essid') else 'Unknown',
                'ip': ip,
                'rssi': self.sta.status('rssi')
            }
        
        return status


# Global WiFi manager instance
wifi = WiFiManager()
