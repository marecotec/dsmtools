# Import dependencies
import sys, os, select, string, getopt
import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")

In_Raster = arcpy.GetParameterAsText(0)
Out_Raster = arcpy.GetParameterAsText(1)
Cell_Size = arcpy.GetParameterAsText(2)
InterpType = arcpy.GetParameterAsText(3)
Mask_Data = arcpy.GetParameterAsText(4)

arcpy.AddMessage("Resampling to cellsize: " + str(Cell_Size) + " with " + str(InterpType) + " interpolation.")
arcpy.Resample_management(In_Raster, "in_memory", Cell_Size, InterpType)
arcpy.AddMessage("Extracting by mask")
outExtractByMask = ExtractByMask("in_memory", Mask_Data)
outExtractByMask.save(Out_Raster)
