# General Library Imports
from collections import deque
import time
import numpy as np

# PyQt Imports
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
import pyqtgraph as pg
from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel, QWidget, QVBoxLayout

# Local Imports

# Logger

class SurfaceClassification():
    def __init__(self):
        self.surfaceList = ['Not Grass', 'Grass']
        self.surfaceLatestResults = deque(100*[0], 100)
        self.currFrameClassification = -1
        self.plotStart = 0

    def setupGUI(self, gridLayout, demoTabs, device):
        # Init setup pane on left hand side
        statBox = self.initStatsPane()
        gridLayout.addWidget(statBox,2,0,1,1)

        # Init setup pane on left hand side
        demoGroupBox = self.initSurfacePhysicalSetupPane()
        gridLayout.addWidget(demoGroupBox,3,0,1,1)
        # gridLayout.replaceWidget(gridLayout.itemAt(3).widget(), demoGroupBox)

        self.surfaceTab = QWidget()
        vboxSurface = QVBoxLayout()

        vboxOutput = QGridLayout()
        self.surfaceOutput = QLabel("<b>Grass Classification</b><br>" + str(self.surfaceList[0]))
        self.surfaceOutput.setAlignment(Qt.AlignCenter)
        self.surfaceOutput.setStyleSheet('background-color: #46484f; color: white; font-size: 40px; font-weight: light')
        
        self.surfaceOutputRaw = QLabel("<b>Grass Probability</b><br>0.0%")
        self.surfaceOutputRaw.setAlignment(Qt.AlignCenter)
        self.surfaceOutputRaw.setStyleSheet('background-color: #46484f; color: white; font-size: 40px; font-weight: light')

        surfaceDescStr = """
        <p style="font-size: 30px"><b>Sensor Setup:</b></p><p style="font-size: 20px">18cm off the ground with 27 degree tilt off the vertical</p>
        <p style="font-size: 30px"><b>Model:       </b></p><p style="font-size: 20px">Sequential model trained on grass and large stone pavers</p>
        <p style="font-size: 30px"><b>More info:   </b></p><p style="font-size: 20px">See User Guide in the Radar Toolbox on dev.ti.com       </p>
        """
        self.surfaceDesc = QLabel(surfaceDescStr)
        self.surfaceDesc.setOpenExternalLinks(True)
        self.surfaceDesc.setAlignment(Qt.AlignLeft)
        self.surfaceDesc.setStyleSheet('background-color: white; color: black; font-size: 30px; font-weight: light')

        font = QFont()
        font.setPointSize(int(self.surfaceTab.width() / 20))
        self.surfaceOutput.setFont(font)
        self.surfaceOutputRaw.setFont(font)
        self.surfaceDesc.setFont(font)

        self.surfaceOutputRange = pg.PlotWidget()
        self.surfaceOutputRange.setBackground((70,72,79))
        self.surfaceOutputRange.showGrid(x=True,y=True,alpha=1)
        self.surfaceOutputRange.getAxis('bottom').setPen('w') 
        self.surfaceOutputRange.getAxis('left').setPen('w') 
        self.surfaceOutputRange.getAxis('right').setStyle(showValues=False) 
        self.surfaceOutputRange.hideAxis('top') 
        self.surfaceOutputRange.hideAxis('right') 
        self.surfaceOutputRange.setXRange(0,100,padding=0.00)
        self.surfaceOutputRange.setYRange(0,1,padding=0.00)
        self.surfaceOutputRange.setMouseEnabled(False,False)
        self.surfaceOutputRangeData = pg.PlotCurveItem(pen=pg.mkPen(width=3, color='b'))
        self.surfaceOutputRange.addItem(self.surfaceOutputRangeData)

        self.surfaceOutputRange.getPlotItem().setLabel('bottom', '<p style="font-size: 20px;color: white">Relative Frame # (0 is most recent)</p>')
        self.surfaceOutputRange.getPlotItem().setLabel('left', '<p style="font-size: 20px;color: white">Grass Probability Value</p>')
        self.surfaceOutputRange.getPlotItem().setLabel('right', ' ')
        self.surfaceOutputRange.getPlotItem().setTitle('<p style="font-size: 30px;color: white">Probability Value over Time</p>')

        self.surfaceOutputRange.getAxis('top').setStyle(tickTextOffset=150) 

        vboxOutput.addWidget(self.surfaceOutput, 0, 0, 1, 1)
        vboxOutput.addWidget(self.surfaceOutputRaw, 1, 0, 1, 1)
        vboxOutput.addWidget(self.surfaceDesc, 0, 1, 2, 1)
        vboxOutput.addWidget(self.surfaceOutputRange, 2, 0, 1, 2)
        #vboxOutput.setVerticalSpacing(0)
        vboxSurface.addLayout(vboxOutput)

        self.surfaceFontSize = '80px' 

        self.surfaceTab.setLayout(vboxSurface)
        demoTabs.addTab(self.surfaceTab, 'Surface Classification')
        demoTabs.setCurrentIndex(1)

    def initSurfacePhysicalSetupPane(self):
        self.surfaceSetupBox = QGroupBox('Physical Setup')

        self.gestureSetupGrid = QGridLayout()
        self.gestureSetupImg = QPixmap('./images/surface_setup.png')
        self.gestureImgLabel = QLabel()
        self.gestureImgLabel.setPixmap(self.gestureSetupImg)
        self.gestureSetupGrid.addWidget(self.gestureImgLabel, 1, 1)

        self.surfaceSetupBox.setLayout(self.gestureSetupGrid)

        return self.surfaceSetupBox

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

        if ('surfaceClassificationOutput' in outputDict) :
            classification = outputDict['surfaceClassificationOutput']
            self.surfaceLatestResults.appendleft(classification)

            # Simply take a weighted rolling average of the last 5 frames of data, customers should create a more robust algorithm
            currentClassification = np.average(list(self.surfaceLatestResults)[0:5], weights=[5, 4, 3, 2, 1])
            self.surfaceOutputRangeData.setData(np.arange(0, 100), list(self.surfaceLatestResults))

            # grass > 0.5, not grass <= 0.5
            if (currentClassification > 0.5) :
                self.surfaceOutput.setText("<b>Grass Classification</b><br>" + str(self.surfaceList[1]))
                self.surfaceOutput.setStyleSheet('background-color: green; color: white; font-size: 40px; font-weight: light')
                self.surfaceOutputRaw.setStyleSheet('background-color: green; color: white; font-size: 40px; font-weight: light')
            else :
                self.surfaceOutput.setText("<b>Grass Classification</b><br>" + str(self.surfaceList[0]))
                self.surfaceOutput.setStyleSheet('background-color: #46484f; color: white; font-size: 40px; font-weight: light')
                self.surfaceOutputRaw.setStyleSheet('background-color: #46484f; color: white; font-size: 40px; font-weight: light')
            
            self.surfaceOutputRaw.setText("<b>Grass Classification Value</b><br>" + "{:8.5f}".format(classification * 100) + "%")

        self.graphDone(outputDict)

    def graphDone(self, outputDict):
        plotTime = int(round(time.time()*1000)) - self.plotStart
        self.plotTimeDisplay.setText('Plot Time: ' + str(plotTime) + 'ms')
        self.plotComplete = 1

        if ('frameNum' in outputDict):
            self.frameNumDisplay.setText('Frame: ' + str(outputDict['frameNum']))

        if ('numDetectedPoints' in outputDict):
            self.numPointsDisplay.setText('Points: ' + str(outputDict['numDetectedPoints']))
