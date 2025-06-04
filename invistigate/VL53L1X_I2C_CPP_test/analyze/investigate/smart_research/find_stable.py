import matplotlib.pyplot as plt
import os
import numpy as np

from lib.common_analysis import (
    load_yml_data,
    load_csv_data,
    lowpass_filter,
    find_stable_sections_data,
    plot_highlighted_sections,
    print_stable_sections,
    narrow_stable_sections,
    write_stable_sections_to_csv
)

# plt.style.use('dark_background')

dir_workspace = "analyze/investigate/smart_research"
mode, timing_budget_us, inter_measurement_ms = load_yml_data(dir_workspace)
dir_raw_data = os.path.join(dir_workspace, "raw_data")
times, distances = load_csv_data(dir_raw_data, mode, timing_budget_us, inter_measurement_ms)

fs = 100  # サンプリング周波数[Hz]
fc = 2    # カットオフ周波数[Hz]
filtered_distances = lowpass_filter(distances, fs, fc)

plt.plot(times, distances, 'g-', label='Raw')
plt.plot(times, filtered_distances, 'b-', label='LP')

window_ms = 300
std_threshold = 2.0
similarity_th = 10.0

detected_count, found_sections = find_stable_sections_data(
    times, filtered_distances, window_ms, std_threshold, distance_similarity_threshold=similarity_th)

plot_highlighted_sections(found_sections, color='cyan', alpha=0.2, show_section_number=True, text_y_position=630)
print(f"発見された安定区間数: {detected_count}（標準偏差しきい値: {std_threshold}, 距離類似性しきい値: {similarity_th} mm）")
print_stable_sections(found_sections)

narrowed_sections = narrow_stable_sections(found_sections, 500)
plot_highlighted_sections(narrowed_sections, color='orange', alpha=0.3)
print("\n狭めた安定区間:")
print_stable_sections(narrowed_sections)

list_target = np.arange(500, 0, -50)
sections_dir = os.path.join(dir_workspace, "sections")
os.makedirs(sections_dir, exist_ok=True)
write_stable_sections_to_csv(narrowed_sections, sections_dir, "narrowed_stable_sections.csv", list_target=list_target)

plt.xlabel('Time [ms]')
plt.ylabel('Distance [mm]')
plt.title(f'VL53L1X Distance Sensor: {mode} {timing_budget_us}us {inter_measurement_ms}ms')
plt.grid()
plt.yticks(range(0, 700, 50))
plt.legend()
plt.show()