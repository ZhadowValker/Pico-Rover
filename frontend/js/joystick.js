/**
 * JoystickController - Virtual joystick using nipple.js
 */
class JoystickController {
    constructor() {
        this.manager = null;
        this.speedA = 0;
        this.speedB = 0;
        this.enabled = false;
    }

    /**
     * Initialize joystick in container
     */
    init() {
        const container = document.getElementById('joystick-container');
        if (!container) {
            console.warn('Joystick container not found');
            return false;
        }

        try {
            // Load nipple.js if not already loaded
            if (typeof nipplejs === 'undefined') {
                console.error('nipple.js not loaded');
                return false;
            }

            this.manager = nipplejs.create({
                zone: container,
                mode: 'static',
                position: { left: '50%', top: '50%' },
                color: '#00adb5',
                size: 150,
                threshold: 0.1,
                fadeTime: 250
            });

            // Handle joystick movement
            this.manager.on('move', (evt, data) => {
                this.updateFromJoystick(data);
            });

            // Handle joystick release
            this.manager.on('end', () => {
                this.speedA = 0;
                this.speedB = 0;
            });

            this.enabled = true;
            console.log('✅ Joystick initialized');
            return true;
        } catch (e) {
            console.error('Joystick init failed:', e);
            return false;
        }
    }

    /**
     * Update speeds from joystick position
     */
    updateFromJoystick(data) {
        if (!data) return;

        // data.angle.degree: 0-360 (0=up, 90=right, 180=down, 270=left)
        // data.distance: 0-1 (normalized)
        
        const angle = data.angle.degree;
        const distance = Math.min(data.distance, 1);

        // Convert to radians
        const radians = (angle * Math.PI) / 180;

        // Forward/backward component (Y axis)
        const forward = -Math.cos(radians) * distance * 100;

        // Left/right component (X axis) for differential steering
        const turn = Math.sin(radians) * distance * 100 * 0.5;

        // Differential steering:
        this.speedA = Math.round(forward - turn);
        this.speedB = Math.round(forward + turn);

        // Clamp
        this.speedA = Math.max(-100, Math.min(100, this.speedA));
        this.speedB = Math.max(-100, Math.min(100, this.speedB));
    }

    /**
     * Get current motor speeds
     */
    getSpeeds() {
        return {
            a: this.speedA,
            b: this.speedB
        };
    }

    /**
     * Destroy joystick
     */
    destroy() {
        if (this.manager) {
            this.manager.destroy();
            this.manager = null;
            this.enabled = false;
        }
    }
}

// Global instance
const joystick = new JoystickController();
