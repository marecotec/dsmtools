#!/usr/bin/env python
import arcpy
import os
from math import radians, sin, cos, sqrt

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

        # Input Island Points
        input_points = arcpy.Parameter(name="input_points",
                                       displayName="Input Feature Class",
                                       datatype="DEFeatureClass",
                                       parameterType="Optional",  # Required|Optional|Derived
                                       direction="Input",  # Input|Output
                                       )
        # You can set filters here for example input_fc.filter.list = ["Polygon"]
        # You can set a default if you want -- this makes debugging a little easier.
        input_points.value = "E:/2016/Corals/IndividualIslands/KUR_2004.shp"
        params.append(input_points)  # ..and then add it to the list of defined parameters

        # Input Island Points
        input_directory = arcpy.Parameter(name="input_directory",
                                       displayName="Input Directory",
                                       datatype="DEFeatureClass",
                                       parameterType="Optional",  # Required|Optional|Derived
                                       direction="Input",  # Input|Output
                                       )
        # You can set filters here for example input_fc.filter.list = ["Polygon"]
        # You can set a default if you want -- this makes debugging a little easier.
        input_directory.value = ""
        params.append(input_directory)  # ..and then add it to the list of defined parameters


        points_order = arcpy.Parameter(name="points_order",
                                       displayName="Are your points in FID order?",
                                       datatype="GPBoolean",
                                       parameterType="Required",
                                       direction="Input",
                                       )
        points_order.value = "False"
        params.append(points_order)

        # Select attribute column for the calculation
        attribute_process = arcpy.Parameter(name="attribute_1",
                                      displayName="Column to process",
                                      datatype="Field",
                                      parameterType="Required",
                                      direction="Input")
        # Derived parameter
        attribute_process.parameterDependencies = [input_points.name]
        attribute_process.value = "MACROALGAE"
        params.append(attribute_process)

        # Distance to draw polygon
        distance = arcpy.Parameter(name="distance",
                                   displayName="Distance to capture coastline",
                                   datatype="GPDouble",
                                   parameterType="Required", # Required|Optional|Derived
                                   direction="Input", # Input|Output
                                   )
        # You could set a list of acceptable values here for example
        # number.filter.type = "ValueList"
        # number.filter.list = [1,2,3,123]
        # You can set a default value here.
        distance.value = 100000
        params.append(distance)

        # Angle to capture patterns
        angle = arcpy.Parameter(name="angle",
                                 displayName="Angle for search",
                                 datatype="GPLong",
                                 parameterType="Required", # Required|Optional|Derived
                                 direction="Input", # Input|Output
                                )
        # You could set a list of acceptable values here for example
        # number.filter.type = "ValueList"
        # number.filter.list = [1,2,3,123]
        # You can set a default value here.
        angle.value = 10
        params.append(angle)

        # Output feature class
        output_directory = arcpy.Parameter(name="output_directory",
                                        displayName="Output directory",
                                        datatype="DEWorkspace",
                                        parameterType="Optional",  # Required|Optional|Derived
                                        direction="Output",  # Input|Output
                                        )
        output_directory.value = "E:/2016/Corals/Temp/"
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
        """The source code of your tool."""
        arcpy.env.overwriteOutput = True
        arcpy.AddMessage("Orientation of species distributions")
        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText))

        # See http://resources.arcgis.com/en/help/main/10.2/index.html#//018z00000063000000
        input_points = parameters[0].valueAsText
        input_directory = parameters[1].valueAsText
        points_order = parameters[2].valueAsText
        attribute_process = parameters[3].value
        distance = parameters[4].value
        angle = parameters[5].value
        output_directory = parameters[6].valueAsText
        clean_up = parameters[7].valueAsText


        # Make output directory if it does not exist
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        featureclasses = []

        if input_directory is None:
            featureclasses.append(input_points)
        elif input_directory is not None:
            arcpy.env.workspace = input_directory
            featureclasses = arcpy.ListFeatureClasses()
            arcpy.env.workspace = output_directory

        for fc in featureclasses:

            if input_directory is None:
                input_points = fc
            elif input_directory is not None:
                input_points = os.path.join(input_directory, fc)

            # 0 Describe files to set coordinate systems
            desc_input = arcpy.Describe(input_points)
            coord_system = desc_input.spatialReference
            arcpy.env.outputCoordinateSystem = coord_system

            # 1 Generate an Island Polygon from our input points, intersect it with a fishnet and then keep only
            # polygons within the Island polygon.

            if points_order == "false":
                arcpy.AddMessage("Calculating convex hull for " + os.path.splitext(os.path.basename(input_points))[0] + ".")
                arcpy.MinimumBoundingGeometry_management(in_features=input_points,
                                                         out_feature_class=os.path.join(output_directory,"Island_Poly.shp"),
                                                         geometry_type="CONVEX_HULL",
                                                         group_option="ALL",
                                                         group_field="",
                                                         mbg_fields_option="NO_MBG_FIELDS"
                                                         )

            if points_order == "true":
                arcpy.AddMessage("Joining points for " + os.path.splitext(os.path.basename(input_points))[0] + ".")
                arcpy.PointsToLine_management(Input_Features=input_points,
                                              Output_Feature_Class=os.path.join(output_directory,"Island_Line.shp"),
                                              Line_Field="",
                                              Sort_Field="FID",
                                              Close_Line="CLOSE")
                arcpy.FeatureToPolygon_management(in_features=os.path.join(output_directory,"Island_Line.shp"),
                                                  out_feature_class=os.path.join(output_directory,"Island_Poly.shp"),
                                                  cluster_tolerance="",
                                                  attributes="NO_ATTRIBUTES",
                                                  label_features="")

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
                "....fishnet size is: " + str(island_area_polygon) + ".")

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

            arcpy.CreateRandomPoints_management(out_path=output_directory,
                                                out_name="RndPts.shp",
                                                constraining_feature_class=os.path.join(output_directory,"FishClipInner.shp"),
                                                constraining_extent="0 0 250 250",
                                                number_of_points_or_field="5",
                                                minimum_allowed_distance="0 Meters",
                                                create_multipoint_output="POINT",
                                                multipoint_size="0")

            arcpy.DefineProjection_management(os.path.join(output_directory,"RndPts.shp"), coord_system)

            # 3 Create area polygons
            arcpy.DefineProjection_management(os.path.join(output_directory,"RndPts.shp"), coord_system)
            rows = arcpy.SearchCursor(os.path.join(output_directory,"RndPts.shp"))
            desc = arcpy.Describe(os.path.join(output_directory,"RndPts.shp"))
            shapefieldname = desc.ShapeFieldName

            featureclass = os.path.join(output_directory,"SectorPoly.shp")

            if not arcpy.Exists(featureclass):
                arcpy.CreateFeatureclass_management(os.path.dirname(featureclass), os.path.basename(featureclass), "Polygon")
                arcpy.AddField_management(featureclass, str("FID_Fishne"), "TEXT", "", "", "150")
                arcpy.AddField_management(featureclass, "BEARING", "SHORT", "", "", "4")
                arcpy.DeleteField_management(featureclass, ["Id"])
                arcpy.DefineProjection_management(featureclass, coord_system)

            finalfeatureclass = os.path.join(output_directory,"Final.shp")

            if not arcpy.Exists(featureclass):
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

            arcpy.AddMessage("....now making sectors")

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

            arcpy.AddMessage("....now joining with observations")

            arcpy.SpatialJoin_analysis(featureclass, input_points, r"in_memory/points_SpatialJoin", "JOIN_ONE_TO_MANY", "KEEP_ALL", "", "INTERSECT")

            with arcpy.da.UpdateCursor(r"in_memory/points_SpatialJoin", "Join_Count") as cursor:
                for row in cursor:
                    if row[0] == 0:
                        cursor.deleteRow()

            arcpy.CopyFeatures_management(r"in_memory/points_SpatialJoin",os.path.join(output_directory, os.path.splitext(os.path.basename(input_points))[0] + "_join.shp"))

            arcpy.AddMessage("....calculating statistics")

            stats = [[attribute_process, "MEAN"], [attribute_process, "STD"]]

            arcpy.Statistics_analysis(r"in_memory/points_SpatialJoin",
                                      os.path.join(output_directory, os.path.splitext(os.path.basename(input_points))[0] + ".dbf"),
                                      stats, "BEARING")
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

            arcpy.AddMessage("....completed: " + os.path.splitext(os.path.basename(input_points))[0] + ".")

        return

def main():
    tool = IntertidalToolsSpeciesPatternsAroundIslands()
    tool.execute(tool.getParameterInfo(), None)

if __name__=='__main__':
    main()