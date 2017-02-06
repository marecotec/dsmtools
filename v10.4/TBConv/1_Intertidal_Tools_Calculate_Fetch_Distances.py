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
from collections import Counter
from math import radians, sin, cos

points = arcpy.GetParameter(0)
fieldID = arcpy.GetParameter(1)
distance = float(int(arcpy.GetParameter(2)))
angle = int(arcpy.GetParameter(3))
clipfeature = arcpy.GetParameterAsText(4)
featureclass = arcpy.GetParameterAsText(5)

# Get spatial reference from INPUT
desc_input = arcpy.Describe(points)
coord_sys = desc_input.spatialReference

if not arcpy.Exists(featureclass):
    arcpy.CreateFeatureclass_management(os.path.dirname(featureclass), os.path.basename(featureclass), "Polyline")
    arcpy.AddField_management(featureclass, str(fieldID), "TEXT", "", "", "150")
    arcpy.AddField_management(featureclass, "BEARING", "SHORT", "", "", "4")
    arcpy.DeleteField_management(featureclass, ["Id"])
    arcpy.DefineProjection_management(featureclass, coord_sys)

    featureclass_in_mem = arcpy.CreateFeatureclass_management("in_memory", "featureclass_in_mem", "Polyline")
    arcpy.AddField_management(featureclass_in_mem, str(fieldID), "TEXT", "", "", "150")
    arcpy.AddField_management(featureclass_in_mem, "BEARING", "SHORT", "", "", "4")
    arcpy.DeleteField_management(featureclass_in_mem, ["Id"])
    arcpy.DefineProjection_management(featureclass_in_mem, coord_sys)

# create list of bearings
desc = arcpy.Describe(points)
shapefieldname = desc.ShapeFieldName
rows = arcpy.SearchCursor(points)

