import serial
from concurrent.futures import ThreadPoolExecutor

# 複数のBNO08xセンサー（Arduino等）からのCSVデータを受信し、区別して表示する
# 各センサーは milisec,x,y,z の形式で出力することを想定

def read_serial(port, baudrate, name):
    # すべての行を出力するように変更
    try:
        
        with serial.Serial(port, baudrate, timeout=1) as ser:
            print(f"[{name}] Opened {port}")
            while True:
                line = ser.readline().decode(errors='ignore').strip()
                if line:
                    try:
                        parts = line.split(',')
                        # milisec,x,y,z 形式のデータをパース
                        if len(parts) == 4:
                            milisec, x, y, z = map(float, parts)
                            print(f"[{name}] t={milisec:.0f} x={x:.6f} y={y:.6f} z={z:.6f}")
                        else:
                            print(f"[{name}] {line}")
                    except Exception:
                        print(f"[{name}] {line}")
    except Exception as e:
        print(f"[{name}] Error: {e}")

if __name__ == "__main__":
    # ここで各COMポート・センサー名を指定
    ports = [
        {"port": "COM3", "baudrate": 115200, "name": "BNO08x_1"},
        {"port": "COM6", "baudrate": 115200, "name": "BNO08x_2"},
        # 必要に応じて追加
    ]

    print("複数BNO08xセンサーからの受信を開始しました。Ctrl+Cで終了します。")
    try:
        with ThreadPoolExecutor(max_workers=len(ports)) as executor:
            futures = [
                executor.submit(read_serial, p["port"], p["baudrate"], p["name"])
                for p in ports
            ]
            for f in futures:
                f.result()  # 各スレッドの終了を待つ（通常は無限ループなのでCtrl+Cまで待機）
    except KeyboardInterrupt:
        print("終了します。")