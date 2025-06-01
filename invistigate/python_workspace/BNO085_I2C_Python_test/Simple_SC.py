import serial
import serial.tools.list_ports
import threading

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
    """シリアルポートからのデータを随時出力"""
    while True:
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8', errors='ignore').strip()
            if response:
                print(f"[DEVICE] {response}")

# 別スレッドで受信データを処理
threading.Thread(target=read_serial, daemon=True).start()

print("Enter text to send. Press Ctrl+R to send reboot command. Ctrl+C to exit.")

try:
    while True:
        # ユーザー入力をチェック
        cmd = input("> ")
        if cmd.lower() == '\x12':  # Ctrl+R のASCIIコードは 0x12
            print("[INFO] Sending Ctrl+D to reboot the device...")
            ser.write(b'\x04')  # Ctrl+D を送信
        else:
            ser.write((cmd + "\r\n").encode())  # 入力データを送信
except KeyboardInterrupt:
    print("\n[INFO] Exiting program...")
finally:
    ser.close()
    print("[INFO] Serial port closed.")