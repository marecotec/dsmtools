import os
import arcpy
from Includes import error_logging
from Includes import downloadremoteurl


class DataToolsBathymetryDownloadGMRT(object):

    def __init__(self):
        self.label = "Bathymetry Download from the GMRT (Global Multi-Resolution Topography) Data set"
        self.description = """
        This script downloads bathymetric data from the Global Multi-Resolution Topography
        data set (GMRT). This resource contains a multi-resolutional compilation of edited
        multibeam sonar data. The script works by downloading data in a predefined moving
        window across a defined area extent, it then saves the data into a directory, and
        then merges the data to create a single file that can be used for topographical
        modelling or variable generation.
        """
        self.canRunInBackground = True
        self.category = "Data Tools"

    def getParameterInfo(self):
        params = []
        arcpy.env.overwriteOutput = True
        # extraction_extent
        extraction_extent = arcpy.Parameter(name="extraction_extent",
                                       displayName="Extraction Extent",
                                       datatype="GPExtent",
                                       parameterType="Required",  # Required|Optional|Derived
                                       direction="Input",  # Input|Output
                                       )
        extraction_extent.value = "-5 -90 0 90"
        params.append(extraction_extent)  # ..and then add it to the list of defined parameters

        # extraction_search_window
        extraction_search_window = arcpy.Parameter(name="extraction_search_window",
                                       displayName="Extraction Window (degrees)",
                                       datatype="GPString",
                                       parameterType="Required",  # Required|Optional|Derived
                                       direction="Input",  # Input|Output
                                       )
        extraction_search_window.value = 2.5
        params.append(extraction_search_window)  # ..and then add it to the list of defined parameters

        # extraction_format
        extraction_format = arcpy.Parameter(name="extraction_format",
                                       displayName="Extraction Format",
                                       datatype="GPString",
                                       parameterType="Required",  # Required|Optional|Derived
                                       direction="Input",  # Input|Output
                                       )
        extraction_format.filter.type = "ValueList"
        extraction_format.filter.list = ["ASCII Grid", "GeoTIFF"]
        extraction_format.value = "GeoTIFF"
        params.append(extraction_format)  # ..and then add it to the list of defined parameters

        # extraction_resolution
        extraction_resolution = arcpy.Parameter(name="extraction_resolution",
                                            displayName="Cell Resolution (m)",
                                            datatype="GPDouble",
                                            parameterType="Required",  # Required|Optional|Derived
                                            direction="Input",  # Input|Output
                                            )
        extraction_resolution.value = 200
        params.append(extraction_resolution)  # ..and then add it to the list of defined parameters

        # extraction_in_fill
        extraction_in_fill = arcpy.Parameter(name="extraction_in_fill",
                                            displayName="Fill in with GEBCO 08?",
                                            datatype="GPBoolean",
                                            parameterType="Required",  # Required|Optional|Derived
                                            direction="Input",  # Input|Output
                                            )
        extraction_in_fill.value = False
        params.append(extraction_in_fill)  # ..and then add it to the list of defined parameters

        # output raster
        output_raster = arcpy.Parameter(name="output_raster",
                                            displayName="Output Raster",
                                            datatype="GPString",
                                            parameterType="Required",  # Required|Optional|Derived
                                            direction="Output",  # Input|Output
                                            )
        output_raster.value = "D:/Temp2/raster1.tif"
        params.append(output_raster)  # ..and then add it to the list of defined parameters

        # temporary directory
        temporary_directory = arcpy.Parameter(name="temporary_directory",
                                            displayName="Temporary Directory",
                                            datatype="DEFolder",
                                            parameterType="Required",  # Required|Optional|Derived
                                            direction="Output",  # Input|Output
                                            )
        temporary_directory.value = "D:/Temp2"
        params.append(temporary_directory)  # ..and then add it to the list of defined parameters

        # logging
        logging = arcpy.Parameter(name="logging",
                                            displayName="Logging enabled",
                                            datatype="GPBoolean",
                                            parameterType="Required",  # Required|Optional|Derived
                                            direction="Input",  # Input|Output
                                            )
        logging.value = True
        params.append(logging)  # ..and then add it to the list of defined parameters

        return params

    def isLicensed(self):
        return True

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        arcpy.env.overwriteOutput = True

        extraction_extent = parameters[0].valueAsText
        extraction_search_window = parameters[1].valueAsText
        extraction_format = parameters[2].valueAsText
        extraction_resolution = parameters[3].valueAsText
        extraction_in_fill = parameters[4].valueAsText
        output_raster = parameters[5].valueAsText
        temporary_directory = parameters[6].valueAsText
        logging = parameters[7].valueAsText

        # Create Logfile Directory
        output_directory = os.path.dirname(output_raster)

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        # Start logging
        if logging:
            error_logging(output_directory, str("Bathymetry Download from the GMRT (Global "
                                               "Multi-Resolution Topography) "
                                               "Data set, running on "))
            error_logging(output_directory, str("--extraction_extent: " + extraction_extent))
            error_logging(output_directory, str("--extraction_search_window: " + str(extraction_search_window)))
            error_logging(output_directory, str("--extraction_format: " + extraction_format))
            error_logging(output_directory, str("--extraction_resolution: " + str(extraction_resolution)))
            error_logging(output_directory, str("--extraction_in_fill: " + str(extraction_in_fill)))
            error_logging(output_directory, str("--output_raster: " + str(output_raster)))
            error_logging(output_directory, str("--temporary_directory: " + str(temporary_directory)))
            error_logging(output_directory, str("-- Note any error codes\n----OK=Data downloaded OK"
                                               "\n----404=No data returned, invalid output format, "
                                               "invalid layer, invalid bounds, invalid resolution."
                                               "\n----413=File requested too large"))

        extraction_extent = extraction_extent.split()

        if extraction_in_fill is True:
            extraction_in_fill = "topo"
        else:
            extraction_in_fill = "topo-mask"

        file_extension = ""

        if extraction_format == "ASCII Grid":
            extraction_format = "esriascii"
            file_extension = ".asc"
        elif extraction_format == "GeoTIFF":
            extraction_format = "geotiff"
            file_extension = ".tif"

        # Build a list of search windows based on the extraction_search_window and the extraction_extent
        # 1 - First calculate the number of windows on the x and y axes
        nWindowsX = float(extraction_extent[2]) - float(extraction_extent[0])
        if nWindowsX < 0:
            nWindowsX *= -1
        nWindowsY = float(extraction_extent[3]) - float(extraction_extent[1])
        if nWindowsY < 0:
            nWindowsY *= -1
        nWindowsX /= float(extraction_search_window)
        nWindowsY /= float(extraction_search_window)

        if logging:
           error_logging(output_directory, str("Mosaicking "
                                               + str(nWindowsX)
                                               + " x blocks, and "
                                               + str(nWindowsY)
                                               + " y blocks. "
                                               + str(nWindowsX * nWindowsY)
                                               + " blocks in total."))

        # 2 - Now build a list of coordinates to test
        Xn = 0
        Yn = 0
        stringURL = []
        xMin = 0
        xMax = 0
        yMin = 0
        yMax = 0

        # Build URL String
        while Xn < nWindowsX + 1:
            if Xn == 0:
                xMin = float(extraction_extent[0])
                yMin = float(extraction_extent[1])
                xMax = float(extraction_extent[0]) + float(extraction_search_window)
                yMax = float(extraction_extent[1]) + float(extraction_search_window)
            else:
                xMin = xMax
                xMax += float(extraction_search_window)
                yMin = yMin
                yMax = yMax

                if xMax >= float(extraction_extent[2]):
                    xMax = float(extraction_extent[2])
                    Xn = nWindowsX + 1

            Xn += 1

            while Yn < nWindowsY + 1:
                if Yn == 0:
                    xMin = xMin
                    xMax = xMax
                    yMin = float(extraction_extent[1])
                    yMax = float(extraction_extent[1]) + float(extraction_search_window)
                    Yn = Yn + 1
                else:
                    xMin = xMin
                    xMax = xMax
                    yMin = yMin + float(extraction_search_window)
                    yMax = yMax + float(extraction_search_window)
                    Yn = Yn + 1

                    if yMax >= float(extraction_extent[3]):
                        yMax = float(extraction_extent[3])
                        Yn = nWindowsY + 1

                stringURL.append("minlongitude="
                                 + str(xMin)
                                 + "&maxlongitude="
                                 + str(xMax)
                                 + "&minlatitude="
                                 + str(yMin)
                                 + "&maxlatitude="
                                 + str(yMax))
            Yn = 0

            # if logging:
            # error_logging(output_directory, str("String URL: " + str(stringURL)))

        nWindows = len(stringURL)
        n = 1
        downloads = 0

        for i in stringURL:
            OutFile = os.path.join(temporary_directory, "depth" + str(n) + str(file_extension))
            if os.path.exists(OutFile):
                downloads = + 1

            if not os.path.exists(OutFile):
                try:
                    stringURL2 = str("http://www.marine-geo.org:80/services/GridServer?"
                                     + str(i)
                                     + "&format="
                                     + str(extraction_format)
                                     + "&mresolution="
                                     + str(extraction_resolution)
                                     + "&layer="
                                     + str(extraction_in_fill))
                    error_logging(output_directory, stringURL2)
                    status_code = downloadremoteurl(stringURL2, OutFile)
                    if logging:
                       error_logging(output_directory, str("Writing: "
                                                           + str(OutFile)
                                                           + " -- Status code is: "
                                                           + str(status_code)))
                    if status_code == "OK":
                        downloads = + 1
                except OSError:
                    pass
            n += 1

        arcpy.env.workspace = temporary_directory

        if downloads == 0:
            if logging:
                error_logging(output_directory, str("No downloaded layers"))
        else:
            GridDirList = []
            limit = 150000
            for path, dirs, files in os.walk(temporary_directory):
                for f in files:
                    size = os.path.getsize(os.path.join(path, f))
                    if size > limit:
                        if os.path.splitext(f)[-1].lower() == file_extension:
                            GridDirList.append(f)
            if logging:
                error_logging(output_directory, str("Mosaicking "
                                                    + str(len(GridDirList))
                                                    + " rasters."))
            arcpy.MosaicToNewRaster_management(input_rasters=GridDirList,
                                               output_location=output_directory,
                                               raster_dataset_name_with_extension=os.path.basename(output_raster),
                                               coordinate_system_for_the_raster="GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',"
                                                                                "SPHEROID['WGS_1984',6378137.0,298.257223563]],"
                                                                                "PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]",
                                               pixel_type="16_BIT_SIGNED",
                                               cellsize="",
                                               number_of_bands="1",
                                               mosaic_method="LAST",
                                               mosaic_colormap_mode="MATCH")

        return


def main():
    tool = DataToolsBathymetryDownloadGMRT()
    tool.execute(tool.getParameterInfo(), None)

if __name__ == '__main__':
    main()

