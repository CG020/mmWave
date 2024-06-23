# General Library Imports
import numpy as np 

# PyQt Imports
import pyqtgraph as pg

# Local Imports
from gui_common import next_power_of_2

# Logger
import logging
log = logging.getLogger(__name__)

class Plot1D():
    def __init__(self):
        self.rangeProfileType = -1
        self.NumOfAdcSamples = -1
        self.rangeAxisVals = -1
        self.DigOutputSampRate = -1
        self.NumOfAdcSamples = -1
        self.ChirpRfFreqSlope = -1
        self.rangeProfile = np.zeros(128)
        self.ChirpTxMimoPatSel = -1

        self.rangePlot = pg.PlotWidget()
        self.rangePlot.setBackground('w')
        self.rangePlot.showGrid(x=True,y=True)
        self.rangePlot.setXRange(0,self.NumOfAdcSamples/2,padding=0.01)
        self.rangePlot.setYRange(0,150,padding=0.01)
        self.rangePlot.setMouseEnabled(False,False)
        self.rangeData = pg.PlotCurveItem(pen=pg.mkPen(width=3, color='r'))
        self.rangePlot.addItem(self.rangeData)
        
    def update1DGraph(self, outputDict):
        # TODO add range profile to 6843
        if ('rangeProfile' in outputDict) :
            # 6432 Major Motion or Minor Motion
            if (self.rangeProfileType == 1 or self.rangeProfileType == 2):
                    numRangeBinsParsed = len(outputDict['rangeProfile'])
                    # Check size of rangeData matches expected size
                    if (numRangeBinsParsed == next_power_of_2(round(self.NumOfAdcSamples / 2))):
                        self.rangeProfile = [np.log10(max(1, item)) * 20 for item in outputDict['rangeProfile']] # list comprehension required so we don't take log(0)         
                        # Update graph data
                        self.rangeData.setData(self.rangeAxisVals, self.rangeProfile)
                    else:
                        log.error(f'Size of rangeProfile (${numRangeBinsParsed}) did not match the expected size (${next_power_of_2(round(self.NumOfAdcSamples / 2))})')

#-----------------------------------------------------
# Config Parsing Functions
#-----------------------------------------------------

    def parseChirpComnCfg(self, args):
        self.DigOutputSampRate = int(args[1])
        self.NumOfAdcSamples = int(args[4])
        self.ChirpTxMimoPatSel = int(args[5])

    def parseChirpTimingCfg(self, args):
        self.ChirpRfFreqSlope = float(args[4])

    def parseGuiMonitor(self, args):
        self.rangeProfileType = int(args[2])

    def setRangeValues(self):
        # Set range resolution
        self.rangeRes = (3e8*(100/self.DigOutputSampRate)*1e6)/(2*self.ChirpRfFreqSlope*1e12*self.NumOfAdcSamples)
        self.rangePlot.setXRange(0,(self.NumOfAdcSamples/2)*self.rangeRes,padding=0.01)
        self.rangeAxisVals = np.arange(0, self.NumOfAdcSamples/2*self.rangeRes, self.rangeRes)

        # Set title based on selected range profile type
        if (self.rangeProfileType == 1):
            self.rangePlot.getPlotItem().setLabel('top','Major Range Profile')
        elif (self.rangeProfileType == 2):
            self.rangePlot.getPlotItem().setLabel('top','Minor Range Profile')
        else:
            self.rangePlot.getPlotItem().setLabel('top','Range Profile DISABLED')
