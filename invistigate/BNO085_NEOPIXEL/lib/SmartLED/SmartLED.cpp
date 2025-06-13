#include "SmartLED.h"

SmartLED::SmartLED(Adafruit_NeoPixel& pixels) : _pixels(pixels), _state(Initializing) {
    update();
}

void SmartLED::setState(State state) {
    if (_state != state) {
        _state = state;
        update();
    }
}

void SmartLED::update() {
    uint32_t color = 0;
    switch (_state) {
        case Initializing:
            color = _pixels.Color(255, 80, 0); // オレンジ寄りの黄色
            break;
        case Error:
            color = _pixels.Color(255, 0, 0); // 赤
            break;
        case Outputting:
            color = _pixels.Color(0, 255, 0); // 緑
            break;
    }
    _pixels.fill(color);
    _pixels.show();
}
