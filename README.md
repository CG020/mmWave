# MMWave IWR6843AOPEVM Data Exraction

Source code from the mmWaveSDK toolbox where visualizers are run to display real-time data
capture from the Texas Instruments IWR6843AOPEVM MCBOOST milimeter wave radar board. 
Edited to output data capture into organized structure - parameters for Vital Signs Lab updated.


## Scripts

- figure_scripts folder holds Python scripts for graphing vital sign trends including heart rate over distance, breathing rate over distance, and leaning direction over distance
- Visualizer Data folder holds raw CSV data capture
- fix_times and fix_timestamps scripts handle formatting times from raw collection format for graphing and saving back to CSV
- vital_signs_AOP_6m.cfg is the specific configuration for the IWR6843AOPEVM radar board - parameters edited throughout project for wider range of detection
- Demo_Classes/vital_signs.py where extraction code and collection grouping added
