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
    if not i2c.try_lock():
        print("Failed to acquire I2C lock for pcaselect")
        return
    try:
        i2c.writeto(0x70, bytes([1 << channel]))  # マルチプレクサのアドレスは0x70
    finally:
        i2c.unlock()

# センサーの初期化
sensors = []
for channel in range(8):
    try:
        pcaselect(channel)
        if not i2c.try_lock():
            print(f"Failed to acquire I2C lock for sensor initialization on channel {channel}")
            continue
        try:
            sensor1 = BNO08X_I2C(i2c, address=0x4A)  # アドレス0x4Aのセンサー
            sensor2 = BNO08X_I2C(i2c, address=0x4B)  # アドレス0x4Bのセンサー
            sensors.append((sensor1, sensor2))
            print(f"Sensors initialized on channel {channel}")
        finally:
            i2c.unlock()
    except Exception as e:
        print(f"Failed to initialize sensors on channel {channel}: {e}")

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
            accel1 = sensor1.acceleration
            accel2 = sensor2.acceleration
            now = time.monotonic()
            print(f"Channel {channel} - Sensor 1: {now:.3f},{accel1[0]:.6f},{accel1[1]:.6f},{accel1[2]:.6f}")
            print(f"Channel {channel} - Sensor 2: {now:.3f},{accel2[0]:.6f},{accel2[1]:.6f},{accel2[2]:.6f}")
        except RuntimeError as e:
            print(f"Runtime error on channel {channel}: {e}")
        except Exception as e:
            print(f"Unexpected error on channel {channel}: {e}")
    time.sleep(0.1)
