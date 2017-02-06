import arcpy
import os
from arcpy.sa import *

arcpy.CheckOutExtension("Spatial")

class TerrainToolsCalculateSTDSlope(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate the Standard Deviation of a Slope"
        self.description = """Equation taken from http://gis4geomorphology.com/roughness-topographic-position/
        Standard Deviation of Slope. See Grohmann et al. (2011) for a comparison of several roughness techniques.
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
        input_slope.value = "D:\Example\TerrainToolsCalculateSTDSlope\slope_deg"
        params.append(input_slope)

        output_directory = arcpy.Parameter(name="output_directory",
                                       displayName="Output Directory",
                                       datatype="DEWorkspace",
                                       parameterType="Required",
                                       direction="Output",
                                       )
        output_directory.value = "D:\Example\TerrainToolsCalculateSTDSlope\Output/"
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

        arcpy.AddMessage("Calculating standard deviation of slope from " + str(input_slope) + ".")

        slopestd = FocalStatistics(input_slope, focal_neighbourhood, "STD", "DATA")
        slopestd.save(os.path.join(output_directory, "std_slope"))
        return


def main():
    tool = TerrainToolsCalculateSTDSlope()
    tool.execute(tool.getParameterInfo(), None)

if __name__ == '__main__':
    main()
