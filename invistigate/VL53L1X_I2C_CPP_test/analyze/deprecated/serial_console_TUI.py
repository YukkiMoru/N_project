import serial
import time
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
    with serial.Serial(PORT, BAUD, timeout=0.1) as ser:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        console.print("[cyan]シリアルポートからのデータ受信開始...（Ctrl+Cで終了）[/cyan]")
        sensor_data = {}
        freq_dict = {}
        count_dict = {}
        last_time = time.time()
        def make_table():
            table = Table(title="センサーデータ", show_lines=True)
            table.add_column("Sensor ID", justify="center")
            table.add_column("ms", justify="right")
            table.add_column("Distance", justify="right")
            table.add_column("Rate(Hz)", justify="right")
            for sid, (ms, dist) in sensor_data.items():
                rate = freq_dict.get(sid, 0)
                table.add_row(sid, ms, dist, str(rate))
            return table
        try:
            with Live(make_table(), refresh_per_second=4, console=console) as live:
                while True:
                    line = ser.readline().decode().strip()
                    now = time.time()
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
                        count_dict[sensor_id] = count_dict.get(sensor_id, 0) + 1
                    # 1秒ごとに周波数更新
                    if now - last_time >= 1.0:
                        for sid in count_dict:
                            freq_dict[sid] = count_dict[sid]
                        count_dict = {}
                        last_time = now
                        live.update(make_table())
        except KeyboardInterrupt:
            console.print("[yellow]終了します[/yellow]")

if __name__ == "__main__":
    main()