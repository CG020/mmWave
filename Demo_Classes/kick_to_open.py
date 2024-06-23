# General Library Imports
from collections import deque
import time

# PyQt Imports
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import pyqtgraph as pg
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel, QVBoxLayout
import numpy as np

# Local Imports

# Logger


# x432 KTO/Gesture - Presence/Gesture Mode
KTO_PRESENCE_MODE  = 0
KTO_GESTURE_MODE   = 1

# x432 KTO Gesture Demo - Gesture Indices
KTO_NO_GESTURE     = 0
KTO_KICK           = 1
KTO_KICK_IN        = 2
KTO_KICK_OUT       = 3

class KickToOpen():
    def __init__(self):
        self.numGestures = 2,
        # List of gesture strings
        self.gestureList = ['Waiting for Kick', 'Kick']
        #Draw the box for gesture zone
        #TODO: this will eventually be a CLI command so will need to be moved to parseCfg
        leftX = -0.95
        rightX = 0.95
        nearY = 0.2
        farY = 1.5
        bottomZ = -0.5
        topZ = 1

        # Plotting Code
        self.contGestureFramecount = 10
        self.powerValues = []
        self.presenceThresh = 0
        self.presenceThreshDeque = []
        self.dopplerAvgVals = []
        self.gesture_featurePlots = {}
        self.frameDelayDoppler = 0
        self.frameDelayPresence = 0 # number of frames passed after changed to gesture mode
        self.isOn = 0 # Checking if the plot is visible or not
        presCfgArg = []
        self.presenceDetectCfg = 0
        FEATURE_VEC_LEN = 15
        self.x_avg = np.zeros(FEATURE_VEC_LEN - round(0.33 * FEATURE_VEC_LEN))
        self.y_avg = np.zeros(FEATURE_VEC_LEN - round(0.33 * FEATURE_VEC_LEN))

        # inits for presence and gesture
        self.ktoGesture = KTO_NO_GESTURE
        self.gesturePresence = KTO_PRESENCE_MODE

        self.plotStart = 0

    def setupGUI(self, gridLayout, demoTabs, device):
        # Init setup pane on left hand side
        statBox = self.initStatsPane()
        gridLayout.addWidget(statBox,2,0,1,1)

        self.ktoPane = QGroupBox()
        ktoPaneLayout = QGridLayout()
        self.ktoPane.setVisible(True)
        
        self.kto = {}
        self.gestureMode = KTO_PRESENCE_MODE # 0 = presence mode, 1 = gesture mode
        ktoTempDict = {}
        
        # Initialize the power pane and layout
        powerPane = QGroupBox("Power Plot")
        powerPaneLayout = QGridLayout()

        # Set up power usage plot
        ktoTempDict['powerplot'] = pg.PlotWidget()
        ktoTempDict['powerplot'].setMouseEnabled(False, False)
        ktoTempDict['powerplot'].setTitle('Power Usage (mW)')
        ktoTempDict['powerplot'].setFixedHeight(325)

        # # Set up basic labels so we can edit their appearance
        powerLabel = QLabel('Average Power Usage:')
        
        # # Set up data fields
        ktoTempDict['powerUsage'] = QLabel('--.-- mW')
        ktoTempDict['powerNote'] = QLabel('Please allow 15 seconds after mode switch for power to settle')
        
        # # Format text to make it attractive
        labelFont = QFont('Arial', 21)
        dataFont = QFont('Arial', 20)
        noteFont = QFont('Arial', 14)
        dataFont.setBold(True)
        powerLabel.setFont(labelFont)
        ktoTempDict['powerNote'].setFont(noteFont)
        ktoTempDict['powerUsage'].setFont(dataFont)
        ktoTempDict['powerUsage'].setStyleSheet('color: blue')
       
        # # Put the widgets into the layout
        powerPaneLayout.addWidget(powerLabel, 1,0,alignment=Qt.AlignHCenter)
        powerPaneLayout.addWidget(ktoTempDict['powerUsage'], 2,0,alignment=Qt.AlignCenter)
        powerPaneLayout.addWidget(ktoTempDict['powerNote'], 3,0, alignment=Qt.AlignCenter)

        # Set layout for the Power Pane
        powerPaneLayout.addWidget(ktoTempDict['powerplot'], 0,0)
        # powerPaneLayout.addWidget(ktoTempDict['powerUsage'], 2, 0)
        powerPane.setLayout(powerPaneLayout)
        ktoTempDict['powerPane'] = powerPane

        # Initialize the status pane and layout
        ktoStatusPane = QGroupBox("Status")
        ktoStatusPaneLayout = QVBoxLayout()
       
        # Setup gesture status box
        gestureBox = QVBoxLayout()
        ktoTempDict['gestureStatus'] = QLabel(self.gestureList[0])
        ktoTempDict['gestureStatus'].setAlignment(Qt.AlignCenter)
        ktoTempDict['gestureStatus'].setStyleSheet('background-color: black; color: white; font-size: 60px; font-weight: bold')
        #labelFont = QFont('Arial', 16)
        #ktoTempDict['gestureStatus'].setFont(labelFont)
        gestureBox.addWidget(ktoTempDict['gestureStatus'],1)
        ktoStatusPaneLayout.addLayout(gestureBox)
       
        # Setup mode status box
        modeBox = QVBoxLayout()
        ktoTempDict['modeStatus'] = QLabel("Undefined")
        ktoTempDict['modeStatus'].setAlignment(Qt.AlignCenter)
        ktoTempDict['modeStatus'].setStyleSheet('background-color: green; color: white; font-size: 60px; font-weight:bold')
        #labelFont = QFont('Arial', 14)
        #ktoTempDict['modeStatus'].setFont(labelFont)
        modeBox.addWidget(ktoTempDict['modeStatus'],2)
        ktoStatusPaneLayout.addLayout(modeBox)
        ktoStatusPane.setLayout(ktoStatusPaneLayout)
        ktoTempDict['statusPane'] = ktoStatusPane

        # Initialize plot pane and layout
        ktoPlotPane = QGroupBox("Presence Plot")
        ktoPlotPaneLayout = QGridLayout()


        ktoTempDict['presenceNote'] = QLabel('Searching for presence between 0.25 and 2.25 m')
        ktoTempDict['presenceNote'].setFont(noteFont)

        # Set up presence threshold plot
        ktoTempDict['presenceplot'] = pg.PlotWidget()
        # ktoTempDict['plot'].setBackground('w')
        # ktoTempDict['plot'].showGrid(x=True, y=True)
        ref = self.presenceDetectCfg
        ktoTempDict['presenceplot'].setMouseEnabled(False, False)
        ktoTempDict['presenceplot'].setTitle('Presence Threshold')
        ktoTempDict['presenceplot'].setFixedHeight(250)

        ktoTempDict['dopplerplot'] = pg.PlotWidget()
        ktoTempDict['dopplerplot'].setMouseEnabled(False, False)
        ktoTempDict['dopplerplot'].setTitle('Doppler Average')
        ktoTempDict['dopplerplot'].setFixedHeight(250)

        # Put the widgets into the layout
        ktoPlotPaneLayout.addWidget(ktoTempDict['presenceNote'], 0, 0, alignment=Qt.AlignCenter)
        ktoPlotPaneLayout.addWidget(ktoTempDict['presenceplot'], 1,0)
        ktoPlotPaneLayout.addWidget(ktoTempDict['dopplerplot'], 1,1)
        ktoTempDict['dopplerplot'].hide()
        ktoPlotPane.setLayout(ktoPlotPaneLayout)
        ktoTempDict['pane'] = ktoPlotPane

        # Make KTO data accessible by other functions
        #self.kto.append(ktoTempDict)
        self.kto = ktoTempDict

        # Add all panes to the overall KTO display
        ktoPaneLayout.addWidget(powerPane, 2,0)
        ktoPaneLayout.addWidget(ktoStatusPane, 1,0)
        ktoPaneLayout.addWidget(ktoPlotPane, 0,0)

        self.ktoPane.setLayout(ktoPaneLayout)

        self.ktoGestureTimer = QTimer()
        self.ktoGestureTimer.setInterval(1000)
        self.ktoGestureTimer.timeout.connect(self.resetKTOGestureDisplay)

        demoTabs.addTab(self.ktoPane, 'Kick to Open')
        demoTabs.setCurrentIndex(1)

    def initStatsPane(self):
        statBox = QGroupBox('Statistics')
        self.frameNumDisplay = QLabel('Frame: 0')
        self.plotTimeDisplay = QLabel('Plot Time: 0 ms')
        self.statsLayout = QVBoxLayout()
        self.statsLayout.addWidget(self.frameNumDisplay)
        self.statsLayout.addWidget(self.plotTimeDisplay)
        statBox.setLayout(self.statsLayout)

        return statBox

    def updateGraph(self, outputDict):
        self.plotStart = int(round(time.time()*1000))

        if ('gestureFeatures' in outputDict):
            self.gestureFeatures = outputDict['gestureFeatures']
            self.updateGestureFeatures(self.gestureFeatures)

        if all(key in outputDict for key in ['ktoGesture', 'gestureFeatures', 'localization_mag', 'localization_range', 'localization_elevidx', 'localization_azimidx']):
            Localization_points = 5
            FEATURE_VEC_LEN = 15
            classifierOutput = outputDict['ktoGesture']
            dopAve_sample = np.zeros(FEATURE_VEC_LEN - round(0.33 * FEATURE_VEC_LEN))

            ArrangedMagnitudeTopKPoints, Index = zip(*sorted(zip(outputDict['localization_mag'], range(len(outputDict['localization_mag']))), reverse=True))
            ArrangedRangeIdx = outputDict['localization_range']
            Range = [i * 0.054 for i in ArrangedRangeIdx]
            ArrangedElevIdx = outputDict['localization_elevidx']
            ArrangedAzimIdx = outputDict['localization_azimidx']
            Range = Range[:Localization_points]
            ArrangedElevIdx = np.array(ArrangedElevIdx[:Localization_points]).astype(float)
            ArrangedAzimIdx = np.array(ArrangedAzimIdx[:Localization_points]).astype(float)
            azim_angles = [np.degrees(np.arcsin(2 * i / 32)) for i in ArrangedAzimIdx]
            elev_angles = [np.degrees(np.arcsin(2 * i / 32)) for i in ArrangedElevIdx]
            x_loc = [Range[i] * np.cos(np.radians(azim_angles[i])) * np.cos(np.radians(elev_angles[i])) for i in range(len(Range))]
            y_loc = [Range[i] * np.sin(np.radians(azim_angles[i])) * np.cos(np.radians(elev_angles[i])) for i in range(len(Range))]
            self.x_avg[-1] = np.mean(x_loc)
            self.y_avg[-1] = np.mean(y_loc)
            if classifierOutput == KTO_KICK:
                dop_samp = list(self.dopplerAvgVals)[::-1][-10:]
                minVal, minIdx = np.min(dop_samp), np.argmin(dop_samp)
                maxVal, maxIdx = np.max(dop_samp), np.argmax(dop_samp)
                if minVal < -3.8 and maxVal > 3.8:
                    x_plot = self.x_avg[minIdx:maxIdx]
                    y_plot = self.y_avg[minIdx:maxIdx]
                    count_val_loc = np.count_nonzero((y_plot <= 0.3) & (y_plot >= -0.3) & (x_plot <= 0.4))
                    count_val_loc_far = np.count_nonzero((y_plot <= 0.3) & (y_plot >= -0.3) & (x_plot <= 0.7) & (x_plot >= 0.4))
                    if count_val_loc >= 3 and (count_val_loc_far >= 3 or count_val_loc >= 5):
                        classifierOutput = 3
                        self.updateKTOGestureDisplay('Kick inside ROI')
                    else:
                        classifierOutput = 2
                        self.updateKTOGestureDisplay('Kick outside ROI')
                else:
                    self.updateKTOGestureDisplay('Kick')
            
            self.x_avg = np.roll(self.x_avg, -1)
            self.y_avg = np.roll(self.y_avg, -1)

        elif ('ktoGesture' in outputDict):
            self.ktoGesture = outputDict['ktoGesture']

            if (self.ktoGesture is KTO_KICK):
                self.updateKTOGestureDisplay('Kick')

        if ('gesturePresence' in outputDict):
            self.gesturePresence = outputDict['gesturePresence']

            # print('Presence Threshold ', self.presenceDetectCfg)
            #if gesture/presence mode switched, 
            if(self.gestureMode != self.gesturePresence):
                if(self.gesturePresence==KTO_PRESENCE_MODE):
                    self.isOn = False
                    self.kto['modeStatus'].setStyleSheet('background-color: green; color: white; font-size: 60px; font-weight:bold')
                    self.kto['modeStatus'].setText("Low Power Mode")
                    self.kto['presenceplot'].setVisible(True)
                    self.kto['presenceNote'].setVisible(True)
                    self.frameDelayPresence = 0
                    self.updateKTOGestureDisplay('Searching for Presence')
                    # for box in self.boundaryBoxViz:
                    #     if ('gestureZone' in box['name']):
                    #         box['color'].setCurrentText('Blue')
                elif(self.gesturePresence==KTO_GESTURE_MODE):
                    self.isOn = True
                    self.frameDelayDoppler = 0
                    self.kto['modeStatus'].setStyleSheet('background-color: orange; color: white; font-size: 60px; font-weight:bold')
                    self.kto['modeStatus'].setText("Gesture Mode")
                    self.kto['dopplerplot'].setVisible(True)
                    self.updateKTOGestureDisplay(self.gestureList[0])
                    # for box in self.boundaryBoxViz:
                    #     if ('gestureZone' in box['name']):
                    #         box['color'].setCurrentText('Red')                
                self.gestureMode = self.gesturePresence
            if (self.isOn == True):
                self.frameDelayPresence+=1
            elif (self.isOn == False):
                self.frameDelayDoppler+=1
            if (self.isOn and self.frameDelayPresence > 80):
                # Delay the plot from disappearing for 80 frames to show the spike in presence
                self.kto['presenceplot'].setVisible(False)
                self.kto['presenceNote'].hide()
                # self.isOn = False
            elif (not self.isOn and self.frameDelayDoppler > 2):
                self.kto['dopplerplot'].setVisible(False)
            #     self.isOn = True 

        if ('powerData' in outputDict):
            self.powerData = outputDict['powerData']
            self.ktoPowerDataHandler(self.powerData)

        if ('presenceThreshold' in outputDict):
            self.presenceThresh = outputDict['presenceThreshold']
            self.presenceThresholdHandler(self.presenceThresh)

        self.graphDone(outputDict)

    def graphDone(self, outputDict):
        plotTime = int(round(time.time()*1000)) - self.plotStart
        self.plotTimeDisplay.setText('Plot Time: ' + str(plotTime) + 'ms')
        self.plotComplete = 1

        if ('frameNum' in outputDict):
            self.frameNumDisplay.setText('Frame: ' + str(outputDict['frameNum']))

        if ('numDetectedPoints' in outputDict):
            self.plotTimeDisplay.setText('Points: ' + str(plotTime) + 'ms')

    def updateKTOGestureDisplay(self, text):
        if('Kick' in text):
            self.kto['gestureStatus'].setStyleSheet(f'background-color: green; color: white; font-size: 60px; font-weight: bold')
        else:
            self.kto['gestureStatus'].setStyleSheet(f'background-color: black; color: white; font-size: 60px; font-weight: bold')
        self.kto['gestureStatus'].setText(text)
        self.ktoGestureTimer.start()  

    def updateGestureFeatures(self, features):

        self.kto['dopplerplot'].setXRange(0, 28, padding=0.001)
        self.kto['dopplerplot'].setYRange(-25, 25, padding=0.001)

        dopplerAvgData = deque(self.dopplerAvgVals)
        dopplerAvgData.appendleft(features[1])
        if (len(dopplerAvgData) > 30):
            dopplerAvgData.pop()

        self.dopplerAvgVals = dopplerAvgData

        self.kto['dopplerplot'].clear()
        self.kto['dopplerplot'].plot(self.dopplerAvgVals)
                
    def ktoPowerDataHandler(self, powerData):
        powerStr = str((powerData['power1v2'] \
            + powerData['power1v2RF'] + powerData['power1v8'] + powerData['power3v3']) * 0.1)
        self.kto['powerUsage'].setText(powerStr[:5] + ' mW')
        # print(powerStr)
        # Convert the value into an integer to be used in plotting
        # Definitely could have been done better
        powerval = ((powerData['power1v2'] \
            + powerData['power1v2RF'] + powerData['power1v8'] + powerData['power3v3']) * 0.1) 

        self.kto['powerplot'].setXRange(0, 500, padding=0.001)
        self.kto['powerplot'].setYRange(0, 350, padding=0.001)

        powData = deque(self.powerValues)
        powData.appendleft(powerval)

        if (len(powData) > 500):
            powData.pop()

        self.powerValues = powData

        self.kto['powerplot'].clear()
        self.kto['powerplot'].plot(self.powerValues)

    def presenceThresholdHandler(self, presenceThreshold):
        ref = self.presenceDetectCfg
        refLine = pg.InfiniteLine(pos=ref, angle=0, pen='r', label='Presence Threshold Value')

        # presencemin = str(self.presenceMinCfg)
        # presencemax = str(self.presenceMaxCfg)

        self.kto['presenceplot'].setXRange(0, 150, padding=0.001)
        self.kto['presenceplot'].setYRange(0, ref*1.75, padding=0.001)

        presData = deque(self.presenceThreshDeque)
        # print(self.presenceThresh) # print out each value in the frame for 160 frames
        presData.appendleft(presenceThreshold)

        if (len(presData) > 160):
            presData.pop()
        
        self.presenceThreshDeque = presData

        self.kto['presenceplot'].clear()
        self.kto['presenceplot'].addItem(refLine) # Plot the presence threshold value as a red line
        self.kto['presenceplot'].plot(self.presenceThreshDeque)

    def resetKTOGestureDisplay(self):
        # presence mode
        if(self.gestureMode == KTO_PRESENCE_MODE):
            self.kto['gestureStatus'].setStyleSheet(f'background-color: black; color: white; font-size: 60px; font-weight: bold')
            self.kto['gestureStatus'].setText('Searching for Presence')
        # gesture mode
        elif(self.gestureMode == KTO_GESTURE_MODE):
            self.kto['gestureStatus'].setStyleSheet(f'background-color: black; color: white; font-size: 60px; font-weight: bold')
            self.kto['gestureStatus'].setText(self.gestureList[0])
        self.ktoGestureTimer.stop()

    def parseSensorPosition(self, args, is_x843):
        if (is_x843):
            self.sensorHeight = float(args[1])
            self.az_tilt = float(args[2])
            self.elev_tilt = float(args[3])
        else:
            self.xOffset = float(args[1])
            self.yOffset = float(args[2])
            self.sensorHeight = float(args[3])
            self.az_tilt = float(args[4])
            self.elev_tilt = float(args[5])

        self.evmBox.resetTransform()
        self.evmBox.rotate(-1 * self.elev_tilt, 1, 0, 0)
        self.evmBox.rotate(-1 * self.az_tilt, 0, 0, 1)
        self.evmBox.translate(0, 0, self.sensorHeight)

        bottomZ += self.sensorHeight
        topZ += self.sensorHeight

    def parsePresenceDetectConfig(self, args):
        self.presenceDetectCfg = float(args[2])
