import os
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt
from numpy.fft import rfft, rfftfreq

# --- ユーザー設定 ---
CUTOFF_HZ = 0.2      # カットオフ周波数[Hz]
ORDER = 1           # フィルタ次数
# ---

# CSVファイルを読み込み
csv_path = os.path.join(os.path.dirname(__file__), 'log.csv')
df = pd.read_csv(csv_path, encoding='utf-8', usecols=["sensor_id", "ms", "distance"])

# ローパスフィルタ関数
def lowpass_filter(data, cutoff, fs, order=2):
    nyq = 0.5 * fs
    normal_cutoff = min(cutoff / nyq, 0.99)  # 正常化カットオフは1未満
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
        cutoff = min(CUTOFF_HZ, freq/2)  # ユーザー指定 or ナイキスト未満
        try:
            filtered = lowpass_filter(sdf['distance'].astype(float), cutoff, freq, order=ORDER)
            plt.plot(sdf['ms'], sdf['distance'], label=f'Sensor {sid} (raw)', alpha=0.4, linestyle='dotted')
            plt.plot(sdf['ms'], filtered, label=f'Sensor {sid} (LPF, cutoff={cutoff:.1f}Hz, order={ORDER})')
        except Exception as e:
            plt.plot(sdf['ms'], sdf['distance'], label=f'Sensor {sid} (raw)')
    else:
        sampling_freqs.append((sid, 0))
        plt.plot(sdf['ms'], sdf['distance'], label=f'Sensor {sid} (raw)')

plt.xlabel('ms')
plt.ylabel('Distance [mm]')
freq_str = ', '.join([f'S{sid}: {freq:.2f}Hz' for sid, freq in sampling_freqs])
plt.title(f'Distance by Sensor (Lowpass filtered & Raw)\nSampling Freq: {freq_str}')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()

# --- 追加: フィルタ前後の周波数特性（パワースペクトル）を表示 ---
plt.figure(figsize=(10, 6))
for sid in df['sensor_id'].unique():
    sdf = df[df['sensor_id'] == sid].sort_values('ms')
    if len(sdf) > 1:
        delta_ms = sdf['ms'].diff().dropna()
        mean_delta = delta_ms.mean()
        freq = 1000.0 / mean_delta if mean_delta > 0 else 0
        if freq > 0:
            # フィルタ前
            raw = sdf['distance'].astype(float).values
            N = len(raw)
            yf_raw = abs(rfft(raw - raw.mean()))
            xf = rfftfreq(N, d=mean_delta/1000.0)
            # フィルタ後
            cutoff = min(CUTOFF_HZ, freq/2)
            try:
                filtered = lowpass_filter(raw, cutoff, freq, order=ORDER)
                yf_filt = abs(rfft(filtered - filtered.mean()))
                plt.plot(xf, yf_raw, label=f'S{sid} Raw', alpha=0.4, linestyle='dotted')
                plt.plot(xf, yf_filt, label=f'S{sid} LPF', alpha=0.8)
            except Exception as e:
                plt.plot(xf, yf_raw, label=f'S{sid} Raw', alpha=0.4, linestyle='dotted')
plt.xlabel('Frequency [Hz]')
plt.ylabel('Amplitude (FFT)')
plt.title('Frequency Spectrum (Raw vs Lowpass)')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()