# motor_test.py - run this FIRST, with the wheels lifted off the ground.
# Standalone: edit the pin numbers below to match YOUR wiring.
# It does not need WiFi or the rest of the project.

from machine import Pin, PWM
import time

# ---- EDIT THESE to match your wiring ----
A_IN1, A_IN2 = 19, 18     # left motor  -> DRV8833 AIN1, AIN2
B_IN1, B_IN2 = 17, 16     # right motor -> DRV8833 BIN1, BIN2
SLEEP_PIN = None          # GPIO wired to nSLEEP, or None if tied to 3V3
# -----------------------------------------

if SLEEP_PIN is not None:
    Pin(SLEEP_PIN, Pin.OUT).on()

def pwm(p):
    x = PWM(Pin(p)); x.freq(5000); x.duty_u16(0); return x

a1, a2, b1, b2 = pwm(A_IN1), pwm(A_IN2), pwm(B_IN1), pwm(B_IN2)

def run(ch, label, duty=45000, t=1.5):
    print("Testing:", label)
    ch.duty_u16(duty)
    time.sleep(t)
    ch.duty_u16(0)
    time.sleep(0.5)

run(a1, "Motor A forward")
run(a2, "Motor A reverse")
run(b1, "Motor B forward")
run(b2, "Motor B reverse")
print("Done. If nothing moved: check motor battery on VM, common GND, nSLEEP, wiring.")
