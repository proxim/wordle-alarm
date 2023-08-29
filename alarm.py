import datetime

class Alarm:
    def __init__(self, armed=True, on=False, time=datetime.time(8,0,0)) -> None:
        self.is_armed = armed
        self.is_on = on
        self.time = time

    def arm(self):
        self.is_armed = True

    def disarm(self):
        self.is_armed = False

    def activate(self):
        self.is_on = True
        print('Activated alarm!')
    
    def deactivate(self):
        self.is_on = False
        print('Deactivated alarm!')
    