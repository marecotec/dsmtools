#!/usr/bin/env python
import sys

sys.dont_write_bytecode = True

from DataToolsBathymetryDownloadGMRT import DataToolsBathymetryDownloadGMRT
from DataToolsMatlabTableImport import DataToolsMatlabTableImport
from DataToolsZonalStatisticsMultipleRasters import DataToolsZonalStatisticsMultipleRasters
from DeepSeaSDMToolsExtractDepths import DeepSeaSDMToolsExtractDepths
from DeepSeaSDMToolsDepthWeightedExtrapolation import DeepSeaSDMToolsDepthWeightedExtrapolation
from DeepSeaSDMToolsExtractWOANetCDF import DeepSeaSDMToolsExtractWOANetCDF
from DeepSeaSDMToolsExtractWOANetCDF_mp import DeepSeaSDMToolsExtractWOANetCDF_mp
from DeepSeaSDMToolsMatchEnvironmentalLayers import DeepSeaSDMToolsMatchEnvironmentalLayers
from GenericToolsBatchConvertMXERaster import GenericToolsBatchConvertMXERaster
from GenericToolsBatchConvertRastersASCIIMXE import GenericToolsBatchConvertRastersASCIIMXE
from GenericToolsOverlappingPolygons import GenericToolsOverlappingPolygons
from GenericToolsBatchProjectRasters import GenericToolsBatchProjectRasters
from GenericToolsBatchReProjectRasters import GenericToolsBatchReProjectRasters
from GenericToolsSplitByAttributes import GenericToolsSplitByAttributes
from IntertidalToolsSpeciesPatternsAroundIslands import IntertidalToolsSpeciesPatternsAroundIslands
from TerrainToolsCalculateNorthnessEastness import TerrainToolsCalculateNorthnessEastness
from TerrainToolsCalculateSlopeVariability import TerrainToolsCalculateSlopeVariability
from TerrainToolsCalculateSTDBathymetry import TerrainToolsCalculateSTDBathymetry
from TerrainToolsCalculateSTDSlope import TerrainToolsCalculateSTDSlope
from TerrainToolsCalculateTRIRiley import TerrainToolsCalculateTRIRiley
from IntertidalToolsSpeciesPatternsGridGeneration import IntertidalToolsSpeciesPatternsGridGeneration


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Deep-sea Modelling Tools"
        self.alias = "dsmtools"
        self.description = """
                The dsmtools ArcGIS Toolbox contains a series of tools used for working with ocean data.
                The scripts here underpin much of the research into global distribution modelling for deep-sea species,
                fetch calculations, and some other code working with data from tropical regions. However, saying that
                most are likely applicable to a variety of different land and seascapes. The tools are largely
                written and maintained by Andy Davies of Bangor University. All tools are released under the MIT
                License.

                The MIT License (MIT) Copyright (c) 2017 Andy Davies

                Permission is hereby granted, free of charge, to any person obtaining a copy of this software
                and associated documentation files (the "Software"), to deal in the Software without restriction,
                including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
                and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
                subject to the following conditions:

                The above copyright notice and this permission notice shall be included in all
                copies or substantial portions of the Software.

                THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
                LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO
                EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
                IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
                USE OR OTHER DEALINGS IN THE SOFTWARE."""
        # List of tool classes associated with this toolbox
        self.tools = [DataToolsBathymetryDownloadGMRT,
                      DataToolsMatlabTableImport,
                      DataToolsZonalStatisticsMultipleRasters,
                      DeepSeaSDMToolsExtractDepths,
                      DeepSeaSDMToolsDepthWeightedExtrapolation,
                      DeepSeaSDMToolsExtractWOANetCDF,
                      DeepSeaSDMToolsExtractWOANetCDF_mp,
                      DeepSeaSDMToolsMatchEnvironmentalLayers,
                      GenericToolsBatchConvertMXERaster,
                      GenericToolsBatchConvertRastersASCIIMXE,
                      GenericToolsOverlappingPolygons,
                      GenericToolsBatchProjectRasters,
                      GenericToolsBatchReProjectRasters,
                      GenericToolsSplitByAttributes,
                      IntertidalToolsSpeciesPatternsAroundIslands,
                      IntertidalToolsSpeciesPatternsGridGeneration,
                      TerrainToolsCalculateNorthnessEastness,
                      TerrainToolsCalculateSlopeVariability,
                      TerrainToolsCalculateSTDBathymetry,
                      TerrainToolsCalculateSTDSlope,
                      TerrainToolsCalculateTRIRiley
                      ]
