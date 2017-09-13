import arcpy
import os
from arcpy.sa import *
from Includes import error_logging, rename_fields

arcpy.CheckOutExtension("Spatial")


class DataToolsZonalStatisticsMultipleRasters(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Caculate zonal statistics for multiple rasters"
        self.description = """This script extracts zonal statistics for multiple overlapping
        zone polygons on multiple rasters. It then attempts to join the data back to the zone
         file with the name of the column being the name of the parent raster.
        """
        self.canRunInBackground = True
        self.category = "Data Tools"  # Use your own category here, or an existing one.

    def getParameterInfo(self):
        params = []

        zone_data = arcpy.Parameter(name="zone_data",
                                    displayName="Input Zone Polygon",
                                    datatype="DEFeatureClass",
                                    parameterType="Required",
                                    direction="Input"
                                    )
        zone_data.value = "D:\Example\DataToolsZonalStatisticsMultipleRasters\Zone.shp"
        params.append(zone_data)

        zone_field = arcpy.Parameter(name="zone_field",
                                       displayName="Field that identifies zones",
                                       datatype="Field",
                                       parameterType="Required",
                                       direction="Input"
                                       )
        zone_field.value = "Id"
        params.append(zone_field)

        statistic_type = arcpy.Parameter(name="statistic_type",
                                       displayName="Calculate which statistic?",
                                       datatype="GPString",
                                       parameterType="Required",
                                       direction="Output"
                                       )
        statistic_type.value = "MEAN"
        params.append(statistic_type)

        raster_list = arcpy.Parameter(name="raster_list",
                                      displayName="Rasters",
                                      datatype="DERasterDataset",
                                      parameterType="Required",
                                      direction="Output",
                                      multiValue=True
                                      )
        raster_list.value = ["D:\Example\DataToolsZonalStatisticsMultipleRasters\depth",
                             "D:\Example\DataToolsZonalStatisticsMultipleRasters\slope_deg"]
        params.append(raster_list)

        # temporary directory
        temporary_directory = arcpy.Parameter(name="temporary_directory",
                                            displayName="Temporary Directory",
                                            datatype="DEFolder",
                                            parameterType="Required",  # Required|Optional|Derived
                                            direction="Output"  # Input|Output
                                            )
        temporary_directory.value = "D:\Example\DataToolsZonalStatisticsMultipleRasters\Temporary\/"
        params.append(temporary_directory)  # ..and then add it to the list of defined parameters

        output_feature = arcpy.Parameter(name="output_feature",
                                       displayName="Output Zone Polygon with statistics",
                                       datatype="DEFeatureClass",
                                       parameterType="Required",
                                       direction="Output"
                                       )
        output_feature.value = "D:\Example\DataToolsZonalStatisticsMultipleRasters\Zone_polygon_output.shp"
        params.append(output_feature)

        logging = arcpy.Parameter(name="logging",
                                  displayName="Logging enabled",
                                  datatype="GPBoolean",
                                  parameterType="Required",  # Required|Optional|Derived
                                  direction="Input"  # Input|Output
                                  )
        logging.value = True
        params.append(logging)  # ..and then add it to the list of defined parameters

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    #def updateParameters(self, parameters):

        #return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of your tool."""
        arcpy.env.overwriteOutput = True

        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )

        zone_data = parameters[0].valueAsText
        zone_field = parameters[1].valueAsText
        statistic_type = parameters[2].valueAsText
        raster_list = parameters[3].valueAsText
        temporary_directory = parameters[4].valueAsText
        output_feature = parameters[5].valueAsText
        logging = parameters[6].valueAsText

        if not os.path.exists(temporary_directory):
            os.makedirs(temporary_directory)

        if isinstance(raster_list, basestring):
            raster_list = raster_list.split(";")

        arcpy.AddMessage("Conduct zonal statistics on multiple rasters for "
                         + str(len(raster_list)) + " rasters.")

        arcpy.env.workspace = temporary_directory
        loop_count = False
        loop_count_2 = False
        concatenate_table_list_merge = []
        first = ""
        arcpy.env.qualifiedFieldNames = False

        for raster in raster_list:
            concatenate_table_list_iterator = []
            concatenate_feature_list_iterator = []
            raster_name = arcpy.Describe(raster)
            if logging:
                error_logging(temporary_directory, str("----Extracting values for "
                                                       + str(raster_name.baseName)))

            zone_name = str(raster_name.baseName)
            # Now we need to loop through the zones to get around a limitation of having overlapping zones
            in_rows = arcpy.SearchCursor(zone_data)
            in_row = in_rows.next()
            string_id = '"FID" ='
            temp_zone = str(zone_name + "_tmp")
            arcpy.MakeFeatureLayer_management(zone_data, temp_zone)
            cell_assign = "CELL_CENTER"
            priority = "NONE"
            new_selection = "NEW_SELECTION"
            count = 0
            while in_row:
                count += 1
                # select the fid to process
                arcpy.SelectLayerByAttribute_management(temp_zone, new_selection, string_id + str(in_row.FID))
                # create a unique name for the zone
                unique_zone = os.path.join(temporary_directory, temp_zone + str(count) + "s.shp")
                unique_table = os.path.join(temporary_directory, temp_zone + str(count) + ".dbf")
                # create a temporary feature to use for zonal stats as table
                arcpy.CopyFeatures_management(temp_zone, unique_zone)
                outZSaT = ZonalStatisticsAsTable(unique_zone, zone_field, raster, unique_table, "NODATA",
                                                 statistic_type)
                concatenate_table_list_iterator.append(unique_table)
                concatenate_feature_list_iterator.append(unique_zone)
                # move to next record.
                in_row = in_rows.next()

            # Clear the last selection.
            #arcpy.SelectLayerByAttribute_management(zone_data, "CLEAR_SELECTION")
            # merge the tables so the can be joined to the zone feature class
            merged_table = os.path.join(temporary_directory, temp_zone + "_merge" + ".dbf")
            arcpy.Merge_management(concatenate_table_list_iterator, merged_table)


            # do some clean up
            for i in concatenate_feature_list_iterator:
                arcpy.Delete_management(i)
            for i in concatenate_table_list_iterator:
                arcpy.Delete_management(i)
            del concatenate_table_list_iterator, concatenate_feature_list_iterator

            # Clean up merged table

            if statistic_type == "MEAN":
                if len(zone_name) > 6:
                    column_name = zone_name[:6] + "_me"
                else:
                    column_name = zone_name + "_me"

                new_name_by_old_name = {'MEAN': column_name}
                rename_fields(merged_table, os.path.join(temporary_directory, temp_zone + "_merge2" + ".dbf"),
                              new_name_by_old_name)

            arcpy.Delete_management(merged_table)

            if not loop_count:
                loop_count = True
            elif loop_count:
                arcpy.DeleteField_management(os.path.join(temporary_directory, temp_zone + "_merge2" + ".dbf"),
                                             ["ZONE_CODE", "COUNT", "AREA"])

            if not loop_count_2:
                loop_count_2 = True
                first = os.path.join(temporary_directory, temp_zone + "_merge2" + ".dbf")
            elif loop_count_2:
                arcpy.JoinField_management(first, zone_field,
                                           os.path.join(temporary_directory, temp_zone + "_merge2" + ".dbf"),
                                           zone_field, [column_name])
                arcpy.Delete_management(os.path.join(temporary_directory, temp_zone + "_merge2" + ".dbf"))
            #ConcatenateTableList_Merge.append(os.path.join(TempDir, tempZone + "_merge2" + ".dbf"))
            del in_row, zone_name

        # join them
        arcpy.MakeFeatureLayer_management(zone_data, "zone_data_fc")
        arcpy.AddJoin_management("zone_data_fc", zone_field, first, zone_field)
        arcpy.Delete_management(first)
        # save the joined data as a new feature
        arcpy.CopyFeatures_management("zone_data_fc", output_feature)

        return


def main():
    tool = DataToolsZonalStatisticsMultipleRasters()
    tool.execute(tool.getParameterInfo(), None)

if __name__ == '__main__':
    main()
