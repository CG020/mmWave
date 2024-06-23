# General Library Imports
from collections import deque
import time

# PyQt Imports
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QFont
import pyqtgraph as pg
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget

# Local Imports
from demo_defines import *

# Logger

# GESTURE DEMOs
# 6843 Gesture Demo variants
GESTURE_6843 = "Near Range (0.05-0.3m)"

IWR6843_GESTURE_DEMO_TYPES = [GESTURE_6843]

GESTURE_FD_DEMO = "Fixed Distance (2m)"

xWRLx432_GESTURE_DEMO_TYPES = [GESTURE_FD_DEMO]

# Gestures
GESTURE_NONE        = "No Gesture"
GESTURE_L2R         = "Left-to-Right"
GESTURE_R2L         = "Right-to-Left"
GESTURE_U2D         = "Up-to-Down"
GESTURE_D2U         = "Down-to-Up"
GESTURE_PUSH        = "Push"
GESTURE_PULL        = "Pull"
GESTURE_TWIRL_CW    = "CW Twirl"
GESTURE_TWIRL_CCW   = "CCW Twirl"
GESTURE_SHINE       = "Shine"

# Supported Gestures by Demo
GESTURE_6843_GESTURES       = [GESTURE_NONE, GESTURE_L2R, GESTURE_R2L, GESTURE_U2D, GESTURE_D2U, GESTURE_TWIRL_CW, GESTURE_TWIRL_CCW, GESTURE_PUSH, GESTURE_PULL, GESTURE_SHINE]
GESTURE_FD_DEMO_GESTURES    = [GESTURE_NONE, GESTURE_L2R, GESTURE_R2L, GESTURE_U2D, GESTURE_D2U, GESTURE_PUSH, GESTURE_PULL]

# Constants for 6843 gesture demo used in post processing alg
GESTURE_FEATURE_LENGTH = 15 
GESTURE_NUM_GESTURES   = 9

# Constants for 6432 gesture demos
GESTURE_PRESENCE_MODE_x432  = 0
GESTURE_GESTURE_MODE_x432   = 1

# # 6432 6 Gesture Demo - Gestures
GESTURE_NO_GESTURE_6432     = 0

