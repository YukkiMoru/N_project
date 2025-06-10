import serial
import struct
import matplotlib.pyplot as plt
import threading
import time
from collections import deque
import yaml
import numpy as np
import os

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

# main.cppの出力に合わせて7バイト（4+2+1）
DATA_SIZE = 7  # 4バイト(ms) + 2バイト(dist) + 1バイト(timeout)

times = deque(maxlen=200)
distances = deque(maxlen=200)
exit_flag = False

# --- polyfit係数の読み込み ---
# スクリプトの絶対パスからYAMLファイルの絶対パスを組み立てる
script_dir = os.path.dirname(os.path.abspath(__file__))
polyfit_coeffs_path = os.path.join(
    script_dir,
    'investigate', 'smart_research', 'polyfit_coeffs', 'polyfit_coeffs.yml'
)
if not os.path.exists(polyfit_coeffs_path):
    # analyze/ajd_graph_poly.py から見て1つ上の階層に移動
    polyfit_coeffs_path = os.path.join(
        script_dir, '..', 'investigate', 'smart_research', 'polyfit_coeffs', 'polyfit_coeffs.yml'
    )
    polyfit_coeffs_path = os.path.abspath(polyfit_coeffs_path)

with open(polyfit_coeffs_path, 'r', encoding='utf-8') as f:
    polyfit_data = yaml.safe_load(f)
poly_coeffs = polyfit_data['polyfit_coeffs']
poly_func = np.poly1d(poly_coeffs)

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
            # main.cpp: ms(uint32_t), dist(uint16_t), timeout(uint8_t)
            ms, dist, timeout = struct.unpack('<IHB', data)
            if timeout:
                print(f"{ms}, TIMEOUT")
                times.append(ms)
                distances.append(float('nan'))
                plt.pause(0.0001)
                continue
            times.append(ms)
            distances.append(dist)
            # --- polyfit補正値の計算 ---
            corrected_distances = [poly_func(d) if not np.isnan(d) else np.nan for d in distances]
            if len(times) > 0 and len(times) == len(distances):
                x_end = times[-1] + X_WIDTH // 10  # 右端に少し余白
                times_with_blank = list(times) + [x_end]
                corrected_with_blank = list(corrected_distances) + [float('nan')]
                line.set_xdata(times_with_blank)
                line.set_ydata(corrected_with_blank)
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
            ax.set_title(f'VL53L1X Distance Sensor [Polyfit]  [Sampling: {sampling_freq:.1f} Hz]')
            plt.pause(0.0001)
except KeyboardInterrupt:
    print("終了します")
finally:
    ser.close()
    plt.ioff()
    plt.show()