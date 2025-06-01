import time
import board
import busio
import digitalio # CSピン制御に必要
import sys # sys.stderr を使用するためにインポート
# import traceback
from adafruit_bno08x import (
    BNO_REPORT_ACCELEROMETER,
    BNO_REPORT_GYROSCOPE,
    BNO_REPORT_MAGNETOMETER,
    BNO_REPORT_ROTATION_VECTOR,
)
from adafruit_bno08x.spi import BNO08X_SPI

# SPIピン定義
# GP6 for SCK -> board.D8 or board.SCK
# GP3 for MOSI (TX) -> board.D10 or board.MOSI
# GP4 for MISO (RX) -> board.D9 or board.MISO
# GP5 for CS -> board.D7 or board.RX (GPIO5)
try:
    SPI_SCK_PIN = board.SCK # または board.D8 (GPIO6)
    SPI_MOSI_PIN = board.MOSI # または board.D10 (GPIO3)
    SPI_MISO_PIN = board.MISO # または board.D9 (GPIO4)
    CS_PIN = board.RX       # または board.RX (GPIO5)
    # 割り込みピンとリセットピンの定義を追加
    INT_PIN_BOARD = board.TX  # 例: GPIO29
    RESET_PIN_BOARD = board.SCL # 例: GPIO28
except AttributeError as e:
    print(f"Error defining SPI/CS/INT/RESET pins: {e}. Please check your board\\'s pin definitions.")
    # ピン定義エラー時のフォールバック
    SPI_SCK_PIN, SPI_MOSI_PIN, SPI_MISO_PIN, CS_PIN, INT_PIN_BOARD, RESET_PIN_BOARD = (None,) * 6

# SPIバスの初期化
spi = None
if SPI_SCK_PIN and SPI_MOSI_PIN and SPI_MISO_PIN:
    try:
        spi = busio.SPI(SPI_SCK_PIN, MOSI=SPI_MOSI_PIN, MISO=SPI_MISO_PIN)
        print("SPI bus initialized successfully")
    except Exception as e:
        print(f"Failed to initialize SPI bus: {e}")
        # raise # ここでエラーを発生させると、以降のprintも実行されない可能性がある
        spi = None # 初期化失敗を示す
else:
    print("SPI pins not fully defined. Cannot initialize SPI bus.")

# CSピンの初期化
cs = None
if CS_PIN and spi: # spiが初期化されていることも確認
    try:
        cs = digitalio.DigitalInOut(CS_PIN)
        cs.direction = digitalio.Direction.OUTPUT
        cs.value = True # 初期状態はHigh (非選択)
        print("CS pin initialized successfully")
    except Exception as e:
        print(f"Failed to initialize CS pin: {e}")
        cs = None # 初期化失敗を示す
else:
    if not CS_PIN:
        print("CS pin not defined.")
    if not spi:
        print("SPI bus not initialized, skipping CS pin setup.")

# 割り込みピンとリセットピンのオブジェクトを初期化
int_pin = None
if INT_PIN_BOARD:
    try:
        int_pin = digitalio.DigitalInOut(INT_PIN_BOARD)
        # 割り込みピンの方向はライブラリが入力として処理します
        print("INT pin initialized successfully")
    except Exception as e:
        print(f"Failed to initialize INT pin ({INT_PIN_BOARD}): {e}")
        int_pin = None

reset_pin = None
if RESET_PIN_BOARD:
    try:
        reset_pin = digitalio.DigitalInOut(RESET_PIN_BOARD)
        reset_pin.direction = digitalio.Direction.OUTPUT
        reset_pin.value = True  # BNO08xのリセットは通常アクティブローなので、Highに保持
        print("RESET pin initialized successfully")
    except Exception as e:
        print(f"Failed to initialize RESET pin ({RESET_PIN_BOARD}): {e}")
        reset_pin = None

# Global sensor object
bno = None

# Define features and flags at module level
FEATURES_TO_CONFIGURE = [
    (BNO_REPORT_ACCELEROMETER, "Accelerometer"),
    (BNO_REPORT_GYROSCOPE, "Gyroscope"),
    (BNO_REPORT_MAGNETOMETER, "Magnetometer"),
    (BNO_REPORT_ROTATION_VECTOR, "Rotation Vector"),
]

FEATURE_ENABLE_FLAGS = {
    "Accelerometer": True,
    "Gyroscope": False, # Set to True to enable Gyroscope
    "Magnetometer": False, # Set to True to enable Magnetometer
    "Rotation Vector": False, # Set to True to enable Rotation Vector
}
enabled_features_status = {}

