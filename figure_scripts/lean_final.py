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

    parts_combined['Leaning Angle'] = pd.to_numeric(parts_combined['Leaning Angle'], errors='coerce')

    def find_closest_radar_lean(target_time):
        closest_rows = parts_combined[parts_combined['Leaning Angle'].notna()].iloc[
            (parts_combined[parts_combined['Leaning Angle'].notna()]['Seconds'] - target_time).abs().argsort()[:1]
        ]
        return closest_rows['Leaning Angle'].values[0] if not closest_rows.empty else np.nan

    vitals_data['Radar Lean Angle'] = vitals_data['Seconds'].apply(find_closest_radar_lean)

    plt.figure(figsize=(12, 6))
    
    plt.scatter(vitals_data['Marker'], vitals_data['Radar Lean Angle'], color='blue', label='Radar Lean Angle')

    plt.plot(vitals_data['Marker'], vitals_data['Radar Lean Angle'], color='blue', alpha=0.5)

    plt.xlabel('Distance (Marker)')
    plt.ylabel('Lean Angle (Degrees)')
    plt.title(f'Radar Lean Angle Over Distance - {subfolder}')
    plt.legend()
    plt.grid(True)

    plt.xticks(vitals_data['Marker'].unique())

    y_min = vitals_data['Radar Lean Angle'].min()
    y_max = vitals_data['Radar Lean Angle'].max()
    y_range = y_max - y_min
    y_bottom = y_min - y_range * 0.1
    y_top = y_max + y_range * 0.1
    plt.ylim(y_bottom, y_top)

    tick_interval = max(10, int(y_range / 10))
    y_ticks = np.arange(int(y_bottom), int(y_top) + 1, tick_interval)
    plt.yticks(y_ticks)

    plt.axhline(y=0, color='red', linestyle='--', label='Upright')

    plt.tight_layout()
    output_file_name = f"figures/lean/{subfolder}_radar_lean_angle.png"
    os.makedirs(os.path.dirname(output_file_name), exist_ok=True)
    plt.savefig(output_file_name)
    plt.close()

    print(f"\nResults for {subfolder}:")
    print("Radar Lean Angle Range:", 
          vitals_data['Radar Lean Angle'].min(), "-", vitals_data['Radar Lean Angle'].max())
    print("\nFirst few rows of aligned data:")
    print(vitals_data[['Marker', 'Radar Lean Angle']].head())

    avg_lean = vitals_data['Radar Lean Angle'].mean()
    print(f"\nAverage Radar Lean Angle: {avg_lean:.2f} degrees")

    total_readings = len(vitals_data)
    left_lean = (vitals_data['Radar Lean Angle'] < -5).sum() / total_readings * 100
    right_lean = (vitals_data['Radar Lean Angle'] > 5).sum() / total_readings * 100
    upright = ((vitals_data['Radar Lean Angle'] >= -5) & (vitals_data['Radar Lean Angle'] <= 5)).sum() / total_readings * 100

    print(f"\nPercentage of time leaning left (radar): {left_lean:.2f}%")
    print(f"Percentage of time leaning right (radar): {right_lean:.2f}%")
    print(f"Percentage of time upright (radar): {upright:.2f}%")

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