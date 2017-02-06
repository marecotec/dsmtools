# clip all by each other and export as a new format

# gubbins
import sys, os, select, string, getopt
import arcpy
from arcpy import env
from arcpy.sa import *

arcpy.CheckOutExtension("Spatial")

inDir = arcpy.GetParameterAsText(0)
outDir = arcpy.GetParameterAsText(1)
if not os.path.exists(outDir):
    os.makedirs(outDir)
cellSize = arcpy.GetParameterAsText(2)
finalDir = arcpy.GetParameterAsText(3)
if not os.path.exists(finalDir):
    os.makedirs(finalDir)
b = arcpy.GetParameterAsText(4)
if len(b) > 1:
    removeList = b.split(',')
else:
    removeList = ""

# set environment variables
arcpy.env.workspace = inDir
arcpy.CheckOutExtension("Spatial")
arcpy.env.pyramid = "PYRAMIDS 3 BILINEAR JPEG"
arcpy.env.rasterStatistics = "STATISTICS 4 6 (0)"
WKID = arcpy.GetParameterAsText(5)  # WGS-1984=4326
if not os.path.exists(WKID):
    sr = arcpy.SpatialReference()
    sr.factoryCode = WKID
    sr.create()
    env.outputCoordinateSystem = sr
else:
    sr = arcpy.SpatialReference()
    dataset = WKID
    WKID = arcpy.Describe(dataset).spatialReference
    env.outputCoordinateSystem = WKID

rasterList = arcpy.ListRasters("*")
arcpy.env.extent = rasterList[0]
arcpy.env.cellSize = cellSize
arcpy.env.scratchWorkspace = outDir

arcpy.AddMessage("Extent is: " + str(arcpy.env.extent))

# remove listed rasters from list
if len(removeList) >= 1:
    for rL in removeList:
        rL2 = os.path.basename(os.path.normpath(rL))
        rasterList.remove(rL2)
        arcpy.AddMessage(str(rL2) + " removed")

rasCount = len(rasterList)
arcpy.AddMessage("\nThere are " + str(rasCount) + " rasters to process")
arcpy.env.workspace = outDir
arcpy.env.scratchWorkspace = outDir
counter = 0

try:
    # list rasters in directory or workspace
    for item in rasterList:
        counter = counter + 1
        if not arcpy.Exists(os.path.join(outDir, item)):
            arcpy.env.mask = os.path.join(inDir, item)
            outConstRaster = CreateConstantRaster(1, "INTEGER", cellSize, "")
            outConstRaster.save(os.path.join(outDir, item))
            arcpy.env.mask = ""
        arcpy.AddMessage(str(counter) + " of " + str(rasCount))

    rasterList2 = arcpy.ListRasters("*")

    arcpy.env.mask = ""

    arcpy.AddMessage("\n\nCalculating sum of all rasters")
    outSUM = arcpy.gp.CellStatistics_sa(rasterList2, os.path.join(outDir, "temp1"), "SUM", "DATA")
    rasCountMax = arcpy.GetRasterProperties_management(os.path.join(outDir, "temp1"), "MAXIMUM")
    whereClause = "VALUE < " + str(rasCountMax)

    field = "VALUE"
    outSetNull = SetNull(os.path.join(outDir, "temp1"), 1, whereClause)
    outSetNull.save(os.path.join(outDir, "temp2"))
    arcpy.RasterToPolygon_conversion(os.path.join(outDir, "temp2"), os.path.join(outDir, "temp2.shp"), "NO_SIMPLIFY",
                                     field)

    counter = 0

    for item2 in rasterList:
        counter = counter + 1
        mask = os.path.join(outDir, "temp2")
        # arcpy.env.snapRaster = os.path.join(outDir,"temp2")
        arcpy.env.extent = os.path.join(outDir, "temp2.shp")
        arcpy.env.mask = os.path.join(outDir, "temp2.shp")

        if not arcpy.Exists(os.path.join(finalDir, item2)):
            arcpy.AddMessage("Now extracting by mask for " + str(counter) + " of " + str(rasCount))
            rclip = arcpy.sa.ApplyEnvironment(os.path.join(inDir, item2))
            rclip.save(os.path.join(finalDir, item2))

            # outExtractByMask = ExtractByMask(os.path.join(inDir,item2), mask)
            # outExtractByMask.save(os.path.join(finalDir,item2))
            dsc = arcpy.Describe(rclip)
            arcpy.AddMessage("Set: " + str(arcpy.env.extent))
            arcpy.AddMessage("Out: " + str(dsc.Extent))
        # arcpy.BuildPyramids_management(os.path.join(finalDir,item2))

    arcpy.AddMessage("Done")
except:
    arcpy.AddMessage(arcpy.GetMessages())
