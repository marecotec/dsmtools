# Variable Distance Background 0.01 - Dec 2012
#
# Calculates background files for Maxent based on selected distances around the input
# sample locations. Randomly selects n points within these distances and produces an output
# text file that can be used direct in Maxent, after you append the header to correct for short filenames.
#
# You need to specify several variables:
#
#   -h -- Show help.
#   -i -- Input folder containing shapefiles, or input file name for a single shapefile.
#   -d -- The folder containing your grids in any standard grid format.
#   -o -- Final output path for created files, can be new directory.
#   -u -- Distances for the background selection, can be single or a comma seperated list.
#   -m -- Distance unit, i.e. meters, kilometers.
#   -p -- Number of random points for final background file.
#   -t -- Temporary directory location.
#
# All commands need to be called from the command line:
#   i.e. "PYTHONDIR" "THIS_SCRIPT.py" 
#
# Dependencies:
#   ArcGIS 10
#   ArcPy
#   Spatial Analyst Extension

# Import dependencies
import sys, os, select, string, getopt, time, random
from datetime import datetime
import arcpy
from arcpy import env
from arcpy.sa import *
arcpy.CheckOutExtension("Spatial")

#import variables from commandline
def help_message():
	print("\nCookie cutter version 5.02 - July 2011\n\nUses the cookie cutting approach of Davies & Guinotte (2011) PLoS ONE. \nOptions:\n-i -- Input folder for raw data such as temp (must be in zlayers)\n-a -- Appended filename for raw data (i.e tav000)\n-d -- The location of the depths (zlayers)\n-u -- Standard depths to use, so far: WOA, Steinacher or a list of values between " ", within sep by , i.e. \"1,2,3\"\n-t -- Temporary directory location\n-c -- Clean up temporary files? True or False\n-o -- Output variable file path and name")
	sys.exit(0)

try:
	options, xarguments = getopt.getopt(sys.argv[1:], 'hi:d:o:u:m:p:t:')
except getopt.error:
	print "\nError: You tried to use an unknown option or the argument for an option that requires it was missing."
	help_message()
	sys.exit(0)

for a in options[:]:
	if a[0] == '-h':
		help_message()

for a in options[:]:
	if a[0] == '-i' and a[1] != '':
		print a[0]+' = '+ a[1]
		InData = a[1]
		options.remove(a)
		break
	elif a[0] == '-i' and a[1] == '':
		print '-i expects an argument'
		sys.exit(0)

for a in options[:]:
	if a[0] == '-d' and a[1] != '':
		print a[0]+' = '+ a[1]
		GridDir = a[1]
		options.remove(a)
		break
	elif a[0] == '-d' and a[1] == '':
		print '-d expects an argument'
		sys.exit(0)
		
for a in options[:]:
	if a[0] == '-o' and a[1] != '':
		print a[0]+' = '+ a[1]
		OutputDir = a[1]
		options.remove(a)
		break
	elif a[0] == '-o' and a[1] == '':
		print '-o expects an argument'
		sys.exit(0)

for a in options[:]:
	if a[0] == '-u' and a[1] != '':
		print a[0]+' = '+ a[1]
		Dist1 = a[1]
		Dist = Dist1.split(',')
		options.remove(a)
		break
	elif a[0] == '-u' and a[1] == '':
		print '-u expects an argument'
		sys.exit(0)

for a in options[:]:
	if a[0] == '-m' and a[1] != '':
		print a[0]+' = '+ a[1]
		DistUnit = a[1]
		options.remove(a)
		break
	elif a[0] == '-m' and a[1] == '':
		print '-m expects an argument'
		sys.exit(0)

for a in options[:]:
	if a[0] == '-p' and a[1] != '':
		print a[0]+' = '+ a[1]
		NumPoints = a[1]
		options.remove(a)
		break
	elif a[0] == '-p' and a[1] == '':
		print '-p expects an argument'
		sys.exit(0)
		
