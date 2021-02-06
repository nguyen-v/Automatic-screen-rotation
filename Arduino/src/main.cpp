
// Main source file for screen rotation detection
// main.cpp

// Author:           Nguyen Vincent
// Created:          Feb, 02, 2021
// Updated:          Feb, 03, 2021
// Version:          1.1

// Hardware Resources:
// Sensor            LSM6DS3 Accelerometer and Gyroscope

// Development Environment Specifics:
// IDE:              PlatformIO for VSCode
// Board:            Arduino Nano 33 IoT
// Connection type:  Serial USB

// ### INCLUDES ################################################################

// Libraries
#include "Arduino.h"
#include <Arduino_LSM6DS3.h>
#include <Adafruit_SleepyDog.h>

// Custom headers
#include "Orientation.h"

// ### SETUP ###################################################################

IMUData data;
Orientation old_orientation = START_ORIENTATION;
Orientation orientation = old_orientation;
Configuration config;
unsigned long previous_millis = 0;

void setup() {

  // Blink built-in LED at startup for debugging purposes
  pinMode(LED_BUILTIN, OUTPUT);
  for(int i = 0; i < 3; ++i) {
    // digitalWrite(LED_BUILTIN, HIGH);
    // delay(500);
    // digitalWrite(LED_BUILTIN, LOW);
    // delay(500);
  }

  // Initiate serial connection
  Serial.begin(BAUD_RATE);
  while (!Serial);

  Serial.println(RESET_MESSAGE);
  establishContact();
  
  config = getConfigParams();
  // config.displayConfig();
  Watchdog.enable(WATCHDOG_INTERVAL);

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }
  // Indicate that data is ready to be received

  //  Read and store configuration variables
  old_orientation = data.orientation(old_orientation, config);
}

void blink() {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(50);
    digitalWrite(LED_BUILTIN, LOW);
}

// ### LOOP ####################################################################

void loop() {

  unsigned long current_millis = millis();
  if (current_millis - previous_millis >= CHECK_CONNECTION_INTERVAL) {
    checkConnection();
    previous_millis = current_millis;
  }

  orientation = data.orientation(old_orientation, config);
  if(orientation != old_orientation) {
    Serial.print(COMMAND_START);
    data.sendOrientation(orientation);
    Serial.println(COMMAND_END);
    old_orientation = orientation;
    // blink(); // for debugging
  }
  // data.displayAcceleration();
}
