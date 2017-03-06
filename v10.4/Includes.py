import arcpy
import time
import numpy as np
import csv
import os
import gc

# Reusable includes that are used by several programs
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


def load_depth_string(depth):
    depth_list = []
    if depth == 'WOA05':
        depth_list = ["0", "10", "20", "30", "50", "75", "100", "125", "150", "200", "250", "300", "400", "500", "600",
                  "700", "800", "900", "1000", "1100", "1200", "1300", "1400", "1500", "1750", "2000", "2500",
                  "3000", "3500", "4000", "4500", "5000", "5500"]
    elif depth == 'Steinacher':
        depth_list = ["6", "19", "38", "62", "93", "133", "183", "245", "322", "415", "527", "661", "818", "1001", "1211",
                  "1449", "1717", "2014", "2340", "2693", "3072", "3473", "3894", "4329", "4775"]
    elif depth == 'WOA13v2':
        depth_list = ["0", "5", "10", "15", "20", "25", "30", "35", "40", "45", "50", "55", "60",
                  "65", "70", "75", "80", "85", "90", "95", "100", "125", "150", "175", "200",
                  "225", "250", "275", "300", "325", "350", "375", "400", "425", "450", "475",
                  "500", "550", "600", "650", "700", "750", "800", "850", "900", "950", "1000",
                  "1050", "1100", "1150", "1200", "1250", "1300", "1350", "1400", "1450", "1500",
                  "1550", "1600", "1650", "1700", "1750", "1800", "1850", "1900", "1950", "2000",
                  "2100", "2200", "2300", "2400", "2500", "2600", "2700", "2800", "2900", "3000",
                  "3100", "3200", "3300", "3400", "3500", "3600", "3700", "3800", "3900", "4000",
                  "4100", "4200", "4300", "4400", "4500", "4600", "4700", "4800", "4900", "5000",
                  "5100", "5200", "5300", "5400", "5500"]
    elif depth != ' ':
        b = depth.encode('ascii', 'ignore')
        depth_list = b.split(',')
    return depth_list


# From Josh Werts - http://joshwerts.com/blog/2014/04/01/arcpy-rename-fields/
def rename_fields(table, out_table, new_name_by_old_name):
    """ Renames specified fields in input feature class/table
    :table:                 input table (fc, table, layer, etc)
    :out_table:             output table (fc, table, layer, etc)
    :new_name_by_old_name:  {'old_field_name':'new_field_name',...}
    ->  out_table
    """
    import arcpy
    existing_field_names = [field.name for field in arcpy.ListFields(table)]

    field_mappings = arcpy.FieldMappings()
    field_mappings.addTable(table)

    for old_field_name, new_field_name in new_name_by_old_name.iteritems():
        if old_field_name not in existing_field_names:
            message = "Field: {0} not in {1}".format(old_field_name, table)
            raise Exception(message)

        mapping_index = field_mappings.findFieldMapIndex(old_field_name)
        field_map = field_mappings.fieldMappings[mapping_index]
        output_field = field_map.outputField
        output_field.name = new_field_name
        output_field.aliasName = new_field_name
        field_map.outputField = output_field
        field_mappings.replaceFieldMap(mapping_index, field_map)

    # use merge with single input just to use new field_mappings
    arcpy.Merge_management(table, out_table, field_mappings)
    return out_table


def error_logging(output_directory, log_message):
    import os
    import arcpy
    name = os.path.join(output_directory, "log.txt")
    log_file = open(name, 'a')
    log_file.write("\n")
    log_file.write(log_message)
    arcpy.AddMessage(log_message)
    log_file.close()
    return


def downloadremoteurl(URL, OutFile):
    from urllib2 import urlopen, URLError, HTTPError
    import sys
    try:
        f = urlopen(URL, timeout=300)
        status_code = "OK"
        with open(OutFile, "wb") as local_file:
            while True:
                tmp = f.read(1024)
                if not tmp:
                    status_code = "OK"
                    break
                local_file.write(tmp)
                status_code = "OK"

    # handle errors
    except HTTPError, e:
        status_code = str("HTTP Error: " + str(e.code))
    except URLError, e:
        status_code = str("URL Error: " + str(e.code))
    except MemoryError, e:
        status_code = str("Memory Error (use smaller search window): " + str(e.code))
    except:
        status_code = str("Other error: " + str(sys.exc_info()[0]))

    return status_code


