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

# センサーの初期化
try:
    bno1 = BNO08X_I2C(i2c, address=0x4A)  # 1台目のセンサー (例: アドレス0x4A)
    print("BNO08X (1) initialized successfully at address 0x4A")
    bno2 = BNO08X_I2C(i2c, address=0x4B)  # 2台目のセンサー (例: アドレス0x4B)
    print("BNO08X (2) initialized successfully at address 0x4B")
except Exception as e:
    print(f"Failed to initialize BNO08X: {e}")
    traceback.print_exc()
    raise

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

enabled_features_1 = {}
enabled_features_2 = {}
for feature, name in features:
    enabled_features_1[name] = enable_sensor_feature(bno1, feature, name)
    enabled_features_2[name] = enable_sensor_feature(bno2, feature, name)

print("Enabled features for BNO08X (1):", enabled_features_1)
print("Enabled features for BNO08X (2):", enabled_features_2)

# メインループ
while True:
    try:
        # 1台目のセンサーからデータ取得
        accel_x1, accel_y1, accel_z1 = bno1.acceleration
        now1 = time.monotonic()
        print(f"Sensor 1: {now1:.3f},{accel_x1:.6f},{accel_y1:.6f},{accel_z1:.6f}")

        # 2台目のセンサーからデータ取得
        accel_x2, accel_y2, accel_z2 = bno2.acceleration
        now2 = time.monotonic()
        print(f"Sensor 2: {now2:.3f},{accel_x2:.6f},{accel_y2:.6f},{accel_z2:.6f}")

        time.sleep(0.01)  # データ取得間隔
    except RuntimeError as e:
        print(f"Error reading sensor data: {e}")
    except Exception as e:
        print(f"Unexpected error reading sensor data: {e}")
        traceback.print_exc()
