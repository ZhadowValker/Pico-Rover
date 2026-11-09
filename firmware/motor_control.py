# motor_control.py - DRV8833 Motor Control (fixed)
#
# The DRV8833 has NO separate speed/PWM/enable input per motor.
# Each motor has two inputs (IN1/IN2) and speed is set by putting PWM
# directly on the input that matches the direction:
#   forward : IN1 = PWM,  IN2 = LOW
#   reverse : IN1 = LOW,  IN2 = PWM
#   coast   : IN1 = LOW,  IN2 = LOW
# The chip's nSLEEP pin must be HIGH (tie to 3V3, or drive from a GPIO).

from machine import Pin, PWM, Timer
from config import *

# Smooth ramping: every RAMP_MS the speed moves this many % toward the target.
RAMP_MS = 20
RAMP_UP = 10      # 0 -> 100 % in about 0.2 s
RAMP_DOWN = 20    # 100 -> 0 % in about 0.1 s

# Lowest PWM duty (%) at which the motors actually turn. Below it they only buzz.
try:
    _MIN_DUTY = MOTOR_MIN_DUTY
except NameError:
    _MIN_DUTY = 0

# Optional nSLEEP pin. Set SLEEP_PIN = None in config.py if nSLEEP is
# wired straight to 3V3.
try:
    _SLEEP_PIN = SLEEP_PIN
except NameError:
    _SLEEP_PIN = None


class Motor:
    """Control a single DC motor via DRV8833"""

    def __init__(self, in1_pin, in2_pin, invert=False):
        self.in1 = PWM(Pin(in1_pin))
        self.in2 = PWM(Pin(in2_pin))
        self.in1.freq(PWM_FREQ)
        self.in2.freq(PWM_FREQ)
        self.invert = invert
        self.speed = 0
        self.set_speed(0)

    def set_speed(self, speed):
        """speed: -100 (full reverse) .. 0 (stop) .. 100 (full forward)"""
        speed = max(-100, min(100, speed))
        self.speed = speed
        if self.invert:
            speed = -speed

        # Motors don't turn below MIN_DUTY (they only buzz), so map any
        # non-zero speed onto MIN_DUTY..100 % instead of 0..100 %.
        if speed == 0:
            duty = 0
        else:
            pct = _MIN_DUTY + (100 - _MIN_DUTY) * abs(speed) / 100.0
            duty = int(pct / 100.0 * 65535)
        if speed > 0:
            self.in1.duty_u16(duty)
            self.in2.duty_u16(0)
        elif speed < 0:
            self.in1.duty_u16(0)
            self.in2.duty_u16(duty)
        else:
            self.in1.duty_u16(0)
            self.in2.duty_u16(0)

    def stop(self):
        self.set_speed(0)

    def get_speed(self):
        return self.speed


class Rover:
    """Dual-motor rover with differential steering and smooth speed ramping.

    drive() only sets a TARGET speed. A hardware timer moves the real motor
    speed toward the target every RAMP_MS, so the rover accelerates smoothly
    instead of jumping between the 5-10 commands per second the phone sends.
    stop() is immediate (no ramp) for safety.
    """

    def __init__(self):
        # Wake the driver up (nSLEEP must be HIGH or motors never move)
        self.sleep = None
        if _SLEEP_PIN is not None:
            self.sleep = Pin(_SLEEP_PIN, Pin.OUT)
            self.sleep.on()

        # If a wheel spins the wrong way, set invert=True for that motor
        self.motor_a = Motor(MOTOR_A_IN1, MOTOR_A_IN2, invert=False)
        self.motor_b = Motor(MOTOR_B_IN1, MOTOR_B_IN2, invert=False)

        self.target_a = 0
        self.target_b = 0
        self.cur_a = 0
        self.cur_b = 0
        self._timer = Timer(period=RAMP_MS, mode=Timer.PERIODIC, callback=self._tick)

    @staticmethod
    def _step(cur, tgt):
        if cur == tgt:
            return cur
        # Slowing down or reversing: ramp faster than speeding up.
        slowing = abs(tgt) < abs(cur) or (cur > 0 > tgt) or (cur < 0 < tgt)
        step = RAMP_DOWN if slowing else RAMP_UP
        if tgt > cur:
            return min(tgt, cur + step)
        return max(tgt, cur - step)

    def _tick(self, _t):
        a = self._step(self.cur_a, self.target_a)
        b = self._step(self.cur_b, self.target_b)
        if a != self.cur_a:
            self.cur_a = a
            self.motor_a.set_speed(a)
        if b != self.cur_b:
            self.cur_b = b
            self.motor_b.set_speed(b)

    def drive(self, speed_a, speed_b):
        self.target_a = max(-100, min(100, int(speed_a)))
        self.target_b = max(-100, min(100, int(speed_b)))

    def stop(self):
        # Immediate, no ramp
        self.target_a = self.target_b = 0
        self.cur_a = self.cur_b = 0
        self.motor_a.stop()
        self.motor_b.stop()

    def forward(self, speed=100):
        self.drive(speed, speed)

    def backward(self, speed=100):
        self.drive(-speed, -speed)

    def turn_left(self, speed=100):
        self.drive(-speed * 0.5, speed * 0.5)

    def turn_right(self, speed=100):
        self.drive(speed * 0.5, -speed * 0.5)

    def get_speeds(self):
        return {'a': self.target_a, 'b': self.target_b}


# Global rover instance
rover = Rover()
