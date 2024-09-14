import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from icecream import ic

def process_csv_files_in_directory(root_folder, subfolder):
    visualizer_data_folder = os.path.join(root_folder, 'visualizer_data', subfolder)
    
    if not os.path.exists(visualizer_data_folder):
        print(f"Folder '{visualizer_data_folder}' does not exist.")
        return None, None

    all_parts_combined = []
    vitals_file_path = None

    for file in os.listdir(visualizer_data_folder):
        file_path = os.path.join(visualizer_data_folder, file)
        # print(f"Found file: {file}")
        if file.endswith('vitals.csv'):
            vitals_file_path = file_path
            # print(f"Vitals file found: {file}")
        elif file.endswith('.csv') and 'part' in file:
            all_parts_combined.append(pd.read_csv(file_path))
            # print(f"Part file found: {file}")

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
    else:
        raise ValueError(f"Unexpected time format in vitals: {time_str}")

def radar_time_to_seconds(time_str):
    return float(time_str) 

def process_csv_file(vitals_file_path, parts_combined, subfolder):
    if vitals_file_path is None or parts_combined is None:
        print(f"Required CSV files not found for {subfolder}.")
        return

    print(f"Processing {subfolder}")
    vitals = pd.read_csv(vitals_file_path)


    breath_data = vitals.copy()
    
    breath_data['Seconds'] = breath_data['Time for Breath'].apply(vitals_time_to_seconds).astype(float)
    parts_combined['Seconds'] = parts_combined['Timestamp'].apply(radar_time_to_seconds)

    parts_combined['Breath Rate'] = pd.to_numeric(parts_combined['Breath Rate'], errors='coerce')

    def find_closest_radar_breath(target_time):
        closest_rows = parts_combined[parts_combined['Breath Rate'].notna()].iloc[
            (parts_combined[parts_combined['Breath Rate'].notna()]['Seconds'] - target_time).abs().argsort()[:1]
        ]
        return closest_rows['Breath Rate'].values[0] if not closest_rows.empty else np.nan

    breath_data['Radar Breath Rate'] = breath_data['Seconds'].apply(find_closest_radar_breath)

    plt.figure(figsize=(12, 6))
    plt.plot(breath_data['Marker'], breath_data['Breath'], 'o-', label='Manually Measured Breath Rate', color='blue')
    plt.plot(breath_data['Marker'], breath_data['Radar Breath Rate'], 'o-', label='Radar Breath Rate', color='red')

    plt.xlabel('Distance (Feet)')
    plt.ylabel('Breath Rate (BPM)')
    plt.title(f'Manually Measured Breath Rate vs MMWave Radar Breath Rate - {subfolder}')
    plt.legend()
    plt.grid(True)

    plt.xticks(breath_data['Marker'].unique()[::2])

    y_min = 0
    y_max = 80
    plt.ylim(y_min, y_max)

    tick_interval = 5
    y_ticks = np.arange(y_min, y_max + 1, tick_interval)
    plt.yticks(y_ticks)

    plt.tight_layout()
    output_file_name = f"figures/breath/{subfolder}_breath_comparison.png"
    os.makedirs(os.path.dirname(output_file_name), exist_ok=True)
    plt.savefig(output_file_name)
    plt.close()

    print(f"\nResults for {subfolder}:")
    print("Manually Measured Breath Rate Range:", 
          breath_data['Breath'].min(), "-", breath_data['Breath'].max())
    print("Radar Measured Breath Rate Range:", 
          breath_data['Radar Breath Rate'].min(), "-", breath_data['Radar Breath Rate'].max())

    avg_manual = breath_data['Breath'].mean()
    avg_radar = breath_data['Radar Breath Rate'].mean()
    print(f"\nAverage Manually Measured Breath Rate: {avg_manual:.2f} BPM")
    print(f"Average Radar Measured Breath Rate: {avg_radar:.2f} BPM")

    correlation = breath_data['Breath'].corr(breath_data['Radar Breath Rate'])
    print(f"\nCorrelation between Manual and Radar Breath Rate: {correlation:.2f}")

    results = {
        'Subfolder': subfolder,
        'Manual_Breath_Min': breath_data['Breath'].min(),
        'Manual_Breath_Max': breath_data['Breath'].max(),
        'Radar_Breath_Min': breath_data['Radar Breath Rate'].min(),
        'Radar_Breath_Max': breath_data['Radar Breath Rate'].max(),
        'Avg_Manual_Breath': breath_data['Breath'].mean(),
        'Avg_Radar_Breath': breath_data['Radar Breath Rate'].mean(),
        'Correlation': breath_data['Breath'].corr(breath_data['Radar Breath Rate'])
    }

    return results

def process_all_groups(root_folder):
    visualizer_data_folder = os.path.join(root_folder, 'visualizer_data')

    if not os.path.exists(visualizer_data_folder):
        print(f"Folder '{visualizer_data_folder}' does not exist.")
        return

    all_results = []
    
    print(f"Processing groups in: {root_folder}")
    print(f"Visualizer data folder: {visualizer_data_folder}")
    
    if not os.path.exists(visualizer_data_folder):
        print(f"Folder '{visualizer_data_folder}' does not exist.")
        return

    for subfolder in os.listdir(visualizer_data_folder):
        subfolder_path = os.path.join(visualizer_data_folder, subfolder)
        if os.path.isdir(subfolder_path):
            vitals_file_path, parts_combined = process_csv_files_in_directory(root_folder, subfolder)
            results = process_csv_file(vitals_file_path, parts_combined, subfolder)
            if results:
                all_results.append(results)
    
    results_df = pd.DataFrame(all_results)

    output_csv = 'visualizer_data/aggregates/breath_results.csv'
    results_df.to_csv(output_csv, index=False)
    print(f"Results saved to {output_csv}")

if __name__ == "__main__":
    root_folder = '.'
    process_all_groups(root_folder)