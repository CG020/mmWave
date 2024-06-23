import struct
import logging
import numpy as np
import math

# Local File Imports
from gui_common import NUM_CLASSES_IN_CLASSIFIER, sphericalToCartesianPointCloud

log = logging.getLogger(__name__)

# ================================================== Parsing Functions For Individual TLV's ==================================================

# Point Cloud TLV from SDK
def parsePointCloudTLV(tlvData, tlvLength, outputDict):
    pointCloud = outputDict['pointCloud']
    pointStruct = '4f'  # X, Y, Z, and Doppler
    pointStructSize = struct.calcsize(pointStruct)
    numPoints = int(tlvLength/pointStructSize)

    for i in range(numPoints):
        try:
            x, y, z, doppler = struct.unpack(pointStruct, tlvData[:pointStructSize])
        except:
            numPoints = i
            log.error('Point Cloud TLV Parser Failed')
            break
        tlvData = tlvData[pointStructSize:]
        pointCloud[i,0] = x 
        pointCloud[i,1] = y
        pointCloud[i,2] = z
        pointCloud[i,3] = doppler
    outputDict['numDetectedPoints'], outputDict['pointCloud'] = numPoints, pointCloud


# Point Cloud Ext TLV from SDK for xWRL6432
def parsePointCloudExtTLV(tlvData, tlvLength, outputDict):
    pointCloud = outputDict['pointCloud']
    pUnitStruct = '4f2h' # Units for the 5 results to decompress them
    pointStruct = '4h2B' # x y z doppler snr noise
    pUnitSize = struct.calcsize(pUnitStruct)
    pointSize = struct.calcsize(pointStruct)

    # Parse the decompression factors
    try:
        pUnit = struct.unpack(pUnitStruct, tlvData[:pUnitSize])
    except:
            log.error('Point Cloud TLV Parser Failed')
            outputDict['numDetectedPoints'], outputDict['pointCloud'] = 0, pointCloud
    # Update data pointer
    tlvData = tlvData[pUnitSize:]

    # Parse each point
    numPoints = int((tlvLength-pUnitSize)/pointSize)
    for i in range(numPoints):
        try:
            x, y, z, doppler, snr, noise = struct.unpack(pointStruct, tlvData[:pointSize])
        except:
            numPoints = i
            log.error('Point Cloud TLV Parser Failed')
            break
        
        tlvData = tlvData[pointSize:]
        # Decompress values
        pointCloud[i,0] = x * pUnit[0]          # x
        pointCloud[i,1] = y * pUnit[0]          # y
        pointCloud[i,2] = z * pUnit[0]          # z
        pointCloud[i,3] = doppler * pUnit[1]    # Doppler
        pointCloud[i,4] = snr * pUnit[2]        # SNR
        pointCloud[i,5] = noise * pUnit[3]      # Noise
    outputDict['numDetectedPoints'], outputDict['pointCloud'] = numPoints, pointCloud

# Enhanced Presence Detection TLV from SDK
def parseEnhancedPresenceInfoTLV(tlvData, tlvLength, outputDict):
    pointStruct = '1b'  # While there are technically 2 bits per zone, we need to use at least 1 byte to represent
    pointStructSize = struct.calcsize(pointStruct)
    numZones = (tlvData[0]) # First byte in the TLV is the number of zones, the rest of it is the occupancy data
    zonePresence = [0]
    tlvData = tlvData[1:]
    zoneCount = 0
    while(zoneCount < numZones):
        try:
            idx = math.floor((zoneCount)/4)
            zonePresence.append(tlvData[idx] >> (((zoneCount) * 2) % 8) & 3)
            zoneCount = zoneCount + 1
        except:
            log.error('Enhanced Presence Detection TLV Parser Failed')
            break
    tlvData = tlvData[pointStructSize:]
    outputDict['enhancedPresenceDet'] = zonePresence

# Side info TLV from SDK
def parseSideInfoTLV(tlvData, tlvLength, outputDict):
    pointCloud = outputDict['pointCloud']
    pointStruct = '2H'  # Two unsigned shorts: SNR and Noise
    pointStructSize = struct.calcsize(pointStruct)
    numPoints = int(tlvLength/pointStructSize)

    for i in range(numPoints):
        try:
            snr, noise = struct.unpack(pointStruct, tlvData[:pointStructSize])
        except:
            numPoints = i
            log.error('Side Info TLV Parser Failed')
            break
        tlvData = tlvData[pointStructSize:]
        # SNR and Noise are sent as uint16_t which are measured in 0.1 dB Steps
        pointCloud[i,4] = snr * 0.1
        pointCloud[i,5] = noise * 0.1
    outputDict['pointCloud'] = pointCloud

