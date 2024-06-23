# General Library Imports
# PyQt Imports
# Local Imports
# Logger
# # Different methods to color the points 
COLOR_MODE_SNR = 'SNR'
COLOR_MODE_HEIGHT = 'Height'
COLOR_MODE_DOPPLER = 'Doppler'
COLOR_MODE_TRACK = 'Associated Track'

MAX_PERSISTENT_FRAMES = 30

from collections import deque
import numpy as np
import time
import string

from PyQt5.QtCore import Qt, QThread
from PyQt5.QtGui import QPixmap, QFont
import pyqtgraph.opengl as gl
import pyqtgraph as pg
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel, QWidget, QVBoxLayout, QTabWidget, QComboBox, QCheckBox, QSlider, QFormLayout, QGraphicsWidget

from Common_Tabs.plot_2d import Plot2D
from Common_Tabs.plot_1d import Plot1D
from Demo_Classes.Helper_Classes.fall_detection import *
from graph_utilities import get_trackColors, eulerRot
from gl_text import GLTextItem

from gui_threads import updateQTTargetThread3D
from gui_common import TAG_HISTORY_LEN

import logging

log = logging.getLogger(__name__)


class EBikes(Plot2D):
    def __init__(self):
        Plot2D.__init__(self)
        self.fallDetection = FallDetection()
        self.tabs = None
        self.cumulativeCloud = np.empty((0,5))
        self.colorGradient = pg.GradientWidget(orientation='right')
        self.colorGradient.restoreState({'ticks': [ (1, (255, 0, 0, 255)), (0, (131, 238, 255, 255))], 'mode': 'hsv'})
        self.colorGradient.setVisible(False)
        self.maxTracks = int(5) # default to 5 tracks
        self.trackColorMap = get_trackColors(self.maxTracks)

    def setupGUI(self, gridLayout, demoTabs, device):
        # Init setup pane on left hand side
        statBox = self.initStatsPane()
        gridLayout.addWidget(statBox,2,0,1,1)

        demoGroupBox = self.initPlotControlPane()
        gridLayout.addWidget(demoGroupBox,3,0,1,1)

        demoTabs.addTab(self.plot_2d, '2D Plot')

        self.tabs = demoTabs

    def updateGraph(self, outputDict):
        self.plotStart = int(round(time.time()*1000))
        self.updatePointCloud(outputDict)

        # Since track indexes are delayed a frame on the xWR6843 demo, delay showing the current points by 1 frame
        if ('frameNum' in outputDict and outputDict['frameNum'] > 1 and len(self.previousClouds[:-1]) > 0):
            self.cumulativeCloud = np.concatenate(self.previousClouds[:-1])
        elif (len(self.previousClouds) > 0):
            self.cumulativeCloud = np.concatenate(self.previousClouds)

        if ('numDetectedPoints' in outputDict):
            self.numPointsDisplay.setText('Points: '+ str(outputDict['numDetectedPoints']))
        if ('numDetectedTracks' in outputDict):
            self.numTargetsDisplay.setText('Targets: '+ str(outputDict['numDetectedTracks']))

        # Plot
        if (self.tabs.currentWidget() == self.plot_2d):
            if ('trackData' in outputDict):
                tracks = outputDict['trackData']
            else:
                tracks = None
            if (self.plotComplete):
                self.plotStart = int(round(time.time()*1000))
                for roi in self.ellipsoids:
                    roi.setPen(None)
                self.plotComplete = 0

        self.graphDone(outputDict)
        if ('frameNum' in outputDict):
            self.frameNumDisplay.setText('Frame: ' + str(outputDict['frameNum']))

    def graphDone(self, outputDict):
        if ('frameNum' in outputDict):
            self.frameNumDisplay.setText('Frame: ' + str(outputDict['frameNum']))

        plotTime = int(round(time.time()*1000)) - self.plotStart
        self.plotTimeDisplay.setText('Plot Time: ' + str(plotTime) + 'ms')
        self.plotComplete = 1
        self.scatter.setData(pos=self.cumulativeCloud[:, 0:2])
        if ('trackData' in outputDict):
            tracks = outputDict['trackData']
            for track in tracks:
                tid = int(track[0])
                x = track[1]
                y = track[2]
                track = self.ellipsoids[tid]
                track.setPos((x-2, y-2))
                track.setSize((4, 4), center=(x, y))
                track.setPen(pg.mkPen(color='r', width=2))

    def initStatsPane(self):
        statBox = QGroupBox('Statistics')
        self.frameNumDisplay = QLabel('Frame: 0')
        self.plotTimeDisplay = QLabel('Plot Time: 0 ms')
        self.numPointsDisplay = QLabel('Points: 0')
        self.numTargetsDisplay = QLabel('Targets: 0')
        self.avgPower = QLabel('Average Power: 0 mw')
        self.statsLayout = QVBoxLayout()
        self.statsLayout.addWidget(self.frameNumDisplay)
        self.statsLayout.addWidget(self.plotTimeDisplay)
        self.statsLayout.addWidget(self.numPointsDisplay)
        self.statsLayout.addWidget(self.numTargetsDisplay)
        self.statsLayout.addWidget(self.avgPower)
        statBox.setLayout(self.statsLayout)

        return statBox

    def initPlotControlPane(self):
        plotControlBox = QGroupBox('Plot Controls')
        self.pointColorMode = QComboBox()
        self.pointColorMode.addItems([COLOR_MODE_SNR, COLOR_MODE_HEIGHT, COLOR_MODE_DOPPLER, COLOR_MODE_TRACK])

        #self.displayFallDet = QCheckBox('Detect Falls')
        #self.displayFallDet.stateChanged.connect(self.fallDetDisplayChanged)
        self.persistentFramesInput = QComboBox()
        self.persistentFramesInput.addItems([str(i) for i in range(1, MAX_PERSISTENT_FRAMES + 1)])
        self.persistentFramesInput.setCurrentIndex(self.numPersistentFrames - 1)
        self.persistentFramesInput.currentIndexChanged.connect(self.persistentFramesChanged)
        plotControlLayout = QFormLayout()
        plotControlLayout.addRow("Color Points By:",self.pointColorMode)
        #plotControlLayout.addRow("Enable Fall Detection", self.displayFallDet)
        plotControlLayout.addRow("# of Persistent Frames",self.persistentFramesInput)
        plotControlBox.setLayout(plotControlLayout)

        return plotControlBox

    def persistentFramesChanged(self, index):
        self.numPersistentFrames = index + 1

    def parseTrackingCfg(self, args):
        self.maxTracks = int(args[4])
        self.updateNumTracksBuffer() # Update the max number of tracks based off the config file
        self.trackColorMap = get_trackColors(self.maxTracks)
        for m in range(self.maxTracks):
            # Add track gui object
            roi = pg.ROI((0,0), movable=False)
            self.ellipsoids.append(roi)
            self.scatter.getViewBox().addItem(roi)
            


    def updateNumTracksBuffer(self):
        # Use a deque here because the append operation adds items to the back and pops the front
        self.classifierTags = [deque([0] * TAG_HISTORY_LEN, maxlen = TAG_HISTORY_LEN) for i in range(self.maxTracks)]
        self.tracksIDsInPreviousFrame = []
        self.wasTargetHuman = [0 for i in range(self.maxTracks)]
        #self.fallDetection = FallDetection(self.maxTracks)

