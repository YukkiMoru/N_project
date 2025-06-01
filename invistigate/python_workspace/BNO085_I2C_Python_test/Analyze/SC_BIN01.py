import serial
import serial.tools.list_ports
import threading
import struct
import time # 追加 (オプション)

# 利用可能なCOMポートを表示
ports = list(serial.tools.list_ports.comports())
print("利用可能なポート:")
for p in ports:
    print(p.device)

# COMポートとボーレートを設定
PORT = 'COM3'  # 必要に応じて変更
BAUD = 115200

try:
    ser = serial.Serial(PORT, BAUD, timeout=0.1)  # タイムアウトを短く設定
    print(f"[INFO] Connected to {PORT}")
except serial.SerialException as e:
    print(f"[ERROR] Could not open port {PORT}: {e}")
    exit()

def read_serial():
    """シリアルポートからのデータを随時出力。バイナリセンサーデータとテキストデータの両方を処理"""
    binary_mode = False  # バイナリ通信モードのフラグ

    while True:
        try:
            if binary_mode:
                if ser.in_waiting >= 25:  # ヘッダー(4B) + センサーID(1B) + タイムスタンプ(4B) + 3x float(12B) + チェックサム(4B) = 25B
                    raw_data = ser.read(25)
                    try:
                        header, sensor_id, timestamp, accel_x, accel_y, accel_z, checksum = struct.unpack('<4sBffffI', raw_data)
                        if header != b'HEAD':
                            print(f"[ERROR] Invalid header: {header}, Raw Data: {raw_data}")
                            continue

                        # チェックサムの検証
                        calculated_checksum = sum(raw_data[:-4]) & 0xFFFFFFFF
                        if checksum != calculated_checksum:
                            print(f"[ERROR] Checksum mismatch: received {checksum}, calculated {calculated_checksum}")
                            continue

                        if sensor_id in (1, 2):
                            print(f"[SENSOR {sensor_id}] Timestamp: {timestamp}, Accel X: {accel_x:.2f}, Y: {accel_y:.2f}, Z: {accel_z:.2f}")
                        else:
                            print(f"[ERROR] Unexpected sensor ID: {sensor_id}")
                    except struct.error as e:
                        print(f"[ERROR] Struct unpacking failed: {e}")

            elif ser.in_waiting > 0:
                response = ser.readline().decode('utf-8', errors='ignore').strip()
                if response == "BINARY COM":
                    print("[INFO] BINARY COM received. Switching to binary mode...")
                    binary_mode = True
                elif response:
                    print(f"[DEVICE-TEXT] {response}")

            time.sleep(0.001)  # CPU負荷軽減

        except serial.SerialException as e:
            print(f"[ERROR] Serial error in read_serial: {e}")
            break
        except Exception as e:
            print(f"[ERROR] General error in read_serial: {e}")

# read_binary_data 関数は read_serial に統合されたため削除されました。

# 別スレッドで受信データを処理
threading.Thread(target=read_serial, daemon=True).start()

print("Enter text to send or type 'binary:<value>' to send binary data. Ctrl+C to exit.")

try:
    while True:
        cmd = input("> ")
        if cmd.startswith('binary:'):
            try:
                value = float(cmd.split(':')[1])
            except ValueError:
                print("[ERROR] Invalid binary value. Please enter a valid float.")
        elif cmd.lower() == '\x04':  # Ctrl+D のASCIIコードは 0x04
            print("[INFO] Sending Ctrl+D to reboot the device...")
            ser.write(b'\x04')  # Ctrl+D を送信
        else:
            ser.write((cmd + "\r\n").encode())  # 入力データを送信
except KeyboardInterrupt:
    print("\n[INFO] Exiting program...")
finally:
    ser.close()
    print("[INFO] Serial port closed.")