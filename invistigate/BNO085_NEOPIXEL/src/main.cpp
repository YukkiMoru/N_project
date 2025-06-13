#include <Arduino.h>
#include <SmartLED.h>

SmartLED statusLED;

void setup() {
  Serial.begin(115200);

  statusLED.setState(SLED_Init);
  delay(1000);
}

void loop() {
  statusLED.setState(SLED_Run);
  delay(1000);
  statusLED.setState(SLED_Error);
  delay(1000);
  Serial.println("reset");
}