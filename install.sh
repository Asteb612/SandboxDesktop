#!/usr/bin/bash
pip install -r requirements.txt
(
    cd ui ;
    ./install.sh ;
    ./build.sh
)
