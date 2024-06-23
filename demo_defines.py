# OOB demo names must be different
DEMO_OOB_x843 = 'x843 Out of Box Demo'
DEMO_OOB_x432 = 'x432 Out of Box Demo'

DEMO_3D_PEOPLE_TRACKING = '3D People Tracking'
DEMO_VITALS = 'Vital Signs with People Tracking'
DEMO_LONG_RANGE = 'Long Range People Detection'
DEMO_MOBILE_TRACKER = 'Mobile Tracker'
DEMO_SMALL_OBSTACLE = 'Small Obstacle Detection'
DEMO_GESTURE = 'Gesture Recognition'
DEMO_SURFACE = 'Surface Classification'
DEMO_LEVEL_SENSING = 'Level Sensing'
DEMO_GROUND_SPEED = 'True Ground Speed'
DEMO_KTO = 'Kick to Open'
DEMO_CALIBRATION = 'Calibration'
DEMO_DASHCAM = 'Exterior Intrusion Monitoring'
DEMO_EBIKES = 'Bike Radar'

# Com Port names
CLI_XDS_SERIAL_PORT_NAME = 'XDS110 Class Application/User UART'
DATA_XDS_SERIAL_PORT_NAME = 'XDS110 Class Auxiliary Data Port'
CLI_SIL_SERIAL_PORT_NAME = 'Enhanced COM Port'
DATA_SIL_SERIAL_PORT_NAME = 'Standard COM Port'

BUSINESS_DEMOS = {
    "Industrial": [
        DEMO_OOB_x843, DEMO_OOB_x432, DEMO_3D_PEOPLE_TRACKING, DEMO_VITALS, DEMO_LONG_RANGE, DEMO_MOBILE_TRACKER, DEMO_SMALL_OBSTACLE, 
        DEMO_GESTURE, DEMO_SURFACE, DEMO_LEVEL_SENSING, DEMO_GROUND_SPEED, DEMO_CALIBRATION, DEMO_EBIKES
    ],
    "BAC": [
        DEMO_OOB_x843, DEMO_OOB_x432, DEMO_3D_PEOPLE_TRACKING, DEMO_GESTURE, DEMO_KTO, DEMO_CALIBRATION, DEMO_DASHCAM
    ]
}


# Populated with all devices and the demos each of them can run
DEVICE_DEMO_DICT = {
    "xWR6843": {
        "isxWRx843": True,
        "isxWRLx432": False,
        "singleCOM": False,
        "demos": [DEMO_OOB_x843, DEMO_3D_PEOPLE_TRACKING, DEMO_SMALL_OBSTACLE, DEMO_GESTURE, DEMO_SURFACE, DEMO_LONG_RANGE, DEMO_MOBILE_TRACKER, DEMO_VITALS]
    },
    "xWR1843": {
        "isxWRx843": True,
        "isxWRLx432": False,
        "singleCOM": False,
        "demos": [DEMO_OOB_x843, DEMO_3D_PEOPLE_TRACKING, DEMO_GESTURE, DEMO_SURFACE, DEMO_LONG_RANGE, DEMO_MOBILE_TRACKER]
    },
    "xWRL6432": {
        "isxWRx843": False,
        "isxWRLx432": True,
        "singleCOM": True,
        "demos": [DEMO_OOB_x432, DEMO_LEVEL_SENSING, DEMO_GESTURE, DEMO_SURFACE, DEMO_GROUND_SPEED, DEMO_SMALL_OBSTACLE, DEMO_KTO, DEMO_CALIBRATION, DEMO_VITALS, DEMO_DASHCAM]
    },
    "xWRL1432": {
        "isxWRx843": False,
        "isxWRLx432": True,
        "singleCOM": True,
        "demos": [DEMO_OOB_x432, DEMO_LEVEL_SENSING, DEMO_GROUND_SPEED, DEMO_KTO, DEMO_CALIBRATION, DEMO_DASHCAM, DEMO_EBIKES]
    }
}