class NetCDFFile(object):
    """-------------------------------------------------------------------------------------
    Class Name: NetCDFFile
    Creation Date: 3/1/2012
    Creator: KSigwart
    Description: This is a helper class that extends the NetCDFFile Properties to be more in
                 line with tools that let users interact with a netCDF file in forms of
                 lat/lon points.
    Inputs:
            netCDF file path:  The location of a netCDF file
    -------------------------------------------------------------------------------------"""

    # Class Parameters
    __sourceLocation = ''
    __variables = list()
    __dimensions = list()
    __latDimension = 'lat'
    __lonDimension = 'lon'
    __latValue = 0
    __lonValue = 0

    def __init__(self, netCDFloc):
        '''
         Defines the Class Properties based off the the NetCDF File Properties inputted
        '''
        ncFileProp = arcpy.NetCDFFileProperties(netCDFloc)
        self.__ncFileProperties = ncFileProp

        self.__sourceLocation = netCDFloc;
        self.__determineDimensions()
        self.__determineVariables()

    def __determineDimensions(self):
        '''
         We only want the dimensions that are not lat and lon.  The lat, lon
         dimensions are already being described by the point that will be mapped
         by the user.
        '''
        dimensions = self.__ncFileProperties.getDimensions();

        # Storing lat and lon dimensions to get the varables associated with both
        dimList = list(dimensions)
        newDimList = list()
        for dim in dimList:
            # if str(dim).lower().startswith('lat'):
            if 'lat' in str(dim).lower():
                self.__latDimension = str(dim)
            # elif str(dim).lower().startswith('lon'):
            elif 'lon' in str(dim).lower():
                self.__lonDimension = str(dim)
            else:
                newDimList.append(dim);

        self.__dimensions = newDimList
        return newDimList

    def __determineVariables(self):
        '''
         We only want variables that have a lat and long dimensions b/c we are
         mapping the variable to a point.  Also, lat and lon are already described
         by the point.
        '''
        latVariables = list(self.__ncFileProperties.getVariablesByDimension(self.__latDimension))
        lonVariables = list(self.__ncFileProperties.getVariablesByDimension(self.__lonDimension))

        variables = list()

        for variable in latVariables:
            if (variable != self.__latDimension and variable != self.__lonDimension) and variable in lonVariables:
                variables.append(variable)

        self.__variables = variables

        return variables

    def __is0to360(self):
        '''
        We need to check to get the Min and Max lon values to determine if
        the dataset goes from 0 - 360 or -180 - 180
        '''

        is0to360 = False

        netCDFProp = self.__ncFileProperties;
        dimLen = netCDFProp.getDimensionSize(self.__lonDimension);

        # Determining the min and max dim.  Looking for values less than 0 and/or greater
        # than 180
        minLon = 360
        maxLon = -180
        start = time.time()

        for index in range(0, dimLen):

            value = netCDFProp.getDimensionValue(self.__lonDimension, index)
            elapsed = (time.time() - start)
            arcpy.AddMessage("Get Dimension Value for index: " + str(index) + "...." + str(elapsed))

            if value < minLon:
                minLon = value;
            if value > maxLon:
                maxLon = value;

        arcpy.AddMessage("Min Lon Value: " + str(minLon))
        arcpy.AddMessage("Max Lon Value: " + str(maxLon))

        # Checking if the min and or max values fall in the right range
        if minLon >= 0 and maxLon > 180:
            is0to360 = True

        arcpy.AddMessage("Is 0 to 360" + str(is0to360))

        return is0to360

    def getDimensions(self):
        return self.__dimensions

    def getVariables(self):
        return self.__variables

    def getLatDimension(self):
        return self.__latDimension

    def getLonDimension(self):
        return self.__lonDimension

    def getLatValue(self):
        return self.__latValue

    def getLonValue(self):
        return self.__lonValue

    def makeNetCDFTable(self, inpnt, variableName, rowDim, outTableView):
        '''
         Method Name:  makeNetCDFTable
         Description:  Creates a netCDF Table view from the first point selected
                       on the map, the variable choosen and the row dimension.  The
                       table contains every variable value at that particular point
                       for each slice of the row dimension.  For example: Every sea
                       temperature (Variable) value at each elevation(Row Dimension)
                       for a particular point(Input Point) in sea.
         Input:
                       inpnt:         The selected Point
                       variableName:  The variable to get each value
                       rowDim:        How to slice up the netCDF file
                       outTableView:  The table being outputed
        '''

        netCDFSource = str(self.__sourceLocation)

        lonVar = self.getLonDimension()
        latVar = self.getLatDimension()

        # Printing out the inputs
        arcpy.AddMessage("Input NetCDF: " + netCDFSource)
        arcpy.AddMessage("Variable Name: " + str(variableName))
        arcpy.AddMessage("Row Dim: " + str(rowDim))
        arcpy.AddMessage("Lat Dim: " + latVar)
        arcpy.AddMessage("Lon Dim: " + lonVar)

        copyStartTime = time.time()

        arcpy.CopyFeatures_management(inpnt, r'in_memory\updateFeat')

        elapsedTime = (time.time() - copyStartTime)
        arcpy.AddMessage("Copy Features " + str(elapsedTime))

        is0to360 = self.__is0to360()

        # Only getting the first point.  Others ignored
        with arcpy.da.SearchCursor('in_memory\updateFeat', ('SHAPE@X', 'SHAPE@Y')) as cursor:
            for row in cursor:

                # Store x,y coordinates of current point
                if is0to360:
                    self.__lonValue = row[0] + 180
                else:
                    self.__lonValue = row[0]

                self.__latValue = row[1]

                arcpy.AddMessage(lonVar + ": " + str(self.__lonValue) + " " + latVar + ": " + str(self.__latValue))

        netCDFStartTime = time.time()
        arcpy.MakeNetCDFTableView_md(netCDFSource, variableName, outTableView, rowDim,
                                     lonVar + " " + str(self.__lonValue) + ";" + latVar + " " + str(self.__latValue),
                                     "BY_VALUE")

        elapsedNetCDFTime = (time.time() - copyStartTime)
        arcpy.AddMessage("Make netCDF Table Time: " + str(elapsedNetCDFTime))

    @staticmethod
    def isNetCDF(netCDFLoc):
        '''
         Method Name:  isNetCDF
         Description:  Checks to see if the file is a netCDF by checking that it ends
                       with '.nc'
         Input:        NetCDF File location
         Output:       True/False if the file is a NetCDF File
        '''
        isNetCDFBool = True

        if not str(netCDFLoc).endswith(".nc"):
            isNetCDFBool = False

        return isNetCDFBool

    @staticmethod
    def getNetCDFPathfromLayer(netCDFLayer):
        '''
         Method Name:  getNetCDFPathfromLayer
         Description:  The data source of a NetCDF Raster layer contains some sort of
                       additional text that represents the raster in memory.
                       We want to strip that piece off so that we only have the
                       exact loaction of the netCDF file
         Input:        NetCDF Raster Layer
         Output:       String: The path to the NetCDF File
        '''
        datasource = str(netCDFLayer.dataSource)
        return datasource.replace('\\' + netCDFLayer.datasetName, '')


