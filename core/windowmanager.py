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


class WindowManager(Thread):

    def __init__(self, sm,  param, config):
        Thread.__init__(self)
        self._sm = sm
        self.display = Display()  # Initialise display
        self.rootWindow = self.display.screen().root
        for win in self.display.screen().root.query_tree().children:
            print("Win id: {} CEF id: {}".format(win.id, sm._cef.wid))
            if win.id == sm._cef.wid:
                self.cef = win
                break
        else:
            print("ERRO: CEF windows not found")
            raise "CEF windows not found"
        #TODO: Décider comment les événement vont être géré et par qui
        # Je pense que déléguer les événement clavier a cef et les focus a xlib pour le rediriger vers cef est envisageable
        self.rootWindow.change_attributes(event_mask = X.SubstructureRedirectMask)
        self.keyboardHandler = keyboard(self.display, self.rootWindow)
        self.mouseHandler = mouse()
        self.mappingHandler = mapping(self.display, self.rootWindow)

        self.cef.change_attributes(event_mask = X.SubstructureRedirectMask)
        self.keyboardHandler2 = keyboard(self.display, self.cef)
        self.mouseHandler2 = mouse()
        self.mappingHandler2 = mapping(self.display, self.cef)

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
            if event.type == X.KeyPress:
                self.keyboardHandler.handleKeyEvent(event)
            elif event.type == X.MapRequest:
                self.mappingHandler.handleMapEvent(event)
            elif event.type == X.ButtonPress:
                self.mouseHandler.handleMouseEvent(event)
            elif event.type == X.ButtonRelease:
                self.mouseHandler.handleMouseEvent(event)
            elif event.type == X.MotionNotify:
                self.mouseHandler.handleMouseEvent(event)

    def run(self):
        while self._sm.running:
            print('Window Manager')
            self.handleEvents()
            self.mappingHandler.drawBorders()
            self.mappingHandler.updateFocus()
