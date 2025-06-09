import serial
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from rich.live import Live
from rich.table import Table
import time

# 複数のBNO08xセンサー（Arduino等）からのCSVデータを受信し、区別して表示する
# 各センサーは milisec,x,y,z の形式で出力することを想定

def read_serial(port, baudrate, name, data_queue):
    try:
        with serial.Serial(port, baudrate, timeout=1) as ser:
            while True:
                line = ser.readline().decode(errors='ignore').strip()
                if line:
                    try:
                        parts = line.split(',')
                        # milisec,x,y,z 形式のデータをパース
                        if len(parts) == 4:
                            milisec, x, y, z = map(float, parts)
                            data_queue.put({
                                'name': name,
                                'milisec': milisec,
                                'x': x,
                                'y': y,
                                'z': z
                            })
                        else:
                            data_queue.put({'name': name, 'raw': line})
                    except Exception:
                        data_queue.put({'name': name, 'raw': line})
    except Exception as e:
        data_queue.put({'name': name, 'error': str(e)})

if __name__ == "__main__":
    # ここで各COMポート・センサー名を指定
    ports = [
        {"port": "COM3", "baudrate": 115200, "name": "BNO08x_1"},
        {"port": "COM6", "baudrate": 115200, "name": "BNO08x_2"},
        # 必要に応じて追加
    ]

    from collections import defaultdict
    latest_data = defaultdict(dict)
    data_queue = Queue()

    def make_table():
        table = Table(title="BNO08x Sensors Live Data")
        table.add_column("Sensor", style="cyan", no_wrap=True)
        table.add_column("Time(ms)", justify="right")
        table.add_column("X", justify="right")
        table.add_column("Y", justify="right")
        table.add_column("Z", justify="right")
        for p in ports:
            d = latest_data.get(p["name"], {})
            if 'error' in d:
                table.add_row(p["name"], d['error'], '-', '-', '-')
            elif 'milisec' in d:
                table.add_row(p["name"], f"{d['milisec']:.0f}", f"{d['x']:.6f}", f"{d['y']:.6f}", f"{d['z']:.6f}")
            elif 'raw' in d:
                table.add_row(p["name"], d['raw'], '-', '-', '-')
            else:
                table.add_row(p["name"], '-', '-', '-', '-')
        return table

    print("複数BNO08xセンサーからの受信をTUIで開始しました。Ctrl+Cで終了します。")
    try:
        with ThreadPoolExecutor(max_workers=len(ports)) as executor:
            for p in ports:
                executor.submit(read_serial, p["port"], p["baudrate"], p["name"], data_queue)
            with Live(make_table(), refresh_per_second=10) as live:
                while True:
                    while not data_queue.empty():
                        d = data_queue.get()
                        latest_data[d['name']] = d
                    live.update(make_table())
                    time.sleep(0.05)
    except KeyboardInterrupt:
        print("終了します。")