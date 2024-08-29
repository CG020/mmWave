import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

pulse_results = pd.read_csv('visualizer_data/aggregates/pulse_results.csv')
breath_results = pd.read_csv('visualizer_data/aggregates/breath_results.csv')
averages_by_distance = pd.read_csv('visualizer_data/aggregates/pulse_breath_averages_by_distance.csv')

markers_of_interest = [1, 5, 10, 15]
filtered_averages = averages_by_distance[averages_by_distance['Distance'].isin(markers_of_interest)]

grouped_averages = filtered_averages.groupby('Distance').agg({
    'Pulse': 'mean',
    'Radar Heart Rate': 'mean',
    'Heart': 'mean',
    'Breath': 'mean',
    'Radar Breath Rate': 'mean'
}).reset_index()

plt.figure(figsize=(10, 6))
bar_width = 0.2
index = np.arange(len(grouped_averages))

plt.bar(index - bar_width, grouped_averages['Pulse'], bar_width, label='Manual Pulse')
plt.bar(index, grouped_averages['Radar Heart Rate'], bar_width, label='Radar Pulse')
plt.bar(index + bar_width, grouped_averages['Heart'], bar_width, label='Polar Pulse')

plt.xlabel('Distance (Feet)', weight='bold', fontsize=12)
plt.ylabel('Average Pulse Rate (BPM)', weight='bold', fontsize=12)
plt.title('Average Pulse Rates by Marker', weight='bold', fontsize=14)

plt.xticks(index, grouped_averages['Distance'],  ha='right', fontsize=11, weight='bold')
plt.yticks(fontsize=11, weight='bold')

ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.legend(loc='center right')
plt.tight_layout()

output_pulse_file = 'figures/combined_marker_averages_pulse.png'
plt.savefig(output_pulse_file)
plt.close()

plt.figure(figsize=(10, 6))
bar_width = 0.3
index = np.arange(len(grouped_averages))

plt.bar(index, grouped_averages['Breath'], bar_width, label='Manual Breath')
plt.bar(index + bar_width, grouped_averages['Radar Breath Rate'], bar_width, label='Radar Breath')

plt.xlabel('Distance (Feet)', weight='bold', fontsize=12)
plt.ylabel('Average Breath Rate (BPM)', weight='bold', fontsize=12)
plt.title('Average Breath Rates by Distance', weight='bold', fontsize=14)

plt.xticks(index + bar_width / 2, grouped_averages['Distance'], ha='right', fontsize=11, weight='bold')
plt.yticks(fontsize=11, weight='bold')

ax = plt.gca()
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.legend()
plt.tight_layout()

output_breath_file = 'figures/combined_marker_averages_breath.png'
plt.savefig(output_breath_file)
plt.close()
