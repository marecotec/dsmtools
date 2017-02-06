# Title: Calculate fetch distances from points
#
# Summary:
#    This script builds radiating lines from file of unique point locations, it then extracts the radiating
#    line length from an intersect with a coastline, and calculates the length of the line. It only works in
#    projected space, so any errors will likely come from that.
#
#    This script is an evolution from an approach I presented in my first paper:
#    Davies and Johnson (2006) "Coastline configuration
#    disrupts large-scale climatic forcing, leading to divergent temporal trends in wave
#    exposure" Estuarine and Coastal Shelf Science 69 (3-4): 643-648.
#
#
#    Needs an inverted polygon shapefile of the sea not land - from OS Streetmap produce better coastline polygon
#    Point ID's need to be strings (change str to float conversion)
#    All layers must be in same coordinate system, i.e. projected - write catch all to detect projectiopn system of the points/coastline layer
#
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

points = arcpy.GetParameter(0)
fieldID = arcpy.GetParameterAsText(1)
distance = float(int(arcpy.GetParameter(2)))
angle = int(arcpy.GetParameter(3))
clipfeature = arcpy.GetParameterAsText(4)
featureclass = arcpy.GetParameterAsText(5)

#Get spatial reference from INPUT
desc_input = arcpy.Describe(points)
coord_sys = desc_input.spatialReference

if arcpy.Exists(os.path.join(os.path.dirname(featureclass),"temp.shp")):
    arcpy.Delete_management(os.path.join(os.path.dirname(featureclass),"temp.shp"))
arcpy.CreateFeatureclass_management(os.path.dirname(featureclass),"temp.shp", "Polyline")
arcpy.DefineProjection_management(os.path.join(os.path.dirname(featureclass),"temp.shp"), coord_sys)  

if arcpy.Exists(os.path.join(os.path.dirname(featureclass),"temp2.shp")):
    arcpy.Delete_management(os.path.join(os.path.dirname(featureclass),"temp2.shp"))
arcpy.CreateFeatureclass_management(os.path.dirname(featureclass),"temp2.shp", "Polyline")
arcpy.DefineProjection_management(os.path.join(os.path.dirname(featureclass),"temp2.shp"), coord_sys)

if arcpy.Exists(os.path.join(os.path.dirname(featureclass),"temp3.shp")):
    arcpy.Delete_management(os.path.join(os.path.dirname(featureclass),"temp3.shp"))

if not arcpy.Exists(os.path.join(os.path.dirname(featureclass),"output.shp")):
	arcpy.CreateFeatureclass_management(os.path.dirname(featureclass),"output.shp", "Polyline")
	arcpy.AddField_management(os.path.join(os.path.dirname(featureclass),"output.shp"), str(fieldID), "TEXT", "", "", "150")
	arcpy.AddField_management(os.path.join(os.path.dirname(featureclass),"output.shp"), "BEARING", "SHORT", "", "", "4")
	arcpy.DefineProjection_management(os.path.join(os.path.dirname(featureclass),"output.shp"), coord_sys)
	
if not arcpy.Exists(featureclass):
	arcpy.CreateFeatureclass_management(os.path.dirname(featureclass),os.path.basename(featureclass), "Polyline")
	arcpy.AddField_management(featureclass, str(fieldID), "TEXT", "", "", "150")
	arcpy.AddField_management(featureclass, "BEARING", "SHORT", "", "", "4")
	arcpy.DefineProjection_management(featureclass, coord_sys)

#create list of bearings
angles = range(0, 360,angle)

desc = arcpy.Describe(points)
shapefieldname = desc.ShapeFieldName
rows = arcpy.SearchCursor(points)

