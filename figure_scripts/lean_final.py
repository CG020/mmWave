import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score
from icecream import ic

def process_csv_files_in_directory(root_folder, subfolder):
    visualizer_data_folder = os.path.join(root_folder, 'visualizer_data', subfolder)
    
    print(f"Checking folder: {visualizer_data_folder}")
    if not os.path.exists(visualizer_data_folder):
        print(f"Folder '{visualizer_data_folder}' does not exist.")
        return None, None

    all_parts_combined = []
    vitals_file_path = None

    for file in os.listdir(visualizer_data_folder):
        file_path = os.path.join(visualizer_data_folder, file)
        print(f"Found file: {file}")
        if file.endswith('vitals.csv'):
            vitals_file_path = file_path
            print(f"Vitals file found: {file}")
        elif file.endswith('.csv') and 'part' in file:
            all_parts_combined.append(pd.read_csv(file_path))
            print(f"Part file found: {file}")

    if vitals_file_path is None:
        print("No vitals file found!")
    if not all_parts_combined:
        print("No part files found!")

    return vitals_file_path, pd.concat(all_parts_combined, ignore_index=True) if all_parts_combined else None

def vitals_time_to_seconds(time_str):
    if pd.isna(time_str):
        return np.nan
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

def process_csv_file(vitals_file_path, parts_combined, subfolder, overall_results):
    if vitals_file_path is None or parts_combined is None:
        print(f"Required CSV files not found for {subfolder}.")
        return

    if "chair" not in subfolder.lower():
        print(f"Skipping {subfolder} as it doesn't contain 'chair'.")
        return

    print(f"Processing {subfolder}")
    vitals = pd.read_csv(vitals_file_path)

    vitals_data = vitals.copy()
    
    vitals_data['Start Seconds'] = vitals_data['Start'].apply(vitals_time_to_seconds).astype(float)
    vitals_data['End Seconds'] = vitals_data['End'].apply(vitals_time_to_seconds).astype(float)
    parts_combined['Seconds'] = parts_combined['Timestamp'].apply(radar_time_to_seconds)

    parts_combined['Leaning Angle'] = pd.to_numeric(parts_combined['Leaning Angle'], errors='coerce')

    def find_radar_lean_in_range(start_time, end_time):
        relevant_rows = parts_combined[(parts_combined['Seconds'] >= start_time) & (parts_combined['Seconds'] <= end_time)]
        if not relevant_rows.empty:
            return relevant_rows['Leaning Angle'].mean()
        else:
            return np.nan

    vitals_data['Radar Lean Angle'] = vitals_data.apply(lambda row: find_radar_lean_in_range(row['Start Seconds'], row['End Seconds']), axis=1)

    def determine_color(row):
        if row['Radar Lean Angle'] > 5 and row['lean_direction'] == 'left':
            return 'green'
        elif row['Radar Lean Angle'] < -5 and row['lean_direction'] == 'right':
            return 'green'
        elif abs(row['Radar Lean Angle']) <= 5 and row['lean_direction'] == 'upright':
            return 'green'
        else:
            return 'red'

    vitals_data['Color'] = vitals_data.apply(determine_color, axis=1)

    overall_results.append(vitals_data)

    plt.figure(figsize=(12, 6))
    
    plt.scatter(vitals_data['Marker'], vitals_data['Radar Lean Angle'], color=vitals_data['Color'], label='Radar Lean Angle')
    plt.plot(vitals_data['Marker'], vitals_data['Radar Lean Angle'], color='blue', alpha=0.5)

    # Apply bold font and increase font size
    plt.xlabel('Distance (Marker)', fontsize=14, fontweight='bold')
    plt.ylabel('Lean Angle (Degrees)', fontsize=14, fontweight='bold')
    plt.title('Radar Lean Angle', fontsize=16, fontweight='bold')
    
    # Customize xticks and yticks
    plt.xticks(vitals_data['Marker'].unique(), fontsize=12, fontweight='bold')
    plt.yticks(fontsize=12, fontweight='bold')

    plt.legend()
    plt.grid(True)

    y_min = vitals_data['Radar Lean Angle'].min()
    y_max = vitals_data['Radar Lean Angle'].max()
    y_range = y_max - y_min
    y_bottom = y_min - y_range * 0.1
    y_top = y_max + y_range * 0.1
    plt.ylim(y_bottom, y_top)

    tick_interval = max(10, int(y_range / 10))
    y_ticks = np.arange(int(y_bottom), int(y_top) + 1, tick_interval)
    plt.yticks(y_ticks)

    plt.axhline(y=0, color='red', linestyle='--', label='Upright')

    plt.tight_layout()
    output_file_name = f"figures/lean/{subfolder}_radar_lean_angle.png"
    os.makedirs(os.path.dirname(output_file_name), exist_ok=True)
    plt.savefig(output_file_name, bbox_inches='tight')
    plt.close()


