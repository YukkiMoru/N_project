import time
import board
import busio
import traceback
import struct
from adafruit_bno08x import (
    BNO_REPORT_ACCELEROMETER,
    BNO_REPORT_GYROSCOPE,
    BNO_REPORT_MAGNETOMETER,
    BNO_REPORT_ROTATION_VECTOR,
)
from adafruit_bno08x.i2c import BNO08X_I2C

# I2Cの初期化
i2c = busio.I2C(board.SCL1, board.SDA1, frequency=400000)

# センサーの初期化
try:
    bno1 = BNO08X_I2C(i2c, address=0x4A)  # 1台目のセンサー
    bno2 = BNO08X_I2C(i2c, address=0x4B)  # 2台目のセンサー
except Exception as e:
    raise

# Custom checksum calculation function
def calculate_checksum(data):
    """Calculate a simple checksum by summing the byte values."""
    return sum(data) & 0xFFFFFFFF  # Ensure it fits in 4 bytes

# センサー機能の有効化
def enable_sensor_feature(sensor, feature, feature_name):
    try:
        sensor.enable_feature(feature)
        return True
    except RuntimeError as e:
        return False
    except Exception as e:
        traceback.print_exc()
        return False

# 各センサーの機能を有効化
features = [
    (BNO_REPORT_ACCELEROMETER, "Accelerometer"),
]

enabled_features_1 = {}
enabled_features_2 = {}
for feature, name in features:
    enabled_features_1[name] = enable_sensor_feature(bno1, feature, name)
    enabled_features_2[name] = enable_sensor_feature(bno2, feature, name)

def send_binary_data(sensor_id, accel_x, accel_y, accel_z):
    """センサーID、タイムスタンプ（ミリ秒単位）、加速度データを送信"""
    try:
        timestamp_ms = int(time.time() * 1000)  # 現在のタイムスタンプをミリ秒単位で取得
        header = b'HEAD'  # 固定ヘッダー
        packed_data = struct.pack('<4sBIf3f', header, sensor_id, timestamp_ms, accel_x, accel_y, accel_z)  # ヘッダーを含むデータをパック
        checksum = calculate_checksum(packed_data)  # Custom checksum calculation
        final_data = packed_data + struct.pack('<I', checksum)  # チェックサムを追加
        ser.write(final_data)  # シリアルポートを使用してデータを送信
    except Exception as e:
        print(f"[ERROR] Failed to send data: {e}")

def process_sensor_data(sensor, sensor_id):
    """センサーからデータを取得し、バイナリデータを送信"""
    try:
        accel_x, accel_y, accel_z = sensor.acceleration
        send_binary_data(sensor_id, accel_x, accel_y, accel_z)  # バイナリデータ送信
    except RuntimeError:
        print(f"[WARNING] Runtime error while processing sensor {sensor_id}")
    except Exception as e:
        print(f"[ERROR] General error while processing sensor {sensor_id}: {e}")

# センサーの初期化が成功したらBINARY COMを送信
try:
    print("[INFO] Sensors initialized successfully.")
    # BINARY COMを送信
    print("BINARY COM")
    # 実際の送信処理をここに追加（例: シリアル通信で送信）
except Exception as e:
    print(f"[ERROR] Failed to send BINARY COM: {e}")
    raise

# メインループ
while True:
    process_sensor_data(bno1, 1)  # 1台目のセンサー処理
    process_sensor_data(bno2, 2)  # 2台目のセンサー処理
    time.sleep(0.01)  # データ取得間隔
