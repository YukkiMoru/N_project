#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#include <StatusLED.h>

#define NUMPIXELS 1

Adafruit_NeoPixel pixels(NUMPIXELS, PIN_NEOPIXEL, NEO_GRB + NEO_KHZ800);
StatusLED statusLED(pixels);

void setup() {
  Serial.begin(115200);

#if defined(NEOPIXEL_POWER)
  pinMode(NEOPIXEL_POWER, OUTPUT);
  digitalWrite(NEOPIXEL_POWER, HIGH);
#endif

  pixels.begin();
  pixels.setBrightness(20);
  delay(10); // 初期化の安定化
  statusLED.setState(StatusLED::Initializing);
  pixels.show(); // 明示的にshowを呼ぶ
  delay(1000);
}

void loop() {
  statusLED.setState(StatusLED::Outputting);
  delay(1000);
  statusLED.setState(StatusLED::Error);
  delay(1000);
  Serial.println("reset");
}