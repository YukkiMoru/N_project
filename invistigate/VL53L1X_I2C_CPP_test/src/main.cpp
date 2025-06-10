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

#include <Arduino.h>
#include <Wire.h>
#include <VL53L1X.h>

VL53L1X sensor;

void applySettings(String mode, int timing, int interval) {
  if (mode == "short") {
    sensor.setDistanceMode(VL53L1X::Short);
  } else if (mode == "medium") {
    sensor.setDistanceMode(VL53L1X::Medium);
  } else if (mode == "long") {
    sensor.setDistanceMode(VL53L1X::Long);
  }
  sensor.setMeasurementTimingBudget(timing);
  sensor.startContinuous(interval);
}

void setup()
{
  Serial.begin(115200);
  while (!Serial) {
    delay(10); // シリアルポートが開くまで待機
  }
  Serial.println("Adafruit VL53L1X Example");
  Wire.begin();
  Wire.setClock(400000); // use 400 kHz I2C

  sensor.setTimeout(500);
  if (!sensor.init())
  {
    Serial.println("Failed to detect and initialize sensor!");
    while (1);
  }

  // デフォルト設定
  applySettings("medium", 33000, 33);

  // センサの設定
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
        applySettings(mode, timing, interval);
        Serial.println("OK");
        enabled = true;
        delay(1000); // 追加: 設定完了後に1秒待つ
      }
    }
  }
  delay(3000);
}

void loop()
{
  uint32_t ms = millis();
  uint16_t dist = sensor.read();
  uint8_t timeout = sensor.timeoutOccurred() ? 1 : 0;
  Serial.print(ms);
  Serial.print(",");
  Serial.print(dist);
  Serial.print(",");
  Serial.println(timeout);
  delay(1); // 追加: 1ms待つことでバッファオーバーフロー防止
}