for a in options[:]:
	if a[0] == '-t' and a[1] != '':
		print a[0]+' = '+ a[1]
		TempDir = a[1]
		#test if Temporary directory exists, if not create it.
		if not os.path.exists(TempDir):
			os.makedirs(TempDir)
			
		class Tee(object):
			def __init__(self, *files):
				self.files = files
			def write(self, obj):
				for f in self.files:
					f.write(obj)
		
		LogDir = TempDir + os.path.sep + "log.dat"
		counter = 0
		while os.path.exists(LogDir):
			counter = counter + 1
			LogDir = TempDir + os.path.sep + "log" + str(counter) + ".dat"
		LogDirBase = os.path.basename(LogDir)
		f = open(LogDir,'w')
		original = sys.stdout
		sys.stdout = Tee(sys.stdout, f)
		options.remove(a)
		break
	elif a[0] == '-t' and a[1] == '':
		print '-t expects an argument'
		sys.exit(0)

startTime = datetime.now()	
print "\nScript start time: " + str(startTime)
# Get details of 1st raster in the GridDir, we will use this to set the environmental variables
arcpy.env.workspace = GridDir
GridDirList = arcpy.ListRasters("*", "ALL")
GridDirListComp = list()
for g in GridDirList:
	GridDirListComp.append(GridDir + os.path.sep + g)
#set environment variables
arcpy.env.mask = GridDirList[0]
arcpy.env.cellSize = GridDirList[0]
arcpy.env.extent = GridDirList[0]
arcpy.env.overwriteOutput = True

# Now test whether we have multiple shapefile input, or just a single one.
if os.path.isdir(InData):
	print "\nYou specified a directory of files."
	InDataMulti = 1
	InDataList = list()
	for file in os.listdir(InData):    
		if file.endswith(".shp"):
			InDataList.append(file)
	len1 = len(InDataList)
	print "\nThere are " + str(len1) + " files to process.."
else:
	InDataMulti = 0
	print "\nYou specified a single file for processing called: " + InData

print "\nTesting and creating output directories..."
	
#test if Output directory exists, if not create it.
if not os.path.exists(OutputDir):
	os.makedirs(OutputDir)
print "\nOutput dir is " + OutputDir +  ". Temporary dir is " + TempDir + ". There is a log file called " + LogDirBase + " in this directory."
arcpy.env.workspace = TempDir

OperationsNumCount = 1.0
#Do ring buffer on single input
if InDataMulti == 0:
	OperationsNum = len(Dist) * 9

#Do ring buffer on multiple input
if InDataMulti == 1:
	OperationsNum = float(len(Dist) * len(InDataList)) * 9
	
for d in Dist:
	
	if InDataMulti == 1:
		for i in InDataList:
			InData1 = InData + os.path.sep + i
	else:
		InData1 = InData
		
	print "\nThere are " + str(OperationsNum) + " operations to complete.."
	
	Prog = float(OperationsNumCount / OperationsNum)
	sys.stdout = original
	print("\nProgress: [{0:50s}] {1:.1f}%".format('#' * int(Prog * 50), Prog * 100))
	sys.stdout = Tee(sys.stdout, f)
	OperationsNumCount = OperationsNumCount + 1
	
	DistandUnit = str(d) + " " + DistUnit
	print "\nCreating ring buffer at " + str(d) + " " + DistUnit + " for feature " + os.path.splitext(os.path.basename(InData1))[0] + "."
	OutFeature = TempDir + os.path.sep + "ringbuffer_" + os.path.splitext(os.path.basename(InData1))[0] + "_" + str(d) + ".shp"
	arcpy.Buffer_analysis(InData1, OutFeature, DistandUnit, "FULL", "ROUND", "ALL")

