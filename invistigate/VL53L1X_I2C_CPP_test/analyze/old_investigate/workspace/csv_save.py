"""
このスクリプトは、VL53L1X距離センサとシリアル通信を行い、計測コマンドを送信します。
'q'キーを押すことでデータ取得を終了できます。

使い方:
    - シリアルポート(PORT)とボーレート(BAUD)を正しく設定してください。
    - 最初にセンサへ計測開始コマンドを送信します。
    - "OK"応答を受信後、距離データの受信・プロットを開始します。
    - ターミナルで'q'を押すとデータ取得を終了し、プロットを閉じます。

センサへのコマンド書式例:
    "medium,33000,10\n"
    # <mode>,<timing_budget_us>,<inter_measurement_ms>
    # 例: "medium,33000,10" の意味（デフォルト）
    #   - mode: "medium"（計測モード。例: "short", "medium", "long"）
    #   - timing_budget_us: 33000（1回の計測にかける時間[マイクロ秒]。精度と速度に影響）
    #   - inter_measurement_ms: 10（計測間隔[ミリ秒]）

他の設定例（解説付き）:
    # ser.write(b"short,20000,5\n")
    #   - "short"モード: 近距離向け。高速だが精度はやや低い。
    #   - timing_budget_us: 20000（20ms/回。高速・低精度）
    #   - inter_measurement_ms: 5（5msごとに計測。高サンプリングレート）

    # ser.write(b"medium,33000,33\n")
    #   - "medium"モード: バランス型。速度と精度の中間。
    #   - timing_budget_us: 33000（33ms/回）
    #   - inter_measurement_ms: 33（33msごとに計測。約30Hzサンプリング）

    # ser.write(b"long,50000,50\n")
    #   - "long"モード: 長距離向け。遅いが精度・レンジが高い。
    #   - timing_budget_us: 50000（50ms/回。高精度・低速）
    #   - inter_measurement_ms: 50（50msごとに計測。低サンプリングレート）

必要なライブラリ:
    - pyserial
注意:
    - センサが上記コマンドプロトコルに対応している必要があります。
    - timing_budget_usやinter_measurement_msは用途に応じて調整してください。
"""
import serial
import struct
import matplotlib.pyplot as plt
import threading
import time
from collections import deque
import csv

PORT = 'COM6'
BAUD = 115200

# --- センサ設定コマンド送信 ---
ser = serial.Serial(PORT, BAUD, timeout=1)
ser.write(b"short,20000,30\n") 
# ([short,medium,long],timing_budget_us,inter_measurement_ms)

# "OK"が返るまで最大5行読む
ok_received = False
for _ in range(5):
    response = ser.readline().decode().strip()
    if response == "OK":
        print("コマンドが正常に受け付けられました")
        ok_received = True
        break
if not ok_received:
    print("OK応答が得られませんでした")
ser.close()
# --- ここまでコマンド送信 ---

# データ受信用に再度オープン
ser = serial.Serial(PORT, BAUD, timeout=0.1)
ser.reset_input_buffer()
ser.reset_output_buffer()

DATA_SIZE = 7  # 4バイト(ms) + 2バイト(dist) + 1バイト(timeout)

# データ保存用
csv_filename = "distance_data.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["time", "distance"])

times = deque(maxlen=200)
distances = deque(maxlen=200)
exit_flag = False

def check_key():
    global exit_flag
    while True:
        if input().strip().lower() == 'q':
            exit_flag = True
            break

print("シリアルポートからのデータ受信開始...（qで終了）")
time.sleep(3)

plt.ion()
fig, ax = plt.subplots()
line, = ax.plot([0], [0], 'bo-')
ax.set_xlabel('Time [ms]')
ax.set_ylabel('Distance [mm]')
ax.set_title('VL53L1X Distance Sensor')
ax.grid(True)
ax.set_ylim(0, 600)

X_WIDTH = 5000

threading.Thread(target=check_key, daemon=True).start()

try:
    while not exit_flag:
        data = ser.read(DATA_SIZE)
        if len(data) == DATA_SIZE:
            ms, dist, timeout = struct.unpack('<IHB', data)
            if timeout:
                print(f"{ms}, TIMEOUT")
                times.append(ms)
                distances.append(float('nan'))
                # CSVにもnanで記録
                with open(csv_filename, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([ms, 'nan'])
                plt.pause(0.0001)
                continue
            times.append(ms)
            distances.append(dist)
            # CSVに追記
            with open(csv_filename, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([ms, dist])
            if len(times) > 0 and len(times) == len(distances):
                x_end = times[-1] + X_WIDTH // 10  # 右端に少し余白
                times_with_blank = list(times) + [x_end]
                distances_with_blank = list(distances) + [float('nan')]
                line.set_xdata(times_with_blank)
                line.set_ydata(distances_with_blank)
            ax.relim()
            ax.autoscale_view(scaley=False)
            if len(times) > 0:
                ax.set_xlim(max(times[-1] - X_WIDTH, 0), times[-1] + X_WIDTH // 10)
            if len(times) > 1:
                duration_ms = times[-1] - times[0]
                if duration_ms > 0:
                    sampling_freq = (len(times) - 1) * 1000 / duration_ms
                else:
                    sampling_freq = 0
            else:
                sampling_freq = 0
            ax.set_title(f'VL53L1X Distance Sensor  [Sampling: {sampling_freq:.1f} Hz]')
            plt.pause(0.0001)
except KeyboardInterrupt:
    print("終了します")
finally:
    ser.close()
    plt.ioff()
    plt.show()