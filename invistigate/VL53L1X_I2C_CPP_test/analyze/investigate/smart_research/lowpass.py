import matplotlib.pyplot as plt
import os
from lib.common_analysis import lowpass_filter, load_yml_data, load_csv_data  # 共通ライブラリの関数を利用

# plt.style.use('dark_background')

# --- 設定ファイル（setting.yml）から読み込み ---
dir_workspace = "analyze/investigate/smart_research"
mode, timing_budget_us, inter_measurement_ms = load_yml_data(dir_workspace)

dir_raw_data = os.path.join(dir_workspace, "raw_data")
times, distances = load_csv_data(dir_raw_data, mode, timing_budget_us, inter_measurement_ms)

# --- サンプリング周波数とカットオフ周波数を指定 ---
fs = 100  # 例: サンプリング周波数[Hz]
fc = 2    # 例: カットオフ周波数[Hz]

filtered_distances = lowpass_filter(distances, fs, fc)

# plt.plot(times, distances, 'b-', label='Raw')
plt.plot(times, filtered_distances, 'r-', label='Low-pass')
plt.xlabel('Time [ms]')
plt.ylabel('Distance [mm]')
plt.title('VL53L1X Distance Sensor: '+str(mode)+" "+ str(timing_budget_us)+"us "+str(inter_measurement_ms)+"ms")
plt.grid()
plt.yticks(range(0, 700, 50))
plt.legend()
plt.show()