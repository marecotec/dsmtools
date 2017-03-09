# !/usr/bin/env python
import arcpy
import os
from arcpy import env
from Includes import load_depth_string
from Includes import NetCDFFile
from Includes import raster_to_xyz
import pandas as pd
import gc
import numpy as np
import time
import multiprocessing
from functools import partial
import shutil
import sys

gc.enable()

arcpy.CheckOutExtension("Spatial")


def mpprocess_call(output_directory, variable_name, input_woa_netcdf, interpolation_procedure,
                   interpolation_resolution, coordinate_system, createxyz, extraction_extent, depth_range):
    DeepSeaSDMToolsExtractWOANetCDF_mp.mpprocess(output_directory, variable_name, input_woa_netcdf,
                                                 interpolation_procedure,
                                                 interpolation_resolution, coordinate_system, createxyz,
                                                 extraction_extent, depth_range)


class DeepSeaSDMToolsExtractWOANetCDF_mp(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        self.label = "Extract depth layers for variables from World Ocean Atlas NetCDF files (Multiprocessor)"
        self.description = """To use the cookie cutting approach of Davies & Guinotte (2011) or the trilinear
               interpolation, we first need to extract z-layers from our environmental data layers, which are usually
               encapsulated in NetCDF files."""
        self.canRunInBackground = True
        self.category = "Deep-sea SDM Tools"  # Use your own category here, or an existing one.

    def getParameterInfo(self):
        params = []

    def getParameterInfo(self):
        params = []

        input_woa_netcdf = arcpy.Parameter(name="input_woa_netcdf",
                                           displayName="Input WOA NetCDF file",
                                           datatype="DEFile",
                                           parameterType="Required",
                                           direction="Input",
                                           )
        input_woa_netcdf.value = "G:\Oceanographic_Data\Temperature\WOA13v2\Raw_NetCDF\Decadal_Average\woa13_decav_t00_04v2.nc"
        params.append(input_woa_netcdf)

        variable_name = arcpy.Parameter(displayName="Variable",
                                        name="variable_name",
                                        datatype="GPString",
                                        parameterType="Required",
                                        direction="Input")
        variable_name.value = "t_an"
        params.append(variable_name)

        depths = arcpy.Parameter(name="depths",
                                 displayName="Select depths (WOA13v2, WOA05, Steinacher or Custom (in CSV style)",
                                 datatype="GPString",
                                 parameterType="Required",
                                 direction="Input",
                                 )
        depths.value = "WOA13v2"
        params.append(depths)

        interpolation_procedure = arcpy.Parameter(name="interpolation_procedure",
                                                  displayName="Select interpolation procedure",
                                                  datatype="GPString",
                                                  parameterType="Required",
                                                  direction="Input",
                                                  )
        interpolation_procedure.filter.type = "ValueList"
        interpolation_procedure.filter.list = ["IDW", "Spline", "Kriging", "None"]
        interpolation_procedure.value = "Spline"
        params.append(interpolation_procedure)

        interpolation_resolution = arcpy.Parameter(name="interpolation_resolution",
                                                   displayName="Specify interpolation resolution",
                                                   datatype="GPString",
                                                   parameterType="Required",
                                                   direction="Input",
                                                   )
        interpolation_resolution.value = "0.2"
        params.append(interpolation_resolution)

        extraction_extent = arcpy.Parameter(name="extraction_extent",
                                            displayName="Extraction Extent",
                                            datatype="GPExtent",
                                            parameterType="Required",
                                            direction="Input",
                                            )
        extraction_extent.value = "-181 -91 181 91"
        params.append(extraction_extent)

        output_directory = arcpy.Parameter(name="output_directory",
                                           displayName="Output Directory",
                                           datatype="DEFolder",
                                           parameterType="Required",
                                           direction="Output",
                                           )
        output_directory.value = "G:\Oceanographic_Data\Temperature\WOA13v2\Gridded_Quarter\/"
        params.append(output_directory)

        coordinate_system = arcpy.Parameter(name="coordinate_system",
                                            displayName="Coordinate System",
                                            datatype="GPCoordinateSystem",
                                            parameterType="Optional",
                                            direction="Input",
                                            )
        coordinate_system.value = "PROJCS['World_Mercator',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984'," \
                                  "SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0]," \
                                  "UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator'],PARAMETER['False_Easting'," \
                                  "0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0]," \
                                  "PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]"
        params.append(coordinate_system)

        createxyz = arcpy.Parameter(name="createxyz",
                                    displayName="Create XYZ (needed for Trilinear interpolation)",
                                    datatype="GPString",
                                    parameterType="Required",
                                    direction="Output",
                                    )
        createxyz.filter.type = "ValueList"
        createxyz.filter.list = ["Only Geographic", "Only Projected", "Both", "None"]
        createxyz.value = "Only Projected"
        params.append(createxyz)

        cpu_cores_used = arcpy.Parameter(name="cpu_cores_used",
                                         displayName="Number of CPU cores to use",
                                         datatype="GPString",
                                         parameterType="Required",
                                         direction="Output",
                                         )
        params.append(cpu_cores_used)
        cpu_cores_used.value = "10"

        return params

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        netCDFSource = parameters[0].valueAsText

        if netCDFSource is not None:
            # Making sure that the layers source is a netCDF file
            if NetCDFFile.isNetCDF(netCDFSource):
                netCDFFile = NetCDFFile(netCDFSource)
                variables = netCDFFile.getVariables()
                parameters[1].filter.list = variables
        return

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        try:

            netCDFSource = parameters[0].valueAsText

            if netCDFSource is not None:
                # Making sure that the layers source is a netCDF file
                if not NetCDFFile.isNetCDF(netCDFSource):
                    parameters[0].setErrorMessage("Invalid input file. "
                                                  "A netCDF(.nc) "
                                                  "is expected.")
        except Exception:
            pass
        return

    @staticmethod
    def mpprocess(output_directory, variable_name, input_woa_netcdf, interpolation_procedure,
                  interpolation_resolution, coordinate_system, extraction_extent, createxyz, depth_range):
        try:
            i = depth_range

            arcpy.env.extent = extraction_extent

            arcpy.AddMessage("Processing depth: " + str(int(i)))

            out_temp_layer = variable_name[0:4] + str(int(i)) + ".shp"
            dimensionValues = "depth " + str(int(i))

            output_dir_geographic = os.path.join(output_directory, "temp", "Geographic",
                                                 variable_name[0:4] + str(int(i)))
            output_geographic = os.path.join(output_dir_geographic, variable_name[0:4] + str(int(i)))

            output_dir_projected = os.path.join(output_directory, "temp", "Projected", variable_name[0:4] + str(int(i)))
            output_projected = os.path.join(output_dir_projected, variable_name[0:4] + str(int(i)))

            if not os.path.exists(os.path.join(output_dir_projected, "xy_coords.yxz")) or os.path.exists(
                    os.path.join(output_dir_geographic, "xy_coords.yxz")):

                if not os.path.exists(output_dir_geographic):
                    os.makedirs(output_dir_geographic)

                if not os.path.exists(output_dir_projected):
                    os.makedirs(output_dir_projected)

                env.workspace = os.path.join(output_directory, "temp", variable_name[0:4] + str(int(i)))

                # 1 Extract layer to a temporary feature class
                arcpy.MakeNetCDFFeatureLayer_md(in_netCDF_file=input_woa_netcdf, variable=variable_name,
                                                x_variable="lon",
                                                y_variable="lat",
                                                out_feature_layer=out_temp_layer,
                                                row_dimension="lat;lon",
                                                z_variable="", m_variable="", dimension_values=dimensionValues,
                                                value_selection_method="BY_VALUE")

                # 2 Interpolate to higher resolution and 3 save to output directory
                if interpolation_procedure == "IDW":
                    status = "Interpolating " + str(int(i)) + " using IDW"
                    arcpy.gp.Idw_sa(out_temp_layer, variable_name, output_geographic,
                                    interpolation_resolution, "2", "VARIABLE 10", "")
                elif interpolation_procedure == "Spline":
                    status = "Interpolating " + str(int(i)) + " using Spline"
                    arcpy.CopyFeatures_management(out_temp_layer, os.path.join(output_dir_geographic, "out.shp"))
                    arcpy.gp.Spline_sa(out_temp_layer, variable_name, output_geographic,
                                       interpolation_resolution, "TENSION", "0.1", "10")
                    arcpy.Delete_management(
                        os.path.join(output_directory, "temp", "Geographic", variable_name[0:4] + str(int(i)),
                                     "out.shp"))
                elif interpolation_procedure == "Kriging":
                    status = "Interpolating " + str(int(i)) + " using Ordinary Kriging"
                    arcpy.gp.Kriging_sa(out_temp_layer, variable_name,
                                        output_geographic,
                                        "Spherical " + str(interpolation_resolution), interpolation_resolution,
                                        "VARIABLE 10", "")

                elif interpolation_procedure == "None":
                    status = "Making a raster for " + str(int(i))
                    arcpy.MakeNetCDFRasterLayer_md(in_netCDF_file=input_woa_netcdf, variable=variable_name,
                                                   x_dimension="lon", y_dimension="lat",
                                                   out_raster_layer=output_geographic,
                                                   band_dimension="", dimension_values="",
                                                   value_selection_method="BY_VALUE")

                if len(coordinate_system) > 1:
                    status = "Reprojecting " + variable_name[0:4] + str(int(i)) + "."
                    arcpy.ProjectRaster_management(output_geographic,
                                                   output_projected,
                                                   coordinate_system, "NEAREST", "#", "#", "#", "#")

                if createxyz == "Only Geographic" or createxyz == "Both":
                    status = "Building geographic xy coords for " + variable_name[0:4] + str(int(i)) + "."
                    raster_to_xyz(output_geographic,
                                  variable_name[0:4] + str(int(i)),
                                  output_dir_geographic,
                                  349000000.0)

                    df = pd.read_csv(os.path.join(output_dir_geographic, variable_name[0:4] + str(int(i)) + ".yxz"),
                                     header=0, names=["y", "x", "z"], sep=" ",
                                     dtype={"y": np.float32, "x": np.float32, "z": np.float32})
                    master = df[["x", "y"]].copy()
                    master.columns = ["x", "y"]
                    master = np.round(master, 4)
                    master.to_pickle(os.path.join(output_dir_geographic, "xy_coords.yxz"))
                    del master, df
                    gc.collect()

                if createxyz == "Only Projected" or createxyz == "Both":
                    status = "Building projected xy coords for " + variable_name[0:4] + str(int(i)) + "."
                    raster_to_xyz(output_projected,
                                  variable_name[0:4] + str(int(i)),
                                  output_dir_projected,
                                  349000000.0)

                    df = pd.read_csv(os.path.join(output_dir_projected, variable_name[0:4] + str(int(i)) + ".yxz"),
                                     header=0, names=["y", "x", "z"], sep=" ",
                                     dtype={"y": np.float32, "x": np.float32, "z": np.float32})
                    master = df[["x", "y"]].copy()
                    master.columns = ["x", "y"]
                    master = np.round(master, 4)
                    master.to_pickle(os.path.join(output_dir_projected, "xy_coords.yxz"))
                    del master, df
                    gc.collect()
            else:
                arcpy.AddMessage("Skipping " + str(int(i)) + ".")
        except:
            arcpy.AddMessage("Failed on " + str(int(i)) + ",at status: " + str(status))
            arcpy.AddMessage(arcpy.GetMessages())

    def execute(self, parameters, messages):

        t_start = time.clock()

        arcpy.env.overwriteOutput = True

        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText))

        input_woa_netcdf = parameters[0].valueAsText
        variable_name = parameters[1].valueAsText
        depths = parameters[2].valueAsText
        interpolation_procedure = parameters[3].valueAsText
        interpolation_resolution = parameters[4].valueAsText
        extraction_extent = parameters[5].valueAsText
        output_directory = parameters[6].valueAsText
        coordinate_system = parameters[7].valueAsText
        createxyz = parameters[8].valueAsText
        cpu_cores_used = parameters[9].valueAsText

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        if not os.path.exists(os.path.join(output_directory, "Projected")):
            os.makedirs(os.path.join(output_directory, "Projected"))

        if not os.path.exists(os.path.join(output_directory, "Geographic")):
            os.makedirs(os.path.join(output_directory, "Geographic"))

        arcpy.env.extent = extraction_extent

        arcpy.AddMessage("Extracting " + str(input_woa_netcdf) + ".")

        # Set environment variables and build other variables for processing
        arcpy.env.mask = ""
        arcpy.env.workspace = output_directory
        depth_range = load_depth_string(depths)

        arcpy.AddMessage("There are " + str(len(depth_range)) + " to process.")

        if int(cpu_cores_used) > int(multiprocessing.cpu_count()):
            cpu_cores_used = multiprocessing.cpu_count() - 1

        arcpy.AddMessage("Will use " + str(cpu_cores_used) + " cores for processing")

        python_exe = os.path.join(sys.exec_prefix, 'pythonw.exe')
        multiprocessing.set_executable(python_exe)

        pool = multiprocessing.Pool(int(cpu_cores_used))
        func = partial(mpprocess_call, output_directory, variable_name, input_woa_netcdf, interpolation_procedure,
                       interpolation_resolution, coordinate_system, extraction_extent, createxyz)
        pool.map(func, depth_range)
        pool.close()

        count = 0

        depth_range = load_depth_string(depths)

        for i in depth_range:
            try:
                output_geographic = os.path.join(output_directory, "temp", "Geographic",
                                                 variable_name[0:4] + str(int(i)), variable_name[0:4] + str(int(i)))
                if arcpy.Exists(output_geographic) and not arcpy.Exists(
                        os.path.join(output_directory, "Geographic", variable_name[0:4] + str(int(i)))):
                    shutil.copytree(output_geographic, os.path.join(output_directory, "Geographic",
                                                                    variable_name[0:4].lower() + str(int(i))))
            except:
                arcpy.AddMessage("Issue copying, geographic for depth " + str(int(i)))

            try:
                output_projected = os.path.join(output_directory, "temp", "Projected", variable_name[0:4] + str(int(i)),
                                                variable_name[0:4] + str(int(i)))
                if arcpy.Exists(output_projected) and not arcpy.Exists(
                        os.path.join(output_directory, "Projected", variable_name[0:4] + str(int(i)))):
                    shutil.copytree(output_projected, os.path.join(output_directory, "Projected",
                                                                   str(variable_name[0:4].lower() + str(int(i)))))
            except:
                arcpy.AddMessage("Issue copying, projected for depth " + str(int(i)))

            try:
                if count == 0:
                    if os.path.exists(
                            os.path.join(output_directory, "temp", "Projected", variable_name[0:4] + str(int(i)),
                                         "xy_coords.yxz")):
                        shutil.copyfile(
                            os.path.join(output_directory, "temp", "Projected", variable_name[0:4] + str(int(i)),
                                         "xy_coords.yxz"),
                            os.path.join(output_directory, "Projected", "xy_coords.yxz"))
                        count = 1
            except:
                arcpy.AddMessage("Issue copying, xyz coordiantes for depth " + str(int(i)))

        arcpy.AddMessage("Making pyramids and statistics for outputs")
        arcpy.BuildPyramidsandStatistics_management(in_workspace=os.path.join(output_directory, "Geographic"),
                                                    include_subdirectories="NONE",
                                                    build_pyramids="BUILD_PYRAMIDS",
                                                    calculate_statistics="CALCULATE_STATISTICS", BUILD_ON_SOURCE="NONE",
                                                    block_field="", estimate_statistics="NONE", x_skip_factor="1",
                                                    y_skip_factor="1", ignore_values="", pyramid_level="-1",
                                                    SKIP_FIRST="NONE", resample_technique="NEAREST",
                                                    compression_type="DEFAULT", compression_quality="75",
                                                    skip_existing="SKIP_EXISTING")
        if len(coordinate_system) > 1:
            arcpy.BuildPyramidsandStatistics_management(in_workspace=os.path.join(output_directory, "Projected"),
                                                        include_subdirectories="NONE",
                                                        build_pyramids="BUILD_PYRAMIDS",
                                                        calculate_statistics="CALCULATE_STATISTICS",
                                                        BUILD_ON_SOURCE="NONE",
                                                        block_field="", estimate_statistics="NONE", x_skip_factor="1",
                                                        y_skip_factor="1", ignore_values="", pyramid_level="-1",
                                                        SKIP_FIRST="NONE", resample_technique="NEAREST",
                                                        compression_type="DEFAULT", compression_quality="75",
                                                        skip_existing="SKIP_EXISTING")

        arcpy.AddMessage("Script complete in %s hours." % str((time.clock() - t_start) / 3600))

        return


def main():
    tool = DeepSeaSDMToolsExtractWOANetCDF_mp()
    tool.execute(tool.getParameterInfo(), None)


if __name__ == '__main__':
    main()


