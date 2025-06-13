import serial
import time
import csv
import os
from rich.live import Live
from rich.table import Table
from rich.console import Console

PORT = 'COM6'
BAUD = 115200


def main():
    console = Console()
    # --- センサ設定コマンド送信 ---
    with serial.Serial(PORT, BAUD, timeout=1) as ser:
        ser.write(b"short,20000,20\n")
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
    with serial.Serial(PORT, BAUD, timeout=0.1) as ser, \
         open(os.path.join(os.path.dirname(__file__), "log.csv"), "w", newline="", encoding="utf-8") as csvfile:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        console.print("[cyan]シリアルポートからのデータ受信開始...（Ctrl+Cで終了）[/cyan]")
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "sensor_id", "ms", "distance"])
        def make_table():
            table = Table(title="センサーデータ", show_lines=True)
            table.add_column("Sensor ID", justify="center")
            table.add_column("ms", justify="right")
            table.add_column("Distance", justify="right")
            for sid, (ms, dist) in sensor_data.items():
                table.add_row(sid, ms, dist)
            return table
        sensor_data = {}
        try:
            start_time = time.time()  # 追加: 開始時刻を記録
            with Live(make_table(), refresh_per_second=20, console=console) as live:
                while True:
                    if time.time() - start_time > 10:  # 追加: 10秒経過で終了
                        break
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
                        else:
                            dist_disp = dist
                        sensor_data[sensor_id] = (ms, dist_disp)
                        # CSVに保存（そのまま）
                        writer.writerow([
                            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)),
                            sensor_id, ms, dist
                        ])
                        csvfile.flush()
                        updated = True
                    if updated:
                        live.update(make_table())
        except KeyboardInterrupt:
            console.print("[yellow]終了します[/yellow]")

if __name__ == "__main__":
    main()
