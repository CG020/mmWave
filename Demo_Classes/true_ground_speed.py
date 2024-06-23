# General Library Imports
from collections import deque

# PyQt Imports
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import pyqtgraph as pg
from PyQt5.QtWidgets import QGroupBox, QLabel, QWidget, QVBoxLayout, QTabWidget

# Local Imports

# Logger

class TrueGroundSpeed():
    def __init__(self):
        self.speedPlots = {}
        self.speedVals = {'speedVals': []}

    def setupGUI(self, gridLayout, demoTabs, device):
        # Init setup pane on left hand side
        statBox = self.initStatsPane()
        gridLayout.addWidget(statBox,2,0,1,1)

        self.groundSpeedTab = QWidget()
        vboxGroundSpeed = QVBoxLayout()

        vboxDetectedSpeed = QVBoxLayout()
        vboxDetectedSpeedMph = QVBoxLayout()
        self.speedOutput = QLabel("Undefined")
        self.speedOutputMph = QLabel("Undefined")
        self.speedOutput.setAlignment(Qt.AlignCenter)
        self.speedOutputMph.setAlignment(Qt.AlignCenter)
        self.speedOutput.setStyleSheet('background-color: rgb(70, 72, 79); color: white; font-size: 60px; font-weight: bold')
        self.speedOutputMph.setStyleSheet('background-color: rgb(70, 72, 79); color: white; font-size: 60px; font-weight: bold')
        font = QFont()
        font.setPointSize(int(self.groundSpeedTab.width() / 20))
        self.speedOutput.setFont(font)
        self.speedOutputMph.setFont(font)
        vboxDetectedSpeed.addWidget(self.speedOutput, 1)
        vboxDetectedSpeedMph.addWidget(self.speedOutputMph, 1)
        vboxGroundSpeed.addLayout(vboxDetectedSpeed)
        vboxGroundSpeed.addLayout(vboxDetectedSpeedMph)

        vBoxFeatures = QVBoxLayout()
        pen = pg.mkPen(color='b', width=2, style=Qt.SolidLine)
        self.speedPlots['avgSpeedPlot'] = pg.PlotWidget()
        self.speedPlots['avgSpeedPlot'].setBackground((70, 72, 79))
        self.speedPlots['avgSpeedPlot'].showGrid(x=True, y=True)
        self.speedPlots['avgSpeedPlot'].setYRange(-7, 7)
        self.speedPlots['avgSpeedPlot'].setXRange(1, 30)
        self.speedPlots['avgSpeedPlot'].setTitle('True Ground Speed')
        self.speedPlots['avgSpeedPlot'].plot(self.speedVals['speedVals'], pen=pen)
        vBoxFeatures.addWidget(self.speedPlots['avgSpeedPlot'])

        vboxGroundSpeed.addLayout(vBoxFeatures)
        self.groundSpeedTab.setLayout(vboxGroundSpeed)

        demoTabs.addTab(self.groundSpeedTab, 'True Ground Speed')
        demoTabs.setCurrentIndex(1)

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

    def updateGraph(self, outputDict):
        pen = pg.mkPen(color='b', width=2, style=Qt.SolidLine)
        speedData = deque(self.speedVals['speedVals'])
        if ('velocity' in outputDict):
            # get velocity
            velocity = outputDict['velocity'][0][0]

            # update the plot
            speedData.appendleft(velocity) # doppler avg feature is at index 1
            if (len(speedData) > 40):
                speedData.pop()
            self.speedVals['speedVals'] = speedData
            self.speedPlots['avgSpeedPlot'].clear()
            self.speedPlots['avgSpeedPlot'].plot(self.speedVals['speedVals'], pen=pen)

            # update text
            self.speedOutput.setStyleSheet(f'background-color: blue; color: white; font-weight: bold')
            self.speedOutput.setText("{0:.2f} m/s".format(velocity))
            
            self.speedOutputMph.setStyleSheet(f'background-color: blue; color: white; font-weight: bold')
            self.speedOutputMph.setText("{0:.2f} mph".format(velocity * 2.237))