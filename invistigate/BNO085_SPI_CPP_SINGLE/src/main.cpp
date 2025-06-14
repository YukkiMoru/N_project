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
const int bno08x_cs_pins[] = {5}; // GPIOを使用すると仮定
// , 20, 25, 24, 26, 27, 28, 29
const int NUM_SENSORS = sizeof(bno08x_cs_pins) / sizeof(bno08x_cs_pins[0]);

// BNO08xリセットピン・INTピン定義
#define BNO08X_RESET_PIN 20
#define BNO08X_INT_PIN   25

// BNO08xセンサーオブジェクトの配列
Adafruit_BNO08x bno08x_sensors[NUM_SENSORS] = { Adafruit_BNO08x(BNO08X_RESET_PIN) };

// センサーレポート設定
sh2_SensorId_t reportType = SH2_GEOMAGNETIC_ROTATION_VECTOR;
long reportIntervalUs = 5000; // 5ms

void setup_bno08x(int index) {
  Serial.print("Initializing BNO08x #");
  Serial.println(index);

  // begin_SPIの引数にSPIバスを追加
  if (!bno08x_sensors[index].begin_SPI(bno08x_cs_pins[index], BNO08X_INT_PIN, &SPI)) {
    Serial.print("Failed to find BNO08x #");
    Serial.println(index);
    while (1) {
      delay(10);
    }
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

  // CSピンをOUTPUTに設定し、HIGHに設定 (非選択状態)
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

  // CSVヘッダー出力
  Serial.println("milisec,x,y,z");
}

void loop() {
  sh2_SensorValue_t sensorValue;

  for (int i = 0; i < NUM_SENSORS; i++) {
    if (bno08x_sensors[i].getSensorEvent(&sensorValue)) {
      switch (sensorValue.sensorId) {
        case SH2_GEOMAGNETIC_ROTATION_VECTOR:
          Serial.print(millis());
          Serial.print(",");
          Serial.print(sensorValue.un.rotationVector.real, 6);
          Serial.print(",");
          Serial.print(sensorValue.un.rotationVector.i, 6);
          Serial.print(",");
          Serial.print(sensorValue.un.rotationVector.j, 6);
          Serial.print(",");
          Serial.println(sensorValue.un.rotationVector.k, 6);
          break;
        // 他のセンサータイプのケースも追加可能
        default:
          Serial.print("BNO08x #");
          Serial.print(i);
          Serial.print(" - Unknown sensor ID: ");
          Serial.println(sensorValue.sensorId);
          break;
      }
    }
    // CSピンをHIGHにしてセンサーを非選択 (Adafruitライブラリが内部で処理するはず)
    // digitalWrite(bno08x_cs_pins[i], HIGH);
    
    // センサー間の読み取りに遅延を入れる (オプション)
    // delay(10); 
  }
  delay(1); // 全センサーの読み取り後、少し待機
}
