# General Library Imports
# PyQt Imports
# Local Imports
# Logger
from Demo_Classes.people_tracking import PeopleTracking

from gui_common import median
from demo_defines import DEVICE_DEMO_DICT

from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel, QWidget
from PyQt5.QtGui import QFont
import pyqtgraph as pg
from PyQt5.QtCore import Qt

# Vitals Configurables
MAX_VITALS_PATIENTS = 2
NUM_FRAMES_PER_VITALS_PACKET = 15
NUM_VITALS_FRAMES_IN_PLOT = 150
NUM_HEART_RATES_FOR_MEDIAN = 10
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
            
            # Initialize the pane and layout
            patientPane = QGroupBox(patientName)
            patientPaneLayout = QGridLayout()

            # Set up basic labels so we can edit their appearance
            statusLabel = QLabel('Patient Status:')
            breathLabel = QLabel('Breath Rate:')
            heartLabel = QLabel('Heart Rate:')
            rangeBinLabel = QLabel('Range Bin:')

            # Set up patient vitals plot
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

            # Set up all other patient data fields
            patientDict['breathRate'] = QLabel('Undefined')
            patientDict['heartRate'] = QLabel('Undefined')
            patientDict['status'] = QLabel('Undefined')
            patientDict['rangeBin'] = QLabel('Undefined')
            patientDict['name'] = patientName
            
            # Format text to make it attractive
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

            # Put the widgets into the layout
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

            # Make patient vitals data accessable by other functions
            self.vitals.append(patientDict)

            if (i != 0):
                patientPane.setVisible(False)

            # Add this patient to the overall vitals pane
            vitalsPaneLayout.addWidget(patientPane,i,0)
        
        self.vitalsPane.setLayout(vitalsPaneLayout)

    def updateGraph(self, outputDict):
        PeopleTracking.updateGraph(self, outputDict)

        # Vital Signs Info
        if ('vitals' in outputDict):
            self.vitalsDict = outputDict['vitals']

                # Number of Tracks
        if ('numDetectedTracks' in outputDict):
            self.numTracks = outputDict['numDetectedTracks']

        # Vital Signs info
        if (self.vitalsDict is not None and self.numTracks is not None):
            # Update info for each patient
            patientId = self.vitalsDict['id']
            # Check that patient id is valid
            if (patientId < self.maxTracks):
                self.vitalsPatientData[patientId]['rangeBin'] = self.vitalsDict['rangeBin']
                self.vitalsPatientData[patientId]['breathDeviation'] = self.vitalsDict['breathDeviation']
                self.vitalsPatientData[patientId]['breathRate'] = self.vitalsDict['breathRate']

                # Take the median of the last n heartrates to prevent it from being sporadic
                self.vitalsPatientData[patientId]['heartRate'].append(self.vitalsDict['heartRate'])
                while (len(self.vitalsPatientData[patientId]['heartRate']) > NUM_HEART_RATES_FOR_MEDIAN):
                    self.vitalsPatientData[patientId]['heartRate'].pop(0)
                medianHeartRate = median(self.vitalsPatientData[patientId]['heartRate'])
                
                # Check if the patient is holding their breath, and if there is a patient  detected at all
                # TODO ensure vitals output is 0 
                if(float(self.vitalsDict['breathDeviation']) == 0 or self.numTracks == 0):
                    patientStatus = 'No Patient Detected'
                    breathRateText = "N/A"
                    heartRateText = "N/A"
                    # Workaround to ensure waveform is flat when no track is present
                    for i in range(NUM_FRAMES_PER_VITALS_PACKET):
                        self.vitalsDict['heartWaveform'][i] = 0
                        self.vitalsDict['breathWaveform'][i] = 0
                else:
                    if (medianHeartRate == 0):
                        heartRateText = "Updating"
                    else:
                        heartRateText = str(round(self.vitalsDict['heartWaveform'][0], 1))
                    # Patient breathing normally
                    if (float(self.vitalsDict['breathDeviation']) >= 0.02):
                        patientStatus = 'Presence'
                        if(self.vitalsPatientData[patientId]['breathRate'] == 0):
                            breathRateText = "Updating"
                        else:
                            # Round the floats to 1 decimal place and format them for display
                            breathRateText = str(round(self.vitalsPatientData[patientId]['breathRate'], 1))
                     # Patient holding breath
                    else:
                        patientStatus = 'Holding Breath'
                        breathRateText = "N/A"
                 
                if(self.xWRLx432 == 1):                
                    self.vitalsPatientData[patientId]['heartWaveform'].extend(self.vitalsDict['heartWaveform'])
                    while (len(self.vitalsPatientData[patientId]['heartWaveform']) > NUM_VITALS_FRAMES_IN_PLOT_IWRL6432):
                        self.vitalsPatientData[patientId]['heartWaveform'].pop(0)

                    # Add breathing rate waveform data for this packet to the graph
                    self.vitalsPatientData[patientId]['breathWaveform'].extend(self.vitalsDict['breathWaveform'])
                    while (len(self.vitalsPatientData[patientId]['breathWaveform']) > NUM_VITALS_FRAMES_IN_PLOT_IWRL6432):
                        self.vitalsPatientData[patientId]['breathWaveform'].pop(0)
                else: 
                    # Add heart rate waveform data for this packet to the graph
                    self.vitalsPatientData[patientId]['heartWaveform'].extend(self.vitalsDict['heartWaveform'])
                    while (len(self.vitalsPatientData[patientId]['heartWaveform']) > NUM_VITALS_FRAMES_IN_PLOT):
                        self.vitalsPatientData[patientId]['heartWaveform'].pop(0)

                    # Add breathing rate waveform data for this packet to the graph
                    self.vitalsPatientData[patientId]['breathWaveform'].extend(self.vitalsDict['breathWaveform'])
                    while (len(self.vitalsPatientData[patientId]['breathWaveform']) > NUM_VITALS_FRAMES_IN_PLOT):
                        self.vitalsPatientData[patientId]['breathWaveform'].pop(0)

                # Copy waveforms so that we can reverse their orientation
                heartWaveform = self.vitalsPatientData[patientId]['heartWaveform'].copy()
                heartWaveform.reverse()

                # Copy waveforms so that we can reverse their orientation
                breathWaveform = self.vitalsPatientData[patientId]['breathWaveform'].copy()
                breathWaveform.reverse()

                # Update relevant info in GUI
                self.vitals[patientId]['heartGraph'].setData(heartWaveform)
                self.vitals[patientId]['breathGraph'].setData( breathWaveform)
                self.vitals[patientId]['heartRate'].setText(heartRateText)
                self.vitals[patientId]['breathRate'].setText(breathRateText)
                self.vitals[patientId]['status'].setText(patientStatus)
                self.vitals[patientId]['rangeBin'].setText(str(self.vitalsPatientData[patientId]['rangeBin']))

    def parseTrackingCfg(self, args):
        PeopleTracking.parseTrackingCfg(self, args)
        if (self.maxTracks == 1):
            self.vitals[1]['pane'].setVisible(False)
        for i in range(min(self.maxTracks,MAX_VITALS_PATIENTS)):
            # Initialize Vitals output dictionaries for each potential patient 
            patientDict = {}
            patientDict ['id'] = i
            patientDict ['rangeBin'] = 0
            patientDict ['breathDeviation'] = 0
            patientDict ['heartRate'] = []
            patientDict ['breathRate'] = 0
            patientDict ['heartWaveform'] = []
            patientDict ['breathWaveform'] = []
            self.vitalsPatientData.append(patientDict)

            # Make each patient's pane visible
            self.vitals[i]['pane'].setVisible(True)
