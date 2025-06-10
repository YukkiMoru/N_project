# BNO085_NEOPIXEL サンプル

このプロジェクトは、Adafruit NeoPixelと自作StatusLEDライブラリを使い、LEDの状態（初期化中・エラー・データ出力中）を色で表示するサンプルです。

## 構成

- `src/main.cpp` : メインスケッチ
- `lib/StatusLED/StatusLED.h`, `StatusLED.cpp` : 状態表示用LEDライブラリ

## 動作概要

- 初期化中はLEDが黄色（オレンジ寄り）
- データ出力中は緑
- エラー時は赤

## 使い方

1. 必要なライブラリ
    - [Adafruit NeoPixel](https://github.com/adafruit/Adafruit_NeoPixel)
    - StatusLED（本リポジトリのlib/StatusLED）
2. `platformio.ini` でボード・ライブラリを設定
3. `PIN_NEOPIXEL` を実際の配線に合わせて定義
4. PlatformIOでビルド＆書き込み

## main.cpp のポイント

```cpp
#include <Arduino.h>
#include <Adafruit_NeoPixel.h>
#include "StatusLED.h"

#define NUMPIXELS 1
Adafruit_NeoPixel pixels(NUMPIXELS, PIN_NEOPIXEL, NEO_GRB + NEO_KHZ800);
StatusLED statusLED(pixels);

void setup() {
  // ...初期化...
  statusLED.setState(StatusLED::Initializing);
  pixels.show();
  delay(1000);
}

void loop() {
  statusLED.setState(StatusLED::Outputting);
  delay(1000);
  statusLED.setState(StatusLED::Error);
  delay(1000);
}
```

## StatusLEDライブラリについて

- `setState(StatusLED::Initializing)` : 初期化中（黄色）
- `setState(StatusLED::Outputting)` : データ出力中（緑）
- `setState(StatusLED::Error)` : エラー（赤）

## 注意
- `PIN_NEOPIXEL` の定義を忘れずに（例: `#define PIN_NEOPIXEL 8`）
- NeoPixelの仕様上、初回の色反映には`delay`や`show()`が必要な場合があります

---

ご質問・不具合はIssueまでどうぞ。
