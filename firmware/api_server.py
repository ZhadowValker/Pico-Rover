"""
Pico Rover REST API Server with Static File Serving
Serves HTML interface + REST API endpoints
"""

import socket
import json
import time
import gc
import os
import select
from machine import ADC, Pin

try:
    import ssl
except ImportError:
    ssl = None

FAILSAFE_MS = 2000  # stop motors if no drive command for this long
MAX_PLAIN_CLIENTS = 6   # open plain-HTTP connections watched at once
PLAIN_IDLE_MS = 10000   # close a spare connection the browser never used

CERT_FILE = '/cert.der'
KEY_FILE = '/key.der'


def _write_all(client, data):
    """Write all bytes to a plain or TLS socket."""
    if hasattr(client, 'sendall'):
        client.sendall(data)
        return
    mv = memoryview(data)
    sent = 0
    while sent < len(data):
        n = client.write(mv[sent:])
        if n is None:
            continue
        sent += n


def _read_some(client, n):
    """Read up to n bytes from a plain or TLS socket."""
    if hasattr(client, 'recv'):
        return client.recv(n)
    return client.read(n)


class APIServer:
    def __init__(self, rover, port=8000, use_tls=False, http_port=None):
        """
        Initialize API server
        
        Args:
            rover: Rover instance (from motor_control.py)
            port: Server port (default 8000)
        """
        self.rover = rover
        self.port = port
        self.use_tls = use_tls
        self.http_port = http_port
        self.ctx = None
        self.conn_header = 'close'
        self.moving = False
        self.last_cmd_ms = 0
        self.close_reason = 'unknown'
        self.poll = None
        # timing stats, printed every 5 s while commands flow
        self.st_n = 0; self.st_sum = 0; self.st_max = 0
        self.st_cmds = 0; self.st_gap_max = 0; self.st_last_cmd = 0
        self.st_t0 = time.ticks_ms()
        self.st_conn_sum = 0; self.st_conn_max = 0; self.st_conns = 0
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
            f"Connection: {self.conn_header}\r\n"
            f"\r\n"
        )
        
        try:
            head = response.encode()
            if len(body) <= 1400:
                # Header + body in ONE write: two small writes trigger the TCP
                # Nagle / delayed-ACK stall (tens to hundreds of ms per reply).
                _write_all(client, head + body)
            else:
                _write_all(client, head)
                mv = memoryview(body)
                for i in range(0, len(body), 1024):
                    _write_all(client, mv[i:i+1024])
        except Exception as e:
            print(f"[APIServer] Error sending response: {e}")

    def send_file(self, client, path, content_type):
        """Stream a file from flash without loading it all into RAM."""
        try:
            size = os.stat(path)[6]
        except OSError:
            self.send_response(client, 404, {'error': 'not found', 'path': path})
            return
        header = (
            f"HTTP/1.1 200 OK\r\n"
            f"Content-Type: {content_type}; charset=utf-8\r\n"
            f"Content-Length: {size}\r\n"
            f"Cache-Control: no-store\r\n"
            f"Connection: {self.conn_header}\r\n"
            f"\r\n"
        )
        try:
            _write_all(client, header.encode())
            with open(path, 'rb') as f:
                buf = bytearray(1024)
                while True:
                    n = f.readinto(buf)
                    if not n:
                        break
                    _write_all(client, memoryview(buf)[:n])
        except Exception as e:
            print(f"[APIServer] Error streaming file: {e}")
    
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
        if path == '/' or path == '/index.html':
            self.send_file(client, '/index.html', 'text/html')
        
        elif path == '/status' and method == 'GET':
            # Get rover status
            speeds = self.rover.get_speeds()
            self.send_response(client, 200, {
                'battery_voltage': self.get_battery_voltage(),
                'uptime_ms': self.get_uptime_ms(),
                'motor_a_speed': speeds['a'],
                'motor_b_speed': speeds['b'],
                'latency_ms': 15
            })
        
        elif path == '/motor' and method == 'POST':
            # Control motors
            data = self.parse_json_body(request)
            speed_a = data.get('a', 0)
            speed_b = data.get('b', 0)
            
            self.rover.drive(int(speed_a), int(speed_b))
            now = time.ticks_ms()
            if self.st_last_cmd:
                g = time.ticks_diff(now, self.st_last_cmd)
                if g < 2000 and g > self.st_gap_max:
                    self.st_gap_max = g
            self.st_last_cmd = now
            self.st_cmds += 1
            self.last_cmd_ms = now
            self.moving = bool(speed_a or speed_b)

            self.send_response(client, 200, {
                'success': True,
                'motor_a': speed_a,
                'motor_b': speed_b
            })
        
        elif path == '/motor/stop' and method == 'POST':
            # Emergency stop
            self.rover.stop()
            self.moving = False
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
    
    def report_stats(self):
        now = time.ticks_ms()
        span = time.ticks_diff(now, self.st_t0)
        if span < 5000:
            return
        if self.st_n:
            print("[stats] %ds: %d req (%.1f/s), handle avg %d max %d ms | req->reply avg %d max %d ms | motor cmds %.1f/s, max gap %d ms | free %d" % (
                span // 1000, self.st_n, self.st_n * 1000 / span, self.st_sum // self.st_n, self.st_max,
                self.st_conn_sum // max(1, self.st_conns), self.st_conn_max,
                self.st_cmds * 1000 / span, self.st_gap_max, gc.mem_free()))
        self.st_n = self.st_sum = self.st_max = self.st_cmds = self.st_gap_max = 0
        self.st_conns = self.st_conn_sum = self.st_conn_max = 0
        self.st_t0 = now

    def failsafe_check(self):
        """Stop the motors if the phone stopped sending drive commands."""
        self.report_stats()
        if self.moving and time.ticks_diff(time.ticks_ms(), self.last_cmd_ms) > FAILSAFE_MS:
            self.rover.stop()
            self.moving = False
            print("[APIServer] Failsafe: no command, motors stopped")

    def read_request(self, client, max_wait_ms=2000, yield_ms=8000):
        """Read one full HTTP request (headers + body). b'' if none arrives.

        The socket has a short timeout, so this loop wakes up often and can
        run the failsafe while waiting for the next request.
        """
        data = b''
        start = time.ticks_ms()
        while True:
            try:
                chunk = _read_some(client, 1024)
            except OSError:
                chunk = None  # read timeout
            if chunk is None:
                self.failsafe_check()
                idle = time.ticks_diff(time.ticks_ms(), start)
                if idle > max_wait_ms:
                    self.close_reason = 'idle-timeout'
                    return b''
                # Someone else is waiting to connect and this connection has been
                # quiet for a long while: hand over instead of blocking them.
                # (Long, so a phone that is merely between commands keeps its
                # connection; the page pings every few seconds to stay alive.)
                if not data and idle > yield_ms and self.poll is not None and self.poll.poll(0):
                    self.close_reason = 'yield-to-new-connection'
                    return b''
                continue
            if not chunk:
                self.close_reason = 'peer-closed'
                return b''  # peer closed
            data += chunk
            if b'\r\n\r\n' in data:
                head, _, body = data.partition(b'\r\n\r\n')
                clen = 0
                for line in head.split(b'\r\n'):
                    if line.lower().startswith(b'content-length:'):
                        clen = int(line.split(b':', 1)[1].strip())
                while len(body) < clen:
                    try:
                        more = _read_some(client, clen - len(body))
                    except OSError:
                        more = None
                    if more is None:
                        if time.ticks_diff(time.ticks_ms(), start) > max_wait_ms:
                            break
                        continue
                    if not more:
                        break
                    body += more
                return head + b'\r\n\r\n' + body

    def _listen(self, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', port))
        s.listen(4)
        return s

    def serve_client(self, client, use_tls):
        """Serve one connection (possibly many keep-alive requests), then close it."""
        t_conn = time.ticks_ms()
        n_req = 0
        self.close_reason = 'unknown'
        raw = client  # TLS wrapper has no settimeout(); use the raw socket
        try:
            raw.settimeout(5)  # generous while a TLS handshake runs
            if use_tls:
                gc.collect()
                client = self.ctx.wrap_socket(client, server_side=True)
            tag = 'https' if use_tls else 'http'
            if use_tls:
                print("[conn] %s open, handshake %d ms" % (tag, time.ticks_diff(time.ticks_ms(), t_conn)))

            while True:
                # Short reads so the failsafe can run while we wait.
                raw.settimeout(0.3)
                # First request: short wait (a browser that connects and never
                # sends would block us). After that keep the connection open
                # longer so the phone reuses it.
                if use_tls:
                    # Hand over to a waiting connection only after 6 s of silence: longer than
                    # the page's 4 s keep-alive ping, so a page in use keeps its one connection
                    # (every new HTTPS connection costs the Pico a 1-3 s handshake).
                    request_data = self.read_request(client, 3000 if n_req == 0 else 15000, 6000)
                else:
                    # Plain HTTP: a request arrives within milliseconds of connecting, so
                    # don't let a silent (speculative) connection block real ones.
                    request_data = self.read_request(client, 1500, 300)
                if not request_data:
                    break
                n_req += 1
                request_str = request_data.decode()
                method, path = self.handle_request(request_str)
                low = request_str[:600].lower()
                # Plain HTTP: one request per connection (connecting is nearly free, and
                # it stops one idle connection from starving the next command).
                # HTTPS: keep-alive, because each new handshake costs 1-3 s on the Pico.
                if (not use_tls) or 'connection: close' in low:
                    self.conn_header = 'close'
                else:
                    self.conn_header = 'keep-alive'
                if method and path:
                    # Sending needs a generous timeout (the 0.3 s read timeout
                    # would cut a slow transfer off halfway).
                    raw.settimeout(5)
                    t_req = time.ticks_ms()
                    self.route_request(client, method, path, request_str)
                    d = time.ticks_diff(time.ticks_ms(), t_req)
                    self.st_n += 1; self.st_sum += d
                    if d > self.st_max: self.st_max = d
                if self.conn_header == 'close':
                    self.close_reason = 'client-asked-close'
                    break

            if use_tls: print("[conn] closed (%s) after %d requests, open %d ms" % (
                self.close_reason, n_req, time.ticks_diff(time.ticks_ms(), t_conn)))
        except OSError as e:
            # Connection error / idle timeout / failed TLS handshake
            print("[APIServer] Connection error: %s" % e)
        except Exception as e:
            print("[APIServer] Error: %s" % e)
        try:
            client.close()
        except Exception:
            pass
        d = time.ticks_diff(time.ticks_ms(), t_conn)
        self.st_conns += 1; self.st_conn_sum += d
        if d > self.st_conn_max: self.st_conn_max = d

    # ---------- plain HTTP: many connections watched at once ----------
    # Phone browsers open spare connections early and use them later. Serving
    # one connection at a time meant waiting on a silent spare while the real
    # command sat behind it. Instead, every open plain connection is watched
    # with poll(), and whichever one actually sends a request is answered.

    def _plain_close(self, c):
        try:
            self.poll.unregister(c)
        except Exception:
            pass
        try:
            c.close()
        except Exception:
            pass
        self.clients.pop(c, None)

    def _plain_readable(self, c):
        st = self.clients.get(c)
        if st is None:
            self._plain_close(c)
            return
        try:
            chunk = c.recv(1024)
        except OSError:
            return  # nothing there yet
        if not chunk:
            self._plain_close(c)  # browser closed its spare connection
            return
        st[1] += chunk
        data = st[1]
        if b'\r\n\r\n' not in data:
            if len(data) > 4096:
                self._plain_close(c)
            return
        head, _, body = data.partition(b'\r\n\r\n')
        clen = 0
        for line in head.split(b'\r\n'):
            if line.lower().startswith(b'content-length:'):
                try:
                    clen = int(line.split(b':', 1)[1].strip())
                except ValueError:
                    clen = 0
        if len(body) < clen:
            return  # body still on its way
        # Complete request: answer it, then close (one request per connection).
        try:
            c.settimeout(2)  # blocking send, but never stuck for long
            request_str = data.decode()
            method, path = self.handle_request(request_str)
            self.conn_header = 'close'
            if method and path:
                t_req = time.ticks_ms()
                self.route_request(c, method, path, request_str)
                d = time.ticks_diff(time.ticks_ms(), t_req)
                self.st_n += 1
                self.st_sum += d
                if d > self.st_max:
                    self.st_max = d
        except Exception as e:
            print("[APIServer] Error: %s" % e)
        d = time.ticks_diff(time.ticks_ms(), st[2])  # first byte -> reply sent
        self.st_conns += 1
        self.st_conn_sum += d
        if d > self.st_conn_max:
            self.st_conn_max = d
        self._plain_close(c)

    def _plain_accept(self, sock):
        try:
            c, addr = sock.accept()
        except OSError:
            return
        # Keep the number of open spares bounded (lwIP has few sockets).
        if len(self.clients) >= MAX_PLAIN_CLIENTS:
            oldest = None
            for k in self.clients:
                if oldest is None or time.ticks_diff(self.clients[oldest][0], self.clients[k][0]) > 0:
                    oldest = k
            self._plain_close(oldest)
        c.setblocking(False)
        now = time.ticks_ms()
        self.clients[c] = [now, b'', now]
        self.poll.register(c, select.POLLIN)

    def start(self):
        """Start API server: HTTPS on `port` (for gyro) and plain HTTP on `http_port`."""
        self.running = True
        self.start_time = time.time()
        self.clients = {}

        tls_sock = None
        plain_sock = None
        if self.use_tls:
            if ssl is None:
                raise RuntimeError("ssl module not available in this firmware")
            with open(CERT_FILE, 'rb') as f:
                cert = f.read()
            with open(KEY_FILE, 'rb') as f:
                key = f.read()
            self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            self.ctx.load_cert_chain(cert, key)
            gc.collect()
            tls_sock = self._listen(self.port)
            print("[APIServer] ✓ HTTPS on port %d  -> https://192.168.4.1/" % self.port)
            if self.http_port:
                plain_sock = self._listen(self.http_port)
                print("[APIServer] ✓ HTTP  on port %d  -> http://192.168.4.1/" % self.http_port)
        else:
            plain_sock = self._listen(self.port)
            print("[APIServer] ✓ HTTP on port %d" % self.port)

        self.poll = select.poll()
        for s in (tls_sock, plain_sock):
            if s is not None:
                self.poll.register(s, select.POLLIN)

        try:
            while self.running:
                for item in self.poll.poll(50):
                    obj, ev = item[0], item[1]
                    if obj is plain_sock:
                        self._plain_accept(plain_sock)
                    elif obj is tls_sock:
                        try:
                            client, addr = tls_sock.accept()
                        except OSError:
                            continue
                        self.serve_client(client, True)  # HTTPS: one at a time (gyro page)
                    elif obj in self.clients:
                        if ev & (select.POLLHUP | select.POLLERR):
                            self._plain_close(obj)
                        else:
                            if not self.clients[obj][1]:
                                self.clients[obj][2] = time.ticks_ms()  # first byte time
                            self._plain_readable(obj)
                    else:
                        try:
                            self.poll.unregister(obj)
                        except Exception:
                            pass

                # Drop spare connections the browser never used.
                now = time.ticks_ms()
                for c in list(self.clients):
                    if time.ticks_diff(now, self.clients[c][0]) > PLAIN_IDLE_MS:
                        self._plain_close(c)

                self.failsafe_check()  # also prints the 5 s stats
                if gc.mem_free() < 60000:
                    gc.collect()
        except KeyboardInterrupt:
            print("[APIServer] Shutting down...")
        finally:
            for c in list(self.clients):
                self._plain_close(c)
            for s in (tls_sock, plain_sock):
                if s is not None:
                    s.close()
            self.running = False

    def stop(self):
        """Stop API server"""
        self.running = False
        print("[APIServer] Stopped")
