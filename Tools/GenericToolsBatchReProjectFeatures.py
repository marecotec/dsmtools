#!/usr/bin/env python
import os
import arcpy
from arcpy import env


class GenericToolsBatchReProjectFeatures(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Batch reproject directory of shapefules"
        self.description = """Reproject a directory of shapefiles into a consistent projection"""
        self.canRunInBackground = True
        self.category = "Generic Tools"  # Use your own category here, or an existing one.

    def getParameterInfo(self):
        params = []

        input_directory = arcpy.Parameter(name="input_directory",
                                       displayName="Input Directory",
                                       datatype="DEWorkspace",
                                       parameterType="Required",  # Required|Optional|Derived
                                       direction="Input",  # Input|Output
                                       )
        #input_directory.value = "D:\Example\GenericToolsBatchReProjectRasters\Rasters_WGS1984\/"
        input_directory.value = r"D:\MP_Run\IndividualIslands_ByYear_Lines"
        params.append(input_directory)  # ..and then add it to the list of defined parameters

        output_directory = arcpy.Parameter(name="output_directory",
                                       displayName="Output Directory",
                                       datatype="DEWorkspace",
                                       parameterType="Required",  # Required|Optional|Derived
                                       direction="Output",  # Input|Output
                                       )
        #output_directory.value = "D:\Example\GenericToolsBatchReProjectRasters\Rasters_ReProjected\/"
        output_directory.value = r"D:\MP_Run\IndividualIslands_ByYear_Lines_2"
        params.append(output_directory)  # ..and then add it to the list of defined parameters

        coordinate_system = arcpy.Parameter(name="coordinate_system",
                                       displayName="Coordinate System",
                                       datatype="GPCoordinateSystem",
                                       parameterType="Required",  # Required|Optional|Derived
                                       direction="Input",  # Input|Output
                                       )
        coordinate_system.value = "PROJCS['World_Mercator',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984'," \
                                  "SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0]," \
                                  "UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator'],PARAMETER['False_Easting'," \
                                  "0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0]," \
                                  "PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]"
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

        arcpy.AddMessage("Reproject a directory of rasters into a consistent projection")

        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )

        input_directory = parameters[0].valueAsText
        output_directory = parameters[1].valueAsText
        coordinate_system = parameters[2].valueAsText

        # Set environment settings
        env.workspace = input_directory
        featurelist = arcpy.ListFeatureClasses("*")
        arcpy.AddMessage("There are " + str(len(featurelist)) + " features to process.")
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        for feature in featurelist:
            # Execute RasterToASCII
            arcpy.AddMessage("Reprojecting " + str(feature) + ".")
            arcpy.Project_management(in_dataset=feature,
                                     out_dataset=os.path.join(output_directory,feature),
                                     out_coor_system=coordinate_system,
                                     transform_method="",
                                     in_coor_system="GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]",
                                     preserve_shape="NO_PRESERVE_SHAPE", max_deviation="", vertical="NO_VERTICAL")

        return


def main():
    tool = GenericToolsBatchReProjectFeatures()
    tool.execute(tool.getParameterInfo(), None)

if __name__ == '__main__':
    main()
