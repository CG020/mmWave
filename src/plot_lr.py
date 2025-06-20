import pandas as pd
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import os
import src.lib.directory as dir
from src.lib.globals import *
import numpy as np
import scipy.stats as stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder
from icecream import ic


def determine_physio_mode(*data_col: Tuple[str]) -> str:
    for _,col in enumerate(data_col):
        if 'heart' in col.lower():
            return 'heartrate'
        elif 'breath' in col.lower():
            return 'breath'
    else:
        print(f"Physio mode not found for column: {data_col}")
        os._exit(1)


def get_trial_info(filename: str) -> Dict:
    base = os.path.basename(filename)
    lowercased_base = base.lower()
    og_file_split = lowercased_base.replace('.csv', '').split('_')
    _PHYSIO = 0
    RADAR_POSITION = 1
    SUBJECT = 2
    POSTURE = 3

    SUBJECT_MAPPING = {
        'aaron': '1',
        'linda': '2',
        'jesus': '3',
        'candice': '4',
        'mikhail': '5',
        'natalie': '6'
    }

    trial_info = {
        'subject' : SUBJECT_MAPPING[og_file_split[SUBJECT]],
        'radar position' : og_file_split[RADAR_POSITION],
        'posture' : og_file_split[POSTURE]
    }

    return trial_info


def aggregate_data(a_modality: str, b_modality: str) -> pd.DataFrame:
    physio_mode = determine_physio_mode(a_modality, b_modality)
    files = dir.search(physio_mode, directory=PROCESSED_DIR)

    temp_lst = []

    def get_trial_data(df: pd.DataFrame) -> Dict:
        a = df[a_modality].values
        b = df[b_modality].values
        markers = df['Marker'].values
        out_data = [
            {'distance': int(marker), 'diff': float(diff)}
            for marker, diff in zip(markers, a - b)
        ]
        return out_data
    
    for file in files:
        temp_df = dir.file_to_df(file)
        trial_info = get_trial_info(file)

        for row in get_trial_data(temp_df):
            combined_row = {**trial_info, **row}
            temp_lst.append(combined_row)
    
    df = pd.DataFrame(temp_lst)
    return df


def plot_subplot(ax: plt.Axes, df: pd.DataFrame) -> None:
    x = df['distance'].values.reshape(-1, 1)
    y = df['diff'].values
    radar = df['radar position'].astype(str).values.reshape(-1, 1)

    encoder = OneHotEncoder(drop='first')
    radar_encoded = encoder.fit_transform(radar).toarray()

    interaction_terms = x * radar_encoded
    X = np.hstack([x, radar_encoded, interaction_terms])

    model = LinearRegression().fit(X, y)

    categories = encoder.categories_[0][1:]
    full_categories = [encoder.categories_[0][0]] + list(categories)

    colors = plt.cm.tab10.colors

    for i, category in enumerate(full_categories):
        mask = df['radar position'] == category
        x_vals = x[mask].flatten()
        y_vals = y[mask]
        ax.scatter(x_vals, y_vals, label=f'{category}', alpha=0.5, color=colors[i % len(colors)], s=2)

        x_range = np.linspace(x_vals.min(), x_vals.max(), 100).reshape(-1, 1)
        radar_dummy = np.zeros((100, len(categories)))
        if i > 0:
            radar_dummy[:, i - 1] = 1
        interaction = x_range * radar_dummy
        X_plot = np.hstack([x_range, radar_dummy, interaction])
        y_pred = model.predict(X_plot)
        ax.plot(x_range, y_pred, color=colors[i % len(colors)], linewidth=2)

    return


def set_text(ax: plt.Axes, subtitle: str) -> None:
    ax.set_xlabel('Distance (ft)', fontweight='bold', fontsize=10)
    ax.set_ylabel('Difference (Radar - Ground Truth)', fontweight='bold', fontsize=10)
    ax.set_title(subtitle, fontweight='bold', fontsize=14)
    ax.legend()
    return


def plot_all():
    hr_x_manual_df = aggregate_data('Radar Heart Rate', 'Pulse')
    hr_x_polar_df = aggregate_data('Radar Heart Rate', 'Heart')
    br_x_manual_df = aggregate_data('Radar Breath Rate', 'Breath')

    fig, axes = plt.subplots(1, 3, figsize=(18, 7))
    ax1, ax2, ax3 = axes

    plot_subplot(ax1, hr_x_manual_df)
    plot_subplot(ax2, hr_x_polar_df)
    plot_subplot(ax3, br_x_manual_df)

    set_text(ax1, 'Heart Rate: Radar X Manual')
    set_text(ax2, 'Heart Rate: Radar X Polar H10')
    set_text(ax3, 'Breath Rate: Radar X Manual')

    plt.suptitle(
        'Regression: Radar Differences by Distance',
        fontweight = 'bold',
        fontsize=20
    )

    
    plt.show()
    plt.close()

    return


def main():
    plot_all()


if __name__ == "__main__":
    main()
