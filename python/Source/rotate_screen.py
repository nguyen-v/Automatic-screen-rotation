#  Python script for reading serial data and changing screen orientation
#  rotate_screen.py

#  Author:           Nguyen Vincent
#  Created:          Feb, 03, 2021
#  Updated:          Feb, 06, 2021

#  Hardware Resources:
#  Sensor            LSM6DS3 Accelerometer and Gyroscope

#  Development Environment Specifics:
#  IDE:              PlatformIO for VSCode
#  Board:            Arduino Nano 33 IoT

### IMPORTS ####################################################################

import sys
import os                               # file paths
import serial                           # serial connection with Arduino
import serial.tools.list_ports          # detection of serial ports
import string
import time                             # delays
import threading                        # thread to verify the connection

from subprocess import call             # to execute display.exe
from configparser import ConfigParser   # to read config file

import win32api                         # get the number of screens

### Global Constants ###########################################################

# Choose your configuration mode here
# You can create a custom mode in the configuration file
CONFIG_MODE                     = "ONLY_XY"
CONFIG_FILENAME                 = "rotate_screen_config.ini"

ACCEL_THR_MIN                   = 0
ACCEL_THR_MAX                   = 1     # greater than 1 for no detection
SAMPLING_RATE_MIN               = 1
NUMBER_STABLE_SAMPLES_MIN       = 1
POSSIBLE_ORIENTATIONS           = ("PORTRAIT", "PORTRAIT_FLIPPED", 
                                   "LANDSCAPE", "LANDSCAPE_FLIPPED", "")


SERIAL_PORT_LABEL               = "COM"
SERIAL_PORT_LABEL_MIN           = 1

# Serial

BAUD_RATE                       = 9600
# More valid names can be added here for non original Arduino ports
VALID_PORT_NAMES = [
    "Arduino",
    "USB Serial Device"
]
# Ready and confirmation and connected messages
# must be the same in Arduino and Python

# Interval are in seconds

READY_MESSAGE                   = "Ready"  
CONFIRMATION_MESSAGE            = "Confirmation"
CONNECTED_MESSAGE               = "Connected"
READY_MESSAGE_INTERVAL          = 0.3

COMMAND_START                   = "<"
COMMAND_END                     = ">"

# ERROR_COUNT_TIMEOUT             = 10
ERROR_COUNT_TIMEOUT             = float('inf') # use this for no timeout

SERIAL_CONNECTION_INTERVAL      = 1
CHECK_CONNECTION_INTERVAL       = 1

### Error messages #############################################################

def ERROR_FILENAME(filename):
    return filename + " file not found."   

def ERROR_MODE(mode, mode_list):
    return mode + " is not a valid mode.\n Valid modes are:" + str(mode_list)

ERROR_SERIAL_PORT        = ("Serial port name must follow the syntax " 
+ SERIAL_PORT_LABEL + "X where X is an integer greater or equal than " 
+ str(SERIAL_PORT_LABEL_MIN) + ", or empty.")

def ERROR_MONITOR_NUMBER(number_of_monitors):
    return ("Monitor number must be a positive integer between 1 and "
            + str(number_of_monitors) + "!")

ERROR_ACCEL_THR          = ("Acceleration threshold values must be a decimal"
" value between " + str(ACCEL_THR_MIN) + " and " + str(ACCEL_THR_MAX) + "!")

ERROR_SAMPLING_RATE      = ("The sampling rate must be an integer greater than "
+ str(SAMPLING_RATE_MIN) + "!")

ERROR_NUMBER_SAMPLE      = ("The number of stable samples must be an integer"
" greater than " + str(NUMBER_STABLE_SAMPLES_MIN) + "!")

ERROR_SCREEN_ORIENTATION = ("Screen orientation is invalid. Valid orientations:"
" PORTRAIT, PORTRAIT_FLIPPED, LANDSCAPE, LANDSCAPE_FLIPPED, or leave it empty.")

ERROR_SCREEN_POSITION    = ("Screen coordinates must be integers or empty!")

ERROR_SERIAL_WRONG       = ("Ready message from Arduino was not received. "
"\nTrying next available port...\n")

ERROR_SERIAL_TIMEOUT     = ("Serial connection timed out. No connection was "
"established. Possible solutions:\n"
"- Check your wiring\n"
"- Restart the Arduino board before attempting a new connection.\n"
"- If a port was specified in the configuration file, double-check it.")

### Variables ##################################################################
ser = None # I don't like global variables, but couldn't find a better way...

### Classes ####################################################################
# https://stackoverflow.com/q/43229939
# "How to pass a boolean by reference across threads and modules"
class ConfigurationToken:
    def __init__(self):
        self.config_sent = False
    def isSent(self):
        self.config_sent = True
    def isNotSent(self):
        self.config_sent = False

