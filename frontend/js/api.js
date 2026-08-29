/**
 * RoverAPI - HTTP client for Pico W rover backend
 */
class RoverAPI {
    constructor(ip = '192.168.1.100', port = 8000) {
        this.baseURL = `http://${ip}:${port}`;
        this.connected = false;
        this.lastRequestTime = Date.now();
        this.latency = 0;
        
        // Try common rover IPs
        this.tryIPs = [
            '192.168.1.100',
            '192.168.0.100',
            '192.168.4.1',      // AP default
            'rover.local',
            'localhost:8000'
        ];
        
        // Load from localStorage
        this.loadConfig();
    }

    loadConfig() {
        const stored = localStorage.getItem('roverConfig');
        if (stored) {
            const config = JSON.parse(stored);
            this.baseURL = `http://${config.ip}:${config.port}`;
        }
    }

    saveConfig() {
        const parts = this.baseURL.split(':');
        const ip = parts[1].replace('//', '');
        const port = parts[2] || 8000;
        localStorage.setItem('roverConfig', JSON.stringify({ ip, port }));
    }

    /**
     * Discover rover on network
     */
    async discover() {
        console.log('🔍 Discovering rover...');
        
        for (const ip of this.tryIPs) {
            try {
                const url = ip.includes(':') ? `http://${ip}/status` : `http://${ip}:8000/status`;
                const startTime = Date.now();
                
                const response = await Promise.race([
                    fetch(url, { method: 'GET' }),
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('timeout')), 2000)
                    )
                ]);
                
                this.latency = Date.now() - startTime;
                
                if (response.ok) {
                    const parts = ip.split(':');
                    this.baseURL = ip.includes(':') ? `http://${ip}` : `http://${ip}:8000`;
                    this.connected = true;
                    console.log(`✅ Rover found at ${ip}`);
                    this.saveConfig();
                    return ip;
                }
            } catch (e) {
                // Continue to next IP
            }
        }
        
        this.connected = false;
        console.log('❌ Rover not found');
        return null;
    }

    /**
     * Send motor command to rover
     * @param {number} speedA -100 to 100
     * @param {number} speedB -100 to 100
     */
    async sendMotor(speedA, speedB) {
        if (!this.connected) return null;
        
        try {
            const startTime = Date.now();
            const response = await fetch(
                `${this.baseURL}/motor?a=${Math.round(speedA)}&b=${Math.round(speedB)}`,
                { method: 'POST' }
            );
            
            this.latency = Date.now() - startTime;
            
            if (response.ok) {
                return await response.json();
            } else {
                this.connected = false;
            }
        } catch (e) {
            this.connected = false;
            console.error('Motor command failed:', e);
        }
        return null;
    }

    /**
     * Get rover status
     */
    async getStatus() {
        if (!this.connected) return null;
        
        try {
            const startTime = Date.now();
            const response = await fetch(`${this.baseURL}/status`);
            
            this.latency = Date.now() - startTime;
            
            if (response.ok) {
                return await response.json();
            } else {
                this.connected = false;
            }
        } catch (e) {
            this.connected = false;
        }
        return null;
    }

    /**
     * Scan available WiFi networks
     */
    async scanNetworks() {
        if (!this.connected) return [];
        
        try {
            const response = await fetch(`${this.baseURL}/api/scan`);
            if (response.ok) {
                return await response.json();
            }
        } catch (e) {
            console.error('Scan failed:', e);
        }
        return [];
    }

    /**
     * Connect to WiFi network
     */
    async connectWiFi(ssid, password) {
        if (!this.connected) return false;
        
        try {
            const response = await fetch(`${this.baseURL}/api/connect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ssid, password })
            });
            
            if (response.ok) {
                const result = await response.json();
                return result.success;
            }
        } catch (e) {
            console.error('WiFi connect failed:', e);
        }
        return false;
    }

    /**
     * Emergency stop
     */
    async stop() {
        return this.sendMotor(0, 0);
    }

    /**
     * Reconnect to rover
     */
    async reconnect() {
        this.connected = false;
        return this.discover();
    }
}

// Global instance
const rover = new RoverAPI();
