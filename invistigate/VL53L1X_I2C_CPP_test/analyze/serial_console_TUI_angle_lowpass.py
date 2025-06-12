import serial
import time
import math
from rich.live import Live
from rich.table import Table
from rich.console import Console

PORT = 'COM6'
BAUD = 115200


def main():
    console = Console()
    # --- センサ設定コマンド送信 ---
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        ser.write(b"short,50000,100\n")
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
        BASE_MM = 100  # センサー間の基準距離（mm）
        # --- ローパスフィルタ用 ---
        lp_dist = {}  # 各センサーのフィルタ済み距離
        prev_lp_dist = {}  # 前回のフィルタ値
        fc = 0.1  # カットオフ周波数(Hz)
        Ts = 0.05  # サンプリング周期(秒)（20Hz表示を想定）
        alpha = Ts / (Ts + (1/(2*math.pi*fc)))
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
            with Live(make_table(), refresh_per_second=20, console=console) as live:  # 更新頻度を20に
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
                        # --- ローパスフィルタ適用 ---
                        if dist_val is not None:
                            if sensor_id not in prev_lp_dist:
                                prev_lp_dist[sensor_id] = dist_val
                            lp_dist[sensor_id] = alpha * dist_val + (1 - alpha) * prev_lp_dist[sensor_id]
                            prev_lp_dist[sensor_id] = lp_dist[sensor_id]
                        # 差分と角度計算（センサーが2つの場合を想定）
                        if dist_val is not None:
                            if len(sensor_data) == 2 and len(lp_dist) == 2:
                                ids = sorted(sensor_data.keys())
                                try:
                                    d1 = lp_dist[ids[0]]
                                    d2 = lp_dist[ids[1]]
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