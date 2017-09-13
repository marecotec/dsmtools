#!/usr/bin/env python
import sys, os, select, string, getopt
import arcpy
from arcpy import env


class GenericToolsBatchProjectRasters(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Batch project directory of rasters"
        self.description = """Project a directory of rasters into a consistent projection"""
        self.canRunInBackground = True
        self.category = "Generic Tools"  # Use your own category here, or an existing one.

    def getParameterInfo(self):
        params = []

        # Input Island Points
        input_directory = arcpy.Parameter(name="input_directory",
                                       displayName="Input Feature Class",
                                       datatype="DEWorkspace",
                                       parameterType="Required",  # Required|Optional|Derived
                                       direction="Input",  # Input|Output
                                       )
        input_directory.value = "D:\Example\GenericToolsBatchProjectRasters\Example_Unprojected"
        params.append(input_directory)  # ..and then add it to the list of defined parameters

        # Input Island Points
        coordinate_system = arcpy.Parameter(name="coordinate_system",
                                       displayName="Coordinate System",
                                       datatype="GPCoordinateSystem",
                                       parameterType="Required",  # Required|Optional|Derived
                                       direction="Input",  # Input|Output
                                       )
        coordinate_system.value = "GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]"
        params.append(coordinate_system)  # ..and then add it to the list of defined parameters

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

        arcpy.AddMessage("Project a directory of rasters into a consistent projection")

        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )

        input_directory = parameters[0].valueAsText
        coordinate_system = parameters[1].valueAsText

        # Set environment settings
        env.workspace = input_directory

        rasterlist = arcpy.ListRasters("*")
        arcpy.AddMessage("There are " + str(len(rasterlist)) + " rasters to process.")

        for raster in rasterlist:
            # Execute RasterToASCII
            arcpy.AddMessage("Defining projection for " + str(raster) + ".")
            arcpy.DefineProjection_management(raster, coordinate_system)

        return


def main():
    tool = GenericToolsBatchProjectRasters()
    tool.execute(tool.getParameterInfo(), None)

if __name__ == '__main__':
    main()
