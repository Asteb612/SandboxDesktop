#!/usr/bin/env python3
# -*- coding: utf-8 -*

import time

from cefmanager import CEFManager
from modulemanager import ModuleManager
from windowsmanager import WindowsManager
from resourcemanager import ResourceManager

class SandboxDesktop(ResourceManager):
    """."""
    _module_manager = None
    _cef_manager = None
    _windows_manager = None

    def __init__(self):
        """."""
        super(ResourceManager, self).__init__()
        self._module_manager = ModuleManager()
        self._windows_manager = WindowsManager()
        self._cef_manager = CEFManager()

    def run(self):
        while True:
            print("SandboxDesktop: wait event {}".format(self.events))
            time.sleep(0.5)



def main():
    sd = SandboxDesktop()
    sd.run()

if __name__ == '__main__':
    main()
