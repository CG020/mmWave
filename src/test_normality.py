from typing import List
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats
import os
import src.lib.directory as dir
from src.lib.globals import *


def test_normality(data_a: pd.Series, data_b, title) -> bool:
    differences = data_a - data_b
    print(f'{title} has {len(differences)} data points')
    plt.hist(differences, bins=50, density=True, alpha=0.7, color='g')

    xmin, xmax = plt.xlim()
    x = np.linspace(xmin, xmax, 100)

    mu, std = stats.norm.fit(differences)
    plt.plot(x, stats.norm.pdf(x, mu, std), 'k', linewidth=2)

    
    plt.title(f'Distribution of Differences; {title}')
    plt.xlabel('Difference')
    plt.ylabel('Density')
    
    stat, p_value = stats.shapiro(differences)
    print(f"\nShapiro-Wilk Test Statistic: {stat:.4f}, p-value: {p_value:.4e}")

    if p_value > 0.05:
        print("The differences are likely normally distributed (fail to reject null hypothesis).")
    else:
        print("The differences are not normally distributed (reject null hypothesis).")
    plt.show()
    plt.close()
    return


def gather_data(found_files: List[str], data_a_mode: str, data_b_mode: str):
    temp_lst_a = []
    temp_lst_b = []
    for file in found_files:
        df = dir.file_to_df(file)
        temp_lst_a.extend(df[data_a_mode].values)
        temp_lst_b.extend(df[data_b_mode].values)
    
    series_a = pd.Series(temp_lst_a)
    series_b = pd.Series(temp_lst_b)
    return series_a, series_b


def test_singular_dataset():
    test_modality = ('heartrate', 'floor')
    data_modality = ('Radar Heart Rate', 'Pulse')

    found_files = dir.search(*test_modality, directory=PROCESSED_DIR)
    a, b = gather_data(found_files, *data_modality)

    title = f"{test_modality} {data_modality}"
    test_normality(a, b, title)
    return


def test_all_datasets():
    PHYSIO_METRICS = [
        'heartrate',
        'breath'
    ]

    RADAR_POSITION = [
        'floor',
        'tripod'
    ]

    DATA_MODALITY_PAIRS = [
        ('Radar Heart Rate', 'Pulse'),
        ('Radar Heart Rate', 'Heart'),
        ('Radar Breath Rate', 'Breath')
    ]

    # Map each physio metric to the modality pairs relevant to it
    modality_map = {
        'heartrate': [('Radar Heart Rate', 'Pulse'), ('Radar Heart Rate', 'Heart')],
        'breath': [('Radar Breath Rate', 'Breath')]
    }

    for physio_metric in PHYSIO_METRICS:
        for radar_pos in RADAR_POSITION:
            relevant_pairs = modality_map.get(physio_metric, [])
            for data_modality in relevant_pairs:
                test_modality = (physio_metric, radar_pos)
                found_files = dir.search(*test_modality, directory=PROCESSED_DIR)
                a, b = gather_data(found_files, *data_modality)
                title = f"{test_modality} {data_modality}"
                test_normality(a, b, title)




def main():
    test_all_datasets()
    return


if __name__ == "__main__":
    main()
