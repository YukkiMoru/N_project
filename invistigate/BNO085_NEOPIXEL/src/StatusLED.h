#pragma once
#include <Adafruit_NeoPixel.h>

class StatusLED {
public:
    enum State {
        Initializing,
        Error,
        Outputting
    };

    StatusLED(Adafruit_NeoPixel& pixels);
    void setState(State state);

private:
    Adafruit_NeoPixel& _pixels;
    State _state;
    void update();
};
