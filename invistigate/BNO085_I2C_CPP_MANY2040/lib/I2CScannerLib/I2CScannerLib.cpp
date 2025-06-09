\
#include "I2CScannerLib.h"

bool i2cScanner() {
  Serial.println("[SP]Scanning...");

  int devicesFound = 0;
  uint8_t connectedDevice = 0;
  for (uint8_t address = 1; address < 127; address++) {
    Wire1.beginTransmission(address);
    if (Wire1.endTransmission() == 0) {
      Serial.print("[SP]I2C device found at address 0x");
      Serial.println(address, HEX);
      devicesFound++;
      connectedDevice = address; // Store the last connected device address
    }
  }

  if (devicesFound == 0) {
    Serial.println("[SP]No I2C devices found");
    return false;
  } else {
    Serial.print("[SP]Total devices found: ");
    Serial.println(devicesFound);
    Serial.print("[SP]Connected device address: 0x");
    Serial.println(connectedDevice, HEX);
    return true;
  }
}
