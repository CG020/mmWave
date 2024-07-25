import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

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

    return vitals_file_path, pd.concat(all_parts_combined, ignore_index=True) if all_parts_combined else None

def process_csv_file(vitals_file_path, parts_combined, subfolder):
    if vitals_file_path is None or parts_combined is None:
        print("Required CSV files not found.")
        return

    vitals = pd.read_csv(vitals_file_path)

    metrics = {
        'pulse': 'Heart Rate',
        'breath': 'Breath Rate'
    }
    
    for metric_type, radar_metric in metrics.items():
        metric_data = vitals[vitals['Type'] == metric_type].copy()
        if metric_data.empty:
            print(f"No data for {metric_type} in {vitals_file_path}")
            continue

        metric_data['Time_Diff'] = metric_data['Timestamp'].diff()
        metric_data['Physical_Rate'] = 60 / metric_data['Time_Diff']

        def find_closest_value(timestamp):
            idx = (parts_combined['Timestamp'] - timestamp).abs().idxmin()
            return parts_combined.loc[idx, radar_metric] if radar_metric in parts_combined.columns else np.nan

        metric_data['Measured_Rate'] = metric_data['Timestamp'].apply(find_closest_value)
        metric_data = metric_data.replace([np.inf, -np.inf], np.nan).dropna(subset=['Physical_Rate', 'Measured_Rate'])

        metric_data['Physical_Rate'] = pd.to_numeric(metric_data['Physical_Rate'], errors='coerce')
        metric_data['Measured_Rate'] = pd.to_numeric(metric_data['Measured_Rate'], errors='coerce')
        metric_data = metric_data.dropna(subset=['Physical_Rate', 'Measured_Rate'])

        if metric_data.empty:
            print(f"No aligned data for {metric_type} in {vitals_file_path}")
            continue

        plt.figure(figsize=(14, 7))
        plt.scatter(metric_data['Mark'], metric_data['Physical_Rate'], 
                    label=f'Taken {metric_type.capitalize()} Rate', marker='o', color='blue', alpha=0.6)
        plt.scatter(metric_data['Mark'], metric_data['Measured_Rate'], 
                    label=f'Radar {metric_type.capitalize()} Rate', marker='o', color='red', alpha=0.6)

        plt.xlabel('Distance (Markers)')
        plt.ylabel(f'{metric_type.capitalize()} Rate')
        plt.title(f'Taken {metric_type.capitalize()} Rate vs MMWave Radar {metric_type.capitalize()} Rate')
        plt.legend()
        plt.grid(True)
        plt.minorticks_on()

        y_min = max(0, min(metric_data['Physical_Rate'].min(), metric_data['Measured_Rate'].min()) - 10)
        y_max = min(150, max(metric_data['Physical_Rate'].max(), metric_data['Measured_Rate'].max()) + 10)
        plt.ylim(y_min, y_max)

        plt.xticks(rotation=45)
        plt.tight_layout()

        output_file_name = f"{subfolder}_{metric_type}_comparison.png"
        plt.savefig(output_file_name)

        print(f"\n{metric_type.capitalize()} Rate Range:", 
              metric_data['Physical_Rate'].min(), "-", metric_data['Physical_Rate'].max())
        print(f"Measured {metric_type.capitalize()} Rate Range:", 
              metric_data['Measured_Rate'].min(), "-", metric_data['Measured_Rate'].max())
        print("\nFirst few rows of aligned data:")
        print(metric_data[['Mark', 'Physical_Rate', 'Measured_Rate']].head())

        print("\nUnique timestamps in metric_data:", metric_data['Timestamp'].nunique())
        print("Total rows in metric_data:", len(metric_data))
        print("\nUnique timestamps in parts_combined:", parts_combined['Timestamp'].nunique())
        print("Total rows in parts_combined:", len(parts_combined))

if __name__ == "__main__":
    root_folder = '.'
    visualizer_data_folder = os.path.join(root_folder, 'visualizer_data')

    if not os.path.exists(visualizer_data_folder):
        print(f"Folder '{visualizer_data_folder}' does not exist.")
        exit()

    subfolders = [subfolder for subfolder in os.listdir(visualizer_data_folder) if os.path.isdir(os.path.join(visualizer_data_folder, subfolder))]

    for current in subfolders:
        vitals_file_path, parts_combined = process_csv_files_in_directory(root_folder, current)
        process_csv_file(vitals_file_path, parts_combined, current)
