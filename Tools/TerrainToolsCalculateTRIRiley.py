#!/usr/bin/env python
import arcpy
import os
from arcpy.sa import *


class TerrainToolsCalculateTRIRiley(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate Terrain Ruggedness Index (Riley)"
        self.description = """Calculate Terrain Ruggedness Index (Riley), with equation obtained from
        http://gis4geomorphology.com/roughness-topographic-position/. Terrain Ruggedness Index (TRI)
        is the difference between the value of a cell and the mean of an 8-cell neighborhood of
        surrounding cells. First create the two input neighborhood rasters from a DEM (use a 3x3
        neighborhood for min and max), then run the equation in Raster Calculator. Syntax matters.
        Classify the resulting ruggedness index values using the categories of Riley et al. (1999).
        If not the life of Riley, at least his landscape. Your particular DEM may not yield the
        full range of values possible (fewer ruggedness categories may result)."""
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
        input_bathymetry.value = "D:\Example\TerrainToolsCalculateTRIRiley\depth"
        params.append(input_bathymetry)

        output_directory = arcpy.Parameter(name="output_directory",
                                       displayName="Output Directory",
                                       datatype="DEWorkspace",
                                       parameterType="Required",
                                       direction="Output",
                                       )
        output_directory.value = "D:\Example\TerrainToolsCalculateTRIRiley\Output\/"
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

    def execute(self, parameters):
        """The source code of your tool."""
        arcpy.env.overwriteOutput = True

        arcpy.CheckOutExtension("Spatial")

        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )

        input_bathymetry = parameters[0].valueAsText
        output_directory = parameters[1].valueAsText
        focal_neighbourhood = parameters[2].valueAsText

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        arcpy.AddMessage("Calculating terrain ruggedness index from " + str(input_bathymetry) + ".")

        windowmin = FocalStatistics(input_bathymetry, focal_neighbourhood, "MINIMUM", "DATA")
        windowmax = FocalStatistics(input_bathymetry, focal_neighbourhood, "MAXIMUM", "DATA")
        tri = (Abs((windowmax * windowmax) - (windowmin * windowmin)))
        tri = SquareRoot(tri)
        tri.save(os.path.join(output_directory, "tri_riley"))

        return


def main():
    tool = TerrainToolsCalculateTRIRiley()
    tool.execute(tool.getParameterInfo())

if __name__ == '__main__':
    main()
