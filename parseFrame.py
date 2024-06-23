import struct
import logging
import sys
import numpy as np
import math
import os
import datetime

# Local File Imports
from parseTLVs import *
from gui_common import *
from tlv_defines import *

log = logging.getLogger(__name__)

parserFunctions = {
    MMWDEMO_OUTPUT_MSG_DETECTED_POINTS:                     parsePointCloudTLV,
    MMWDEMO_OUTPUT_MSG_RANGE_PROFILE:                       parseRangeProfileTLV,
    MMWDEMO_OUTPUT_EXT_MSG_RANGE_PROFILE_MAJOR:             parseRangeProfileTLV,
    MMWDEMO_OUTPUT_EXT_MSG_RANGE_PROFILE_MINOR:             parseRangeProfileTLV,
    MMWDEMO_OUTPUT_MSG_DETECTED_POINTS_SIDE_INFO:           parseSideInfoTLV,
    MMWDEMO_OUTPUT_MSG_SPHERICAL_POINTS:                    parseSphericalPointCloudTLV,
    MMWDEMO_OUTPUT_MSG_TRACKERPROC_3D_TARGET_LIST:          parseTrackTLV,
    MMWDEMO_OUTPUT_EXT_MSG_TARGET_LIST:                     parseTrackTLV,
    MMWDEMO_OUTPUT_MSG_TRACKERPROC_TARGET_HEIGHT:           parseTrackHeightTLV,
    MMWDEMO_OUTPUT_MSG_TRACKERPROC_TARGET_INDEX:            parseTargetIndexTLV,
    MMWDEMO_OUTPUT_EXT_MSG_TARGET_INDEX:                    parseTargetIndexTLV,
    MMWDEMO_OUTPUT_MSG_COMPRESSED_POINTS:                   parseCompressedSphericalPointCloudTLV,
    MMWDEMO_OUTPUT_MSG_OCCUPANCY_STATE_MACHINE:             parseOccStateMachTLV,
    MMWDEMO_OUTPUT_MSG_VITALSIGNS:                          parseVitalSignsTLV,
    MMWDEMO_OUTPUT_EXT_MSG_DETECTED_POINTS:                 parsePointCloudExtTLV,
    MMWDEMO_OUTPUT_MSG_GESTURE_FEATURES_6843:               parseGestureFeaturesTLV,
    MMWDEMO_OUTPUT_MSG_GESTURE_OUTPUT_PROB_6843:            parseGestureProbTLV6843,
    MMWDEMO_OUTPUT_MSG_GESTURE_CLASSIFIER_6432:             parseGestureClassifierTLV6432,
    MMWDEMO_OUTPUT_EXT_MSG_ENHANCED_PRESENCE_INDICATION:    parseEnhancedPresenceInfoTLV,
    MMWDEMO_OUTPUT_EXT_MSG_CLASSIFIER_INFO:                 parseClassifierTLV,
    MMWDEMO_OUTPUT_MSG_SURFACE_CLASSIFICATION:              parseSurfaceClassificationTLV,
    MMWDEMO_OUTPUT_EXT_MSG_VELOCITY:                        parseVelocityTLV,
    MMWDEMO_OUTPUT_EXT_MSG_RX_CHAN_COMPENSATION_INFO:       parseRXChanCompTLV,
    MMWDEMO_OUTPUT_MSG_EXT_STATS:                           parseExtStatsTLV,
    MMWDEMO_OUTPUT_MSG_GESTURE_FEATURES_6432:               parseGestureFeaturesTLV6432,
    MMWDEMO_OUTPUT_MSG_GESTURE_PRESENCE_x432:               parseGesturePresenceTLV6432,
    MMWDEMO_OUTPUT_MSG_GESTURE_PRESENCE_THRESH_x432:        parsePresenceThreshold,
    MMWDEMO_OUTPUT_EXT_MSG_STATS_BSD:                       parseExtStatsTLVBSD,
    MMWDEMO_OUTPUT_EXT_MSG_TARGET_LIST_2D_BSD:              parseTrackTLV2D,
    MMWDEMO_OUTPUT_EXT_MSG_CAM_TRIGGERS:                    parseCamTLV
}