# Range Profile Parser
def parseRangeProfileTLV(tlvData, tlvLength, outputDict):
    rangeProfile = []
    rangeDataStruct = 'I' # Every range bin gets a uint32_t
    rangeDataSize = struct.calcsize(rangeDataStruct)

    numRangeBins = int(len(tlvData)/rangeDataSize)
    for i in range(numRangeBins):
        # Read in single range bin data
        try:
            rangeBinData = struct.unpack(rangeDataStruct, tlvData[:rangeDataSize])
        except:
            log.error(f'Range Profile TLV Parser Failed To Parse Range Bin Number ${i}')
            break
        rangeProfile.append(rangeBinData[0])

        # Move to next value
        tlvData = tlvData[rangeDataSize:]
    outputDict['rangeProfile'] = rangeProfile

# Occupancy state machine TLV from small obstacle detection
def parseOccStateMachTLV(tlvData, tlvLength, outputDict):
    occStateMachOutput = [False] * 32 # Initialize to 32 empty zones
    occStateMachStruct = 'I' # Single uint32_t which holds 32 booleans
    occStateMachLength = struct.calcsize(occStateMachStruct)
    try:
        occStateMachData = struct.unpack(occStateMachStruct, tlvData[:occStateMachLength])
        for i in range(32):
            # Since the occupied/not occupied flags are individual bits in a uint32, mask out each flag one at a time
            occStateMachOutput[i] = ((occStateMachData[0] & (1 << i)) != 0)
    except Exception as e:
        log.error('Occupancy State Machine TLV Parser Failed')
        log.error(e)
        return None
    outputDict['occupancy'] = occStateMachOutput

# Spherical Point Cloud TLV Parser
def parseSphericalPointCloudTLV(tlvData, tlvLength, outputDict):
    pointCloud = outputDict['pointCloud']
    pointStruct = '4f'  # Range, Azimuth, Elevation, and Doppler
    pointStructSize = struct.calcsize(pointStruct)
    numPoints = int(tlvLength/pointStructSize)

    for i in range(numPoints):
        try:
            rng, azimuth, elevation, doppler = struct.unpack(pointStruct, tlvData[:pointStructSize])
        except:
            numPoints = i
            log.error('Point Cloud TLV Parser Failed')
            break
        tlvData = tlvData[pointStructSize:]
        pointCloud[i,0] = rng
        pointCloud[i,1] = azimuth
        pointCloud[i,2] = elevation
        pointCloud[i,3] = doppler
    
    # Convert from spherical to cartesian
    pointCloud[:,0:3] = sphericalToCartesianPointCloud(pointCloud[:, 0:3])
    outputDict['numDetectedPoints'], outputDict['pointCloud'] =  numPoints, pointCloud

# Point Cloud TLV from Capon Chain
def parseCompressedSphericalPointCloudTLV(tlvData, tlvLength, outputDict):
    pointCloud = outputDict['pointCloud']
    pUnitStruct = '5f' # Units for the 5 results to decompress them
    pointStruct = '2bh2H' # Elevation, Azimuth, Doppler, Range, SNR
    pUnitSize = struct.calcsize(pUnitStruct)
    pointSize = struct.calcsize(pointStruct)

    # Parse the decompression factors
    try:
        pUnit = struct.unpack(pUnitStruct, tlvData[:pUnitSize])
    except:
            log.error('Point Cloud TLV Parser Failed')
            outputDict['numDetectedPoints'], outputDict['pointCloud'] = 0, pointCloud
    # Update data pointer
    tlvData = tlvData[pUnitSize:]

    # Parse each point
    numPoints = int((tlvLength-pUnitSize)/pointSize)
    for i in range(numPoints):
        try:
            elevation, azimuth, doppler, rng, snr = struct.unpack(pointStruct, tlvData[:pointSize])
        except:
            numPoints = i
            log.error('Point Cloud TLV Parser Failed')
            break
        
        tlvData = tlvData[pointSize:]
        if (azimuth >= 128):
            log.error('Az greater than 127')
            azimuth -= 256
        if (elevation >= 128):
            log.error('Elev greater than 127')
            elevation -= 256
        if (doppler >= 32768):
            log.error('Doppler greater than 32768')
            doppler -= 65536
        # Decompress values
        pointCloud[i,0] = rng * pUnit[3]          # Range
        pointCloud[i,1] = azimuth * pUnit[1]      # Azimuth
        pointCloud[i,2] = elevation * pUnit[0]    # Elevation
        pointCloud[i,3] = doppler * pUnit[2]      # Doppler
        pointCloud[i,4] = snr * pUnit[4]          # SNR

    # Convert from spherical to cartesian
    pointCloud[:,0:3] = sphericalToCartesianPointCloud(pointCloud[:, 0:3])
    outputDict['numDetectedPoints'] = numPoints
    outputDict['pointCloud'] = pointCloud