def process_all_groups(root_folder):
    visualizer_data_folder = os.path.join(root_folder, 'visualizer_data')
    
    print(f"Processing groups in: {root_folder}")
    print(f"Visualizer data folder: {visualizer_data_folder}")
    
    if not os.path.exists(visualizer_data_folder):
        print(f"Folder '{visualizer_data_folder}' does not exist.")
        return

    overall_results = []

    for subfolder in os.listdir(visualizer_data_folder):
        subfolder_path = os.path.join(visualizer_data_folder, subfolder)
        if os.path.isdir(subfolder_path):
            if "chair" in subfolder.lower():
                vitals_file_path, parts_combined = process_csv_files_in_directory(root_folder, subfolder)
                process_csv_file(vitals_file_path, parts_combined, subfolder, overall_results)
            else:
                print(f"Skipping {subfolder} as it doesn't contain 'chair'.")

    all_data = pd.concat(overall_results, ignore_index=True)

    all_data['Detected Category'] = all_data['Radar Lean Angle'].apply(
        lambda x: 'left' if x < -5 else 'right'
        )
    all_data['Expected Category'] = all_data['lean_direction'].replace({'left': 'right', 'right': 'left'})

    cm = confusion_matrix(all_data['Expected Category'], all_data['Detected Category'], labels=['left', 'right'])

    accuracy = accuracy_score(all_data['Expected Category'], all_data['Detected Category'])
    precision = precision_score(all_data['Expected Category'], all_data['Detected Category'], average='weighted')
    recall = recall_score(all_data['Expected Category'], all_data['Detected Category'], average='weighted')
    f1 = f1_score(all_data['Expected Category'], all_data['Detected Category'], average='weighted')

    print(f"\nOverall Accuracy: {accuracy:.2f}")
    print(f"Overall Precision: {precision:.2f}")
    print(f"Overall Recall: {recall:.2f}")
    print(f"Overall F1 Score: {f1:.2f}")

    plt.figure(figsize=(8, 6))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    
    plt.title('Lean Angle Matrix', weight='bold', fontsize=16)
    plt.colorbar()
    tick_marks = np.arange(len(['left', 'right']))
    
    plt.xticks(tick_marks, ['left', 'right'], fontsize=12, fontweight='bold')
    plt.yticks(tick_marks, ['left', 'right'], fontsize=12, fontweight='bold')

    fmt = 'd'
    thresh = cm.max() / 2.
    for i, j in np.ndindex(cm.shape):
        plt.text(j, i, format(cm[i, j], fmt),
                 ha="center", va="center",
                 color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    
    # Apply bold font to labels
    plt.ylabel('True Category', weight='bold', fontsize=14)
    plt.xlabel('Detected Category', weight='bold', fontsize=14)

    output_file_name = "figures/lean/overall_lean_matrix.png"
    plt.savefig(output_file_name, bbox_inches='tight')
    plt.close()


if __name__ == "__main__":
    root_folder = '.'
    process_all_groups(root_folder)
