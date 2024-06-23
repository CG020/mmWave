import numpy as np
import pyqtgraph as pg
import pyqtgraph.opengl as gl

from graph_utilities import eulerRot, getBoxArcs, getBoxLines

# Different methods to color the points 
COLOR_MODE_SNR = 'SNR'
COLOR_MODE_HEIGHT = 'Height'
COLOR_MODE_DOPPLER = 'Doppler'
COLOR_MODE_TRACK = 'Associated Track'


class Plot2D():
    def __init__(self):
        self.plot_2d = pg.GraphicsLayoutWidget()
        self.plot_2d.setBackground('w')
        self.scatterPlot2D = self.plot_2d.addPlot(title='E-Bikes Visualizer')
        self.scatterPlot2D.showGrid(x=False,y=False)
        self.scatterPlot2D.setXRange(-40,40,padding=0.01)
        self.scatterPlot2D.setYRange(0,150,padding=0.01)
        # self.scatterPlot2D.setLimits(xMin=-40, xMax=40, yMin=0, yMax=150, minXRange=80, maxXRange=80, maxYRange=150, minYRange=150)
        self.scatterPlot2D.disableAutoRange()
        self.scatterPlot2D.setAspectLocked(lock=True, ratio=1)
        self.scatter = pg.ScatterPlotItem()
        self.scatterPlot2D.setLabel('bottom', 'X (m)')
        self.scatterPlot2D.setLabel('left', 'Y (m)')
        self.scatterPlot2D.addItem(self.scatter)

        self.maxRange = 150 # meters
        self.minAngle = -40
        self.maxAngle = 40 # degrees

        self.plotComplete = 1


        self.boundaryBoxViz = []
        self.ellipsoids = []
        # Persistent point cloud
        self.previousClouds = []
        self.numPersistentFrames = int(1)

        self.mpdZoneType = None

    def updatePointCloud(self, outputDict):
        if ('pointCloud' in outputDict and 'numDetectedPoints' in outputDict):
            pointCloud = outputDict['pointCloud']

            # Rotate point cloud and tracks to account for elevation and azimuth tilt
            if (self.elev_tilt != 0 or self.az_tilt != 0):
                for i in range(outputDict['numDetectedPoints']):
                    rotX, rotY, rotZ = eulerRot (pointCloud[i,0], pointCloud[i,1], pointCloud[i,2], self.elev_tilt, self.az_tilt)
                    pointCloud[i,0] = rotX
                    pointCloud[i,1] = rotY
                    pointCloud[i,2] = rotZ

            # Shift points to account for sensor height
            if (self.sensorHeight != 0):
                pointCloud[:,2] = pointCloud[:,2] + self.sensorHeight

            # Add current point cloud to the cumulative cloud if it's not empty
            self.previousClouds.append(outputDict['pointCloud'])

        # If we have more point clouds than needed, stated by numPersistentFrames, delete the oldest ones 
        while(len(self.previousClouds) > self.numPersistentFrames):
            self.previousClouds.pop(0)


            # def add tracks:
            #                     if (tracks is not None):
            #         for i in range(numTracks):
            #             rotX, rotY, rotZ = eulerRot (tracks[i,1], tracks[i,2], tracks[i,3], self.elev_tilt, self.az_tilt)
            #             tracks[i,1] = rotX
            #             tracks[i,2] = rotY
            #             tracks[i,3] = rotZ
            #             if (tracks is not None):
            #         tracks[:,3] = tracks[:,3] + self.sensorHeight
            
    # Add a boundary box to the boundary boxes tab
    def addBoundBox(self, name, minX=0, maxX=0, minY=0, maxY=0):
        newBox = gl.GLLinePlotItem()
        newBox.setVisible(True)
        self.plot_2d.addItem(newBox)     

        if ('arcBox' in name):
            try:
                boxLines = getBoxArcs(minX,minY,maxX,maxY)
                boxColor = pg.glColor('b')
                newBox.setData(pos=boxLines,color=boxColor,width=2,antialias=True,mode='lines')

                # TODO add point boundary back into visualizer

                boundaryBoxItem = {
                    'plot': newBox,
                    'name': name,
                    'boxLines': boxLines,
                    'minX': float(minX),
                    'maxX': float(maxX),
                    'minY': float(minY),
                    'maxY': float(maxY),
                }   

                self.boundaryBoxViz.append(boundaryBoxItem) 
                self.plot_2d.addItem(newBox)
            except:
                # You get here if you enter an invalid number
                # When you enter a minus sign for a negative value, you will end up here before you type the full number
                pass
        else:
            try:
                boxLines = getBoxLines(minX,minY,maxX,maxY)
                boxColor = pg.glColor('b')
                newBox.setData(pos=boxLines,color=boxColor,width=2,antialias=True,mode='lines')

                # TODO add point boundary back into visualizer

                boundaryBoxItem = {
                    'plot': newBox,
                    'name': name,
                    'boxLines': boxLines,
                    'minX': float(minX),
                    'maxX': float(maxX),
                    'minY': float(minY),
                    'maxY': float(maxY),
                }   

                self.boundaryBoxViz.append(boundaryBoxItem) 
                self.plot_2d.addItem(newBox)
            except:
                # You get here if you enter an invalid number
                # When you enter a minus sign for a negative value, you will end up here before you type the full number
                pass      

    def changeBoundaryBoxColor(self, box, color):
        box['plot'].setData(pos=box['boxLines'], color=pg.glColor(color),width=2,antialias=True,mode='lines')
        
    def parseTrackingCfg(self, args):
        self.maxTracks = int(args[4])

    def parseBoundaryBox(self, args):
        if (args[0] == 'SceneryParam' or args[0] == 'boundaryBox'):
            leftX = float(args[1])
            rightX = float(args[2])
            nearY = float(args[3])
            farY = float(args[4])
            bottomZ = float(args[5])
            topZ = float(args[6])
                        
            self.addBoundBox('trackerBounds', leftX, rightX, nearY, farY)
        elif (args[0] == 'zoneDef'):
            zoneIdx = int(args[1])
            minX = float(args[2])
            maxX = float(args[3])
            minY = float(args[4])
            maxY = float(args[5])
            # Offset by 3 so it is in center of screen
            minZ = float(args[6]) + self.sensorHeight
            maxZ = float(args[7]) + self.sensorHeight

            name = 'occZone' + str(zoneIdx)
            self.addBoundBox(name, minX, maxX, minY, maxY, minZ, maxZ)
        elif (args[0] == 'mpdBoundaryBox'):
            zoneIdx = int(args[1])
            minX = float(args[2])
            maxX = float(args[3])
            minY = float(args[4])
            maxY = float(args[5])
            minZ = float(args[6])
            maxZ = float(args[7])
            name = 'mpdBox' + str(zoneIdx)
            self.addBoundBox(name, minX, maxX, minY, maxY, minZ, maxZ)
        elif (args[0] == 'mpdBoundaryArc'):
            zoneIdx = int(args[1])
            minR = float(args[2])
            maxR = float(args[3])
            minTheta = float(args[4])
            maxTheta = float(args[5])
            minZ = float(args[6])
            maxZ = float(args[7])
            name = 'arcBox' + str(zoneIdx)
            self.addBoundBox(name, minR, maxR, minTheta, maxTheta, minZ, maxZ)

        # TODO print out somewhere these boundary boxes

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

        # TODO update text showing sensor position text?
