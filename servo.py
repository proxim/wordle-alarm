import gpiozero
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import AngularServo

gpiozero.Device.pin_factory = PiGPIOFactory('127.0.0.1')

SERVO_PIN = 18

class ServoMotor:
    def __init__(self, pin=SERVO_PIN, min_pw=0.0004, max_pw=0.0024):
        self.pin = pin
        self.servo = AngularServo(self.pin, min_pulse_width=min_pw, max_pulse_width=max_pw)
    
    def on(self):
        self.servo.angle = -90

    def off(self):
        self.servo.angle = 0
