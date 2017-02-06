#!/usr/bin/env python
import os
import arcpy
from arcpy import env


class GenericToolsBatchConvertMXERaster(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Batch convert MXE to ArcGIS Raster"
        self.description = """Batch convert MXE to ArcGIS Raster"""
        self.canRunInBackground = True
        self.category = "Generic Tools"  # Use your own category here, or an existing one.

    def getParameterInfo(self):
        params = []

        input_directory = arcpy.Parameter(name="input_directory",
                                          displayName="Directory of rasters",
                                          datatype="DEWorkspace",
                                          parameterType="Required",
                                          direction="Input",
                                          )
        input_directory.value = "D:\Example\GenericToolsBatchConvertMXERaster\MXE\/"
        params.append(input_directory)

        output_directory = arcpy.Parameter(name="output_directory",
                                           displayName="Output directory",
                                           datatype="DEWorkspace",
                                           parameterType="Required",  # Required|Optional|Derived
                                           direction="Output",  # Input|Output
                                           )
        output_directory.value = "D:\Example\GenericToolsBatchConvertMXERaster\Output\/"
        params.append(output_directory)

        path_mxe = arcpy.Parameter(name="path_mxe",
                                   displayName="Path to Maxent jar",
                                   datatype="DEFolder",
                                   parameterType="Required",
                                   direction="Input",
                                   )
        path_mxe.value = "D:\Misc\MaxentJar\/"
        params.append(path_mxe)

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    #def updateParameters(self, parameters):

        #return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        try:
            path_mxe = parameters[2].valueAsText
            os.path.exists(os.path.join(path_mxe, "maxent.jar"))
            if not os.path.exists(os.path.join(path_mxe, "maxent.jar")):
                parameters[2].setErrorMessage("Maxent Jar not found in directory ")
        except Exception:
            pass
        return

    def execute(self, parameters, messages):
        """The source code of your tool."""
        arcpy.env.overwriteOutput = True

        arcpy.AddMessage("Batch convert MXE to ArcGIS Raster")

        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )

        input_directory = parameters[0].valueAsText
        output_directory = parameters[1].valueAsText
        path_mxe = parameters[2].valueAsText

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        command = 'java -cp "' + os.path.join(path_mxe, "maxent.jar") + '" density.Convert ' \
                  + str(input_directory) + " mxe " + output_directory + " asc"

        os.system(str(command))

        # Set environment settings
        env.workspace = output_directory
        rasterlist = arcpy.ListRasters("*")
        arcpy.AddMessage("There are " + str(len(rasterlist)) + " rasters to process.")

        for raster in rasterlist:

            if not arcpy.Exists(os.path.join(output_directory, raster[0:5])):
                arcpy.AddMessage("Converting " + str(raster) + ".")
                arcpy.ASCIIToRaster_conversion(os.path.join(output_directory, raster),
                                               os.path.join(output_directory, raster[0:5]), "FLOAT")

        arcpy.BuildPyramidsandStatistics_management(in_workspace=output_directory, include_subdirectories="NONE",
                                                    build_pyramids="BUILD_PYRAMIDS",
                                                    calculate_statistics="CALCULATE_STATISTICS", BUILD_ON_SOURCE="NONE",
                                                    block_field="", estimate_statistics="NONE", x_skip_factor="1",
                                                    y_skip_factor="1", ignore_values="", pyramid_level="-1",
                                                    SKIP_FIRST="NONE", resample_technique="NEAREST",
                                                    compression_type="DEFAULT", compression_quality="75",
                                                    skip_existing="SKIP_EXISTING")
        return


def main():
    tool = GenericToolsBatchConvertMXERaster()
    tool.execute(tool.getParameterInfo(), None)

if __name__ == '__main__':
    main()
