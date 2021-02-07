# Accelerometer based automatic screen rotation for Windows
A Python and C++ utility for automatic screen rotation.

## Features
- Automatic port detection and automatic (re)connection to the Arduino board
- Screen orientation and position customizable for each of the 5 physical orientations (portrait, portrait flipped, landscape, landscape flipped and flat) using a configuration file
- Control over rotation threshold and sample rates

## Requirements:

### Python 3.x
#### Packages:
    - PySerial
    - wmi

If access is denied, try:
python -m pip install <package> 
instead of:
pip install <package>

If you get unresolved imports, see: https://stackoverflow.com/q/53939751

### VSCode with PlatformIO IDE
#### Libraries
    - Arduino_LSM6DS3
    - Adafruit_SleepyDog
    
| Board             | Sensor               |
|-------------------|----------------------|
|Arduino Nano 33 IoT| LSM6DS3 Accelerometer and Gyroscope (included in the board)  | 

## Setup process
1. Unzip the source folder
2. Install Python
    - Install listed modules
3. Install VSCode and PlatformIO
    - Install listed libraries
4. Plug in the board (USB) and upload (arrow at bottom left)
5. Create a startup task in task scheduler
https://www.jcchouinard.com/python-automation-using-task-scheduler/
Use pythonw.exe for creating a background process (start at logon), usually located at e.g.
C:\Python39\pythonw.exe

6. Change the settings in rotate_screen_config.ini
    - You can execute the python script in a console for debugging purposes 
    with py .\rotate_screen.py (open the terminal in the Source folder)
