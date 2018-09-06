# Xlib imports - Interface with the X window system
from Xlib import X, XK
from Xlib.display import Display

from threading import Thread, Lock, Event
import time

# HackWM imports - Core functions of HackWM
from .Keyboard import keyboard
from .Mouse import mouse
from .Mapping import mapping

from .Utilities import runProcess

def setWallpaper():
    runProcess(["feh", "--bg-scale", "DefaultWallpaper.jpeg"])


class WindowManager(Thread):

    def __init__(self, sm,  param, config):
        Thread.__init__(self)
        self._sm = sm
        self.display = Display()  # Initialise display

        for win in self.display.screen().root.query_tree().children:
            print("Win id: {} CEF id: {}".format(win.id, sm._cef.wid))
            if win.id == sm._cef.wid:
                self.rootWindow = win
                break
        else:
            print("ERRO: CEF windows not found")
            raise "CEF windows not found"
        self.rootWindow.change_attributes(event_mask = X.SubstructureRedirectMask)
        self.keyboardHandler = keyboard(self.display, self.rootWindow)
        self.mouseHandler = mouse()
        self.mappingHandler = mapping(self.display, self.rootWindow)

        # setWallpaper()

    def handleEvents(self):
        if True: #self.display.pending_events() > 0:  # If there is an event in the queue
            print("Wait event")
            event = self.display.next_event()  # Grab it
            print("Got an event! ({})".format(str(event.type)))
            print(
                "type map: {}\n".format(X.MapRequest),
                "type key: {}\n".format(X.KeyPress),
                "type button press: {}\n".format(X.ButtonPress),
                "type button release: {}\n".format(X.ButtonRelease),
                "type motion: {}\n".format(X.MotionNotify))
            if event.type == X.KeyPress: self.keyboardHandler.handleKeyEvent(event)
            elif event.type == X.MapRequest: self.mappingHandler.handleMapEvent(event)
            elif event.type == X.ButtonPress: self.mouseHandler.handleMouseEvent(event)
            elif event.type == X.ButtonRelease: self.mouseHandler.handleMouseEvent(event)
            elif event.type == X.MotionNotify: self.mouseHandler.handleMouseEvent(event)

    def run(self):
        while self._sm.running:
            print('Window Manager')
            self.handleEvents()
            self.mappingHandler.drawBorders()
            self.mappingHandler.updateFocus()
