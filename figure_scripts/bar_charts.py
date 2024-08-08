import pandas as pd
import matplotlib.pyplot as plt

def create_bar_charts(csv_file, output_prefix):
    df = pd.read_csv(csv_file)
    
    metrics = [col for col in df.columns if col != 'Subfolder']
    
    for metric in metrics:
        plt.figure(figsize=(12, 6))
        plt.bar(df['Subfolder'], df[metric])
        plt.title(f'{metric} by Subfolder')
        plt.xlabel('Subfolder')
        plt.ylabel(metric)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'figures/bar_charts/{output_prefix}_{metric.lower().replace(" ", "_")}.png')
        plt.close()

create_bar_charts('visualizer_data/aggregates/breath_results.csv', 'breath')

create_bar_charts('visualizer_data/aggregates/pulse_results.csv', 'pulse')

print("Bar charts have been created and saved.")