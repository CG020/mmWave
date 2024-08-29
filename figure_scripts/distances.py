import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

subject_mapping = {
    'AARON': 'Subject 1',
    'LINDA': 'Subject 2',
    'JESUS': 'Subject 3',
    'CANDICE': 'Subject 4',
    'MIKHAIL': 'Subject 5',
    'NATALIE': 'Subject 6'
}

def apply_subject_mapping(df):
    def map_subject(subfolder):
        parts = subfolder.split('_')
        subject_name = parts[1]
        return subject_mapping.get(subject_name, subject_name)
    
    df['Subject'] = df['Subfolder'].apply(map_subject)
    return df

def sort_by_subject(df):
    def extract_subject_number(subject):
        return int(subject.split(' ')[-1])
    
    df['Subject_Number'] = df['Subject'].apply(extract_subject_number)
    df = df.sort_values('Subject_Number').drop(columns='Subject_Number')
    return df

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
    elif len(parts) == 1:
        return int(parts[0])
    else:
        raise ValueError(f"Unexpected time format: {time_str}")

def radar_time_to_seconds(time_str):
    return float(time_str)

def process_csv_file(vitals_file_path, parts_combined, subfolder):
    if vitals_file_path is None or parts_combined is None:
        print(f"Required CSV files not found for {subfolder}.")
        return

    vitals = pd.read_csv(vitals_file_path)
    vitals_data = vitals.copy()
    
    vitals_data['Seconds'] = vitals_data['Time for Pulse'].apply(vitals_time_to_seconds).astype(float)
    parts_combined['Seconds'] = parts_combined['Timestamp'].apply(radar_time_to_seconds)

    parts_combined['Heart Rate'] = pd.to_numeric(parts_combined['Heart Rate'], errors='coerce')
    parts_combined['Breath Rate'] = pd.to_numeric(parts_combined['Breath Rate'], errors='coerce')

    def find_closest_radar_measurement(target_time, metric):
        closest_rows = parts_combined[parts_combined[metric].notna()].iloc[
            (parts_combined[parts_combined[metric].notna()]['Seconds'] - target_time).abs().argsort()[:1]
        ]
        return closest_rows[metric].values[0] if not closest_rows.empty else np.nan

    vitals_data['Radar Heart Rate'] = vitals_data['Seconds'].apply(lambda x: find_closest_radar_measurement(x, 'Heart Rate'))
    vitals_data['Radar Breath Rate'] = vitals_data['Seconds'].apply(lambda x: find_closest_radar_measurement(x, 'Breath Rate'))

    vitals_data['Distance'] = vitals_data['Marker']

    avg_results = vitals_data.groupby('Distance').agg({
        'Pulse': 'mean',
        'Radar Heart Rate': 'mean',
        'Heart': 'mean',
        'Breath': 'mean',
        'Radar Breath Rate': 'mean'
    }).reset_index()

    avg_results['Subfolder'] = subfolder

    return avg_results

def process_all_groups(root_folder):
    visualizer_data_folder = os.path.join(root_folder, 'visualizer_data')
    
    if not os.path.exists(visualizer_data_folder):
        print(f"Folder '{visualizer_data_folder}' does not exist.")
        return

    all_results = []

    for subfolder in os.listdir(visualizer_data_folder):
        subfolder_path = os.path.join(visualizer_data_folder, subfolder)
        if os.path.isdir(subfolder_path):
            vitals_file_path, parts_combined = process_csv_files_in_directory(root_folder, subfolder)
            results = process_csv_file(vitals_file_path, parts_combined, subfolder)
            if results is not None:
                all_results.append(results)

    combined_results = pd.concat(all_results, ignore_index=True)

    output_csv = 'visualizer_data/aggregates/pulse_breath_averages_by_distance.csv'
    combined_results.to_csv(output_csv, index=False)
    print(f"Results saved to {output_csv}")

    return combined_results

