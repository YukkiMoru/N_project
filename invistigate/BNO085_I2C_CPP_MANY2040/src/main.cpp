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
  Wire1.setClock(100000); // Set I2C clock speed to 400kHz
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
  // Enable the Rotation Vector report.
  // The interval BNO08X_SAMPLERATE_DELAY_MS (20ms) corresponds to 50Hz.
  if (!bno08x.enableReport(SH2_LINEAR_ACCELERATION, BNO08X_SAMPLERATE_DELAY_MS))
  {
    Serial.println("[SP]Could not enable rotation vector report. Check sensor state.");
    while (1)
    {
      delay(10); // Halt execution
    }
  }
  Serial.println("[SP]LINEAR ACCELERATION report enabled successfully.");

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

  if (!bno08x.enableReport(SH2_LINEAR_ACCELERATION, BNO08X_SAMPLERATE_DELAY_MS))
  {
    Serial.println("[SP]Could not enable rotation vector report after reinitialization.");
  }
  else
  {
    Serial.println("[SP]LINEAR ACCELERATION report re-enabled successfully.");
    // センサー通信が再確立されたため、タイミング変数をリセット
    startTime = millis(); // スタート時間を現在の時刻にリセット
    lastTime = startTime; // lastTime もリセットして、次のインターバルチェックを正しく行う
  }
}

void loop()
{
  unsigned long currentMillis = millis();                          // ループ開始時の現在時刻を取得
  unsigned long currentTimeForPayload = currentMillis - startTime; // データペイロード用のタイムスタンプ (スタート/再初期化からの経過時間)

  // サンプリング時間かどうかを確認
  if ((currentMillis - lastTime) >= BNO08X_SAMPLERATE_DELAY_MS)
  {
    lastTime = currentMillis; // 次のインターバルのために lastTime を更新

    // センサーデータの取得
    if (bno08x.getSensorEvent(&sensorValue))
    {
      if (sensorValue.sensorId == SH2_LINEAR_ACCELERATION) // ←ここを変更
      {
        float timestamp_f = (float)currentTimeForPayload; // currentTimeForPayload を使用
        float val_1 = sensorValue.un.linearAcceleration.x;    // x軸加速度
        float val_2 = sensorValue.un.linearAcceleration.y; // y軸加速度
        float val_3 = sensorValue.un.linearAcceleration.z; // z軸加速度
        // float z_val = 0.0f; // リニア加速度にはw成分はないので0で埋める

        Serial.printf("%.2f,%.6f,%.6f,%.6f\n", timestamp_f, val_1, val_2, val_3);
      }
    } else
    {
      // センサーデータの取得に失敗
      if (currentMillis - lastReinitAttemptTime > REINIT_COOLDOWN_MS)
      {
        Serial.println("[SP]Failed to get sensor event. Cooldown passed, attempting reinitialization.");
        lastReinitAttemptTime = currentMillis; // 再初期化試行時刻を更新
        attemptReinitialization();
      }
    }
  }
}
