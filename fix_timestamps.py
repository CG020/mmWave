import csv
import tempfile
import shutil

def adjust_timestamps(file_path, offset=603.045):
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, newline='')
    
    with open(file_path, 'r') as csvfile, temp_file:
        reader = csv.reader(csvfile)
        writer = csv.writer(temp_file)

        # Write header
        header = next(reader)
        writer.writerow(header)

        # Process each row
        for row in reader:
            # Adjust timestamp
            row[0] = str(float(row[0]) + offset)
            writer.writerow(row)

    # Replace the original file with the modified temp file
    shutil.move(temp_file.name, file_path)

# Usage
file_path = 'visualizer_data\\floor_MIKHAIL_stand\\vs_MIKHAIL_stand_20240710_130134_part6.csv'
adjust_timestamps(file_path)
print(f"Timestamps in {file_path} have been adjusted.")