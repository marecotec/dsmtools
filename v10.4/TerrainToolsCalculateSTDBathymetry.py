#!/usr/bin/env python
import arcpy
import os
from arcpy.sa import *

arcpy.CheckOutExtension("Spatial")

class TerrainToolsCalculateSTDBathymetry(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate the Standard Deviation of a Bathymetry"
        self.description = """# Equation taken from http://gis4geomorphology.com/roughness-topographic-position/
        Standard deviation of slope is a measure of topographic roughness (Ascione et al., 2008).
        """
        self.canRunInBackground = True
        self.category = "Terrain Tools"  # Use your own category here, or an existing one.

    def getParameterInfo(self):
        params = []

        input_bathymetry = arcpy.Parameter(name="input_bathymetry",
                                       displayName="Input Bathymetry Raster",
                                       datatype="DERasterDataset",
                                       parameterType="Required",
                                       direction="Input",
                                       )
        input_bathymetry.value = "D:\Example\TerrainToolsCalculateSTDBathymetry\depth"
        params.append(input_bathymetry)

        output_directory = arcpy.Parameter(name="output_directory",
                                       displayName="Output Directory",
                                       datatype="DEWorkspace",
                                       parameterType="Required",
                                       direction="Output",
                                       )
        output_directory.value = "D:\Example\TerrainToolsCalculateSTDBathymetry\Output\/"
        params.append(output_directory)

        focal_neighbourhood = arcpy.Parameter(name="focal_neighbourhood",
                                           displayName="Focal Neighbourhood",
                                           datatype="GPSANeighborhood",
                                           parameterType="Required",
                                           direction="Output",
                                           )
        focal_neighbourhood.value = "Rectangle 3 3 CELL"
        params.append(focal_neighbourhood)

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    #def updateParameters(self, parameters):

        #return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of your tool."""
        arcpy.env.overwriteOutput = True

        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )

        input_bathymetry = parameters[0].valueAsText
        output_directory = parameters[1].valueAsText
        focal_neighbourhood = parameters[2].valueAsText

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        arcpy.AddMessage("Calculating standard deviation of bathymetry from " + str(input_bathymetry) + ".")

        meandem = FocalStatistics(input_bathymetry, focal_neighbourhood, "mean", "DATA")
        rangedem = FocalStatistics(input_bathymetry, focal_neighbourhood, "range", "DATA")

        stdevelv = (meandem - input_bathymetry) / rangedem
        stdevelv_n = IsNull(stdevelv)
        stdevelv_n1 = Con(stdevelv_n, "0", stdevelv, "VALUE = 1")
        stdevelv_n1.save(os.path.join(output_directory, "std_depth"))

        return


def main():
    tool = TerrainToolsCalculateSTDBathymetry()
    tool.execute(tool.getParameterInfo(), None)

if __name__ == '__main__':
    main()
