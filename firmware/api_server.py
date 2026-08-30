"""
Pico Rover REST API Server with Static File Serving
Serves HTML interface + REST API endpoints
"""

import socket
import json
import time
import gc
from machine import ADC, Pin

class APIServer:
    def __init__(self, rover, port=8000):
        """
        Initialize API server
        
        Args:
            rover: Rover instance (from motor_control.py)
            port: Server port (default 8000)
        """
        self.rover = rover
        self.port = port
        self.running = False
        self.start_time = time.time()
        self.battery_adc = ADC(Pin(26))  # GPIO 26 for battery voltage
        
        print(f"[APIServer] Initialized on port {port}")
    
    def get_battery_voltage(self):
        """Read battery voltage from ADC (GPIO 26)"""
        try:
            # Read ADC (0-65535)
            # Voltage ref: 3.3V
            # Adjust based on your voltage divider ratio
            raw_value = self.battery_adc.read_u16()
            voltage = (raw_value / 65535) * 3.3
            return round(voltage, 2)
        except:
            return 0.0
    
    def get_uptime_ms(self):
        """Get uptime in milliseconds"""
        return int((time.time() - self.start_time) * 1000)
    
    def read_file(self, filename):
        """Read file from filesystem"""
        try:
            with open(filename, 'r') as f:
                return f.read()
        except OSError:
            return None
    
    def get_mime_type(self, filename):
        """Get MIME type for file"""
        if filename.endswith('.html'):
            return 'text/html'
        elif filename.endswith('.css'):
            return 'text/css'
        elif filename.endswith('.js'):
            return 'application/javascript'
        elif filename.endswith('.json'):
            return 'application/json'
        elif filename.endswith('.png'):
            return 'image/png'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            return 'image/jpeg'
        else:
            return 'text/plain'
    
    def send_response(self, client, status_code, body, content_type='application/json'):
        """Send HTTP response"""
        status_messages = {
            200: 'OK',
            404: 'Not Found',
            500: 'Internal Server Error'
        }
        
        status_text = status_messages.get(status_code, 'Unknown')
        
        # Build response header
        if isinstance(body, dict):
            body = json.dumps(body)
            content_type = 'application/json'
        
        if isinstance(body, str):
            body = body.encode()
        
        response = (
            f"HTTP/1.1 {status_code} {status_text}\r\n"
            f"Content-Type: {content_type}; charset=utf-8\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Access-Control-Allow-Origin: *\r\n"
            f"Connection: close\r\n"
            f"\r\n"
        )
        
        try:
            client.send(response.encode())
            client.send(body)
        except Exception as e:
            print(f"[APIServer] Error sending response: {e}")
    
    def parse_json_body(self, request):
        """Parse JSON from request body"""
        try:
            # Find empty line (end of headers)
            parts = request.split('\r\n\r\n', 1)
            if len(parts) > 1:
                body = parts[1]
                return json.loads(body)
        except:
            pass
        return {}
    
    def handle_request(self, request):
        """Parse HTTP request"""
        try:
            lines = request.split('\r\n')
            request_line = lines[0].split()
            
            if len(request_line) < 2:
                return None, None
            
            method = request_line[0]
            path = request_line[1]
            
            return method, path
        except:
            return None, None
    
    def route_request(self, client, method, path, request):
        """Route HTTP request to handler"""
        
        # CORS preflight
        if method == 'OPTIONS':
            self.send_response(client, 200, '')
            return
        
        # API Routes
        if path == '/':
            # Serve index.html or root status
            html_content = self.read_file('/index.html')
            if html_content:
                self.send_response(client, 200, html_content, 'text/html')
            else:
                self.send_response(client, 200, {
                    'status': 'online',
                    'message': 'Pico Rover API Server',
                    'version': '1.0'
                })
        
        elif path == '/index.html':
            # Serve HTML interface
            html_content = self.read_file('/index.html')
            if html_content:
                self.send_response(client, 200, html_content, 'text/html')
            else:
                self.send_response(client, 404, {'error': 'index.html not found'})
        
        elif path == '/status' and method == 'GET':
            # Get rover status
            speeds = self.rover.get_speeds()
            self.send_response(client, 200, {
                'battery_voltage': self.get_battery_voltage(),
                'uptime_ms': self.get_uptime_ms(),
                'motor_a_speed': speeds[0],
                'motor_b_speed': speeds[1],
                'latency_ms': 15
            })
        
        elif path == '/motor' and method == 'POST':
            # Control motors
            data = self.parse_json_body(request)
            speed_a = data.get('a', 0)
            speed_b = data.get('b', 0)
            
            self.rover.drive(speed_a, speed_b)
            
            self.send_response(client, 200, {
                'success': True,
                'motor_a': speed_a,
                'motor_b': speed_b
            })
        
        elif path == '/motor/stop' and method == 'POST':
            # Emergency stop
            self.rover.stop()
            self.send_response(client, 200, {
                'success': True,
                'message': 'All motors stopped'
            })
        
        elif path == '/api/scan' and method == 'GET':
            # Scan WiFi networks (from wifi_manager)
            try:
                from wifi_manager import WiFiManager
                wifi = WiFiManager()
                networks = wifi.scan_networks()
                self.send_response(client, 200, {'networks': networks})
            except:
                self.send_response(client, 200, {'networks': []})
        
        elif path == '/api/connect' and method == 'POST':
            # Connect to WiFi network
            data = self.parse_json_body(request)
            ssid = data.get('ssid')
            password = data.get('password')
            
            if not ssid:
                self.send_response(client, 400, {'error': 'Missing SSID'})
                return
            
            try:
                from wifi_manager import WiFiManager
                wifi = WiFiManager()
                result = wifi.connect_to_network(ssid, password)
                
                if result:
                    self.send_response(client, 200, {
                        'success': True,
                        'ssid': ssid,
                        'ip': result.get('ip')
                    })
                else:
                    self.send_response(client, 200, {
                        'success': False,
                        'error': 'Connection failed'
                    })
            except Exception as e:
                self.send_response(client, 500, {
                    'success': False,
                    'error': str(e)
                })
        
        else:
            # 404 Not Found
            self.send_response(client, 404, {
                'error': 'Endpoint not found',
                'path': path
            })
    
    def start(self):
        """Start API server"""
        self.running = True
        self.start_time = time.time()
        
        # Create socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', self.port))
        server_socket.listen(4)
        
        print(f"[APIServer] ✓ Server started on port {self.port}")
        print(f"[APIServer] Access at http://192.168.4.1:{self.port}/")
        
        try:
            while self.running:
                try:
                    client, addr = server_socket.accept()
                    
                    # Receive request
                    request_data = b''
                    while True:
                        chunk = client.recv(1024)
                        if not chunk:
                            break
                        request_data += chunk
                        if b'\r\n\r\n' in request_data:
                            break
                    
                    if request_data:
                        request_str = request_data.decode('utf-8', errors='ignore')
                        method, path = self.handle_request(request_str)
                        
                        if method and path:
                            self.route_request(client, method, path, request_str)
                    
                    client.close()
                
                except OSError as e:
                    # Connection error
                    print(f"[APIServer] Connection error: {e}")
                except Exception as e:
                    print(f"[APIServer] Error: {e}")
                
                # Garbage collection
                gc.collect()
        
        except KeyboardInterrupt:
            print("[APIServer] Shutting down...")
        finally:
            server_socket.close()
            self.running = False
    
    def stop(self):
        """Stop API server"""
        self.running = False
        print("[APIServer] Stopped")
