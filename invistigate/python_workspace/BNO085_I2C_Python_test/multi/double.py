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
def initialize_sensor(channel, address):
    try:
        pcaselect(channel)
        sensor = BNO08X_I2C(i2c, address=address, debug=debug_mode)
        if debug_mode:
            print(f"Sensor initialized on channel {channel} at address {hex(address)}")

        # 加速度機能を有効化
        sensor.enable_feature(BNO_REPORT_ACCELEROMETER)
        if debug_mode:
            print("Accelerometer feature enabled.")

        return sensor
    except Exception as e:
        if debug_mode:
            print(f"Failed to initialize sensor on channel {channel} at address {hex(address)}: {e}")
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
    sensor1 = initialize_sensor(channel, 0x4A)  # 1台目のセンサー
    sensor2 = initialize_sensor(channel, 0x4B)  # 2台目のセンサー

    if sensor1 is None or sensor2 is None:
        print("One or both sensors failed to initialize. Exiting.")
        exit(1)

    while True:
        try:
            # 1台目のセンサーからデータ取得
            accel1 = sensor1.acceleration
            now1 = time.monotonic()
            print(f"Sensor 1: {now1:.3f},{accel1[0]:.6f},{accel1[1]:.6f},{accel1[2]:.6f}")

            # 2台目のセンサーからデータ取得
            accel2 = sensor2.acceleration
            now2 = time.monotonic()
            print(f"Sensor 2: {now2:.3f},{accel2[0]:.6f},{accel2[1]:.6f},{accel2[2]:.6f}")

            time.sleep(0.01)  # データ取得間隔
        except RuntimeError as e:
            if debug_mode:
                print(f"Runtime error: {e}")
        except Exception as e:
            if debug_mode:
                print(f"Unexpected error: {e}")