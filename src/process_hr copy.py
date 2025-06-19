import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from icecream import ic


def vitals_time_to_seconds(time_str):
    parts = time_str.split(':')
    return int(parts[0]) * 60 + float(parts[1]) if len(parts) == 2 else float(time_str)


def radar_time_to_seconds(timestamp):
    try:
        h, m, s = timestamp.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        return np.nan


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

    if vitals_file_path is None:
        print("No vitals file found!")
        return None, None
    if not all_parts_combined:
        print("No part files found!")
        return None, None

    vitals_df = pd.read_csv(vitals_file_path)
    parts_df = pd.concat(all_parts_combined, ignore_index=True)
    return vitals_df, parts_df


def generate_combined_data(vitals, parts_combined):
    vitals_data = vitals.copy()

    vitals_data['Seconds'] = vitals_data['Time for Pulse'].apply(vitals_time_to_seconds).astype(float)
    parts_combined['Seconds'] = parts_combined['Timestamp'].apply(radar_time_to_seconds)
    parts_combined['Heart Rate'] = pd.to_numeric(parts_combined['Heart Rate'], errors='coerce')

    def find_closest_radar_heart_rate(target_time):
        valid = parts_combined[parts_combined['Heart Rate'].notna()]
        if valid.empty:
            return np.nan
        closest = valid.iloc[(valid['Seconds'] - target_time).abs().argsort()[:1]]
        return closest['Heart Rate'].values[0] if not closest.empty else np.nan

    vitals_data['Radar Heart Rate'] = vitals_data['Seconds'].apply(find_closest_radar_heart_rate)

    return vitals_data


def main():
    root_folder = '.'
    vis_dir = os.path.join(root_folder, 'visualizer_data')

    for subfolder in os.listdir(vis_dir):
        
        vitals, parts_combined = process_csv_files_in_directory(root_folder, subfolder)
        if vitals is not None and parts_combined is not None:
            vitals_data = generate_combined_data(vitals, parts_combined, subfolder)
            ic(vitals_data)
            


if __name__ == "__main__":
    main()
