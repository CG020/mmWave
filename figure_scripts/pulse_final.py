import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from icecream import ic

def process_csv_files_in_directory(root_folder, subfolder):
    visualizer_data_folder = os.path.join(root_folder, 'visualizer_data', subfolder)
    
    print(f"Checking folder: {visualizer_data_folder}")
    if not os.path.exists(visualizer_data_folder):
        print(f"Folder '{visualizer_data_folder}' does not exist.")
        return None, None

    all_parts_combined = []
    vitals_file_path = None

    for file in os.listdir(visualizer_data_folder):
        file_path = os.path.join(visualizer_data_folder, file)
        print(f"Found file: {file}")
        if file.endswith('vitals.csv'):
            vitals_file_path = file_path
            print(f"Vitals file found: {file}")
        elif file.endswith('.csv') and 'part' in file:
            all_parts_combined.append(pd.read_csv(file_path))
            print(f"Part file found: {file}")

    if vitals_file_path is None:
        print("No vitals file found!")
    if not all_parts_combined:
        print("No part files found!")

    return vitals_file_path, pd.concat(all_parts_combined, ignore_index=True) if all_parts_combined else None

def vitals_time_to_seconds(time_str):
    parts = time_str.split(':')
    if len(parts) == 2:
        m, s = map(int, parts)
        return m * 60 + s
    elif len(parts) == 1:
        return int(parts[0])
    else:
        raise ValueError(f"Unexpected time format: {time_str}")

def radar_time_to_seconds(time_str):
    return float(time_str) 

def process_csv_file(vitals_file_path, parts_combined, subfolder):
    if vitals_file_path is None or parts_combined is None:
        print(f"Required CSV files not found for {subfolder}.")
        return

    print(f"Processing {subfolder}")
    vitals = pd.read_csv(vitals_file_path)
    print(f"Columns in vitals file: {vitals.columns.tolist()}")
    print(f"First few rows of vitals file:\n{vitals.head()}")

    vitals_data = vitals.copy()
    
    vitals_data['Seconds'] = vitals_data['Time for Pulse'].apply(vitals_time_to_seconds).astype(float)
    parts_combined['Seconds'] = parts_combined['Timestamp'].apply(radar_time_to_seconds)

    parts_combined['Heart Rate'] = pd.to_numeric(parts_combined['Heart Rate'], errors='coerce')

    def find_closest_radar_heart_rate(target_time):
        closest_rows = parts_combined[parts_combined['Heart Rate'].notna()].iloc[
            (parts_combined[parts_combined['Heart Rate'].notna()]['Seconds'] - target_time).abs().argsort()[:1]
        ]
        return closest_rows['Heart Rate'].values[0] if not closest_rows.empty else np.nan

    vitals_data['Radar Heart Rate'] = vitals_data['Seconds'].apply(find_closest_radar_heart_rate)

    plt.figure(figsize=(12, 6))
    plt.plot(vitals_data['Marker'], vitals_data['Pulse'], 'o-', label='Manually Taken Heart Rate', color='blue')
    plt.plot(vitals_data['Marker'], vitals_data['Radar Heart Rate'], 'o-', label='Radar Heart Rate', color='red')
    plt.plot(vitals_data['Marker'], vitals_data['Heart'], 'o-', label='Polar H10 Heart Rate', color='green')

    plt.xlabel('Distance (Feet)')
    plt.ylabel('Heart Rate (BPM)')
    plt.title(f'Heart Rate Comparison - {subfolder}')
    plt.legend()
    plt.grid(True)

    plt.xticks(vitals_data['Marker'].unique()[::2])

    y_min = 30 
    y_max = 180
    plt.ylim(y_min, y_max)

    tick_interval = 10
    y_ticks = np.arange(y_min, y_max + 1, tick_interval)
    plt.yticks(y_ticks)

    plt.tight_layout()
    output_file_name = f"figures/pulse/{subfolder}_heart_comparison.png"
    os.makedirs(os.path.dirname(output_file_name), exist_ok=True)
    plt.savefig(output_file_name)
    plt.close()

    print(f"\nResults for {subfolder}:")
    print("Manually Taken Heart Rate Range:", 
          vitals_data['Pulse'].min(), "-", vitals_data['Pulse'].max())
    print("Radar Heart Rate Range:", 
          vitals_data['Radar Heart Rate'].min(), "-", vitals_data['Radar Heart Rate'].max())
    print("Polar H10 Heart Rate Range:", 
          vitals_data['Heart'].min(), "-", vitals_data['Heart'].max())
    print("\nFirst few rows of aligned data:")
    print(vitals_data[['Marker', 'Pulse', 'Radar Heart Rate', 'Heart']].head())

    avg_manual = vitals_data['Pulse'].mean()
    avg_radar = vitals_data['Radar Heart Rate'].mean()
    avg_polar = vitals_data['Heart'].mean()
    print(f"\nAverage Manually Taken Heart Rate: {avg_manual:.2f} BPM")
    print(f"Average Radar Heart Rate: {avg_radar:.2f} BPM")
    print(f"Average Polar H10 Heart Rate: {avg_polar:.2f} BPM")

    correlation_manual_radar = vitals_data['Pulse'].corr(vitals_data['Radar Heart Rate'])
    correlation_manual_polar = vitals_data['Pulse'].corr(vitals_data['Heart'])
    correlation_radar_polar = vitals_data['Radar Heart Rate'].corr(vitals_data['Heart'])
    print(f"\nCorrelation between Manual and Radar Heart Rate: {correlation_manual_radar:.2f}")
    print(f"Correlation between Manual and Polar H10 Heart Rate: {correlation_manual_polar:.2f}")
    print(f"Correlation between Radar and Polar H10 Heart Rate: {correlation_radar_polar:.2f}")

def process_all_groups(root_folder):
    visualizer_data_folder = os.path.join(root_folder, 'visualizer_data')
    
    print(f"Processing groups in: {root_folder}")
    print(f"Visualizer data folder: {visualizer_data_folder}")
    
    if not os.path.exists(visualizer_data_folder):
        print(f"Folder '{visualizer_data_folder}' does not exist.")
        return

    for subfolder in os.listdir(visualizer_data_folder):
        subfolder_path = os.path.join(visualizer_data_folder, subfolder)
        if os.path.isdir(subfolder_path):
            vitals_file_path, parts_combined = process_csv_files_in_directory(root_folder, subfolder)
            process_csv_file(vitals_file_path, parts_combined, subfolder)

if __name__ == "__main__":
    root_folder = '.'
    process_all_groups(root_folder)