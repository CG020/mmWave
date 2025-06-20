import os
import src.lib.directory as dir
from src.lib.globals import *
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from icecream import ic



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
        closest_rows = parts_combined[parts_combined['Heart Rate'].notna()].iloc[
            (parts_combined[parts_combined['Heart Rate'].notna()]['Seconds'] - target_time).abs().argsort()[:1]
        ]
        return closest_rows['Heart Rate'].values[0] if not closest_rows.empty else np.nan

    vitals_data['Radar Heart Rate'] = vitals_data['Seconds'].apply(find_closest_radar_heart_rate)
    ic(vitals_data['Radar Heart Rate'])
    return vitals_data



def main():
    root_folder = '.'
    vis_dir = os.path.join(root_folder, 'visualizer_data')

    for subfolder in os.listdir(vis_dir):
        subfolder_path = os.path.join(vis_dir, subfolder)
        if not os.path.isdir(subfolder_path) or \
              'aggregates' in subfolder or \
               '__pycache__' in subfolder:
            continue
        
        vitals, parts_combined = process_csv_files_in_directory(root_folder, subfolder)
        if vitals is not None and parts_combined is not None:
            print(f'Processing {subfolder}')
            vitals_data = generate_combined_data(vitals, parts_combined)
            outfile = f'heartrate_{subfolder}.csv'
            outpath = os.path.join(PROCESSED_DIR, outfile)
            df = pd.DataFrame(vitals_data)
            df.to_csv(outpath, index=False)



if __name__ == "__main__":
    main()
