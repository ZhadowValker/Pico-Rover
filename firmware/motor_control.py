# motor_control.py - DRV8833 Motor Control

from machine import Pin, PWM
from config import *

class Motor:
    """Control a single DC motor via DRV8833"""
    
    def __init__(self, in1_pin, in2_pin, pwm_pin):
        self.in1 = Pin(in1_pin, Pin.OUT)
        self.in2 = Pin(in2_pin, Pin.OUT)
        self.pwm = PWM(Pin(pwm_pin))
        self.pwm.freq(PWM_FREQ)
        self.pwm.duty_u16(0)
        self.speed = 0
    
    def set_speed(self, speed):
        """
        Set motor speed
        speed: -100 to 100 (-100=full reverse, 0=stop, 100=full forward)
        """
        self.speed = max(-100, min(100, speed))
        
        if self.speed > 0:
            # Forward
            self.in1.on()
            self.in2.off()
        elif self.speed < 0:
            # Reverse
            self.in1.off()
            self.in2.on()
        else:
            # Stop
            self.in1.off()
            self.in2.off()
        
        # Set PWM duty (0-65535)
        duty = int((abs(self.speed) / 100.0) * 65535)
        self.pwm.duty_u16(duty)
    
    def stop(self):
        """Stop the motor"""
        self.set_speed(0)
    
    def get_speed(self):
        """Get current speed"""
        return self.speed


class Rover:
    """Dual-motor rover with differential steering"""
    
    def __init__(self):
        self.motor_a = Motor(MOTOR_A_IN1, MOTOR_A_IN2, MOTOR_A_PWM)
        self.motor_b = Motor(MOTOR_B_IN1, MOTOR_B_IN2, MOTOR_B_PWM)
    
    def drive(self, speed_a, speed_b):
        """
        Drive rover with differential steering
        speed_a: left motor speed (-100 to 100)
        speed_b: right motor speed (-100 to 100)
        """
        self.motor_a.set_speed(speed_a)
        self.motor_b.set_speed(speed_b)
    
    def stop(self):
        """Emergency stop"""
        self.motor_a.stop()
        self.motor_b.stop()
    
    def forward(self, speed=100):
        """Move forward"""
        self.drive(speed, speed)
    
    def backward(self, speed=100):
        """Move backward"""
        self.drive(-speed, -speed)
    
    def turn_left(self, speed=100):
        """Turn left (rotate)"""
        self.drive(-speed * 0.5, speed * 0.5)
    
    def turn_right(self, speed=100):
        """Turn right (rotate)"""
        self.drive(speed * 0.5, -speed * 0.5)
    
    def get_speeds(self):
        """Get current motor speeds"""
        return {
            'a': self.motor_a.get_speed(),
            'b': self.motor_b.get_speed()
        }


# Global rover instance
rover = Rover()
