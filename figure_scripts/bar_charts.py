import os
import pandas as pd
import matplotlib.pyplot as plt

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
        try:
            return int(subject.split(' ')[1])
        except (IndexError, ValueError):
            return 9999

    df['Subject Number'] = df['Subject'].apply(extract_subject_number)
    df = df.sort_values('Subject Number').drop(columns='Subject Number')
    return df

def create_grouped_bar_charts(df, output_prefix, experiment_type):
    df = apply_subject_mapping(df.copy())
    df = sort_by_subject(df)
    filtered_df = df[df['Subfolder'].str.contains(experiment_type)]

    chair_df = filtered_df[filtered_df['Subfolder'].str.contains('chair')]
    stand_df = filtered_df[filtered_df['Subfolder'].str.contains('stand')]

    metrics = [col for col in df.columns if col not in ['Subfolder', 'Subject']]

    for metric in metrics:
        plt.figure(figsize=(12, 6))
        
        bar_width = 0.35
        index = range(len(chair_df))
        
        plt.bar(index, chair_df[metric], bar_width, label='Chair')
        plt.bar([i + bar_width for i in index], stand_df[metric], bar_width, label='Stand')
        
        plt.title(f'{metric} - {experiment_type.capitalize()}', weight='bold', fontsize=14)
        plt.xlabel('Subject', weight='bold', fontsize=12)
        plt.ylabel(metric, weight='bold', fontsize=12)
        
        subject_labels = chair_df.apply(lambda row: f"{row['Subject']}_chair", axis=1)
        plt.xticks([i + bar_width/2 for i in index], subject_labels, rotation=45, ha='right', fontsize=11, weight='bold')
        plt.yticks(fontsize=11, weight='bold')
        
        ax = plt.gca()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        plt.legend()
        plt.tight_layout()
        
        plt.savefig(f'figures/bar_charts/{output_prefix}_{metric.lower().replace(" ", "_")}_{experiment_type}.png')
        plt.close()

def create_manual_radar_polar_barcharts(df, output_prefix, experiment_type):
    df = apply_subject_mapping(df.copy())
    df = sort_by_subject(df)
    filtered_df = df[df['Subfolder'].str.contains(experiment_type)]
    
    avg_columns = [col for col in df.columns if 'Avg_' in col]
    
    plt.figure(figsize=(12, 6))
    
    bar_width = 0.25
    index = range(len(filtered_df))
    
    for i, col in enumerate(avg_columns):
        plt.bar([j + i * bar_width for j in index], filtered_df[col], bar_width, label=col)
    
    plt.title(f'Manual, Radar, and Polar Avg Values - {experiment_type.capitalize()}', weight='bold', fontsize=14)
    plt.xlabel('Subject', weight='bold', fontsize=12)
    plt.ylabel('Avg Values', weight='bold', fontsize=12)
    
    subject_labels = filtered_df.apply(lambda row: f"{row['Subject']}_{row['Subfolder'].split('_')[-1]}", axis=1)
    plt.xticks([j + bar_width for j in index], subject_labels, rotation=45, ha='right', fontsize=11, weight='bold')
    plt.yticks(fontsize=11, weight='bold')
    
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.legend()
    plt.tight_layout()
    
    plt.savefig(f'figures/bar_charts/{output_prefix}_manual_radar_polar_{experiment_type}.png')
    plt.close()

def create_correlation_comparison(df, experiment_type):
    df = apply_subject_mapping(df.copy())
    df = sort_by_subject(df)
    filtered_df = df[df['Subfolder'].str.contains(experiment_type)]
    correlation_columns = [
        'Correlation_Manual_Radar',
        'Correlation_Manual_Polar',
        'Correlation_Radar_Polar'
    ]
    
    plt.figure(figsize=(14, 8))
    bar_width = 0.25
    index = range(len(filtered_df))

    for i, col in enumerate(correlation_columns):
        plt.bar([j + i * bar_width for j in index], filtered_df[col], bar_width, label=col)

    plt.title(f'Correlation Heart Rate - {experiment_type.capitalize()}', weight='bold', fontsize=16)
    plt.xlabel('Subject', weight='bold', fontsize=14)
    plt.ylabel('Correlation', weight='bold', fontsize=14)
    
    subject_labels = filtered_df.apply(lambda row: f"{row['Subject']}_{row['Subfolder'].split('_')[-1]}", axis=1)
    plt.xticks([j + bar_width for j in index], subject_labels, rotation=45, ha='right', fontsize=11, weight='bold')
    plt.yticks(fontsize=11, weight='bold')
    
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.legend()
    plt.tight_layout()

    plt.savefig(f'figures/correlation_comparison_{experiment_type}.png')
    plt.close()

