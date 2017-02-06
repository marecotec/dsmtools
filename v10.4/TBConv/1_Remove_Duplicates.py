#clip all by each other and export as a new format

#gubbins
import sys, os, select, string, getopt
import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")

# get the map document
inRaster = arcpy.GetParameterAsText(0)
inSpecies = arcpy.GetParameterAsText(1)
tempDir = arcpy.GetParameterAsText(2)
if not os.path.exists(tempDir):
	os.makedirs(tempDir)
outSpecies = arcpy.GetParameterAsText(3)
recordIDfield = arcpy.GetParameterAsText(4)

#set environment variables
arcpy.env.workspace = tempDir
arcpy.CheckOutExtension("Spatial")
arcpy.env.extent = inRaster
arcpy.env.cellSize = inRaster

arcpy.AddMessage("There are " + str(arcpy.GetCount_management(inSpecies)) + " records to process")
valueList = []
valueSet = set()
rows = arcpy.SearchCursor(inSpecies)

for row in rows:
	value = row.getValue(recordIDfield)
	if value not in valueSet:
		valueList.append(value)
		valueSet.add(value)
valueList.sort()
del(rows,row,value)
arcpy.AddMessage("There are " + str(len(valueList)) + " unique groups. They are: " + str(valueList) + ".")
 
try:
	#Step 1- convert points to raster
	cellSizeRasterResult = arcpy.GetRasterProperties_management(inRaster, "CELLSIZEX")
	cellSizeRaster = cellSizeRasterResult.getOutput(0) 
	arcpy.PointToRaster_conversion(inSpecies, "FID", os.path.join(tempDir,"conv"), "COUNT", "NONE", cellSizeRaster)
	arcpy.RasterToPoint_conversion(os.path.join(tempDir,"conv"),os.path.join(tempDir,"conv_point.shp"),"VALUE")
	arcpy.PointToRaster_conversion(os.path.join(tempDir,"conv_point.shp"), "POINTID", os.path.join(tempDir,"conv2"), "SUM", "NONE", cellSizeRaster)
	#Step 2- convert to polygon
	arcpy.RasterToPolygon_conversion(os.path.join(tempDir,"conv2"), os.path.join(tempDir,"conv.shp"), "NO_SIMPLIFY", "VALUE")
	#Step 3- join points to polygon to create field for extraction/filtering in Excel
	arcpy.SpatialJoin_analysis(inSpecies,os.path.join(tempDir,"conv.shp"),outSpecies,"JOIN_ONE_TO_ONE","KEEP_ALL","","INTERSECT","#","#")

	for rec in valueList:
		arcpy.MakeFeatureLayer_management(outSpecies,"lr")
		whereString = '"%s" = ' %recordIDfield + "'%s'" %rec
		arcpy.management.SelectLayerByAttribute("lr","ADD_TO_SELECTION",whereString)
		arcpy.CopyFeatures_management("lr", os.path.join(tempDir, str(rec) + ".shp"))
		arcpy.Sort_management("lr", os.path.join(tempDir, str(rec) + "dedupe.shp"), [["GRIDCODE", "ASCENDING"]])
		arcpy.AddMessage(str(rec) + " contains " + str(arcpy.GetCount_management("lr")) + " records")
		arcpy.Delete_management("lr")
		del(whereString)
	
	for rec in valueList:
		layerloc = os.path.join(tempDir, str(rec) + "dedupe.shp")
		
		firstTime = True
		rows = arcpy.UpdateCursor(layerloc)
		xField = "GRIDCODE" # the field containing the x value
		yField = "FID" # the field containing the y value

		xValue = None
		yValue = None
		
		#Create an empty list
		firstTime = True

		for row in rows:
			if firstTime: #first time around
				xValue = int(row.getValue(xField))
				yValue = int(row.getValue(yField))
				firstTime = False
				
			else:
				if int(row.getValue(xField)) == xValue: #if same and not first time around
					#delete row
					rows.deleteRow(row)
				else:
					xValue = int(row.getValue(xField))
					yValue = int(row.getValue(yField))
		del(row,rows)
		arcpy.AddMessage(str(rec) + " deduped now contains " + str(arcpy.GetCount_management(layerloc)) + " records")

	arcpy.Merge_management(arcpy.ListFeatureClasses("*dedupe*"), os.path.join(tempDir, "de_duper_full_merge.shp"))

except:
	arcpy.AddMessage(arcpy.GetMessages())
	