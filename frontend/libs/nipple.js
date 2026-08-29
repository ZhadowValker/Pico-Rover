/**
 * nipple.js - Minimal virtual joystick library
 * Simplified implementation for rover control
 */
(function(window) {
    'use strict';

    class Joystick {
        constructor(options) {
            this.options = options || {};
            this.zone = this.options.zone;
            this.color = this.options.color || '#00adb5';
            this.size = this.options.size || 100;
            this.threshold = this.options.threshold || 0.1;
            this.fadeTime = this.options.fadeTime || 250;

            this.events = {};
            this.active = false;
            this.touch = null;

            this.createDOM();
            this.attachEvents();
        }

        createDOM() {
            // Create container
            this.container = document.createElement('div');
            this.container.style.cssText = `
                position: absolute;
                left: 50%;
                top: 50%;
                transform: translate(-50%, -50%);
                width: ${this.size * 2.5}px;
                height: ${this.size * 2.5}px;
                display: flex;
                align-items: center;
                justify-content: center;
            `;

            // Create outer circle
            this.outer = document.createElement('div');
            this.outer.style.cssText = `
                position: relative;
                width: ${this.size * 2}px;
                height: ${this.size * 2}px;
                border: 3px solid ${this.color};
                border-radius: 50%;
                background: rgba(0, 0, 0, 0.1);
                opacity: 0;
                transition: opacity ${this.fadeTime}ms;
            `;

            // Create inner stick
            this.inner = document.createElement('div');
            this.inner.style.cssText = `
                position: absolute;
                left: 50%;
                top: 50%;
                transform: translate(-50%, -50%);
                width: ${this.size * 0.6}px;
                height: ${this.size * 0.6}px;
                border-radius: 50%;
                background: ${this.color};
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
            `;

            this.outer.appendChild(this.inner);
            this.container.appendChild(this.outer);
            this.zone.style.position = 'relative';
            this.zone.appendChild(this.container);
        }

        attachEvents() {
            // Touch events
            this.zone.addEventListener('touchstart', (e) => this.onStart(e));
            this.zone.addEventListener('touchmove', (e) => this.onMove(e));
            this.zone.addEventListener('touchend', (e) => this.onEnd(e));

            // Mouse events
            this.zone.addEventListener('mousedown', (e) => this.onStart(e));
            document.addEventListener('mousemove', (e) => this.onMove(e));
            document.addEventListener('mouseup', (e) => this.onEnd(e));
        }

        onStart(e) {
            if (e.touches) {
                this.touch = e.touches[0];
            } else {
                this.touch = e;
            }
            
            this.active = true;
            this.outer.style.opacity = '1';
            this.trigger('start');
        }

        onMove(e) {
            if (!this.active || !this.touch) return;

            const current = e.touches ? e.touches[0] : e;
            const rect = this.zone.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;

            const dx = current.clientX - centerX;
            const dy = current.clientY - centerY;
            const distance = Math.sqrt(dx * dx + dy * dy) / this.size;
            const angle = Math.atan2(dy, dx) * (180 / Math.PI);

            // Clamp distance to 1.0
            const clampedDistance = Math.min(distance, 1.0);

            // Apply threshold
            if (clampedDistance < this.threshold) {
                this.inner.style.left = '50%';
                this.inner.style.top = '50%';
            } else {
                const x = Math.cos(angle * (Math.PI / 180)) * (clampedDistance * this.size) + this.size;
                const y = Math.sin(angle * (Math.PI / 180)) * (clampedDistance * this.size) + this.size;
                
                this.inner.style.left = x + 'px';
                this.inner.style.top = y + 'px';
            }

            this.trigger('move', {
                angle: { degree: (angle + 360) % 360 },
                distance: clampedDistance
            });
        }

        onEnd(e) {
            this.active = false;
            this.touch = null;
            this.outer.style.opacity = '0';
            this.inner.style.left = '50%';
            this.inner.style.top = '50%';
            this.trigger('end');
        }

        on(event, callback) {
            if (!this.events[event]) {
                this.events[event] = [];
            }
            this.events[event].push(callback);
        }

        trigger(event, data) {
            if (this.events[event]) {
                this.events[event].forEach(callback => {
                    callback({}, data);
                });
            }
        }

        destroy() {
            this.zone.removeChild(this.container);
        }
    }

    // nipplejs namespace
    window.nipplejs = {
        create: function(options) {
            return new Joystick(options);
        }
    };

})(window);
