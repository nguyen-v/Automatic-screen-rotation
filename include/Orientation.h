
// Orientation.h

// Author:           Nguyen Vincent
// Created:          Feb, 02, 2021
// Updated:          Feb, 03, 2021


#ifndef ORIENTATION_H 
#define ORIENTATION_H

// Intervals are in ms

// Watchdog timer
// Has to be greater than CHECK_CONNECTION_INTERVAL in the python script
#define WATCHDOG_INTERVAL       5000

// Serial
#define BAUD_RATE               9600

// Ready, confirmation and connected messages 
// must be the same in Arduino and Python

#define RESET_MESSAGE             "Reset"
#define READY_MESSAGE             "Ready"
#define CONFIRMATION_MESSAGE      "Confirmation"
#define CONNECTED_MESSAGE         "Connected"
#define READY_MESSAGE_INTERVAL    300
#define CHECK_CONNECTION_INTERVAL 1000

#define COMMAND_START             "<"
#define COMMAND_END               ">"

// Default configuration values for reference ----------------------------------

// Number of stable samples before rotation is detected
#define NUMBER_STABLE_SAMPLES     10
#define SAMPLING_RATE_MS          20

// Threshold (0-1) of maximum acceleration before change is detected
// Higher threshold means lower sensitivity
#define X_THRESHOLD               0.90
#define Y_THRESHOLD               0.90
#define Z_THRESHOLD               0.75

// No access to these values in the configuration file -------------------------

// Maximum acceleration value in Gs
#define X_MAX                     1.00
#define Y_MAX                     1.00
#define Z_MAX                     1.00

// -----------------------------------------------------------------------------

enum Orientation { 
  X_POS, X_NEG, Y_POS, Y_NEG, FLAT, START_ORIENTATION
};

struct Configuration {

    int sampling_rate_ms;
    int number_stable_samples;
    float x_threshold;
    float y_threshold;
    float z_threshold;
    float x_max;
    float y_max;
    float z_max;

    Configuration();
    Configuration(int num_sam, int sam_rate, 
                  float x_thr, float y_thr, float z_thr);
    void displayConfig();
};

class IMUData {
    float x = 0, y = 0, z = 0;
    void setAcceleration(float x_, float y_, float z_);
    Orientation getOrientation(Orientation old_orientation, 
                               Configuration config) const;
    void readAcceleration();

  public:
    Orientation orientation(Orientation old_orientation, Configuration config);
    void sendOrientation(Orientation orientation) const;
    void displayAcceleration() const;
};


void establishContact();
Configuration getConfigParams();

void checkConnection();

#endif