# General Library Imports

# PyQt Imports
import pyqtgraph as pg

# Local Imports
from Common_Tabs.plot_1d import Plot1D

# Logger
import logging
log = logging.getLogger(__name__)

class Calibration(Plot1D):
    def __init__(self):
        Plot1D.__init__(self)  
        self.channelCfg = {'RX':3, 'TX':2}
        self.sigProcChain = {'majorMotionEnabled':1}
        self.clutterRemoval = 0
        self.measureRangeBiasAndRxChanPhase = {'enabled':0, 'centerDist':0,'searchRange':0}
        self.chirpComnCfg = {'ChirpTxMimoPatSel':4}

    def setupGUI(self, gridLayout, demoTabs, device):
        demoTabs.addTab(self.rangePlot, 'Range Plot')

    def updateGraph(self, outputDict):
        self.update1DGraph(outputDict)
        self.graphDone(outputDict)

    def graphDone(self, outputDict):
        if ('RXChanCompInfo' in outputDict):
            coefficients = outputDict['RXChanCompInfo']
            # Print results to the terminal output to be copied later
            print("compRangeBiasAndRxChanPhase", end=" ")
            for i in range(13):
                print(f'{coefficients[i]:0.4f}', end=" ")
            print('\n')

    def parseRangePhaseCfg(self, args):
        self.measureRangeBiasAndRxChanPhase['enabled'] = 1
        self.measureRangeBiasAndRxChanPhase['centerDist'] = float(args[2])
        self.measureRangeBiasAndRxChanPhase['searchRange'] = float(args[3])

    def parseClutterRemovalCfg(self, args):
        self.clutterRemoval = int(args[1])

    def parseSigProcChainCfg(self, args):
        # Major Motion is if the motion mode is equal to 1 or 3
        self.sigProcChain['majorMotionEnabled'] = int(args[3]) % 2
        # Minor Motion is if the motion mode is 2 or 3
        self.sigProcChain['minorMotionEnabled'] = 1 if int(args[3]) > 1 else 0

    def parseChannelCfg(self, args):
        self.channelCfg['RX'] = int(args[1])
        self.channelCfg['TX'] = int(args[2])

    def checkCalibrationParams(self):
        if (self.measureRangeBiasAndRxChanPhase['enabled'] != 1):
            log.error("measureRangeBiasAndRxChanPhase must be enabled, set first argument to 1")
        # Only run the measurement if BPM is disabled, clutter removal is off, major motion is on and the number of TX/RX antennas is 2/3
        if (self.ChirpTxMimoPatSel != 1):
            log.error("measureRangeBiasAndRxChanPhase requires TDM mode not BPM Mode. Change the 5th argument of chirpComnCfg to 1")
        if (self.clutterRemoval != 0):
            log.error("measureRangeBiasAndRxChanPhase requires Clutter Removal Off. Change the 1st argument clutterRemoval to 0")
        if (self.sigProcChain['majorMotionEnabled'] != 1):
            log.error("measureRangeBiasAndRxChanPhase requires Major Motion Enabled. Change the 3rd argument of sigProcChainCfg to 1 or 3")
        if (self.channelCfg['TX'] != 3):
            log.error("measureRangeBiasAndRxChanPhase requires 2 TX enabled. Change the 2nd argument of channelCfg to 3")
        if (self.channelCfg['RX'] != 7):
            log.error("measureRangeBiasAndRxChanPhase requires 3 RX enabled. Change the 1st argument of channelCfg to 7")

        # Create range bin zone in the gui
        rangeMin = self.measureRangeBiasAndRxChanPhase['centerDist'] - self.measureRangeBiasAndRxChanPhase['searchRange']/2
        rangeMax = self.measureRangeBiasAndRxChanPhase['centerDist'] + self.measureRangeBiasAndRxChanPhase['searchRange']/2
        self.compRangeBiasZone = pg.LinearRegionItem((rangeMin, rangeMax), movable=False,span=(0, 0.94))
        self.rangePlot.addItem(self.compRangeBiasZone)
        text = pg.TextItem(text='Place Peak in Calibration Zone', color=(200,0,0), anchor=(0.5, 0))
        text.setPos(self.measureRangeBiasAndRxChanPhase['centerDist'],145)
        self.rangePlot.addItem(text)
        text.setVisible(True)