class ReceiveDataToken:
    def __init__(self):
        self.receiving = False
    def isReceiving(self):
        self.receiving = True
    def isNotReceiving(self):
        self.receiving = False

class ConfigurationData:
    def __init__(self, filename):
        error_count = 0
        while error_count <= ERROR_COUNT_TIMEOUT:
            value_error = False
            self.filename   = filename
            if os.path.isfile(filename):
                config = ConfigParser()
                config.read(filename)

                # Mode
                self.mode = config['MODE']['Mode']
                mode_list = [x for x in config.sections() if "MODE" not in x]
                mode_list.append("DEFAULT")
                if(self.mode not in mode_list):
                    print(ERROR_MODE(self.mode, mode_list))
                    value_error = True
                # Monitor number

                number_of_monitors = len(win32api.EnumDisplayMonitors())

                if config[self.mode]['MonitorNumber'] == "":
                    self.monitor = ""
                else:
                    try:
                        mon = int(config[self.mode]['MonitorNumber'])
                        if mon <= 0 or mon > number_of_monitors:
                            print(ERROR_MONITOR_NUMBER(number_of_monitors))
                            value_error = True
                        else:
                            self.monitor = config[self.mode]['MonitorNumber']
                    except ValueError:
                        print(ERROR_MONITOR_NUMBER(number_of_monitors))
                        value_error = True

                # Sampling rate

                try:
                    sam_rate = int(config[self.mode]['SamplingRate'])
                except ValueError:
                    print(ERROR_SAMPLING_RATE)
                    value_error = True
                if (sam_rate >= SAMPLING_RATE_MIN):
                    self.sampling_rate = sam_rate
                else:
                    print(ERROR_SAMPLING_RATE)
                    value_error = True

                # Number of stable samples

                try:
                    num_stable_sam = int(config[self.mode]['NumberStableSamples'])
                except ValueError:
                    print(ERROR_NUMBER_SAMPLE)
                    value_error = True
                if (num_stable_sam >= NUMBER_STABLE_SAMPLES_MIN):
                    self.number_stable_samples = num_stable_sam
                else:
                    print(ERROR_NUMBER_SAMPLE)
                    value_error = True

                # Acceleration thresholds
                try:
                    x_thr = float(config[self.mode]['XThreshold'])
                    y_thr = float(config[self.mode]['YThreshold'])
                    z_thr = float(config[self.mode]['ZThreshold'])
                except ValueError:
                    print(ERROR_ACCEL_THR)
                    value_error = True
                if all(ACCEL_THR_MIN <= thr <= ACCEL_THR_MAX 
                for thr in (x_thr, y_thr, z_thr)):
                    self.x_threshold = x_thr
                    self.y_threshold = y_thr
                    self.z_threshold = z_thr
                else:
                    print(ERROR_ACCEL_THR)
                    value_error = True

                # Screen orientation

                try:
                    x_p     = str(config[self.mode]['XPos'])
                    y_p     = str(config[self.mode]['YPos'])
                    x_n     = str(config[self.mode]['XNeg'])
                    y_n     = str(config[self.mode]['YNeg'])
                    flat_   = str(config[self.mode]['Flat'])
                except ValueError:
                    print(ERROR_SCREEN_ORIENTATION)
                    value_error = True
                if all(orientations in POSSIBLE_ORIENTATIONS
                       for orientations in (x_p, y_p, x_n, y_n, flat_)):
                    self.x_pos = x_p
                    self.y_pos = y_p
                    self.x_neg = x_n
                    self.y_neg = y_n
                    self.flat  = flat_
                else:
                    print(ERROR_SCREEN_ORIENTATION)
                    value_error = True
                
                # Screen position

                self.x_px = str(config[self.mode]['XPos_x'])
                self.x_py = str(config[self.mode]['XPos_y'])

                self.y_px = str(config[self.mode]['YPos_x'])
                self.y_py = str(config[self.mode]['YPos_Y'])

                self.x_nx = str(config[self.mode]['XNeg_x'])
                self.x_ny = str(config[self.mode]['XNeg_y'])

                self.y_nx = str(config[self.mode]['YNeg_x'])
                self.y_ny = str(config[self.mode]['YNeg_y'])

                self.fx   = str(config[self.mode]['Flat_x'])
                self.fy   = str(config[self.mode]['Flat_y'])
                positions = (self.x_px, self.x_py, self.y_px, self.y_py, 
                             self.x_nx, self.x_ny, self.y_nx, self.y_ny, 
                             self.fx, self.fy)
                for position in positions:
                    if position == "":
                        continue
                    else:
                        try:
                            int(position)
                        except ValueError:
                            print(ERROR_SCREEN_POSITION)
                            value_error = True
                if not(value_error):
                    break


            else:
                print(ERROR_FILENAME(filename))
                value_error = True
            if value_error:
                error_count += 1
            time.sleep(1)
        if value_error:
            raise IOError(ERROR_SERIAL_TIMEOUT)


    def initSerial(self):
        # Serial port
        if os.path.isfile(self.filename):
            config = ConfigParser()
            config.read(self.filename)
            port = self.serial_port = config[self.mode]['SerialPort']
            if port != "":
                try:
                    ser_port_number = int(port[len(SERIAL_PORT_LABEL):])
                    error_count = 0
                    while error_count <= ERROR_COUNT_TIMEOUT:
                        is_connected, ser = attemptConnection(port)
                        if is_connected:
                            return port, ser
                        time.sleep(SERIAL_CONNECTION_INTERVAL)
                        error_count += 1
                    raise IOError(ERROR_SERIAL_TIMEOUT)
                except ValueError:
                    print(ERROR_SERIAL_PORT)
                    # os._exit(1)

                if (port[0:len(SERIAL_PORT_LABEL)] == SERIAL_PORT_LABEL):
                    self.serial_port = port
                else:
                    raise ValueError(ERROR_SERIAL_PORT)
                    # os._exit(1)

            else:
                self.serial_port, ser = findPort()
                return self.serial_port, ser
        else:
            raise ValueError(ERROR_FILENAME(filename))
            # os._exit(1)
            
    def sendConfigParameters(self, ser):
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        # time.sleep(0.1)
        # add new line character to integers for proper separation
        ser.write((str(self.sampling_rate)+"\n").encode())
        ser.write((str(self.number_stable_samples)+"\n").encode())
        ser.write(str(self.x_threshold).encode())
        ser.write(("\n").encode())
        ser.write(str(self.y_threshold).encode())
        ser.write(("\n").encode())
        ser.write(str(self.z_threshold).encode())