#Extract by mask

	Prog = float(OperationsNumCount / OperationsNum)
	sys.stdout = original
	print("\nProgress: [{0:50s}] {1:.1f}%".format('#' * int(Prog * 50), Prog * 100))
	sys.stdout = Tee(sys.stdout, f)
	print "\nExtracting one of the GridDir rasters by the buffer."
	
	outExtractByMask = ExtractByMask(GridDir + os.path.sep + GridDirList[0], OutFeature)
	OperationsNumCount = OperationsNumCount + 1


	Prog = float(OperationsNumCount / OperationsNum)
	sys.stdout = original
	print("\nProgress: [{0:50s}] {1:.1f}%".format('#' * int(Prog * 50), Prog * 100))
	sys.stdout = Tee(sys.stdout, f)
	print "\nConverting raster to points."

	OutFeature1 = TempDir + os.path.sep + "points_" + os.path.splitext(os.path.basename(InData1))[0] + "_" + str(d) + ".shp"
	arcpy.RasterToPoint_conversion(outExtractByMask, OutFeature1, "VALUE")
	OperationsNumCount = OperationsNumCount + 1	

#print out number of points in file
	Prog = float(OperationsNumCount / OperationsNum)
	sys.stdout = original
	print("\nProgress: [{0:50s}] {1:.1f}%".format('#' * int(Prog * 50), Prog * 100))
	sys.stdout = Tee(sys.stdout, f)

	TotalPoints = arcpy.GetCount_management(OutFeature1)
	PropTotalPoints = float(NumPoints) / float(TotalPoints.getOutput(0)) * 100.0
	print "\nThere were " + str(TotalPoints) + " points in the buffered extracted file: " + OutFeature1 + "." + " With the " + str(NumPoints) + " points that you've specified, I'm working on " + str(round(PropTotalPoints,2)) + "% of the total." 
	TotalPointsInt = int(TotalPoints.getOutput(0))
	OperationsNumCount = OperationsNumCount + 1

#select n points
	print "\nSelecting " + str(NumPoints) + " random points. May take a while.."
	Prog = float(OperationsNumCount / OperationsNum)
	sys.stdout = original
	print("\nProgress: [{0:50s}] {1:.1f}%".format('#' * int(Prog * 50), Prog * 100))
	sys.stdout = Tee(sys.stdout, f)
	
	arcpy.AddField_management(OutFeature1, "Sort", "LONG")
	arcpy.AddField_management(OutFeature1, "Choice", "LONG")
	srows = arcpy.UpdateCursor(OutFeature1)	
	
	lrowOperationsNum = TotalPointsInt
	SrowOperationsNum = TotalPointsInt
	SrowOperationsNumCount = 1.0
	lrowOperationsNumCount = 1.0
	print "\n"
	
	for srow in srows:
		SrowProg = float(SrowOperationsNumCount / SrowOperationsNum)
		sys.stdout = original
		print("\rRandomising: [{0:50s}] {1:.1f}%".format('#' * int(SrowProg * 50), SrowProg * 100)),
		sys.stdout = Tee(sys.stdout, f)
		
		wacky = random.randint(0,TotalPointsInt)
		srow.sort = wacky
		srows.updateRow(srow)
		SrowOperationsNumCount = SrowOperationsNumCount + 1
	print "\n"
	lrows = arcpy.UpdateCursor(OutFeature1,"","","", "Sort" + " A")
	count = 0
	for lrow in lrows:
		lrowProg = float(lrowOperationsNumCount / lrowOperationsNum)
		sys.stdout = original
		print("\rSelecting: [{0:50s}] {1:.1f}%".format('#' * int(lrowProg * 50), lrowProg * 100)),
		sys.stdout = Tee(sys.stdout, f)
		lrow.choice = count
		lrows.updateRow(lrow)
		count += 1
		lrowOperationsNumCount = lrowOperationsNumCount + 1
	# release cursors    
	print "\n"
	del srow
	del srows
	del lrow
	del lrows
	
	expression2 = "\"Choice\" < " + str(NumPoints)

	print "\nGenerating random point file."
	Prog = float(OperationsNumCount / OperationsNum)
	sys.stdout = original
	print("\nProgress: [{0:50s}] {1:.1f}%".format('#' * int(Prog * 50), Prog * 100))
	sys.stdout = Tee(sys.stdout, f)

	OutFeature2 = TempDir + os.path.sep + "points_" + os.path.splitext(os.path.basename(InData1))[0] + "_" + str(d) + "_2.shp"
	arcpy.Select_analysis(OutFeature1, OutFeature2, expression2)
	drop_fields = ["Sort", "Choice", "GRID_CODE"]
	arcpy.DeleteField_management(OutFeature2, drop_fields)
	OperationsNumCount = OperationsNumCount + 1