def _enable_single_feature_on_sensor(bno_instance, feature_const, feature_name):
    """Helper function to enable a single feature on a given BNO08x instance."""
    if not bno_instance:
        print(f"BNO08X instance not valid. Cannot enable {feature_name}.")
        return False
    try:
        bno_instance.enable_feature(feature_const)
        print(f"{feature_name} enabled successfully")
        return True
    except RuntimeError as e:
        print(f"Error enabling {feature_name}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error enabling {feature_name}: {e}")
        return False

def initialize_sensor_and_setup_features():
    """
    Initializes the BNO08X sensor and enables the configured features.
    Returns True if successful, False otherwise.
    Modifies global 'bno' and 'enabled_features_status'.
    """
    global bno, spi, cs, int_pin, reset_pin, enabled_features_status

    if not (spi and cs and int_pin and reset_pin):
        print("Cannot initialize BNO08X: SPI, CS, INT, or RESET pin/object not ready.")
        bno = None
        return False

    try:
        print("Attempting to initialize BNO08X (SPI)...")
        current_bno = BNO08X_SPI(spi, cs, int_pin, reset_pin)
        print("BNO08X (SPI) object created.")
        
        bno = current_bno
        print("BNO08X (SPI) initialized successfully.")

        enabled_features_status.clear()
        print("Enabling sensor features...")
        for feature_const, name in FEATURES_TO_CONFIGURE:
            if FEATURE_ENABLE_FLAGS.get(name, False):
                status = _enable_single_feature_on_sensor(bno, feature_const, name)
                enabled_features_status[name] = status
                if not status:
                    print(f"Failed to enable {name}. Sensor might not be fully operational.")
            else:
                enabled_features_status[name] = False
        
        print("Feature enabling process complete.")
        print("Enabled features status:", enabled_features_status)
        
        if any(status for name, status in enabled_features_status.items() if FEATURE_ENABLE_FLAGS.get(name)):
            return True
        elif not any(FEATURE_ENABLE_FLAGS.values()):
            return True
        else:
            print("Warning: Sensor initialized, but no requested features could be enabled.")
            return True

    except Exception as e:
        print(f"Failed to initialize BNO08X (SPI) or enable features: {e}", file=sys.stderr)
        bno = None
        return False

# Initial attempt to initialize sensor and features
print("Starting initial sensor setup...")
initial_setup_successful = initialize_sensor_and_setup_features()
if initial_setup_successful:
    print("Initial sensor setup successful.")
else:
    print("Initial sensor setup failed. Will attempt re-initialization in the main loop if needed.")


# メインループ
while True:
    try:
        if not bno:
            print("BNO08X sensor not available. Attempting to re-initialize...")
            time.sleep(1) 
            if not initialize_sensor_and_setup_features():
                print("Re-initialization failed. Skipping data read for this iteration.")
                time.sleep(1) 
                continue
            else:
                print("Sensor re-initialized and features configured successfully.")
        
        data_points = []
        now_str = f"{time.monotonic():.3f}"
        data_points.append(now_str)

        if enabled_features_status.get("Accelerometer", False) and bno:
            accel_x, accel_y, accel_z = bno.acceleration
            data_points.extend([f"{accel_x:.3f}", f"{accel_y:.3f}", f"{accel_z:.3f}"])
        else:
            data_points.extend(["N/A"] * 3)

        if enabled_features_status.get("Gyroscope", False) and bno:
            gyro_x, gyro_y, gyro_z = bno.gyro
            data_points.extend([f"{gyro_x:.3f}", f"{gyro_y:.3f}", f"{gyro_z:.3f}"])
        else:
            data_points.extend(["N/A"] * 3)

        if enabled_features_status.get("Magnetometer", False) and bno:
            mag_x, mag_y, mag_z = bno.magnetic
            data_points.extend([f"{mag_x:.3f}", f"{mag_y:.3f}", f"{mag_z:.3f}"])
        else:
            data_points.extend(["N/A"] * 3)
            
        if enabled_features_status.get("Rotation Vector", False) and bno:
            quat_i, quat_j, quat_k, quat_real = bno.quaternion
            data_points.extend([f"{quat_i:.3f}", f"{quat_j:.3f}", f"{quat_k:.3f}", f"{quat_real:.3f}"])
        else:
            data_points.extend(["N/A"] * 4)

        print(",".join(data_points))

    except RuntimeError as e:
        print(f"RuntimeError during main loop (data read or sensor communication): {e}", file=sys.stderr)
        bno = None
        print("Marked sensor for re-initialization.")
        time.sleep(0.5)
    except Exception as e:
        print(f"Unexpected error in main loop: {e}", file=sys.stderr)
        bno = None 
        print("Marked sensor for re-initialization due to unexpected error.")
        time.sleep(0.5)

    time.sleep(0.1) # Loop delay
