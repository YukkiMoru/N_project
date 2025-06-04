import os
import serial
import threading
import time
import csv
import yaml
import struct

PORT = 'COM6'
BAUD = 115200

# --- 設定ファイル（setting.yml）から読み込み ---
dir_workspace = "analyze/investigate/smart_research"
with open(os.path.join(dir_workspace, "setting.yml"), "r", encoding="utf-8") as f:
    setting = yaml.safe_load(f)
mode = setting["mode"]
timing_budget_us = setting["timing_budget_us"]
inter_measurement_ms = setting["inter_measurement_ms"]

raw_data_dir = os.path.join(dir_workspace, "raw_data")
os.makedirs(raw_data_dir, exist_ok=True)
csv_filename = os.path.join(raw_data_dir, f"{mode}_{timing_budget_us}us_{inter_measurement_ms}ms.csv")

# --- ここからコマンド送信 ---
ser = serial.Serial(PORT, BAUD, timeout=1)
command = f"{mode},{timing_budget_us},{inter_measurement_ms}\n"
ser.write(command.encode())

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

times = []
distances = []
exit_flag = False

def check_key():
    global exit_flag
    while True:
        if input().strip().lower() == 'q':
            exit_flag = True
            break

# データ受信開始直後にsleep
print("シリアルポートからのデータ受信開始...（qで終了）")
time.sleep(3)

# キー入力監視スレッド開始
threading.Thread(target=check_key, daemon=True).start()

# 受信開始前にファイルを初期化しヘッダーを書き込む
with open(csv_filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["time", "distance"])

try:
    while not exit_flag:
        data = ser.read(DATA_SIZE)
        if len(data) == DATA_SIZE:
            ms, dist, timeout = struct.unpack('<IHB', data)
            if timeout:
                print(f"{ms}, TIMEOUT")
                times.append(ms)
                distances.append('TIMEOUT')
                with open(csv_filename, "a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([ms, 'TIMEOUT'])
                continue
            print(f"{ms}, {dist}")
            times.append(ms)
            distances.append(dist)
            with open(csv_filename, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([ms, dist])
except KeyboardInterrupt:
    print("終了します")
finally:
    ser.close()