# Decode 3D People Counting Target List TLV
# 3D Struct format
#uint32_t     tid;     /*! @brief   tracking ID */
#float        posX;    /*! @brief   Detected target X coordinate, in m */
#float        posY;    /*! @brief   Detected target Y coordinate, in m */
#float        posZ;    /*! @brief   Detected target Z coordinate, in m */
#float        velX;    /*! @brief   Detected target X velocity, in m/s */
#float        velY;    /*! @brief   Detected target Y velocity, in m/s */
#float        velZ;    /*! @brief   Detected target Z velocity, in m/s */
#float        accX;    /*! @brief   Detected target X acceleration, in m/s2 */
#float        accY;    /*! @brief   Detected target Y acceleration, in m/s2 */
#float        accZ;    /*! @brief   Detected target Z acceleration, in m/s2 */
#float        ec[16];  /*! @brief   Target Error covariance matrix, [4x4 float], in row major order, range, azimuth, elev, doppler */
#float        g;
#float        confidenceLevel;    /*! @brief   Tracker confidence metric*/
def parseTrackTLV(tlvData, tlvLength, outputDict):
    targetStruct = 'I27f'
    targetSize = struct.calcsize(targetStruct)
    numDetectedTargets = int(tlvLength/targetSize)
    targets = np.empty((numDetectedTargets,16))
    for i in range(numDetectedTargets):
        try:
            targetData = struct.unpack(targetStruct,tlvData[:targetSize])
        except:
            log.error('Target TLV parsing failed')
            outputDict['numDetectedTracks'], outputDict['trackData'] = 0, targets

        targets[i,0] = targetData[0] # Target ID
        targets[i,1] = targetData[1] # X Position
        targets[i,2] = targetData[2] # Y Position
        targets[i,3] = targetData[3] # Z Position
        targets[i,4] = targetData[4] # X Velocity
        targets[i,5] = targetData[5] # Y Velocity
        targets[i,6] = targetData[6] # Z Velocity
        targets[i,7] = targetData[7] # X Acceleration
        targets[i,8] = targetData[8] # Y Acceleration
        targets[i,9] = targetData[9] # Z Acceleration
        targets[i,10] = targetData[26] # G
        targets[i,11] = targetData[27] # Confidence Level
        
        # Throw away EC
        tlvData = tlvData[targetSize:]
    outputDict['numDetectedTracks'], outputDict['trackData'] = numDetectedTargets, targets

# Decode 2D People Counting Target List TLV
# 2D Struct format
#uint32_t     tid;     /*! @brief   tracking ID */
#float        posX;    /*! @brief   Detected target X coordinate, in m */
#float        posY;    /*! @brief   Detected target Y coordinate, in m */
#float        velX;    /*! @brief   Detected target X velocity, in m/s */
#float        velY;    /*! @brief   Detected target Y velocity, in m/s */
#float        accX;    /*! @brief   Detected target X acceleration, in m/s2 */
#float        accY;    /*! @brief   Detected target Y acceleration, in m/s2 */
#float        ec[9];  /*! @brief   Target Error covariance matrix, [3x3 float], in row major order, range, azimuth, elev, doppler */
#float        g;
#float        confidenceLevel;    /*! @brief   Tracker confidence metric*/
def parseTrackTLV2D(tlvData, tlvLength, outputDict):
    targetStruct = 'I17f'
    targetSize = struct.calcsize(targetStruct)
    numDetectedTargets = int(tlvLength/targetSize)
    targets = np.empty((numDetectedTargets,16))
    for i in range(numDetectedTargets):
        try:
            targetData = struct.unpack(targetStruct,tlvData[:targetSize])
        except:
            log.error('Target TLV parsing failed')
            outputDict['numDetectedTracks'], outputDict['trackData'] = 0, targets

        targets[i,0] = targetData[0] # Target ID
        targets[i,1] = targetData[1] # X Position
        targets[i,2] = targetData[2] # Y Position
        targets[i,3] = targetData[3] # X Velocity
        targets[i,4] = targetData[4] # Y Velocity
        targets[i,5] = targetData[5] # X Acceleration
        targets[i,6] = targetData[6] # Y Acceleration
        targets[i,7] = targetData[16] # G
        targets[i,8] = targetData[17] # Confidence Level
        
        # Throw away EC
        tlvData = tlvData[targetSize:]
    outputDict['numDetectedTracks'], outputDict['trackData'] = numDetectedTargets, targets

