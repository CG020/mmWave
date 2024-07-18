# General Library Imports
# PyQt Imports
# Local Imports
# Logger
from Demo_Classes.people_tracking import PeopleTracking
import csv

from gui_common import median
from demo_defines import DEVICE_DEMO_DICT

from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel, QWidget
from PyQt5.QtGui import QFont
import pyqtgraph as pg
from PyQt5.QtCore import Qt
import datetime
import os
import numpy as np
from scipy.signal import find_peaks
import time
from icecream import ic 
from scipy.signal import medfilt

import math



# Vitals Configurables
MAX_VITALS_PATIENTS = 2
NUM_FRAMES_PER_VITALS_PACKET = 10
NUM_VITALS_FRAMES_IN_PLOT = 150
NUM_HEART_RATES_FOR_MEDIAN = 6
NUM_VITALS_FRAMES_IN_PLOT_IWRL6432 = 15


SUBJECT = "TAZMEEN"
CHAIR = True
EXPERIMENT = 'tripod'


class VitalSigns(PeopleTracking):
    def __init__(self):
        PeopleTracking.__init__(self)
        self.hearPlotData = []
        self.breathPlotData = []
        self.vitalsDict = None
        self.numTracks = None
        self.vitalsPatientData = []
        self.xWRLx432 = False
        self.vitals = []
        self.angle_buffer = [] 
        self.start_time = time.time()


        self.current_file_start_time = self.start_time
        self.file_duration = 300  # Duration in seconds before starting a new file
        self.file_counter = 0
        

        self.angle_history = []
        self.leaning_state = "upright"
        self.leaning_threshold = 20  # degrees
        self.state_change_threshold = 5

    
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if CHAIR:
            state = "chair"
        else:
            state = "stand"
        self.create_new_csv_file()
    
    def generate_csv_filename(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        state = "chair" if CHAIR else "stand"
        return os.path.join('visualizer_data', f'{EXPERIMENT}_{SUBJECT}_{state}_{timestamp}_part{self.file_counter}.csv')

    def create_new_csv_file(self):
        self.csv_file = self.generate_csv_filename()
        self.file_counter += 1
        self.current_file_start_time = time.time()
        with open(self.csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Patient ID', 'Breath Rate', 'Heart Rate', 'Patient Status', 'Range Bin',
                            'Leaning Angle', 'Leaning State'])

    def estimate_leaning_angle(self, point_cloud, height_range=(0.5, 1.8)):
        if point_cloud is None or len(point_cloud) < 2:
            return None

        # torso region filtering
        torso_points = point_cloud[(point_cloud[:, 2] > height_range[0]) & (point_cloud[:, 2] < height_range[1])]
        
        if len(torso_points) < 2:
            return None

        #  x and z coordinates
        points = torso_points[:, [0, 2]]  # x and z
        
        # weights based on y-coordinate (closer points get higher weight)
        weights = 1 / (torso_points[:, 1] + 0.1)
        
        #  weighted mean and covariance
        mean = np.average(points, axis=0, weights=weights)
        cov = np.cov(points.T, aweights=weights)

        #  eigenvectors and eigenvalues
        eigenvalues, eigenvectors = np.linalg.eigh(cov)

        # eigenvector corresponding to the largest eigenvalue
        angle_rad = np.arctan2(eigenvectors[0, 1], eigenvectors[0, 0])
        angle_deg = np.degrees(angle_rad)

        # normalize angle
        if angle_deg > 90:
            angle_deg -= 180
        elif angle_deg < -90:
            angle_deg += 180

        #  temporal filtering
        self.angle_history.append(angle_deg)
        if len(self.angle_history) > 10:
            self.angle_history.pop(0)

        filtered_angle = np.median(self.angle_history)

        return filtered_angle

    def update_leaning_state(self, angle):
        if angle is None:
            return "unknown"

        if abs(angle) <= self.leaning_threshold:
            new_state = "upright"
        elif angle > self.leaning_threshold:
            new_state = "leaning right"
        else:
            new_state = "leaning left"

        self.leaning_state = new_state

        if new_state != self.leaning_state:
            consistent_count = sum(1 for a in self.angle_history[-self.state_change_threshold:] 
                                   if (abs(a) < self.leaning_threshold) == (new_state == "upright"))
            if consistent_count >= self.state_change_threshold:
                self.leaning_state = new_state

        return self.leaning_state
    
    def init_csv(self):
        with open(self.csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Patient ID', 'Breath Rate', 'Heart Rate', 'Patient Status', 'Range Bin',
                            'Leaning Angle', 'Leaning State'])

    def write_to_csv(self, patient_id, breath_rate, heart_rate, patient_status, range_bin, leaning_angle, leaning_state):
        current_time = time.time()
        if current_time - self.current_file_start_time >= self.file_duration:
            self.create_new_csv_file()
        
        elapsed_time = current_time - self.start_time
        with open(self.csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([f"{elapsed_time:.3f}", patient_id, breath_rate, heart_rate, patient_status,
                            range_bin, leaning_angle, leaning_state])
    
    def get_pulse_time_point(self, signal):
        signal = (signal - np.min(signal)) / (np.max(signal) - np.min(signal))
        signal = np.convolve(signal, np.ones(3)/3, mode='same')
        peaks, _ = find_peaks(signal, height=0.2, distance=5)

        if len(peaks) > 0:
            return peaks[0]
        else:
            return None


    def setupGUI(self, gridLayout, demoTabs, device):
        PeopleTracking.setupGUI(self, gridLayout, demoTabs, device)

        if (DEVICE_DEMO_DICT[device]["isxWRLx432"]):
            self.xWRLx432 = True

        self.initVitalsPlots()

        gridLayout.addWidget(self.vitalsPane, 0, 2, 8, 1)

    def initVitalsPlots(self):
        self.vitalsPane = QGroupBox('Vital Signs')
        vitalsPaneLayout = QGridLayout()
        self.vitals = []

        for i in range(MAX_VITALS_PATIENTS):
            patientDict = {}
            patientName = 'Patient' + str(i+1)
            
            patientPane = QGroupBox(patientName)
            patientPaneLayout = QGridLayout()

            statusLabel = QLabel('Patient Status:')
            breathLabel = QLabel('Breath Rate:')
            heartLabel = QLabel('Heart Rate:')
            rangeBinLabel = QLabel('Range Bin:')

            patientDict['plot'] = pg.PlotWidget()
            patientDict['plot'].setBackground('w')
            patientDict['plot'].showGrid(x=True,y=True)
            patientDict['plot'].invertX(True)
            
            if(self.xWRLx432 == 1):
                patientDict['plot'].setXRange(0, NUM_VITALS_FRAMES_IN_PLOT_IWRL6432, padding=0.01)
                patientDict['plot'].setYRange(0,120,padding=0.1)
                patientDict['plot'].getPlotItem().setLabel('left', 'Hear Rate and Breath Rate per minute')
                patientDict['plot'].getPlotItem().setLabel('bottom', 'Vital Signs Frame Number')
            else:
                patientDict['plot'].setXRange(0,NUM_VITALS_FRAMES_IN_PLOT,padding=0.01)
                patientDict['plot'].setYRange(-1,1,padding=0.1)
                
            patientDict['plot'].setMouseEnabled(False,False)
            patientDict['heartGraph'] = pg.PlotCurveItem(pen=pg.mkPen(width=3, color='r'))
            patientDict['breathGraph'] = pg.PlotCurveItem(pen=pg.mkPen(width=3, color='b'))
            patientDict['plot'].addItem(patientDict['heartGraph'])
            patientDict['plot'].addItem(patientDict['breathGraph'])

            patientDict['breathRate'] = QLabel('Undefined')
            patientDict['heartRate'] = QLabel('Undefined')
            patientDict['status'] = QLabel('Undefined')
            patientDict['rangeBin'] = QLabel('Undefined')
            patientDict['name'] = patientName
            
            labelFont = QFont('Arial', 16)
            labelFont.setBold(True)
            dataFont = (QFont('Arial', 12))
            heartLabel.setFont(labelFont)
            breathLabel.setFont(labelFont)
            statusLabel.setFont(labelFont)
            rangeBinLabel.setFont(labelFont)
            patientDict['breathRate'].setStyleSheet('color: blue')
            patientDict['heartRate'].setStyleSheet('color: red')
            patientDict['status'].setFont(dataFont)
            patientDict['breathRate'].setFont(dataFont)
            patientDict['heartRate'].setFont(dataFont)
            patientDict['rangeBin'].setFont(dataFont)

            patientPaneLayout.addWidget(patientDict['plot'],2,0,1,4)
            patientPaneLayout.addWidget(statusLabel,0,0,alignment=Qt.AlignHCenter)
            patientPaneLayout.addWidget(patientDict['status'],1,0,alignment=Qt.AlignHCenter)
            patientPaneLayout.addWidget(breathLabel,0,1,alignment=Qt.AlignHCenter)
            patientPaneLayout.addWidget(patientDict['breathRate'],1,1,alignment=Qt.AlignHCenter)
            patientPaneLayout.addWidget(heartLabel,0,2,alignment=Qt.AlignHCenter)
            patientPaneLayout.addWidget(patientDict['heartRate'],1,2,alignment=Qt.AlignHCenter)
            patientPaneLayout.addWidget(rangeBinLabel,0,3,alignment=Qt.AlignHCenter)
            patientPaneLayout.addWidget(patientDict['rangeBin'],1,3,alignment=Qt.AlignHCenter)

            patientPane.setLayout(patientPaneLayout)
            patientDict['pane'] = patientPane

            self.vitals.append(patientDict)

            if (i != 0):
                patientPane.setVisible(False)

            vitalsPaneLayout.addWidget(patientPane,i,0)
        
        self.vitalsPane.setLayout(vitalsPaneLayout)
        

    def updateGraph(self, outputDict):
        PeopleTracking.updateGraph(self, outputDict)

        leaning_angle = None
        leaning_state = "unknown"

        if 'vitals' in outputDict:
            self.vitalsDict = outputDict['vitals']

        if 'numDetectedTracks' in outputDict:
            self.numTracks = outputDict['numDetectedTracks']

        if self.numTracks == 0 or self.vitalsDict is None:
            for patientId in range(min(self.maxTracks, MAX_VITALS_PATIENTS)):
                self.vitals[patientId]['status'].setText('No Patient Detected')
                self.vitals[patientId]['breathRate'].setText("N/A")
                self.vitals[patientId]['heartRate'].setText("N/A")
                self.vitals[patientId]['rangeBin'].setText("0")
                self.vitals[patientId]['heartGraph'].setData([0] * NUM_VITALS_FRAMES_IN_PLOT)
                self.vitals[patientId]['breathGraph'].setData([0] * NUM_VITALS_FRAMES_IN_PLOT)
                self.write_to_csv(patientId, "N/A", "N/A", 'No Patient Detected', 0, None, "unknown")
            return

        patientId = self.vitalsDict['id']
        if patientId < self.maxTracks:
            self.vitalsPatientData[patientId]['rangeBin'] = self.vitalsDict['rangeBin']
            self.vitalsPatientData[patientId]['breathDeviation'] = self.vitalsDict['breathDeviation']
            self.vitalsPatientData[patientId]['breathRate'] = self.vitalsDict['breathRate']

            if 'pointCloud' in outputDict:
                point_cloud = outputDict['pointCloud']
                if isinstance(point_cloud, np.ndarray) and point_cloud.shape[0] > 0:
                    current_angle = self.estimate_leaning_angle(point_cloud)
                    if current_angle is not None:
                        leaning_state = self.update_leaning_state(current_angle)
                        leaning_angle = current_angle if leaning_state != "upright" else 0.0
                    else:
                        leaning_angle = None
                        leaning_state = "unknown"
                else:
                    leaning_angle = None
                    leaning_state = "unknown"
            else:
                leaning_angle = None
                leaning_state = "unknown"

            if self.vitalsDict['heartRate'] > 0:
                self.vitalsPatientData[patientId]['heartRate'].append(self.vitalsDict['heartRate'])
            while len(self.vitalsPatientData[patientId]['heartRate']) > NUM_HEART_RATES_FOR_MEDIAN:
                self.vitalsPatientData[patientId]['heartRate'].pop(0)

            medianHeartRate = median(self.vitalsPatientData[patientId]['heartRate'])

            if float(self.vitalsDict['breathDeviation']) == 0:
                patientStatus = 'No Patient Detected'
                breathRateText = "N/A"
                heartRateText = "N/A"
                for i in range(NUM_FRAMES_PER_VITALS_PACKET):
                    self.vitalsDict['heartWaveform'][i] = 0
                    self.vitalsDict['breathWaveform'][i] = 0
            else:
                if medianHeartRate == 0:
                    heartRateText = "Updating"
                else:
                    heartRateText = str(round(medianHeartRate, 1))

                if float(self.vitalsDict['breathDeviation']) >= 0.01:
                    patientStatus = 'Presence'
                    if self.vitalsPatientData[patientId]['breathRate'] == 0:
                        breathRateText = "Updating"
                    else:
                        breathRateText = str(round(self.vitalsPatientData[patientId]['breathRate'], 1))
                else:
                    patientStatus = 'Holding Breath'
                    breathRateText = "N/A"
                

                if self.xWRLx432 == 1:
                    self.vitalsPatientData[patientId]['heartWaveform'].extend(self.vitalsDict['heartWaveform'])
                    while len(self.vitalsPatientData[patientId]['heartWaveform']) > NUM_VITALS_FRAMES_IN_PLOT_IWRL6432:
                        self.vitalsPatientData[patientId]['heartWaveform'].pop(0)

                    self.vitalsPatientData[patientId]['breathWaveform'].extend(self.vitalsDict['breathWaveform'])
                    while len(self.vitalsPatientData[patientId]['breathWaveform']) > NUM_VITALS_FRAMES_IN_PLOT_IWRL6432:
                        self.vitalsPatientData[patientId]['breathWaveform'].pop(0)
                else:
                    self.vitalsPatientData[patientId]['heartWaveform'].extend(self.vitalsDict['heartWaveform'])
                    while len(self.vitalsPatientData[patientId]['heartWaveform']) > NUM_VITALS_FRAMES_IN_PLOT:
                        self.vitalsPatientData[patientId]['heartWaveform'].pop(0)

                    self.vitalsPatientData[patientId]['breathWaveform'].extend(self.vitalsDict['breathWaveform'])
                    while len(self.vitalsPatientData[patientId]['breathWaveform']) > NUM_VITALS_FRAMES_IN_PLOT:
                        self.vitalsPatientData[patientId]['breathWaveform'].pop(0)

                heartWaveform = self.vitalsPatientData[patientId]['heartWaveform'].copy()
                heartWaveform.reverse()

                breathWaveform = self.vitalsPatientData[patientId]['breathWaveform'].copy()
                breathWaveform.reverse()

                self.vitals[patientId]['heartGraph'].setData(heartWaveform)
                self.vitals[patientId]['breathGraph'].setData(breathWaveform)
                self.vitals[patientId]['heartRate'].setText(heartRateText)
                self.vitals[patientId]['breathRate'].setText(breathRateText)
                self.vitals[patientId]['status'].setText(patientStatus)
                self.vitals[patientId]['rangeBin'].setText(str(self.vitalsPatientData[patientId]['rangeBin']))

                self.write_to_csv(patientId, breathRateText, heartRateText, patientStatus, 
                    self.vitalsPatientData[patientId]['rangeBin'], leaning_angle, leaning_state)


    def parseTrackingCfg(self, args):
        PeopleTracking.parseTrackingCfg(self, args)
        if self.maxTracks == 1:
            self.vitals[1]['pane'].setVisible(False)
        for i in range(min(self.maxTracks, MAX_VITALS_PATIENTS)):
            patientDict = {}
            patientDict['id'] = i
            patientDict['rangeBin'] = 0
            patientDict['breathDeviation'] = 0
            patientDict['heartRate'] = []
            patientDict['breathRates'] = []
            patientDict['heartWaveform'] = []
            patientDict['breathWaveform'] = []
            self.vitalsPatientData.append(patientDict)

            self.vitals[i]['pane'].setVisible(True)