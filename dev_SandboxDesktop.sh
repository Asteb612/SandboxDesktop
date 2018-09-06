#!/usr/bin/bash
killall Xephyr  # Kill any existing Xephyr windows
export DISPLAY=:0  # Set display to main display
Xephyr -screen $1 -br :3 &  # Start new Xephyr session
export DISPLAY=:3  # Set display to Xephyr window
python SandboxDesktop.py run  # Run SandboxDesktop
