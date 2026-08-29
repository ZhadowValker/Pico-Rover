/**
 * ControlSystem - Maps sensor inputs to motor speeds
 */
class ControlSystem {
    constructor() {
        this.mode = 'gyro';  // gyro, joystick, keyboard
        this.maxSpeed = 60;  // 0-100%
        this.lastSpeedA = 0;
        this.lastSpeedB = 0;
        this.keyPressed = new Set();
    }

    /**
     * Set control mode
     */
    setMode(mode) {
        this.mode = mode;
        console.log(`🎮 Control mode: ${mode}`);
    }

    /**
     * Set max speed limit
     */
    setMaxSpeed(speed) {
        this.maxSpeed = Math.max(10, Math.min(100, speed));
    }

    /**
     * Get motor speeds based on current control mode
     */
    getMotorSpeeds() {
        let speedA = 0;
        let speedB = 0;

        switch (this.mode) {
            case 'gyro':
                if (gyro.enabled) {
                    const speeds = gyro.getMotorSpeeds(this.maxSpeed);
                    speedA = speeds.a;
                    speedB = speeds.b;
                }
                break;

            case 'joystick':
                if (joystick.enabled) {
                    const speeds = joystick.getSpeeds();
                    speedA = speeds.a * (this.maxSpeed / 100);
                    speedB = speeds.b * (this.maxSpeed / 100);
                }
                break;

            case 'keyboard':
                const speeds = this.getKeyboardSpeeds();
                speedA = speeds.a * (this.maxSpeed / 100);
                speedB = speeds.b * (this.maxSpeed / 100);
                break;
        }

        this.lastSpeedA = speedA;
        this.lastSpeedB = speedB;

        return { a: speedA, b: speedB };
    }

    /**
     * Handle keyboard input
     */
    getKeyboardSpeeds() {
        let forward = 0;
        let turn = 0;

        if (this.keyPressed.has('ArrowUp') || this.keyPressed.has('w')) forward = 100;
        if (this.keyPressed.has('ArrowDown') || this.keyPressed.has('s')) forward = -100;
        if (this.keyPressed.has('ArrowLeft') || this.keyPressed.has('a')) turn = -50;
        if (this.keyPressed.has('ArrowRight') || this.keyPressed.has('d')) turn = 50;

        const motorA = forward - turn;
        const motorB = forward + turn;

        return {
            a: Math.max(-100, Math.min(100, motorA)),
            b: Math.max(-100, Math.min(100, motorB))
        };
    }

    /**
     * Register keyboard key down
     */
    onKeyDown(key) {
        this.keyPressed.add(key.toLowerCase());
        
        // Handle special commands
        if (key === ' ') {
            this.keyPressed.clear();  // Space = stop
        }
    }

    /**
     * Register keyboard key up
     */
    onKeyUp(key) {
        this.keyPressed.delete(key.toLowerCase());
    }

    /**
     * Stop all motors
     */
    stop() {
        this.keyPressed.clear();
        return { a: 0, b: 0 };
    }
}

// Global instance
const control = new ControlSystem();
