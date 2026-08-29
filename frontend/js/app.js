/**
 * Main Rover Control Application
 */
class RoverApp {
    constructor() {
        this.controlLoop = null;
        this.telemetryLoop = null;
        this.updateRate = 10;  // Hz
        this.telemetryRate = 1;  // Hz
        this.debugMode = false;
    }

    /**
     * Initialize the app
     */
    async init() {
        console.log('🚀 Rover Control App initializing...');

        // Setup event listeners
        this.setupEventListeners();

        // Load saved settings
        this.loadSettings();

        // Try to discover rover
        ui.updateConnection(false);
        const discoveredIP = await rover.discover();

        if (discoveredIP) {
            ui.updateConnection(true, discoveredIP);
            ui.notify('✅ Rover connected!', 'success');
            
            // Start control loops
            this.startControlLoop();
            this.startTelemetryLoop();

            // Initialize joystick if in joystick mode
            if (control.mode === 'joystick') {
                joystick.init();
            }
        } else {
            ui.notify('❌ Rover not found. Check WiFi connection.', 'error', 5000);
            // Retry in 5 seconds
            setTimeout(() => this.init(), 5000);
        }
    }

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // Mode buttons
        document.getElementById('gyro-mode-btn').addEventListener('click', () => {
            control.setMode('gyro');
            ui.switchMode('gyro');
        });

        document.getElementById('joystick-mode-btn').addEventListener('click', () => {
            control.setMode('joystick');
            ui.switchMode('joystick');
            joystick.init();
        });

        document.getElementById('keyboard-mode-btn').addEventListener('click', () => {
            control.setMode('keyboard');
            ui.switchMode('keyboard');
        });

        // Speed control
        document.getElementById('speed-slider').addEventListener('input', (e) => {
            const speed = parseInt(e.target.value);
            control.setMaxSpeed(speed);
            ui.updateSpeedDisplay(speed);
            localStorage.setItem('maxSpeed', speed);
        });

        // Speed presets
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const speed = parseInt(btn.dataset.speed);
                control.setMaxSpeed(speed);
                document.getElementById('speed-slider').value = speed;
                ui.updateSpeedDisplay(speed);
                
