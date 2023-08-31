import datetime
from servo import ServoMotor
from gpiozero import LED

class Alarm:
    def __init__(self, armed=True, time=datetime.time(8,0,0)) -> None:
        self.is_armed = armed
        self.time = time
        self.servo = ServoMotor(pin=18)
        self.is_on = False
        self.servo.off()
        self.led = LED(26) # led pin
        if self.is_armed:
            self.led.on()

    def arm(self):
        self.is_armed = True
        self.led.on()
        print('Alarm armed.')

    def disarm(self):
        self.is_armed = False
        self.led.off()
        print('Alarm disarmed.')

    def activate(self):
        self.is_on = True
        self.servo.on()
        print('Activated alarm!')
    
    def deactivate(self):
        self.is_on = False
        self.servo.off()
        print('Deactivated alarm!')
    