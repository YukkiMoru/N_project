#pragma once
#include <Adafruit_NeoPixel.h>

class SmartLED {
public:
    enum State {
        Initializing,
        Error,
        Outputting
    };

    SmartLED(Adafruit_NeoPixel& pixels);
    void setState(State state);

private:
    Adafruit_NeoPixel& _pixels;
    State _state;
    void update();
};
