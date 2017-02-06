# Single point time series extract

# Import dependencies
import sys, os, select, string, getopt, csv
import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")

In_Point_X = arcpy.GetParameterAsText(0)
In_Point_Y = arcpy.GetParameterAsText(1)
In_Directory = arcpy.GetParameterAsText(2)
OutCSV = arcpy.GetParameterAsText(3)


# Get rasters in directory
env.workspace = In_Directory
rasterList = arcpy.ListRasters("*")
arcpy.AddMessage("There are " + str(len(rasterList)) + " rasters to process.")

# Get xy location - single point only
with open(OutCSV, 'wb') as test_file:
	csv_writer = csv.writer(test_file)
	csv_writer.writerow(["rastername", "value"])
	for raster in rasterList:
		result = arcpy.GetCellValue_management(raster, str(In_Point_X) + " " + str(In_Point_Y), "#")
		value = result.getOutput(0)
		csv_writer.writerow([str(raster), str(value)])