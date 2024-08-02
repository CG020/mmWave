import pandas as pd
from datetime import datetime, timedelta

# Correct path to the CSV file
file_path = 'visualizer_data/floor_CANDICE_chair/floor_Candice_chair_vitals.csv'

# Read the CSV file
try:
    data = pd.read_csv(file_path)
except FileNotFoundError:
    print(f"Error: The file '{file_path}' was not found.")
    exit(1)
except Exception as e:
    print(f"An error occurred while reading the file: {e}")
    exit(1)

# Convert time strings to datetime objects
for col in ['Time for Heart', 'Time for Pulse', 'Time for Breath']:
    data[col] = pd.to_datetime(data[col], format='%M:%S', errors='coerce')

# Find the last timestamp for each column
last_heart_time = data['Time for Heart'].max()
last_pulse_time = data['Time for Pulse'].max()
last_breath_time = data['Time for Breath'].max()

# Function to adjust time
def adjust_time(time, last_time):
    if pd.isnull(time) or pd.isnull(last_time):
        return time
    if time < last_time:
        return last_time + (time - datetime(1900, 1, 1, 0, 0, 0))
    return time

# Adjust times
data['Time for Heart'] = data['Time for Heart'].apply(lambda x: adjust_time(x, last_heart_time))
data['Time for Pulse'] = data['Time for Pulse'].apply(lambda x: adjust_time(x, last_pulse_time))
data['Time for Breath'] = data['Time for Breath'].apply(lambda x: adjust_time(x, last_breath_time))

# Convert back to string format
for col in ['Time for Heart', 'Time for Pulse', 'Time for Breath']:
    data[col] = data[col].dt.strftime('%M:%S')

# Display the adjusted data
print(data.to_string(index=False))