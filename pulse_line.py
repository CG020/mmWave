import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from icecream import ic

current = 'floor_AARON_stand'

def process_csv_files_in_directory(root_folder, subfolder):
    visualizer_data_folder = os.path.join(root_folder, 'visualizer_data', subfolder)
    
    if not os.path.exists(visualizer_data_folder):
        print(f"Folder '{visualizer_data_folder}' does not exist.")
        return None, None

    all_parts_combined = []
    vitals_file_path = None

    for file in os.listdir(visualizer_data_folder):
        file_path = os.path.join(visualizer_data_folder, file)
        if file.endswith('vitals.csv'):
            vitals_file_path = file_path
        elif file.endswith('.csv') and 'part' in file:
            all_parts_combined.append(pd.read_csv(file_path))

    return vitals_file_path, pd.concat(all_parts_combined, ignore_index=True) if all_parts_combined else None

def process_csv_file(vitals_file_path, parts_combined, subfolder):
    if vitals_file_path is None or parts_combined is None:
        print("Required CSV files not found.")
        return

    vitals = pd.read_csv(vitals_file_path)
    pulse_data = vitals[vitals['Type'] == 'pulse'].copy()
    pulse_data['Time_Diff'] = pulse_data['Timestamp'].diff()
    pulse_data['Physical_Heart_Rate'] = 60 / pulse_data['Time_Diff']

    def find_closest_heart_rate(timestamp):
        idx = (parts_combined['Timestamp'] - timestamp).abs().idxmin()
        return parts_combined.loc[idx, 'Heart Rate']

    pulse_data['Measured_Heart_Rate'] = pulse_data['Timestamp'].apply(find_closest_heart_rate)

    pulse_data = pulse_data.replace([np.inf, -np.inf], np.nan).dropna()

    print("Pulse data info:")
    print(pulse_data.info())
    print("\nPulse data description:")
    print(pulse_data.describe())

    plt.figure(figsize=(14, 7))

    plt.scatter(pulse_data['Timestamp'], pulse_data['Physical_Heart_Rate'], 
                label='Taken Heart Rate', marker='o', color='blue', alpha=0.6)
    plt.scatter(pulse_data['Timestamp'], pulse_data['Measured_Heart_Rate'], 
                label='Radar Heart Rate', marker='o', color='red', alpha=0.6)

    plt.xlabel('Time (Minutes)')
    plt.ylabel('Heart Rate (BPM)')
    plt.title('Taken Heart Rate vs MMWave Radar Heart Rate')
    plt.legend()
    plt.grid(True)
    plt.minorticks_on()

    y_min = max(40, min(pulse_data['Physical_Heart_Rate'].min(), pulse_data['Measured_Heart_Rate'].min()) - 10)
    y_max = min(150, max(pulse_data['Physical_Heart_Rate'].max(), pulse_data['Measured_Heart_Rate'].max()) + 10)
    plt.ylim(y_min, y_max)

    plt.xticks(rotation=45)
    plt.tight_layout()

    output_file_name = f"{subfolder}_heart_comparison.png"
    plt.savefig(output_file_name)
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

if __name__ == "__main__":
    root_folder = '.'
    vitals_file_path, parts_combined = process_csv_files_in_directory(root_folder, current)
    process_csv_file(vitals_file_path, parts_combined, current)
