# General Library Imports
import time
from serial.tools import list_ports
import os
import sys
from contextlib import suppress

# PyQt Imports
from PyQt5 import QtGui
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QTabWidget,
    QGridLayout,
    QMenu,
    QGroupBox,
    QLineEdit,
    QLabel,
    QPushButton,
    QComboBox,
    QFileDialog,
    QMainWindow,
    QWidget,
    QShortcut,
)

# Local Imports
from cached_data import CachedDataType
from demo_defines import *
from gui_threads import *

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'Common_Tabs')))


from Common_Tabs.plot_1d import Plot1D
from Common_Tabs.plot_2d import Plot2D
from Common_Tabs.plot_3d import Plot3D

from Demo_Classes.surface_classification import SurfaceClassification
from Demo_Classes.people_tracking import PeopleTracking
from Demo_Classes.gesture_recognition import GestureRecognition
from Demo_Classes.level_sensing import LevelSensing
from Demo_Classes.small_obstacle import SmallObstacle
from Demo_Classes.out_of_box_x843 import OOBx843
from Demo_Classes.out_of_box_x432 import OOBx432
from Demo_Classes.true_ground_speed import TrueGroundSpeed
from Demo_Classes.long_range_pd import LongRangePD
from Demo_Classes.mobile_tracker import MobileTracker
from Demo_Classes.kick_to_open import KickToOpen
from Demo_Classes.calibration import Calibration
from Demo_Classes.vital_signs import VitalSigns
from Demo_Classes.dashcam import Dashcam
from Demo_Classes.ebikes_x432 import EBikes

# Logger
import logging
log = logging.getLogger(__name__)


