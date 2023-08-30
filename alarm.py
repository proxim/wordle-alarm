import datetime

class Alarm:
    def __init__(self, armed=True, time=datetime.time(8,0,0)) -> None:
        self.is_on = False
        self.is_armed = armed
        self.time = time

    def arm(self):
        self.is_armed = True
        print('Alarm armed.')

    def disarm(self):
        self.is_armed = False
        print('Alarm disarmed.')

    def activate(self):
        self.is_on = True
        print('Activated alarm!')
    
    def deactivate(self):
        self.is_on = False
        print('Deactivated alarm!')
    