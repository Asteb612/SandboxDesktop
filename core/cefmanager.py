from cefpython3 import cefpython as cef
from threading import Thread, Lock, Event
import platform
import sys
import os

"""CEFManager:
This object control the front part of SandboxDesktop
"""

class CEFManager(Thread):
    _settings = {
        "debug": True,
        "log_severity": cef.LOGSEVERITY_INFO,
        "log_file": "debug.log",
    }

    def __init__(self, sm,  param, config):
        Thread.__init__(self)
        self._sm = sm
        print("CEF: Create object")

        self.check_versions()

    def check_versions(self):
        ver = cef.GetVersion()
        print("[hello_world.py] CEF Python {ver}".format(ver=ver["version"]))
        print("[hello_world.py] Chromium {ver}".format(ver=ver["chrome_version"]))
        print("[hello_world.py] CEF {ver}".format(ver=ver["cef_version"]))
        print("[hello_world.py] Python {ver} {arch}".format(
               ver=platform.python_version(),
               arch=platform.architecture()[0]))
        assert cef.__version__ >= "57.0", "CEF Python v57.0+ required to run this"

    def open_popup(url, x=0, y=0, height=100, width=100):
        """Create a popup.
        url: Start point of popup
        """
        print("CEF: Create new popup url='{}' x={} y={} height={} width={}".format(url, x, x, height, width))
        pass

    def run(self):
        sys.excepthook = cef.ExceptHook
        try:
            print("CEF: Initialise")
            cef.Initialize(settings=self._settings)
            print("CEF: CreateBrowser")
            br_WindowInfo = cef.WindowInfo()
            br_WindowInfo.SetAsChild(0)
            br_WindowInfo.windowRect = [0, 0, 1200, 720]
            br_WindowInfo.windowName = 'SandboxDesktop: Web Windows Manager'
            self.win = cef.CreateBrowserSync(br_WindowInfo, url="file://{}/ui/dist/ui/index.html".format(os.getcwd()), window_title="Hello World!")
            self.wid = self.win.GetWindowHandle()
            print("CEF: Started on {}".format(self.wid))
            cef.MessageLoop()
            cef.Shutdown()
            self._sm.stop()
        except cef.ExceptHook:
            print("CEF Crash")
