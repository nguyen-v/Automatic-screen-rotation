
// Orientation.cpp

// Author:           Nguyen Vincent
// Created:          Feb, 02, 2021
// Updated:          Feb, 03, 2021

#include "Orientation.h"
#include <Arduino_LSM6DS3.h>
#include <Adafruit_SleepyDog.h>

void IMUData::setAcceleration(float x_, float y_, float z_) {
    x = x_;
    y = y_;
    z = z_;
}

void IMUData::readAcceleration() {
    if (IMU.accelerationAvailable()) {
        float x_read, y_read, z_read;
        IMU.readAcceleration(x_read, y_read, z_read);
        setAcceleration(x_read, y_read, z_read);
    }
}


Orientation IMUData::getOrientation(Orientation old_orientation, 
                                    Configuration config) const {
    if (abs(x) > config.x_threshold * X_MAX) {
        if (x > 0)  return X_POS;
        else        return X_NEG;
    } else if (abs(y) > config.y_threshold * Y_MAX ) {
        if (y > 0)  return Y_POS;
        else        return Y_NEG;
    } else if (abs(z) > config.z_threshold * Z_MAX) {
        return FLAT;
    }
    return old_orientation;
}

Orientation IMUData::orientation(Orientation old_orientation, 
                                 Configuration config) {
    readAcceleration();
    Orientation new_orientation = getOrientation(old_orientation, config);
    delay(config.sampling_rate_ms);

    for (int i = 0; i < config.number_stable_samples; i++) {
        readAcceleration();
        if (new_orientation != getOrientation(old_orientation, config))
            return old_orientation;
        delay(config.sampling_rate_ms);
    }
    return new_orientation;
}


void IMUData::sendOrientation(Orientation orientation) const {
    switch(orientation) {
        case X_POS: Serial.print("X_POS"); break;
        case X_NEG: Serial.print("X_NEG"); break;
        case Y_POS: Serial.print("Y_POS"); break;
        case Y_NEG: Serial.print("Y_NEG"); break;
        case FLAT:  Serial.print("FLAT");  break;
        case START_ORIENTATION:            break;
    }
}

void IMUData::displayAcceleration() const {
    Serial.print(x);
    Serial.print('\t');
    Serial.print(y);
    Serial.print('\t');
    Serial.println(z);
}

Configuration::Configuration() {

    sampling_rate_ms        = SAMPLING_RATE_MS;                            
    number_stable_samples   = NUMBER_STABLE_SAMPLES;

    x_threshold             = X_THRESHOLD;
    y_threshold             = Y_THRESHOLD;
    z_threshold             = Z_THRESHOLD;
}

Configuration::Configuration(int sam_rate, int num_sam, 
                            float x_thr, float y_thr, float z_thr) {

    sampling_rate_ms        = sam_rate;                            
    number_stable_samples   = num_sam;

    x_threshold             = x_thr;
    y_threshold             = y_thr;
    z_threshold             = z_thr;
}

void Configuration::displayConfig() {
    Serial.println("Current configuration parameters:"); 

    Serial.println("Modifiable values");

    Serial.print("SamplingRate:" );         Serial.print("\t"); 
    Serial.println(sampling_rate_ms);
    
    Serial.print("NumberStableSamples:" );  Serial.print("\t"); 
    Serial.println(number_stable_samples);

    Serial.print("XThreshold:" );           Serial.print("\t"); 
    Serial.println(x_threshold);

    Serial.print("YThreshold:" );           Serial.print("\t"); 
    Serial.println(y_threshold);

    Serial.print("ZThreshold:" );           Serial.print("\t"); 
    Serial.println(z_threshold);

    Serial.println("Non-modifiable values");

    Serial.print("X_MAX:" );                Serial.print("\t"); 
    Serial.println(X_MAX);
    Serial.print("Y_MAX:" );                Serial.print("\t"); 
    Serial.println(Y_MAX);
    Serial.print("Z_MAX:" );                Serial.print("\t"); 
    Serial.println(Z_MAX);

}

void establishContact() {
  while (Serial.readStringUntil('\n') != CONFIRMATION_MESSAGE) {
    Serial.println(READY_MESSAGE);
    delay(READY_MESSAGE_INTERVAL);
  }
}

Configuration getConfigParams() {
    while(!Serial.available()){}
    int sam_rate = Serial.parseInt();                         
    int num_sam  = Serial.parseInt();
    float x_thr  = Serial.parseFloat();
    float y_thr  = Serial.parseFloat();
    float z_thr  = Serial.parseFloat();
    return Configuration(sam_rate, num_sam, 
                         x_thr, y_thr, z_thr);
}

void checkConnection() {
     if(Serial.readStringUntil('\n') == CONNECTED_MESSAGE)
         Watchdog.reset();
}