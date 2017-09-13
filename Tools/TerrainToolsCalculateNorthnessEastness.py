#!/usr/bin/env python
import os
import arcpy
from arcpy import env
from arcpy.sa import *


class TerrainToolsCalculateNorthnessEastness(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate northness and eastness from a slope raster"
        self.description = """Calculate northness and eastness from a slope raster"""
        self.canRunInBackground = True
        self.category = "Terrain Tools"  # Use your own category here, or an existing one.

    def getParameterInfo(self):

        arcpy.env.overwriteOutput = True
        # Check out the ArcGIS Spatial Analyst extension license
        arcpy.CheckOutExtension("Spatial")

        params = []

        input_slope = arcpy.Parameter(name="input_slope",
                                       displayName="Input Slope Raster (degrees)",
                                       datatype="DERasterDataset",
                                       parameterType="Required",
                                       direction="Input",
                                       )
        input_slope.value = "D:\Example\TerrainToolsCalculateNorthnessEastness\slope_deg"
        params.append(input_slope)

        output_directory = arcpy.Parameter(name="output_directory",
                                       displayName="Output Directory",
                                       datatype="DEWorkspace",
                                       parameterType="Required",
                                       direction="Output",
                                       )
        params.append(output_directory)
        output_directory.value = "D:\Example\TerrainToolsCalculateNorthnessEastness\Output\/"
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

        arcpy.AddMessage("Calculate northness and eastness from a slope raster")

        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )

        input_slope = parameters[0].valueAsText
        output_directory = parameters[1].valueAsText

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # Set environment settings
        env.workspace = output_directory

        arcpy.AddMessage("Converting " + str(input_slope) + ".")

        constant = 0.0174444444444

        convRadians = Times(input_slope, constant)
        outCos = Cos(convRadians)
        outSin = Sin(convRadians)
        outCos.save(os.path.join(output_directory, "northness"))
        outSin.save(os.path.join(output_directory, "eastness"))

        return


def main():
    tool = TerrainToolsCalculateNorthnessEastness()
    tool.execute(tool.getParameterInfo(), None)

if __name__ == '__main__':
    main()
# That's all!
