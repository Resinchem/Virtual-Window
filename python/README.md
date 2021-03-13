# Python Application

## Prerequisites

* Raspberry Pi 4 Raspberry Pi OS Lite, updated and connected to WiFi
* VLC
* Python 3
* VLC, MQTT and RPi GPIO Python libraries installed

## Configuration

You **must** edit the vlc_player.py file and update the global variable section at the top of the file to match your environment.  Specifically, you must update:

* MQTT settings (server IP, user, password and topic)
* Camera names and RTSP URLs for each camera to show
* Video clips and paths (if any)

## Optional Settings

There are a few other optional settings at the top of the file you may wish to change:

* How long each camera or video is shown when in 'loop' mode
* Which camera and video is shown first in the list when changing modes
* Which mode (camera or video) to use when the application launches

## Launching the application

The application can be launched by running the command: ```python3 vlc_player.py```

### More details on installation, configuration and use can be found in the wiki
