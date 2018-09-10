#Sandbox Desktop

##Summary
SandboxDesktop: Entry point
ConfigManager: Control config edition
WindowsManager: Detects windows events
ModuleManager: Load modules and check dependencies
ResourceManager: Manager and control resources access and contexts
    - Module resources has been stored in a context
    - Global context its read only on modules


##Ideas
- Each modules has been loaded with a auth token. This token is used in each API request to identify the module and his rigths.

-----
### Request owned by module to Windows Manager
Must of request are owned by module and because modules are writen by users its need security.
[Modules] <> Modules API <> REST Requests <> ModuleManager <> Resource Manager <> Windows Manager

### Request owned by Window Manager to module
All request owned by Windows Manager are with top priority.
#### To python callback
Windows Manager <> Module Manager <> Module

#### To js callback
Windows Manager <> Module Manager <> Module
* Each Modules can define callback called by ModuleManager

### Setuptools
* https://python-packaging.readthedocs.io/en/latest/


### Border
```python
window.configure(border_width = preferences.theme.border.borderWidth)
window.change_attributes(None,border_pixel=borderColour)
self.display.sync()
```

### Window Background
https://tronche.com/gui/x/xlib/window/attributes/background.html
https://en.wikipedia.org/wiki/Alpha_compositing

```python
colormap = d.screen().default_colormap

    red = colormap.alloc_named_color("red").pixel
    blue = colormap.alloc_named_color("blue").pixel
    background = colormap.alloc_named_color("white").pixel

    window = root.create_window(100, 100, 100, 100, 1,
                                X.CopyFromParent, X.InputOutput,
                                X.CopyFromParent,
                                background_pixel = background,
                                event_mask = X.StructureNotifyMask | X.ExposureMask)
    window.map()
```

```python
r.change_property(Xatom.WM_NORMAL_HINTS, Xatom.STRING, 32, [1, 2, 3, 4])
```
