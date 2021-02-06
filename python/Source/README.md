Automatic screen rotation for Windows

Requirements:

Python 3.x
    Packages:
    - PySerial
    - wmi

If access is denied, try:
python -m pip install <package> 
instead of:
pip install <package>

If you get unresolved imports, see: https://stackoverflow.com/q/53939751

VSCode with PlatformIO IDE
    Libraries
    - Arduino_LSM6DS3
    - Adafruit_SleepyDog

Board:            Arduino Nano 33 IoT
Sensor            LSM6DS3 Accelerometer and Gyroscope (included in the board)
Connection type:  Serial USB
Operating system: Windows 10

0) Unzip the source folder
1) Install Python
1.1) Install listed libraries
2) Install VSCode and PlatformIO
2.1) Install listed libraries
3) Plug in the board (USB) and upload (arrow at bottom left)
4) Create a startup task in task scheduler
https://www.jcchouinard.com/python-automation-using-task-scheduler/
Use pythonw.exe for background process, usually located at e.g.
C:\Python39\pythonw.exe

5) Change the settings in rotate_screen_config.ini
5.1) You can execute the python script in a console for debugging purposes 
    with py .\rotate_screen.py (open the terminal in the Source folder)