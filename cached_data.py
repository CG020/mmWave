# General Library Imports
from os.path import exists
from os import mkdir

# Logger
import logging
log = logging.getLogger(__name__)

class CachedDataType:
    def __init__(self):
        self.cachedDemoName = ""
        self.cachedCfgPath = ""
        self.cachedDeviceName = ""

        try:
            if(exists("cache\cachedData.txt")):
                configCacheFile = open("cache\cachedData.txt", 'r')
                lines = configCacheFile.readlines()
                self.cachedDeviceName = lines[0][0:-1]
                self.cachedDemoName = lines[1][0:-1]
                self.cachedCfgPath = lines[2]
                configCacheFile.close()
        except:
            log.warning("Missing some or all of cached data")

    def writeToFile(self):
        if not exists("cache"):
        # Note that this will create the folder in the caller's path, not necessarily in the Industrial Viz Folder
            mkdir("cache")
        configCacheFile = open("cache\cachedData.txt", 'w')
        configCacheFile.write(self.cachedDeviceName + '\n')
        configCacheFile.write(self.cachedDemoName + '\n')
        configCacheFile.write(self.cachedCfgPath)
        configCacheFile.close()

    def getCachedDeviceName(self):
        return self.cachedDeviceName

    def getCachedDemoName(self):
        return self.cachedDemoName

    def getCachedCfgPath(self):
        return self.cachedCfgPath

    def setCachedDemoName(self, newDemo):
        self.cachedDemoName = newDemo
        self.writeToFile()

    def setCachedDeviceName(self, newDevice):
        self.cachedDeviceName = newDevice
        self.writeToFile()

    def setCachedCfgPath(self, newPath):
        self.cachedCfgPath = newPath
        self.writeToFile()

