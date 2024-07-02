import serial
import time

# Configuration
control_port = 'COM6'  # Replace with your control port
data_port = 'COM5'     # Replace with your data port
control_baudrate = 115200
data_baudrate = 921600
config_file_path = 'vital_signs_AOP_6m.cfg'
raw_data_file = 'raw_data.bin'

# Open serial ports
control_serial = serial.Serial(control_port, control_baudrate, timeout=1)
data_serial = serial.Serial(data_port, data_baudrate, timeout=1)

# Function to send configuration commands from file
def send_config_from_file(file_path, serial_port):
    with open(file_path, 'r') as file:
        for line in file:
            serial_port.write((line.strip() + '\n').encode())
            serial_port.flush()
            time.sleep(0.1)

# Send configuration commands
send_config_from_file(config_file_path, control_serial)

# Capture raw data
capture_duration = 10  # Capture for 10 seconds

try:
    start_time = time.time()
    with open(raw_data_file, 'wb') as f:
        while time.time() - start_time < capture_duration:
            data = data_serial.read(4096)
            f.write(data)
    print(f"Raw data saved to {raw_data_file}")

except KeyboardInterrupt:
    print("Data capture interrupted. Writing captured data to file...")

finally:
    # Close serial ports
    control_serial.close()
    data_serial.close()
