import serial
import time
import math
from rich.live import Live
from rich.table import Table
from rich.console import Console

# --- 設定ここから ---
PORT = 'COM6'  # シリアルポート名
BAUD = 115200  # ボーレート
SENSOR_CMD_MODE = 'short'  # センサーモード: 'short', 'medium', 'long'
SENSOR_CMD_TIMING = 33000  # 測定タイミングバジェット[us]（例: 33000, 50000, 110000 など）
SENSOR_CMD_INTERVAL = 33  # 連続測定間隔[ms]（例: 5, 33, 100 など）
SAMPLE_FREQ = int(1000 / SENSOR_CMD_INTERVAL)  # サンプリング周波数(Hz)（自動計算）
BASE_MM = 150  # センサー間の基準距離（mm）
# --- 設定ここまで ---

def main():
    console = Console()
    # --- センサ設定コマンド送信 ---
    command = f"{SENSOR_CMD_MODE},{SENSOR_CMD_TIMING},{SENSOR_CMD_INTERVAL}\n".encode()
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        ser.write(command)
        # "OK"が返るまで最大5行読む
        for _ in range(5):
            response = ser.readline().decode().strip()
            if response == "OK":
                console.print("[green]コマンドが正常に受け付けられました[/green]")
                break
        else:
            console.print("[red]OK応答が得られませんでした[/red]")
            return
        ser.reset_input_buffer()
        time.sleep(4)

    # --- データ受信 ---
    with serial.Serial(PORT, BAUD, timeout=0.1) as ser:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        console.print("[cyan]シリアルポートからのデータ受信開始...（Ctrl+Cで終了）[/cyan]")
        sensor_data = {}
        freq_dict = {}
        count_dict = {}
        last_time = time.time()
        angle_dict = {}
        def make_table():
            table = Table(title="センサーデータ", show_lines=True)
            table.add_column("Sensor ID", justify="center")
            table.add_column("ms", justify="right")
            table.add_column("Distance", justify="right")
            table.add_column("Rate(Hz)", justify="right")
            table.add_column("Angle(deg)", justify="right")
            for sid, (ms, dist) in sensor_data.items():
                rate = freq_dict.get(sid, 0)
                angle = angle_dict.get(sid, "-")
                table.add_row(sid, ms, dist, str(rate), str(angle))
            return table
        try:
            with Live(make_table(), refresh_per_second=20, console=console) as live:
                while True:
                    line = ser.readline().decode().strip()
                    now = time.time()
                    updated = False
                    if line:
                        parts = line.split(',')
                        if len(parts) != 3:
                            continue
                        sensor_id, ms, dist = parts
                        if dist == 'NULL':
                            dist_disp = '[red]TIMEOUT[/red]'
                            dist_val = None
                        else:
                            dist_disp = dist
                            try:
                                dist_val = float(dist)
                            except ValueError:
                                dist_val = None
                        sensor_data[sensor_id] = (ms, dist_disp)
                        count_dict[sensor_id] = count_dict.get(sensor_id, 0) + 1
                        # 差分と角度計算（センサーが2つの場合を想定、生データで計算）
                        if dist_val is not None:
                            if len(sensor_data) == 2:
                                ids = sorted(sensor_data.keys())
                                try:
                                    d1 = float(sensor_data[ids[0]][1])
                                    d2 = float(sensor_data[ids[1]][1])
                                    diff = d1 - d2
                                    angle_rad = math.atan(diff / BASE_MM)
                                    angle_deg = round(math.degrees(angle_rad), 2)
                                    angle_dict[ids[0]] = angle_deg
                                    angle_dict[ids[1]] = -angle_deg
                                except Exception:
                                    angle_dict[ids[0]] = "-"
                                    angle_dict[ids[1]] = "-"
                            else:
                                angle_dict[sensor_id] = "-"
                        updated = True
                    # 周波数更新は1秒ごと
                    if now - last_time >= 1.0:
                        for sid in count_dict:
                            freq_dict[sid] = count_dict[sid]
                        count_dict = {}
                        last_time = now
                        updated = True
                    if updated:
                        live.update(make_table())
        except KeyboardInterrupt:
            console.print("[yellow]終了します[/yellow]")

if __name__ == "__main__":
    main()