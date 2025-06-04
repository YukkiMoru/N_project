import serial

PORT = 'COM6'  # ここをCOM6に変更
BAUD = 115200

ser = serial.Serial(PORT, BAUD, timeout=0.1)

print("シリアルポートからのデータ受信開始...")

try:
    while True:
        line = ser.readline().decode('utf-8').strip()
        if line:
            print(line)  # 例: 24622,420
except KeyboardInterrupt:
    print("終了します")
finally:
    ser.close()