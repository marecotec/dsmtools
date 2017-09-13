#!/usr/bin/env python
import arcpy
import os
from math import radians, sin, cos


class GenericToolsSplitByAttributes(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Split by attributes"
        self.description = """Split a shapefile by it's attributes"""
        self.canRunInBackground = False
        self.category = "Generic Tools"  # Use your own category here, or an existing one.

    def getParameterInfo(self):
        """Define parameter definitions
           Refer to http://resources.arcgis.com/en/help/main/10.2/index.html#/Defining_parameters_in_a_Python_toolbox/001500000028000000/
           For datatype see http://resources.arcgis.com/en/help/main/10.2/index.html#/Defining_parameter_data_types_in_a_Python_toolbox/001500000035000000/
        """

        # You can define a tool to have no parameters
        params = []

        # Input Island Points
        input_feature = arcpy.Parameter(name="input_feature",
                                       displayName="Input Feature Class",
                                       datatype="DEFeatureClass",
                                       parameterType="Required",  # Required|Optional|Derived
                                       direction="Input",  # Input|Output
                                       )
        input_feature.value = r"E:\2016\Corals\IndividualIslands_ByYear_Points_Env\IntegratedWavePower-2012.shp"

        params.append(input_feature)

        # Select attribute columns for the split
        attribute_1 = arcpy.Parameter(name="attribute_1",
                                      displayName="Attribute 1 to filter",
                                      datatype="Field",
                                      parameterType="Required",
                                      direction="Input")
        # Derived parameter
        attribute_1.parameterDependencies = [input_feature.name]
        attribute_1.value = "ISL"
        params.append(attribute_1)

        # Select attribute columns for the split
        attribute_2 = arcpy.Parameter(name="attribute_2",
                                      displayName="Attribute 2 to filter",
                                      datatype="Field",
                                      parameterType="Required",
                                      direction="Input")
        # Derived parameter
        attribute_2.parameterDependencies = [input_feature.name]
        attribute_2.value = "year"
        params.append(attribute_2)

        # Output feature class
        output_directory = arcpy.Parameter(name="output_directory",
                                        displayName="Output directory",
                                        datatype="DEWorkspace",
                                        parameterType="Required",  # Required|Optional|Derived
                                        direction="Output",  # Input|Output
                                        )
        output_directory.value = r"E:\2016\Corals\IndividualIslands_ByYear_Points_Env\IntegratedWavePower-1979-2012"

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
        arcpy.AddMessage("Split feature by attributes")
        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )

        # See http://resources.arcgis.com/en/help/main/10.2/index.html#//018z00000063000000
        input_feature = parameters[0].valueAsText
        attribute_1 = parameters[1].valueAsText
        attribute_2 = parameters[2].valueAsText
        output_directory = parameters[3].valueAsText

        # Make output directory if it does not exist
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # Read through the attribute table to create a list of unique attributes, start with parent
        # aka Attribute 1

        attribute_1_types = set([row.getValue(attribute_1) for row in arcpy.SearchCursor(input_feature)])

        # Output a feature for the parent attribute
        for each_attribute in attribute_1_types:
            output_feature = os.path.join(output_directory, str(each_attribute) + "_ALL.shp")
            arcpy.AddMessage(str(output_feature))
            arcpy.Select_analysis(input_feature, output_feature, "\"" + attribute_1 +
                                  "\" = '" + each_attribute + "'")

            #Need to do anyting to a layer, do it here, will propagate
            arcpy.AddField_management(output_feature, "Flag", "SHORT", "", "", "4")

            # Now iterate through the second attribute filter
            attribute_2_types = set([row.getValue(attribute_2) for row in arcpy.SearchCursor(output_feature)])

            for each_attribute_2 in attribute_2_types:
                output_feature_2 = os.path.join(output_directory, str(each_attribute) + "_" +
                                                str(each_attribute_2) + ".shp")

                arcpy.AddMessage(str(output_feature_2))

                arcpy.Select_analysis(output_feature, output_feature_2, "\"" + attribute_2 + "\" = " +
                                      str(each_attribute_2))



        return


def main():
    tool = GenericToolsSplitByAttributes()
    tool.execute(tool.getParameterInfo(), None)

if __name__ == '__main__':
    main()
