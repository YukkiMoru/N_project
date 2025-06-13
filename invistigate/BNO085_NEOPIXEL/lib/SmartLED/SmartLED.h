#pragma once
#include <Adafruit_NeoPixel.h>

// 必要に応じて値を変更
#define SLED_NUMPIXELS  1
#define SLED_PIN        6
#define SLED_BRIGHTNESS 20

enum SmartLEDState {
    SLED_Init,
    SLED_Error,
    SLED_Run
};

class SmartLED {
public:
    SmartLED() : _pixels(SLED_NUMPIXELS, SLED_PIN, NEO_GRB + NEO_KHZ800), _state(SLED_Init) {
        _pixels.begin();
        _pixels.setBrightness(SLED_BRIGHTNESS); // ← ここで明るさも設定
        update();
    }
    void setState(SmartLEDState state) {
        if (_state != state) {
            _state = state;
            update();
        }
    }
private:
    Adafruit_NeoPixel _pixels;
    SmartLEDState _state;
    void update() {
        uint32_t color = 0;
        switch (_state) {
            case SLED_Init:  color = _pixels.Color(255, 80, 0); break;
            case SLED_Error: color = _pixels.Color(255, 0, 0); break;
            case SLED_Run:   color = _pixels.Color(0, 255, 0); break;
        }
        _pixels.fill(color);
        _pixels.show();
    }
};
