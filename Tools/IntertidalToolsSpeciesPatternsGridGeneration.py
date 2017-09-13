#!/usr/bin/env python
import arcpy
import os
import numpy as np
from math import radians, sin, cos, sqrt

class IntertidalToolsSpeciesPatternsGridGeneration(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Species distribution patterns around islands, generate a grid for analysis"
        self.description = """Orientation of species distributions for G. Williams"""
        self.canRunInBackground = True
        self.category = "Intertidal Tools"

    def getParameterInfo(self):

        params = []

        # Input Island Points
        input_line = arcpy.Parameter(name="input_line",
                                       displayName="Input Line Feature Class",
                                       datatype="DEFile",
                                       parameterType="Optional",
                                       direction="Input",
                                       )
        input_line.value = r"E:\2016\Corals\Gareth_Temp\MAU_NEW_LINE.shp"
        params.append(input_line)

        # Output Directory
        output_directory = arcpy.Parameter(name="output_directory",
                                           displayName="Output Directory",
                                           datatype="DEFolder",
                                           parameterType="Optional",
                                           direction="Input",
                                           )
        output_directory.value = r"E:\2016\Corals\Gareth_Temp1"
        params.append(output_directory)

        # Distance to draw polygon
        distance = arcpy.Parameter(name="distance",
                                   displayName="Buffer distance (metres)",
                                   datatype="GPDouble",
                                   parameterType="Required",
                                   direction="Input",
                                   )
        distance.value = 250
        params.append(distance)

        # Simplify distance to draw polygon
        simp_distance = arcpy.Parameter(name="simp_distance",
                                   displayName="Simplify distance (metres)",
                                   datatype="GPDouble",
                                   parameterType="Required",
                                   direction="Input",
                                   )
        simp_distance.value = 1000
        params.append(simp_distance)

        # Simplify distance to draw polygon
        points_distance = arcpy.Parameter(name="points_distance",
                                   displayName="Points distance (metres)",
                                   datatype="GPDouble",
                                   parameterType="Required",
                                   direction="Input",
                                   )
        points_distance.value = 100
        params.append(points_distance)

        # Clean up
        clean_up = arcpy.Parameter(name="clean_up",
                                   displayName="Delete temporary files?",
                                   datatype="GPBoolean",
                                   parameterType="Required",
                                   direction="Input",
                                   )
        clean_up.value = True
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
        arcpy.AddMessage("Species distribution patterns around islands, generate a grid for analysis")
        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText))

        # See http://resources.arcgis.com/en/help/main/10.2/index.html#//018z00000063000000
        input_line = parameters[0].valueAsText
        output_directory = parameters[1].valueAsText
        distance = parameters[2].value
        simp_distance = parameters[3].value
        points_distance = parameters[4].value
        clean_up = parameters[5].value

        # 0 Describe files to set coordinate systems
        desc_input = arcpy.Describe(input_line)
        coord_system = desc_input.spatialReference
        arcpy.env.outputCoordinateSystem = coord_system

        # 1 Make output director and output files they do not exist
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        arcpy.env.workspace = output_directory

        # 2 Buffer at distance around line
        arcpy.Buffer_analysis(in_features=input_line,
                              out_feature_class=os.path.join(output_directory, "buffer.shp"),
                              buffer_distance_or_field=str(distance) + " Meters", line_side="FULL", line_end_type="ROUND",
                              dissolve_option="NONE", dissolve_field="", method="PLANAR")

        # 3 Convert polygon to Line
        def polys_to_lines(fc, new_fc):
            # From http://gis.stackexchange.com/questions/129662/creating-lines-from-polygon-borders-with-polygon-attributes-using-arcgis-arcpy
            path, name = os.path.split(new_fc)
            sm = 'SAME_AS_TEMPLATE'
            arcpy.CreateFeatureclass_management(path, name, 'POLYLINE', fc, sm, sm, fc)

            fields = [f.name for f in arcpy.ListFields(new_fc)
                      if f.type not in ('OID', 'Geometry')]

            # get attributes
            with arcpy.da.SearchCursor(fc, ['SHAPE@'] + fields) as rows:
                values = [(r[0].boundary(),) + tuple(r[1:]) for r in rows]

            # insert rows
            with arcpy.da.InsertCursor(new_fc, ['SHAPE@'] + fields) as irows:
                for vals in values:
                    irows.insertRow(vals)
            return new_fc

        polys_to_lines(os.path.join(output_directory, "buffer.shp"), os.path.join(output_directory, "lines.shp"))

        arcpy.MultipartToSinglepart_management(in_features=os.path.join(output_directory, "lines.shp"),
                                               out_feature_class=os.path.join(output_directory, "lines_explode.shp"))

        arcpy.SimplifyLine_cartography(in_features=os.path.join(output_directory, "lines_explode.shp"),
                                       out_feature_class=os.path.join(output_directory, "lines_explode_simplify.shp"),
                                       algorithm="BEND_SIMPLIFY", tolerance=str(simp_distance) + " Meters",
                                       error_resolving_option="FLAG_ERRORS",
                                       collapsed_point_option="KEEP_COLLAPSED_POINTS", error_checking_option="CHECK")

        # 4 Create points along the line

        arcpy.CreateFeatureclass_management(output_directory, "points_line.shp", 'POINT')

        arcpy.Project_management(in_dataset=os.path.join(output_directory, "lines_explode_simplify.shp"),
                                 out_dataset=os.path.join(output_directory, "lines_explode_simplify_proj.shp"),
                                 out_coor_system="PROJCS['World_Mercator',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]",
                                 transform_method="",
                                 in_coor_system=coord_system,
                                 preserve_shape="NO_PRESERVE_SHAPE", max_deviation="", vertical="NO_VERTICAL")

        arcpy.CreateFeatureclass_management(output_directory, "points_line_outer.shp", 'POINT')
        arcpy.CreateFeatureclass_management(output_directory, "points_line_inner.shp", 'POINT')

        def points_along_line(line_lyr, pnt_layer, pnt_dist, inn_out):
            # From https://geonet.esri.com/thread/95549

            search_cursor = arcpy.da.SearchCursor(line_lyr, ['SHAPE@', 'FID'])
            insert_cursor = arcpy.da.InsertCursor(pnt_layer, 'SHAPE@')

            for row in search_cursor:
                if inn_out == "inner":
                    if row[1] == 1:
                        for dist in range(0, int(row[0].length), int(pnt_dist)):
                            point = row[0].positionAlongLine(dist).firstPoint
                            insert_cursor.insertRow([point])
                elif inn_out == "outer":
                    if row[1] == 0:
                        for dist in range(0, int(row[0].length), int(pnt_dist)):
                            point = row[0].positionAlongLine(dist).firstPoint
                            insert_cursor.insertRow([point])

        points_along_line(os.path.join(output_directory, "lines_explode_simplify_proj.shp"),
                          os.path.join(output_directory, "points_line.shp"),
                          points_distance, "inner")

        points_along_line(os.path.join(output_directory, "lines_explode_simplify_proj.shp"),
                          os.path.join(output_directory, "points_line_outer.shp"),
                          1, "outer")

        points_along_line(os.path.join(output_directory, "lines_explode_simplify_proj.shp"),
                          os.path.join(output_directory, "points_line_inner.shp"),
                          1, "inner")

        rows_list = [row for row in arcpy.da.SearchCursor(os.path.join(output_directory, "points_line.shp"), "FID")]
        delete_cursor = arcpy.da.UpdateCursor(os.path.join(output_directory, "points_line.shp"), "FID")
        delete_value = rows_list[-1][0]

        for row in delete_cursor:
            if row[0] == delete_value:
                delete_cursor.deleteRow()

        arcpy.DefineProjection_management(os.path.join(output_directory, "points_line.shp"),
                                          coor_system="PROJCS['World_Mercator',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]")

        arcpy.DefineProjection_management(os.path.join(output_directory, "points_line_outer.shp"),
                                          coor_system="PROJCS['World_Mercator',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]")

        arcpy.DefineProjection_management(os.path.join(output_directory, "points_line_inner.shp"),
                                          coor_system="PROJCS['World_Mercator',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]")

        arcpy.Project_management(os.path.join(output_directory, "points_line.shp"),
                                 out_dataset=os.path.join(output_directory, "points_line_wgs.shp"),
                                 out_coor_system=coord_system,
                                 transform_method="",
                                 in_coor_system="PROJCS['World_Mercator',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]",
                                 preserve_shape="NO_PRESERVE_SHAPE", max_deviation="", vertical="NO_VERTICAL")

        def points_to_polygon_line(output_directory, points):
            sr = arcpy.Describe(os.path.join(output_directory, points)).spatialReference

            coords = np.array(list(list(x) for x in arcpy.da.FeatureClassToNumPyArray(
                os.path.join(output_directory, points), ["SHAPE@X", "SHAPE@Y"], "", sr,
                explode_to_points=True)), dtype="float64")

            arcpy.CreateFeatureclass_management(output_directory, "p2pl_li_" + points, "Polyline")
            arcpy.CreateFeatureclass_management(output_directory, "p2pl_pol_" + points, "Polygon")

            pnt = arcpy.Point()
            ary = arcpy.Array()

            cur = arcpy.InsertCursor(os.path.join(output_directory, "p2pl_pol_" + points))
            for coord in coords:
                pnt.X = coord[0]
                pnt.Y = coord[1]
                ary.add(pnt)
            polygon = arcpy.Polygon(ary)
            feat = cur.newRow()
            feat.shape = polygon
            cur.insertRow(feat)

            del cur, pnt, ary, coord, polygon, feat

            pnt = arcpy.Point()
            ary = arcpy.Array()

            cur = arcpy.InsertCursor(os.path.join(output_directory, "p2pl_li_" + points))
            for coord in coords:
                pnt.X = coord[0]
                pnt.Y = coord[1]
                ary.add(pnt)
            line = arcpy.Polyline(ary)
            feat = cur.newRow()
            feat.shape = line
            cur.insertRow(feat)
            del cur, pnt, ary, coord, line, feat

            arcpy.DefineProjection_management(os.path.join(output_directory, "p2pl_li_" + points),
                                              coor_system="PROJCS['World_Mercator',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]")

            arcpy.DefineProjection_management(os.path.join(output_directory, "p2pl_pol_" + points),
                                              coor_system="PROJCS['World_Mercator',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]")

            return

        points_to_polygon_line(output_directory, "points_line_inner.shp")

        points_to_polygon_line(output_directory, "points_line_outer.shp")

        # 5 Generate perpendicular lines
        desc = arcpy.Describe(os.path.join(output_directory, "points_line.shp"))
        sr = arcpy.SpatialReference(desc.spatialReference.factoryCode)

        dests = np.array(list(list(x) for x in
                              arcpy.da.FeatureClassToNumPyArray(os.path.join(output_directory, "points_line_outer.shp"),
                                                                ["SHAPE@X", "SHAPE@Y"], "", sr, True)), dtype="float64")

        arcpy.CreateFeatureclass_management(output_directory, "intersect_lines.shp", "Polyline")

        search_cursor = arcpy.da.SearchCursor(os.path.join(output_directory, "points_line.shp"), ['SHAPE@X', 'SHAPE@Y'])

        for row in search_cursor:
            origin = np.array((row[0], row[1]), dtype="float64")
            deltas = dests - origin
            distances = np.hypot(deltas[:, 0], deltas[:, 1])
            min_dist = np.min(distances)
            wh = np.where(distances == min_dist)
            closest = dests[wh[0]]

            cur = arcpy.InsertCursor(os.path.join(output_directory, "intersect_lines.shp"))

            # Build array of start/ends
            line_array = arcpy.Array()
            # start point
            start = arcpy.Point()
            (start.ID, start.X, start.Y) = (1, origin.item((0)), origin.item((1)))
            line_array.add(start)
            # end point
            end = arcpy.Point()
            (end.ID, end.X, end.Y) = (2, closest.item((0, 0)), closest.item((0, 1)))
            line_array.add(end)
            # write our fancy feature to the shapefile
            feat = cur.newRow()
            feat.shape = line_array
            cur.insertRow(feat)
            # yes, this shouldn't really be necessary...
            line_array.removeAll()
            del origin

        arcpy.DefineProjection_management(os.path.join(output_directory, "intersect_lines.shp"),
                                          coor_system="PROJCS['World_Mercator',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]")

        arcpy.Union_analysis(in_features=[os.path.join(output_directory, "p2pl_pol_points_line_inner.shp"),
                                          os.path.join(output_directory, "p2pl_pol_points_line_outer.shp")],
                             out_feature_class=os.path.join(output_directory, "simplified_polygon.shp"),
                             join_attributes="ALL", cluster_tolerance="", gaps="GAPS")

        with arcpy.da.UpdateCursor(os.path.join(output_directory, "simplified_polygon.shp"), "FID") as cursor:
            for row in cursor:
                if row[0] == 1:
                    cursor.deleteRow()

        arcpy.Buffer_analysis(in_features=os.path.join(output_directory, "intersect_lines.shp"),
                              out_feature_class=os.path.join(output_directory, "intersect_lines_buf.shp"),
                              buffer_distance_or_field="1 Centimeters", line_side="FULL",
                              line_end_type="ROUND", dissolve_option="NONE", dissolve_field="",
                              method="PLANAR")

        arcpy.Union_analysis(in_features=[os.path.join(output_directory, "intersect_lines_buf.shp"),
                                          os.path.join(output_directory, "simplified_polygon.shp")],
                             out_feature_class=os.path.join(output_directory, "intersect_lines_buffered_polygon.shp"),
                             join_attributes="ALL", cluster_tolerance="", gaps="GAPS")

        arcpy.Project_management(os.path.join(output_directory, "intersect_lines_buffered_polygon.shp"),
                                 out_dataset=os.path.join(output_directory, "intersect_lines_buffered_polygon_proj.shp"),
                                 out_coor_system="PROJCS['World_Mercator',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]",
                                 transform_method="",
                                 in_coor_system=coord_system,
                                 preserve_shape="NO_PRESERVE_SHAPE", max_deviation="", vertical="NO_VERTICAL")

        arcpy.CalculateAreas_stats(
            Input_Feature_Class=os.path.join(output_directory, "intersect_lines_buffered_polygon_proj.shp"),
            Output_Feature_Class=os.path.join(output_directory, "intersect_lines_buffered_polygon_areas.shp"))

        polygon_sizes = []

        with arcpy.da.SearchCursor(os.path.join(output_directory, "intersect_lines_buffered_polygon_areas.shp"),
                                   "F_Area") as cursor:
            for row in cursor:
                polygon_sizes.append(int(row[0]))

        polygon_sizes = sorted(polygon_sizes, key=int, reverse=True)

        with arcpy.da.UpdateCursor(os.path.join(output_directory, "intersect_lines_buffered_polygon_areas.shp"),
                                   "F_Area") as cursor:
            for row in cursor:
                if int(row[0]) == int(polygon_sizes[0]):
                    pass
                else:
                    cursor.deleteRow()

        arcpy.MultipartToSinglepart_management(
            in_features=os.path.join(output_directory, "intersect_lines_buffered_polygon_areas.shp"),
            out_feature_class=os.path.join(output_directory, "grid_file1.shp"))

        arcpy.Project_management(os.path.join(output_directory, "grid_file1.shp"),
                                 out_dataset=os.path.join(output_directory, "grid_file.shp"),
                                 out_coor_system="PROJCS['World_Mercator',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]",
                                 transform_method="",
                                 in_coor_system=coord_system,
                                 preserve_shape="NO_PRESERVE_SHAPE", max_deviation="", vertical="NO_VERTICAL")

        arcpy.AddField_management(in_table=os.path.join(output_directory, "grid_file.shp"), field_name="GRID_ID",
                                  field_type="LONG",
                                  field_precision="", field_scale="", field_length="", field_alias="",
                                  field_is_nullable="NULLABLE", field_is_required="NON_REQUIRED", field_domain="")

        with arcpy.da.UpdateCursor(os.path.join(output_directory, "grid_file.shp"), ["FID", "GRID_ID"]) as cursor:
            for row in cursor:
                row[1] = row[0]
                cursor.updateRow(row)

        arcpy.Project_management(os.path.join(output_directory, "grid_file.shp"),
                                 out_dataset=os.path.join(output_directory, "grid_file_wgs.shp"),
                                 out_coor_system=coord_system,
                                 transform_method="",
                                 in_coor_system="PROJCS['World_Mercator',GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]],PROJECTION['Mercator'],PARAMETER['False_Easting',0.0],PARAMETER['False_Northing',0.0],PARAMETER['Central_Meridian',0.0],PARAMETER['Standard_Parallel_1',0.0],UNIT['Meter',1.0]]",
                                 preserve_shape="NO_PRESERVE_SHAPE", max_deviation="", vertical="NO_VERTICAL")

        arcpy.AddWarning("The field name GRID_ID will likely not be sequential, and you will have to fix manually.")

        arcpy.AddMessage("After fixing the non-sequentially spaced names, you will have to manually join "
                         "the layer back to the original point observations.")

        if clean_up:
            delete_list = [os.path.join(output_directory, "buffer.shp"),
                           os.path.join(output_directory, "lines.shp"),
                           os.path.join(output_directory, "lines_explode.shp"),
                           os.path.join(output_directory, "lines_explode_simplify.shp"),
                           os.path.join(output_directory, "lines_explode_simplify_Pnt.shp"),
                           os.path.join(output_directory, "intersect_lines_buffered_polygon_areas.shp"),
                           os.path.join(output_directory, "intersect_lines_buffered_polygon_proj.shp"),
                           os.path.join(output_directory, "lines_explode_simplify_proj.shp"),
                           os.path.join(output_directory, "p2pl_li_points_line_inner.shp"),
                           os.path.join(output_directory, "p2pl_li_points_line_outer.shp"),
                           os.path.join(output_directory, "p2pl_pol_points_line_inner.shp"),
                           os.path.join(output_directory, "p2pl_pol_points_line_outer.shp"),
                           os.path.join(output_directory, "points_line.shp"),
                           os.path.join(output_directory, "points_line_inner.shp"),
                           os.path.join(output_directory, "points_line_outer.shp"),
                           os.path.join(output_directory, "points_line_wgs.shp"),
                           os.path.join(output_directory, "simplified_polygon.shp"),
                           os.path.join(output_directory, "grid_file1.shp"),
                           os.path.join(output_directory, "intersect_lines.shp"),
                           os.path.join(output_directory, "intersect_lines_buf.shp"),
                           os.path.join(output_directory, "intersect_lines_buffered_polygon.shp"),
                           ]
            for i in delete_list:
                arcpy.Delete_management(i)

        return

def main():
    tool = IntertidalToolsSpeciesPatternsGridGeneration()
    tool.execute(tool.getParameterInfo(), None)

if __name__=='__main__':
    main()