class Window(QMainWindow):
    def __init__(self, parent=None, size=[], title="Applications Visualizer"):
        super(Window, self).__init__(parent)

        self.core = Core()

        self.setWindowIcon(QtGui.QIcon("./images/logo.png"))

        self.shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        self.shortcut.activated.connect(self.close)

        # Set the layout
        # Create tab for different graphing options
        self.demoTabs = QTabWidget()

        self.gridLayout = QGridLayout()

        # Add connect options
        self.initConfigPane()
        self.initConnectionPane()

        self.gridLayout.addWidget(self.comBox, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.configBox, 1, 0, 1, 1)
        self.gridLayout.addWidget(self.demoTabs, 0, 1, 8, 1)

        self.gridLayout.setColumnStretch(0, 1)
        self.gridLayout.setColumnStretch(1, 5)

        self.central = QWidget()
        self.central.setLayout(self.gridLayout)

        self.setWindowTitle(title)
        self.initMenuBar()

        self.setCentralWidget(self.central)

        self.showMaximized()

    def initMenuBar(self):
        menuBar = self.menuBar()
        # Creating menus using a QMenu object
        fileMenu = QMenu("&File", self)
        self.loadAction = QAction("&Load and Replay", self)
        self.loadAction.setDisabled(True)
        optionMenu = fileMenu.addMenu("Options")
        self.saveBinaryAction = QAction("Save Binary Data to File", self)
        self.logOutputAction = QAction("Log Terminal Output to File", self)
        self.loadAction.triggered.connect(self.loadForReplay)
        self.saveBinaryAction.triggered.connect(self.toggleSaveData)
        self.saveBinaryAction.setCheckable(True)
        self.logOutputAction.triggered.connect(self.toggleLogOutput)
        self.logOutputAction.setCheckable(True)
        fileMenu.addAction(self.loadAction)
        optionMenu.addAction(self.saveBinaryAction)
        optionMenu.addAction(self.logOutputAction)
        menuBar.addMenu(fileMenu)

    def loadForReplay(self):
        print("TODO")

    def toggleSaveData(self):
        if self.saveBinaryAction.isChecked():
            self.core.parser.setSaveBinary(True)
        else:
            self.core.parser.setSaveBinary(False)

    def toggleLogOutput(self):
        if (
            self.saveBinaryAction.isChecked()
        ):  # Save terminal output to logFile, set 0 to show terminal output
            ts = time.localtime()
            terminalFileName = str(
                "logfile_"
                + str(ts[2])
                + str(ts[1])
                + str(ts[0])
                + "_"
                + str(ts[3])
                + str(ts[4])
                + ".txt"
            )
            sys.stdout = open(terminalFileName, "w")
        else:
            sys.stdout = sys.__stdout__

    def initConnectionPane(self):
        self.comBox = QGroupBox("Connect to COM Ports")
        self.cliCom = QLineEdit("")
        self.dataCom = QLineEdit("")
        self.connectStatus = QLabel("Not Connected")
        self.connectButton = QPushButton("Connect")
        self.connectButton.clicked.connect(self.onConnect)
        self.demoList = QComboBox()
        self.deviceList = QComboBox()

        # TODO Add replay support
        self.demoList.addItems(self.core.getDemoList())
        self.demoList.currentIndexChanged.connect(self.onChangeDemo)
        self.deviceList.addItems(self.core.getDeviceList())
        self.deviceList.currentIndexChanged.connect(self.onChangeDevice)
        self.comLayout = QGridLayout()
        self.comLayout.addWidget(QLabel("Device:"), 0, 0)
        self.comLayout.addWidget(self.deviceList, 0, 1)
        self.comLayout.addWidget(QLabel("CLI COM:"), 1, 0)
        self.comLayout.addWidget(self.cliCom, 1, 1)
        self.comLayout.addWidget(QLabel("DATA COM:"), 2, 0)
        self.comLayout.addWidget(self.dataCom, 2, 1)
        self.comLayout.addWidget(QLabel("Demo:"), 3, 0)
        self.comLayout.addWidget(self.demoList, 3, 1)
        self.comLayout.addWidget(self.connectButton, 4, 0)
        self.comLayout.addWidget(self.connectStatus, 4, 1)

        self.comBox.setLayout(self.comLayout)
        self.demoList.setCurrentIndex(1)  # initialize this to a stable value
        self.demoList.setCurrentIndex(0)  # initialize this to a stable value

        # Find all Com Ports
        serialPorts = list(list_ports.comports())

        # Find default CLI Port and Data Port
        for port in serialPorts:
            if (
                CLI_XDS_SERIAL_PORT_NAME in port.description
                or CLI_SIL_SERIAL_PORT_NAME in port.description
            ):
                log.info(f"CLI COM Port found: {port.device}")
                comText = port.device
                comText = comText.replace("COM", "")
                self.cliCom.setText(comText)

            elif (
                DATA_XDS_SERIAL_PORT_NAME in port.description
                or DATA_SIL_SERIAL_PORT_NAME in port.description
            ):
                log.info(f"Data COM Port found: {port.device}")
                comText = port.device
                comText = comText.replace("COM", "")
                self.dataCom.setText(comText)

        self.core.isGUILaunched = 1
        self.loadCachedData()

    def initConfigPane(self):
        self.configBox = QGroupBox("Configuration")
        self.selectConfig = QPushButton("Select Configuration")
        self.sendConfig = QPushButton("Start and Send Configuration")
        self.start = QPushButton("Start without Send Configuration ")
        self.sensorStop = QPushButton("Send sensorStop Command")
        self.sensorStop.setToolTip("Stop sensor (only works if lowPowerCfg is 0)")
        self.filename_edit = QLineEdit()
        self.selectConfig.clicked.connect(lambda: self.selectCfg(self.filename_edit))
        self.sendConfig.clicked.connect(self.sendCfg)
        self.start.clicked.connect(self.startApp)
        self.sensorStop.clicked.connect(self.stopSensor)
        self.sensorStop.setHidden(True)
        self.configLayout = QGridLayout()
        self.configLayout.addWidget(self.filename_edit, 0, 0, 1, 1)
        self.configLayout.addWidget(self.selectConfig, 0, 1, 1, 1)
        self.configLayout.addWidget(self.sendConfig, 1, 0, 1, 2)
        self.configLayout.addWidget(self.start, 2, 0, 1, 2)
        self.configLayout.addWidget(self.sensorStop, 3, 0, 1, 2)
        # self.configLayout.addStretch(1)
        self.configBox.setLayout(self.configLayout)

    def loadCachedData(self):
        self.core.loadCachedData(
            self.demoList, self.deviceList, self.gridLayout, self.demoTabs
        )

    # Callback function when device is changed
    def onChangeDevice(self):
        self.core.changeDevice(
            self.demoList, self.deviceList, self.gridLayout, self.demoTabs
        )
        self.core.updateCOMPorts(self.cliCom, self.dataCom)
        self.core.updateResetButton(self.sensorStop)

    # Callback function when demo is changed
    def onChangeDemo(self):
        self.core.changeDemo(
            self.demoList, self.deviceList, self.gridLayout, self.demoTabs
        )
        # self.core.changeDevice(self.demoList, self.deviceList, self.gridLayout, self.demoTabs)

    # Callback function when connect button clicked
    def onConnect(self):
        if (
            self.connectStatus.text() == "Not Connected"
            or self.connectStatus.text() == "Unable to Connect"
        ):
            if self.core.connectCom(self.cliCom, self.dataCom, self.connectStatus) == 0:
                self.connectButton.setText("Reset Connection")
        else:
            self.core.gracefulReset()
            self.connectButton.setText("Connect")
            self.connectStatus.setText("Not Connected")

            # need to do ser.close()

    # Callback function when 'Select Configuration' is clicked
    def selectCfg(self, filename):
        self.core.selectCfg(filename)

    # Callback function when 'Start and Send Configuration' is clicked
    def sendCfg(self):
        self.core.sendCfg()

    # Callback function to send sensorStop to device
    def stopSensor(self):
        self.core.stopSensor()

    # Callback function when 'Start without Send Configuration' is clicked
    def startApp(self):
        self.core.startApp()


