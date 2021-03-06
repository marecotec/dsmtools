#!/usr/bin/env python
import arcpy
import os
from math import radians, sin, cos, sqrt
import gc
import time
import csv
import pandas as pd

class IntertidalToolsSpeciesPatternsAroundIslands(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Species distribution patterns around islands"
        self.description = """Orientation of species distributions for G. Williams"""
        self.canRunInBackground = True
        self.category = "Intertidal Tools"  # Use your own category here, or an existing one.

    def getParameterInfo(self):

        # You can define a tool to have no parameters
        params = []

        # Input Island Line - Demarks the area in which we will spatially bootstrap
        input_line = arcpy.Parameter(name="input_line_folder",
                                       displayName="Input Island Line",
                                       datatype="DEFeatureClass",
                                       parameterType="Required",
                                       direction="Input",
                                       )
        input_line.value = "D:/2016/Corals/IndividualIslands_ByYear_Lines/TUT.shp"
        params.append(input_line)

        # Input Island Points - Original points that will be sampled by the spatial bootstrap
        input_points = arcpy.Parameter(name="input_points",
                                       displayName="Input Island Points",
                                       datatype="DEFeatureClass",
                                       parameterType="Required",
                                       direction="Input",
                                       )
        input_points.value = "D:/2016/Corals/IndividualIslands_ByYear_Points/TUT_ALL.shp"
        params.append(input_points)

        # Select attribute column for the calculation
        attribute_process = arcpy.Parameter(name="attribute_1",
                                      displayName="Column to process",
                                      datatype="Field",
                                      parameterType="Required",
                                      direction="Input")
        attribute_process.value = "CORAL,CCA,MACROALGAE"
        params.append(attribute_process)

        # Select attribute column for the calculation
        flag_field = arcpy.Parameter(name="flag_field",
                                      displayName="Flag field",
                                      datatype="Field",
                                      parameterType="Required",
                                      direction="Input")
        # Derived parameter
        flag_field.parameterDependencies = [input_points.name]
        flag_field.value = "Flag"
        params.append(flag_field)

        # Distance to draw polygon - in metres
        distance = arcpy.Parameter(name="distance",
                                   displayName="Distance to capture sample points",
                                   datatype="GPDouble",
                                   parameterType="Required",
                                   direction="Input",
                                   )
        distance.value = 100000
        params.append(distance)

        # Angle to capture patterns within circle - in degrees
        angle = arcpy.Parameter(name="angle",
                                 displayName="Angle for search",
                                 datatype="GPLong",
                                 parameterType="Required",
                                 direction="Input",
                                )
        angle.value = 10
        params.append(angle)

        # Output feature class
        output_directory = arcpy.Parameter(name="output_directory",
                                        displayName="Output directory",
                                        datatype="DEWorkspace",
                                        parameterType="Optional",
                                        direction="Output",
                                        )
        output_directory.value = "D:/2016/Corals/IndividualIslands_ByYear_GP/TUT_ALL"
        params.append(output_directory)

        clean_up = arcpy.Parameter(name="clean_up",
                                       displayName="Delete temporary files?",
                                       datatype="GPBoolean",
                                       parameterType="Required",
                                       direction="Input",
                                       )
        clean_up.value = "False"
        params.append(clean_up)

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        arcpy.env.overwriteOutput = True
        arcpy.CheckOutExtension('Spatial')
        arcpy.AddMessage("Orientation of species distributions")
        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText))

        # Read in variables for the tool
        input_line = parameters[0].valueAsText
        input_points = parameters[1].valueAsText
        attribute_process = parameters[2].valueAsText
        flag_field = parameters[3].valueAsText
        distance = parameters[4].value
        angle = parameters[5].value
        output_directory = parameters[6].valueAsText
        clean_up = parameters[7].valueAsText

        # Make output directory if it does not exist
        output_directory.strip()
        arcpy.AddMessage(output_directory)

        if not os.path.exists(str(output_directory)):
            os.makedirs(output_directory)

        arcpy.env.workspace = output_directory

        # 0 Describe files to set coordinate systems
        desc_input = arcpy.Describe(input_points)
        coord_system = desc_input.spatialReference
        arcpy.env.outputCoordinateSystem = coord_system


        # 1 Convert island line to a polygon - numpy work around due to lack of license

        if not arcpy.Exists(os.path.join(output_directory, "Island_Poly.shp")):
            def polygon_to_line_no_gap(input_line_, output_polygon):
                array = arcpy.da.FeatureClassToNumPyArray(input_line_, ["SHAPE@X", "SHAPE@Y"], spatial_reference=coord_system, explode_to_points=True)
                if array.size == 0:
                    arcpy.AddError("Line has no features, check to ensure it is OK")
                else:
                    array2 = arcpy.Array()
                    for x, y in array:
                        pnt = arcpy.Point(x, y)
                        array2.add(pnt)
                    polygon = arcpy.Polygon(array2)
                    arcpy.CopyFeatures_management(polygon, output_polygon)
                return

            polygon_to_line_no_gap(input_line, os.path.join(output_directory, "Island_Poly.shp"))

            # 2 Create Fishnet for random sampling of points within the cells of the net
            extent = arcpy.Describe(input_points).extent
            origin_coord = str(extent.XMin) + " " + str(extent.YMin)
            y_coord = str(extent.XMin) + " " + str(extent.YMin + 1)
            corner_coord = str(extent.XMax) + " " + str(extent.YMax)

            island_area = 0

            with arcpy.da.SearchCursor(os.path.join(output_directory,"Island_Poly.shp"), "SHAPE@") as rows:
                for row in rows:
                    island_area += row[0].getArea("GEODESIC", "SQUAREKILOMETERS")

            island_area_polygon = sqrt(island_area * 0.1) * 100

            arcpy.AddMessage(
                "....fishnet size is: " + str(round(island_area_polygon,2)) + " m x " + str(round(island_area_polygon,2)) + " m. Island area is: " + str(round(island_area,0)) + " km2.")

            arcpy.CreateFishnet_management(out_feature_class=os.path.join(output_directory,"Fishnet.shp"),
                                           origin_coord=origin_coord,
                                           y_axis_coord=y_coord,
                                           cell_width=island_area_polygon,
                                           cell_height=island_area_polygon,
                                           number_rows="",
                                           number_columns="",
                                           corner_coord=corner_coord,
                                           labels="",
                                           template="",
                                           geometry_type="POLYGON"
                                           )

            arcpy.Intersect_analysis(in_features=os.path.join(output_directory,"Fishnet.shp") + " #;" + os.path.join(output_directory,"Island_Poly.shp") + " #",
                                     out_feature_class=os.path.join(output_directory,"FishClip.shp"),
                                     join_attributes="ONLY_FID",
                                     cluster_tolerance="-1 Unknown",
                                     output_type="INPUT")

            arcpy.DefineProjection_management(os.path.join(output_directory,"FishClip.shp"), coord_system)

            arcpy.AddField_management(os.path.join(output_directory,"FishClip.shp"), "Shape_Area", "DOUBLE")

            arcpy.CalculateField_management(os.path.join(output_directory,"FishClip.shp"),
                                            "Shape_Area",
                                            "!SHAPE.AREA@SQUAREMETERS!",
                                            "PYTHON_9.3")

            maxvalue = arcpy.SearchCursor(os.path.join(output_directory,"FishClip.shp"),
                                          "",
                                          "",
                                          "",
                                          "Shape_Area" + " D").next().getValue("Shape_Area")

            maxvalue = str(int(maxvalue-1))

            where = '"Shape_Area" > ' + "%s" %maxvalue
            arcpy.Select_analysis(in_features=os.path.join(output_directory,"FishClip.shp"),
                                  out_feature_class=os.path.join(output_directory,"FishClipInner.shp"),
                                  where_clause=where
                                  )

            # 3 Create n random points within the cells of the fishnet
            arcpy.CreateRandomPoints_management(out_path=output_directory,
                                                out_name="RndPts.shp",
                                                constraining_feature_class=os.path.join(output_directory,"FishClipInner.shp"),
                                                constraining_extent="0 0 250 250",
                                                number_of_points_or_field="5",
                                                minimum_allowed_distance="0 Meters",
                                                create_multipoint_output="POINT",
                                                multipoint_size="0")

            arcpy.DefineProjection_management(os.path.join(output_directory,"RndPts.shp"), coord_system)

        else:
            arcpy.AddMessage("....skipping building polygons as they already exist")

        # 3 Create spatial bootstrapping circle polygons
        rows = arcpy.SearchCursor(os.path.join(output_directory,"RndPts.shp"))
        desc = arcpy.Describe(os.path.join(output_directory,"RndPts.shp"))
        shapefieldname = desc.ShapeFieldName

        if not arcpy.Exists(os.path.join(output_directory,"SectorPoly.shp")):
            arcpy.AddMessage("....now conducting spatial bootstrap.")

            featureclass = os.path.join(output_directory, "SectorPoly.shp")
            arcpy.CreateFeatureclass_management(os.path.dirname(featureclass), os.path.basename(featureclass), "Polygon")
            arcpy.AddField_management(featureclass, str("FID_Fishne"), "TEXT", "", "", "150")
            arcpy.AddField_management(featureclass, "BEARING", "SHORT", "", "", "4")
            arcpy.DeleteField_management(featureclass, ["Id"])
            arcpy.DefineProjection_management(featureclass, coord_system)

            finalfeatureclass = os.path.join(output_directory,"Final.shp")

            arcpy.CreateFeatureclass_management(os.path.dirname(finalfeatureclass), os.path.basename(finalfeatureclass), "Polygon")
            arcpy.AddField_management(finalfeatureclass, str("FID_Fishne"), "TEXT", "", "", "150")
            arcpy.AddField_management(finalfeatureclass, "BEARING", "SHORT", "", "", "4")
            arcpy.DeleteField_management(finalfeatureclass, ["Id"])
            arcpy.DefineProjection_management(finalfeatureclass, coord_system)

            featureclass_in_mem = arcpy.CreateFeatureclass_management("in_memory", "featureclass_in_mem", "Polygon")
            arcpy.AddField_management(featureclass_in_mem, "OriginID", "TEXT", "", "", "150")
            arcpy.AddField_management(featureclass_in_mem, "BEARING", "SHORT", "", "", "4")
            arcpy.DeleteField_management(featureclass_in_mem, ["Id"])
            arcpy.DefineProjection_management(featureclass_in_mem, coord_system)

            for row in rows:
                angles = range(0, 360, angle)
                feat = row.getValue(shapefieldname)
                columnValue = row.getValue(str("FID"))
                pnt = feat.getPart()
                origin_x = pnt.X
                origin_y = pnt.Y

                for ang in angles:
                    angleorigin = float(int(ang))
                    # Point 1
                    (disp_x, disp_y) = (distance * sin(radians(angleorigin)), distance * cos(radians(angleorigin)))
                    (end_x, end_y) = (origin_x + disp_x, origin_y + disp_y)
                    # Point 2
                    anglestep = float(int(ang) + int(angle))
                    (disp2_x, disp2_y) = (distance * sin(radians(anglestep)), distance * cos(radians(anglestep)))
                    (end2_x, end2_y) = (origin_x + disp2_x, origin_y + disp2_y)

                    # Create a polygon geometry
                    array = arcpy.Array([arcpy.Point(origin_x, origin_y),
                                         arcpy.Point(end_x, end_y),
                                         arcpy.Point(end2_x, end2_y),
                                         ])
                    polygon = arcpy.Polygon(array)

                    with arcpy.da.InsertCursor(featureclass_in_mem, ['OriginID', 'BEARING', 'SHAPE@']) as cur:
                        cur.insertRow([columnValue, ang, polygon])

                    array.removeAll()

            arcpy.CopyFeatures_management(r"in_memory\featureclass_in_mem",featureclass)
        else:
            arcpy.AddMessage("....using previous spatial bootstrap.")


        arcpy.AddMessage("....now joining with observations")

        query = '"' + str(flag_field) + '" = ' + str(0)
        arcpy.MakeFeatureLayer_management(input_points, "input_points_query_sub")
        arcpy.Select_analysis("input_points_query_sub", r"in_memory/input_points_query", query)

        count_records = arcpy.GetCount_management(r"in_memory/input_points_query").getOutput(0)
        arcpy.AddMessage("....total number of records to process: " + str(count_records))

        if int(count_records) > 500:
            arcpy.AddMessage("....spatial join will fail due to memory error, working around this limitation...")
            count_records = arcpy.GetCount_management(os.path.join(output_directory, "SectorPoly.shp")).getOutput(0)
            query_1_range = '"' + str("FID") + '" <= ' + str(int(count_records) / 4)
            query_2_range = '"' + str("FID") + '" > ' + str(int(count_records) / 4) + ' And "' + str("FID") + '" < ' + str(int(count_records) / 2)
            query_3_range = '"' + str("FID") + '" >= ' + str(int(count_records) / 2) + ' And "' + str("FID") + '" < ' + str(int(count_records) / 2 + int(count_records) / 4)
            query_4_range = '"' + str("FID") + '" >= ' + str(int(count_records) / 2 + int(count_records) / 4)

            query_list = [query_1_range, query_2_range, query_3_range, query_4_range]
            count = 1

            for i in query_list:
                if not arcpy.Exists(os.path.join(output_directory, "SectorPoly" + str(count) + ".shp")):
                    arcpy.Select_analysis(os.path.join(output_directory, "SectorPoly.shp"), os.path.join(output_directory, "SectorPoly" + str(count) + ".shp"), i)

                    arcpy.SpatialJoin_analysis(os.path.join(output_directory, "SectorPoly" + str(count) + ".shp"),
                                               r"in_memory/input_points_query",
                                               os.path.join(output_directory, "SpatialJoin" + str(count) + ".shp"), "JOIN_ONE_TO_MANY",
                                               "KEEP_ALL", "", "INTERSECT")
                    with arcpy.da.UpdateCursor(os.path.join(output_directory, "SpatialJoin" + str(count) + ".shp"), "Join_Count") as cursor:
                        for row in cursor:
                            if row[0] == 0:
                                cursor.deleteRow()

                if not arcpy.Exists(os.path.join(output_directory, "SpatialJoin" + str(count) + ".csv")):
                    dbf2csv(os.path.join(output_directory, "SpatialJoin" + str(count) + ".dbf"), os.path.join(output_directory, "SpatialJoin" + str(count) + ".csv"))

                count += 1
        else:
            arcpy.SpatialJoin_analysis(os.path.join(output_directory, "SectorPoly.shp"), r"in_memory/input_points_query", r"in_memory/points_SpatialJoin", "JOIN_ONE_TO_MANY", "KEEP_ALL", "", "INTERSECT")

            with arcpy.da.UpdateCursor(r"in_memory/points_SpatialJoin", "Join_Count") as cursor:
                for row in cursor:
                    if row[0] == 0:
                        cursor.deleteRow()

            arcpy.CopyFeatures_management(r"in_memory/points_SpatialJoin",os.path.join(output_directory, os.path.splitext(os.path.basename(input_points))[0] + "_join.shp"))


        attribute_process = attribute_process.split(",")

        if arcpy.Exists(r"in_memory/points_SpatialJoin"):
            for i in attribute_process:
                arcpy.AddMessage("....calculating statistics for " + str(i))
                stats = [[i, "MEAN"], [i, "STD"]]
                arcpy.Statistics_analysis(r"in_memory/points_SpatialJoin",
                                          os.path.join(output_directory, os.path.splitext(os.path.basename(input_points))[0] + "_" + i +".dbf"),
                                          stats, "BEARING")

        else:

            header_saved = False

            if not arcpy.Exists(os.path.join(output_directory, "SpatialJoin_Merge" + ".csv")):

                with open(os.path.join(output_directory, "SpatialJoin_Merge" + ".csv"), 'wb') as fout:
                    for num in range(1,5):
                        with open(os.path.join(output_directory, "SpatialJoin" + str(num) + ".csv")) as fin:
                            header = next(fin)
                            if not header_saved:
                                fout.write(header)
                                header_saved = True
                            for line in fin:
                                fout.write(line)

            for i in attribute_process:
                arcpy.AddMessage("....calculating statistics for " + str(i) + " using pandas1.")
                chunks = pd.read_csv(os.path.join(output_directory, "SpatialJoin_Merge" + ".csv"), chunksize=100000)
                pieces = [x.groupby('BEARING', as_index=False)[i].agg(['count', 'mean', 'std']) for x in chunks]
                result = pd.concat(pieces)
                result.columns = result.columns.droplevel(0)
                result = result.reset_index()
                name_mean = "MEAN_" + str(i)
                name_std = "STD_" + str(i)
                result.rename(columns={'count': 'FREQUENCY'}, inplace=True)
                result.rename(columns={'mean': name_mean[0:10]}, inplace=True)
                result.rename(columns={'std': name_std[0:10]}, inplace=True)

                f = {'FREQUENCY':['sum'], name_mean[0:10]:['mean'], name_std[0:10]:['mean']}

                result_2 = result.groupby('BEARING').agg(f)

                result_2 = result_2.reset_index()

                result_2 = result_2[['BEARING', 'FREQUENCY', name_mean[0:10], name_std[0:10]]]

                result_2.to_csv(os.path.join(output_directory, os.path.splitext(os.path.basename(input_points))[0] + "_" + i +".csv"), index=False)

                if os.path.exists(os.path.join(output_directory, os.path.splitext(os.path.basename(input_points))[0] + "_" + i +".csv")):
                    with open(os.path.join(output_directory, os.path.splitext(os.path.basename(input_points))[0] + "_" + i +".csv"), "r") as f:
                        reader = list(csv.reader(f, delimiter=","))
                        reader.pop(1)
                        reader.pop(1)
                        with open(os.path.join(output_directory, os.path.splitext(os.path.basename(input_points))[0] + "_" + i +".csv"), "w") as out:
                            writer = csv.writer(out, delimiter=",")
                            for row in reader:
                                writer.writerow(row)

                result = arcpy.TableToDBASE_conversion(os.path.join(output_directory, os.path.splitext(os.path.basename(input_points))[0] + "_" + i +".csv"),
                                              output_directory)

        try:
            arcpy.Delete_management(r"in_memory/points_SpatialJoin")
            arcpy.Delete_management(r"in_memory/input_points_query")
        except:
            pass

        if clean_up == "true":
            arcpy.Delete_management(os.path.join(output_directory,"Island_Line.shp"))
            arcpy.CopyFeatures_management(os.path.join(output_directory,"Island_Poly.shp"),os.path.join(output_directory, os.path.splitext(os.path.basename(input_points))[0] + "_poly.shp"))
            arcpy.Delete_management(os.path.join(output_directory,"Island_Poly.shp"))
            arcpy.Delete_management(os.path.join(output_directory,"SectorPoly.shp"))
            arcpy.Delete_management(os.path.join(output_directory,"Fishnet.shp"))
            arcpy.Delete_management(os.path.join(output_directory,"Fishnet_label.shp"))
            arcpy.Delete_management(os.path.join(output_directory,"FishClip.shp"))
            arcpy.Delete_management(os.path.join(output_directory,"FishClipInner.shp"))
            arcpy.Delete_management(os.path.join(output_directory,"RndPts.shp"))
            if int(count_records) > 500:
                arcpy.Delete_management(os.path.join(output_directory, "SectorPoly1" + ".shp"))
                arcpy.Delete_management(os.path.join(output_directory, "SectorPoly2" + ".shp"))
                arcpy.Delete_management(os.path.join(output_directory, "SectorPoly3" + ".shp"))
                arcpy.Delete_management(os.path.join(output_directory, "SectorPoly4" + ".shp"))
                arcpy.Delete_management(os.path.join(output_directory, "SpatialJoin1" + ".shp"))
                arcpy.Delete_management(os.path.join(output_directory, "SpatialJoin2" + ".shp"))
                arcpy.Delete_management(os.path.join(output_directory, "SpatialJoin3" + ".shp"))
                arcpy.Delete_management(os.path.join(output_directory, "SpatialJoin4" + ".shp"))



        arcpy.AddMessage("....completed: " + os.path.splitext(os.path.basename(input_points))[0] + ".")
        arcpy.CheckInExtension('Spatial')
        return

def dbf2csv(dbfpath, csvpath):
    ''' To convert .dbf file or any shapefile/featureclass to csv file
    Inputs:
        dbfpath: full path to .dbf file [input] or featureclass
        csvpath: full path to .csv file [output]
        edited from http://gis.stackexchange.com/questions/93303/bulk-convert-dbf-to-csv-in-a-folder-arcgis-10-1-using-python
    '''
    #import csv
    rows = arcpy.SearchCursor(dbfpath)
    csvFile = csv.writer(open(csvpath, 'wb')) #output csv
    fieldnames = [f.name for f in arcpy.ListFields(dbfpath)]
    csvFile.writerow(fieldnames)

    for row in rows:
        rowlist = []
        for field in fieldnames:
            rowlist.append(row.getValue(field))
        csvFile.writerow(rowlist)

def main():
    tool = IntertidalToolsSpeciesPatternsAroundIslands()
    tool.execute(tool.getParameterInfo(), None)

if __name__=='__main__':
    main()
