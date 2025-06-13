#pragma once
#include <Adafruit_NeoPixel.h>

enum SmartLEDState {
    SLED_Init,
    SLED_Error,
    SLED_Run
};

class SmartLED {
public:
    SmartLED(Adafruit_NeoPixel& pixels) : _pixels(pixels), _state(SLED_Init) { update(); }
    void setState(SmartLEDState state) {
        if (_state != state) {
            _state = state;
            update();
        }
    }
private:
    Adafruit_NeoPixel& _pixels;
    SmartLEDState _state;
    void update() {
        uint32_t color = 0;
        switch (_state) {
            case SLED_Init: color = _pixels.Color(255, 80, 0); break;
            case SLED_Error:        color = _pixels.Color(255, 0, 0); break;
            case SLED_Run:   color = _pixels.Color(0, 255, 0); break;
        }
        _pixels.fill(color);
        _pixels.show();
    }
};
