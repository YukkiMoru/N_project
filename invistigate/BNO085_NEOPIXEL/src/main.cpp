#include <Arduino.h>
#include <Adafruit_NeoPixel.h>

#define NUMPIXELS 1

Adafruit_NeoPixel pixels(NUMPIXELS, PIN_NEOPIXEL, NEO_GRB + NEO_KHZ800);

void setup() {
  Serial.begin(115200);

#if defined(NEOPIXEL_POWER)
  pinMode(NEOPIXEL_POWER, OUTPUT);
  digitalWrite(NEOPIXEL_POWER, HIGH);
#endif

  pixels.begin();
  pixels.setBrightness(20);
}

void loop() {
  Serial.println("Hello!");
  pixels.fill(0x0000FF); // 赤
  pixels.show();
  delay(500);

  pixels.fill(0x000000); // 消灯
  pixels.show();
  delay(500);
}