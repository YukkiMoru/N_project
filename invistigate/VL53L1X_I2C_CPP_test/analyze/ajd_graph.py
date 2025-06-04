import serial
import struct
import matplotlib.pyplot as plt
import threading
import time
from collections import deque

PORT = 'COM6'
BAUD = 115200

# --- センサ設定コマンド送信 ---
ser = serial.Serial(PORT, BAUD, timeout=1)
ser.write(b"short,20000,5\n") 
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

# main.cppの出力に合わせて7バイト（4+2+1）
DATA_SIZE = 7  # 4バイト(ms) + 2バイト(dist) + 1バイト(timeout)

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