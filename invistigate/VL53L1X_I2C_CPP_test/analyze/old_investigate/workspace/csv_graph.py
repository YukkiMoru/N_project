import matplotlib.pyplot as plt
import csv

times = []
distances = []

with open('distance_data.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # ヘッダーをスキップ
    for row in reader:
        t, d = map(int, row)
        times.append(t)
        distances.append(d)

plt.plot(times, distances, 'b-')
plt.xlabel('Time [ms]')
plt.ylabel('Distance [mm]')
plt.title('VL53L1X Distance Sensor')
plt.show()