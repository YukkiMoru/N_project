import serial
import threading

def read_serial(port, baudrate, name):
    count = 0
    try:
        with serial.Serial(port, baudrate, timeout=1) as ser:
            print(f"[{name}] Opened {port}")
            while True:
                line = ser.readline().decode(errors='ignore').strip()
                if line:
                    try:
                        parts = line.split(',')
                        if len(parts) == 4:
                            timestamp, x, y, z = map(float, parts)
                            count += 1
                            if count % 10 == 0:  # 10行に1回だけ表示
                                print(f"[{name}] t={timestamp:.2f} x={x:.6f} y={y:.6f} z={z:.6f}")
                        else:
                            if count % 10 == 0:
                                print(f"[{name}] {line}")
                    except Exception:
                        if count % 10 == 0:
                            print(f"[{name}] {line}")
    except Exception as e:
        print(f"[{name}] Error: {e}")

if __name__ == "__main__":
    # 1つのCOMポートとボーレートを指定
    port = "COM6"
    baudrate = 115200
    name = "COM6"

    print(f"{name} からの受信を開始します。Ctrl+Cで終了します。")
    try:
        read_serial(port, baudrate, name)
    except KeyboardInterrupt:
        print("終了します。")