unusedTLVs = [
    MMWDEMO_OUTPUT_MSG_NOISE_PROFILE,
    MMWDEMO_OUTPUT_MSG_AZIMUT_STATIC_HEAT_MAP,
    MMWDEMO_OUTPUT_MSG_RANGE_DOPPLER_HEAT_MAP,
    MMWDEMO_OUTPUT_MSG_STATS,
    MMWDEMO_OUTPUT_MSG_AZIMUT_ELEVATION_STATIC_HEAT_MAP,
    MMWDEMO_OUTPUT_MSG_TEMPERATURE_STATS,
    MMWDEMO_OUTPUT_MSG_PRESCENCE_INDICATION,
    MMWDEMO_OUTPUT_MSG_GESTURE_PRESENCE_x432,
    MMWDEMO_OUTPUT_MSG_GESTURE_PRESENCE_THRESH_x432,
    MMWDEMO_OUTPUT_EXT_MSG_MICRO_DOPPLER_RAW_DATA,
    MMWDEMO_OUTPUT_EXT_MSG_MICRO_DOPPLER_FEATURES,
    MMWDEMO_OUTPUT_EXT_MSG_QUICK_EVAL_INFO
]

def parseStandardFrame(frameData):
    # Constants for parsing frame header
    headerStruct = 'Q8I'
    frameHeaderLen = struct.calcsize(headerStruct)
    tlvHeaderLength = 8

    # Define the function's output structure and initialize error field to no error
    outputDict = {}
    outputDict['error'] = 0

    # A sum to track the frame packet length for verification for transmission integrity 
    totalLenCheck = 0   

    # Read in frame Header
    try:
        magic, version, totalPacketLen, platform, frameNum, timeCPUCycles, numDetectedObj, numTLVs, subFrameNum = struct.unpack(headerStruct, frameData[:frameHeaderLen])
    except:
        log.error('Error: Could not read frame header')
        outputDict['error'] = 1

    # Move frameData ptr to start of 1st TLV   
    frameData = frameData[frameHeaderLen:]
    totalLenCheck += frameHeaderLen

    # Save frame number to output
    outputDict['frameNum'] = frameNum

    # Initialize the point cloud struct since it is modified by multiple TLV's
    # Each point has the following: X, Y, Z, Doppler, SNR, Noise, Track index
    outputDict['pointCloud'] = np.zeros((numDetectedObj, 7), np.float64)
    # Initialize the track indexes to a value which indicates no track
    outputDict['pointCloud'][:, 6] = 255
    # Find and parse all TLV's
    for i in range(numTLVs):
        try:
            tlvType, tlvLength = tlvHeaderDecode(frameData[:tlvHeaderLength])
            frameData = frameData[tlvHeaderLength:]
            totalLenCheck += tlvHeaderLength
        except:
            log.warning('TLV Header Parsing Failure: Ignored frame due to parsing error')
            outputDict['error'] = 2
            return {}

        # print(tlvType)

        if (tlvType in parserFunctions):
            parserFunctions[tlvType](frameData[:tlvLength], tlvLength, outputDict)
        elif (tlvType in unusedTLVs):
            log.debug("No function to parse TLV type: %d" % (tlvType))
        else:
            log.info("Invalid TLV type: %d" % (tlvType))

        # Move to next TLV
        frameData = frameData[tlvLength:]
        totalLenCheck += tlvLength
    
    # Pad totalLenCheck to the next largest multiple of 32
    # since the device does this to the totalPacketLen for transmission uniformity
    totalLenCheck = 32 * math.ceil(totalLenCheck / 32)

    # Verify the total packet length to detect transmission error that will cause subsequent frames to dropped
    if (totalLenCheck != totalPacketLen):
        log.warning('Frame packet length read is not equal to totalPacketLen in frame header. Subsequent frames may be dropped.')
        outputDict['error'] = 3

    return outputDict

# Decode TLV Header
def tlvHeaderDecode(data):
    tlvType, tlvLength = struct.unpack('2I', data)
    return tlvType, tlvLength