for row in rows:
    angles = range(0, 360, angle)
    feat = row.getValue(shapefieldname)
    columnValue = row.getValue(str(fieldID))
    pnt = feat.getPart()
    origin_x = pnt.X
    origin_y = pnt.Y
    arcpy.AddMessage("Site ID: " + str(columnValue) + ", X is: " + str(origin_x) + ", Y is: " + str(origin_y))

    # Create Temp Files
    for ang in angles:
        temp = arcpy.CreateFeatureclass_management("in_memory", "temp", "POLYLINE", "", "DISABLED", "DISABLED",
                                                   coord_sys, "", "0", "0", "0")[0]
        arcpy.AddField_management(temp, str(fieldID), "TEXT", "", "", "150")
        arcpy.AddField_management(temp, "BEARING", "SHORT", "", "", "4")

        temp2 = arcpy.CreateFeatureclass_management("in_memory", "temp2", "POLYLINE", "", "DISABLED", "DISABLED",
                                                    coord_sys, "", "0", "0", "0")
        arcpy.AddField_management(temp2, str(fieldID), "TEXT", "", "", "150")
        arcpy.AddField_management(temp2, "BEARING", "SHORT", "", "", "4")
        arcpy.AddField_management(temp, "outFID", "SHORT", "", "", "4")

        temp3 = arcpy.CreateFeatureclass_management("in_memory", "temp3", "POLYLINE", "", "DISABLED", "DISABLED",
                                                    coord_sys, "", "0", "0", "0")
        arcpy.AddField_management(temp3, str(fieldID), "TEXT", "", "", "150")
        arcpy.AddField_management(temp3, "BEARING", "SHORT", "", "", "4")

        output = arcpy.CreateFeatureclass_management("in_memory", "output", "POLYLINE", "", "DISABLED", "DISABLED",
                                                     coord_sys, "", "0", "0", "0")
        arcpy.AddField_management(output, str(fieldID), "TEXT", "", "", "150")
        arcpy.AddField_management(output, "BEARING", "SHORT", "", "", "4")

        # calculate offsets with light trig
        ang = float(int(ang))

        (disp_x, disp_y) = (distance * sin(radians(ang)), distance * cos(radians(ang)))
        (end_x, end_y) = (origin_x + disp_x, origin_y + disp_y)

        # start point
        start = arcpy.Point()
        (start.ID, start.X, start.Y) = (1, origin_x, origin_y)
        # end point
        end = arcpy.Point()
        (end.ID, end.X, end.Y) = (2, end_x, end_y)
        #arcpy.AddMessage("sx: " + str(start.X) + ", sy: " + str(start.Y) + ", ex: " + str(end.X) + ", ey: " + str(end.Y))

        lineArray = arcpy.Array([arcpy.Point(start.X, start.Y),
                                arcpy.Point(end.X, end.Y)])

        line = arcpy.Polyline(lineArray)
        lineArray.removeAll()

        # add line to file
        #feat = cur.newRow()
        #arcpy.AddMessage(str(line))
        #feat.shape(line)

        #arcpy.AddMessage("Point ID is: " + str(columnValue) + ", bearing: " + str(ang))
        #feat.setValue(str(fieldID), str(columnValue))
        #feat.setValue("BEARING", ang)
        #arcpy.CopyFeatures_management(r"in_memory\temp",r"D:\Jack_Fetch\Output\test_in_mem.shp")

        with arcpy.da.InsertCursor(temp, [str(fieldID), 'BEARING', 'SHAPE@']) as cur:
            cur.insertRow([columnValue, ang, line])
            #arcpy.CopyFeatures_management(r"in_memory\temp",r"D:\Jack_Fetch\Output\test_in_mem.shp")

        # yes, this shouldn't really be necessary...
        del cur, disp_x, disp_y, start, end

        # intersetc line
        arcpy.Intersect_analysis(r"in_memory\temp" + " #;" + str(clipfeature) + " #", r"in_memory\temp2", "ALL", "#", "LINE")
        # arcpy.CopyFeatures_management(temp2,os.path.join(os.path.dirname(featureclass),"test0_int.shp"))
        arcpy.Delete_management(r"in_memory\temp")
        # convert intersect line to verteces
        temp = arcpy.CreateFeatureclass_management("in_memory", "temp", "POLYLINE", "", "DISABLED", "DISABLED",
                                                   coord_sys, "", "0", "0", "0")
        arcpy.AddField_management(temp, str(fieldID), "TEXT", "", "", "150")
        arcpy.AddField_management(temp, "BEARING", "SHORT", "", "", "4")
        arcpy.AddField_management(temp, "inFID", "SHORT", "", "", "4")
        inFC = r"in_memory\temp2"
        outFC = r"in_memory\temp"

        # arcpy.AddMessage("Clipping line for ID: " + str(columnValue) + ", bearing: " + str(ang))
        iCursor = arcpy.da.InsertCursor(outFC, ["inFID", "SHAPE@"])
        with arcpy.da.SearchCursor(inFC, ["OID@", "SHAPE@"]) as sCursor:
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
                                iCursor.insertRow([inFID, polyline])
                            prevX = pnt.X
                            prevY = pnt.Y
                        else:
                            # If pnt is None, this represents an interior ring
                            #
                            print("Interior Ring:")
                    partnum += 1

        del iCursor
        del sCursor
        # arcpy.JoinField_management(outFC,"inFID",inFC,"outFID","#")
        # Now select nearest feature
        arcpy.MakeFeatureLayer_management(outFC, 'outFC_lyr')
        # Create update cursor for feature class
        insert_value_rows = arcpy.UpdateCursor('outFC_lyr')
        for value_row in insert_value_rows:
            value_row.setValue(str(fieldID), str(columnValue))
            value_row.setValue("BEARING", ang)
            insert_value_rows.updateRow(value_row)
        del value_row, insert_value_rows

        arcpy.DeleteField_management('outFC_lyr', ["inFID"])

        with arcpy.da.SearchCursor('outFC_lyr', ["SHAPE@", str(fieldID), "BEARING"]) as sCur:
            with arcpy.da.InsertCursor(featureclass_in_mem, ["SHAPE@", str(fieldID), "BEARING"]) as iCur:
                for row in sCur:

                    firstpointlineX = round(row[0].firstPoint.X, 0)
                    firstpointlineY = round(row[0].firstPoint.Y, 0)
                    endpointlineX = round(row[0].lastPoint.X, 0)
                    endpointlineY = round(row[0].lastPoint.X, 0)
                    round_origin_x = round(origin_x, 0)
                    round_origin_y = round(origin_y, 0)

                    if firstpointlineX == round_origin_x and firstpointlineY == round_origin_y:
                        iCur.insertRow(row)
                    # arcpy.AddMessage("MATCH FIRST: " + str(ang))
                    else:
                        if endpointlineX == round_origin_x and endpointlineY == round_origin_y:
                            iCur.insertRow(row)
                        # arcpy.AddMessage("MATCH LAST: " + str(ang))

        # arcpy.CopyFeatures_management('outFC_lyr',os.path.join(os.path.dirname(featureclass),"test1.shp"))
        # arcpy.Delete_management(inFC)
        # arcpy.Delete_management(outFC)
        # arcpy.SelectLayerByLocation_management('outFC_lyr',"WITHIN_A_DISTANCE",points,"1 Meters","NEW_SELECTION")
        # arcpy.CopyFeatures_management('outFC_lyr',temp3)
        # arcpy.CopyFeatures_management('outFC_lyr',os.path.join(os.path.dirname(featureclass),"test2.shp"))
        # fieldmap = "Id Id true false false 6 Long 0 6 ,First,#," + str(temp3) + "Id,-1,-1; " + str(fieldID) + " " + str(fieldID) + " true false false 150 Text 0 0 ,First,#," + str(temp3) + "," + str(fieldID) + ",-1,-1; " + "BEARING BEARING true false false 4 Short 0 4 ,First,#," + str(temp3) + ",BEARING,-1,-1"
        # arcpy.Append_management(temp3, featureclass, "NO_TEST",fieldmap,"#")
        # arcpy.CopyFeatures_management(featureclass,os.path.join(os.path.dirname(featureclass),"test3.shp"))
        arcpy.DeleteFeatures_management('outFC_lyr')
    # arcpy.Delete_management(temp3)
    # arcpy.Delete_management(temp2)
    # arcpy.Delete_management(temp)
