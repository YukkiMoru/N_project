import os
import csv
import yaml
import numpy as np
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt

def load_yml_data(dir_workspace, setting_filename="setting.yml"):
    """
    設定ファイル（setting.yml）から設定を読み込む関数
    戻り値: mode, timing_budget_us, inter_measurement_ms
    """
    setting_path = os.path.join(dir_workspace, setting_filename)
    with open(setting_path, "r", encoding="utf-8") as f:
        setting = yaml.safe_load(f)
    mode = setting["mode"]
    timing_budget_us = setting["timing_budget_us"]
    inter_measurement_ms = setting["inter_measurement_ms"]
    return mode, timing_budget_us, inter_measurement_ms

def load_csv_data(dir_raw_data, mode, timing_budget_us, inter_measurement_ms):
    """
    指定されたパラメータに基づいてCSVファイルからデータを読み込み、timesとdistancesのnp.arrayを返す。
    """
    csv_name = os.path.join(dir_raw_data, f"{mode}_{timing_budget_us}us_{inter_measurement_ms}ms.csv")
    if not os.path.exists(csv_name):
        raise FileNotFoundError(f"CSV file not found: {csv_name}")
    times = []
    distances = []
    with open(csv_name, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # ヘッダーをスキップ
        for row in reader:
            try:
                t = int(row[0])
                d = int(row[1])
                times.append(t)
                distances.append(d)
            except (ValueError, IndexError):
                continue
    return np.array(times), np.array(distances)

def lowpass_filter(data, fs, fc, order=4):
    """
    バターワースローパスフィルターを適用する関数
    data: フィルタ対象データ（リストまたは1次元np.array）
    fs: サンプリング周波数 [Hz]
    fc: カットオフ周波数 [Hz]
    order: フィルター次数（デフォルト4）
    """
    if len(data) < order + 1:
        return data
    nyq = 0.5 * fs
    normal_cutoff = fc / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, data)

def find_stable_sections_data(times, filtered_distances, window_ms=500, std_threshold=0.5, distance_similarity_threshold=5.0):
    """
    安定している区間を検出し、その情報をリストとして返す。
    times: 時間配列
    filtered_distances: フィルタ済み距離データ
    window_ms: ウィンドウサイズ[ms]
    std_threshold: 標準偏差のしきい値
    distance_similarity_threshold: 同程度の距離とみなす閾値[mm]。この値未満の差は類似と判断。
    戻り値: (検出した区間数, 検出した区間のリスト [(start_time, end_time, avg_dist), ...])
    """
    if times.size < 2:
        return 0, []
    dt = times[1] - times[0]
    if dt == 0:
        return 0, []
    window_size = int(window_ms / dt)
    if window_size <= 0:
        return 0, []
    if len(filtered_distances) < window_size:
        return 0, []
    used = np.zeros(len(times), dtype=bool)
    stable_sections_list = []
    detected_count = 0
    i = 0
    while i <= len(times) - window_size:
        current_window_indices = slice(i, i + window_size)
        if np.any(used[current_window_indices]):
            i += 1
            continue
        window_data = filtered_distances[current_window_indices]
        if len(window_data) < window_size:
            i += 1
            continue
        std = np.std(window_data)
        if std <= std_threshold:
            current_avg_distance = np.mean(window_data)
            is_too_similar = False
            if distance_similarity_threshold is not None:
                for _, _, existing_avg_dist in stable_sections_list:
                    if abs(current_avg_distance - existing_avg_dist) < distance_similarity_threshold:
                        is_too_similar = True
                        break
            if is_too_similar:
                i += 1
                continue
            stable_start_time = times[i]
            stable_end_time = times[i + window_size - 1]
            stable_sections_list.append((stable_start_time, stable_end_time, current_avg_distance))
            used[current_window_indices] = True
            detected_count += 1
            i += window_size
        else:
            i += 1
    return detected_count, stable_sections_list

def plot_highlighted_sections(sections_data, color='cyan', alpha=0.2, show_section_number=False, text_y_position=630):
    """
    与えられた区間データをグラフ上にハイライト描画する。
    sections_data: 安定区間のリスト [(start_time, end_time, avg_dist), ...]
    color: ハイライト色
    alpha: ハイライトの透明度
    show_section_number: 区間番号を表示するかどうか（デフォルト: False）
    text_y_position: 区間番号テキストのY座標
    """
    for idx, (start_time, end_time, _) in enumerate(sections_data):
        plt.axvspan(start_time, end_time, color=color, alpha=alpha)
        if show_section_number:
            text_x = (start_time + end_time) / 2
            plt.text(text_x, text_y_position, str(idx + 1), ha='center', va='top', fontsize=10)

def print_stable_sections(found_sections_with_dist):
    print(f"No., start[ms], end[ms]")
    for idx, (start, end, avg) in enumerate(found_sections_with_dist, 1):
        print(f"{idx},{start},{end}")

def narrow_stable_sections(sections, narrow_margin_ms=200):
    narrowed = []
    for start, end, avg in sections:
        new_start = start + narrow_margin_ms
        new_end = end - narrow_margin_ms
        if new_start < new_end:
            narrowed.append((new_start, new_end, avg))
    return narrowed

def write_stable_sections_to_csv(sections, dir_workspace, filename="narrow_sections.csv", list_target=None):
    output_path = os.path.join(dir_workspace, filename)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['No.', 'Start[ms]', 'End[ms]', 'Target Distance[mm]'])
        for idx, (start, end, _) in enumerate(sections, 1):
            target_value = list_target[idx - 1] if list_target is not None and idx - 1 < len(list_target) else ""
            writer.writerow([idx, start, end, target_value])
