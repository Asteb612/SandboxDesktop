#Sandbox Desktop

##TODO
- Find a good x11 lib
- Check if out rendering is ok or find how to use the x11 protocol

- Local Windows Manager + ssh connection

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
[Modules]   <-> Modules API  <-> REST Requests <-> ModuleManager <-> Resource Manager <-> Windows Manager

### Request owned by Window Manager to module
All request owned by Windows Manager are with top priority.
#### To python callback
Windows Manager <-> Module Manager <-> Module
#### To js callback
Windows Manager <-> Module Manager <-> Module
----
Each Modules can define callback called by ModuleManager