# calculate length
arcpy.AddMessage("Adding fetch distances")
arcpy.AddField_management(featureclass_in_mem, "FETCHKM", "DOUBLE", "9", "4")
arcpy.CalculateField_management(featureclass_in_mem, "FETCHKM", "!Shape.length@KILOMETERS!", "PYTHON_9.3")
# if you can use a key to identify the fields to remove, then it's solved
# fields = arcpy.ListFields(featureclass)
# manually enter field names to keep here
# include mandatory fields name such as OBJECTID and Shape in keepfields
# keepFields = ["Shape","FID","\"" + str(fieldID) + "\"","BEARING","FETCH"]
# dropFields = [x.name for x in fields if x.name not in keepFields]
# delete fields
# arcpy.DeleteField_management(featureclass, dropFields)
# calculate length
# arcpy.Delete_management(os.path.join(os.path.dirname(featureclass),"output.shp"))

# now compare lists to identify if any points are invalid
arcpy.AddMessage("Checking points to ensure all have fetch...")
with arcpy.da.SearchCursor(featureclass_in_mem, [str(fieldID)]) as cursor:
    finallist = str(sorted({row[0] for row in cursor}))
    #arcpy.AddMessage(str(finallist) + " len of final list1")
with arcpy.da.SearchCursor(points, [str(fieldID)]) as cursor:
    originallist = str(sorted({row[0] for row in cursor}))
    #arcpy.AddMessage(str(originallist) + " len of final list2")
missinglist = list(set(originallist) - set(finallist))
#arcpy.AddMessage(str(int(len(missinglist))) + " len of missing list")

if len(missinglist) > 0:
    arcpy.AddWarning(str(int(len(missinglist))) + " points without fetch")
    j = ', '.join(str(missinglist))
    arcpy.AddWarning("These are the ID's: " + str(j))
else:
    arcpy.AddMessage("All points had fetch")

arcpy.AddMessage("Checking points to ensure all have required number of fetch angles...")
# zipcode_cnt = collections.Counter(row[0] for row in arcpy.da.SearchCursor("ZipCodeBoundaries", "STATE"))
with arcpy.da.SearchCursor(featureclass_in_mem, ["BEARING", str(fieldID)]) as cur:
    count_of_items = Counter(row[1] for row in cur)
# arcpy.AddMessage(str(count_of_items))
# for item in sorted(count_of_items.items(), key=lambda x:x[1]):
#    arcpy.AddMessage("{0:>12} {1:>4}".format(item[0], item[1]))

errorList = []
# arcpy.AddMessage("number of angles:" + str(len(angles)))

for item in sorted(count_of_items.items(), key=lambda x: x[1]):
    #	arcpy.AddWarning("letter" + str(item[0]))
    #	arcpy.AddWarning("count" + str(item[1]))
    if item[1] < len(angles):
        errorList.append(item[0])
if len(errorList) > 0:
    pp = ', '.join(str(errorList))
    arcpy.AddWarning("These are the ID's: " + str(pp))
else:
    arcpy.AddMessage("All points had required fetch lines")
arcpy.CopyFeatures_management(r"in_memory\featureclass_in_mem",featureclass)
