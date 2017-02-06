import sys, os, select, string, getopt
import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")

In_Directory =  arcpy.GetParameterAsText(0)
Out_Folder = arcpy.GetParameterAsText(1)
if not os.path.exists(Out_Folder):
	os.makedirs(Out_Folder)
Filter_Value = arcpy.GetParameterAsText(2)
Cell_Size = arcpy.GetParameterAsText(3)

#reinterpolate

RasterList = []
arcpy.env.workspace = In_Directory
RasterList = arcpy.ListRasters("*")

for rst in RasterList:
	outRasterLayer = "z" + rst
	points = os.path.join(Out_Folder, str(rst) + ".shp")
	#test raster
	#Get the geoprocessing result object
	try:
		testRasterResult = arcpy.GetRasterProperties_management(rst, "STD")
		testRaster = testRasterResult.getOutput(0)
		testRaster = 1
	except:
		testRaster = 0
	
	if testRaster == 0:
		arcpy.AddMessage("Skipping " + str(rst))
	else:
		
		arcpy.CopyRaster_management(os.path.join(In_Directory, rst),os.path.join(Out_Folder, rst + "2"))
		os.remove(os.path.join(Out_Folder, rst + "2", "prj.adf"))	
		arcpy.RasterToPoint_conversion(os.path.join(Out_Folder, rst + "2"), points, "VALUE")
		points2 = os.path.join(Out_Folder, str(rst) + "2.shp")
		arcpy.Select_analysis(points, points2, Filter_Value)
		arcpy.gp.Kriging_sa(points2, "GRID_CODE", os.path.join(Out_Folder,outRasterLayer), "Spherical " + Cell_Size,Cell_Size,"VARIABLE 12","#")