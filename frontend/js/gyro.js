/**
 * GyroController - Device orientation sensor handling
 */
class GyroController {
    constructor() {
        this.alpha = 0;  // Z axis rotation (yaw)
        this.beta = 0;   // X axis rotation (pitch)
        this.gamma = 0;  // Y axis rotation (roll)
        this.enabled = false;
        this.supported = false;
        this.permissionRequested = false;
    }

    /**
     * Request permission (iOS 13+)
     */
    async requestPermission() {
        if (typeof DeviceOrientationEvent === 'undefined') {
            console.warn('DeviceOrientationEvent not supported');
            return false;
        }

        // iOS 13+
        if (typeof DeviceOrientationEvent.requestPermission === 'function') {
            try {
                const permission = await DeviceOrientationEvent.requestPermission();
                if (permission === 'granted') {
                    this.supported = true;
                    this.start();
                    return true;
                } else {
                    console.warn('Gyroscope permission denied');
                    return false;
                }
            } catch (e) {
                console.error('Permission request failed:', e);
                return false;
            }
        } else {
            // Android and older iOS - automatically supported
            this.supported = true;
            this.start();
            return true;
        }
    }

    /**
     * Start listening for device orientation
     */
    start() {
        if (this.enabled) return;

        window.addEventListener('deviceorientation', (event) => {
            this.alpha = event.alpha || 0;
            this.beta = event.beta || 0;
            this.gamma = event.gamma || 0;
        });

        this.enabled = true;
        console.log('✅ Gyroscope enabled');
    }

    /**
     * Stop listening
     */
    stop() {
        window.removeEventListener('deviceorientation', null);
        this.enabled = false;
    }

    /**
     * Get motor speeds based on gyro orientation
     * Pitch (beta): forward/backward
     * Roll (gamma): left/right turn
     */
    getMotorSpeeds(maxSpeed = 100) {
        if (!this.enabled) {
            return { a: 0, b: 0 };
        }

        // Normalize angles
        let pitch = this.beta;    // Forward/back (-90 to 90)
        let roll = this.gamma;    // Left/right (-90 to 90)

        // Map pitch to forward speed
        const forward = (pitch / 90) * maxSpeed;

        // Map roll to differential steering
        const turn = (roll / 90) * maxSpeed * 0.5;

        // Differential steering formula:
        // Motor A (left) = forward - turn
        // Motor B (right) = forward + turn
        const motorA = forward - turn;
        const motorB = forward + turn;

        // Clamp values
        return {
            a: Math.max(-100, Math.min(100, motorA)),
            b: Math.max(-100, Math.min(100, motorB))
        };
    }

    /**
     * Draw gyro compass visualization
     */
    drawCompass(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;
        const centerX = w / 2;
        const centerY = h / 2;
        const radius = 80;

        // Clear canvas
        ctx.fillStyle = '#333';
        ctx.fillRect(0, 0, w, h);

        // Draw background circle
        ctx.strokeStyle = '#00adb5';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.stroke();

        // Draw grid
        ctx.strokeStyle = '#404040';
        ctx.lineWidth = 1;
        for (let i = 1; i < 4; i++) {
            const r = (radius / 3) * i;
            ctx.beginPath();
            ctx.arc(centerX, centerY, r, 0, Math.PI * 2);
            ctx.stroke();
        }

        // Draw pitch indicator (forward/back)
        const pitchAngle = (this.beta / 90) * Math.PI;
        const pitchX = centerX + Math.sin(pitchAngle) * radius * 0.7;
        const pitchY = centerY - Math.cos(pitchAngle) * radius * 0.7;

        ctx.strokeStyle = '#4caf50';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(pitchX, pitchY);
        ctx.stroke();

        // Draw roll indicator (left/right)
        ctx.save();
        ctx.translate(centerX, centerY);
        const rollAngle = (this.gamma / 90) * (Math.PI / 2);
        ctx.rotate(rollAngle);
        
        ctx.fillStyle = '#ff9800';
        ctx.fillRect(-3, -radius * 0.6, 6, radius * 1.2);
        ctx.restore();

        // Draw center dot
        ctx.fillStyle = '#00adb5';
        ctx.beginPath();
        ctx.arc(centerX, centerY, 6, 0, Math.PI * 2);
        ctx.fill();

        // Draw labels
        ctx.fillStyle = '#b0b0b0';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('Forward', centerX, centerY - radius - 10);
        ctx.fillText('Back', centerX, centerY + radius + 15);
        ctx.textAlign = 'right';
        ctx.fillText('Left', centerX - radius - 10, centerY + 4);
        ctx.textAlign = 'left';
        ctx.fillText('Right', centerX + radius + 10, centerY + 4);
    }

    /**
     * Calibrate gyro (set current position as zero)
     */
    calibrate() {
        this.alpha = 0;
        this.beta = 0;
        this.gamma = 0;
        console.log('✅ Gyro calibrated');
    }
}

// Global instance
const gyro = new GyroController();
