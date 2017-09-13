#!/usr/bin/env python
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

gc.enable()

arcpy.CheckOutExtension("Spatial")


# noinspection PyPep8Naming
class DeepSeaSDMToolsExtractWOANetCDF(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        self.label = "Extract depth layers for variables from World Ocean Atlas NetCDF files"
        self.description = """To use the cookie cutting approach of Davies & Guinotte (2011) or the trilinear
               interpolation for the upcoming GlobENV approach, we first need to extract z-layers from our environmental data layers, which are usually
               encapsulated in NetCDF files (or at least that's the easiest file format for us to work with)."""
        self.canRunInBackground = True
        self.category = "Deep-sea SDM Tools"  # Use your own category here, or an existing one.

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
        #extraction_extent.value = "-16 55 -13 57"
        params.append(extraction_extent)

        temporary_directory = arcpy.Parameter(name="temporary_directory",
                                              displayName="Temporary Directory",
                                              datatype="DEWorkspace",
                                              parameterType="Required",
                                              direction="Output",
                                              )
        temporary_directory.value = "G:\Oceanographic_Data\Temperature\WOA13v2\Gridded_Quarter\Temp/"
        params.append(temporary_directory)

        output_directory = arcpy.Parameter(name="output_directory",
                                           displayName="Output Directory",
                                           datatype="DEWorkspace",
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
        temporary_directory = parameters[6].valueAsText
        output_directory = parameters[7].valueAsText
        coordinate_system = parameters[8].valueAsText
        createxyz = parameters[9].valueAsText

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        if not os.path.exists(os.path.join(output_directory, "Projected")):
            os.makedirs(os.path.join(output_directory, "Projected"))

        if not os.path.exists(os.path.join(output_directory, "Geographic")):
            os.makedirs(os.path.join(output_directory, "Geographic"))

        if not os.path.exists(temporary_directory):
            os.makedirs(temporary_directory)

        arcpy.env.extent = extraction_extent

        arcpy.AddMessage("Extracting " + str(input_woa_netcdf) + ".")

        # Set environment variables and build other variables for processing
        arcpy.env.mask = ""
        arcpy.env.workspace = temporary_directory
        depth_range = load_depth_string(depths)

        # Process goes: 1) Convert depth layer to a point file. 2) Interpolate to selected resolution using your selected
        # interpolation procedure, 3) Save that layer back into a layer with the name of the variable, plus the
        # actual depth value associated with it, you will end up with a specified direction of n rasters (n = number of
        # depth layers.

        # First lets give an indication of the magnitude of this analysis
        arcpy.AddMessage("There are " + str(len(depth_range)) + " to process.")

        count_geo = 0
        count_proj = 0

        for i in depth_range:
            arcpy.AddMessage("Working on " + str(int(i)))

            # Set some values that we will use to extract data from the NetCDF file
            out_temp_layer = variable_name[0:4] + str(int(i)) + ".shp"

            dimensionValues = "depth " + str(int(i))

            # 1 Extract layer to a temporary feature class
            arcpy.MakeNetCDFFeatureLayer_md(in_netCDF_file=input_woa_netcdf, variable=variable_name, x_variable="lon",
                                            y_variable="lat",
                                            out_feature_layer=out_temp_layer,
                                            row_dimension="lat;lon",
                                            z_variable="", m_variable="", dimension_values=dimensionValues,
                                            value_selection_method="BY_VALUE")

            # 2 Interpolate to higher resolution and 3 save to output directory
            if interpolation_procedure == "IDW":
                arcpy.AddMessage("Interpolating " + str(int(i)) + " using IDW")
                arcpy.gp.Idw_sa(out_temp_layer, variable_name,
                                os.path.join(output_directory, "Geographic", variable_name[0:4] + str(int(i))),
                                interpolation_resolution, "2", "VARIABLE 10", "")
            elif interpolation_procedure == "Spline":
                arcpy.AddMessage("Interpolating " + str(int(i)) + " using Spline")
                arcpy.CopyFeatures_management(out_temp_layer, os.path.join(output_directory, "out.shp"))
                arcpy.gp.Spline_sa(out_temp_layer, variable_name,
                                   os.path.join(output_directory, "Geographic", variable_name[0:4] + str(int(i))),
                                   interpolation_resolution, "TENSION", "0.1", "10")
                arcpy.Delete_management(os.path.join(output_directory, "out.shp"))
            elif interpolation_procedure == "Kriging":
                arcpy.AddMessage("Interpolating " + str(int(i)) + " using Ordinary Kriging")
                arcpy.gp.Kriging_sa(out_temp_layer, variable_name,
                                    os.path.join(output_directory, "Geographic", variable_name[0:4] + str(int(i))),
                                    "Spherical " + str(interpolation_resolution), interpolation_resolution,
                                    "VARIABLE 10", "")
            elif interpolation_procedure == "None":
                arcpy.AddMessage("Making a raster for " + str(int(i)))
                arcpy.MakeNetCDFRasterLayer_md(in_netCDF_file=input_woa_netcdf, variable=variable_name,
                                               x_dimension="lon", y_dimension="lat",
                                               out_raster_layer=variable_name[0:4] + str(int(i)),
                                               band_dimension="", dimension_values="",
                                               value_selection_method="BY_VALUE")
                arcpy.CopyRaster_management(variable_name[0:4] + str(int(i)),
                                            os.path.join(output_directory, "Geographic", variable_name[0:4] + str(int(i))),
                                            "", "", "", "NONE", "NONE", "")

            if len(coordinate_system) > 1:
                arcpy.AddMessage("Reprojecting " + variable_name[0:4] + str(int(i)) + ".")
                arcpy.ProjectRaster_management(os.path.join(output_directory, "Geographic", variable_name[0:4] + str(int(i))),
                                               os.path.join(output_directory, "Projected", variable_name[0:4] + str(int(i))),
                                               coordinate_system, "NEAREST", "#", "#", "#", "#")

            arcpy.AddMessage("Generating master file for trilinear interpolation")

            if createxyz == "Only Geographic" or createxyz == "Both":
                if not os.path.exists(os.path.join(output_directory, "Geographic_yxz")):
                    os.makedirs(os.path.join(output_directory, "Geographic_yxz"))
                raster_to_xyz(os.path.join(output_directory, "Geographic", variable_name[0:4] + str(int(i))),
                              variable_name[0:4] + str(int(i)),
                              os.path.join(output_directory, "Geographic_yxz"), 349000000.0)
                depth = int(filter(str.isdigit, str(i)))

                if count_geo == 0:
                    df = pd.read_csv(os.path.join(output_directory, "Geographic_yxz", variable_name[0:4] + str(int(i)) + ".yxz"),
                                     header=0, names=["y", "x", "z"], sep=" ", dtype={"y": np.float64,  "x": np.float64, "z": np.float64})
                    master = df[["x", "y", "z"]].copy()
                    master.columns = ["x", "y", int(depth)]
                    master.to_pickle(os.path.join(output_directory, "Geographic_yxz", "master.pkl"))
                    os.remove(os.path.join(output_directory, "Geographic_yxz", variable_name[0:4] + str(int(i)) + ".yxz"))
                    del df, master
                    gc.collect()
                    count_geo = 1
                if count_geo == 1:
                    master = pd.read_pickle(os.path.join(output_directory, "Geographic_yxz", "master.pkl"))
                    df = pd.read_csv(os.path.join(output_directory, "Geographic_yxz", variable_name[0:4] + str(int(i)) + ".yxz"),
                                     header=0, names=["y", "x", "z"], sep=" ", dtype={"y": np.float64,  "x": np.float64, "z": np.float64})
                    master[int(depth)] = df["z"].copy()
                    master.to_pickle(os.path.join(output_directory, "Geographic_yxz", "master.pkl"))
                    os.remove(os.path.join(output_directory, "Geographic_yxz", variable_name[0:4] + str(int(i)) + ".yxz"))
                    del df, master
                    gc.collect()

            if createxyz == "Only Projected" or createxyz == "Both":
                if not os.path.exists(os.path.join(output_directory, "Projected_yxz")):
                    os.makedirs(os.path.join(output_directory, "Projected_yxz"))
                raster_to_xyz(os.path.join(output_directory, "Projected", variable_name[0:4] + str(int(i))),
                              variable_name[0:4] + str(int(i)),
                              os.path.join(output_directory, "Projected_yxz"), 349000000.0)

                depth = int(filter(str.isdigit, str(i)))

                if count_proj == 0:
                    df = pd.read_csv(os.path.join(output_directory, "Projected_yxz", variable_name[0:4] + str(int(i)) + ".yxz"),
                                     header=0, names=["y", "x", "z"], sep=" ", dtype={"y": np.float64,  "x": np.float64, "z": np.float64})
                    master = df[["x", "y"]].copy()
                    master.columns = ["x", "y"]
                    master = np.round(master, 4)
                    master.to_pickle(os.path.join(output_directory, "Projected_yxz", "xy_coords.pkl"))
                    master.to_pickle(os.path.join(output_directory, "Projected", "xy_coords.pkl"))
                    del master
                    gc.collect()
                    master_z = df[["z"]].copy()
                    master_z.columns = [int(depth)]
                    master_z = np.round(master_z, 4)
                    master_z.to_pickle(os.path.join(output_directory, "Projected_yxz", str(int(i)) + ".pkl"))
                    os.remove(os.path.join(output_directory, "Projected_yxz", variable_name[0:4] + str(int(i)) + ".yxz"))
                    del df, master_z
                    gc.collect()
                    count_proj = 1
                elif count_proj == 1:
                    df = pd.read_csv(os.path.join(output_directory, "Projected_yxz", variable_name[0:4] + str(int(i)) + ".yxz"),
                                     header=0, names=["y", "x", "z"], sep=" ", dtype={"y": np.float64,  "x": np.float64, "z": np.float64})
                    master_z = df[["z"]].copy()
                    master_z.columns = [int(depth)]
                    master_z = np.round(master_z, 4)
                    master_z.to_pickle(os.path.join(output_directory, "Projected_yxz", str(int(i)) + ".pkl"))
                    os.remove(os.path.join(output_directory, "Projected_yxz", variable_name[0:4] + str(int(i)) + ".yxz"))
                    del df, master_z
                    gc.collect()

        arcpy.AddMessage("Making pyramids and statistics for outputs")
        arcpy.BuildPyramidsandStatistics_management(in_workspace=os.path.join(output_directory, "Geographic"), include_subdirectories="NONE",
                                                    build_pyramids="BUILD_PYRAMIDS",
                                                    calculate_statistics="CALCULATE_STATISTICS", BUILD_ON_SOURCE="NONE",
                                                    block_field="", estimate_statistics="NONE", x_skip_factor="1",
                                                    y_skip_factor="1", ignore_values="", pyramid_level="-1",
                                                    SKIP_FIRST="NONE", resample_technique="NEAREST",
                                                    compression_type="DEFAULT", compression_quality="75",
                                                    skip_existing="SKIP_EXISTING")
        if len(coordinate_system) > 1:
            arcpy.BuildPyramidsandStatistics_management(in_workspace=os.path.join(output_directory, "Projected"), include_subdirectories="NONE",
                                                        build_pyramids="BUILD_PYRAMIDS",
                                                        calculate_statistics="CALCULATE_STATISTICS", BUILD_ON_SOURCE="NONE",
                                                        block_field="", estimate_statistics="NONE", x_skip_factor="1",
                                                        y_skip_factor="1", ignore_values="", pyramid_level="-1",
                                                        SKIP_FIRST="NONE", resample_technique="NEAREST",
                                                        compression_type="DEFAULT", compression_quality="75",
                                                        skip_existing="SKIP_EXISTING")

        arcpy.AddMessage("Script complete in %s seconds." % (time.clock() - t_start))

        return


def main():
    tool = DeepSeaSDMToolsExtractWOANetCDF()
    tool.execute(tool.getParameterInfo(), None)


if __name__ == '__main__':
    main()

