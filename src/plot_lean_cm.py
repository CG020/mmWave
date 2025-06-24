import os
from icecream import ic
import src.lib.directory as dir
from src.lib.globals import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import src.lib.plot_styles as ps
from typing import Tuple, List, Dict


def vitals_time_to_seconds(time_str):
    if pd.isna(time_str):
        return np.nan

    if ':' in time_str:
        minutes, seconds = time_str.split(':')
        return int(minutes) * 60 + int(seconds)
    
    return int(time_str)


def radar_time_to_seconds(time_str):
    return float(time_str) 


def homogenize_trial_files(files: List[str]) -> Tuple[pd.DataFrame]:
    sensor_data = []
    
    for file in files:
        if 'vitals' in file:
            vitals_df = pd.read_csv(file)
        else:
            sensor_data.append(pd.read_csv(file))

    sensor_df = pd.concat(sensor_data, ignore_index=True)
    return vitals_df, sensor_df


def process_trial(vitals_df: pd.DataFrame, sensor_df: pd.DataFrame) -> pd.DataFrame:
    vitals_df['start seconds'] = vitals_df['Start'].apply(vitals_time_to_seconds).astype(float)
    vitals_df['end seconds'] = vitals_df['End'].apply(vitals_time_to_seconds).astype(float)
    sensor_df['seconds'] = sensor_df['Timestamp'].apply(radar_time_to_seconds)
    sensor_df['leaning angle'] = pd.to_numeric(sensor_df['Leaning Angle'], errors='coerce')
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

    return out_df


def aggregate_data() -> pd.DataFrame:
    actual_lean_all = []
    agreement_all = []

    trial_dirs = dir.dir_search('chair', root_dir=RAW_DIR)
    for trial in trial_dirs:
        files = dir.file_search_subdirs(trial, directory=RAW_DIR)

        vitals_df, radar_df = homogenize_trial_files(files)
        trial_df = process_trial(vitals_df, radar_df)

        actual_lean_all.extend(trial_df['lean_direction'].tolist())
        agreement_all.extend(trial_df['agreement'].tolist())

    df = pd.DataFrame({
        'actual lean': actual_lean_all,
        'agreement': agreement_all
    })
    return df



def print_output(df: pd.DataFrame) -> None:
    left_accuracy = len(
        df[(df['agreement'] == True) & (df['actual lean'] == 'left')]) \
        / len(df[df['actual lean'] == 'left']
    )
    right_accuracy = len(
        df[(df['agreement'] == True) & (df['actual lean'] == 'right')]) \
        / len(df[df['actual lean'] == 'right']
    )
    total_accuracy = len(df[df['agreement'] == True]) / len(df)

    ic(left_accuracy, right_accuracy, total_accuracy)
    left = len(df[df['actual lean'] == 'left'])
    right = len(df[df['actual lean'] == 'right'])
    ic(left, right)



def main():
    df = aggregate_data()
    print_output(df)
    return


if __name__ == "__main__":
    main()
