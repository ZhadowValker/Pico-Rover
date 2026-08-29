/**
 * UI Helper functions
 */
const ui = {
    /**
     * Update connection status
     */
    updateConnection(connected, ip = null) {
        const badge = document.getElementById('connection');
        const statusText = document.getElementById('status-text');
        
        if (connected) {
            badge.textContent = '🟢 Connected';
            badge.classList.remove('disconnected');
            badge.classList.add('connected');
            statusText.textContent = 'Connected to rover';
        } else {
            badge.textContent = '🔴 Offline';
            badge.classList.remove('connected');
            badge.classList.add('disconnected');
            statusText.textContent = 'Searching for rover...';
        }
        
        if (ip) {
            document.getElementById('rover-ip').textContent = ip;
        }
    },

    /**
     * Update gyro display values
     */
    updateGyroDisplay(roll, pitch, yaw = 0) {
        document.getElementById('roll-value').textContent = Math.round(roll) + '°';
        document.getElementById('pitch-value').textContent = Math.round(pitch) + '°';
        document.getElementById('yaw-value').textContent = Math.round(yaw) + '°';
    },

    /**
     * Update motor display bars
     */
    updateMotorDisplay(speedA, speedB) {
        // Motor A
        const motorABar = document.getElementById('motor-a-bar');
        const motorAValue = document.getElementById('motor-a-value');
        const absA = Math.abs(speedA);
        motorABar.style.width = absA + '%';
        motorABar.parentElement.style.opacity = speedA === 0 ? '0.5' : '1';
        motorAValue.textContent = Math.round(speedA) + '%';

        // Motor B
        const motorBBar = document.getElementById('motor-b-bar');
        const motorBValue = document.getElementById('motor-b-value');
        const absB = Math.abs(speedB);
        motorBBar.style.width = absB + '%';
        motorBBar.parentElement.style.opacity = speedB === 0 ? '0.5' : '1';
        motorBValue.textContent = Math.round(speedB) + '%';
    },

    /**
     * Update telemetry data
     */
    updateTelemetry(status) {
        if (!status) return;

        if (status.battery !== undefined) {
            const voltage = status.battery.toFixed(2);
            document.getElementById('battery-voltage').textContent = voltage + ' V';
            
            // Calculate percentage (assuming 4.2V = 100%, 3.0V = 0%)
            const percent = Math.round((status.battery - 3.0) / (4.2 - 3.0) * 100);
            document.getElementById('battery-percent').textContent = Math.max(0, percent) + '%';
            
            // Update header battery badge
            const batteryBadge = document.getElementById('battery');
            const emoji = percent > 66 ? '🟢' : percent > 33 ? '🟡' : '🔴';
            batteryBadge.textContent = emoji + ' ' + percent + '%';
        }

        if (status.uptime !== undefined) {
            document.getElementById('uptime').textContent = this.formatUptime(status.uptime);
        }
    },

    /**
     * Update latency display
     */
    updateLatency(latency) {
        document.getElementById('latency').textContent = latency + ' ms';
    },

    /**
     * Update speed display
     */
    updateSpeedDisplay(speed) {
        document.getElementById('speed-display').textContent = speed + '%';
    },

    /**
     * Update signal strength
     */
    updateSignal(strength) {
        const signals = ['🔴', '🟠', '🟡', '🟢', '🟢'];
        const emoji = signals[Math.min(4, Math.max(0, strength))];
        document.getElementById('signal-strength').textContent = emoji + ' ' + strength;
    },

    /**
     * Switch control mode (gyro, joystick, keyboard)
     */
    switchMode(mode) {
        // Hide all sections
        document.getElementById('gyro-section').style.display = 'none';
        document.getElementById('joystick-section').style.display = 'none';
        document.getElementById('keyboard-section').style.display = 'none';

        // Update buttons
        document.getElementById('gyro-mode-btn').classList.remove('active');
        document.getElementById('joystick-mode-btn').classList.remove('active');
        document.getElementById('keyboard-mode-btn').classList.remove('active');

        // Show selected mode
        switch (mode) {
            case 'gyro':
                document.getElementById('gyro-section').style.display = 'block';
                document.getElementById('gyro-mode-btn').classList.add('active');
                break;
            case 'joystick':
                document.getElementById('joystick-section').style.display = 'block';
                document.getElementById('joystick-mode-btn').classList.add('active');
                break;
            case 'keyboard':
                document.getElementById('keyboard-section').style.display = 'block';
                document.getElementById('keyboard-mode-btn').classList.add('active');
                break;
        }
    },

    /**
     * Show/hide settings modal
     */
    showSettings(show = true) {
        const modal = document.getElementById('settings-modal');
        if (show) {
            modal.style.display = 'flex';
            // Load current settings
            document.getElementById('rover-ip-input').value = 
                rover.baseURL.split('//')[1].split(':')[0];
            document.getElementById('rover-port-input').value = 
                rover.baseURL.split(':')[2] || '8000';
        } else {
            modal.style.display = 'none';
        }
    },

    /**
     * Show notification/toast message
     */
    notify(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 16px;
            background: ${type === 'error' ? '#d32f2f' : type === 'success' ? '#4caf50' : '#2196f3'};
            color: white;
            border-radius: 4px;
            font-size: 14px;
            z-index: 9999;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        `;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, duration);
    },

    /**
     * Format uptime in human readable format
     */
    formatUptime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}h ${minutes}m`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }
};
