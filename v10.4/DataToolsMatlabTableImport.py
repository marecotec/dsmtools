#!/usr/bin/env python
import arcpy
import os
import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt

class DataToolsMatlabTableImport(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Matlab Table Import"
        self.description = """Import Matlab outputs and export XYZ/ASCII Grid, in the form of a table of values,
                            first row = longitude, first column = latitude"""
        self.canRunInBackground = True
        self.category = "Data Tools"  # Use your own category here, or an existing one.

    def getParameterInfo(self):

        # You can define a tool to have no parameters
        params = []

        # Input Island Line - Demarks the area in which we will spatially bootstrap
        input_file = arcpy.Parameter(name="input_file",
                                       displayName="Input Matlab file",
                                       datatype="DEFile",
                                       parameterType="Required",
                                       direction="Input",
                                       )
        input_file.value = "D:/Example_Data/DataToolsMatlabTableImport/Example_Matlab_File.dat"
        params.append(input_file)

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
        arcpy.AddMessage("Matlab Table Import")

        for param in parameters:
            arcpy.AddMessage("Parameter: %s = %s" % (param.name, param.valueAsText))

        # Read in variables for the tool
        input_file = parameters[0].valueAsText

        input_file_dir = os.path.dirname(input_file)
        input_file_name = os.path.basename(input_file)

        arcpy.env.workspace = input_file_dir[0]

        data = pd.read_csv(os.path.join(input_file_dir, input_file_name), header=None, delim_whitespace=True)

        data.columns = data.iloc[0]
        data = data[1:]
        data = data.set_index(["Lat"])
        #data = data.T
        data = data.replace([0], [-9999])
        data.stack().to_csv(os.path.join(input_file_dir, input_file_name + ".csv"), sep=',')

        xyz_array = pd.read_csv(os.path.join(input_file_dir, input_file_name + ".csv"), header=0, names=["y", "x", "val"], sep=",")
        result = xyz_array.diff(periods=1, axis=0)

        nrows, ncols = data.shape
        xllcorner = xyz_array['x'].min()
        yllcorner = xyz_array['y'].min()
        cellsize = result['x'].value_counts().idxmax()
        nodataval = "-9999"
        zgrid = np.zeros((nrows, ncols), dtype=np.float32)
        zgrid.fill(nodataval)

        for row in xyz_array.itertuples():
            index, y, x, val = row
            idx = (float(x) - xllcorner) / cellsize
            idy = (float(y) - yllcorner) / cellsize
            zgrid[idy, idx] = float(val)

        with open(os.path.join(input_file_dir, input_file_name + ".asc"), "w") as outfile:
            outfile.write("ncols " + str(int(ncols)) + "\n")
            outfile.write("nrows " + str(int(nrows)) + "\n")
            outfile.write("xllcorner " + str(xllcorner - (cellsize * 0.5)) + "\n")
            outfile.write("yllcorner " + str(yllcorner - (cellsize * 0.5)) + "\n")
            outfile.write("cellsize " + str(cellsize) + "\n")
            outfile.write("nodata_value " + str("%.10f" % float(nodataval)) + "\n" + "\n")
            # write grid to outfile
            np.savetxt(outfile, zgrid[::-1], fmt="%.10f", delimiter=" ")
        return

def main():
    tool = DataToolsMatlabTableImport()
    tool.execute(tool.getParameterInfo(), None)

if __name__=='__main__':
    main()