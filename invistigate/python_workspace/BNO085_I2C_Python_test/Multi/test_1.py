# [DEVICE] Channel 0 - Sensor 1 initialized at address 0x4A.
# [DEVICE] Channel 1 - Sensor 2 initialized at address 0x4B.
# [DEVICE] No sensors detected on channel 2. Skipping this channel.
# [DEVICE] No sensors detected on channel 3. Skipping this channel.
# [DEVICE] No sensors detected on channel 4. Skipping this channel.
# [DEVICE] No sensors detected on channel 5. Skipping this channel.
# [DEVICE] No sensors detected on channel 6. Skipping this channel.
# [DEVICE] No sensors detected on channel 7. Skipping this channel.

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
    channels = range(8)  # 全てのチャンネル（0〜7）を指定
    sensors = []

    # 各チャンネルのセンサーを初期化
    for channel in channels:
        sensor1 = initialize_sensor(channel, 0x4A)  # 1台目のセンサー
        sensor2 = initialize_sensor(channel, 0x4B)  # 2台目のセンサー

        if sensor1 is None and sensor2 is None:
            print(f"No sensors detected on channel {channel}. Skipping this channel.")
            continue

        # センサーが存在する場合のみリストに追加
        sensors.append((channel, sensor1, sensor2))
        if sensor1:
            print(f"Channel {channel} - Sensor 1 initialized at address 0x4A.")
        if sensor2:
            print(f"Channel {channel} - Sensor 2 initialized at address 0x4B.")

    if not sensors:
        print("No sensors initialized successfully. Exiting.")
        exit(1)

    while True:
        for channel, sensor1, sensor2 in sensors:
            try:
                if sensor1:
                    # 1台目のセンサーからデータ取得
                    accel1 = sensor1.acceleration
                    now1 = time.monotonic()
                    print(f"Channel {channel} - Sensor 1: {now1:.3f},{accel1[0]:.6f},{accel1[1]:.6f},{accel1[2]:.6f}")

                if sensor2:
                    # 2台目のセンサーからデータ取得
                    accel2 = sensor2.acceleration
                    now2 = time.monotonic()
                    print(f"Channel {channel} - Sensor 2: {now2:.3f},{accel2[0]:.6f},{accel2[1]:.6f},{accel2[2]:.6f}")

            except RuntimeError as e:
                if debug_mode:
                    print(f"Runtime error on channel {channel}: {e}")
            except Exception as e:
                if debug_mode:
                    print(f"Unexpected error on channel {channel}: {e}")

        time.sleep(0.01)  # データ取得間隔