                document.querySelectorAll('.preset-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                localStorage.setItem('maxSpeed', speed);
            });
        });

        // D-Pad buttons
        document.querySelectorAll('.dpad-btn').forEach(btn => {
            btn.addEventListener('touchstart', (e) => {
                e.preventDefault();
                const direction = btn.dataset.direction;
                this.handleDPadPress(direction);
            });

            btn.addEventListener('touchend', (e) => {
                e.preventDefault();
                control.stop();
            });

            btn.addEventListener('mousedown', () => {
                const direction = btn.dataset.direction;
                this.handleDPadPress(direction);
            });

            btn.addEventListener('mouseup', () => {
                control.stop();
            });
        });

        // Gyro permission button
        document.getElementById('gyro-permission-btn').addEventListener('click', async () => {
            const result = await gyro.requestPermission();
            if (result) {
                ui.notify('✅ Gyroscope enabled', 'success');
            } else {
                ui.notify('❌ Gyroscope permission denied', 'error');
            }
        });

        // Emergency stop button
        document.getElementById('stop-btn').addEventListener('click', async () => {
            control.stop();
            await rover.stop();
            ui.notify('🛑 Emergency stop!', 'error');
        });

        // Reconnect button
        document.getElementById('reconnect-btn').addEventListener('click', async () => {
            const result = await rover.reconnect();
            if (result) {
                ui.updateConnection(true, result);
                ui.notify('✅ Reconnected!', 'success');
            } else {
                ui.notify('❌ Reconnection failed', 'error');
            }
        });

        // Settings modal
        document.getElementById('settings-btn').addEventListener('click', () => {
            ui.showSettings(true);
        });

        document.getElementById('settings-close').addEventListener('click', () => {
            ui.showSettings(false);
        });

        document.getElementById('settings-cancel').addEventListener('click', () => {
            ui.showSettings(false);
        });

        document.getElementById('settings-save').addEventListener('click', () => {
            const ip = document.getElementById('rover-ip-input').value;
            const port = document.getElementById('rover-port-input').value;
            const updateRate = document.getElementById('update-rate-input').value;

            rover.baseURL = `http://${ip}:${port}`;
            rover.saveConfig();
            this.updateRate = parseInt(updateRate);

            ui.notify('✅ Settings saved', 'success');
            ui.showSettings(false);
        });

        // Keyboard controls
        document.addEventListener('keydown', (e) => {
            if (control.mode === 'keyboard') {
                control.onKeyDown(e.key);
            }
        });

        document.addEventListener('keyup', (e) => {
            if (control.mode === 'keyboard') {
                control.onKeyUp(e.key);
            }
        });

        // Debug toggle (Ctrl+D)
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'd') {
                this.debugMode = !this.debugMode;
                console.log(`Debug mode: ${this.debugMode}`);
            }
        });
    }

    /**
     * Handle D-pad button press
     */
    handleDPadPress(direction) {
        const speed = control.maxSpeed;
        
        switch (direction) {
            case 'up':
                control.lastSpeedA = speed;
                control.lastSpeedB = speed;
                break;
            case 'down':
                control.lastSpeedA = -speed;
                control.lastSpeedB = -speed;
                break;
            case 'left':
                control.lastSpeedA = -speed * 0.5;
                control.lastSpeedB = speed * 0.5;
                break;
            case 'right':
                control.lastSpeedA = speed * 0.5;
                control.lastSpeedB = -speed * 0.5;
                break;
            case 'stop':
                control.lastSpeedA = 0;
                control.lastSpeedB = 0;
                break;
        }
    }

    /**
     * Start main control loop
     */
    startControlLoop() {
        const interval = 1000 / this.updateRate;

        this.controlLoop = setInterval(async () => {
            if (!rover.connected) return;

            // Get motor speeds from control system
            const speeds = control.getMotorSpeeds();

            // Send to rover
            const result = await rover.sendMotor(speeds.a, speeds.b);

            if (result) {
                // Update display
                ui.updateMotorDisplay(speeds.a, speeds.b);
                ui.updateLatency(rover.latency);

                if (this.debugMode) {
                    console.log(`Motor: A=${Math.round(speeds.a)}%, B=${Math.round(speeds.b)}%`);
                }
            } else {
                rover.connected = false;
                ui.updateConnection(false);
            }
        }, interval);

        console.log(`✅ Control loop started (${this.updateRate}Hz)`);
    }

    /**
     * Start telemetry loop
     */
    startTelemetryLoop() {
        this.telemetryLoop = setInterval(async () => {
            if (!rover.connected) return;

            const status = await rover.getStatus();
            if (status) {
                ui.updateTelemetry(status);
                
                if (this.debugMode) {
                    console.log('Telemetry:', status);
                }
            }
        }, 1000 / this.telemetryRate);

        console.log(`✅ Telemetry loop started (${this.telemetryRate}Hz)`);
    }

    /**
     * Stop all loops
     */
    stop() {
        if (this.controlLoop) clearInterval(this.controlLoop);
        if (this.telemetryLoop) clearInterval(this.telemetryLoop);
        rover.stop();
        console.log('⏹️ Loops stopped');
    }

    /**
     * Save settings to localStorage
     */
    saveSettings() {
        const settings = {
            maxSpeed: control.maxSpeed,
            controlMode: control.mode,
            roverIP: rover.baseURL,
            debugMode: this.debugMode
        };
        localStorage.setItem('roverSettings', JSON.stringify(settings));
    }

    /**
     * Load settings from localStorage
     */
    loadSettings() {
        const stored = localStorage.getItem('roverSettings');
        if (stored) {
            const settings = JSON.parse(stored);
            control.setMaxSpeed(settings.maxSpeed || 60);
            control.setMode(settings.controlMode || 'gyro');
            this.debugMode = settings.debugMode || false;
            
            document.getElementById('speed-slider').value = settings.maxSpeed || 60;
            ui.updateSpeedDisplay(settings.maxSpeed || 60);
        }
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new RoverApp();
    window.app.init();

    // Save settings on page close
    window.addEventListener('beforeunload', () => {
        window.app.saveSettings();
    });
});

// Auto-reconnect if connection lost
setInterval(async () => {
    if (!rover.connected) {
        console.log('🔄 Connection lost. Attempting to reconnect...');
        const result = await rover.reconnect();
        if (result) {
            console.log('✅ Reconnected');
            ui.updateConnection(true, result);
            window.app.startControlLoop();
            window.app.startTelemetryLoop();
        }
    }
}, 5000);
