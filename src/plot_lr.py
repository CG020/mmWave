import pandas as pd
import statsmodels.api as sm
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
import matplotlib as mpl
import src.lib.plot_styles as ps


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

    X = sm.add_constant(x)
    model = sm.OLS(y, X).fit()
    print(model.summary())

    ax.scatter(x, y, alpha=0.5, color='gray', s=2)

    x_range = np.linspace(x.min(), x.max(), 100)
    X_plot = sm.add_constant(x_range.reshape(-1, 1))
    y_pred = model.predict(X_plot)
    ax.plot(x_range, y_pred, color='#29A4E1', linewidth=2)

    slope = model.params[1]
    pval = model.pvalues[1]
    star = '*' if pval < 0.05 else ''
    r_squared = model.rsquared

    ax.text(x_range[-1] - 4, y_pred[-1] + 0.05 * (y.max() - y.min()),
        f'{slope:.2f}{star}, R²={r_squared:.2f}', color='#29A4E1', fontsize=12,
        bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))




def set_text(ax: plt.Axes, subtitle: str, sample_size: str) -> None:
    tick_label_dict = {
        'fontsize': 10,
        'fontweight': 'bold',
    }

    ax.text(0.85, 0.9, f'n={sample_size}',
                transform=ax.transAxes, size=12, color='grey',
                weight='bold', fontfamily='Arial')

    ax.set_xlabel('Distance (ft)', fontweight='bold', fontsize=14)
    ax.set_ylabel('Diff (Radar - Ground Truth)', fontweight='bold', fontsize=14)
    ax.set_title(subtitle, fontweight='bold', fontsize=14)
    return


def plot_all():
    ps.color_style()

    hr_x_manual_df = aggregate_data('Radar Heart Rate', 'Pulse')
    hr_x_polar_df = aggregate_data('Radar Heart Rate', 'Heart')
    br_x_manual_df = aggregate_data('Radar Breath Rate', 'Breath')

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    ax1, ax2, ax3 = axes

    plot_subplot(ax1, hr_x_manual_df)
    plot_subplot(ax2, hr_x_polar_df)
    plot_subplot(ax3, br_x_manual_df)

    set_text(ax1, 'Heart Rate: Radar x Manual', len(hr_x_manual_df['diff']))
    set_text(ax2, 'Heart Rate: Radar x Polar H10', len(hr_x_polar_df['diff']))
    set_text(ax3, 'Respiratory Rate: Radar x Manual', len(br_x_manual_df['diff']))

    # plt.suptitle(
    #     'Difference in Radar Measurements Against Distance',
    #     fontweight = 'bold',
    #     fontsize=20
    # )

    outpath = os.path.join(FIGURE_DIR, 'linear_regression_all.png')
    plt.savefig(outpath, dpi=300)
    plt.show()
    plt.close()

    return


def main():
    plot_all()


if __name__ == "__main__":
    main()