class GestureRecognition():
    def __init__(self):
        self.gesture_featurePlots = {}
        self.plots = {}
        self.activePlots = []
        self.frameNum = 0
        self.plotStart = 0
        self.frameDelayDoppler = 0
        self.frameDelayPresence = 0 # number of frames passed after changed to gesture mode
        self.isOn = 0 # Checking if the plot is visible or not
        self.gesturePcControl = False
        self.powerValues = []
        self.presenceThresh = []
        self.dopplerAvgVals = []
        self.ContGestureCnt = 0
        self.demoMode = 1 # 0-gesture only mode; 1-presence+gesture mode; 2-presence only mode
        self.firstTimeSetupDone = False


    def setupGUI(self, gridLayout, demoTabs, device):
        self.parentGridLay = gridLayout
        self.windowDemoTabs = demoTabs
        self.device = device
        # Default gesture demo variant
        if (DEVICE_DEMO_DICT[device]["isxWRLx432"]):
            self.gestureVersion = GESTURE_FD_DEMO
            self.gestureMode = 1 # 0 = presence mode, 1 = gesture mode
        elif (DEVICE_DEMO_DICT[device]["isxWRx843"]):
            self.gestureVersion = GESTURE_6843

        # # Init setup pane on left hand side
        statBox = self.initStatsPane()
        gridLayout.addWidget(statBox,2,0,1,1)
        # Init setup pane on left hand side
        demoGroupBox = self.initGestureInfoPane()
        gridLayout.addWidget(demoGroupBox,3,0,1,1)


        if (self.gestureVersion == GESTURE_6843):
            self.gestureList = GESTURE_6843_GESTURES
            # Probability and count thresholds for post processing of neural network outputs
            # [No Gesture, Gesture1, Gesture2, ...]
            self.probabilityThresholds = [0.99, 0.6, 0.6, 0.6, 0.6, 0.9, 0.9, 0.6, 0.6, 0.99]
            self.countThresholds = [4, 4, 4, 4, 4, 9, 9, 4, 4, 8]
            self.contGestureFramecount = 10
            self.sumProbs = [0] * len(self.gestureList) * GESTURE_FEATURE_LENGTH

        elif (self.gestureVersion == GESTURE_FD_DEMO):
            self.gestureList = GESTURE_FD_DEMO_GESTURES

        self.currFramegesture = -1
        self.prevFramegesture = -1
        self.lastFrameProcd = -1

        self.initGestureTab(demoTabs, device)

        if (self.firstTimeSetupDone == False):
            self.firstTimeSetupDone = True

    def initGestureTab(self, demoTabs, device):
        self.gestureTab = QWidget()
        
        if (DEVICE_DEMO_DICT[device]["isxWRLx432"]):
            gesturePaneLayout = QGridLayout()
            # Initialize the power pane and layout
            powerPane = QGroupBox("Power Plot")
            powerPaneLayout = QGridLayout()

            # Set up power usage plot
            self.plots['powerplot'] = pg.PlotWidget()
            self.plots['powerplot'].setMouseEnabled(False, False)
            self.plots['powerplot'].setTitle('Power Usage (mW)')
            self.plots['powerplot'].setBackground((70, 72, 79))
            self.plots['powerplot'].showGrid(x=True, y=True)
            self.plots['powerplot'].setXRange(0, 500, padding=0.001)
            self.plots['powerplot'].setYRange(0, 500, padding=0.001)

            # Set layout for the Power Pane
            powerPaneLayout.addWidget(self.plots['powerplot'], 0,0)
            powerPane.setLayout(powerPaneLayout)
            self.plots['powerPane'] = powerPane

            # Initialize the status pane and layout
            gestureStatusPane = QGroupBox("Status")
            gestureStatusPaneLayout = QVBoxLayout()

            # Setup gesture status box
            gestureBox = QVBoxLayout()
            self.plots['gestureStatus'] = QLabel(self.gestureList[0])
            self.plots['gestureStatus'].setAlignment(Qt.AlignCenter)
            self.plots['gestureStatus'].setStyleSheet('background-color: rgb(70, 72, 79); color: white; font-size: 60px; font-weight: bold')
            gestureBox.addWidget(self.plots['gestureStatus'],1)
            gestureStatusPaneLayout.addLayout(gestureBox)

            # Setup mode status box
            modeBox = QVBoxLayout()
            if (self.demoMode == 0):
                self.plots['modeStatus'] = QLabel("Gesture Mode")
                self.plots['modeStatus'].setStyleSheet('background-color: rgb(70, 72, 79); color: white; font-size: 60px; font-weight:bold')
            else:
                self.plots['modeStatus'] = QLabel("Send Configuration File")
                self.plots['modeStatus'].setStyleSheet('background-color: green; color: white; font-size: 60px; font-weight:bold')
            self.plots['modeStatus'].setAlignment(Qt.AlignCenter)

            modeBox.addWidget(self.plots['modeStatus'],2)
            gestureStatusPaneLayout.addLayout(modeBox)
            gestureStatusPane.setLayout(gestureStatusPaneLayout)
            self.plots['statusPane'] = gestureStatusPane

                # Initialize plot pane and layout
            dataPlotPane = QGroupBox("Data Plot")
            gesturePlotPaneLayout = QGridLayout()

            # Set up presence threshold plot
            self.plots['presenceplot'] = pg.PlotWidget()
            self.plots['presenceplot'].setXRange(0, 150, padding=0.001)
            self.plots['presenceplot'].setBackground((70, 72, 79))
            self.plots['presenceplot'].showGrid(x=True, y=True)
            self.plots['presenceplot'].setMouseEnabled(False, False)
            self.plots['presenceplot'].setTitle('Presence Magnitude')
            # ktoTempDict['presenceplot'].setFixedHeight(250)

            self.plots['dopplerplot'] = pg.PlotWidget()
            self.plots['dopplerplot'].setBackground((70, 72, 79))
            self.plots['dopplerplot'].showGrid(x=True, y=True)
            self.plots['dopplerplot'].setYRange(-15, 15)
            self.plots['dopplerplot'].setXRange(1, 30)
            self.plots['dopplerplot'].setMouseEnabled(False, False)
            self.plots['dopplerplot'].setTitle('Doppler Average')

            # Put the widgets into the layout
            gesturePlotPaneLayout.addWidget(self.plots['presenceplot'], 1,0)
            gesturePlotPaneLayout.addWidget(self.plots['dopplerplot'], 1,1)
            if(self.demoMode == 0):
                self.plots['presenceplot'].hide()
            else:
                self.plots['dopplerplot'].hide()
            dataPlotPane.setLayout(gesturePlotPaneLayout)
            self.plots['pane'] = dataPlotPane

            # Add all panes to the overall Gesture display
            gesturePaneLayout.addWidget(powerPane, 2,0)
            gesturePaneLayout.addWidget(gestureStatusPane, 0,0)
            gesturePaneLayout.addWidget(dataPlotPane, 1,0)

            self.gestureTab.setLayout(gesturePaneLayout)

        elif (DEVICE_DEMO_DICT[device]["isxWRx843"]):
            vboxGesture = QVBoxLayout()

            hboxOutput = QHBoxLayout()

            vBoxStatus = QVBoxLayout()

            vboxDetectedGesture = QVBoxLayout()
            self.gestureOutput = QLabel("Undefined")
            self.gestureOutput.setAlignment(Qt.AlignCenter)
            self.gestureOutput.setStyleSheet('background-color: rgb(70, 72, 79); color: white; font-size: 60px; font-weight: bold')
            font = QFont()
            font.setPointSize(int(self.gestureTab.width() / 20))
            self.gestureOutput.setFont(font)
            vboxDetectedGesture.addWidget(self.gestureOutput, 1)
            vBoxStatus.addLayout(vboxDetectedGesture)

            hboxOutput.addLayout(vBoxStatus, 35)
            vboxGesture.addLayout(hboxOutput, 35)

            self.gestureTab.setLayout(vboxGesture)

        self.gestureFontSize = '60px' 

        if (self.firstTimeSetupDone == False):
            self.gestureTimer = QTimer()
            self.gestureTimer.setInterval(1000)
            self.gestureTimer.timeout.connect(self.resetGestureDisplay)

        
        demoTabs.addTab(self.gestureTab, 'Gesture Recognition')
        demoTabs.setCurrentIndex(1)

    # Creates the info panel for teh gesture demo. Info panel has instructions about supported range, a figure depicting the physical setup and a list of supported gestures
    def initGestureInfoPane(self):
        self.gestureSetupBox = QGroupBox('Info')
        self.gestureSetupGrid = QGridLayout()
        self.gestureImgLabel = QLabel()
        instructionsLabel = QLabel()
        
        if (self.gestureVersion == GESTURE_6843):
            instructionsLabel.setText("Perform gestures at a range of 0.05-0.3m directly in front of the radar.")
        elif (self.gestureVersion == GESTURE_FD_DEMO):
            self.gestureSetupImg = QPixmap('images/xWRL6432_gesture_setup2.jpg')
            self.gestureImgLabel.setPixmap(self.gestureSetupImg)
            instructionsLabel.setText("Stand 2m away, directly in front of the radar.") 

        self.gestureSetupGrid.addWidget(self.gestureImgLabel, 1, 1)
        self.gestureSetupGrid.addWidget(instructionsLabel, 2, 1)
        self.gestureSetupBox.setLayout(self.gestureSetupGrid)

        return self.gestureSetupBox

    def initStatsPane(self):
        statBox = QGroupBox('Statistics')
        self.frameNumDisplay = QLabel('Frame: 0')
        self.plotTimeDisplay = QLabel('Plot Time: 0 ms')
        self.avgPower = QLabel('Average Power: 0 mw')
        self.statsLayout = QVBoxLayout()
        self.statsLayout.addWidget(self.frameNumDisplay)
        self.statsLayout.addWidget(self.plotTimeDisplay)
        self.statsLayout.addWidget(self.avgPower)
        statBox.setLayout(self.statsLayout)

        return statBox

    def resetGestureDisplay(self):
        if (DEVICE_DEMO_DICT[self.device]["isxWRLx432"]):
            # global ContGestureCnt
            self.ContGestureCnt = 0
            # presence mode
            if(self.gestureMode == GESTURE_PRESENCE_MODE_x432):
                self.plots['gestureStatus'].setStyleSheet(f'background-color: rgb(70, 72, 79); color: white; font-size: 60px; font-weight: bold')
                self.plots['gestureStatus'].setText('Searching for Presence')
            # gesture mode
            elif(self.gestureMode == GESTURE_GESTURE_MODE_x432):
                self.plots['gestureStatus'].setStyleSheet(f'background-color: rgb(70, 72, 79); color: white; font-size: 60px; font-weight: bold')
                self.plots['gestureStatus'].setText(self.gestureList[0])
            self.gestureTimer.stop()
        elif (DEVICE_DEMO_DICT[self.device]["isxWRx843"]):
            self.gestureOutput.setStyleSheet(f'background-color: rgb(70, 72, 79); color: white; font-size: {self.gestureFontSize}; font-weight: bold')
            self.gestureOutput.setText(self.gestureList[0])
            self.gestureTimer.stop()

    def gestureHandler(self, gesture):
        self.updateGestureDisplay(self.gestureList[gesture], gesture)
        # TODO: Add additional functionality based on detected gesture

    def updateGraph(self, outputDict):
        self.plotStart = int(round(time.time()*1000))

        gestureNeuralNetProb = None
        gestureFeatures = None
        gesture = None
        powerData = None
        gesturePresence = None
        presenceThresh = None

        # Frame number
        if ('frameNum' in outputDict):
            self.frameNum = outputDict['frameNum'] 
        if ('gesture' in outputDict):
            gesture = outputDict['gesture']
        if ('gestureNeuralNetProb' in outputDict):
            gestureNeuralNetProb = outputDict['gestureNeuralNetProb']
        if ('gestureFeatures' in outputDict):
            gestureFeatures = outputDict['gestureFeatures']  
        if ('powerData' in outputDict):
            powerData = outputDict['powerData'] 
        if ('gesturePresence' in outputDict):
            gesturePresence = outputDict['gesturePresence']
        if ('presenceThreshold' in outputDict):
            presenceThresh = outputDict['presenceThreshold']

        # Process gesture info
        if (gestureNeuralNetProb is not None and self.lastFrameProcd != self.frameNum):
            self.lastFrameProcd = self.frameNum
            gesture = self.gesturePostProc(gestureNeuralNetProb)
        elif (gesture is not None and gesture is not GESTURE_NO_GESTURE_6432):
            self.gestureHandler(gesture)

        # Process gesture/presence mode info
        if(gesturePresence is not None):
            self.gesturePresenceHandler(gesturePresence)

        # Process gesture features
        if(gestureFeatures is not None):
            self.updateGestureFeatures(gestureFeatures)

        # Presence Threshold info
        if (presenceThresh is not None):
            self.presenceThresholdHandler(presenceThresh)

        if(powerData is not None):
            # self.updatePowerNumbers(powerData)
            if (DEVICE_DEMO_DICT[self.device]["isxWRLx432"]):
                self.gesturePowerDataHandler(powerData)

        self.graphDone(outputDict)

    def graphDone(self, outputDict):
        if ('frameNum' in outputDict):
            self.frameNumDisplay.setText('Frame: ' + str(outputDict['frameNum']))

        plotTime = int(round(time.time()*1000)) - self.plotStart
        self.plotTimeDisplay.setText('Plot Time: ' + str(plotTime) + 'ms')
        self.plotComplete = 1    
    
    # TODO: Add when feature is supported in demo code
    def gesturePresenceHandler(self, gesturePresence):
        #if gesture/presence mode switched, 
        if(self.gestureMode != gesturePresence):
            if(gesturePresence==GESTURE_PRESENCE_MODE_x432):
                self.isOn = False
                self.plots['modeStatus'].setStyleSheet('background-color: green; color: white; font-size: 60px; font-weight:bold')
                self.plots['modeStatus'].setText("Low Power Mode")
                self.plots['presenceplot'].setVisible(True)
                # self.kto['presenceNote'].setVisible(True)
                self.frameDelayPresence = 0
                self.updateGestureDisplay('Searching for Presence', -1)
            elif(gesturePresence==GESTURE_GESTURE_MODE_x432):
                self.isOn = True
                self.frameDelayDoppler = 0
                self.plots['modeStatus'].setStyleSheet('background-color: rgb(70, 72, 79); color: white; font-size: 60px; font-weight:bold')
                self.plots['modeStatus'].setText("Gesture Mode")
                self.plots['dopplerplot'].setVisible(True)
                self.updateGestureDisplay(self.gestureList[0], -1)             
            self.gestureMode = gesturePresence

        if (self.isOn == True):
            self.frameDelayPresence+=1
        elif (self.isOn == False):
            self.frameDelayDoppler+=1

        if (self.isOn and self.frameDelayPresence > 80):
            # Delay the plot from disappearing for 80 frames to show the spike in presence
            self.plots['presenceplot'].setVisible(False)
            # self.kto['presenceNote'].hide()
            # self.isOn = False
        elif (not self.isOn and self.frameDelayDoppler > 2):
            self.plots['dopplerplot'].setVisible(False)
        #     self.isOn = True  

    def gesturePowerDataHandler(self, powerData):
        pen = pg.mkPen(color='r', width=2, style=Qt.SolidLine)

        powerStr = str((powerData['power1v2'] \
            + powerData['power1v2RF'] + powerData['power1v8'] + powerData['power3v3']) * 0.1)
        # self.plots['powerUsage'].setText(powerStr[:5] + ' mW')
        # Convert the value into an integer to be used in plotting
        # Definitely could have been done better
        powerval = ((powerData['power1v2'] \
            + powerData['power1v2RF'] + powerData['power1v8'] + powerData['power3v3']) * 0.1) 

        powData = deque(self.powerValues)
        powData.appendleft(powerval)

        if (len(powData) > 500):
            powData.pop()

        self.powerValues = powData

        self.plots['powerplot'].clear()
        self.plots['powerplot'].plot(self.powerValues, pen=pen)

        self.avgPower.setText('Average Power: ' + powerStr[:5] + ' mW')

    def updateGestureFeatures(self, features):
        if (DEVICE_DEMO_DICT[self.device]["isxWRLx432"]):

            pen = pg.mkPen(color='b', width=2, style=Qt.SolidLine)

            dopplerAvgData = deque(self.dopplerAvgVals)
            dopplerAvgData.appendleft(features[1])
            if (len(dopplerAvgData) > 40):
                dopplerAvgData.pop()

            self.dopplerAvgVals = dopplerAvgData

            self.plots['dopplerplot'].clear()
            self.plots['dopplerplot'].plot(self.dopplerAvgVals, pen=pen)
        else:
            pen = pg.mkPen(color='b', width=2, style=Qt.SolidLine)
            # Update doppler avg feature plot
            dopplerAvgData = deque(self.gesture_featureVals['dopplerAvgVals'])
            dopplerAvgData.appendleft(features[1]) # doppler avg feature is at index 1
            if (len(dopplerAvgData) > 40):
                dopplerAvgData.pop()
            self.gesture_featureVals['dopplerAvgVals'] = dopplerAvgData
            self.gesture_featurePlots['dopplerAvgPlot'].clear()
            self.gesture_featurePlots['dopplerAvgPlot'].plot(self.gesture_featureVals['dopplerAvgVals'], pen=pen)

            # Update range avg feature plot
            rangeAvgData = deque(self.gesture_featureVals['rangeAvgVals'])
            rangeAvgData.appendleft(features[0]) # range avg feature is at index 0
            if (len(rangeAvgData) > 40):
                rangeAvgData.pop()
            self.gesture_featureVals['rangeAvgVals'] = rangeAvgData
            self.gesture_featurePlots['rangeAvgPlot'].clear()
            self.gesture_featurePlots['rangeAvgPlot'].plot(self.gesture_featureVals['rangeAvgVals'], pen=pen)

            # Update num points feature plot
            numPointsData = deque(self.gesture_featureVals['numPointsVals'])
            numPointsData.appendleft(features[4]) # num points feature is at index 4
            if (len(numPointsData) > 40):
                numPointsData.pop()
            self.gesture_featureVals['numPointsVals'] = numPointsData
            self.gesture_featurePlots['numPointsPlot'].clear()
            self.gesture_featurePlots['numPointsPlot'].plot(self.gesture_featureVals['numPointsVals'], pen=pen)

    def presenceThresholdHandler(self, presenceThreshold):
        ref = float(self.presenceDetectCfg[2])
        refLine = pg.InfiniteLine(pen=pg.mkPen(color='r', style=Qt.DashLine, width=2), pos=ref, angle=0, label='Presence Threshold Value')
        pen = pg.mkPen(color='b', width=2, style=Qt.SolidLine)

        presData = deque(self.presenceThresh)
        # print(self.presenceThresh) # print out each value in the frame for 160 frames
        presData.appendleft(presenceThreshold)

        if (len(presData) > 160):
            presData.pop()
        
        self.presenceThresh = presData
        self.plots['presenceplot'].setYRange(0, float(self.presenceDetectCfg[2])*1.75, padding=0.001)
        self.plots['presenceplot'].clear()
        self.plots['presenceplot'].addItem(refLine) # Plot the presence threshold value as a red line
        self.plots['presenceplot'].plot(self.presenceThresh, pen=pen)

    # Perform post processing on the raw probabilities output by the neural network.
    # Uses a probabilities threshold and count threshold to determine if a gesture has occurred.
    def gesturePostProc(self, ann_probs):
        numOutputProbs = len(self.gestureList)

        i = 0
        j = 0
        confSum = 0

        # Shift the existing values
        for i in range(GESTURE_FEATURE_LENGTH * numOutputProbs - numOutputProbs):
            self.sumProbs[i] = self.sumProbs[i + numOutputProbs]

        #  Add the values for the current frame
        for i in range(numOutputProbs):
            if ann_probs[i] >= self.probabilityThresholds[i]:
                self.sumProbs[GESTURE_FEATURE_LENGTH * numOutputProbs - numOutputProbs + i] = 1
            else:
                self.sumProbs[GESTURE_FEATURE_LENGTH * numOutputProbs - numOutputProbs + i] = 0

        self.currFramegesture = 0

        for i in range(numOutputProbs):
            confSum = 0

            for j in range(GESTURE_FEATURE_LENGTH):
                confSum += self.sumProbs[j*numOutputProbs + i]

            # Sum must be larger than count threshold to be considered a gesture
            if confSum > self.countThresholds[i]:
                self.currFramegesture = i

        if self.prevFramegesture != self.currFramegesture:
            if self.currFramegesture != GESTURE_NO_GESTURE_6843:
                self.gestureHandler(self.currFramegesture)
        else:
            if self.frameNum % self.contGestureFramecount == 0 :
                if self.currFramegesture == GESTURE_CW_TWIRL_6843 or self.currFramegesture == GESTURE_CCW_TWIRL_6843 or self.currFramegesture == GESTURE_SHINE_6843:
                    self.gestureHandler(self.currFramegesture) 

        self.prevFramegesture = self.currFramegesture


    def updateGestureDisplay(self, text, gesture):
        if (DEVICE_DEMO_DICT[self.device]["isxWRLx432"]):
            # global ContGestureCnt

            if text == "Searching for Presence" or text == self.gestureList[0]:
                self.plots['gestureStatus'].setStyleSheet(f'background-color: rgb(70, 72, 79); color: white; font-size: 60px; font-weight: bold')
            else:
                self.plots['gestureStatus'].setStyleSheet(f'background-color: blue; color: white; font-size: 60px; font-weight: bold')
            self.plots['gestureStatus'].setText(text)
            self.gestureTimer.start()  
        else:
            self.gestureOutput.setStyleSheet(f'background-color: blue; color: white; font-size: {self.gestureFontSize}; font-weight: bold')
            self.gestureOutput.setText(text)
            self.gestureTimer.start()  



    def updateGestureDisplayText(self, gesture):
        self.gestureOutput.setStyleSheet(f'background-color: blue; color: white; font-size: {self.gestureFontSize}; font-weight: bold')
        self.gestureOutput.setText(self.gestureList[gesture])
        self.gestureTimer.start() 

    def parsePresenceDetectCfg(self, args):
        self.presenceDetectCfg = args

        # self.demoMode = int(args[1])

        if (self.demoMode != int(args[1])):
            self.demoMode = int(args[1])
            for _ in range(self.windowDemoTabs.count()):
                self.windowDemoTabs.removeTab(0)
            self.initGestureTab(self.windowDemoTabs, self.device)

    def parseSigProcChainCfg2(self, args):
        self.sigProcChainCfg2 = args


    def onChangeGestureVersion(self):
        self.gestureVersion = self.gestureVersionList.currentText()
        if (self.gestureVersion == GESTURE_FD_DEMO):
            self.gestureList = GESTURE_FD_DEMO_GESTURES