def create_breath_rate_correlation_comparison(df, experiment_type):
    df = apply_subject_mapping(df.copy())
    df = sort_by_subject(df)
    filtered_df = df[df['Subfolder'].str.contains(experiment_type)]
    
    plt.figure(figsize=(14, 8))
    bar_width = 0.50
    index = range(len(filtered_df))

    plt.bar([i for i in index], filtered_df['Correlation'], bar_width, label='Correlation_Manual_Radar')

    plt.title(f'Breath Rate Correlation - {experiment_type.capitalize()}', weight='bold', fontsize=16)
    plt.xlabel('Subject', weight='bold', fontsize=14)
    plt.ylabel('Correlation', weight='bold', fontsize=14)
    
    subject_labels = filtered_df.apply(lambda row: f"{row['Subject']}_{row['Subfolder'].split('_')[-1]}", axis=1)
    plt.xticks([i for i in index], subject_labels, rotation=45, ha='right', fontsize=11, weight='bold')
    plt.yticks(fontsize=11, weight='bold')
    
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.legend()
    plt.tight_layout()

    plt.savefig(f'figures/breath_rate_correlation_{experiment_type}.png')
    plt.close()

def calculate_averages(df):
    numeric_df = df.drop(columns=['Subfolder'])
    
    total_averages = numeric_df.mean()
    
    combined_averages = {
        'Manual_Avg': numeric_df[[col for col in numeric_df.columns if 'Manual' in col]].mean().mean(),
        'Radar_Avg': numeric_df[[col for col in numeric_df.columns if 'Radar' in col]].mean().mean(),
        'Polar_Avg': numeric_df[[col for col in numeric_df.columns if 'Polar' in col]].mean().mean()
    }
    
    return total_averages, combined_averages

def display_correlation_averages(df):
    df = apply_subject_mapping(df.copy())
    df = sort_by_subject(df)
    floor_df = df[df['Subfolder'].str.contains('floor')]
    tripod_df = df[df['Subfolder'].str.contains('tripod')]
    
    floor_avg_correlation = floor_df['Correlation'].mean()
    tripod_avg_correlation = tripod_df['Correlation'].mean()
    
    print(f"Average Breath Rate Correlation for Floor Experiments: {floor_avg_correlation:.4f}")
    print(f"Average Breath Rate Correlation for Tripod Experiments: {tripod_avg_correlation:.4f}")

def display_pulse_correlation_averages(df):
    df = apply_subject_mapping(df.copy())
    df = sort_by_subject(df)
    floor_df = df[df['Subfolder'].str.contains('floor')]
    tripod_df = df[df['Subfolder'].str.contains('tripod')]
    
    floor_avg_corr_manual_radar = floor_df['Correlation_Manual_Radar'].mean()
    floor_avg_corr_manual_polar = floor_df['Correlation_Manual_Polar'].mean()
    floor_avg_corr_radar_polar = floor_df['Correlation_Radar_Polar'].mean()

    tripod_avg_corr_manual_radar = tripod_df['Correlation_Manual_Radar'].mean()
    tripod_avg_corr_manual_polar = tripod_df['Correlation_Manual_Polar'].mean()
    tripod_avg_corr_radar_polar = tripod_df['Correlation_Radar_Polar'].mean()

    print(f"Average Pulse Rate Correlations for Floor Experiments:")
    print(f"  Manual vs Radar: {floor_avg_corr_manual_radar:.4f}")
    print(f"  Manual vs Polar: {floor_avg_corr_manual_polar:.4f}")
    print(f"  Radar vs Polar: {floor_avg_corr_radar_polar:.4f}")

    print(f"\nAverage Pulse Rate Correlations for Tripod Experiments:")
    print(f"  Manual vs Radar: {tripod_avg_corr_manual_radar:.4f}")
    print(f"  Manual vs Polar: {tripod_avg_corr_manual_polar:.4f}")
    print(f"  Radar vs Polar: {tripod_avg_corr_radar_polar:.4f}")

output_dir = 'figures/bar_charts/'
os.makedirs(output_dir, exist_ok=True)

breath_df = pd.read_csv('visualizer_data/aggregates/breath_results.csv')
pulse_df = pd.read_csv('visualizer_data/aggregates/pulse_results.csv')

create_grouped_bar_charts(breath_df, 'breath', 'floor')
create_grouped_bar_charts(breath_df, 'breath', 'tripod')
create_grouped_bar_charts(pulse_df, 'pulse', 'floor')
create_grouped_bar_charts(pulse_df, 'pulse', 'tripod')

create_manual_radar_polar_barcharts(breath_df, 'breath', 'floor')
create_manual_radar_polar_barcharts(breath_df, 'breath', 'tripod')
create_manual_radar_polar_barcharts(pulse_df, 'pulse', 'floor')
create_manual_radar_polar_barcharts(pulse_df, 'pulse', 'tripod')

breath_total_averages, breath_combined_averages = calculate_averages(breath_df)
pulse_total_averages, pulse_combined_averages = calculate_averages(pulse_df)

print("Total Averages for Breath Data:")
print(breath_total_averages)

print("\nCombined Averages for Breath Data:")
print(breath_combined_averages)

print("\nTotal Averages for Pulse Data:")
print(pulse_total_averages)

print("\nCombined Averages for Pulse Data:")
print(pulse_combined_averages)

create_correlation_comparison(pulse_df, 'floor')
create_correlation_comparison(pulse_df, 'tripod')

create_breath_rate_correlation_comparison(breath_df, 'floor')
create_breath_rate_correlation_comparison(breath_df, 'tripod')

display_correlation_averages(breath_df)
display_pulse_correlation_averages(pulse_df)

