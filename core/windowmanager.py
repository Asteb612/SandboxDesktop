from threading import Thread, Lock, Event
import time

class WindowManager(Thread):

    def __init__(self, sm,  param, config):
        Thread.__init__(self)
        self._sm = sm

    def run(self):
        while self._sm.running:
            print('Window Manager')
            time.sleep(1)
