from cefpython3 import cefpython as cef
from threading import Thread, Lock, Event
import platform
import sys
import os

class CEFManager(Thread):
    _settings = {
        "debug": True,
        "log_severity": cef.LOGSEVERITY_INFO,
        "log_file": "debug.log",
    }

    def __init__(self, sm,  param, config):
        Thread.__init__(self)
        self._sm = sm

    def check_versions(self):
        ver = cef.GetVersion()
        print("[hello_world.py] CEF Python {ver}".format(ver=ver["version"]))
        print("[hello_world.py] Chromium {ver}".format(ver=ver["chrome_version"]))
        print("[hello_world.py] CEF {ver}".format(ver=ver["cef_version"]))
        print("[hello_world.py] Python {ver} {arch}".format(
               ver=platform.python_version(),
               arch=platform.architecture()[0]))
        assert cef.__version__ >= "57.0", "CEF Python v57.0+ required to run this"

    def run(self):
        self.check_versions()
        sys.excepthook = cef.ExceptHook
        try:
            cef.Initialize(settings=self._settings)
            cef.CreateBrowserSync(url="file://{}/ui/dist/ui/index.html".format(os.getcwd()), window_title="Hello World!")
            cef.MessageLoop()
            # while self._sm.running:
            #     print('Window Manager')
            #     time.sleep(1)
            cef.Shutdown()
        except cef.ExceptHook:
            print("CEF Crash")
