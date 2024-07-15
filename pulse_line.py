import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from icecream import ic

vitals = pd.read_csv('visualizer_data/floor_LINDA_stand/floor_LINDA_stand_vitals.csv')

pulse_data = vitals[vitals['Type'] == 'pulse'].copy()

pulse_data['Time_Diff'] = pulse_data['Timestamp'].diff()
pulse_data['Physical_Heart_Rate'] = 60 / pulse_data['Time_Diff']

# Load and combinepart CSVs
part_files = [
    'visualizer_data/floor_LINDA_stand/floor_LINDA_stand_20240710_103602_part0.csv',
    'visualizer_data/floor_LINDA_stand/floor_LINDA_stand_20240710_104102_part1.csv',
    'visualizer_data/floor_LINDA_stand/floor_LINDA_stand_20240710_104602_part2.csv',
    'visualizer_data/floor_LINDA_stand/floor_LINDA_stand_20240710_105102_part3.csv',
    'visualizer_data/floor_LINDA_stand/floor_LINDA_stand_20240710_105602_part4.csv',
    'visualizer_data/floor_LINDA_stand/floor_LINDA_stand_20240710_110102_part5.csv',
    'visualizer_data/floor_LINDA_stand/floor_LINDA_stand_20240710_110603_part6.csv'
]

parts_combined = pd.concat([pd.read_csv(file) for file in part_files], ignore_index=True)
# ic(parts_combined)

# closest heart rate from parts_combined
def find_closest_heart_rate(timestamp):
    idx = (parts_combined['Timestamp'] - timestamp).abs().idxmin()
    return parts_combined.loc[idx, 'Heart Rate']

# corresponding heart rates from parts_combined
pulse_data['Measured_Heart_Rate'] = pulse_data['Timestamp'].apply(find_closest_heart_rate)

pulse_data = pulse_data.replace([np.inf, -np.inf], np.nan).dropna()

print("Pulse data info:")
print(pulse_data.info())
print("\nPulse data description:")
print(pulse_data.describe())


plt.figure(figsize=(14, 7))

plt.scatter(pulse_data['Timestamp'], pulse_data['Physical_Heart_Rate'], 
            label='Physical Vitals', marker='o', color='blue', alpha=0.6)
plt.scatter(pulse_data['Timestamp'], pulse_data['Measured_Heart_Rate'], 
            label='Measured Heart Rate', marker='o', color='red', alpha=0.6)

plt.xlabel('Time')
plt.ylabel('Heart Rate (BPM)')
plt.title('Physical Vitals vs Measured Heart Rate')
plt.legend()
plt.grid(True)

y_min = max(40, min(pulse_data['Physical_Heart_Rate'].min(), pulse_data['Measured_Heart_Rate'].min()) - 10)
y_max = min(150, max(pulse_data['Physical_Heart_Rate'].max(), pulse_data['Measured_Heart_Rate'].max()) + 10)
plt.ylim(y_min, y_max)

plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig('Heart_Rate_Comparison.png')
plt.show()

print("\nPhysical Heart Rate Range:", 
      pulse_data['Physical_Heart_Rate'].min(), "-", pulse_data['Physical_Heart_Rate'].max())
print("Measured Heart Rate Range:", 
      pulse_data['Measured_Heart_Rate'].min(), "-", pulse_data['Measured_Heart_Rate'].max())
print("\nFirst few rows of aligned data:")
print(pulse_data[['Timestamp', 'Physical_Heart_Rate', 'Measured_Heart_Rate']].head())

print("\nUnique timestamps in pulse_data:", pulse_data['Timestamp'].nunique())
print("Total rows in pulse_data:", len(pulse_data))
print("\nUnique timestamps in parts_combined:", parts_combined['Timestamp'].nunique())
print("Total rows in parts_combined:", len(parts_combined))