### Functions ##################################################################

# https://stackoverflow.com/q/24214643
# "Python to automatically select serial ports (for Arduino)"
def findPort():

    # List available ports
    print("Available ports:\n")
    arduino_ports = getArduinoPorts()
    for available_port in list(serial.tools.list_ports.comports()):
        print(available_port)
    print("")
    if not arduino_ports:
        raise IOError("No Arduino found")
    
    error_count = 0
    while error_count <= ERROR_COUNT_TIMEOUT:
        for port in arduino_ports:
            is_connected, ser = attemptConnection(port)
            if is_connected:
                return port, ser
        time.sleep(SERIAL_CONNECTION_INTERVAL)
        error_count += 1
    raise IOError(ERROR_SERIAL_TIMEOUT)

def attemptConnection(port):
    try:
        print("Attempting serial connection to " + port + "...")
        ser = connectToPort(port)
        readyMessage = ser.readline().decode("utf-8")
        # wait a bit to receive the ready message from Arduino
        time.sleep(READY_MESSAGE_INTERVAL) 
        if READY_MESSAGE in readyMessage:
            print("Device found on " + port)
            # Send confirmation message before sending configuration. 
            ser.write(CONFIRMATION_MESSAGE.encode())
            ser.write(("\n").encode())
            ser.reset_input_buffer()
            return True, ser
        else:
            print(ERROR_SERIAL_WRONG)
            return False, None
    except IOError:
        print("Connection failed on " + port + "\n")
        return False, None


def getArduinoPorts():
    arduino_ports = [
        p.device
        for p in serial.tools.list_ports.comports()
        if any(port_name in p.description for port_name in VALID_PORT_NAMES)
    ]
    return arduino_ports

def connectToPort(port):
    ser = serial.Serial(port, BAUD_RATE, timeout=1,
                        xonxoff=False, rtscts=False, dsrdtr=False)
    ser.flushInput()
    ser.flushOutput()
    print("Connection established on " + port)
    return ser