# Track heights
def parseTrackHeightTLV(tlvData, tlvLength, outputDict):
    targetStruct = 'I2f' #incoming data is an unsigned integer for TID, followed by 2 floats
    targetSize = struct.calcsize(targetStruct)
    numDetectedHeights = int(tlvLength/targetSize)
    heights = np.empty((numDetectedHeights,3))
    for i in range(numDetectedHeights):
        try:
            targetData = struct.unpack(targetStruct,tlvData[i * targetSize:(i + 1) * targetSize])
        except:
            log.error('Target TLV parsing failed')
            outputDict['numDetectedHeights'], outputDict['heightData'] = 0, heights

        heights[i,0] = targetData[0] # Target ID
        heights[i,1] = targetData[1] # maxZ
        heights[i,2] = targetData[2] # minZ

    outputDict['numDetectedHeights'], outputDict['heightData'] = numDetectedHeights, heights

def parseCamTLV(tlvData, tlvLength, outputDict):
    targetStruct = '4I'
    targetSize = struct.calcsize(targetStruct)
    camData = struct.unpack(targetStruct, tlvData)

    # bits set in this field = which tracks are currently active
    numTracks = bin(camData[0]).count("1")

    camDataDict = {}
    activeTracks = []
    for j in range(32):
        if( not camData[0] & (0b1<< j) == 0):
            activeTracks.append(j)

    # iterate through the active tracks we have and set bits for triggering cam, etc.
    for activeTrack in activeTracks:
        camDataArr = np.empty(4)

        # camData[0] = track the list is associated with
        camDataArr[0] = activeTrack

        # Tracks data is bit shifted to denote which tracks are active:
        # example: 00000001 = track 1 is active
        # example: 00000010 = track 2 is active
        # example: 00000100 = track 3 is active
        # and so on...

        # unshifting status bits to determine status

        camDataArr[1] = True if (not (camData[1] & (0b1 << activeTrack) == 0 )) else False
        camDataArr[2] = True if (not (camData[2] & (0b1 << activeTrack) == 0 )) else False
        camDataArr[3] = True if (not (camData[3] & (0b1 << activeTrack) == 0 )) else False

        camDataDict.update({activeTrack: camDataArr})
            
    outputDict['camDataDict'] = camDataDict

# Decode Target Index TLV
def parseTargetIndexTLV(tlvData, tlvLength, outputDict):
    indexStruct = 'B' # One byte per index
    indexSize = struct.calcsize(indexStruct)
    numIndexes = int(tlvLength/indexSize)
    indexes = np.empty(numIndexes)
    for i in range(numIndexes):
        try:
            index = struct.unpack(indexStruct, tlvData[:indexSize])
        except:
            log.error('Target Index TLV Parsing Failed')
            outputDict['trackIndexes'] = indexes
        indexes[i] = int(index[0])
        tlvData = tlvData[indexSize:]
    outputDict['trackIndexes'] = indexes

# Vital Signs
def parseVitalSignsTLV (tlvData, tlvLength, outputDict):
    vitalsStruct = '2H33f'
    vitalsSize = struct.calcsize(vitalsStruct)
    
    # Initialize struct in case of error
    vitalsOutput = {}
    vitalsOutput ['id'] = 999
    vitalsOutput ['rangeBin'] = 0
    vitalsOutput ['breathDeviation'] = 0
    vitalsOutput ['heartRate'] = 0
    vitalsOutput ['breathRate'] = 0
    vitalsOutput ['heartWaveform'] = []
    vitalsOutput ['breathWaveform'] = []

    # Capture data for active patient
    try:
        vitalsData = struct.unpack(vitalsStruct, tlvData[:vitalsSize])
    except:
        log.error('ERROR: Vitals TLV Parsing Failed')
        outputDict['vitals'] = vitalsOutput
    
    # Parse this patient's data
    vitalsOutput ['id'] = vitalsData[0]
    vitalsOutput ['rangeBin'] = vitalsData[1]
    vitalsOutput ['breathDeviation'] = vitalsData[2]
    vitalsOutput ['heartRate'] = vitalsData[3]
    vitalsOutput ['breathRate'] = vitalsData [4]
    vitalsOutput ['heartWaveform'] = np.asarray(vitalsData[5:20])
    vitalsOutput ['breathWaveform'] = np.asarray(vitalsData[20:35])

    # Advance tlv data pointer to end of this TLV
    tlvData = tlvData[vitalsSize:]
    outputDict['vitals'] = vitalsOutput