for row in rows:
	feat = row.getValue(shapefieldname)
	columnValue = row.getValue(str(fieldID))
	pnt = feat.getPart()
	origin_x = pnt.X
	origin_y = pnt.Y
    # Print x,y coordinates of current point
    #
	for ang in angles:
		
		if arcpy.Exists(os.path.join(os.path.dirname(featureclass),"temp.shp")):
			arcpy.Delete_management(os.path.join(os.path.dirname(featureclass),"temp.shp"))
		arcpy.CreateFeatureclass_management(os.path.dirname(featureclass),"temp.shp", "Polyline")
		arcpy.AddField_management(os.path.join(os.path.dirname(featureclass),"temp.shp"), str(fieldID), "TEXT", "", "", "150")
		arcpy.AddField_management(os.path.join(os.path.dirname(featureclass),"temp.shp"), "BEARING", "SHORT", "", "", "4")
		arcpy.DefineProjection_management(os.path.join(os.path.dirname(featureclass),"temp.shp"), coord_sys)
		
		if arcpy.Exists(os.path.join(os.path.dirname(featureclass),"temp2.shp")):
			arcpy.Delete_management(os.path.join(os.path.dirname(featureclass),"temp2.shp"))
		arcpy.CreateFeatureclass_management(os.path.dirname(featureclass),"temp2.shp", "Polyline")
		arcpy.DefineProjection_management(os.path.join(os.path.dirname(featureclass),"temp2.shp"), coord_sys)

		if arcpy.Exists(os.path.join(os.path.dirname(featureclass),"temp3.shp")):
			arcpy.Delete_management(os.path.join(os.path.dirname(featureclass),"temp3.shp"))
		arcpy.CreateFeatureclass_management(os.path.dirname(featureclass),"temp3.shp", "Polyline")
		arcpy.DefineProjection_management(os.path.join(os.path.dirname(featureclass),"temp3.shp"), coord_sys)
		
		# calculate offsets with light trig
		angle = float(int(ang))
		(disp_x, disp_y) = (distance * sin(radians(angle)), distance * cos(radians(angle)))
		(end_x, end_y) = (origin_x + disp_x, origin_y + disp_y)
		cur = arcpy.InsertCursor(os.path.join(os.path.dirname(featureclass),"temp.shp"))
		lineArray = arcpy.Array()
		# start point
		start = arcpy.Point()
		(start.ID, start.X, start.Y) = (1, origin_x, origin_y) 
		lineArray.add(start)
		# end point
		end = arcpy.Point()
		(end.ID, end.X, end.Y) = (2, end_x, end_y)
		lineArray.add(end)

		# add line to file
		feat2 = cur.newRow()
		feat2.shape = lineArray
		#arcpy.AddMessage("Point ID is: " + str(columnValue) + ", bearing: " + str(ang))
		feat2.setValue(str(fieldID), str(columnValue))
		feat2.setValue("BEARING", ang)	
		cur.insertRow(feat2)

		# yes, this shouldn't really be necessary...
		lineArray.removeAll()
		del cur,feat2
		
		#intersetc line
		arcpy.Intersect_analysis(os.path.join(os.path.dirname(featureclass),"temp.shp") + " #;" + str(clipfeature) + " #",os.path.join(os.path.dirname(featureclass),"temp2.shp"),"ALL","#","LINE")
		arcpy.Delete_management(os.path.join(os.path.dirname(featureclass),"temp.shp"))
		#convert intersect line to verteces
		arcpy.CreateFeatureclass_management(os.path.dirname(featureclass),"temp.shp", "Polyline")
		inFC = os.path.join(os.path.dirname(featureclass),"temp2.shp")
		outFC = os.path.join(os.path.dirname(featureclass),"temp.shp")
		arcpy.AddField_management(outFC,"inFID","LONG","#","#","#","#","NULLABLE","NON_REQUIRED","#")
		
		iCursor = arcpy.da.InsertCursor(outFC, ["inFID","SHAPE@"])
		with arcpy.da.SearchCursor(inFC,["OID@", "SHAPE@"]) as sCursor:
			for row in sCursor:
				inFID = row[0]
				# Print the current multipoint's ID
				#
				print("Feature {0}:".format(row[0]))
				partnum = 0

				# Step through each part of the feature
				#
				for part in row[1]:
					# Print the part number
					#
					print("Part {0}:".format(partnum))

					# Step through each vertex in the feature
					#
					prevX = None
					prevY = None
					for pnt in part:
						if pnt:
							# Print x,y coordinates of current point
							#
							print("{0}, {1}".format(pnt.X, pnt.Y))
							if prevX:
								array = arcpy.Array([arcpy.Point(prevX, prevY),
													 arcpy.Point(pnt.X, pnt.Y)])
								polyline = arcpy.Polyline(array)
								iCursor.insertRow([inFID,polyline])
							prevX = pnt.X
							prevY = pnt.Y
						else:
							# If pnt is None, this represents an interior ring
							#
							print("Interior Ring:")
					partnum += 1

		del iCursor
		del sCursor
		arcpy.JoinField_management(outFC,"inFID",inFC,"FID","#")
		# Now select nearest feature
		arcpy.MakeFeatureLayer_management(outFC, 'outFC_lyr')
		del outFC
		del inFC		
		arcpy.SelectLayerByLocation_management('outFC_lyr',"WITHIN_A_DISTANCE",points,"1 Meters","NEW_SELECTION")
		arcpy.CopyFeatures_management('outFC_lyr',os.path.join(os.path.dirname(featureclass),"temp3.shp"))
		fieldmap = "Id Id true false false 6 Long 0 6 ,First,#," + str(os.path.join(os.path.dirname(featureclass),"temp3.shp")) + "Id,-1,-1; " + str(fieldID) + " " + str(fieldID) + " true false false 150 Text 0 0 ,First,#," + str(os.path.join(os.path.dirname(featureclass),"temp3.shp")) + "," + str(fieldID) + ",-1,-1; " + "BEARING BEARING true false false 4 Short 0 4 ,First,#," + str(os.path.join(os.path.dirname(featureclass),"temp3.shp")) + ",BEARING,-1,-1"
		arcpy.Append_management(os.path.join(os.path.dirname(featureclass),"temp3.shp"), os.path.join(os.path.dirname(featureclass),"output.shp"), "NO_TEST",fieldmap,"#")
		arcpy.DeleteFeatures_management('outFC_lyr')
		arcpy.Delete_management(os.path.join(os.path.dirname(featureclass),"temp3.shp"))
		arcpy.Delete_management(os.path.join(os.path.dirname(featureclass),"temp2.shp"))
		arcpy.Delete_management(os.path.join(os.path.dirname(featureclass),"temp.shp"))		
