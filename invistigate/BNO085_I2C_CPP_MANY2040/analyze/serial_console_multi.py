import serial
from concurrent.futures import ThreadPoolExecutor

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
                            if count % 10 == 0:
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
    ports = [
        {"port": "COM3", "baudrate": 115200, "name": "COM3"},
        {"port": "COM6", "baudrate": 115200, "name": "COM6"},
    ]

    print("両方のCOMポートからの受信を開始しました。Ctrl+Cで終了します。")
    try:
        with ThreadPoolExecutor(max_workers=len(ports)) as executor:
            futures = [
                executor.submit(read_serial, p["port"], p["baudrate"], p["name"])
                for p in ports
            ]
            for f in futures:
                f.result()  # ここで各スレッドの終了を待つ（通常は無限ループなのでCtrl+Cまで待機）
    except KeyboardInterrupt:
        print("終了します。")