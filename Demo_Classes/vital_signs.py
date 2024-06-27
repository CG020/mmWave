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

import math



# Vitals Configurables
MAX_VITALS_PATIENTS = 2
NUM_FRAMES_PER_VITALS_PACKET = 10
NUM_VITALS_FRAMES_IN_PLOT = 150
NUM_HEART_RATES_FOR_MEDIAN = 6
NUM_VITALS_FRAMES_IN_PLOT_IWRL6432 = 15


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

        self.previous_pulse_time_point1 = None
        self.previous_pulse_time_point2 = None
        self.distance_between_points = 0.3

        # empirical constants (to be updated during calibration)
        self.A = 120
        self.B = 10
        self.C = 80
        self.D = 5

        # blood pressure measurements from sphygmomanometer
        self.sbp_manual = 120  # Systolic Blood Pressure
        self.dbp_manual = 80  # Diastolic Blood Pressure
    
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_file = os.path.join('visualizer_data', f'vital_signs_data_{timestamp}.csv')
        self.init_csv()
    

    def estimate_leaning_angle(self, point_cloud):
        if point_cloud is None or len(point_cloud) < 2:
            return None

        # Extract x and z coordinates
        points = point_cloud[:, [0, 2]]  # x and z

        mean = np.mean(points, axis=0)
        points_centered = points - mean

        if len(points_centered) < 2:
            return None

        cov_matrix = np.cov(points_centered, rowvar=False)

        eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)

        largest_eigenvector = eigenvectors[:, eigenvalues.argmax()]

        angle_rad = np.arctan2(largest_eigenvector[0], largest_eigenvector[1])
        angle_deg = np.degrees(angle_rad)

        # normalize
        if angle_deg > 90:
            angle_deg -= 180
        elif angle_deg < -90:
            angle_deg += 180

        return angle_deg
    
    def init_csv(self):
        with open(self.csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Timestamp', 'Patient ID', 'Breath Rate', 'Heart Rate', 'Patient Status', 'Range Bin', 'PTT', 'PWV', 'SBP', 'DBP', 'Blood Pressure', 'Leaning Angle'])

    def write_to_csv(self, patient_id, breath_rate, heart_rate, patient_status, range_bin, ptt, pwv, sbp, dbp, bp, leaning_angle):
        current_time = time.time() - self.start_time
        with open(self.csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([f"{current_time:.3f}", patient_id, breath_rate, heart_rate, patient_status, range_bin, ptt, pwv, sbp, dbp, bp, leaning_angle])
    
    def get_pulse_time_point(self, signal):
        signal = (signal - np.min(signal)) / (np.max(signal) - np.min(signal))
        signal = np.convolve(signal, np.ones(3)/3, mode='same')
        peaks, _ = find_peaks(signal, height=0.2, distance=5)

        if len(peaks) > 0:
            return peaks[0]
        else:
            return None

    def calculate_ptt(self, pulse_time_point1, pulse_time_point2):
        if pulse_time_point1 is None or pulse_time_point2 is None:
            return None
        ptt = abs(pulse_time_point2 - pulse_time_point1)
        return ptt if ptt != 0 else None

    def calculate_pwv(self, ptt):
        if ptt is None:
            return None
        pwv = self.distance_between_points / ptt
        return pwv
    
    def calibrate(self):
        if self.sbp_manual is None or self.dbp_manual is None:
            raise ValueError("set manual SBP and DBP measurements before calibration")
        ptt_initial = 0.1  # PTT value during initial calibration
        self.B = (self.sbp_manual - 120) / ptt_initial
        self.D = (self.dbp_manual - 80) / ptt_initial
        self.A = 120
        self.C = 80

    def estimate_blood_pressure(self, ptt, pwv):
        if ptt is None or pwv is None:
            return None, None
        sbp = self.A - self.B * ptt
        dbp = self.C - self.D * ptt
        return sbp, dbp

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

        if 'vitals' in outputDict:
            self.vitalsDict = outputDict['vitals']

        if 'numDetectedTracks' in outputDict:
            self.numTracks = outputDict['numDetectedTracks']

        if self.vitalsDict is not None and self.numTracks is not None:
            patientId = self.vitalsDict['id']
            if patientId < self.maxTracks:
                self.vitalsPatientData[patientId]['rangeBin'] = self.vitalsDict['rangeBin']
                self.vitalsPatientData[patientId]['breathDeviation'] = self.vitalsDict['breathDeviation']
                self.vitalsPatientData[patientId]['breathRate'] = self.vitalsDict['breathRate']

                if 'pointCloud' in outputDict:
                    point_cloud = outputDict['pointCloud']
                    if len(point_cloud) > 0:
                        current_angle = self.estimate_leaning_angle(point_cloud)
                        if current_angle is not None:
                            self.angle_buffer.append(current_angle)
                            if len(self.angle_buffer) > 10: 
                                self.angle_buffer.pop(0)
                            leaning_angle = sum(self.angle_buffer) / len(self.angle_buffer)
                        else:
                            leaning_angle = None
                    else:
                        leaning_angle = None

                if self.vitalsDict['heartRate'] > 0:
                    self.vitalsPatientData[patientId]['heartRate'].append(self.vitalsDict['heartRate'])

                while len(self.vitalsPatientData[patientId]['heartRate']) > NUM_HEART_RATES_FOR_MEDIAN:
                    self.vitalsPatientData[patientId]['heartRate'].pop(0)

                medianHeartRate = median(self.vitalsPatientData[patientId]['heartRate'])

                if float(self.vitalsDict['breathDeviation']) == 0 or self.numTracks == 0:
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
                    
                    # PTT and PWV
                    current_pulse_time_point1 = self.get_pulse_time_point(self.vitalsDict['heartWaveform'])  # Pass heart waveform data
                    current_pulse_time_point2 = self.get_pulse_time_point(self.vitalsDict['breathWaveform'])  # Pass breath waveform data
                    ptt = self.calculate_ptt(current_pulse_time_point1, current_pulse_time_point2)
                    pwv = self.calculate_pwv(ptt) if ptt is not None else None

                    if ptt is not None and pwv is not None:
                        sbp = self.A * pwv + self.B
                        dbp = self.C * pwv + self.D
                        bp = sbp/dbp
                    else:
                        sbp = None
                        dbp = None
                        bp = None

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
                              self.vitalsPatientData[patientId]['rangeBin'], ptt, pwv, sbp, dbp, bp, leaning_angle)


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