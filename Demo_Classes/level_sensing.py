# General Library Imports
import time
import numpy as np

# PyQt Imports
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import pyqtgraph as pg
from PyQt5.QtWidgets import QGroupBox, QHBoxLayout, QLabel, QWidget, QVBoxLayout

# Local Imports
from Common_Tabs.plot_1d import Plot1D

# Logger

class LevelSensing(Plot1D):
    def __init__(self):
        Plot1D.__init__(self)   

        self.Peak1 = 0
        self.Peak2 = 0
        self.Peak3 = 0
        self.Peak1Magnitude = 0
        self.Peak2Magnitude = 0
        self.Peak3Magnitude = 0
        self.peakValues = []

    def updateLevelSensingPeaks(self):
        comment1 = "Object 1 in meters : "
        label_text1 = f"{self.Peak1}"
        self.PeakListOutput1.setText(label_text1)        
        
        comment2 = "Object 2 in meters : "
        label_text2 = f"{self.Peak2}"
        self.PeakListOutput2.setText(label_text2)    
        
        comment3 = "Object 3 in meters : "
        label_text3 = f"{self.Peak3}"
        self.PeakListOutput3.setText(label_text3)
        
        comment1 = "Object 1 power in dB : "
        label_text1 = f"{self.Peak1Magnitude}"
        self.PeakMagnitudeOutput1.setText(label_text1)        
        
        comment2 = "Object 2 power in dB : "
        label_text2 = f"{self.Peak2Magnitude}"
        self.PeakMagnitudeOutput2.setText(label_text2)    
        
        comment3 = "Object 3 power in dB : "
        label_text3 = f"{self.Peak3Magnitude}"
        self.PeakMagnitudeOutput3.setText(label_text3)
        
    def updateLevelSensingPower(self, powerData):
        llPower = (powerData['power1v2'] \
            + powerData['power1v2RF'] + powerData['power1v8'] + powerData['power3v3']) * 0.1
        if( powerData['power1v2'] == 65535 ):
           llPower = 0
        else:
           llPower = round(llPower, 2)
  
        power_comment = "Power in mW: "
        power_label = f"{power_comment}{llPower}"
        self.PowerOutput.setText(power_label)
    
    def setupGUI(self, gridLayout, demoTabs, device):
        # Init setup pane on left hand side
        statBox = self.initStatsPane()
        gridLayout.addWidget(statBox,2,0,1,1)

        self.levelsensingTab = QWidget()
        
        vboxLevelSense = QVBoxLayout()
        vboxTop = QHBoxLayout()
        vboxBottom = QHBoxLayout()
        
        vboxRangeProfile = QVBoxLayout()
        self.vboxPeakList = QVBoxLayout()
        self.vboxPeakMagnitude = QVBoxLayout()
        self.vboxObjectNo = QVBoxLayout()
        
        comment1 = "Peak No" 
        label_text1 = f"{comment1}"
        self.ObjectNo = QLabel(label_text1)
        self.ObjectNo.setAlignment(Qt.AlignCenter)
        self.ObjectNo.setStyleSheet('background-color: teal; color: white; font-size: 30px; font-weight: bold')
        font = QFont()
        font.setPointSize(int(self.levelsensingTab.width() / 15))
        self.ObjectNo.setFont(font)
        self.vboxObjectNo.addWidget(self.ObjectNo, 1)
        
        comment1 = "1" 
        label_text1 = f"{comment1}"
        self.ObjectNo1 = QLabel(label_text1)
        self.ObjectNo1.setAlignment(Qt.AlignCenter)
        self.ObjectNo1.setStyleSheet('background-color: teal; color: white; font-size: 30px; font-weight: bold')
        font = QFont()
        font.setPointSize(int(self.levelsensingTab.width() / 15))
        self.ObjectNo1.setFont(font)
        self.vboxObjectNo.addWidget(self.ObjectNo1, 1)

        comment2 = "2"
        label_text2 = f"{comment2}"
        self.ObjectNo2 = QLabel(label_text2)
        self.ObjectNo2.setAlignment(Qt.AlignCenter)
        self.ObjectNo2.setStyleSheet('background-color: teal; color: white; font-size: 30px; font-weight: bold')
        font = QFont()
        font.setPointSize(int(self.levelsensingTab.width() / 15))
        self.ObjectNo2.setFont(font)
        self.vboxObjectNo.addWidget(self.ObjectNo2, 1)
        
        comment3 = "3"
        label_text3 = f"{comment3}"
        self.ObjectNo3 = QLabel(label_text3)
        self.ObjectNo3.setAlignment(Qt.AlignCenter)
        self.ObjectNo3.setStyleSheet('background-color: teal; color: white; font-size: 30px; font-weight: bold')
        font = QFont()
        font.setPointSize(int(self.levelsensingTab.width() / 15))
        self.ObjectNo3.setFont(font)
        self.vboxObjectNo.addWidget(self.ObjectNo3, 1)
        
        comment1 = "Distance in meters" 
        label_text1 = f"{comment1}"
        self.PeakListOutput = QLabel(label_text1)
        self.PeakListOutput.setAlignment(Qt.AlignCenter)
        self.PeakListOutput.setStyleSheet('background-color: teal; color: white; font-size: 30px; font-weight: bold')
        font = QFont()
        font.setPointSize(int(self.levelsensingTab.width() / 15))
        self.PeakListOutput.setFont(font)
        self.vboxPeakList.addWidget(self.PeakListOutput, 1)
        
        comment1 = "Object 1 in meters : " 
        label_text1 = f"{self.Peak1}"
        self.PeakListOutput1 = QLabel(label_text1)
        self.PeakListOutput1.setAlignment(Qt.AlignCenter)
        self.PeakListOutput1.setStyleSheet('background-color: teal; color: white; font-size: 30px; font-weight: bold')
        font = QFont()
        font.setPointSize(int(self.levelsensingTab.width() / 15))
        self.PeakListOutput1.setFont(font)
        self.vboxPeakList.addWidget(self.PeakListOutput1, 1)

        comment2 = "Object 2 in meters : "
        label_text2 = f"{self.Peak2}"
        self.PeakListOutput2 = QLabel(label_text2)
        self.PeakListOutput2.setAlignment(Qt.AlignCenter)
        self.PeakListOutput2.setStyleSheet('background-color: teal; color: white; font-size: 30px; font-weight: bold')
        font = QFont()
        font.setPointSize(int(self.levelsensingTab.width() / 15))
        self.PeakListOutput2.setFont(font)
        self.vboxPeakList.addWidget(self.PeakListOutput2, 1)
        
        comment3 = "Object 3 in meters : "
        label_text3 = f"{self.Peak3}"
        self.PeakListOutput3 = QLabel(label_text3)
        self.PeakListOutput3.setAlignment(Qt.AlignCenter)
        self.PeakListOutput3.setStyleSheet('background-color: teal; color: white; font-size: 30px; font-weight: bold')
        font = QFont()
        font.setPointSize(int(self.levelsensingTab.width() / 15))
        self.PeakListOutput3.setFont(font)
        self.vboxPeakList.addWidget(self.PeakListOutput3, 1)
        
        comment1 = "Power in dB" 
        label_text = f"{comment1}"
        self.PeakMagnitudeOutput = QLabel(label_text)
        self.PeakMagnitudeOutput.setAlignment(Qt.AlignCenter)
        self.PeakMagnitudeOutput.setStyleSheet('background-color: teal; color: white; font-size: 30px; font-weight: bold')
        font = QFont()
        font.setPointSize(int(self.levelsensingTab.width() / 15))
        self.PeakMagnitudeOutput.setFont(font)
        self.vboxPeakMagnitude.addWidget(self.PeakMagnitudeOutput, 1)        
                
        comment1 = "Object 1 power in dB: " 
        label_text1 = f"{self.Peak1Magnitude}"
        self.PeakMagnitudeOutput1 = QLabel(label_text1)
        self.PeakMagnitudeOutput1.setAlignment(Qt.AlignCenter)
        self.PeakMagnitudeOutput1.setStyleSheet('background-color: teal; color: white; font-size: 30px; font-weight: bold')
        font = QFont()
        font.setPointSize(int(self.levelsensingTab.width() / 15))
        self.PeakMagnitudeOutput1.setFont(font)
        self.vboxPeakMagnitude.addWidget(self.PeakMagnitudeOutput1, 1)

        comment2 = "Object 2 power in dB: "
        label_text2 = f"{self.Peak2Magnitude}"
        self.PeakMagnitudeOutput2 = QLabel(label_text2)
        self.PeakMagnitudeOutput2.setAlignment(Qt.AlignCenter)
        self.PeakMagnitudeOutput2.setStyleSheet('background-color: teal; color: white; font-size: 30px; font-weight: bold')
        font = QFont()
        font.setPointSize(int(self.levelsensingTab.width() / 15))
        self.PeakMagnitudeOutput2.setFont(font)
        self.vboxPeakMagnitude.addWidget(self.PeakMagnitudeOutput2, 1)
        
        comment3 = "Object 3 power in dB: "
        label_text3 = f"{self.Peak3Magnitude}"
        self.PeakMagnitudeOutput3 = QLabel(label_text3)
        self.PeakMagnitudeOutput3.setAlignment(Qt.AlignCenter)
        self.PeakMagnitudeOutput3.setStyleSheet('background-color: teal; color: white; font-size: 30px; font-weight: bold')
        font = QFont()
        font.setPointSize(int(self.levelsensingTab.width() / 15))
        self.PeakMagnitudeOutput3.setFont(font)
        self.vboxPeakMagnitude.addWidget(self.PeakMagnitudeOutput3, 1)
        
        self.HighlightPlotPeak1 = pg.ScatterPlotItem(pen=None, size=10, brush=pg.mkBrush('b'))
        self.HighlightPlotPeak2 = pg.ScatterPlotItem(pen=None, size=10, brush=pg.mkBrush('g'))
        self.HighlightPlotPeak3 = pg.ScatterPlotItem(pen=None, size=10, brush=pg.mkBrush('m'))
        self.rangePlot.addItem(self.HighlightPlotPeak1)
        self.rangePlot.addItem(self.HighlightPlotPeak2)
        self.rangePlot.addItem(self.HighlightPlotPeak3)
        
        self.peakLabel1 = pg.TextItem(f'1', anchor=(0.05, 1), color='b')
        self.peakLabel2 = pg.TextItem(f'2', anchor=(0.05, 1), color='g')
        self.peakLabel3 = pg.TextItem(f'3', anchor=(0.05, 1), color='m')
        self.rangePlot.addItem(self.peakLabel1)
        self.rangePlot.addItem(self.peakLabel2)
        self.rangePlot.addItem(self.peakLabel3)
        
        vboxRangeProfile.addWidget(self.rangePlot)
        
        vboxPower = QVBoxLayout()
        llPower = 0
        power_comment = "Power in mW: "
        power_label = f"{power_comment}{llPower}"
        self.PowerOutput = QLabel(power_label)
        self.PowerOutput.setAlignment(Qt.AlignCenter)
        self.PowerOutput.setStyleSheet('background-color: teal; color: white; font-size: 25px; font-weight: bold')
        font = QFont()
        font.setPointSize(int(self.levelsensingTab.width() / 15))
        self.PowerOutput.setFont(font)
        vboxPower.addWidget(self.PowerOutput, 1)
        
        vboxNote = QVBoxLayout()
        noteLabel = QLabel("Note : Peaks are ordered based on their relative power. Peak with the highest relative power is designated as Peak 1")
        font = QFont("Arial", 8)
        noteLabel.setFont(font)
        vboxNote.addWidget(noteLabel)        
     
        vboxGraphics = QVBoxLayout()
        peak_barGraph = pg.BarGraphItem(x = [1, 2, 3], height = [0, 0, 0], width = 0.1, brush = 'g')
       
        self.peakScatterPlot = pg.PlotWidget()
        self.peakScatterPlot.setBackground('w')
        self.peakScatterPlot.showGrid(x=True,y=True)
        self.peakScatterPlot.setXRange(0,1000)
        self.peakScatterPlot.setYRange(0,20,padding=0.01)
        self.peakScatterPlot.setMouseEnabled(False,False)
        self.peakScatterPlot.getPlotItem().setLabel('bottom', 'Frame Number')
        self.peakScatterPlot.getPlotItem().setLabel('left', 'Distance in Meters')
        self.peakScatterPlot.getPlotItem().setLabel('top', 'Peak Movement over time')
        
        vboxGraphics.addWidget(self.peakScatterPlot)
        vboxTop.addLayout(vboxRangeProfile)
        
        vboxBottom.addLayout(self.vboxObjectNo)
        vboxBottom.addLayout(self.vboxPeakList)
        vboxBottom.addLayout(self.vboxPeakMagnitude)
               
        vboxLevelSense.addLayout(vboxTop)
        vboxLevelSense.addLayout(vboxBottom)
        vboxLevelSense.addLayout(vboxPower)
        vboxLevelSense.addLayout(vboxNote)
        self.levelsensingTab.setLayout(vboxLevelSense)   

        self.levelsensingTab.setLayout(vboxLevelSense)
        demoTabs.addTab(self.levelsensingTab, 'Level Sensing')
        demoTabs.setCurrentIndex(1)

    def initStatsPane(self):
        statBox = QGroupBox('Statistics')
        self.frameNumDisplay = QLabel('Frame: 0')
        self.plotTimeDisplay = QLabel('Plot Time: 0 ms')
        self.numPointsDisplay = QLabel('Points: 0')
        self.statsLayout = QVBoxLayout()
        self.statsLayout.addWidget(self.frameNumDisplay)
        self.statsLayout.addWidget(self.plotTimeDisplay)
        self.statsLayout.addWidget(self.numPointsDisplay)
        statBox.setLayout(self.statsLayout)

        return statBox

    def updateGraph(self, outputDict):
        self.plotStart = int(round(time.time()*1000))
        self.update1DGraph(outputDict)
        pointCloud = None
        numPoints = None
        if ('pointCloud' in outputDict):
            pointCloud = outputDict['pointCloud']
        if ('numDetectedPoints' in outputDict):
            numPoints = outputDict['numDetectedPoints']
        if (pointCloud is not None and numPoints is not None):
            for i in range(numPoints):
                if(i == 0):
                    self.Peak1 = round(pointCloud[i, 1], 3)
                    self.Peak1Magnitude = round(np.log10(round((pointCloud[i, 4]*64), 4)+1)*20, 1)
                    #print ( f'Peak 1 Magnitude (${round(pointCloud[i, 4], 4)})')
                elif (i == 1):
                    self.Peak2 = round(pointCloud[i, 1], 3)
                    self.Peak2Magnitude = round(np.log10((round((pointCloud[i, 4]*64), 4)+1))*20, 1)
                    #print ( f'Peak 2 Magnitude (${round(pointCloud[i, 4], 4)})')
                elif (i == 2):
                    self.Peak3 = round(pointCloud[i, 1], 3)
                    self.Peak3Magnitude = round(np.log10((round((pointCloud[i, 4]*64), 4)+1))*20, 1)
                    #print ( f'Peak 3 Magnitude (${round(pointCloud[i, 4], 4)})')
                    
        # Highlighting specific points
        for i in range(len(self.rangeAxisVals)):
            if (self.Peak1 >= self.rangeAxisVals[i] and self.Peak1 < self.rangeAxisVals[i+1]):
                highlight_peak1 = i  
            if (self.Peak2 >= self.rangeAxisVals[i] and self.Peak2 < self.rangeAxisVals[i+1]):
                highlight_peak2 = i   
            if (self.Peak3 >= self.rangeAxisVals[i] and self.Peak3 < self.rangeAxisVals[i+1]):
                highlight_peak3 = i                      

        #self.HighlightPlot.clear()
        highlight_indices = [highlight_peak1]
        highlight_x = [self.rangeAxisVals[i] for i in highlight_indices]
        highlight_y = [self.rangeProfile[i] for i in highlight_indices]
        data = [{'pos': (x_val, y_val)} for x_val, y_val in zip(highlight_x, highlight_y)]
        self.HighlightPlotPeak1.setData(data)

        # Adding labels to highlighted points
        for i in range(len(highlight_indices)):
            self.peakLabel1.setPos(highlight_x[i], highlight_y[i])

        highlight_indices = [highlight_peak2]
        highlight_x = [self.rangeAxisVals[i] for i in highlight_indices]
        highlight_y = [self.rangeProfile[i] for i in highlight_indices]
        data = [{'pos': (x_val, y_val)} for x_val, y_val in zip(highlight_x, highlight_y)]
        self.HighlightPlotPeak2.setData(data)

        for i in range(len(highlight_indices)):
                self.peakLabel2.setPos(highlight_x[i], highlight_y[i])

        highlight_indices = [highlight_peak3]
        highlight_x = [self.rangeAxisVals[i] for i in highlight_indices]
        highlight_y = [self.rangeProfile[i] for i in highlight_indices]
        data = [{'pos': (x_val, y_val)} for x_val, y_val in zip(highlight_x, highlight_y)]
        self.HighlightPlotPeak3.setData(data)

        for i in range(len(highlight_indices)):
                self.peakLabel3.setPos(highlight_x[i], highlight_y[i])
            
        self.updateLevelSensingPeaks()
  
        if ('powerData' in outputDict):
            powerData = outputDict['powerData']
            if(powerData is not None):
                self.updateLevelSensingPower(powerData)
        
        self.graphDone(outputDict)

    def graphDone(self, outputDict):
        plotTime = int(round(time.time()*1000)) - self.plotStart
        self.plotTimeDisplay.setText('Plot Time: ' + str(plotTime) + 'ms')
        self.plotComplete = 1

        if ('frameNum' in outputDict):
            self.frameNumDisplay.setText('Frame: ' + str(outputDict['frameNum']))

        if ('numDetectedPoints' in outputDict):
            self.numPointsDisplay.setText('Points: ' + str(outputDict['numDetectedPoints']))

    def updatePowerNumbers(self, powerData):
        if powerData['power1v2'] == 65535:
            self.avgPower.setText('Average Power: N/A')
        else:
            powerStr = str((powerData['power1v2'] \
                + powerData['power1v2RF'] + powerData['power1v8'] + powerData['power3v3']) * 0.1)
            self.avgPower.setText('Average Power: ' + powerStr[:5] + ' mW')

            
        if(powerData is not None):
            self.updatePowerNumbers(powerData)