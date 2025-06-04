import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'MS Gothic'  # ←この行を追加
import os
import numpy as np
from scipy.signal import butter, filtfilt
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
from lib.common_analysis import load_yml_data, load_csv_data, lowpass_filter
import pandas as pd
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
import yaml

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

# --- polyfit補正 ---
# narrowed_stable_sections.csv から補正用データを読み込む
sections_csv_path = os.path.join(dir_workspace, "sections", "narrowed_stable_sections.csv")
df_sections = pd.read_csv(sections_csv_path)

# 区間中心時刻とターゲット距離のペアを作成
center_times = ((df_sections['Start[ms]'] + df_sections['End[ms]']) / 2).values
# ターゲット距離は float 型で取得
target_distances = df_sections['Target Distance[mm]'].astype(float).values

# times, distances は既に読み込まれている
# 各区間の中心時刻±250msの範囲で生データ距離の平均値を取得
window_ms = 250
center_raw_distances = []
for ct in center_times:
    mask = (np.array(times) >= ct - window_ms) & (np.array(times) <= ct + window_ms)
    if np.any(mask):
        center_raw_distances.append(np.mean(np.array(distances)[mask]))
    else:
        center_raw_distances.append(np.nan)
center_raw_distances = np.array(center_raw_distances)

# nanがあれば除外
valid_mask = ~np.isnan(center_raw_distances)
center_raw_distances = center_raw_distances[valid_mask]
target_distances_valid = target_distances[valid_mask]

# 多項式フィッティング（例：6次）
poly_order = 3
poly_coeffs = np.polyfit(center_raw_distances, target_distances_valid, poly_order)
poly_func = np.poly1d(poly_coeffs)

# 生データ全体に補正を適用
polyfit_corrected_distances = poly_func(distances)
print(f"polyfit項数: {len(poly_coeffs)-1} 次式（{len(poly_coeffs)}項）")
print("polyfit内部パラメータ（係数）:")
for i, coef in enumerate(poly_coeffs):
    print(f"  x^{poly_order - i}: {coef}")
filtered_polyfit_corrected_distances = lowpass_filter(polyfit_corrected_distances, fs, fc)

# 例: 600mm, 450mm, 300mm, 100mm でpolyfit補正後の値を出力
for true_mm in [600, 450, 300, 100]:
    pred = np.polyval(np.flip(poly_coeffs), true_mm)
    print(f"真値 {true_mm}mm → polyfit補正後: {pred:.2f}mm")


# --- グラフ描画 ---
# plt.plot(times, distances, 'g-', label='Raw')
# plt.plot(times, cal_raw_distances, 'y-', label='Raw + Cal')
plt.plot(times, filtered_distances, 'b-', label='LP')
# plt.plot(times, cal_distances, 'r-', label='LP + Cal')
plt.plot(times, filtered_polyfit_corrected_distances, 'm-', label='LP + PC')
plt.xlabel('Time [ms]')
plt.ylabel('Distance [mm]')
plt.title('VL53L1X Distance Sensor: '+str(mode)+" "+ str(timing_budget_us)+"us "+str(inter_measurement_ms)+"ms")
plt.grid()
plt.yticks(range(0, 700, 50))
plt.legend()
plt.show()

# --- Scatter plot: True Value vs Corrected Value ---
plt.figure()
plt.scatter(center_raw_distances, target_distances_valid, label='Target Value', color='blue')
plt.scatter(center_raw_distances, poly_func(center_raw_distances), label='Polyfit Corrected (Points)', color='red', marker='x')

# 連続線を描画
x_line = np.linspace(min(center_raw_distances), max(center_raw_distances), 300)
y_line = poly_func(x_line)
plt.plot(x_line, y_line, color='red', linestyle='-', label='Polyfit Corrected (Line)')

plt.plot([min(center_raw_distances), max(center_raw_distances)], [min(center_raw_distances), max(center_raw_distances)], 'k--', label='y=x (Ideal)')
plt.xlabel('Raw Data Distance')
plt.ylabel('Target/Corrected Distance')
plt.title('Target Value vs Polyfit Corrected Value')
plt.legend()
plt.grid()
plt.show()

# データ分割
X_train, X_val, y_train, y_val = train_test_split(center_raw_distances, target_distances_valid, test_size=0.2, random_state=42)

orders = range(1, 6)
train_mses = []
val_mses = []
for order in orders:
    coeffs = np.polyfit(X_train, y_train, order)
    func = np.poly1d(coeffs)
    train_pred = func(X_train)
    val_pred = func(X_val)
    train_mses.append(mean_squared_error(y_train, train_pred))
    val_mses.append(mean_squared_error(y_val, val_pred))

plt.figure()
plt.plot(orders, train_mses, marker='o', label='学習用MSE')
plt.plot(orders, val_mses, marker='x', label='検証用MSE')
plt.xlabel('poly_order')
plt.ylabel('MSE')
plt.title('polyfit次数ごとのMSE（過学習判定）')
plt.legend()
plt.grid()
plt.show()

print(f"最小MSEのpoly_order: {orders[np.argmin(val_mses)]}")

save_poly_coeffs = True

if save_poly_coeffs:
    # 補正用の多項式係数をYAML形式で保存
    polyfit_coeffs_dir = os.path.join(dir_workspace, 'polyfit_coeffs')
    os.makedirs(polyfit_coeffs_dir, exist_ok=True)
    polyfit_coeffs_path = os.path.join(polyfit_coeffs_dir, 'polyfit_coeffs.yml')
    with open(polyfit_coeffs_path, 'w', encoding='utf-8') as f:
        yaml.dump({'polyfit_coeffs': poly_coeffs.tolist()}, f, allow_unicode=True)
    print(f"polyfit係数をYAMLで保存しました: {polyfit_coeffs_path}")