import serial
from rich.live import Live
from rich.table import Table
import time

def read_serial(ser):
    try:
        line = ser.readline().decode(errors='ignore').strip()
        if line:
            parts = line.split(',')
            if len(parts) == 4:
                milisec, x, y, z = map(float, parts)
                return {'milisec': milisec, 'x': x, 'y': y, 'z': z}
            else:
                return {'raw': line}
    except Exception as e:
        return {'error': str(e)}
    return {}

def make_table(data, sampling_rate=None):
    table = Table(title="BNO08x Sensor Live Data")
    table.add_column("Time(ms)", justify="right")
    table.add_column("X", justify="right")
    table.add_column("Y", justify="right")
    table.add_column("Z", justify="right")
    table.add_column("Sampling Rate(Hz)", justify="right")
    if 'error' in data:
        table.add_row(data['error'], '-', '-', '-', '-')
    elif 'milisec' in data:
        sr_str = f"{sampling_rate:.2f}" if sampling_rate is not None else '-'
        table.add_row(f"{data['milisec']:.0f}", f"{data['x']:.6f}", f"{data['y']:.6f}", f"{data['z']:.6f}", sr_str)
    elif 'raw' in data:
        table.add_row(data['raw'], '-', '-', '-', '-')
    else:
        table.add_row('-', '-', '-', '-', '-')
    return table

if __name__ == "__main__":
    port = "COM6"  # ここを必要なCOMポートに変更
    baudrate = 115200

    print(f"{port} からの受信をTUIで開始します。Ctrl+Cで終了します。")
    try:
        with serial.Serial(port, baudrate, timeout=1) as ser:
            latest_data = {}
            prev_milisec = None  # 前回のmilisec値（センサタイムスタンプ）
            sampling_rate = None
            with Live(make_table(latest_data, sampling_rate), refresh_per_second=250) as live:
                while True:
                    # バッファ内のデータを全て読み捨てて最新だけ取得
                    latest_valid = None
                    for _ in range(20):  # 1ループで最大20件までスキップ
                        d = read_serial(ser)
                        if d and 'milisec' in d:
                            latest_valid = d
                    if latest_valid:
                        d = latest_valid
                    else:
                        d = read_serial(ser)
                    if d and 'milisec' in d:
                        # milisec値（センサタイムスタンプ）でサンプリングレートを計算
                        if prev_milisec is not None:
                            dt = (d['milisec'] - prev_milisec) / 1000.0
                            if dt > 0:  # 負のdt（タイムスタンプ巻き戻り）は無視
                                sampling_rate = 1.0 / dt
                        prev_milisec = d['milisec']
                        latest_data = d
                    elif d:
                        latest_data = d
                    live.update(make_table(latest_data, sampling_rate))
                    time.sleep(0.005)
    except KeyboardInterrupt:
        print("終了します。")
    except Exception as e:
        print(f"エラー: {e}")