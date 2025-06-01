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
    bno = BNO08X_I2C(i2c)
    print("BNO08X initialized successfully")
except Exception as e:
    print(f"Failed to initialize BNO08X: {e}")
    traceback.print_exc()
    raise

# センサー機能の有効化
def enable_sensor_feature(feature, feature_name):
    try:
        bno.enable_feature(feature)
        print(f"{feature_name} enabled successfully")
        return True
    except RuntimeError as e:
        print(f"Error enabling {feature_name}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error enabling {feature_name}: {e}")
        traceback.print_exc()
        return False

# 各センサー機能を有効化
features = [
    (BNO_REPORT_ACCELEROMETER, "Accelerometer"),
    # (BNO_REPORT_GYROSCOPE, "Gyroscope"),
    # (BNO_REPORT_MAGNETOMETER, "Magnetometer"),
    # (BNO_REPORT_ROTATION_VECTOR, "Rotation Vector"),
]

enabled_features = {}
for feature, name in features:
    enabled_features[name] = enable_sensor_feature(feature, name)

print("Enabled features:", enabled_features)

# メインループ
while True:
    # time.sleep(0.2)
    try:
        # データ取得
        accel_x, accel_y, accel_z = bno.acceleration

        # 起動からの経過秒数（ミリ秒まで）
        now = time.monotonic()  # 起動からの秒数（float）
        # 加速度データのみ出力（CSV形式）
        print(f"{now:.3f}", end=",")
        print(f"{accel_x:.6f},{accel_y:.6f},{accel_z:.6f}")
    except RuntimeError as e:
        print(f"Error reading sensor data: {e}")
    except Exception as e:
        print(f"Unexpected error reading sensor data: {e}")
        traceback.print_exc()