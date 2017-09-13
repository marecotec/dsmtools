#!/usr/bin/env python
import arcpy
import os
from arcpy import env
from arcpy.sa import *
from Includes import load_depth_string

arcpy.CheckOutExtension("Spatial")


class DeepSeaSDMToolsExtractDepths(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        self.label = "Extract the depths from the bathymetric layer you insert"
        self.description = """To use the cookie cutting approach of Davies & Guinotte (2011), we
        first need to extract the bathymetric layers from our target bathymetry
        to match those of the source environmental variables.
        Cite this paper if you use this approach or script.
        Davies, A.J. & Guinotte, J.M. (2011) "Global Habitat Suitability for
        Framework-Forming Cold-Water Corals." PLoS ONE 6(4): e18483. doi:10.1371/journal.pone.0018483"""
        self.canRunInBackground = True
        self.category = "Deep-sea SDM Tools"  # Use your own category here, or an existing one.

    def getParameterInfo(self):
        params = []

        input_bathymetry = arcpy.Parameter(name="input_bathymetry",
                                           displayName="Input Bathymetry Raster",
                                           datatype="DERasterDataset",
                                           parameterType="Required",
                                           direction="Input",
                                           )
        input_bathymetry.value = "D:\Example\DeepSeaSDMToolsExtractDepths\depth.tif"
        params.append(input_bathymetry)

        # extraction_format
        depths = arcpy.Parameter(name="depths",
                                 displayName="Select depths (WOA13v2, WOA05, Steinacher or Custom (in CSV style)",
                                 datatype="GPString",
                                 parameterType="Required",
                                 direction="Input",
                                 )
        depths.value = "WOA05"
        params.append(depths)

        output_directory = arcpy.Parameter(name="output_directory",
                                           displayName="Output Directory",
                                           datatype="DEWorkspace",
                                           parameterType="Required",
                                           direction="Output",
                                           )
        output_directory.value = r"D:\Example\DeepSeaSDMToolsExtractDepths\Depths"
        params.append(output_directory)
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):

        arcpy.env.overwriteOutput = True

        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText))

        input_bathymetry = parameters[0].valueAsText
        output_directory = parameters[2].valueAsText
        depths = parameters[1].valueAsText

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        arcpy.AddMessage("Extracting depths from " + str(input_bathymetry) + ".")

        depth_list = load_depth_string(depths)

        arcpy.AddMessage("Depths are: " + str(depth_list))

        # Set environment variables for processing
        env.mask = input_bathymetry
        env.cellSize = input_bathymetry
        extraster = arcpy.Raster(input_bathymetry)
        extent1 = extraster.extent
        env.extent = extent1
        env.workspace = output_directory

        # Conduct the extraction process

        # Loop through each depth in the Depths list
        for item in depth_list:
            individual_depth = int(float(item))
            null_value_clause = "VALUE > " + "-" + str(individual_depth)
            arcpy.AddMessage("Processing depth: " + str(individual_depth))
            output_set_null = SetNull(input_bathymetry, "1", null_value_clause)
            output_set_null_2 = ApplyEnvironment(output_set_null)
            output_set_null_2.save(os.path.join(output_directory, "bath" + str(individual_depth)))
            arcpy.env.pyramid = "PYRAMIDS 3 BILINEAR JPEG"
            arcpy.BuildPyramids_management(os.path.join(output_directory, "bath" + str(individual_depth)))
        return


def main():
    tool = DeepSeaSDMToolsExtractDepths()
    tool.execute(tool.getParameterInfo(), None)


if __name__ == '__main__':
    main()
