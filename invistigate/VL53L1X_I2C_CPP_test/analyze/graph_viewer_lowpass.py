import os
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

# CSVファイルを読み込み
csv_path = os.path.join(os.path.dirname(__file__), 'log.csv')
df = pd.read_csv(csv_path, encoding='utf-8', usecols=["sensor_id", "ms", "distance"])

# ローパスフィルタ関数
# cutoff: カットオフ周波数[Hz], fs: サンプリング周波数[Hz], order: フィルタ次数
def lowpass_filter(data, cutoff, fs, order=2):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y

plt.figure(figsize=(10, 6))
sampling_freqs = []
for sid in df['sensor_id'].unique():
    sdf = df[df['sensor_id'] == sid].sort_values('ms')
    # サンプリング周期・周波数計算
    if len(sdf) > 1:
        delta_ms = sdf['ms'].diff().dropna()
        mean_delta = delta_ms.mean()
        freq = 1000.0 / mean_delta if mean_delta > 0 else 0
        sampling_freqs.append((sid, freq))
        # ローパスフィルタ適用
        cutoff = min(10, freq/2)  # カットオフ周波数例: 10Hzまたはナイキスト未満
        try:
            filtered = lowpass_filter(sdf['distance'].astype(float), cutoff, freq)
            plt.plot(sdf['ms'], filtered, label=f'Sensor {sid} (LPF)')
        except Exception as e:
            plt.plot(sdf['ms'], sdf['distance'], label=f'Sensor {sid} (raw)')
    else:
        sampling_freqs.append((sid, 0))
        plt.plot(sdf['ms'], sdf['distance'], label=f'Sensor {sid} (raw)')

plt.xlabel('ms')
plt.ylabel('Distance [mm]')
# サンプリング周波数をタイトルに追加
freq_str = ', '.join([f'S{sid}: {freq:.2f}Hz' for sid, freq in sampling_freqs])
plt.title(f'Distance by Sensor (Lowpass filtered)\nSampling Freq: {freq_str}')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()