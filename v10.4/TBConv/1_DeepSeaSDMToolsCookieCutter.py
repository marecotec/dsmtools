





# Extrapolate EGV to bathymetry (aka Cookie Cutter)
#
# Uses the extrapolation of eco-geographical variables onto any resolution
# bathymetry (aka the cookie cutting approach) of Davies & Guinotte (2011)
# PLoS ONE # to create depth weighted continuous grids of environmental variables.
# There is no automatic statistical test of how valid this approach is during the
# variable creation process, we recommend post-hoc testing of the layers generated
# using an independent CTD data set to test how valid your extrapolation is within
# your area of interest.
#
# Cite this paper if you use this approach or script.
# Davies, A.J. & Guinotte, J.M. (2011) "Global Habitat Suitability for
# Framework-Forming Cold-Water Corals." PLoS ONE 6(4): e18483.
# doi:10.1371/journal.pone.0018483
#
#  Dependencies:
#   ArcGIS 10.3
#   ArcPy
#   Spatial Analyst Extension
#
# Released under the MIT License (MIT)
#
# Copyright (c) 2016 Andy Davies
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Import dependencies
import os
import arcpy
from arcpy import env
from arcpy.sa import *
from Includes import load_depth_string
arcpy.CheckOutExtension("Spatial")

# Read ArcGIS Geoprocessing parameters into main variables
InDataDir = arcpy.GetParameterAsText(0)
AppenRD = arcpy.GetParameterAsText(1)
DepthsDir = arcpy.GetParameterAsText(2)
dep = arcpy.GetParameterAsText(3)
TempDir = arcpy.GetParameterAsText(4)
c = arcpy.GetParameterAsText(5)
OutVar = arcpy.GetParameterAsText(6)

# Define the options the script will use later
# load depth strings from Includes.py
Depths = load_depth_string(dep)
arcpy.AddMessage(Depths)
if c == 'False':
    CleanUp = 0
elif c == 'True':
    CleanUp = 1

if not os.path.exists(TempDir):
    os.makedirs(TempDir)

arcpy.ResetEnvironments()
arcpy.env.overwriteOutput = "true"

# Set environment variables
env.mask = ""
arcpy.AddMessage("Mask is: " + str(arcpy.env.mask))
description = arcpy.Describe(os.path.join(DepthsDir, "bath" + str(int(float(Depths[0])))))
cellsize1 = description.children[0].meanCellHeight
env.cellSize = cellsize1
arcpy.AddMessage("Cell size is: " + str(arcpy.env.cellSize))
arcpy.AddMessage(os.path.join(DepthsDir, "bath" + str(int(float(Depths[0])))))
extraster = Raster(os.path.join(DepthsDir, "bath" + str(int(float(Depths[0])))))
extent1 = extraster.extent
env.extent = extent1
arcpy.AddMessage("Extent is: " + str(arcpy.env.extent))
arcpy.env.workspace = TempDir
spf = arcpy.Describe(os.path.join(DepthsDir, "bath" + str(int(float(Depths[0]))))).spatialReference
arcpy.AddMessage("Coord sys is: " + str(spf.name))

try:
    # loop through the layers
    for item in Depths:
        Depth = int(float(item))
        arcpy.AddMessage("\nResizing layer " + str(Depth) + " " + InDataDir + "/" + AppenRD + str(Depth))
        arcpy.ProjectRaster_management(os.path.join(InDataDir, AppenRD + str(Depth)),
                                       os.path.join(TempDir, AppenRD + "a" + str(Depth)), spf)
        TempData = arcpy.sa.ApplyEnvironment(os.path.join(TempDir, AppenRD + "a" + str(Depth)))
        arcpy.AddMessage("\nExtracting " + str(Depth) + " to mask\n")
        outExtractByMask = ExtractByMask(TempData, os.path.join(DepthsDir, "bath" + str(Depth)))
        outExtractByMask.save(TempDir + "/clip" + str(Depth))
        arcpy.AddMessage("\nAdding " + str(Depth) + " to final layer")
        arcpy.Mosaic_management(TempDir + "/clip" + str(Depth), TempDir + "/clip" + str(int(float(Depths[0]))), "LAST")
        if Depth == int(float(Depths[-1])):
            arcpy.AddMessage("\nCreating the final layer for you, which will be called " + OutVar)
            arcpy.CopyRaster_management(TempDir + "/clip" + str(int(float(Depths[0]))), OutVar)
            mxd = arcpy.mapping.MapDocument("CURRENT")
            df = arcpy.mapping.ListDataFrames(mxd)[0]
            arcpy.mapping.AddLayer(df, OutVar, "TOP")
            arcpy.RefreshActiveView()
            arcpy.RefreshTOC()
            del mxd, df
            if CleanUp == 1:
                arcpy.AddMessage(
                    "\nOperation successful, your new raster is called " + OutVar + "I am  now cleaning up...")
                try:
                    for item in Depths:
                        Depth2 = int(float(item))
                        arcpy.Delete_management(TempDir + "/clip" + str(Depth2))
                        arcpy.Delete_management(os.path.join(TempDir, AppenRD + "a" + str(Depth2)))
                except:
                    arcpy.AddMessage("\nClean up failed")
            else:
                arcpy.AddMessage(
                    "Script completed, your temporary files are left for bug checking, and your final raster is called " + TempDir + "/" + OutVar)
                break
        arcpy.AddMessage("next layer " + str(Depth))
except:
    arcpy.AddMessage(arcpy.GetMessages())
    arcpy.AddMessage("Something has gone wrong likely with this: " + str(Depth))
