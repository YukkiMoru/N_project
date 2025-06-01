import time
import board
import busio
from adafruit_bno08x import BNO_REPORT_ACCELEROMETER
from adafruit_bno08x.i2c import BNO08X_I2C

# I2Cの初期化
i2c = busio.I2C(board.SCL1, board.SDA1, frequency=400000)

# デバッグモードのフラグ
debug_mode = False

# マルチプレクサのチャンネル選択用関数
def pcaselect(channel):
    if channel > 7:
        return  # チャンネルが範囲外の場合は何もしない
    if not i2c.try_lock():
        if debug_mode:
            print("Failed to acquire I2C lock for pcaselect")
        return
    try:
        i2c.writeto(0x70, bytes([1 << channel]))  # マルチプレクサのアドレスは0x70
    finally:
        i2c.unlock()

# センサーの初期化
def initialize_sensor(channel):
    try:
        pcaselect(channel)
        sensor = BNO08X_I2C(i2c, address=0x4A, debug=debug_mode)
        if debug_mode:
            print(f"Sensor initialized on channel {channel}")

        # 加速度機能を有効化
        sensor.enable_feature(BNO_REPORT_ACCELEROMETER)
        if debug_mode:
            print("Accelerometer feature enabled.")

        return sensor
    except Exception as e:
        if debug_mode:
            print(f"Failed to initialize sensor on channel {channel}: {e}")
        return None

# センサーのリセット
def reset_sensor(sensor):
    try:
        sensor.soft_reset()
        if debug_mode:
            print("Sensor reset successfully.")
    except Exception as e:
        if debug_mode:
            print(f"Failed to reset sensor: {e}")

# メインループ
if __name__ == "__main__":
    channel = 0  # 使用するチャンネルを指定
    sensor = initialize_sensor(channel)
    if sensor is None:
        print("Sensor initialization failed. Exiting.")
        exit(1)

    while True:
        try:
            accel = sensor.acceleration
            print(f"Acceleration: x={accel[0]:.6f}, y={accel[1]:.6f}, z={accel[2]:.6f}")
        except RuntimeError as e:
            if debug_mode:
                print(f"Runtime error: {e}")
            if "No accel report found" in str(e):
                if debug_mode:
                    print("Attempting to reset sensor...")
                reset_sensor(sensor)
        except Exception as e:
            if debug_mode:
                print(f"Unexpected error: {e}")
        # time.sleep(0.5)