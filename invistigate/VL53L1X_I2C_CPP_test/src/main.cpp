/* 
VL53L1X 距離センサーモジュール仕様・ピンアサイン
    - 電源電圧: 3.3~5.0V
    - 測距範囲（最小）: 約10cm
    - 測距範囲（最大）: 約400cm（屋内）
    - 光源: 940nm Class 1 レーザー
    - インターフェース: I2C（信号レベル変換回路搭載）
    - はんだ付け不要の完成品モジュール
  内容物・付属品
    - 本体 (AE-VL53L1X)
    - 説明書（本紙）
    - コネクタ付きケーブル 約50cm
  ピンアサイン:
    | 名称   | 機能                 | 配線色   |
    |--------|----------------------|----------|
    | V+     | 3.3~5V 入力          | 赤       |
    | GND    | GND                  | 黒       |
    | SDA    | データ線             | 黄       |
    | SCL    | クロック線           | 緑       |
    | XSHUT  | シャットダウン入力端子| 青       |
    | GPIO   | GPIO（2.8V レベル）  | 紫       |
  https://github.com/adafruit/Adafruit_VL53L1X

CPU: RP2040
https://learn.adafruit.com/adafruit-qt-py-2040/pinouts
*/
/*
GPIO5 -> VL53L1X XSHUT 0
GPIO6 -> VL53L1X XSHUT 1
*/


#include <Arduino.h>
#include <Wire.h>
#include <VL53L1X.h>
#include <StatusLED.h>

#define NUM_SENSORS 2 // センサーの数を定義
VL53L1X sensors[NUM_SENSORS];

#define NUMPIXELS 1
Adafruit_NeoPixel pixels(NUMPIXELS, PIN_NEOPIXEL, NEO_GRB + NEO_KHZ800);
StatusLED statusLED(pixels);

#define XSHUT_0 5 // GPIO5 -> VL53L1X XSHUT 0
#define XSHUT_1 6 // GPIO6 -> VL53L1X XSHUT 1
#define SENSOR_ADDRESSES {0x30, 0x29} // センサーごとのI2Cアドレス（必要に応じて変更）

void applySettings(String mode, int timing, int interval) {
  for (int i = 0; i < NUM_SENSORS; i++) {
    if (mode == "short") {
      sensors[i].setDistanceMode(VL53L1X::Short);
    } else if (mode == "medium") {
      sensors[i].setDistanceMode(VL53L1X::Medium);
    } else if (mode == "long") {
      sensors[i].setDistanceMode(VL53L1X::Long);
    }
    sensors[i].setMeasurementTimingBudget(timing);
    sensors[i].startContinuous(interval);
  }
}

void applySettingsMulti(int idx, String mode, int timing, int interval) {
  if (mode == "short") {
    sensors[idx].setDistanceMode(VL53L1X::Short);
  } else if (mode == "medium") {
    sensors[idx].setDistanceMode(VL53L1X::Medium);
  } else if (mode == "long") {
    sensors[idx].setDistanceMode(VL53L1X::Long);
  }
  sensors[idx].setMeasurementTimingBudget(timing);
  sensors[idx].startContinuous(interval);
}

void setup()
{
  Serial.begin(115200);
  while (!Serial) {
    delay(10); // シリアルポートが開くまで待機
  }
  #if defined(NEOPIXEL_POWER)
    pinMode(NEOPIXEL_POWER, OUTPUT);
    digitalWrite(NEOPIXEL_POWER, HIGH);
  #endif

  pixels.begin();
  pixels.setBrightness(20);
  delay(10); // 初期化の安定化

  Serial.println("Adafruit VL53L1X Example");

  statusLED.setState(StatusLED::Initializing);
  pixels.show(); // 明示的にshowを呼ぶ
  
  Wire.begin();
  Wire.setClock(400000); // use 400 kHz I2C

  const uint8_t addresses[NUM_SENSORS] = SENSOR_ADDRESSES;

  // XSHUTピン初期化
  pinMode(XSHUT_0, OUTPUT);
  pinMode(XSHUT_1, OUTPUT);
  digitalWrite(XSHUT_0, LOW); // まず両方シャットダウン
  digitalWrite(XSHUT_1, LOW);
  delay(10);

  // 1台ずつ順番に有効化・初期化・アドレス設定
  for (int i = 0; i < NUM_SENSORS; i++) {
    if (i == 0) digitalWrite(XSHUT_0, HIGH);
    if (i == 1) digitalWrite(XSHUT_1, HIGH);
    delay(10);
    sensors[i].setTimeout(500);
    if (!sensors[i].init()) {
      Serial.print("Failed to detect and initialize sensor ");
      Serial.println(i);
      statusLED.setState(StatusLED::Error);
      while (1);
    }
    // デフォルトアドレス(0x29)以外なら変更
    if (addresses[i] != 0x29) {
      sensors[i].setAddress(addresses[i]);
    }
  }

  // デフォルト設定（全センサー）
  for (int i = 0; i < NUM_SENSORS; i++) {
    applySettingsMulti(i, "medium", 33000, 33);
  }

  // センサの設定（すべて同じ設定にする）
  bool enabled = false;
  while (!enabled) {
    if (Serial.available()) {
      String cmd = Serial.readStringUntil('\n');
      cmd.trim();
      int idx1 = cmd.indexOf(',');
      int idx2 = cmd.lastIndexOf(',');
      if (idx1 > 0 && idx2 > idx1) {
        String mode = cmd.substring(0, idx1);
        int timing = cmd.substring(idx1 + 1, idx2).toInt();
        int interval = cmd.substring(idx2 + 1).toInt();
        applySettings(mode, timing, interval); // すべてのセンサーに同じ設定を適用
        Serial.println("OK");
        enabled = true;
      }
    }
  }
  delay(1000);
  statusLED.setState(StatusLED::Outputting);
}

void loop()
{
  uint32_t ms = millis();
  for (int i = 0; i < NUM_SENSORS; i++) {
    uint16_t dist = sensors[i].read();
    uint8_t timeout = sensors[i].timeoutOccurred() ? 1 : 0;
    Serial.print(i);
    Serial.print(",");
    Serial.print(ms);
    Serial.print(",");
    if(timeout) {
      Serial.print("NULL");
    } else {
      Serial.print(dist);
    }
    Serial.println();
    if(timeout) {
      Serial.print("Timeout occurred on sensor ");
      Serial.println(i);
      statusLED.setState(StatusLED::Error);
    }
  }
  delay(5); // 追加: 1ms待つことでバッファオーバーフロー防止
}