# Classifier
def parseClassifierTLV(tlvData, tlvLength, outputDict):
    classifierProbabilitiesStruct = str(NUM_CLASSES_IN_CLASSIFIER) + 'c'
    classifierProbabilitiesSize = struct.calcsize(classifierProbabilitiesStruct)
    numDetectedTargets = int(tlvLength/classifierProbabilitiesSize)
    outputProbabilities = np.empty((numDetectedTargets,NUM_CLASSES_IN_CLASSIFIER))
    for i in range(numDetectedTargets):
        try:
            classifierProbabilities = struct.unpack(classifierProbabilitiesStruct,tlvData[:classifierProbabilitiesSize])
        except:
            log.error('Classifier TLV parsing failed')
            outputDict['classifierOutput'] = 0
        
        for j in range(NUM_CLASSES_IN_CLASSIFIER):
            outputProbabilities[i,j] = float(ord(classifierProbabilities[j])) / 128
        # Throw away EC
        tlvData = tlvData[classifierProbabilitiesSize:]
    outputDict['classifierOutput'] = outputProbabilities

# Extracted features for 6843 Gesture Demo
def parseGestureFeaturesTLV(tlvData, tlvLength, outputDict):
    featuresStruct = '10f'  
    featuresStructSize = struct.calcsize(featuresStruct)
    gestureFeatures = []

    try:
        wtDoppler, wtDopplerPos, wtDopplerNeg, wtRange, numDetections, wtAzimuthMean, wtElevMean, azDoppCorr, wtAzimuthStd, wtdElevStd = struct.unpack(featuresStruct, tlvData[:featuresStructSize])
        gestureFeatures = [wtDoppler, wtDopplerPos, wtDopplerNeg, wtRange, numDetections, wtAzimuthMean, wtElevMean, azDoppCorr, wtAzimuthStd, wtdElevStd]
    except:
        log.error('Gesture Features TLV Parser Failed')
        return None

    outputDict['features'] = gestureFeatures

# Raw ANN Probabilities TLV for 6843 Gesture Demo
def parseGestureProbTLV6843(tlvData, tlvLength, outputDict):
    probStruct = '10f'
    probStructSize = struct.calcsize(probStruct)

    try:
        annOutputProb = struct.unpack(probStruct, tlvData[:probStructSize])
    except:
        log.error('ANN Probabilities TLV Parser Failed')
        return None

    outputDict['gestureNeuralNetProb'] = annOutputProb

# 6432 Gesture demo features
def parseGestureFeaturesTLV6432(tlvData, tlvLength, outputDict):
    featuresStruct = '16f'
    featuresStructSize = struct.calcsize(featuresStruct)
    gestureFeatures = []

    try:
        gestureFeatures = struct.unpack(featuresStruct, tlvData[:featuresStructSize])
    except:
        log.error('Gesture Features TLV Parser Failed')
        return None
    
    outputDict['gestureFeatures'] =  gestureFeatures

# Detected gesture
def parseGestureClassifierTLV6432(tlvData, tlvLength, outputDict):
    classifierStruct = '1b'
    classifierStructSize = struct.calcsize(classifierStruct)
    classifier_result = 0

    try:
        classifier_result = struct.unpack(classifierStruct, tlvData[:classifierStructSize])
    except:
        log.error('Classifier Result TLV Parser Failed')
        return None

    outputDict['gesture'] = classifier_result[0]
    outputDict['ktoGesture'] = classifier_result[0]

# Mode in Gesture/KTO demo 
def parseGesturePresenceTLV6432(tlvData, tlvLength, outputDict):
    presenceStruct = '1b'
    presenceStructSize = struct.calcsize(presenceStruct)
    presence_result = 0

    try:
        presence_result = struct.unpack(presenceStruct, tlvData[:presenceStructSize])
    except:
        log.error('Gesture Presence Result TLV Parser Failed')
        return None

    outputDict['gesturePresence'] = presence_result[0]

