# General Library Imports
# PyQt Imports
# Local Imports
# Logger
from Demo_Classes.people_tracking import PeopleTracking

import string

class SmallObstacle(PeopleTracking):
    def __init__(self):
        PeopleTracking.__init__(self)

    def updateGraph(self, outputDict):
        super().updateGraph(outputDict)

        # Update boundary box colors based on results of Occupancy State Machine
        occupancyStates = outputDict['occupancy']
        if (occupancyStates is not None):
            for box in self.boundaryBoxViz:
                if ('occZone' in box['name']):
                    # Get index of the occupancy zone from the box name
                    occIdx = int(box['name'].lstrip(string.ascii_letters))
                    # Zone unoccupied 
                    if (occIdx >= len(occupancyStates) or not occupancyStates[occIdx]):
                        self.changeBoundaryBoxColor(box, 'g')
                    # Zone occupied
                    else:
                        # Make first box turn red
                        if (occIdx == 0):
                            self.changeBoundaryBoxColor(box, 'r')
                        else:
                            self.changeBoundaryBoxColor(box, 'y')
