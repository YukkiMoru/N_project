#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_BNO08x.h>
#include <I2CScannerLib.h> // I2CScannerライブラリ、自作

// BNO08X センサーの初期化
#define BNO08X_RESET -1 // リセットピンを指定 (-1は未使用)
Adafruit_BNO08x bno08x(BNO08X_RESET);

// I2C アドレス
#define BNO08x_I2CADDR_1 0x4A // デフォルトアドレス

// サンプリングレート
uint16_t BNO08X_SAMPLERATE_DELAY_MS = 10; // 10Hzサンプリングレート

// センサーイベントデータ
sh2_SensorValue_t sensorValue;

// 時間管理用
unsigned long lastTime = 0;
unsigned long startTime = 0; // スタート時の時間を記録

// 再初期化関連のグローバル変数
unsigned long lastReinitAttemptTime = 0;
const unsigned long REINIT_COOLDOWN_MS = 5000; // 再初期化試行のクールダウン期間 (5秒)

void setup()
{
  // 1. Start Serial Communication
  while (!Serial)
    delay(10);                                                 // wait for serial port to open!
  Serial.begin(115200);                                        // port Rate of Serial Communication
  Serial.println("[SP]BNO08X Quaternion & Euler Angles Test"); // Test 1 から変更

  Wire1.begin();          // use secondary I2C bus
  Wire1.setClock(400000); // Set I2C clock speed to 400kHz
  // delay(1000); // Removed, bno08x.begin_I2C will handle necessary waits or checks

  // Initialize BNO08x sensor
  Serial.println("[SP]Initializing BNO08x...");
  if (!bno08x.begin_I2C(BNO08x_I2CADDR_1, &Wire1))
  {
    Serial.println("[SP]Failed to find BNO08x chip. Check wiring, I2C address, and pull-up resistors.");
    Serial.println("[SP]Ensure BNO08x is properly powered and connected to Wire1 (SDA1/SCL1).");
    while (1)
    {
      delay(10); // Halt execution
    }
  }
  Serial.println("[SP]BNO08x Found and Initialized!");

  Serial.println("[SP]Setting up sensor reports...");
  // Enable the Accelerometer report.
  // The interval BNO08X_SAMPLERATE_DELAY_MS (10ms) corresponds to 100Hz.
  if (!bno08x.enableReport(SH2_ACCELEROMETER, BNO08X_SAMPLERATE_DELAY_MS))
  {
    Serial.println("[SP]Could not enable accelerometer report. Check sensor state.");
    while (1)
    {
      delay(10); // Halt execution
    }
  }
  Serial.println("[SP]ACCELEROMETER report enabled successfully.");

  delay(10);
  lastTime = millis();  // Initialize lastTime for the loop's timing mechanism
  startTime = millis(); // スタート時の時間を記録
}

// BNO08xセンサーの再初期化を試みる関数
void attemptReinitialization()
{
  Serial.println("[SP]Attempting to reinitialize BNO08x...");
  if (!bno08x.begin_I2C(BNO08x_I2CADDR_1, &Wire1))
  {
    Serial.println("[SP]Failed to reinitialize BNO08x chip. Check wiring, I2C address, and pull-up resistors.");
    // 再初期化失敗。lastReinitAttemptTime は更新しない（次の試行はすぐには行わない）。
    return;
  }
  Serial.println("[SP]BNO08x Reinitialized!");

  if (!bno08x.enableReport(SH2_ACCELEROMETER, BNO08X_SAMPLERATE_DELAY_MS))
  {
    Serial.println("[SP]Could not enable accelerometer report after reinitialization.");
  }
  else
  {
    Serial.println("[SP]ACCELEROMETER report re-enabled successfully.");
    // センサー通信が再確立されたため、タイミング変数をリセット
    startTime = millis(); // スタート時間を現在の時刻にリセット
    lastTime = startTime; // lastTime もリセットして、次のインターバルチェックを正しく行う
  }
}

void loop()
{
  // 1つのBNO08x(I2C)のみ対応
  if (bno08x.getSensorEvent(&sensorValue)) {
    switch (sensorValue.sensorId) {
      case SH2_ACCELEROMETER:
        Serial.print(millis());
        Serial.print(",");
        Serial.print(sensorValue.un.accelerometer.x, 6);
        Serial.print(",");
        Serial.print(sensorValue.un.accelerometer.y, 6);
        Serial.print(",");
        Serial.println(sensorValue.un.accelerometer.z, 6);
        break;
      default:
        Serial.print("BNO08x - Unknown sensor ID: ");
        Serial.println(sensorValue.sensorId);
        break;
    }
  }
  // サンプリング間隔を維持
  delay(1);
}