def parsePresenceThreshold(tlvData, tlvLength, outputDict):
    threshStruct = '1I'
    threshStructSize = struct.calcsize(threshStruct)

    try: 
        presenceThreshold = struct.unpack(threshStruct, tlvData[:threshStructSize])
        # print('Parsing Threshold: ', presenceThreshold)
    except: 
        log.error('Presence Threshold Parse Failed')
        return 0
    
    outputDict['presenceThreshold'] = presenceThreshold[0]

# Surface Classification
def parseSurfaceClassificationTLV(tlvData, tlvLength, outputDict):
    classifierStruct = '1f'
    classifierStructSize = struct.calcsize(classifierStruct)
    classifier_result = 0

    try:
        classifier_result = struct.unpack(classifierStruct, tlvData[:classifierStructSize])
    except:
        log.error('Classifier Result TLV Parser Failed')
        return None

    outputDict['surfaceClassificationOutput'] = classifier_result[0]

def parseVelocityTLV(tlvData, tlvLength, outputDict):
    velocity = []
    valid = False
    try:
        tempVel, tempConf = struct.unpack('1f1?', tlvData[:struct.calcsize('1f1?')])
        velocity.append(tuple((tempVel, tempConf)))
    except:
        velocity = []
        print('Error: Velocity TLV Parser Failed')
    outputDict['velocity'] = velocity

def parseRXChanCompTLV(tlvData, tlvLength, outputDict):
    compStruct = '13f' # One byte per index
    compSize = struct.calcsize(compStruct)
    coefficients = np.empty(compSize)
    try:
        coefficients = struct.unpack(compStruct, tlvData[:compSize])
    except:
        log.error('RX Channel Comp TLV Parsing Failed')

    outputDict['RXChanCompInfo'] = coefficients

# Statistics
def parseExtStatsTLV(tlvData, tlvLength, outputDict):
    extStatsStruct = '2I8H' # Units for the 5 results to decompress them
    extStatsStructSize = struct.calcsize(extStatsStruct)
    # Parse the decompression factors
    try:
        interFrameProcTime, transmitOutTime, power1v8, power3v3, \
        power1v2, power1v2RF, tempRx, tempTx, tempPM, tempDIG = \
        struct.unpack(extStatsStruct, tlvData[:extStatsStructSize])
    except:
            log.error('Ext Stats Parser Failed')
            return 0

    tlvData = tlvData[extStatsStructSize:]

    procTimeData = {}
    powerData = {}
    tempData = {}

    procTimeData['interFrameProcTime'] = interFrameProcTime
    procTimeData['transmitOutTime'] = transmitOutTime

    powerData['power1v8'] = power1v8
    powerData['power3v3'] = power3v3
    powerData['power1v2'] = power1v2
    powerData['power1v2RF'] = power1v2RF

    tempData['tempRx'] = tempRx
    tempData['tempTx'] = tempTx
    tempData['tempPM'] = tempPM
    tempData['tempDIG'] = tempDIG

    outputDict['procTimeData'], outputDict['powerData'], outputDict['tempData'] = procTimeData, powerData, tempData


# Statistics
def parseExtStatsTLVBSD(tlvData, tlvLength, outputDict):
    extStatsStruct = '2I8H2f' # Units for the 5 results to decompress them
    extStatsStructSize = struct.calcsize(extStatsStruct)
    # Parse the decompression factors
    try:
        interFrameProcTime, transmitOutTime, power1v8, power3v3, \
        power1v2, power1v2RF, tempRx, tempTx, tempPM, tempDIG, egoSpeed, alphaAngle = \
        struct.unpack(extStatsStruct, tlvData[:extStatsStructSize])
    except:
            log.error('Ext Stats Parser Failed')
            return 0

    tlvData = tlvData[extStatsStructSize:]

    procTimeData = {}
    powerData = {}
    tempData = {}

    procTimeData['interFrameProcTime'] = interFrameProcTime
    procTimeData['transmitOutTime'] = transmitOutTime

    powerData['power1v8'] = power1v8
    powerData['power3v3'] = power3v3
    powerData['power1v2'] = power1v2
    powerData['power1v2RF'] = power1v2RF

    tempData['tempRx'] = tempRx
    tempData['tempTx'] = tempTx
    tempData['tempPM'] = tempPM
    tempData['tempDIG'] = tempDIG

    outputDict['procTimeData'], outputDict['powerData'], outputDict['tempData'] = procTimeData, powerData, tempData
