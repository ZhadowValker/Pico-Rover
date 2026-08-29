# api_server.py - REST API Server for Rover Control

import socket
import json
import time
from machine import ADC
from config import *

class APIServer:
    """Simple HTTP REST API server for rover control"""
    
    def __init__(self, rover, wifi_manager, port=SERVER_PORT):
        self.rover = rover
        self.wifi = wifi_manager
        self.port = port
        self.running = False
        self.boot_time = time.time()
        self.battery_adc = ADC(BATTERY_ADC)
    
    def get_battery_voltage(self):
        """Read battery voltage from ADC"""
        try:
            adc_value = self.battery_adc.read_u16()
            # Pico Vref = 3.3V
            voltage = (adc_value / 65535) * 3.3
            # Voltage divider correction (if using voltage divider)
            # voltage *= 2 (example: if dividing by 2)
            return voltage
        except:
            return 0.0
    
    def parse_query_string(self, qs):
        """Parse query string"""
        params = {}
        if qs:
            for pair in qs.split('&'):
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    try:
                        params[key] = float(value) if '.' in value else int(value)
                    except:
                        params[key] = value
        return params
    
    def send_response(self, client, status_code, content_type, body):
        """Send HTTP response with CORS headers"""
        if isinstance(body, dict):
            body = json.dumps(body)
        
        if isinstance(body, str):
            body = body.encode()
        
        response = (
            f"HTTP/1.1 {status_code}\r\n"
            f"Content-Type: {content_type}\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Access-Control-Allow-Origin: *\r\n"
            f"Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
            f"Access-Control-Allow-Headers: Content-Type\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        ).encode() + body
        
        try:
            client.sendall(response)
        except:
            pass
    
    def handle_get_motor(self, params, client):
        """GET /motor - Set motor speeds"""
        speed_a = params.get('a', 0)
        speed_b = params.get('b', 0)
        
        # Clamp speeds
        speed_a = max(-100, min(100, speed_a))
        speed_b = max(-100, min(100, speed_b))
        
        # Apply to rover
        self.rover.drive(speed_a, speed_b)
        
        response = {
            'status': 'ok',
            'a': speed_a,
            'b': speed_b,
            'speeds': self.rover.get_speeds()
        }
        
        self.send_response(client, '200 OK', 'application/json', response)
    
    def handle_post_motor(self, params, body, client):
        """POST /motor - Set motor speeds"""
        self.handle_get_motor(params, client)
    
    def handle_get_status(self, client):
        """GET /status - Get rover status"""
        uptime = int(time.time() - self.boot_time)
        battery = self.get_battery_voltage()
        
        status = {
            'status': 'ok',
            'connected': self.wifi.connected,
            'uptime': uptime,
            'battery': battery,
            'motors': self.rover.get_speeds(),
            'wifi': self.wifi.get_status()
        }
        
        self.send_response(client, '200 OK', 'application/json', status)
    
    def handle_get_scan(self, client):
        """GET /api/scan - Scan WiFi networks"""
        networks = self.wifi.scan_networks()
        response = {
            'status': 'ok',
            'networks': networks
        }
        self.send_response(client, '200 OK', 'application/json', response)
    
    def handle_post_connect(self, body, client):
        """POST /api/connect - Connect to WiFi"""
        try:
            data = json.loads(body.decode())
            ssid = data.get('ssid')
            password = data.get('password')
            
            if not ssid:
                self.send_response(client, '400 Bad Request', 'application/json', 
                                 {'error': 'Missing SSID'})
                return
            
            success = self.wifi.connect_station(ssid, password)
            response = {
                'status': 'ok',
                'success': success,
                'ssid': ssid
            }
            
            self.send_response(client, '200 OK', 'application/json', response)
        except Exception as e:
            self.send_response(client, '400 Bad Request', 'application/json', 
                             {'error': str(e)})
    
    def handle_root(self, client):
        """GET / - Root endpoint"""
        html = """
        <html>
        <head><title>Pico Rover</title></head>
        <body style="font-family: Arial; margin: 20px;">
            <h1>🤖 Pico Rover Control</h1>
            <p>API endpoints:</p>
            <ul>
                <li><code>GET /status</code> - Get rover status</li>
                <li><code>POST /motor?a=50&b=-30</code> - Set motor speeds</li>
                <li><code>GET /api/scan</code> - Scan WiFi networks</li>
                <li><code>POST /api/connect</code> - Connect to WiFi</li>
            </ul>
            <p>Use the <a href="https://zhadowvalker.github.io/Pico-Rover/">GitHub Pages remote</a> to control the rover.</p>
        </body>
        </html>
        """
        self.send_response(client, '200 OK', 'text/html', html)
    
    def handle_client(self, client, addr):
        """Handle incoming client connection"""
        try:
            # Receive request
            request = b''
            while True:
                chunk = client.recv(1024)
                if not chunk:
                    break
                request += chunk
                if len(request) > 4096:
                    break
                if b'\r\n\r\n' in request:
                    break
            
            # Parse request
            request_str = request.decode('utf-8', errors='ignore')
            lines = request_str.split('\r\n')
            
            if not lines:
                return
            
            # Parse request line
            parts = lines[0].split(' ')
            if len(parts) < 2:
                return
            
            method = parts[0]
            path = parts[1]
            
            # Parse path and query string
            if '?' in path:
                path, qs = path.split('?', 1)
                params = self.parse_query_string(qs)
            else:
                params = {}
            
            # Get body if present
            body = b''
            if len(lines) > 1:
                body_start = request.find(b'\r\n\r\n')
                if body_start != -1:
                    body = request[body_start + 4:]
            
            # Route requests
            if path == '/' and method == 'GET':
                self.handle_root(client)
            elif path == '/status' and method == 'GET':
                self.handle_get_status(client)
            elif path == '/motor':
                if method == 'GET':
                    self.handle_get_motor(params, client)
                elif method == 'POST':
                    self.handle_post_motor(params, body, client)
            elif path == '/api/scan' and method == 'GET':
                self.handle_get_scan(client)
            elif path == '/api/connect' and method == 'POST':
                self.handle_post_connect(body, client)
            else:
                self.send_response(client, '404 Not Found', 'text/plain', '404 Not Found')
        
        except Exception as e:
            print(f"❌ Error handling client: {e}")
        
        finally:
            client.close()
    
    def start(self):
        """Start API server"""
        print(f"🌐 Starting API server on port {self.port}...")
        
        self.running = True
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server.bind(('0.0.0.0', self.port))
            server.listen(5)
            print(f"✅ API server listening on port {self.port}")
            
            while self.running:
                try:
                    client, addr = server.accept()
                    print(f"📞 Connection from {addr}")
                    self.handle_client(client, addr)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")
        
        finally:
            server.close()
            print("🛑 API server stopped")
    
    def stop(self):
        """Stop API server"""
        self.running = False


# Global API server instance (created in main.py)
server = None
