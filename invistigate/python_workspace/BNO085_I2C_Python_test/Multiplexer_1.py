import time
import board
import busio
import traceback
from adafruit_bno08x import (
    BNO_REPORT_ACCELEROMETER,
    BNO_REPORT_GYROSCOPE,
    BNO_REPORT_MAGNETOMETER,
    BNO_REPORT_ROTATION_VECTOR,
)
from adafruit_bno08x.i2c import BNO08X_I2C

# I2Cの初期化
i2c = busio.I2C(board.SCL1, board.SDA1, frequency=400000)

# マルチプレクサのチャンネル選択用関数
def pcaselect(channel):
    if channel > 7:
        return  # チャンネルが範囲外の場合は何もしない
    for _ in range(3):  # 最大3回リトライ
        if i2c.try_lock():
            try:
                i2c.writeto(0x70, bytes([1 << channel]))  # マルチプレクサのアドレスは0x70
                return
            finally:
                i2c.unlock()
        time.sleep(0.1)  # ロック取得失敗時に待機
    print(f"Failed to acquire I2C lock for pcaselect on channel {channel}")

# デバッグ用ログを追加
print("Starting sensor initialization...")

# センサーの初期化
sensors = []
for channel in range(8):
    print(f"Initializing sensors on channel {channel}...")
    for attempt in range(3):  # 最大3回リトライ
        try:
            print(f"Selecting channel {channel}, attempt {attempt + 1}...")
            pcaselect(channel)
            if not i2c.try_lock():
                print(f"Failed to acquire I2C lock for sensor initialization on channel {channel}, attempt {attempt + 1}")
                time.sleep(0.1)
                continue
            try:
                print(f"Attempting to initialize sensor1 on channel {channel} with address 0x4A...")
                sensor1 = BNO08X_I2C(i2c, address=0x4A)  # アドレス0x4Aのセンサー
                print(f"Sensor1 initialized successfully on channel {channel}.")

                print(f"Attempting to initialize sensor2 on channel {channel} with address 0x4B...")
                sensor2 = BNO08X_I2C(i2c, address=0x4B)  # アドレス0x4Bのセンサー
                print(f"Sensor2 initialized successfully on channel {channel}.")

                sensors.append((sensor1, sensor2))
                print(f"Sensors initialized on channel {channel}")
                break
            finally:
                i2c.unlock()
        except Exception as e:
            print(f"Failed to initialize sensors on channel {channel}, attempt {attempt + 1}: {e}")
            traceback.print_exc()
        time.sleep(0.1)
    else:
        print(f"Giving up on initializing sensors on channel {channel} after 3 attempts")

print("Sensor initialization complete.")

# センサー機能の有効化
def enable_sensor_feature(sensor, feature, feature_name):
    try:
        sensor.enable_feature(feature)
        print(f"{feature_name} enabled successfully")
        return True
    except RuntimeError as e:
        print(f"Error enabling {feature_name}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error enabling {feature_name}: {e}")
        traceback.print_exc()
        return False

# 各センサーの機能を有効化
features = [
    (BNO_REPORT_ACCELEROMETER, "Accelerometer"),
]

enabled_features = {}
for channel, (sensor1, sensor2) in enumerate(sensors):
    for feature, name in features:
        enabled_features[(channel, name)] = enable_sensor_feature(sensor1, feature, name)

# 有効化された機能の表示
for (channel, name), status in enabled_features.items():
    print(f"Channel {channel} - {name}: {'Enabled' if status else 'Failed to enable'}")

# メインループ
while True:
    for channel, (sensor1, sensor2) in enumerate(sensors):
        try:
            pcaselect(channel)
            if not sensor1._data_ready or not sensor2._data_ready:
                print(f"No data ready on channel {channel}")
                continue
            accel1 = sensor1._read_packet()
            accel2 = sensor2._read_packet()
            now = time.monotonic()
            print(f"Channel {channel} - Sensor 1: {now:.3f},{accel1[0]:.6f},{accel1[1]:.6f},{accel1[2]:.6f}")
            print(f"Channel {channel} - Sensor 2: {now:.3f},{accel2[0]:.6f},{accel2[1]:.6f},{accel2[2]:.6f}")
        except RuntimeError as e:
            print(f"Runtime error on channel {channel}: {e}")
        except Exception as e:
            print(f"Unexpected error on channel {channel}: {e}")
    time.sleep(0.1)
