# ラウンドなし 制限機能有 
import time
import board
import busio
import traceback
import sys
import struct
from adafruit_bno08x import (
  BNO_REPORT_ACCELEROMETER,
  BNO_REPORT_GYROSCOPE,
  BNO_REPORT_MAGNETOMETER,
  BNO_REPORT_ROTATION_VECTOR,
)
from adafruit_bno08x.i2c import BNO08X_I2C

# CRC16-CCITT (0x1021, 初期値0xFFFF)
def crc16_ccitt(data: bytes, poly=0x1021, init=0xFFFF) -> int:
  crc = init
  for b in data:
    crc ^= b << 8
    for _ in range(8):
      if crc & 0x8000:
        crc = (crc << 1) ^ poly
      else:
        crc <<= 1
      crc &= 0xFFFF
  return crc

# I2Cの初期化
i2c = busio.I2C(board.SCL1, board.SDA1, frequency=100000)

# センサーの初期化
try:
  bno = BNO08X_I2C(i2c)
  # BNO08X initialized successfully
except Exception as e:
  # Failed to initialize BNO08X
  traceback.print_exc()
  raise

# センサー機能の有効化
def enable_sensor_feature(feature, feature_name):
  try:
    bno.enable_feature(feature)
    # Feature enabled successfully
    return True
  except RuntimeError as e:
    # Error enabling feature
    return False
  except Exception as e:
    # Unexpected error enabling feature
    traceback.print_exc()
    return False

# 各センサー機能の有効/無効設定（True/False）
USE_ACCELEROMETER = False
USE_GYROSCOPE = False
USE_MAGNETOMETER = False
USE_ROTATION_VECTOR = True

# 有効にする機能をリストに追加
features = []
if USE_ACCELEROMETER:
    features.append((BNO_REPORT_ACCELEROMETER, "Accelerometer"))
if USE_GYROSCOPE:
    features.append((BNO_REPORT_GYROSCOPE, "Gyroscope"))
if USE_MAGNETOMETER:
    features.append((BNO_REPORT_MAGNETOMETER, "Magnetometer"))
if USE_ROTATION_VECTOR:
    features.append((BNO_REPORT_ROTATION_VECTOR, "Rotation Vector"))

enabled_features = {}
for feature, name in features:
    enabled_features[name] = enable_sensor_feature(feature, name)

HEADER = b'\xAA\x55'  # 2バイトの開始シンボル

# メインループ上部に追加
TARGET_RATE = 10  # 目標サンプリングレート (Hz)
SAMPLE_INTERVAL = 1.0 / TARGET_RATE  # 秒単位の間隔

# メインループ
while True:
  start_time = time.monotonic()
  try:
    # センサーのエラーチェックと再初期化
    if not bno:
        try:
            bno = BNO08X_I2C(i2c)
        except Exception as e:
            print(f"Error reinitializing sensor: {e}", file=sys.stderr)
            continue

    # 有効な機能のデータのみ取得
    now = start_time
    
    # 条件分岐を削減し、事前に確認された機能のみを取得
    accel_x, accel_y, accel_z = bno.acceleration if USE_ACCELEROMETER and enabled_features.get("Accelerometer") else (0, 0, 0)
    gyro_x, gyro_y, gyro_z = bno.gyro if USE_GYROSCOPE and enabled_features.get("Gyroscope") else (0, 0, 0)
    mag_x, mag_y, mag_z = bno.magnetic if USE_MAGNETOMETER and enabled_features.get("Magnetometer") else (0, 0, 0)
    quat_i, quat_j, quat_k, quat_real = bno.quaternion if USE_ROTATION_VECTOR and enabled_features.get("Rotation Vector") else (0, 0, 0, 1)

    # データをバイナリ形式でパックして出力
    data_bytes = struct.pack("<14f",
      now,
      accel_x, accel_y, accel_z,
      gyro_x, gyro_y, gyro_z,
      mag_x, mag_y, mag_z,
      quat_i, quat_j, quat_k, quat_real)
    crc = crc16_ccitt(data_bytes)
    data_bytes = HEADER + data_bytes + struct.pack('<H', crc)
    sys.stdout.write(data_bytes)
    
    # 処理時間を測定し、目標レートを維持
    elapsed = time.monotonic() - start_time
    if elapsed < SAMPLE_INTERVAL:
        time.sleep(SAMPLE_INTERVAL - elapsed)
        
  except RuntimeError as e:
    print(f"Error reading sensor data: {e}", file=sys.stderr)
  except Exception as e:
    print(f"Unexpected error: {type(e).__name__}: {e}", file=sys.stderr)
    try:
      if hasattr(e, '__traceback__'):
        traceback.print_exception(type(e), e, e.__traceback__, file=sys.stderr)
      else:
        print("(Full traceback not available or traceback module limited)", file=sys.stderr)
    except Exception as te:
      print(f"(Error during traceback printing: {te})", file=sys.stderr)
