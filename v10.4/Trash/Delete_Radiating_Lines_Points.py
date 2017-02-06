import arcpy, numpy, os
from math import radians, sin, cos

#origin_x, origin_y = (233271.084,  393929.569)
#distance = 500000
#angle = 10 # in degrees

points = arcpy.GetParameter(0)
distance = float(int(arcpy.GetParameter(1)))
angle = int(arcpy.GetParameter(2))
featureclass = arcpy.GetParameterAsText(3)

#pathOut = "E:/2014/Kurr/RadiatingLines/"
#output = "cb2.shp"
arcpy.CreateFeatureclass_management(os.path.dirname(featureclass),os.path.basename(featureclass), "Polyline") 

#create list of bearings
angles = range(0, 360,angle)

desc = arcpy.Describe(points)
shapefieldname = desc.ShapeFieldName
rows = arcpy.SearchCursor(points)

for row in rows:
	feat = row.getValue(shapefieldname)
	pnt = feat.getPart()
	origin_x = pnt.X
	origin_y = pnt.Y
    # Print x,y coordinates of current point
    #
	for ang in angles:
		# calculate offsets with light trig
		angle = float(int(ang))
		(disp_x, disp_y) = (distance * sin(radians(angle)), distance * cos(radians(angle)))
		(end_x, end_y) = (origin_x + disp_x, origin_y + disp_y)

		cur = arcpy.InsertCursor(featureclass)
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