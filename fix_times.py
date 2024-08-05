import os
import csv
from datetime import timedelta

def parse_timestamp(timestamp):
    seconds, milliseconds = map(int, timestamp.split('.'))
    return seconds * 1000 + milliseconds 

def format_timestamp(total_milliseconds):
    seconds = total_milliseconds // 1000
    milliseconds = total_milliseconds % 1000
    return f"{seconds}.{milliseconds:03d}"

def get_last_timestamp(file_path):
    with open(file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header
        last_timestamp = 0
        for row in reader:
            last_timestamp = parse_timestamp(row[0])
    return last_timestamp

def process_files(directory):
    all_files = sorted([f for f in os.listdir(directory) if f.endswith('.csv')])
    
    restart_index = next(i for i, f in enumerate(all_files) if 'part0' in f and i > 0)
    last_file_before_restart = all_files[restart_index - 1]
    
    last_timestamp = get_last_timestamp(os.path.join(directory, last_file_before_restart))
    
    time_offset = last_timestamp + 1  
    
    for file in all_files[restart_index:]:
        output_file = f'realigned_{file}'
        with open(os.path.join(directory, file), 'r') as infile, \
             open(os.path.join(directory, output_file), 'w', newline='') as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            
            headers = next(reader)
            writer.writerow(headers)
            
            for row in reader:
                timestamp = parse_timestamp(row[0])
                adjusted_timestamp = timestamp + time_offset
                row[0] = format_timestamp(adjusted_timestamp)
                writer.writerow(row)
        
        print(f"Processed {file} -> {output_file}")


# Usage
directory = 'visualizer_data/floor_CANDICE_stand'
process_files(directory)