# General Library Imports
import copy
import string
import math
import time
from os import path

# PyQt Imports
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QVector3D, QDoubleValidator
import pyqtgraph.opengl as gl
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel, QVBoxLayout, QLineEdit, QGridLayout
import numpy as np

# Local Imports
from Demo_Classes.people_tracking import PeopleTracking
from gui_common import NUM_CLASSES_IN_CLASSIFIER, TAG_HISTORY_LEN, CLASSIFIER_CONFIDENCE_SCORE, MIN_CLASSIFICATION_VELOCITY, TAG_HISTORY_LEN, MAX_NUM_UNKNOWN_TAGS_FOR_HUMAN_DETECTION

# Logger
import logging
log = logging.getLogger(__name__)

# images for REC and NOT REC
recImgPath = path.normpath("images/recImg.jpg")
notRecImgPath = path.normpath("images/notRecImg.jpg")

class Dashcam(PeopleTracking):
    def __init__(self):
        PeopleTracking.__init__(self)

        # default to white tracks
        self.trackColorMap = [(1,1,1,1)] * self.maxTracks

        # 10 is the direction buffer size.

        # at a framerate of 100 ms, it takes 1s of average forward motion to turn the camera on

        # not the cleanest initialization, but the commented line below has initialization issues
        # self.trackDirection = [[1,1,1,1,1,1,1,1,1,1,1]] * self.maxTracks
        self.trackDirection = [[1,1,1,1,1,1,1,1],
                               [1,1,1,1,1,1,1,1],
                               [1,1,1,1,1,1,1,1],
                               [1,1,1,1,1,1,1,1],
                               [1,1,1,1,1,1,1,1]]

        self.camRecording = False
        self.camLastOnTimestamp = 0
        self.cameraTimeoutValue = 5
        self.noTLVWarning = False

    # overrides setupGUI for people tracking so we can add camera stuff
    def setupGUI(self, gridLayout, demoTabs, device):
        # Init setup pane on left hand side
        statBox = self.initStatsPane()
        gridLayout.addWidget(statBox,2,0,1,1)

        demoGroupBox = self.initPlotControlPane()
        gridLayout.addWidget(demoGroupBox,3,0,1,1)

        fallDetectionOptionsBox = self.initFallDetectPane()
        gridLayout.addWidget(fallDetectionOptionsBox, 4,0,1,1)
        dashcamBox = self.initDashcamGUI()
        gridLayout.addWidget(dashcamBox, 5,0,1,1)

        demoTabs.addTab(self.plot_3d, '3D Plot')
        #demoTabs.addTab(self.rangePlot, 'Range Plot')
        self.tabs = demoTabs

        # draw lines for the FOV of the DC
        # 17/2 and 10/2 gives us a 120 degree FOV
        xx = 0
        yx = 0 
        zx = 0

        xy = 17/2
        yy = 10/2
        zy = 0

        xz = -17/2
        yz = 10/2
        zz = 0

        Xdot = (xx, yx, zx)
        Ydot = (xy, yy, zy)
        Zdot = (xz, yz, zz)

        ptsY = np.array([Xdot, Ydot])
        ptsZ = np.array([Xdot, Zdot])
        lineY = gl.GLLinePlotItem(pos=ptsY, width=1, antialias=False)
        lineZ = gl.GLLinePlotItem(pos=ptsZ, width=1, antialias=False)

        gz = gl.GLGridItem()
        gz.setSize(20,40,20)
        self.plot_3d.addItem(gz)

        self.plot_3d.addItem(lineY)
        self.plot_3d.addItem(lineZ)


        # setting camera to be in a good position for the dashcam demo
        self.plot_3d.setCameraPosition(pos=QVector3D(0,0,0),distance=26,elevation=90,azimuth=0)
        self.plot_3d.pan(0,7,0)

    def initDashcamGUI(self):
        # create small box that notifies users if the camera is on or off
        cameraBox = QGroupBox("Video Camera Status")
        self.cameraLayout = QVBoxLayout()
        # set to picture of camera not recording
        self.cameraStatusDisplay = QLabel("camera off")

        self.cameraTimeoutValueBox  = QLineEdit("5.0")

        # force us to only use double values less than 120
        self.cameraTimeoutValueBox.setValidator(QDoubleValidator(0,120,3,notation=QDoubleValidator.StandardNotation))
        self.cameraTimeoutValueBox.editingFinished.connect(self.onCamTimeoutEdit)

        self.cameraStatusDisplay.setAlignment(Qt.AlignCenter)
        self.cameraStatusDisplay.setPixmap(QPixmap(notRecImgPath))

        self.cameraLayout = QGridLayout()
        self.cameraLayout.addWidget(QLabel("Camera Timeout (seconds)"), 0, 0)
        self.cameraLayout.addWidget(self.cameraTimeoutValueBox, 0, 1)
        self.cameraLayout.addWidget(self.cameraStatusDisplay, 1, 0, 2, Qt.AlignHCenter)

        cameraBox.setLayout(self.cameraLayout)
        return cameraBox

    def onCamTimeoutEdit(self):
        # you can change the length of time the camera stays on through this method
        self.cameraTimeoutValue = float(self.cameraTimeoutValueBox.text())

    def updateGraph(self, outputDict):
        # if we have a track data...
        if "trackData" in outputDict:
            tracks = outputDict["trackData"]

            # default track color is white
            self.trackColorMap = [(1,1,1,1)] * self.maxTracks

            for trackNum, trackData in enumerate(tracks):

                trackID = int(trackData[0])

                if "camDataDict" in outputDict:
                    camData = outputDict["camDataDict"]
                    # trackId[1] = moving towards cam 
                    # trackId[3] = within instant trigger range

                    #if(camData[trackID][1] or camData[trackID][3]):
                    if(camData[trackID][1] == 1 or camData[trackID][3] == 1): 
                        self.trackColorMap[trackID] = (230/255, 25/255, 75/255, 255/255)
                        self.camRecording = True
                        self.cameraStatusDisplay.setPixmap(QPixmap(recImgPath))
                        self.camLastOnTimestamp = int(round(time.time()*1000))

                    # trackId[2] = within monitoring range
                    elif (camData[trackID][2] == 1):
                        self.trackColorMap[trackID] = (255/255, 255/255, 25/255, 255/255)

                    else:
                        # green, outside of detection range 
                        self.trackColorMap[trackID] = (60/255, 180/255, 75/255, 255/255)


                    """
                    self.classifierStr[trackID].setText("Track %s: Distance: %s"  % (trackID, trackData[2]))
                    self.classifierStr[trackID].setX(trackData[1])
                    self.classifierStr[trackID].setY(trackData[2] + 0.5)
                    self.classifierStr[trackID].setZ(trackData[3] + 0.1) # Add 0.1 so it doesn't interfere with height text if enabled

                    self.classifierStr[trackID].setVisible(True)
                    """

                else:
                    if not self.noTLVWarning:
                        log.warning("WARNING: Dashcam TLV not found: are you using the correct dashcam .appimage for your device?")
                        self.noTLVWarning = True

                    # NOTE:
                    # this code block runs the camera trigger logic on the visualizer
                    # it can be re-enabled by un-commenting this section
                    # trackData[2] = y distance
                    # trackData[5] = y velocity

                    # if we're within 15 meters of the camera (y direction)
                    """
                    if trackData[2] < 15:

                        # person's track is red if we've consistently been moving towards cam
                        if (trackData[5] < -0.15):
                            if(sum(self.trackDirection[trackID]) < 0):
                                self.trackColorMap[trackID] = (230/255, 25/255, 75/255, 255/255)
                                self.camRecording = True
                                self.cameraStatusDisplay.setPixmap(QPixmap(recImgPath))
                                self.camLastOnTimestamp = int(round(time.time()*1000))

                            # note that this process is framerate dependent
                            self.trackDirection[trackID].append(-1)

                        # person's track is yellow if we've consistently been moving away from cam
                        elif (trackData[5] > 0.15):
                            if(sum(self.trackDirection[trackID]) > 0):
                                self.trackColorMap[trackID] = (255/255, 255/255, 25/255, 255/255)

                            # decrease buffer                            
                            self.trackDirection[trackID].append(1)

                        # no major movement
                        else:
                            # build up buffer to create "static friction"
                            self.trackDirection[trackID].append(2)
                            self.trackColorMap[trackID] = (1,1,1,1)

                        # keep FIFO the same size by popping out old value
                        self.trackDirection[trackID].pop(0)
                    else:
                        # green, outside of detection range 
                        self.trackColorMap[trackID] = (60/255, 180/255, 75/255, 255/255)

                    if True:
                        # best way to implement a debug mode here?

                        for cstr in self.classifierStr:
                            cstr.setVisible(False)


                    #this sets text over a track listing it's velocity.
                    
                    trackVelocity = (trackData[1] * trackData[4] + trackData[2] * trackData[5] + trackData[3] * trackData[6]) \
                    / math.sqrt(math.pow(trackData[1], 2) + math.pow(trackData[2], 2) + math.pow(trackData[3], 2))

                    distance =  math.sqrt(trackData[2]**2 + trackData[1]**2 )
                    angle = abs(math.tan(trackData[1]/trackData[2]) * 180 / 3.14159)

                    # set track name to velocity relative to sensor
                    self.classifierStr[trackID].setText("Track %s: buf %s: yval %s"  % (trackID, str(sum(self.trackDirection[trackID])),trackData[5]))
                    self.classifierStr[trackID].setX(trackData[1])
                    self.classifierStr[trackID].setY(trackData[2] + 0.5)
                    self.classifierStr[trackID].setZ(trackData[3] + 0.1) # Add 0.1 so it doesn't interfere with height text if enabled

                    self.classifierStr[trackID].setVisible(True)
                    """

        # if no one is moving towards camera in 5 seconds, turn off camera
        if self.camRecording and (int(round(time.time()*1000)) - self.camLastOnTimestamp > self.cameraTimeoutValue * 1000):
            self.cameraStatusDisplay.setPixmap(QPixmap(notRecImgPath))
            self.camRecording = False

        PeopleTracking.updateGraph(self, outputDict)
