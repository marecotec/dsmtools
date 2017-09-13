#!/usr/bin/env python
import arcpy
import pandas as pd
import os, csv
from math import radians, sin, cos


class GenericToolsBatchExecute(object):
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
        input_commands = arcpy.Parameter(name="input_feature",
                                       displayName="Input CSV File",
                                       datatype="GPString",
                                       parameterType="Required",  # Required|Optional|Derived
                                       direction="Input",  # Input|Output
                                       )
        input_commands.value = "D:\Example\GenericToolsBatchExecute\Batch.csv"
        params.append(input_commands)

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
        arcpy.AddMessage("Batch Execute from file")
        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )

        # See http://resources.arcgis.com/en/help/main/10.2/index.html#//018z00000063000000
        input_commands = parameters[0].valueAsText

        csv = pd.read_csv(input_commands)

        print csv

        return


def main():
    tool = GenericToolsBatchExecute()
    tool.execute(tool.getParameterInfo(), None)

if __name__ == '__main__':
    main()
