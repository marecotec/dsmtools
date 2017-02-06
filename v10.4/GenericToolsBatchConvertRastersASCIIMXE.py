#!/usr/bin/env python
import sys, os, arcpy


class GenericToolsBatchConvertRastersASCIIMXE(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Batch convert directory of rasters to ASCII and MXE formats"
        self.description = """Description"""
        self.canRunInBackground = False
        self.category = "Generic Tools"  # Use your own category here, or an existing one.

    def getParameterInfo(self):

        params = []

        input_directory = arcpy.Parameter(name="input_directory",
                                          displayName="Directory of rasters",
                                          datatype="DEWorkspace",
                                          parameterType="Required",
                                          direction="Input",
                                          )
        input_directory.value = "D:\Example\GenericToolsBatchConvertRastersASCIIMXE\Rasters\/"
        params.append(input_directory)

        output_directory = arcpy.Parameter(name="output_directory",
                                           displayName="Output directory",
                                           datatype="DEWorkspace",
                                           parameterType="Required",  # Required|Optional|Derived
                                           direction="Output",  # Input|Output
                                           )
        output_directory.value = "D:\Example\GenericToolsBatchConvertRastersASCIIMXE\Output\/"
        params.append(output_directory)

        out_mxe = arcpy.Parameter(name="out_mxe",
                                  displayName="Do you want to create MXE for Maxent?",
                                  datatype="GPBoolean",
                                  parameterType="Required",
                                  direction="Input",
                                  )
        out_mxe.ValueList = ["True", "False"]
        out_mxe.value = "True"
        params.append(out_mxe)

        path_mxe = arcpy.Parameter(name="path_mxe",
                                   displayName="Path to Maxent jar",
                                   datatype="DEFolder",
                                   parameterType="Required",
                                   direction="Input",
                                   )
        path_mxe.value = "D:\Misc\MaxentJar\/"
        params.append(path_mxe)

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    #def updateParameters(self, parameters):

        #return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        try:
            path_mxe = parameters[3].valueAsText
            os.path.exists(os.path.join(path_mxe, "maxent.jar"))
            if not os.path.exists(os.path.join(path_mxe, "maxent.jar")):
                parameters[3].setErrorMessage("Maxent Jar not found in directory ")
        except Exception:
            pass
        return

    def execute(self, parameters, messages):
        arcpy.AddMessage("Batch convert rasters to ASCII and MXE formats")
        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText) )

        input_directory = parameters[0].valueAsText
        output_directory = parameters[1].valueAsText
        out_mxe = parameters[2].valueAsText
        path_mxe = parameters[3].valueAsText

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        arcpy.env.workspace = input_directory
        rasterlist = arcpy.ListRasters("*")
        arcpy.AddMessage("There are " + str(len(rasterlist)) + " rasters to process.")

        for raster in rasterlist:
            arcpy.AddMessage("Converting " + str(raster) + ".")
            if not arcpy.Exists(os.path.join(output_directory, raster + ".asc")):
                arcpy.RasterToASCII_conversion(raster, os.path.join(output_directory, raster + ".asc"))

        if out_mxe:
            command = 'java -cp "' + os.path.join(path_mxe, "maxent.jar") + '" density.Convert ' + \
                      output_directory + " asc " + output_directory + " mxe"
            arcpy.AddMessage("Calling Maxent to convert ASCII to MXE: " + str(command))
            os.system(str(command))

        return


def main():
    tool = GenericToolsBatchConvertRastersASCIIMXE()
    tool.execute(tool.getParameterInfo(), None)

if __name__ == '__main__':
    main()
