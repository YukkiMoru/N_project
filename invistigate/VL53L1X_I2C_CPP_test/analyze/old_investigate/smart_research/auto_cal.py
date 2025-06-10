import matplotlib.pyplot as plt
import csv
import os
import yaml
import numpy as np
from scipy.signal import butter, filtfilt
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
from lib.common_analysis import load_yml_data, load_csv_data, lowpass_filter

# plt.style.use('dark_background')

times = []
distances = []

# --- 設定ファイル（setting.yml）から読み込み ---
dir_workspace = os.path.dirname(__file__)
mode, timing_budget_us, inter_measurement_ms = load_yml_data(dir_workspace)
file_path = os.path.join(dir_workspace, 'raw_data')

times, distances = load_csv_data(file_path, mode, timing_budget_us, inter_measurement_ms)

# --- サンプリング周波数とカットオフ周波数を指定 ---
fs = 100  # 例: サンプリング周波数[Hz]
fc = 2    # 例: カットオフ周波数[Hz]

filtered_distances = lowpass_filter(distances, fs, fc)

# --- 区間1: 1000ms～2000msをy=100～200mmにスケーリング ---
section1_start = 7300
section1_end = 11000
section1_target = 600

# --- 区間2: 3000ms～4000msをy=300～400mmに定数倍＋オフセットでフィット ---
section2_start = 21000
section2_end = 22000
section2_target = 450
def calibrate_distances(times, filtered_distances, section1_start, section1_end, section1_target,
                        section2_start, section2_end, section2_target):
    # 区間1, 区間2のインデックス取得
    section1_indices = [i for i, t in enumerate(times) if section1_start <= t <= section1_end]
    section2_indices = [i for i, t in enumerate(times) if section2_start <= t <= section2_end]

    # 区間ごとの平均値計算
    section1_mean = np.mean([filtered_distances[i] for i in section1_indices])
    section2_mean = np.mean([filtered_distances[i] for i in section2_indices])

    # 区間1の平均値をy=0にシフト
    shifted_distances = filtered_distances - section1_mean

    # 区間2の平均値がsection2_targetになるように定数倍
    section2_mean_shifted = np.mean([shifted_distances[i] for i in section2_indices])
    scale = (section1_target - section2_target) / (-1 * section2_mean_shifted)
    scaled_distances = shifted_distances * scale

    cal_distances = scaled_distances + section1_target

    print(f"scale: {scale}, shifted: {section1_target-section1_mean}")
    return cal_distances

cal_distances = calibrate_distances(
    times, filtered_distances,
    section1_start, section1_end, section1_target,
    section2_start, section2_end, section2_target
)
cal_raw_distances = calibrate_distances(
    times, distances,
    section1_start, section1_end, section1_target,
    section2_start, section2_end, section2_target
)

# --- グラフ描画 ---
plt.plot(times, distances, 'g-', label='Raw')
plt.plot(times, cal_raw_distances, 'y-', label='Raw + Cal')
plt.plot(times, filtered_distances, 'b-', label='LP')
plt.plot(times, cal_distances, 'r-', label='LP + Cal')
plt.xlabel('Time [ms]')
plt.ylabel('Distance [mm]')
plt.title('VL53L1X Distance Sensor: '+str(mode)+" "+ str(timing_budget_us)+"us "+str(inter_measurement_ms)+"ms")
plt.grid()
plt.yticks(range(0, 700, 50))
plt.legend()
plt.show()