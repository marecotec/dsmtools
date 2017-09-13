#!/usr/bin/env python
import arcpy
import os
from arcpy import env
from arcpy.sa import *
from Includes import load_depth_string

arcpy.CheckOutExtension("Spatial")


class DeepSeaSDMToolsDepthWeightedExtrapolation(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        self.label = "Depth Weighted Environment Extrapolation aka Cookie Cutter (Davies & Guinotte 2011)"
        self.description = """Extrapolates environmental variables of a coarse scale onto any resolution bathymetry 
        (aka the cookie cutting approach) of Davies & Guinotte (2011) PLoS ONE to create depth weighted continuous 
        grids of environmental variables. There is no automatic statistical test of how valid this approach is during 
        the variable creation process, we recommend post-hoc testing of the layers generated using an independent 
        CTD or other dataset to test how valid your extrapolation is within your area of interest. Cite this paper 
        if you use this approach or script. Davies, A.J. & Guinotte, J.M. (2011) "Global Habitat Suitability for
         Framework-Forming Cold-Water Corals." PLoS ONE 6(4): e18483. doi:10.1371/journal.pone.0018483"""
        self.canRunInBackground = True
        self.category = "Deep-sea SDM Tools" 

    def getParameterInfo(self):
        params = []

        # Read ArcGIS Geoprocessing parameters into main variables
        input_bathymetry = arcpy.Parameter(name="input_bathymetry",
                                           displayName="Input Bathymetry Raster Directory",
                                           datatype="DEWorkspace",
                                           parameterType="Required",
                                           direction="Input",
                                           )
        input_bathymetry.value = "D:\Example\DeepSeaSDMToolsDepthWeightedExtrapolation\Depths"
        params.append(input_bathymetry)

        depths = arcpy.Parameter(name="depths",
                                 displayName="Select depths (WOA13v2, WOA05, Steinacher or Custom (in CSV style)",
                                 datatype="GPString",
                                 parameterType="Required",
                                 direction="Input",
                                 )
        depths.value = "WOA05"
        params.append(depths)
        
        input_environment = arcpy.Parameter(name="input_environment",
                                 displayName="Input Environment Raster Directory",
                                 datatype="DEWorkspace",
                                 parameterType="Required",
                                 direction="Input",
                                 )
        input_environment.value = "D:\Example\DeepSeaSDMToolsDepthWeightedExtrapolation\Environment"
        params.append(input_environment)
        
        environment_append = arcpy.Parameter(name="environment_append",
                                 displayName="Name of environment layers (excluding the depth, i.e. i00an)",
                                 datatype="GPString",
                                 parameterType="Required",
                                 direction="Input",
                                 )
        environment_append.value = "i00an1"
        params.append(environment_append)

        temporary_directory = arcpy.Parameter(name="temporary_directory",
                                           displayName="Temporary Directory",
                                           datatype="DEWorkspace",
                                           parameterType="Required",
                                           direction="Output",
                                           )
        temporary_directory.value = r"D:\Example\DeepSeaSDMToolsDepthWeightedExtrapolation\Temp"
        params.append(temporary_directory)
        
        output_raster = arcpy.Parameter(name="output_raster",
                                           displayName="Output raster",
                                           datatype="DERasterDataset",
                                           parameterType="Required",
                                           direction="Output",
                                           )
        output_raster.value = r"D:\Example\DeepSeaSDMToolsDepthWeightedExtrapolation\example.tif"
        params.append(output_raster)
        
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
        depths = parameters[1].valueAsText
        input_environment = parameters[2].valueAsText
        environment_append = parameters[3].valueAsText
        temporary_directory = parameters[4].valueAsText
        output_raster = parameters[5].valueAsText

        # Define the options the script will use later
        # load depth strings from Includes.py
        depths_list = load_depth_string(depths)
        arcpy.AddMessage(depths_list)

        if not os.path.exists(temporary_directory):
            os.makedirs(temporary_directory)

        arcpy.ResetEnvironments()
        arcpy.env.overwriteOutput = "true"

        # Set environment variables
        env.mask = ""
        arcpy.AddMessage("Mask is: " + str(arcpy.env.mask))
        description = arcpy.Describe(os.path.join(input_bathymetry, "bath" + str(int(float(depths_list[0])))))
        cellsize1 = description.children[0].meanCellHeight
        env.cellSize = cellsize1
        arcpy.AddMessage("Cell size is: " + str(arcpy.env.cellSize))
        arcpy.AddMessage(os.path.join(input_bathymetry, "bath" + str(int(float(depths_list[0])))))
        extraster = Raster(os.path.join(input_bathymetry, "bath" + str(int(float(depths_list[0])))))
        extent1 = extraster.extent
        env.extent = extent1
        arcpy.AddMessage("Extent is: " + str(arcpy.env.extent))
        arcpy.env.workspace = temporary_directory
        spf = arcpy.Describe(os.path.join(input_bathymetry, "bath" + str(int(float(depths_list[0]))))).spatialReference
        arcpy.AddMessage("Coord sys is: " + str(spf.name))

        try:
            # loop through the layers
            for item in depths_list:
                depth = int(float(item))
                arcpy.AddMessage("Resizing layer " + str(depth) + " " + input_environment + "/" + environment_append + str(depth))
                arcpy.ProjectRaster_management(os.path.join(input_environment, environment_append + str(depth)),
                                               os.path.join(temporary_directory, environment_append + "a" + str(depth)), spf)
                TempData = arcpy.sa.ApplyEnvironment(os.path.join(temporary_directory, environment_append + "a" + str(depth)))
                arcpy.AddMessage("Extracting " + str(depth) + " to mask")
                outExtractByMask = ExtractByMask(TempData, os.path.join(input_bathymetry, "bath" + str(depth)))
                outExtractByMask.save(temporary_directory + "/clip" + str(depth))
                arcpy.AddMessage("Adding " + str(depth) + " to final layer")
                arcpy.Mosaic_management(temporary_directory + "/clip" + str(depth), temporary_directory + "/clip" + str(int(float(depths_list[0]))),
                                        "LAST")
                if depth == int(float(depths_list[-1])):
                    arcpy.AddMessage("Creating the final layer for you, which will be called " + str(output_raster))
                    arcpy.CopyRaster_management(temporary_directory + "/clip" + str(int(float(depths_list[0]))), output_raster)

                arcpy.AddMessage("next layer " + str(depth))

        except:
            arcpy.AddMessage(arcpy.GetMessages())
            arcpy.AddMessage("Something has gone wrong likely with this: " + str(depth))

        arcpy.AddMessage("Processing complete")

def main():
    tool = DeepSeaSDMToolsDepthWeightedExtrapolation()
    tool.execute(tool.getParameterInfo(), None)

if __name__ == '__main__':
    main()
