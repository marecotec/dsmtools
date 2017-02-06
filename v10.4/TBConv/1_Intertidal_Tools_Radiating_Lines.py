# Title: Radiating lines from a single point
#
# Summary:
#    This script builds radiating lines from a single point, it does little else (i.e. it doesn't
#    clip th radiating lines by a costline). It is unlikely that you will ever use this tool.
#    the Calculate fetch distances from points tool is far more feature rich.
#
# Usage:
#
# Parameters
#    Parameter name:
#        Dialogue Reference
#        Python Reference
#        Data Type
#
# Code Samples
#
#
#  Dependencies:
#   ArcGIS 10.3
#   ArcPy
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

import arcpy, numpy, os
from math import radians, sin, cos

#origin_x, origin_y = (233271.084,  393929.569)
#distance = 500000
#angle = 10 # in degrees

origin_x = float(arcpy.GetParameter(0))
origin_y = float(arcpy.GetParameter(1))
distance = float(int(arcpy.GetParameter(2)))
angle = int(arcpy.GetParameter(3))
OutputFeature = arcpy.GetParameterAsText(4)

#pathOut = "E:/2014/Kurr/RadiatingLines/"
#output = "cb2.shp"
arcpy.CreateFeatureclass_management(os.path.dirname(OutputFeature),os.path.basename(OutputFeature), "Polygon")

#create list of bearings
angles = range(0, 360,angle)


for ang in angles:
	# calculate offsets with light trig
	angle = float(int(ang))
	(disp_x, disp_y) = (distance * sin(radians(angle)), distance * cos(radians(angle)))
	(end_x, end_y) = (origin_x + disp_x, origin_y + disp_y)
	(end2_x, end2_y) = (origin_x + disp_x, origin_y + disp_y)

	cur = arcpy.InsertCursor(OutputFeature)
	lineArray = arcpy.Array()

	# start point
	start = arcpy.Point()
	(start.ID, start.X, start.Y) = (1, origin_x, origin_y) 
	lineArray.add(start)

	# end point
	end = arcpy.Point()
	(end.ID, end.X, end.Y) = (2, end_x, end_y)
	lineArray.add(end)

	# write our fancy feature to the shapefile
	feat = cur.newRow()
	feat.shape = lineArray
	cur.insertRow(feat)

	# yes, this shouldn't really be necessary...
	lineArray.removeAll()
	del cur