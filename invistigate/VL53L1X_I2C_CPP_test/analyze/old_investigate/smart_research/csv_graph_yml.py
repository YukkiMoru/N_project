import matplotlib.pyplot as plt
import os
from lib.common_analysis import load_yml_data, load_csv_data

# --- 設定ファイル（setting.yml）から読み込み ---
dir_workspace = os.path.dirname(__file__)
mode, timing_budget_us, inter_measurement_ms = load_yml_data(dir_workspace)
file_path = os.path.join(dir_workspace, "raw_data")

times, distances = load_csv_data(file_path, mode, timing_budget_us, inter_measurement_ms)

plt.plot(times, distances, 'b-')
plt.xlabel('Time [ms]')
plt.ylabel('Distance [mm]')
plt.title('VL53L1X Distance Sensor: '+str(mode)+" "+ str(timing_budget_us)+"us "+str(inter_measurement_ms)+"ms")
plt.grid()
plt.yticks(range(0, 700, 50))
plt.show()