#!/usr/bin/env python
import arcpy, numpy, os
from math import radians, sin, cos


class IntertidalToolsRadiatingLines(object):
    """This class has the methods you need to define
       to use your code as an ArcGIS Python Tool."""

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Radiating lines from a single defined point"
        self.description = """This script builds radiating lines from a single point, it does little else (i.e. it
        					doesn't clip the radiating lines by a coastline). It is unlikely that you will ever use
        					this tool. The Calculate fetch distances from points tool is far more feature rich."""
        self.canRunInBackground = False
        self.category = "Intertidal Tools"  # Use your own category here, or an existing one.

    def getParameterInfo(self):
        """Define parameter definitions
           Refer to http://resources.arcgis.com/en/help/main/10.2/index.html#/Defining_parameters_in_a_Python_toolbox/001500000028000000/
           For datatype see http://resources.arcgis.com/en/help/main/10.2/index.html#/Defining_parameter_data_types_in_a_Python_toolbox/001500000035000000/
        """

        # You can define a tool to have no parameters
        params = []

distance = float(int(arcpy.GetParameter(2)))
angle = int(arcpy.GetParameter(3))
OutputFeature = arcpy.GetParameterAsText(4)

		# Point X
        angle = arcpy.Parameter(name="origin_x",
                                displayName="X Coordinate",
                                datatype="GPDouble",
                                parameterType="Required",  # Required|Optional|Derived
                                direction="Input",  # Input|Output
                                )


		# Point Y
        angle = arcpy.Parameter(name="origin_y",
                                displayName="Y Coordinate",
                                datatype="GPDouble",
                                parameterType="Required",  # Required|Optional|Derived
                                direction="Input",  # Input|Output
                                )

        # Input Island Points
        input_points = arcpy.Parameter(name="input_points",
                                       displayName="Input Feature Class",
                                       datatype="DEFeatureClass",
                                       parameterType="Required",  # Required|Optional|Derived
                                       direction="Input",  # Input|Output
                                       )
        # You can set filters here for example input_fc.filter.list = ["Polygon"]
        # You can set a default if you want -- this makes debugging a little easier.
        input_points.value = "E:/2016/Corals/Coastline_Independent/Export_Output_3.shp"
        params.append(input_points)  # ..and then add it to the list of defined parameters

        # Distance to draw polygon
        distance = arcpy.Parameter(name="distance",
                                   displayName="Distance to capture coastline",
                                   datatype="GPDouble",
                                   parameterType="Required",  # Required|Optional|Derived
                                   direction="Input",  # Input|Output
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
                                parameterType="Required",  # Required|Optional|Derived
                                direction="Input",  # Input|Output
                                )
        # You could set a list of acceptable values here for example
        # number.filter.type = "ValueList"
        # number.filter.list = [1,2,3,123]
        # You can set a default value here.
        angle.value = 10
        params.append(angle)

        # Output feature class
        output_points = arcpy.Parameter(name="output_points",
                                        displayName="Output feature class",
                                        datatype="DEFeatureClass",
                                        parameterType="Derived",  # Required|Optional|Derived
                                        direction="Output",  # Input|Output
                                        )
        # This is a derived parameter; it depends on the input feature class parameter.
        # You usually use this to define output for using the tool in ESRI models.
        output_points.parameterDependencies = [input_points.name]
        # Cloning tells arcpy you want the schema of this output fc to be the same as input_fc
        # See http://desktop.arcgis.com/en/desktop/latest/analyze/creating-tools/updating-schema-in-a-python-toolbox.htm#ESRI_SECTION1_0F3D82FC6ACA421E97AC6D23D95AF19D
        # output_points.schema.clone = True
        params.append(output_points)

        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of your tool."""

        messages.addMessage("Orientation of species distributions")
        for param in parameters:
            messages.addMessage("Parameter: %s = %s" % (param.name, param.valueAsText))

        # See http://resources.arcgis.com/en/help/main/10.2/index.html#//018z00000063000000
        input_points = parameters[0].valueAsText
        distance = parameters[1].value
        angle = parameters[2].value
        output_points = parameters[3].valueAsText

        # 0 Describe files to set coordinate systems
        desc_input = arcpy.Describe(input_points)
        coord_system = desc_input.spatialReference
        arcpy.env.outputCoordinateSystem = coord_system

        # 1 Generate an Island Polygon from our input points, intersect it with a fishnet and then keep only
        # polygons within the Island polygon.


        return


# That's all!



origin_x = float(arcpy.GetParameter(0))
origin_y = float(arcpy.GetParameter(1))
distance = float(int(arcpy.GetParameter(2)))
angle = int(arcpy.GetParameter(3))
OutputFeature = arcpy.GetParameterAsText(4)

# pathOut = "E:/2014/Kurr/RadiatingLines/"
# output = "cb2.shp"
arcpy.CreateFeatureclass_management(os.path.dirname(OutputFeature), os.path.basename(OutputFeature), "Polygon")

# create list of bearings
angles = range(0, 360, angle)

for ang in angles:
    # calculate offsets with light trig
    angle = float(int(ang))
    (disp_x, disp_y) = (distance * sin(radians(angle)), distance * cos(radians(angle)))
    (end_x, end_y) = (origin_x + disp_x, origin_y + disp_y)
    (end2_x, end2_y) = (origin_x + disp_x, origin_y + disp_y)

    cur = arcpy.InsertCursor(OutputFeature)
    lineArray = arcpy.Array()

    # start point
    start = arcpy.Point()
    (start.ID, start.X, start.Y) = (1, origin_x, origin_y)
    lineArray.add(start)

    # end point
    end = arcpy.Point()
    (end.ID, end.X, end.Y) = (2, end_x, end_y)
    lineArray.add(end)

    # write our fancy feature to the shapefile
    feat = cur.newRow()
    feat.shape = lineArray
    cur.insertRow(feat)

    # yes, this shouldn't really be necessary...
    lineArray.removeAll()
    del cur
