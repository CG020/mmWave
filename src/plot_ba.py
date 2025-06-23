from typing import List, Tuple
import os
import pandas as pd
import matplotlib.pyplot as plt
from src.lib.globals import *
import src.lib.directory as dir
import scipy.stats as stats
import numpy as np
import src.lib.plot_styles as ps


class Plot_specs:
    DATA_MODE_MAPPINGS = {
        'Radar Heart Rate' : 'Radar',
        'Pulse': 'Manual',
        'Heart' : 'Polar H10',
        'Radar Breath Rate' :'Radar',
        'Breath': 'Manual'
    }
    PHYSIO_MAPPINGS = {
        'heartrate' : 'Heart Rate',
        'breath' : 'Respiratory Rate'
    }
    X_LABEL_MAPPINGS = {
        'heartrate' : 'Heart Rate (BPM)',
        'breath' : "Respiratory Rate (Breaths/Min)"
    }

    def __init__(self, physio: str, data_a_mode: str, data_b_mode: str):
        self._a_mode = data_a_mode
        self._b_mode = data_b_mode

        self._a_str = self.DATA_MODE_MAPPINGS[data_a_mode]
        self._b_str = self.DATA_MODE_MAPPINGS[data_b_mode]
        self._physio_str = self.PHYSIO_MAPPINGS[physio]
        
        self._x_label = self.X_LABEL_MAPPINGS[physio]
        self._y_label = f'{self._a_str} - {self._b_str}'

        self._floor_files = dir.search(physio, 'floor', directory=PROCESSED_DIR)
        self._tripod_files = dir.search(physio, 'tripod', directory=PROCESSED_DIR)

        self._floor_a, self._floor_b = self.gather_files(self._floor_files)
        self._tripod_a, self._tripod_b = self.gather_files(self._tripod_files)
        return
    

    def gather_files(self, found_files: List[str]) -> Tuple[pd.Series, pd.Series]:
        temp_lst_a = []
        temp_lst_b = []
        for file in found_files:
            df = dir.file_to_df(file)
            temp_lst_a.extend(df[self._a_mode].values)
            temp_lst_b.extend(df[self._b_mode].values)
        
        series_a = pd.Series(temp_lst_a)
        series_b = pd.Series(temp_lst_b)
        return series_a, series_b
    

    def plot(self):
        ps.color_style()
        fig, axes = plt.subplots(1, 2, figsize=(10, 5))
        
        self._plot_subplot(axes[0], self._tripod_a, self._tripod_b, 'Tripod')
        axes[0].set_title('Tripod', fontweight='bold', fontsize=14)
        axes[0].set_xlabel(self._x_label, fontweight='bold', fontsize=12)
        axes[0].set_ylabel(self._y_label, fontweight='bold', fontsize=12)

        self._plot_subplot(axes[1], self._floor_a, self._floor_b, 'Floor')
        axes[1].set_title('Floor', fontweight='bold', fontsize=14)
        axes[1].set_xlabel(self._x_label, fontweight='bold', fontsize=12)
        axes[1].set_ylabel(self._y_label, fontweight='bold', fontsize=12)

        def add_letter(ax, letter: str) -> None:
            letter_size = 16
            ax.text(-0.15, 1.1, letter,
                    transform=ax.transAxes, size=letter_size,
                    weight='bold', fontfamily='Arial')
            return


        add_letter(axes[0], 'A')
        add_letter(axes[1], 'B')
        
        # fig.suptitle(f'{self._physio_str}: {self._y_label}'.title(), fontweight='bold', fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        outpath = os.path.join(FIGURE_DIR, f'{self._physio_str}_{self._b_str}.png')
        plt.savefig(outpath, dpi=300)
        plt.show()
        plt.close()
        return



    def _plot_subplot(self, ax: plt.Axes, a: pd.Series, b: pd.Series, title: str):
        differences = a - b
        means = (a + b) / 2
        sorted_differences = np.sort(differences)
        
        lower_percentile_index = int(0.05 * len(sorted_differences))
        upper_percentile_index = int(0.95 * len(sorted_differences))
        
        lower_limit = sorted_differences[lower_percentile_index]
        upper_limit = sorted_differences[upper_percentile_index]

        ax.scatter(means, differences, color='#1d6CAB', alpha=0.14, s=10)
        ax.axhline(y=upper_limit, color='green', linestyle='-', label='95th Percentile')
        ax.axhline(y=lower_limit, color='orange', linestyle='-', label='5th Percentile')

        print(
            f'\nPair: {self._y_label} | Radar Position: {title}\n'
            f'Lower limit: {lower_limit:.2f}'
            f'Upper limit: {upper_limit:.2f}'
        )

        return


def plot_all():
    PHYSIO_METRICS = [
        'heartrate',
        'breath'
    ]

    DATA_MODALITY_PAIRS = [
        ('Radar Heart Rate', 'Pulse'),
        ('Radar Heart Rate', 'Heart'),
        ('Radar Breath Rate', 'Breath')
    ]
 
    radar_x_manual = Plot_specs('heartrate', 'Radar Heart Rate', 'Pulse')
    radar_x_manual.plot()

    radar_x_polar = Plot_specs('heartrate', 'Radar Heart Rate', 'Heart')
    radar_x_polar.plot()

    radar_x_manual_breath = Plot_specs('breath', 'Radar Breath Rate', 'Breath')
    radar_x_manual_breath.plot()
    return


def main():
    plot_all()


if __name__ == "__main__":
    main()
