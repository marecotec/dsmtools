#!/usr/bin/env python
import arcpy
import os
from arcpy.sa import *

arcpy.CheckOutExtension("Spatial")

class TerrainToolsCalculateSlopeVariability(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate the variability of slope"
        self.description = """# Equation taken from http://gis4geomorphology.com/roughness-topographic-position/
        Slope Variability, Best calculated using a slope raster and a relatively large roving window (>100m),
        slope variability (SV = Smax - Smin) is a measure of the relief of slope of a landscape
        (Ruszkiczay-Rudiger et al., 2009).
        """
        self.canRunInBackground = True
        self.category = "Terrain Tools"  # Use your own category here, or an existing one.

    def getParameterInfo(self):
        params = []

        input_slope = arcpy.Parameter(name="input_slope",
                                       displayName="Input Slope Raster",
                                       datatype="DERasterDataset",
                                       parameterType="Required",
                                       direction="Input",
                                       )
        input_slope.value = "D:\Example\TerrainToolsCalculateSlopeVariability\slope_deg"
        params.append(input_slope)

        output_directory = arcpy.Parameter(name="output_directory",
                                       displayName="Output Directory",
                                       datatype="DEWorkspace",
                                       parameterType="Required",
                                       direction="Output",
                                       )
        output_directory.value = "D:\Example\TerrainToolsCalculateSlopeVariability\/"
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

        input_slope = parameters[0].valueAsText
        output_directory = parameters[1].valueAsText
        focal_neighbourhood = parameters[2].valueAsText

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        Smax = FocalStatistics(input_slope, focal_neighbourhood, "MAXIMUM", "DATA")
        Smin = FocalStatistics(input_slope, focal_neighbourhood, "MINIMUM", "DATA")

        slopevar = (Smax - Smin)
        slopevar.save(os.path.join(output_directory, "var_slope"))

        return


def main():
    tool = TerrainToolsCalculateSlopeVariability()
    tool.execute(tool.getParameterInfo(), None)

if __name__ == '__main__':
    main()
