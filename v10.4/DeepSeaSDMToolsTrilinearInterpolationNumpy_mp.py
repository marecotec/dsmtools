# !/usr/bin/env python
import sys
import os
import arcpy
from scipy.interpolate import RegularGridInterpolator
import numpy as np
import time
from arcpy import env
from arcpy.sa import *
import pandas as pd
from Includes import raster_to_xyz
import multiprocessing
from Includes import error_logging, rename_fields
from functools import partial


def test(output_directory,
         input_environment_depth,
         input_environment0_cs,
         input_environment,
         environment_name,
         input_environment0_cs_x_min,
         input_environment0_cs_y_min,
         input_bathymetry_list):
    DeepSeaSDMToolsTrilinearInterpolationNumpy_mp.mpprocess(output_directory,
                                                            input_environment_depth,
                                                            input_environment0_cs,
                                                            input_environment,
                                                            environment_name,
                                                            input_environment0_cs_x_min,
                                                            input_environment0_cs_y_min,
                                                            input_bathymetry_list)


def mosaic_chunk(output_directory, input_bathymetry_cs, output_list_chunk):
    DeepSeaSDMToolsTrilinearInterpolationNumpy_mp.mpchunk(output_directory, input_bathymetry_cs, output_list_chunk)


class DeepSeaSDMToolsTrilinearInterpolationNumpy_mp(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Calculate trilinearly interpolated environmental layer (Multiprocessor)"
        self.description = """Calculate trilinearly interpolated environmental layer, designed to work with 2.5D data. Multiprocessor version."""
        self.canRunInBackground = True
        self.category = "Deep-sea SDM Tools"

    def getParameterInfo(self):

        arcpy.env.overwriteOutput = True

        params = []

        input_bathymetry = arcpy.Parameter(name="input_bathymetry",
                                           displayName="Input Bathymetry Raster (m)",
                                           datatype="DERasterDataset",
                                           parameterType="Required",
                                           direction="Input",
                                           )
        input_bathymetry.value = "D:/sponges/bathymetry/Projected/gebco_ocean"
        params.append(input_bathymetry)

        input_environment = arcpy.Parameter(name="input_environment",
                                            displayName="Input Environment Layers (directory, should have name+depth in flename)",
                                            datatype="DEWorkspace",
                                            parameterType="Required",
                                            direction="Input",
                                            )
        ##        input_environment.value = "D:/sponges/world-ocean-atlas/temperature/extracted/Projected"
        input_environment.value = "D:/sponges/world-ocean-atlas/dissolvedO2/extracted/Projected"
        params.append(input_environment)

        environment_name = arcpy.Parameter(name="environment_name",
                                           displayName="Environment variable name (e.g. string before depth integer t_an for t_an0)",
                                           datatype="GPString",
                                           parameterType="Required",
                                           direction="Input",
                                           )
        params.append(environment_name)
        environment_name.value = "o_an"

        output_directory = arcpy.Parameter(name="output_directory",
                                           displayName="Output Directory",
                                           datatype="DEWorkspace",
                                           parameterType="Required",
                                           direction="Output",
                                           )
        params.append(output_directory)
        output_directory.value = "D:/sponges/trilinear_dissolvedo2/run4"

        cpu_cores_used = arcpy.Parameter(name="cpu_cores_used",
                                         displayName="Number of CPU cores to use",
                                         datatype="GPString",
                                         parameterType="Required",
                                         direction="Output",
                                         )
        params.append(cpu_cores_used)
        cpu_cores_used.value = "40"
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

        # def updateParameters(self, parameters):

        # return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    @staticmethod
    def mpchunk(output_directory, input_bathymetry_cs, output_list_chunk):
        arcpy.AddMessage("Processing chunk: " + str(output_list_chunk[0]))
        if not arcpy.Exists(
                os.path.join(output_directory, "SplitRaster", "Outputs_C", str(output_list_chunk[0]) + "_f", "a")):
            if not os.path.exists(
                    os.path.join(output_directory, "SplitRaster", "Outputs_C", str(output_list_chunk[0]) + "_f")):
                os.makedirs(
                    os.path.join(output_directory, "SplitRaster", "Outputs_C", str(output_list_chunk[0]) + "_f"))

            if not os.path.exists(
                    os.path.join(output_directory, "SplitRaster", "Outputs_C", str(output_list_chunk[0]) + "_f",
                                 "temp")):
                os.makedirs(os.path.join(output_directory, "SplitRaster", "Outputs_C", str(output_list_chunk[0]) + "_f",
                                         "temp"))
            env.scratchWorkspace = os.path.join(output_directory, "SplitRaster", "Outputs_C",
                                                str(output_list_chunk[0]) + "_f")
            env.workspace = os.path.join(output_directory, "SplitRaster", "Outputs_C", str(output_list_chunk[0]) + "_f")

            counter = 1
            chunk_list = []
            for raster_output in output_list_chunk:
                if not arcpy.Exists(
                        os.path.join(output_directory, "SplitRaster", "Outputs_C", str(output_list_chunk[0]) + "_f",
                                     "temp", str(counter))):
                    arcpy.Mirror_management(
                        in_raster=os.path.join(output_directory, "SplitRaster", "Outputs", raster_output),
                        out_raster=os.path.join(output_directory, "SplitRaster", "Outputs_C",
                                                str(output_list_chunk[0]) + "_f", "temp", str(counter)))
                    chunk_list.append(
                        os.path.join(output_directory, "SplitRaster", "Outputs_C", str(output_list_chunk[0]) + "_f",
                                     "temp", str(counter)))
                counter += 1

            arcpy.MosaicToNewRaster_management(input_rasters=chunk_list,
                                               output_location=os.path.join(output_directory, "SplitRaster",
                                                                            "Outputs_C",
                                                                            str(output_list_chunk[0]) + "_f"),
                                               raster_dataset_name_with_extension="a",
                                               coordinate_system_for_the_raster="",
                                               pixel_type="32_BIT_FLOAT",
                                               cellsize=input_bathymetry_cs, number_of_bands="1", mosaic_method="MEAN",
                                               mosaic_colormap_mode="MATCH")

        arcpy.AddMessage("Completed chunk: " + str(output_list_chunk[0]))

    @staticmethod
    def mpprocess(output_directory, input_environment_depth, input_environment0_cs,
                  input_environment, environment_name, input_environment0_cs_x_min, input_environment0_cs_y_min,
                  input_bathymetry_list):
        arcpy.CheckOutExtension("Spatial")
        depth_array_min_comp = -9999
        depth_array_max_comp = -9999

        if not os.path.exists(os.path.join(output_directory, "SplitRaster", "1_Temp", str(input_bathymetry_list))):
            os.makedirs(os.path.join(output_directory, "SplitRaster", "1_Temp", str(input_bathymetry_list)))

        env.workspace = os.path.join(output_directory, "SplitRaster", "1_Temp", str(input_bathymetry_list))
        env.scratchWorkspace = os.path.join(output_directory, "SplitRaster", "1_Temp", str(input_bathymetry_list))

        try:
            input_bathymetry_split = arcpy.Raster(os.path.join(output_directory, "SplitRaster", input_bathymetry_list))
            input_bathymetry_split_i = input_bathymetry_list
            arcpy.AddMessage("Reading bathymetric layer: " + str(input_bathymetry_list))
        except:
            arcpy.AddWarning("Unable to read bathymetric layer: " + str(input_bathymetry_list))
            input_bathymetry_split = False
            input_bathymetry_split_i = False

        if arcpy.Exists(input_bathymetry_split) and not arcpy.Exists(os.path.join(output_directory,
                                                                                  "SplitRaster", "Outputs",
                                                                                  str(
                                                                                      input_bathymetry_split) + ".asc")):

            arcpy.RasterToASCII_conversion(input_bathymetry_split, os.path.join(output_directory,
                                                                                "SplitRaster", "1_Temp",
                                                                                str(
                                                                                    input_bathymetry_split) + ".asc"))

            input_bathymetry_split = arcpy.Raster(os.path.join(output_directory,
                                                               "SplitRaster", "1_Temp",
                                                               str(input_bathymetry_split) + ".asc"))

            no_data_value = 349000000.0
            input_bathymetry_split_2 = Con(IsNull(input_bathymetry_split), no_data_value,
                                           input_bathymetry_split)

            raster_to_xyz(input_bathymetry_split_2, str(input_bathymetry_split),
                          os.path.join(output_directory, "SplitRaster", "1_Temp", ), no_data_value)

            input_bathymetry_extent = input_bathymetry_split_2.extent

            depth_array = pd.read_csv(
                os.path.join(output_directory, "SplitRaster", "1_Temp", str(input_bathymetry_split) + ".yxz"), header=0,
                names=["y", "x", "depth"], sep=" ")

            depth_array.loc[depth_array["depth"] == no_data_value, "depth"] = np.nan

            depth_array_min = depth_array['depth'].min()
            depth_array_max = depth_array['depth'].max()
            depth_array_x_min = depth_array['x'].min()
            depth_array_x_max = depth_array['x'].max()
            depth_array_y_min = depth_array['y'].min()
            depth_array_y_max = depth_array['y'].max()

            tri_value_list = []

            if depth_array_min < 0:
                depth_array["depth"] *= -1
                depth_array_min = depth_array['depth'].min()
                depth_array_max = depth_array['depth'].max()

            def build_env_array(location, bname, z_min, z_max, y_min, y_max, x_min, x_max):
                # 1 Extract list of files.
                env_files = []
                env_values = []
                env.workspace = location
                rasterlist1 = arcpy.ListRasters("*")
                for f in rasterlist1:
                    f2 = float(f.replace(bname, ""))
                    env_values.append(f2)
                    env_files.append(f)
                else:
                    pass

                env_file_list = sorted(zip(env_files, env_values), key=lambda tup: tup[1])

                # 2 Get xyz values needed to build array
                xy_coords = pd.read_pickle(os.path.join(location, "xy_coords.pkl"))

                y_min = y_min - (input_environment0_cs)
                y_max = y_max + (input_environment0_cs)
                x_min = x_min - (input_environment0_cs)
                x_max = x_max + (input_environment0_cs)

                x_vals = np.unique(xy_coords["x"])
                y_vals = np.unique(xy_coords["y"])

                if input_environment0_cs_x_min > x_min and input_environment0_cs_y_min > y_min:
                    x_min = input_environment0_cs_x_min
                    y_min = input_environment0_cs_y_min
                elif input_environment0_cs_x_min > x_min:
                    x_min = input_environment0_cs_x_min
                elif input_environment0_cs_y_min > y_min:
                    y_min = input_environment0_cs_y_min

                x_vals = [i for i in x_vals if i > x_min and i < x_max]
                y_vals = [i for i in y_vals if i > y_min and i < y_max]

                x_vals_min = min(x_vals)  # + input_environment0_cs
                x_vals_max = max(x_vals)  # - input_environment0_cs
                y_vals_min = min(y_vals)  # + input_environment0_cs
                y_vals_max = max(y_vals)  # - input_environment0_cs

                temp_name = []
                temp_depth = []

                counter = 1
                key = -1

                for t_pair in env_file_list:
                    key += 1
                    name, depth = t_pair
                    if z_min <= depth <= z_max:
                        key2 = key
                        if counter == 1:
                            v1, v2 = env_file_list[key - 1]
                            temp_name.append(v1)
                            temp_depth.append(v2)
                            del v1, v2
                        temp_name.append(name)
                        temp_depth.append(depth)
                        counter += 1

                if z_min == z_max:
                    key = -1
                    for t_pair in env_file_list:
                        key += 1
                        name, depth = t_pair
                        if depth <= z_min:
                            key2 = key
                            if counter == 1:
                                v1, v2 = env_file_list[key]
                                temp_name.append(v1)
                                temp_depth.append(v2)
                                del v1, v2
                            counter += 1
                if "key2" in locals():
                    if key2 < key:
                        v1, v2 = env_file_list[key2 + 1]
                        temp_name.append(v1)
                        temp_depth.append(v2)
                        del v1, v2
                else:
                    key = -1
                    for t_pair in env_file_list:
                        key += 1
                        name, depth = t_pair
                        if depth >= z_min:
                            if counter == 1:
                                key2 = key
                                v1, v2 = env_file_list[key - 1]
                                temp_name.append(v1)
                                temp_depth.append(v2)
                                del v1, v2
                            counter += 1

                    if key2 < key:
                        v1, v2 = env_file_list[key2 + 1]
                        temp_name.append(v1)
                        temp_depth.append(v2)
                        del v1, v2

                temp_depth_reverse = temp_depth[::-1]

                z_vals = np.unique(np.asarray(temp_depth_reverse, dtype=float))

                data = np.array([np.flipud(arcpy.RasterToNumPyArray(os.path.join(location, bname + "%f" % f),
                                                                    arcpy.Point(x_min, y_min), len(x_vals),
                                                                    len(y_vals),
                                                                    nodata_to_value=np.nan)) for f in
                                 temp_depth])

                data = data.T
                rgi = RegularGridInterpolator((x_vals, y_vals, z_vals), data, method='linear')
                return rgi, y_vals_min, y_vals_max, x_vals_min, x_vals_max

            # Build extents for subsetting the environemtnal grid

            if depth_array_min == depth_array_min_comp and depth_array_max == depth_array_max_comp:
                arcpy.AddMessage(
                    "Skipped building environment value array for " + str(input_bathymetry_split_i))
            else:
                depth_array_min_comp <= depth_array_min
                depth_array_max_comp >= depth_array_max
                arcpy.AddMessage("Building environment value array: " + str(input_bathymetry_split_i))
                # rgi, y_vals_min, y_vals_max, x_vals_min, x_vals_max = build_env_array(input_environment, environment_name, depth_array_min, depth_array_max,input_bathymetry_extent.YMin, input_bathymetry_extent.YMax, input_bathymetry_extent.XMin, input_bathymetry_extent.XMax)


                # deal with single row/column data
                if depth_array_y_min == depth_array_y_max:
                    depth_array_y_min = depth_array_y_min - input_environment0_cs
                    depth_array_y_max = depth_array_y_max + input_environment0_cs

                if depth_array_x_min == depth_array_x_max:
                    depth_array_x_min = depth_array_x_min - input_environment0_cs
                    depth_array_x_max = depth_array_x_max + input_environment0_cs

                rgi, y_vals_min, y_vals_max, x_vals_min, x_vals_max = build_env_array(input_environment,
                                                                                      environment_name,
                                                                                      depth_array_min,
                                                                                      depth_array_max,
                                                                                      depth_array_y_min,
                                                                                      depth_array_y_max,
                                                                                      depth_array_x_min,
                                                                                      depth_array_x_max)

            depth_array = depth_array.iloc[::-1]
            arcpy.AddMessage("Trilinearly interpolating: " + str(input_bathymetry_split_i))

            # Check for edge issue
            if depth_array_x_min < x_vals_min or depth_array_x_max > x_vals_max or depth_array_y_min < y_vals_min or depth_array_y_max > y_vals_max:
                edge = True
            else:
                edge = False

            f = open(os.path.join(output_directory, "SplitRaster", "Outputs",
                                  "tri_" + str(input_bathymetry_split_i) + ".xyz"), 'w')

            if not edge:
                for index, row in depth_array.iterrows():
                    if not np.isnan(row["depth"]) and row["depth"] >= 5500.:
                        tri_value_list.append(rgi((row["x"], row["y"], 5499.0)))
                        f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                            rgi((row["x"], row["y"], 5499.0))) + ', Flag 4\n')
                    elif np.isnan(row["depth"]):
                        tri_value_list.append("-9999")
                        f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + "-9999" + ", Flag 3\n")
                    elif not np.isnan(row["depth"]):
                        tri_value_list.append(rgi((row["x"], row["y"], row["depth"])))
                        f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                            rgi((row["x"], row["y"], row["depth"]))) + ", Flag 2" + '\n')
            elif edge:
                # Deal with edge effect
                for index, row in depth_array.iterrows():
                    if not np.isnan(row["depth"]) and row["depth"] >= 5500.:
                        # In appropriate space
                        if row["x"] > x_vals_min and row["x"] < x_vals_max and row["y"] > y_vals_min and row[
                            "y"] < y_vals_max:
                            tri_value_list.append(rgi((row["x"], row["y"], 5499.0)))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((row["x"], row["y"], 5499.0))) + ", OKDeep" + '\n')
                        # Bottom Left
                        elif row["x"] < x_vals_min and row["y"] < y_vals_min:
                            tri_value_list.append(rgi((x_vals_min, y_vals_min, 5499.0)))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((x_vals_min, y_vals_min, 5499.0))) + ", BotLeftDeep" + '\n')
                        # Upper Left
                        elif row["x"] < x_vals_min and row["y"] > y_vals_max:
                            tri_value_list.append(rgi((x_vals_min, y_vals_max, 5499.0)))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((row["x"], row["y"], 5499.0))) + ", UpLeftDeep" + '\n')
                        # Bottom Right
                        elif row["x"] > x_vals_max and row["y"] < y_vals_min:
                            tri_value_list.append(rgi((x_vals_max, y_vals_min, 5499.0)))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((x_vals_max, y_vals_min, 5499.0))) + ", BotRightDeep" + '\n')
                        # Upper Right
                        elif row["x"] > x_vals_max and row["y"] > y_vals_max:
                            tri_value_list.append(rgi((x_vals_max, y_vals_max, 5499.0)))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((x_vals_max, y_vals_max, 5499.0))) + ", UpRightDeep" + '\n')
                        # Top
                        elif row["y"] > y_vals_max:
                            tri_value_list.append(rgi((row["x"], y_vals_max, 5499.0)))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((row["x"], y_vals_max, 5499.0))) + ", TopDeep" + '\n')
                        # Bottom
                        elif row["y"] < y_vals_min:
                            tri_value_list.append(rgi((row["x"], y_vals_min, 5499.0)))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((row["x"], y_vals_min, 5499.0))) + ", BotDeep" + '\n')
                        # Left
                        elif row["x"] < x_vals_min:
                            tri_value_list.append(rgi((x_vals_min, row["y"], 5499.0)))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((x_vals_min, row["y"], 5499.0))) + ", LeftDeep" + '\n')
                        # Right
                        elif row["x"] > x_vals_max:
                            tri_value_list.append(rgi((x_vals_max, row["y"], 5499.0)))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((x_vals_max, row["y"], 5499.0))) + ", RightDeep" + '\n')
                    elif np.isnan(row["depth"]):
                        tri_value_list.append("-9999")
                        f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + "-9999" + ", Flagged 1" + '\n')
                    elif not np.isnan(row["depth"]):
                        # In appropriate space
                        if row["x"] > x_vals_min and row["x"] < x_vals_max and row["y"] > y_vals_min and row[
                            "y"] < y_vals_max:
                            tri_value_list.append(rgi((row["x"], row["y"], row["depth"])))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((row["x"], row["y"], row["depth"]))) + ", OK, " + str(row["depth"]) + '\n')
                        # Bottom Left
                        elif row["x"] < x_vals_min and row["y"] < y_vals_min:
                            tri_value_list.append(rgi((x_vals_min, y_vals_min, row["depth"])))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((x_vals_min, y_vals_min, row["depth"]))) + ", BotLeft" + '\n')
                        # Upper Left
                        elif row["x"] < x_vals_min and row["y"] > y_vals_max:
                            tri_value_list.append(rgi((x_vals_min, y_vals_max, row["depth"])))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((x_vals_min, y_vals_max, row["depth"]))) + ", UpLeft" + '\n')
                        # Bottom Right
                        elif row["x"] > x_vals_max and row["y"] < y_vals_min:
                            tri_value_list.append(rgi((x_vals_max, y_vals_min, row["depth"])))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((x_vals_max, y_vals_min, row["depth"]))) + ", BotRight" + '\n')
                        # Upper Right
                        elif row["x"] > x_vals_max and row["y"] > y_vals_max:
                            tri_value_list.append(rgi((x_vals_max, y_vals_max, row["depth"])))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((x_vals_max, y_vals_max, row["depth"]))) + ", UpRight" + '\n')
                        # Top
                        elif row["y"] > y_vals_max:
                            tri_value_list.append(rgi((row["x"], y_vals_max, row["depth"])))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((row["x"], y_vals_max, row["depth"]))) + ", Top" + '\n')
                        # Bottom
                        elif row["y"] < y_vals_min:
                            tri_value_list.append(rgi((row["x"], y_vals_min, row["depth"])))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((row["x"], y_vals_min, row["depth"]))) + ", Bottom" + '\n')
                        # Left
                        elif row["x"] < x_vals_min:
                            tri_value_list.append(rgi((x_vals_min, row["y"], row["depth"])))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((x_vals_min, row["y"], row["depth"]))) + ", Left" + '\n')
                        # Right
                        elif row["x"] > x_vals_max:
                            tri_value_list.append(rgi((x_vals_max, row["y"], row["depth"])))
                            f.write(str(row["x"]) + ", " + str(row["y"]) + ", " + str(
                                rgi((x_vals_max, row["y"], row["depth"]))) + ", Right" + '\n')
                    else:
                        f.write(str(row["x"]) + ", " + str(row["y"]) + ", 100000" + ', Flag 5\n')

            f.close()

            # Get headers
            with open(os.path.join(output_directory, "SplitRaster",
                                   str(input_bathymetry_split_i) + ".asc")) as myfile:
                header_ascii = myfile.readlines()[0:6]  # put here the interval you want
            # arcpy.AddMessage("ASCII Header: " + str(header_ascii))

            # Write headers to new file
            with open(os.path.join(output_directory, "SplitRaster", "Outputs",
                                   str(input_bathymetry_split_i) + ".asc"), 'a') as ascii_file:
                for wr in header_ascii:
                    ascii_file.write(wr)

            with open(os.path.join(output_directory, "SplitRaster", "Outputs",
                                   str(input_bathymetry_split_i) + ".asc"), 'a') as ascii_file:
                for tri in tri_value_list:
                    ascii_file.write(str(tri) + " ")

            arcpy.AddMessage("Completed block: " + str(input_bathymetry_split_i))

            del tri_value_list, tri, depth_array, depth_array_min, depth_array_max, input_bathymetry_split
        else:
            arcpy.AddMessage("Skipping empty or previously completed raster: " + str(input_bathymetry_split_i))
            del input_bathymetry_split

        return  # End mpprocess def

    def execute(self, parameters, messages):
        """The source code of your tool."""
        arcpy.env.overwriteOutput = True
        arcpy.CheckOutExtension("Spatial")

        arcpy.AddMessage("Trilinear interpolation")

        t_start = time.clock()

        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText))

        input_bathymetry = parameters[0].valueAsText
        input_environment = parameters[1].valueAsText
        environment_name = parameters[2].valueAsText
        output_directory = parameters[3].valueAsText
        cpu_cores_used = parameters[4].valueAsText

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

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
        input_bathymetry_cs = input_bathymetry_desc.meanCellHeight

        input_environment0_desc = arcpy.Describe(input_environment_list[0])
        input_environment0_sr = input_environment0_desc.spatialReference
        input_environment0_cs = input_environment0_desc.meanCellHeight
        input_environment0_cs_x_min = input_environment0_desc.extent.XMin
        input_environment0_cs_y_min = input_environment0_desc.extent.YMin

        if input_bathymetry_sr.type == "Projected" and input_environment0_sr.type == "Projected":
            arcpy.AddMessage("Both depth and environmental data are in valid projection")
            if input_bathymetry_sr.name == input_environment0_sr.name:
                pass
            else:
                arcpy.AddMessage(
                    "Error: Depth and environmental data are in different projections, must be identical")
                sys.exit(0)
            pass
        else:
            arcpy.AddMessage("Error: Both depth and environmental data need to be in projected coordinate system")
            sys.exit(0)
        # del input_bathymetry_desc, input_bathymetry_sr, input_environment0_desc, input_environment0_sr

        if not os.path.exists(os.path.join(output_directory, "SplitRaster")):
            os.makedirs(os.path.join(output_directory, "SplitRaster"))
            arcpy.SplitRaster_management(in_raster=input_bathymetry,
                                         out_folder=os.path.join(output_directory, "SplitRaster"),
                                         out_base_name="sp", split_method="SIZE_OF_TILE", format="GRID",
                                         resampling_type="NEAREST", num_rasters="2 2", tile_size="1500 1500",
                                         overlap="0",
                                         units="PIXELS", cell_size="", origin="", split_polygon_feature_class="",
                                         clip_type="NONE", template_extent="DEFAULT", nodata_value="#")

        if not os.path.exists(os.path.join(output_directory, "SplitRaster", "Outputs")):
            os.makedirs(os.path.join(output_directory, "SplitRaster", "Outputs"))

        env.workspace = os.path.join(output_directory, "SplitRaster")
        input_bathymetry_list = arcpy.ListRasters("sp*", "GRID")

        arcpy.AddMessage("There are " + str(len(input_bathymetry_list)) + " depth blocks to process.")

        arcpy.AddMessage("Will use " + str(cpu_cores_used) + " cores for processing")

        input_bathymetry_list_done = []

        for i in input_bathymetry_list:
            try:
                r = arcpy.Raster(os.path.join(output_directory, "SplitRaster", i))
            except:
                r = False

            if arcpy.Exists(r) and not arcpy.Exists(os.path.join(output_directory,
                                                                 "SplitRaster",
                                                                 "Outputs",
                                                                 str(i) + ".asc")):
                input_bathymetry_list_done.append(i)
                del r

        arcpy.AddMessage("There are " + str(len(input_bathymetry_list_done)) + " depth left to process.")
        pool = multiprocessing.Pool(int(cpu_cores_used))
        func = partial(test, output_directory, input_environment_depth, input_environment0_cs, input_environment,
                       input_environment_name, input_environment0_cs_x_min, input_environment0_cs_y_min)
        pool.map(func, input_bathymetry_list_done)
        pool.close()

        env.workspace = os.path.join(output_directory, "SplitRaster", "Outputs")
        output_list = arcpy.ListRasters("*", "ALL")

        if not os.path.exists(os.path.join(output_directory, "SplitRaster", "Outputs_C")):
            os.makedirs(os.path.join(output_directory, "SplitRaster", "Outputs_C"))

        if len(output_list) > 200:
            output_list_chunk = [output_list[x:x + 20] for x in xrange(0, len(output_list), 20)]
        else:
            output_list_chunk = [output_list[x:x + 5] for x in xrange(0, len(output_list), 5)]

        arcpy.AddMessage("Building pool to mosaic " + str(len(output_list)) + " rasters, " + "in " + str(
            len(output_list_chunk)) + " chunks.")

        pool2 = multiprocessing.Pool(int(cpu_cores_used))
        func_mosaic = partial(mosaic_chunk, output_directory, input_bathymetry_cs)
        pool2.map(func_mosaic, output_list_chunk)
        pool2.close()

        chunk_list_a = []
        for chunk in output_list_chunk:
            if arcpy.Exists(os.path.join(output_directory, "SplitRaster", "Outputs_C", str(chunk[0]) + "_f", "a")):
                chunk_list_a.append(
                    os.path.join(output_directory, "SplitRaster", "Outputs_C", str(chunk[0]) + "_f", "a"))

        env.workspace = os.path.join(output_directory, "SplitRaster", "Outputs_C")

        arcpy.AddMessage("Mosaicking " + str(len(chunk_list_a)) + " chunks together.")

        arcpy.MosaicToNewRaster_management(
            input_rasters=chunk_list_a,
            output_location=os.path.join(output_directory),
            raster_dataset_name_with_extension="f", coordinate_system_for_the_raster="",
            pixel_type="32_BIT_FLOAT",
            cellsize=input_bathymetry_cs, number_of_bands="1", mosaic_method="MEAN", mosaic_colormap_mode="MATCH")

        arcpy.AddMessage("Script complete in %s seconds." % (time.clock() - t_start))
        return


def main():
    tool = DeepSeaSDMToolsTrilinearInterpolationNumpy_mp()
    tool.execute(tool.getParameterInfo(), None)


if __name__ == '__main__':
    main()