def create_marker_bar_charts(combined_results, experiment_type, metric, radar_metric):
    combined_results = apply_subject_mapping(combined_results)
    combined_results = sort_by_subject(combined_results)

    for marker in combined_results['Distance'].unique():
        marker_data = combined_results[(combined_results['Distance'] == marker) & 
                                       (combined_results['Subfolder'].str.contains(experiment_type))]
        
        plt.figure(figsize=(12, 6))
        bar_width = 0.25
        subjects = marker_data['Subject']
        index = np.arange(len(subjects))
        
        plt.bar(index, marker_data[metric], bar_width, label=f'Manual {metric}')
        plt.bar(index + bar_width, marker_data[radar_metric], bar_width, label=f'Radar {metric}')
        
        plt.xlabel('Subject')
        plt.ylabel(f'Average {metric} Rate (BPM)')
        plt.title(f'Average {metric} Rate at {marker} Feet - {experiment_type.capitalize()}')
        
        subject_labels = marker_data.apply(lambda row: f"{row['Subject']}_{row['Subfolder'].split('_')[-1]}", axis=1)
        plt.xticks(index + bar_width, subject_labels, rotation=45, ha='right')
        
        plt.legend()
        plt.tight_layout()

        output_file_name = f'figures/markers/{experiment_type}_{marker}_feet_{metric.lower()}_rate_comparison.png'
        os.makedirs(os.path.dirname(output_file_name), exist_ok=True)
        plt.savefig(output_file_name)
        plt.close()

def create_combined_marker_averages_chart(combined_results, experiment_type, metric, radar_metric):
    combined_results = apply_subject_mapping(combined_results)
    combined_results = sort_by_subject(combined_results)

    markers_of_interest = ['Marker 1', 'Marker 5', 'Marker 10', 'Marker 15']
    
    filtered_df = combined_results[combined_results['Distance'].isin(markers_of_interest) & 
                                   combined_results['Subfolder'].str.contains(experiment_type)]
    
    averages = filtered_df.groupby('Distance').agg({
        metric: 'mean',
        radar_metric: 'mean'
    }).reset_index()

    plt.figure(figsize=(12, 6))
    bar_width = 0.2
    index = np.arange(len(averages))
    
    plt.bar(index, averages[metric], bar_width, label=f'Manual {metric}')
    plt.bar(index + bar_width, averages[radar_metric], bar_width, label=f'Radar {metric}')
    
    plt.xlabel('Distance (Feet)')
    plt.ylabel(f'Average {metric} Rate (BPM)')
    plt.title(f'Average {metric} Rate Across Markers - {experiment_type.capitalize()}')
    
    plt.xticks(index + bar_width, averages['Distance'], rotation=45, ha='right')
    
    plt.legend()
    plt.tight_layout()

    output_file_name = f'figures/markers/{experiment_type}_combined_marker_averages_{metric.lower()}.png'
    os.makedirs(os.path.dirname(output_file_name), exist_ok=True)
    plt.savefig(output_file_name)
    plt.close()

if __name__ == "__main__":
    root_folder = '.'
    combined_results = process_all_groups(root_folder)
    if combined_results is not None:
        create_marker_bar_charts(combined_results, 'floor', 'Pulse', 'Radar Heart Rate')
        create_marker_bar_charts(combined_results, 'tripod', 'Pulse', 'Radar Heart Rate')
        create_combined_marker_averages_chart(combined_results, 'floor', 'Pulse', 'Radar Heart Rate')
        create_combined_marker_averages_chart(combined_results, 'tripod', 'Pulse', 'Radar Heart Rate')
        
        create_marker_bar_charts(combined_results, 'floor', 'Breath', 'Radar Breath Rate')
        create_marker_bar_charts(combined_results, 'tripod', 'Breath', 'Radar Breath Rate')
        create_combined_marker_averages_chart(combined_results, 'floor', 'Breath', 'Radar Breath Rate')
        create_combined_marker_averages_chart(combined_results, 'tripod', 'Breath', 'Radar Breath Rate')

