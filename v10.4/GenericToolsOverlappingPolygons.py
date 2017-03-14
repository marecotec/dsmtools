#!/usr/bin/env python
import arcpy
import os

arcpy.CheckOutExtension("Spatial")


class GenericToolsOverlappingPolygons(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Overlapping polygons"
        self.description = """Calculate the frequency of overlap in a polygon shapefile using a unique identifier for each polygon"""
        self.canRunInBackground = False
        self.category = "Generic Tools"  # Use your own category here, or an existing one.

    def getParameterInfo(self):

        # You can define a tool to have no parameters
        params = []

        # Input Island Points
        input_feature = arcpy.Parameter(name="input_feature",
                                       displayName="Input Feature Class",
                                       datatype="DEFeatureClass",
                                       parameterType="Required",  # Required|Optional|Derived
                                       direction="Input",  # Input|Output
                                       )
        input_feature.value = "D:\Example\GenericToolsOverlappingPolygons\Input_Data\CONESNAILS.shp"
        params.append(input_feature)

        # Select attribute columns for the split
        attribute_1 = arcpy.Parameter(name="attribute_1",
                                      displayName="Attribute 1 to filter (Use ID or FID, or a numerical field)",
                                      datatype="Field",
                                      parameterType="Required",
                                      direction="Input")
        # Derived parameter
        attribute_1.parameterDependencies = [input_feature.name]
        attribute_1.value = "FID"
        params.append(attribute_1)

        # Select attribute columns for the split
        polygon_conversion_size = arcpy.Parameter(name="polygon_conversion_size",
                                      displayName="Size of polygon conversion (smaller = longer processing time)",
                                      datatype="GPString",
                                      parameterType="Required",
                                      direction="Input")
        # Derived parameter
        polygon_conversion_size.value = "0.05"
        params.append(polygon_conversion_size)

        # Output feature class
        output_directory = arcpy.Parameter(name="output_directory",
                                        displayName="Output directory",
                                        datatype="DEWorkspace",
                                        parameterType="Required",  # Required|Optional|Derived
                                        direction="Output",  # Input|Output
                                        )
        output_directory.value = "D:\Example\GenericToolsOverlappingPolygons\Output_Data"

        # output_points.schema.clone = True
        params.append(output_directory)
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
        arcpy.AddMessage("Overlapping polygons")
        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )

        # See http://resources.arcgis.com/en/help/main/10.2/index.html#//018z00000063000000
        input_feature = parameters[0].valueAsText
        attribute_1 = parameters[1].valueAsText
        polygon_conversion_size = parameters[2].valueAsText
        output_directory = parameters[3].valueAsText

        # Make output directory if it does not exist
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        if not os.path.exists(os.path.join(output_directory, "Temp")):
            os.makedirs(os.path.join(output_directory, "Temp"))

        # Read through the attribute table to create a list of unique attributes, start with parent
        # aka Attribute 1

        attribute_1_types = set([row.getValue(attribute_1) for row in arcpy.SearchCursor(input_feature)])

        count = 1

        # Output a feature for the parent attribute
        for each_attribute in attribute_1_types:

            output_feature = os.path.join(output_directory, "Temp", "poly" + str(count) + ".shp")
            output_raster = os.path.join(output_directory, "Temp", "r" + str(count))
            output_raster_con = os.path.join(output_directory, "Temp", "c" + str(count))

            arcpy.AddMessage("Processing: " + str(output_feature))

            arcpy.Select_analysis(input_feature, output_feature, "\"" + attribute_1 +
                                  "\" = " + str(each_attribute) + "")

            arcpy.PolygonToRaster_conversion(in_features=output_feature, value_field=attribute_1,
                                             out_rasterdataset=output_raster,
                                             cell_assignment="CELL_CENTER", priority_field="NONE",
                                             cellsize=polygon_conversion_size)

            arcpy.gp.Con_sa(output_raster, "1", output_raster_con, "", "VALUE >= 0")

            count = count + 1

        arcpy.env.workspace = os.path.join(output_directory, "Temp")
        raster_list = arcpy.ListRasters("c*")

        outCellStatistics = arcpy.sa.CellStatistics(raster_list, "SUM", "DATA")

        outCellStatistics.save(os.path.join(output_directory, "output"))

        return


def main():
    tool = GenericToolsOverlappingPolygons()
    tool.execute(tool.getParameterInfo(), None)

if __name__ == '__main__':
    main()