arcpy.CopyFeatures_management(os.path.join(os.path.dirname(featureclass),"output.shp"),featureclass)

#calculate length
arcpy.AddMessage("Adding fetch distances")
arcpy.AddField_management(featureclass, "FETCHKM", "DOUBLE", "9", "4")
arcpy.CalculateField_management(featureclass, "FETCHKM", "!Shape.length@KILOMETERS!", "PYTHON_9.3")
# if you can use a key to identify the fields to remove, then it's solved
fields = arcpy.ListFields(featureclass) 
# manually enter field names to keep here
# include mandatory fields name such as OBJECTID and Shape in keepfields
keepFields = ["Shape","FID","\"" + str(fieldID) + "\"","BEARING","FETCH"]
#dropFields = [x.name for x in fields if x.name not in keepFields]
# delete fields
#arcpy.DeleteField_management(featureclass, dropFields)
#calculate length
arcpy.Delete_management(os.path.join(os.path.dirname(featureclass),"output.shp"))

#now compare lists to identify if any points are invalid
with arcpy.da.SearchCursor(featureclass, [str(fieldID)]) as cursor:
        finallist = sorted({row[0] for row in cursor})
with arcpy.da.SearchCursor(points, [str(fieldID)]) as cursor:
        originallist = sorted({row[0] for row in cursor})
missinglist = list(set(originallist) - set(finallist))
if len(missinglist) > 0:
	arcpy.AddWarning(str(int(len(missinglist))) + " points without fetch")
	j = ', '.join(missinglist)
	arcpy.AddWarning("These are the ID's: " + str(j))
else:
	arcpy.AddMessage("All points had fetch, finished.")