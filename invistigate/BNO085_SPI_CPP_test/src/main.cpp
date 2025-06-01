// https://learn.adafruit.com/adafruit-qt-py-2040/pinouts
#include <Arduino.h>
#include <Adafruit_BNO08x.h>
#include <SPI.h>

// SPIピン定義 (GPIO 3, 4, 6 を使用)
#define BNO08X_SPI_SCK  6  // GP6 for SCK
#define BNO08X_SPI_MOSI 3  // GP3 for MOSI (TX)
#define BNO08X_SPI_MISO 4  // GP4 for MISO (RX)

// BNO08xセンサーのCSピン定義 (8個分)
// 使用するGPIOピンに合わせて変更してください
const uint8_t bno08x_cs_pins[] = {5}; // GPIOを使用すると仮定
// 5, 20, 25, 24, 26, 27, 28, 29
const int NUM_SENSORS = sizeof(bno08x_cs_pins) / sizeof(bno08x_cs_pins[0]);

// BNO08xリセットピン・INTピン定義
#define BNO08X_RESET_PIN 25
#define BNO08X_INT_PIN   20

// BNO08xセンサーオブジェクトの配列
Adafruit_BNO08x bno08x_sensors[NUM_SENSORS] = { Adafruit_BNO08x(BNO08X_RESET_PIN) };

// センサーレポート設定
sh2_SensorId_t reportType = SH2_ACCELEROMETER;
long reportIntervalUs = 5000; // 5ms

void setup_bno08x(int index) {
  Serial.print("Initializing BNO08x #");
  Serial.println(index);

  // begin_SPIの引数にSPIバスを追加
  if (!bno08x_sensors[index].begin_SPI(bno08x_cs_pins[index], BNO08X_INT_PIN, &SPI)) {
    Serial.print("Failed to find BNO08x #");
    Serial.println(index);
    return ; // 初期化失敗時は関数を終了
    // while (1) {
    //   delay(10);
    // }
  }
  Serial.print("BNO08x #");
  Serial.print(index);
  Serial.println(" found!");

  Serial.print("Setting desired reports for BNO08x #");
  Serial.println(index);
  if (!bno08x_sensors[index].enableReport(reportType, reportIntervalUs)) {
    Serial.print("Could not enable accelerometer for BNO08x #");
    Serial.println(index);
  }
  delay(100); // センサーがレポートを開始するのを待つ
}

void setup() {
  Serial.begin(115200);
  while (!Serial) {
    delay(10); // シリアルポートが開くまで待機
  }
  Serial.println("Adafruit BNO08x SPI test");
  Serial.print("Connecting to ");
  Serial.print(NUM_SENSORS);
  Serial.println(" sensors...");

  // SPI通信の初期化 (CSピンより前に行うのが一般的)
  // 指定されたGPIOピンにSPI機能を割り当てる
  SPI.setRX(BNO08X_SPI_MISO); // MISOをGP4に設定
  SPI.setTX(BNO08X_SPI_MOSI); // MOSIをGP3に設定
  SPI.setSCK(BNO08X_SPI_SCK); // SCKをGP6に設定
  SPI.begin(); // SPIバスを初期化

  // CSピンをOUTPUTに設定
  for (int i = 0; i < NUM_SENSORS; i++) {
    Serial.println( bno08x_cs_pins[i]);
    pinMode(bno08x_cs_pins[i], OUTPUT);
    digitalWrite(bno08x_cs_pins[i], HIGH);
  }

  // 各センサーを初期化
  for (int i = 0; i < NUM_SENSORS; i++) {
    bno08x_sensors[i] = Adafruit_BNO08x(BNO08X_RESET_PIN);
    setup_bno08x(i);
    delay(100); // 次のセンサーの初期化前に少し待機
  }

  Serial.println("All sensors initialized.");
}

void loop() {
  sh2_SensorValue_t sensorValue;
  unsigned long now_ms = millis();
  for (int i = 0; i < NUM_SENSORS; i++) {

    if (bno08x_sensors[i].getSensorEvent(&sensorValue)) {
      Serial.print("Millis: ");
      Serial.print(now_ms);
      Serial.print(" ");
      switch (sensorValue.sensorId) {
      case SH2_ACCELEROMETER:
        Serial.print("BNO08x #");
        Serial.print(i);
        Serial.print(" - Accel - X: ");
        Serial.print(sensorValue.un.accelerometer.x);
        Serial.print(" Y: ");
        Serial.print(sensorValue.un.accelerometer.y);
        Serial.print(" Z: ");
        Serial.print(sensorValue.un.accelerometer.z);
        Serial.print(" [sensorId: ");
        Serial.print(sensorValue.sensorId);
        Serial.println("]");
        break;
      default:
        Serial.print("BNO08x #");
        Serial.print(i);
        Serial.print(" - Unknown sensor ID: ");
        Serial.println(sensorValue.sensorId);
        break;
      }
    } else {
      // Serial.print("No data from BNO08x #");
      // Serial.println(i);
    }
    // CSピンをHIGHにしてセンサーを非選択 (Adafruitライブラリが内部で処理するはず)
    // digitalWrite(bno08x_cs_pins[i], HIGH);
    
    // センサー間の読み取りに遅延を入れる (オプション)
    // delay(10); 
  }
  delay(1); // 全センサーの読み取り後、少し待機
}
