import arcpy
import os
import sys
from arcpy import env
from arcpy.sa import *

arcpy.CheckOutExtension("Spatial")


class DeepSeaSDMToolsMatchEnvironmentalLayers(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        self.label = "Match all environmental layers to same pixel composition and extent"
        self.description = """This script takes a directory of rasters, and creates a new directory containing identical
        extents and pixel composition. Such an operation is required to allow for use in software such as
        Maxent."""
        self.canRunInBackground = True
        self.category = "Deep-sea SDM Tools"  # Use your own category here, or an existing one.

    def getParameterInfo(self):
        params = []

        input_directory = arcpy.Parameter(name="input_directory",
                                          displayName="Directory of rasters",
                                          datatype="DEWorkspace",
                                          parameterType="Required",
                                          direction="Input",
                                          )
        input_directory.value = "D:\Example\DeepSeaSDMToolsMatchEnvironmentalLayers\Unmatched"
        params.append(input_directory)

        output_directory = arcpy.Parameter(name="output_directory",
                                           datatype="DEWorkspace",
                                           parameterType="Required",  # Required|Optional|Derived
                                           direction="Output",  # Input|Output
                                           )
        output_directory.value = "D:\Example\DeepSeaSDMToolsMatchEnvironmentalLayers\Matched"
        params.append(output_directory)

        temporary_directory = arcpy.Parameter(name="temporary_directory",
                                           displayName="Temporary directory",
                                           datatype="DEWorkspace",
                                           parameterType="Required",  # Required|Optional|Derived
                                           direction="Output",  # Input|Output
                                           )
        temporary_directory.value = "D:\Example\DeepSeaSDMToolsMatchEnvironmentalLayers\Temporary"
        params.append(temporary_directory)

        cell_size = arcpy.Parameter(name="cell_size",
                                           displayName="Target cell size",
                                           datatype="GPString",
                                           parameterType="Required",  # Required|Optional|Derived
                                           direction="Input",  # Input|Output
                                           )
        cell_size.value = "0.1"
        params.append(cell_size)

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

        input_directory = parameters[0].valueAsText
        output_directory = parameters[1].valueAsText
        temporary_directory = parameters[2].valueAsText
        cell_size = parameters[3].valueAsText

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        if not os.path.exists(temporary_directory):
            os.makedirs(temporary_directory)

        if not os.path.exists(os.path.join(temporary_directory, "Unmatched_Copy")):
            os.makedirs(os.path.join(temporary_directory, "Unmatched_Copy"))

        if not os.path.exists(os.path.join(temporary_directory, "tempdir2")):
            os.makedirs(os.path.join(temporary_directory, "tempdir2"))

        # Set Environments
        arcpy.env.workspace = input_directory
        raster_list = arcpy.ListRasters("*")

        if not raster_list:
            arcpy.AddMessage("No rasters in the input directory found! Check path..")
            sys.exit()

        arcpy.CheckOutExtension("Spatial")
        arcpy.env.pyramid = "PYRAMIDS 3 BILINEAR JPEG"
        arcpy.env.rasterStatistics = "STATISTICS 4 6 (0)"
        arcpy.env.cellSize = cell_size
        arcpy.env.scratchWorkspace = temporary_directory

        for raster in raster_list:
            raster1 = arcpy.sa.Raster(raster)
            ext = raster1.extent

            cell_size_raster_2 = raster1.meanCellHeight
            xmin2 = ext.XMin
            xmax2 = ext.XMax
            ymin2 = ext.YMin
            ymax2 = ext.YMax

            xmin = min(xmin2, ext.XMin)
            ymin = min(ymin2, ext.XMax)
            xmax = max(xmax2, ext.YMin)
            ymax = max(ymax2, ext.YMax)
            cell_size_raster = min(cell_size_raster_2, raster1.meanCellHeight)
            extent_valid = True

        if extent_valid:
            arcpy.env.extent = str(xmin) + " " + str(ymin) + " " + str(xmax) + " " + str(ymax)
            arcpy.AddMessage("Extraction extent is: " + str(arcpy.env.extent))
        else:
            arcpy.env.extent = raster_list[0]
            arcpy.AddMessage("Extraction extent of first input: " + str(arcpy.env.extent))

        if cell_size == cell_size_raster:
            for raster in raster_list:
                arcpy.Copy_management(in_data=raster,
                                      out_data=os.path.join(temporary_directory, "Unmatched_Copy", raster),
                                      data_type="RasterDataset")
                arcpy.AddMessage("Cell size requested is same as input rasters.. Proceeding...")
        else:
            arcpy.AddMessage("Cell size requested is different as input rasters.. Resampling...")
            for raster in raster_list:
                arcpy.Resample_management(in_raster=raster,
                                          out_raster=os.path.join(temporary_directory, "Unmatched_Copy", raster),
                                          cell_size=str(cell_size) + " " + str(cell_size), resampling_type="BILINEAR")


        coordinate_system = arcpy.Describe(os.path.join(temporary_directory, "Unmatched_Copy", raster_list[0])).spatialReference
        env.outputCoordinateSystem = coordinate_system

        arcpy.AddMessage("There are " + str(len(raster_list)) + " rasters to process")
        arcpy.env.workspace = temporary_directory
        arcpy.env.scratchWorkspace = temporary_directory
        counter = 0

        try:
            # List rasters in directory and convert to a constant raster
            for raster in raster_list:
                counter += 1
                if not arcpy.Exists(os.path.join(temporary_directory, raster)):
                    arcpy.env.extent = os.path.join(temporary_directory, "Unmatched_Copy", raster)
                    arcpy.env.mask = os.path.join(temporary_directory, "Unmatched_Copy", raster)
                    arcpy.gp.IsNull_sa(os.path.join(temporary_directory, "Unmatched_Copy", raster), os.path.join(temporary_directory, raster))
                    arcpy.gp.Con_sa(os.path.join(temporary_directory, raster), "1",
                                    os.path.join(temporary_directory, "tempdir2", raster), "0", "VALUE = 0")
                    arcpy.env.mask = ""
                arcpy.AddMessage("Processing " + str(counter) + " of " + str(len(raster_list)))

            del raster

            arcpy.env.workspace = os.path.join(temporary_directory, "tempdir2")
            raster_list_2 = arcpy.ListRasters("*")
            arcpy.env.mask = ""

            arcpy.AddMessage("Calculating sum of all rasters")
            arcpy.gp.CellStatistics_sa(raster_list_2, os.path.join(temporary_directory, "temp1"), "SUM", "DATA")
            count_all_constant = arcpy.GetRasterProperties_management(os.path.join(temporary_directory, "temp1"), "MAXIMUM")
            where_clause = "VALUE < " + str(count_all_constant)

            field = "VALUE"
            outSetNull = SetNull(os.path.join(temporary_directory, "temp1"), 1, where_clause)
            outSetNull.save(os.path.join(temporary_directory, "temp2"))
            arcpy.RasterToPolygon_conversion(os.path.join(temporary_directory, "temp2"), os.path.join(temporary_directory, "temp2.shp"),
                                             "NO_SIMPLIFY",
                                             field)

            arcpy.env.workspace = os.path.join(temporary_directory, "Unmatched_Copy")
            raster_list = arcpy.ListRasters("*")

            counter = 0

            for raster in raster_list:
                counter += 1
                mask = os.path.join(temporary_directory, "temp2")
                arcpy.env.snapRaster = os.path.join(temporary_directory, "temp2")
                arcpy.env.extent = os.path.join(temporary_directory, "temp2.shp")
                arcpy.env.mask = os.path.join(temporary_directory, "temp2.shp")

                if not arcpy.Exists(os.path.join(output_directory, raster)):
                    arcpy.AddMessage("Now extracting by mask for " + str(counter) + " of " + str(len(raster_list)))
                    raster_clip = arcpy.sa.ApplyEnvironment(os.path.join(temporary_directory, "Unmatched_Copy", raster))
                    raster_clip.save(os.path.join(output_directory, raster))
            arcpy.AddMessage("Done")

        except:
            arcpy.AddMessage(arcpy.GetMessages())

        return


def main():
    tool = DeepSeaSDMToolsMatchEnvironmentalLayers()
    tool.execute(tool.getParameterInfo(), None)


if __name__ == '__main__':
    main()
