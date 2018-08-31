#!/usr/bin/python3
# Hello world example. Doesn't depend on any third party GUI framework.
# Tested with CEF Python v57.0+.

from cefpython3 import cefpython as cef
from threading import Thread, Lock, Event
import platform
import argparse
import json
import sys
import time


class RequiredConfig(Exception):
    pass

class InvalidCommand(Exception):

    def __init__(self, message):
        self._message = message

    def __str__(self):
        return self._message

    def __repr__(self):
        return self._message

class WindowManager(Thread):

    def __init__(self, sm,  param, config):
        Thread.__init__(self)
        self._sm = sm

    def run(self):
        while self._sm.running:
            print('Window Manager')
            time.sleep(1)

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
            cef.CreateBrowserSync(url="https://www.google.com/", window_title="Hello World!")
            cef.MessageLoop()
            # while self._sm.running:
            #     print('Window Manager')
            #     time.sleep(1)
            cef.Shutdown()
        except cef.ExceptHook:
            print("CEF Crash")

class ModuleManager(Thread):

    def __init__(self, sm, param, config):
        Thread.__init__(self)
        self._sm = sm

    def run(self):
        while self._sm.running:
            print('Module Manager')
            time.sleep(1)

class SandboxManager:
    _config = dict()
    _params = dict()
    _initialized = False
    _running = False
    _wm = None
    _mm = None
    _cef = None
    _lck = Lock()
    _stop_evt = Event()
    _start_points = {
        'run': {
            'name': '',
            'required_config': [],
            'required_param': [],
            'check': None,
            'exec': '_run'
        },
        'install': {
            'name': '',
            'required_config': [],
            'required_param': [],
            'check': None,
            'exec': None
        },
        'uninstall': {
            'name': '',
            'required_config': [],
            'required_param': [],
            'check': None,
            'exec': None,
            },
    }

    def __init__(self):
        # Extract parameters from argparse
        self._parser = argparse.ArgumentParser()

        subparsers = self._parser.add_subparsers(help='sub-command help', dest='command')
        run = subparsers.add_parser('run', help='Start the DeskopManager')
        install = subparsers.add_parser('install', help='Install SandboxManager on system')
        uninstall = subparsers.add_parser('uninstall', help='Uninstall SandboxManager on system')
        # Update internal parameters
        self._params.update(vars(self._parser.parse_args()))


    def _check_minimal_value(self, data, minimal_params):
        for el in minimal_params:
            if el['name'] not in data.keys():
                raise InvalidCommand("Variable {} required".format(el['name']))

    def _load_params(self, data):
        """Load parameters from command line."""
        minimal_params = [
        ]
        self._params.update(data)
        self._check_minimal_value(self._params, minimal_params)

    def _load_config(self, data):
        """Load config file from json."""
        # minimal_params = [
        #     {'name':'', 'type': 'str'}
        # ]
        minimal_params = [
        ]
        with open(self._params.get('config_path', 'config.json'), 'r') as f:
            array = json.load(f)
            self._config.update(array)
            self._check_minimal_value(self._config, minimal_params)

    def _wait_exit(self):
        time.sleep(10)
        self.stop()

    @property
    def running(self):
        self._lck.acquire()
        tmp = self._running
        self._lck.release()
        return tmp

    def stop(self):
        self._stop_evt.set()
        self._lck.acquire()
        self._running = False
        self._lck.release()

    def _run(self):
        try:
            self._mm = ModuleManager(self, self._params, self._config)
            self._wm = WindowManager(self, self._params, self._config)
            self._cef = CEFManager(self, self._params, self._config)
        except Exception:
            print('Module init failed')
        else:
            self._running = True
            self._mm.start()
            self._wm.start()
            self._cef.start()

    def _clean(self):
        if self._mm is not None:
            print("Waite join mm")
            self._mm.join()
        if self._wm is not None:
            print("Waite join wm")
            self._wm.join()
        if self._wm is not None:
            print("Waite join cef")
            self._cef.join()

    def init(self, params={}, config={}):
        self._load_params(params)
        self._load_config(config)
        self._initialized = True

    def run(self):
        if self._params['command'] not in self._start_points.keys():
            raise InvalidCommand("ERROR : {} is a invalid command !".format(command=self._params.get('command', 'Not defined')))
        command = self._start_points[self._params['command']]
        for required in command['required_config']:
            if required not in self._config or self._config[required] is None:
                raise RequiredConfig
        for required in command['required_param']:
            if required not in self._params or self._params[required] is None:
                raise RequiredConfig
        if command['check'] is not None and not getattr(self, command['check'])():
            raise "Check command failed"
        try:
            getattr(self, command['exec'])()
            self._wait_exit()
            if hasattr(self, 'clean'):
                getattr(self, command['clean'])()
        except Exception:
            print('Command {} failed'.format(command['name']))

def main():
    sm = SandboxManager()
    sm.init(params={}, config={})
    sm.run()


if __name__ == '__main__':
    main()
