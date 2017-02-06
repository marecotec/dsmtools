#!/usr/bin/env python
import sys
import os
import arcpy
from scipy.interpolate import RegularGridInterpolator
import numpy as np
import time
from arcpy import env
from arcpy.sa import *
from Includes import error_logging, rename_fields


class DeepSeaSDMToolsTrilinearInterpolation(object):
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

        input_bathymetry = arcpy.Parameter(name="input_bathymetry",
                                       displayName="Input Bathymetry Raster (m)",
                                       datatype="DERasterDataset",
                                       parameterType="Required",
                                       direction="Input",
                                       )
        input_bathymetry.value = "D:\Example\DeepSeaSDMToolsTrilinearInterpolation\Depth_Layer\gebco14sml"
        params.append(input_bathymetry)

        input_environment = arcpy.Parameter(name="input_environment",
                                       displayName="Input Environment Layers (directory, should have name+depth in flename)",
                                       datatype="DEWorkspace",
                                       parameterType="Required",
                                       direction="Input",
                                       )
        input_environment.value = "D:\Example\DeepSeaSDMToolsTrilinearInterpolation\WOA_13\/"
        params.append(input_environment)

        output_directory = arcpy.Parameter(name="output_directory",
                                       displayName="Output Directory",
                                       datatype="DEWorkspace",
                                       parameterType="Required",
                                       direction="Output",
                                       )
        params.append(output_directory)
        output_directory.value = "D:\Example\DeepSeaSDMToolsTrilinearInterpolation\Output4\/"
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

        arcpy.AddMessage("Trilinear interpolation")

        t_start = time.clock()

        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )

        input_bathymetry = parameters[0].valueAsText
        input_environment = parameters[1].valueAsText
        output_directory = parameters[2].valueAsText

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)
        if not os.path.exists(os.path.join(output_directory, "SplitRaster")):
            os.makedirs(os.path.join(output_directory, "SplitRaster"))
        if not os.path.exists(os.path.join(output_directory, "SplitRaster", "Outputs")):
            os.makedirs(os.path.join(output_directory, "SplitRaster", "Outputs"))

        env.workspace = input_environment

        # Build list of environmental data
        input_environment_list = arcpy.ListRasters("*", "ALL")
        input_environment_depth = []

        # Split name to extract depth
        for i in input_environment_list:
            input_environment_depth.append(int(filter(str.isdigit, str(i))))

        input_environment_name = ''.join([i for i in str(input_environment_list[0]) if not i.isdigit()])

        input_environment_depth.sort()

        arcpy.AddMessage("There are " + str(len(input_environment_depth)) + " environmental layers")

        if len(input_environment_depth) < 2:
            arcpy.AddMessage("Error: Too few environmental layers for Trilinear interpolation")
            sys.exit(0)
        else:
            pass

        arcpy.env.outputCoordinateSystem = input_bathymetry
        arcpy.env.cellSize = input_bathymetry

        # Check for Projected coordinate system - IMPORTANT - FAIL if not with warning.
        input_bathymetry_desc = arcpy.Describe(input_bathymetry)
        input_bathymetry_sr = input_bathymetry_desc.spatialReference

        input_environment0_desc = arcpy.Describe(input_environment_list[0])
        input_environment0_sr = input_environment0_desc.spatialReference
        input_environment0_cs = input_environment0_desc.meanCellHeight

        if input_bathymetry_sr.type == "Projected" and input_environment0_sr.type == "Projected":
            arcpy.AddMessage("Both depth and environmental data are in valid projection")
            if input_bathymetry_sr.name == input_environment0_sr.name:
                pass
            else:
                arcpy.AddMessage("Error: Depth and environmental data are in different projections, must be identical")
                sys.exit(0)
            pass
        else:
            arcpy.AddMessage("Error: Both depth and environmental data need to be in projected coordinate system")
            sys.exit(0)
        #del input_bathymetry_desc, input_bathymetry_sr, input_environment0_desc, input_environment0_sr

        # To manage large rasters, split into smaller blocks
        arcpy.SplitRaster_management(in_raster=input_bathymetry,
                                     out_folder=os.path.join(output_directory,"SplitRaster"),
                                     out_base_name="sp", split_method="SIZE_OF_TILE", format="GRID",
                                     resampling_type="NEAREST", num_rasters="2 2", tile_size="100 100", overlap="0",
                                     units="PIXELS", cell_size="", origin="", split_polygon_feature_class="",
                                     clip_type="NONE", template_extent="DEFAULT", nodata_value="#")

        env.workspace = os.path.join(output_directory,"SplitRaster")
        input_bathymetry_list = arcpy.ListRasters("*", "ALL")
        arcpy.AddMessage("There are " + str(len(input_bathymetry_list)) + " depth blocks to process.")

        for input_bathymetry_split_i in input_bathymetry_list:
            input_bathymetry_split = arcpy.Raster(input_bathymetry_split_i)

            arcpy.RasterToASCII_conversion(input_bathymetry_split, os.path.join(output_directory,
                                                             "SplitRaster",
                                                             str(input_bathymetry_split) + ".asc"))

            # Get headers
            with open(os.path.join(output_directory, "SplitRaster", str(input_bathymetry_split) + ".asc")) as myfile:
                header_ascii = myfile.readlines()[0:6]  # put here the interval you want
            #arcpy.AddMessage("ASCII Header: " + str(header_ascii))

            # Write headers to new file
            with open(os.path.join(output_directory, "SplitRaster",  "Outputs", str(input_bathymetry_split) + ".asc"), 'a') as ascii_file:
                for wr in header_ascii:
                    ascii_file.write(wr)

            bathymetry_shapefile = os.path.join(os.path.join(output_directory,
                                                             "SplitRaster",
                                                             str(input_bathymetry_split) + ".shp"))
            # Convert the raster to a point shapefile
            arcpy.RasterToPoint_conversion(input_bathymetry_split, bathymetry_shapefile, "VALUE")
            # Add columns to the shapefile containing the X and Y co-ordinates
            arcpy.AddXY_management(bathymetry_shapefile)
            new_name_by_old_name = {"GRID_CODE": "depth", "POINT_X": "SRC_X", "POINT_Y": "SRC_Y"}
            rename_fields(bathymetry_shapefile, os.path.join(output_directory,
                                                             "SplitRaster",
                                                             str(input_bathymetry_split) + "_2.shp"), new_name_by_old_name)

            #arcpy.AddMessage("Cell size is: " + str(input_environment0_cs))

            arcpy.MakeFeatureLayer_management(os.path.join(output_directory,"SplitRaster",str(input_bathymetry_list[0]) + "_2.shp"), "pts")

            bathymetry_in_points_fields = ['POINTID', 'depth', 'SRC_X', 'SRC_Y']

            tri_value_list = []

            with arcpy.da.SearchCursor("pts", bathymetry_in_points_fields) as cursor:
                for row in cursor:

                    current_depth_location = row[0]

                    #arcpy.AddMessage("Current point is " + str(current_depth_location))
                    arcpy.SelectLayerByAttribute_management("pts", "NEW_SELECTION", str('"POINTID" =') + str(current_depth_location))

                    arcpy.Buffer_analysis(in_features="pts",
                                          out_feature_class="in_memory/pol",
                                          buffer_distance_or_field=input_environment0_cs,
                                          line_side="FULL", line_end_type="ROUND",
                                          dissolve_option="NONE", dissolve_field="", method="PLANAR")

                    # Check to ensure pos/negative depths taken into account
                    if row[1] < 0:
                        depth_positive = row[1] * -1
                    else:
                        depth_positive = row[1]

                    # If depth greater than what we have in our env layers, set to bottom two env for extrapolation
                    if depth_positive >= max(input_environment_depth):
                        lower = max(n for n in input_environment_depth if n != max(input_environment_depth))
                        upper = max(input_environment_depth)
                    # otherwise, locate values
                    else:
                        for lower, upper in zip(input_environment_depth[:-1], input_environment_depth[1:]):
                            if lower <= depth_positive <= upper:
                                break

                    extent_pol = arcpy.Describe("in_memory/pol").extent

                    # Lower
                    arcpy.Clip_management(in_raster=os.path.join(input_environment,input_environment_name + str(lower)),
                                          rectangle=str(float(extent_pol.XMin)) + " " + str(float(extent_pol.YMin)) + " " + str(float(extent_pol.XMax)) + " " + str(float(extent_pol.YMax)),
                                          out_raster="in_memory/lower",
                                          in_template_dataset="in_memory/pol", nodata_value="-3.402823e+038",
                                          clipping_geometry="NONE", maintain_clipping_extent="NO_MAINTAIN_EXTENT")

                    arcpy.RasterToPoint_conversion(in_raster="in_memory/lower",
                                                   out_point_features="in_memory/lower_pts",
                                                   raster_field="Value")

                    arcpy.AddXY_management("in_memory/lower_pts")

                    arcpy.MakeFeatureLayer_management("in_memory/lower_pts", "lower_pnts2")

                    lower_pnts_arr = arcpy.da.TableToNumPyArray("lower_pnts2",("POINT_Y", "POINT_X"))
                    lower_latitude_max = max(lower_pnts_arr["POINT_Y"])
                    lower_latitude_min = min(lower_pnts_arr["POINT_Y"])
                    lower_longitude_max = max(lower_pnts_arr["POINT_X"])
                    lower_longitude_min = min(lower_pnts_arr["POINT_X"])

                    # Upper
                    arcpy.Clip_management(in_raster=os.path.join(input_environment, input_environment_name + str(upper)),
                                          rectangle=str(float(extent_pol.XMin)) + " " + str(float(extent_pol.YMin)) + " " + str(float(extent_pol.XMax)) + " " + str(float(extent_pol.YMax)),
                                          out_raster="in_memory/upper",
                                          in_template_dataset="in_memory/pol",
                                          nodata_value="-3.402823e+038",
                                          clipping_geometry="NONE", maintain_clipping_extent="NO_MAINTAIN_EXTENT")

                    arcpy.RasterToPoint_conversion(in_raster="in_memory/upper",
                                                   out_point_features="in_memory/upper_pts",
                                                   raster_field="Value")
                    arcpy.AddXY_management("in_memory/upper_pts")
                    arcpy.MakeFeatureLayer_management("in_memory/upper_pts", "upper_pnts2")

                    upper_pnts_arr = arcpy.da.TableToNumPyArray("upper_pnts2",("POINT_Y", "POINT_X"))
                    upper_latitude_max = max(upper_pnts_arr["POINT_Y"])
                    upper_latitude_min = min(upper_pnts_arr["POINT_Y"])
                    upper_longitude_max = max(upper_pnts_arr["POINT_X"])
                    upper_longitude_min = min(upper_pnts_arr["POINT_X"])

                    # Now we build the array
                    trilinear_points_fields = ['grid_code', 'POINT_X', 'POINT_Y']

                    with arcpy.da.SearchCursor("lower_pnts2", trilinear_points_fields) as cursor:
                        for trilinear_row in cursor:
                            # Lower Left
                            if trilinear_row[2] == lower_latitude_min and trilinear_row[1] == lower_longitude_min:
                                lower_lower_left = [trilinear_row[1], trilinear_row[2], lower, trilinear_row[0]]
                                #arcpy.AddMessage("lower_lower_left: " + str(lower_lower_left))
                            # Upper left
                            if trilinear_row[2] == lower_latitude_max and trilinear_row[1] == lower_longitude_min:
                                lower_upper_left = [trilinear_row[1], trilinear_row[2], lower, trilinear_row[0]]
                                #arcpy.AddMessage("lower_upper_left: " + str(lower_upper_left))
                            # Lower Right
                            if trilinear_row[2] == lower_latitude_min and trilinear_row[1] == lower_longitude_max:
                                lower_lower_right = [trilinear_row[1], trilinear_row[2], lower, trilinear_row[0]]
                                #arcpy.AddMessage("lower_lower_right: " + str(lower_lower_right))
                            # Upper Right
                            if trilinear_row[2] == lower_latitude_max and trilinear_row[1] == lower_longitude_max:
                                lower_upper_right = [trilinear_row[1], trilinear_row[2], lower, trilinear_row[0]]
                                #arcpy.AddMessage("lower_upper_right: " + str(lower_upper_right))
                    del cursor, trilinear_row

                    with arcpy.da.SearchCursor("upper_pnts2", trilinear_points_fields) as cursor:
                        for trilinear_row in cursor:
                            # Upper Left
                            if trilinear_row[2] == upper_latitude_min and trilinear_row[1] == upper_longitude_min:
                                upper_lower_left = [trilinear_row[1], trilinear_row[2], upper, trilinear_row[0]]
                            # Upper left
                            if trilinear_row[2] == upper_latitude_max and trilinear_row[1] == upper_longitude_min:
                                upper_upper_left = [trilinear_row[1], trilinear_row[2], upper, trilinear_row[0]]
                            # Lower Right
                            if trilinear_row[2] == upper_latitude_min and trilinear_row[1] == upper_longitude_max:
                                upper_lower_right = [trilinear_row[1], trilinear_row[2], upper, trilinear_row[0]]
                            # Upper Right
                            if trilinear_row[2] == upper_latitude_max and trilinear_row[1] == upper_longitude_max:
                                upper_upper_right = [trilinear_row[1], trilinear_row[2], upper, trilinear_row[0]]
                    del cursor, trilinear_row

                    # Build np.arrays
                    x = np.array([lower_lower_left[0], lower_lower_right[0]])
                    #arcpy.AddMessage("X array: ")
                    #arcpy.AddMessage(x)
                    y = np.array([lower_lower_left[1], lower_upper_left[1]])
                    #arcpy.AddMessage("Y array: ")
                    #arcpy.AddMessage(y)
                    z = np.array([lower, upper])
                    #arcpy.AddMessage("Z array: ")
                    #arcpy.AddMessage(z)
                    v = np.array([[[lower_lower_left[3], upper_lower_left[3]],
                                  [lower_upper_left[3], upper_upper_left[3]]],

                                  [[lower_lower_right[3], upper_lower_right[3]],
                                   [lower_upper_right[3], upper_upper_right[3]]]])
                    #arcpy.AddMessage("V array: ")
                    #arcpy.AddMessage(v)

                    #arcpy.AddMessage("Asked for values, x:" + str(row[2]) + ", y: " + str(row[3]) + ", z: " + str(depth_positive))

                    rgi = RegularGridInterpolator((x, y, z), v)
                    tri_value_list.append(rgi((row[2], row[3], depth_positive)))

                    #Clean up, only after finished
                    #arcpy.Delete_management(os.path.join(output_directory, "SplitRaster", input_environment_name + str(upper)))
                    #arcpy.Delete_management(os.path.join(output_directory, "SplitRaster", input_environment_name + str(lower)))
                    #arcpy.Delete_management(os.path.join(output_directory, "SplitRaster", input_environment_name + str(upper) + "pt.shp"))
                    #arcpy.Delete_management(os.path.join(output_directory, "SplitRaster", input_environment_name + str(lower) + "pt.shp"))
                    #arcpy.Delete_management(os.path.join(output_directory, "SplitRaster", str(input_bathymetry_list[0]) + "_" + str(row[0]) + "_POL.shp"))
                del row

            with open(os.path.join(output_directory, "SplitRaster", "Outputs", str(input_bathymetry_split) + ".asc"), 'a') as ascii_file:
                for tri in tri_value_list:
                    ascii_file.write(str(tri) + " ")


        arcpy.AddMessage("Script complete in %s seconds." % (time.clock() - t_start))
        return


def main():
    tool = DeepSeaSDMToolsTrilinearInterpolation()
    tool.execute(tool.getParameterInfo(), None)

if __name__ == '__main__':
    main()

