import sys, os, select, string, getopt
import arcpy
from arcpy import env
from arcpy.sa import *

arcpy.CheckOutExtension("Spatial")

In_Master_Directory = arcpy.GetParameterAsText(0)
Out_Folder = arcpy.GetParameterAsText(1)
Statistic = arcpy.GetParameterAsText(2)
NullVal = arcpy.GetParameter(3)

if not os.path.exists(Out_Folder):
    os.makedirs(Out_Folder)

RasterListMaster = []
Counter = 1
arcpy.env.workspace = In_Master_Directory
RasterListMaster = arcpy.ListRasters("*")
arcpy.AddMessage("There are " + str(len(RasterListMaster)) + " rasters to process")
arcpy.AddMessage("Calculating statistic: " + str(Statistic) + ".")
if len(NullVal) > 1:
    arcpy.AddMessage("Having to Set Null values that = " + str(NullVal) + ".")
    for raster in RasterListMaster:
        arcpy.AddMessage("Processing raster " + str(Counter) + " of " + str(len(RasterListMaster)) + ".")
        newstr = (raster.replace(".", ""))
        if len(newstr) > 11:
            newstr = newstr[2:12]
        if arcpy.Exists(os.path.join(Out_Folder, newstr)):
            pass
        else:
            outSetNull = SetNull(raster, raster, str("VALUE = " + NullVal))
            outSetNull.save(os.path.join(Out_Folder, newstr))
        Counter = Counter + 1
    arcpy.env.workspace = Out_Folder
    RasterListMaster = arcpy.ListRasters("*")
    arcpy.AddMessage("Calculating statistics")
    outCellStats = CellStatistics(RasterListMaster, Statistic, "DATA")
    outCellStats.save(os.path.join(Out_Folder, str(Statistic)))
else:
    arcpy.AddMessage("Calculating statistics")
    outCellStats = CellStatistics(RasterListMaster, Statistic, "DATA")
    outCellStats.save(os.path.join(Out_Folder, str(Statistic)))