# https://stackoverflow.com/q/21050671
# "How to check if device is connected Pyserial"
def checkConnection(port, config_mode, config_filename, data, 
                    config_token, receive_token):
    global ser
    is_connected = True
    while True:
        arduino_ports = getArduinoPorts()
        if port not in arduino_ports:
            print("Arduino disconnected from " + port)
            is_connected = False
            config_token.isNotSent()
            receive_token.isNotReceiving()
        if len(arduino_ports) != 0 and not(is_connected):
            error_count = 0
            while error_count <= ERROR_COUNT_TIMEOUT:
                for port in arduino_ports:
                    try:
                        time.sleep(2*SERIAL_CONNECTION_INTERVAL)
                        print("Attempting serial connection to " + port + "...")
                        ser = connectToPort(port)
                        is_connected = True
                        receive_token.isNotReceiving()
                        break
                    except IOError:
                        print("Connection failed on " + port + "\n")
                        time.sleep(2*SERIAL_CONNECTION_INTERVAL)
                        error_count += 1
                break
            if error_count == ERROR_COUNT_TIMEOUT:
                raise IOError(ERROR_SERIAL_TIMEOUT)

        if port in arduino_ports:
            # Don't read a line if currently receiving rotation commands from
            # the accelerometer
            #print(not(receive_token.receiving))
            if not(receive_token.receiving):
                try:
                    ready_message = ser.readline().decode("utf-8")
                except Exception:
                    pass
            else:
                ready_message = ""
            if READY_MESSAGE in ready_message:
                print("Ready message received on " + port)
                receive_token.isReceiving()
                try:
                    ser.write(CONFIRMATION_MESSAGE.encode())
                    ser.write(("\n").encode())
                # to avoid an error when Arduino is unplugged and 
                # ser.read/write is excecuted at the same time:
                except Exception:
                    pass
                # Re-read configuration file. 
                # Enables changing configuration by unplugging the board
                data.__init__(config_filename)
                # wait a bit for the arduino to react to the confirmation
                # message before sending configuration parameters
                time.sleep(READY_MESSAGE_INTERVAL)
                data.sendConfigParameters(ser)
                config_token.isSent()
                #receive_token.isNotReceiving()
            # Sending "Connected" message to Arduino to reset watchdog timer
            elif config_token.config_sent:
                ser.reset_output_buffer()
                ser.write(CONNECTED_MESSAGE.encode())
                ser.write(("\n").encode())
            # print(ready_message)
        time.sleep(CHECK_CONNECTION_INTERVAL)
        

### Main function ##############################################################

def main():
    global ser
    # config_filename = CONFIG_FILENAME
    # config_mode     = CONFIG_MODE
    data = ConfigurationData(CONFIG_FILENAME)
    # Initialize serial connection with Arduino board
    port, ser = data.initSerial()
    # time.sleep(2)
    # Create a new thread to check connection with Arduino
    config_token    = ConfigurationToken()
    receive_token   = ReceiveDataToken()
    check_connection = threading.Thread(target=checkConnection, 
                                        args = (port, CONFIG_MODE, CONFIG_FILENAME, data, 
                                        config_token, receive_token))
    check_connection.setDaemon(True)
    check_connection.start()
    
    # Send configuration file parameters
    data.sendConfigParameters(ser)
    config_token.isSent()

    orientationAngles = {
        "PORTRAIT_FLIPPED"  : "270"  ,
        "LANDSCAPE"         : "0"   ,
        "PORTRAIT"          : "90" ,
        "LANDSCAPE_FLIPPED" : "180" ,
        ""                  : ""
    }
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    receive_token.isReceiving()
    while True:
        while receive_token.receiving:
            try:
                line = ser.readline().decode("utf-8")
            # Don't throw an error when Arduino is unplugged.
            # This is handled in the check_connection thread.
            except Exception:
                pass
            if line == "": # ignore empty lines
                continue
            # check for the command start indicator at index 0
            if line.find(COMMAND_START) == 0:
                orientation = line[1:line.find(COMMAND_END)]
                print(orientation)
                if orientation   == "X_POS":
                    angle = orientationAngles[data.x_pos]
                    pos_x = data.x_px
                    pos_y = data.x_py
                elif orientation == "Y_POS":
                    angle = orientationAngles[data.y_pos]
                    pos_x = data.y_px
                    pos_y = data.y_py
                elif orientation == "X_NEG":
                    angle = orientationAngles[data.x_neg]
                    pos_x = data.x_nx
                    pos_y = data.x_ny
                elif orientation == "Y_NEG":
                    angle = orientationAngles[data.y_neg]
                    pos_x = data.y_nx
                    pos_y = data.y_ny
                elif orientation == "FLAT":
                    angle = orientationAngles[data.flat]
                    pos_x = data.fx
                    pos_y = data.fy

                monitor = data.monitor

                if (angle != ""):
                    angle = " /rotate " + angle
                else:
                    angle = ""

                if (pos_x != "" and pos_y != ""):
                    position = " /position " + pos_x + " " + pos_y
                else:
                    position = ""
                if (monitor == ""):
                    monitor = " /device 1"
                else:
                    monitor = " /device " + monitor
                if all(param == "" for param in [angle, pos_x, pos_y]):
                    continue
                else:
                    command = "display64.exe " + monitor + angle + position
                    # shell = True to prevent apparition of console
                    call(command, shell=True)
        time.sleep(CHECK_CONNECTION_INTERVAL)

    

################################################################################

if __name__=="__main__":
    main()
