import os
import src.lib.directory as dir
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict
from src.lib.globals import *


def homogenize_trial_files(files: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    sensor_data = []

    for file in files:
        if 'vitals_df' in file:
            vitals_df = pd.read_csv(file)
        else:
            sensor_data.append(pd.read_csv(file))

    sensor_df = pd.concat(sensor_data, ignore_index=True)
    return vitals_df, sensor_df


def vitals_time_to_seconds(time_str):
    if pd.isna(time_str):
        return np.nan

    if ':' in time_str:
        minutes, seconds = time_str.split(':')
        return int(minutes) * 60 + int(seconds)
    
    return int(time_str)


def radar_time_to_seconds(time_str):
    return float(time_str) 


def process_trial(vitals_df: pd.DataFrame, sensor_df: pd.DataFrame) -> pd.DataFrame:
    # TODO: at this point, process the heart rate, respiratory rate, and lean all at once
    # this *should work, haven't tested it yet, and also should probably be refactored 
    # for the sake of readability 

    vitals_df['start seconds'] = vitals_df['Start'].apply(vitals_time_to_seconds).astype(float)
    vitals_df['end seconds'] = vitals_df['End'].apply(vitals_time_to_seconds).astype(float)
    vitals_df['Seconds'] = vitals_df['Time for Breath'].apply(vitals_time_to_seconds).astype(float)
    
    sensor_df['seconds'] = sensor_df['Timestamp'].apply(radar_time_to_seconds)
    sensor_df['leaning angle'] = pd.to_numeric(sensor_df['Leaning Angle'], errors='coerce')
    sensor_df['Breath Rate'] = pd.to_numeric(sensor_df.get('Breath Rate'), errors='coerce')
    sensor_df['Heart Rate'] = pd.to_numeric(sensor_df['Heart Rate'], errors='coerce')
    
    valid_sensor_data = sensor_df[sensor_df['Breath Rate'].notna()]
    def get_nearest_breath_rate(time_sec):
        time_diffs = (valid_sensor_data['Seconds'] - time_sec).abs()
        nearest_idx = time_diffs.idxmin() if not time_diffs.empty else None
        return valid_sensor_data.loc[nearest_idx, 'Breath Rate'] if nearest_idx is not None else np.nan

    vitals_df['Radar Breath Rate'] = vitals_df['Seconds'].apply(get_nearest_breath_rate)
    def find_closest_radar_heart_rate(target_time):
        closest_rows = sensor_df[sensor_df['Heart Rate'].notna()].iloc[
            (sensor_df[sensor_df['Heart Rate'].notna()]['Seconds'] - target_time).abs().argsort()[:1]
        ]
        return closest_rows['Heart Rate'].values[0] if not closest_rows.empty else np.nan

    vitals_df['Radar Heart Rate'] = vitals_df['Seconds'].apply(find_closest_radar_heart_rate)    
    
    out_df = vitals_df.copy()

    def compute_radar_lean(row) -> float:
        relevant_rows = sensor_df[
            (sensor_df['seconds'] >= row['start seconds']) &
            (sensor_df['seconds'] <= row['end seconds'])
        ]
        return relevant_rows['leaning angle'].mean()
    
    out_df['radar lean angle'] = vitals_df.apply(compute_radar_lean, axis=1)

    def is_same_lean(row) -> bool:
        if row['lean_direction'] == 'left':
            return row['radar lean angle'] > 5
        elif row['lean_direction'] == 'right':
            return row['radar lean angle'] < -5
        return False

    out_df['agreement'] = out_df.apply(is_same_lean, axis=1)
    
    return


def get_outpath(trial_name: str) -> str:
    RADAR_POS = 0
    SUBJECT_NAME = 1
    SUBJECT_POS = 2

    SUBJECT_MAP = {
        'aaron' : 0,
        'candice' : 1,
        'jesus' : 2,
        'linda' : 3,
        'mikhail' : 4,
        'natalie' : 5
    }

    trial_parts = trial_name.split('_')
    
    radar_position = trial_parts[RADAR_POS]
    subject_numb = SUBJECT_MAP[trial_parts[SUBJECT_NAME].lower()]
    subject_pos = trial_parts[SUBJECT_POS]

    out_trial_name = '_'.join(radar_position, subject_numb, subject_pos)
    out_file = out_trial_name + '.csv'
    outpath = os.path.join(PROCESSED_DIR, out_file)
    
    return outpath


def main():
    trial_dirs = dir.dir_search('floor', 'tripod', root_dir=RAW_DIR)
    
    for trial in trial_dirs:
        files = dir.file_search_subdirs(trial, directory=RAW_DIR)
        vitals_df, radar_df = homogenize_trial_files(files)
        trial_df = process_trial(vitals_df, radar_df)
        
        trial_path = get_outpath(trial)
        trial_df.to_csv(trial_path)

    return


if __name__ == "__main__":
    main()