#add xy to points

	print "\nAdding XY locations to the table."
	Prog = float(OperationsNumCount / OperationsNum)
	sys.stdout = original
	print("\nProgress: [{0:50s}] {1:.1f}%".format('#' * int(Prog * 50), Prog * 100))
	sys.stdout = Tee(sys.stdout, f)
	
	arcpy.AddXY_management(OutFeature2)
	OperationsNumCount = OperationsNumCount + 1

#extract multivalues - have to loop through the rasters as Arc.py crashes if try to do all at once..

	Prog = float(OperationsNumCount / OperationsNum)
	sys.stdout = original
	print("\nProgress: [{0:50s}] {1:.1f}%".format('#' * int(Prog * 50), Prog * 100))
	sys.stdout = Tee(sys.stdout, f)
	print "\nExtracting values to points.. May take a while..\n"	
	
	OperationsNumCountExtract = 1.0
	OperationsNumExtract = len(GridDirListComp)
	for g1 in GridDirListComp:
		ProgExtract = float(OperationsNumCountExtract / OperationsNumExtract)
		sys.stdout = original
		print("\rExtract progress: [{0:50s}] {1:.1f}%".format('#' * int(ProgExtract * 50), ProgExtract * 100)),
		sys.stdout = Tee(sys.stdout, f)
		ExtractMultiValuesToPoints(OutFeature2, g1, "NONE")
		OperationsNumCountExtract = OperationsNumCountExtract + 1.0
	
	OperationsNumCount = OperationsNumCount + 1
	print "\nExporting CSV file and header list"
	Prog = float(OperationsNumCount / OperationsNum)
	sys.stdout = original
	print("\nProgress: [{0:50s}] {1:.1f}%".format('#' * int(Prog * 50), Prog * 100))
	sys.stdout = Tee(sys.stdout, f)
	
	outCSV = open(OutputDir + os.path.sep + os.path.splitext(os.path.basename(InData1))[0] + "_" + str(d) + ".csv", "w")
	fieldList = arcpy.ListFields(OutFeature2)
	header=[] #An empty list that will be populated with the field names
	for field in fieldList: #For a field in the list fields,
		header.append(field.name)
	outCSV.write('%s\n' % ','.join(header[2:]))
	
	rows = arcpy.SearchCursor(OutFeature2)
	for row in rows:
		line=[]
		for field in fieldList:
			line.append(str(row.getValue(field.name)))
			outCSV.write('%s\n' % ','.join(line[2:]))
	outCSV.close()
	del row, rows
	outHeaderFile = OutputDir + os.path.sep + "Header.txt"
	outHeader = open(outHeaderFile, "w") # output file
	for g2 in GridDirList:
		g2a = os.path.splitext(os.path.basename(g2))[0]
		outHeader.write(str(g2a)),
		outHeader.write(", "),
	outHeader.close()
	OperationsNumCount = OperationsNumCount + 1
	endTime = datetime.now()	
	totalTime = endTime - startTime
	print "\nScript end time: " + str(endTime) + ". Script took, " + str(totalTime) + " seconds to run."