def raster_to_xyz(raster, raster_name, output, no_data_value):
    raster_desc = arcpy.Describe(raster)
    raster_x_min = raster_desc.Extent.XMin
    raster_y_min = raster_desc.Extent.YMin
    raster_ch = raster_desc.MeanCellHeight
    raster_cw = raster_desc.MeanCellWidth
    raster_h = raster_desc.Height
    raster_w = raster_desc.Width

    # Adjust start of xmin and ymin to adjust for centroids
    raster_x_min_adj = raster_x_min + (0.5 * raster_cw)
    raster_y_min_adj = raster_y_min + (0.5 * raster_ch)

    ## Build coordinates
    def raster_centroid_x(raster_h, raster_w):
        coordinates_x = raster_x_min_adj + (raster_cw * raster_w)
        return coordinates_x
    raster_coordinates_x = np.fromfunction(raster_centroid_x, (raster_h, raster_w))  # numpy array of X coord

    def raster_centroid_y(raster_h, raster_w):
        coordinates_y = raster_y_min_adj + (raster_ch * raster_h)
        return coordinates_y
    raster_coordinates_y = np.fromfunction(raster_centroid_y, (raster_h, raster_w))  # numpy array of Y coord

    coordinates_y = raster_y_min_adj + (raster_ch * raster_h)
    coordinates_x = raster_x_min_adj + (raster_cw * raster_w)

    # combine arrays of coordinates (although array for Y is before X, dstack produces [X, Y] pairs)
    raster_coordinates = np.dstack((raster_coordinates_y, raster_coordinates_x))
    del raster_coordinates_y, raster_coordinates_x
    gc.collect()

    ##Raster conversion to NumPy Array
    raster_values = arcpy.RasterToNumPyArray(raster)

    # flip array upside down - then lower left corner cells has the same index as cells in coordinates array
    raster_values = np.flipud(raster_values)

    # combine coordinates and value
    raster_values_full = np.dstack((raster_coordinates, raster_values))
    out = csv.writer(open(os.path.join(output, str(raster_name) + ".yxz"), "wb"),
                     delimiter=' ', quoting=csv.QUOTE_NONNUMERIC)
    (height, width, dim) = raster_values_full.shape
    for row in range(0, height):
        for col in range(0, width):
            out.writerow(raster_values_full[row, col])

    del raster_values, raster_values_full, raster_coordinates,
    gc.collect()

    return coordinates_x, coordinates_y