class Core:
    def __init__(self):
        self.cachedData = CachedDataType()

        self.device = "xWR6843"
        self.demo = DEMO_OOB_x843

        self.frameTime = 50
        self.parser = UARTParser(type="DoubleCOMPort")

        # set to 1 
        self.isGUILaunched = 0

        # Populated with each demo and it's corresponding object
        self.demoClassDict = {
            DEMO_OOB_x843: OOBx843(),
            DEMO_OOB_x432: OOBx432(),
            DEMO_3D_PEOPLE_TRACKING: PeopleTracking(),
            DEMO_VITALS: VitalSigns(),
            DEMO_SMALL_OBSTACLE: SmallObstacle(),
            DEMO_GESTURE: GestureRecognition(),
            DEMO_SURFACE: SurfaceClassification(),
            DEMO_LEVEL_SENSING: LevelSensing(),
            DEMO_GROUND_SPEED: TrueGroundSpeed(),
            DEMO_LONG_RANGE: LongRangePD(),
            DEMO_MOBILE_TRACKER: MobileTracker(),
            DEMO_KTO: KickToOpen(),
            DEMO_CALIBRATION: Calibration(),
            DEMO_DASHCAM: Dashcam(),
            DEMO_EBIKES: EBikes(),
        }

    def loadCachedData(self, demoList, deviceList, gridLayout, demoTabs):
        deviceName = self.cachedData.getCachedDeviceName()
        demoName = self.cachedData.getCachedDemoName()

        if deviceName in self.getDeviceList():
            deviceList.setCurrentIndex(self.getDeviceList().index(deviceName))

        if demoName in self.getDemoList():
            demoList.setCurrentIndex(self.getDemoList().index(demoName))
            self.changeDemo(demoList, deviceList, gridLayout, demoTabs)

    def getDemoList(self):
        return DEVICE_DEMO_DICT[self.device]["demos"]

    def getDeviceList(self):
        return list(DEVICE_DEMO_DICT.keys())

    def changeDemo(self, demoList, deviceList, gridLayout, demoTabs):
        self.demo = demoList.currentText()

        if (self.isGUILaunched):
            self.cachedData.setCachedDemoName(self.demo)
            self.cachedData.setCachedDeviceName(deviceList.currentText())

        permanentWidgetsList = ["Connect to COM Ports", "Configuration", "Tabs"]
        # Destroy current contents of graph pane
        for _ in range(demoTabs.count()):
            demoTabs.removeTab(0)
        for i in range(len(gridLayout)):
            try:
                currWidget = gridLayout.itemAt(i).widget()
                if currWidget.title() not in permanentWidgetsList:
                    currWidget.setVisible(False)
            except AttributeError as e:
                log.log(0, "Demo Tabs don't have title attribute. This is OK")
                continue

        # Make call to selected demo's initialization function
        if self.demo in self.demoClassDict:
            self.demoClassDict[self.demo].setupGUI(gridLayout, demoTabs, self.device)

    def changeDevice(self, demoList, deviceList, gridLayout, demoTabs):
        self.device = deviceList.currentText()

        if (self.isGUILaunched):
            self.cachedData.setCachedDemoName(demoList.currentText())
            self.cachedData.setCachedDeviceName(self.device)

        if DEVICE_DEMO_DICT[self.device]["singleCOM"]:
            self.parser.parserType = "SingleCOMPort"
        else:
            self.parser.parserType = "DoubleCOMPort"

        demoList.clear()
        demoList.addItems(DEVICE_DEMO_DICT[self.device]["demos"])

    def updateCOMPorts(self, cliCom, dataCom):
        if DEVICE_DEMO_DICT[self.device]["isxWRLx432"]:
            dataCom.setText(cliCom.text())
            dataCom.setEnabled(False)
        else:
            dataCom.setEnabled(True)

    def updateResetButton(self, sensorStopButton):
        if DEVICE_DEMO_DICT[self.device]["isxWRLx432"]:
            sensorStopButton.setHidden(True) # TODO change to false once sending sensorStop is implemented
        else:
            sensorStopButton.setHidden(True)

    def stopSensor(self):
        self.parser.sendLine("sensorStop 0")

    def selectFile(self, filename):
        try:
            current_dir = os.getcwd()
            configDirectory = current_dir
            path = self.cachedData.getCachedCfgPath()
            if path != "":
                configDirectory = path
        except:
            configDirectory = ""

        fd = QFileDialog()
        filt = "cfg(*.cfg)"
        fname = fd.getOpenFileName(directory=configDirectory, filter=filt)
        filename.setText(str(fname[0]))
        return fname[0]

    def parseCfg(self, fname):
        with open(fname, "r") as cfg_file:
            self.cfg = cfg_file.readlines()
        for line in self.cfg:
            args = line.split()
            if len(args) > 0:
                # trackingCfg
                if args[0] == "trackingCfg":
                    if len(args) < 5:
                        log.error("trackingCfg had fewer arguments than expected")
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.demo].parseTrackingCfg(args)
                elif args[0] == "SceneryParam" or args[0] == "boundaryBox":
                    if len(args) < 7:
                        log.error(
                            "SceneryParam/boundaryBox had fewer arguments than expected"
                        )
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.demo].parseBoundaryBox(args)
                elif args[0] == "frameCfg":
                    if len(args) < 4:
                        log.error("frameCfg had fewer arguments than expected")
                    else:
                        self.frameTime = float(args[5]) / 2
                elif args[0] == "sensorPosition":
                    # sensorPosition for x843 family has 3 args
                    if DEVICE_DEMO_DICT[self.device]["isxWRx843"] and len(args) < 4:
                        log.error("sensorPosition had fewer arguments than expected")
                    elif DEVICE_DEMO_DICT[self.device]["isxWRLx432"] and len(args) < 6:
                        log.error("sensorPosition had fewer arguments than expected")
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.demo].parseSensorPosition(
                                args, DEVICE_DEMO_DICT[self.device]["isxWRx843"]
                            )
                # Only used for Small Obstacle Detection
                elif args[0] == "occStateMach":
                    numZones = int(args[1])
                # Only used for Small Obstacle Detection
                elif args[0] == "zoneDef":
                    if len(args) < 8:
                        log.error("zoneDef had fewer arguments than expected")
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.demo].parseBoundaryBox(args)
                elif args[0] == "mpdBoundaryBox":
                    if len(args) < 8:
                        log.error("mpdBoundaryBox had fewer arguments than expected")
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.demo].parseBoundaryBox(args)
                elif args[0] == "chirpComnCfg":
                    if len(args) < 8:
                        log.error("chirpComnCfg had fewer arguments than expected")
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.demo].parseChirpComnCfg(args)
                elif args[0] == "chirpTimingCfg":
                    if len(args) < 6:
                        log.error("chirpTimingCfg had fewer arguments than expected")
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.demo].parseChirpTimingCfg(args)
                # TODO This is specifically guiMonitor for 60Lo, this parsing will break the gui when an SDK 3 config is sent
                elif args[0] == "guiMonitor":
                    if DEVICE_DEMO_DICT[self.device]["isxWRLx432"]:
                        if len(args) < 12:
                            log.error("guiMonitor had fewer arguments than expected")
                        else:
                            with suppress(AttributeError):
                                self.demoClassDict[self.demo].parseGuiMonitor(args)
                elif args[0] == "presenceDetectCfg":
                    with suppress(AttributeError):
                        self.demoClassDict[self.demo].parsePresenceDetectCfg(args)
                elif args[0] == "sigProcChainCfg2":
                    with suppress(AttributeError):
                        self.demoClassDict[self.demo].parseSigProcChainCfg2(args)
                elif args[0] == "mpdBoundaryArc":
                    if len(args) < 8:
                        log.error("mpdBoundaryArc had fewer arguments than expected")
                    else:
                        with suppress(AttributeError):
                            self.demoClassDict[self.demo].parseBoundaryBox(args)
                elif args[0] == "measureRangeBiasAndRxChanPhase":
                    with suppress(AttributeError):
                        self.demoClassDict[self.demo].parseRangePhaseCfg(args)
                elif args[0] == "clutterRemoval":
                    with suppress(AttributeError):
                        self.demoClassDict[self.demo].parseClutterRemovalCfg(args)
                elif args[0] == "sigProcChainCfg":
                    with suppress(AttributeError):
                        self.demoClassDict[self.demo].parseSigProcChainCfg(args)
                elif args[0] == "channelCfg":
                    with suppress(AttributeError):
                        self.demoClassDict[self.demo].parseChannelCfg(args)

        # Initialize 1D plot values based on cfg file
        with suppress(AttributeError):
            self.demoClassDict[self.demo].setRangeValues()

    def selectCfg(self, filename):
        try:
            file = self.selectFile(filename)
            self.cachedData.setCachedCfgPath(file)  # cache the file and demo used
            self.parseCfg(file)
        except Exception as e:
            log.error(e)
            log.error(
                "Parsing .cfg file failed. Did you select a valid configuration file?"
            )

        log.debug("Demo Changed to " + self.demo)
        if self.demo == DEMO_CALIBRATION:
            self.demoClassDict[self.demo].checkCalibrationParams()

    def sendCfg(self):
        try:
            if self.demo != "Replay":
                self.parser.sendCfg(self.cfg)
                sys.stdout.flush()
                self.parseTimer.start(int(self.frameTime))  # need this line
        except Exception as e:
            log.error(e)
            log.error("Parsing .cfg file failed. Did you select the right file?")

    def updateGraph(self, outputDict):
        self.demoClassDict[self.demo].updateGraph(outputDict)

    def connectCom(self, cliCom, dataCom, connectStatus):
        if self.demo == DEMO_GESTURE:
            self.frameTime = 25 # Gesture demo runs at 35ms frame time
        # init threads and timers
        self.uart_thread = parseUartThread(self.parser)
        # TODO implement replaying ability
        # if (self.demoList.currentText() != 'Replay'):
        #     self.uart_thread.fin.connect(self.parseData)
        self.uart_thread.fin.connect(self.updateGraph)
        self.parseTimer = QTimer()
        self.parseTimer.setSingleShot(False)
        self.parseTimer.timeout.connect(self.parseData)
        try:
            if os.name == "nt":
                uart = "COM" + cliCom.text()
                data = "COM" + dataCom.text()
            else:
                uart = cliCom.text()
                data = dataCom.text()
            if DEVICE_DEMO_DICT[self.device]["isxWRx843"]:  # If using x843 device
                self.parser.connectComPorts(uart, data)
            else:  # If not x843 device then defer to x432 device
                if self.demo == DEMO_GESTURE or self.demo == DEMO_KTO:
                    self.parser.connectComPort(uart, 1250000)
                else:
                    self.parser.connectComPort(uart)
            connectStatus.setText("Connected")
        except Exception as e:
            log.error(e)
            connectStatus.setText("Unable to Connect")
            return -1

        return 0

    def startApp(self):
        self.parseTimer.start(int(self.frameTime))  # need this line

    def parseData(self):
        self.uart_thread.start(priority=QThread.HighestPriority)

    def gracefulReset(self):
        self.parseTimer.stop()
        self.uart_thread.stop()
        if self.parser.cliCom is not None:
            self.parser.cliCom.close()
        if self.parser.dataCom is not None:
            self.parser.dataCom.close()
        for demo in self.demoClassDict.values():
            if hasattr(demo, "plot_3d_thread"):
                demo.plot_3d_thread.stop()
            if hasattr(demo, "plot_3d"):
                demo.removeAllBoundBoxes()
