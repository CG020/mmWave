import pandas as pd
import numpy as np
import os
import src.lib.directory as dir
from src.lib.globals import *
from icecream import ic


def process_trial(directory: str):
    sensor_data = []
    vitals_file_path = None

    for file in os.listdir(directory):
        filepath = os.path.join(directory, file)

        if file.endswith('vitals.csv'):
            vitals_file_path = filepath
        elif file.endswith('.csv') and 'part' in file:
            sensor_data.append(pd.read_csv(filepath))

    if vitals_file_path is None:
        print(f'Could not find vitals for {directory}')
        os._exit(1)
    if not sensor_data:
        print(f'Could not find sensor data for {directory}')
        os._exit(1)

    cleansed_sensor_data = pd.concat(sensor_data, ignore_index=True) if sensor_data else None

    return vitals_file_path, cleansed_sensor_data


def vitals_time_to_seconds(time_str):
    parts = time_str.split(':')
    if len(parts) == 2:
        m, s = map(int, parts)
        return m * 60 + s
    else:
        raise ValueError(f'Unexpected time format in vitals: {time_str}')


def radar_time_to_seconds(time_str):
    return float(time_str)


def process_csv_file2(vitals_filepath: str, sensor_data: pd.DataFrame) -> pd.DataFrame:
    vitals_df = pd.read_csv(vitals_filepath)
    vitals_df = vitals_df.copy()

    vitals_df['Seconds'] = vitals_df['Time for breath'].apply(vitals_time_to_seconds).astype(float)
    sensor_data = sensor_data.copy()
    sensor_data['Seconds'] = sensor_data['Timestamp'].apply(radar_time_to_seconds)
    sensor_data['Breath Rate'] = pd.to_numeric(sensor_data.get('Breath Ratae'), errors='coerce')
    valid_sensor_data = sensor_data[sensor_data['Breath Rate'].notna()]

    def get_nearest_breath_rate(time_sec):
        time_diffs = (valid_sensor_data['Seconds'] - time_sec).abs()
        nearest_idx = time_diffs.idxmin() if not time_diffs.empty else None
        return valid_sensor_data.loc[nearest_idx, 'Breath Rate'] if nearest_idx is not None else np.nan

    vitals_df['Radar Breath Rate'] = vitals_df['Seconds'].apply(get_nearest_breath_rate)
    return vitals_df



def process_csv_file(vitals_filepath: str, sensor_data: pd.DataFrame) -> pd.DataFrame:
    vitals_df = pd.read_csv(vitals_filepath)
    out_df = vitals_df.copy()

    out_df['Seconds'] = out_df['Time for Breath'].apply(vitals_time_to_seconds).astype(float)
    sensor_data['Seconds'] = sensor_data['Timestamp'].apply(radar_time_to_seconds)
    sensor_data['Breath Rate'] = pd.to_numeric(sensor_data['Breath Rate'], errors='coerce')

    def find_closest_radar_breath(target_time):
        closest_rows = sensor_data[sensor_data['Breath Rate'].notna()].iloc[
            (
                sensor_data[sensor_data['Breath Rate'].notna()]['Seconds'] - target_time
            ).abs().argsort()[:1]
        ]
        return closest_rows['Breath Rate'].values[0] if not closest_rows.empty else np.nan
    
    out_df['Radar Breath Rate'] = out_df['Seconds'].apply(find_closest_radar_breath)

    return out_df


def main():
    vis_dir = os.path.join(CODE_DIR, 'visualizer_data')
    if not os.path.exists(vis_dir):
        return
    
    for subfolder in os.listdir(vis_dir):
        if 'aggregates' in subfolder:
            continue
        
        if '__pycache__' in subfolder:
            continue


        subfolder_path = os.path.join(vis_dir, subfolder)
        if not os.path.isdir(subfolder_path):
            continue

        trial_dir = os.path.join(CODE_DIR, 'visualizer_data', subfolder)
        vitals_df, parts_df = process_trial(trial_dir)
        trial_data = process_csv_file(vitals_df, parts_df)
        
        
        df = pd.DataFrame(trial_data)
        outfile = f'breath_{subfolder}.csv'
        outpath = os.path.join(PROCESSED_DIR, outfile)
        df.to_csv(outpath, index=False)
    
    return


if __name__ == "__main__":
    main()
