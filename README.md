# Deep-sea Modelling Tools (dsmtools)
#### ArcGIS Python Toolbox version 10 containing a series of tools used for working with ocean data.

The scripts in this toolbox underpin much of the research my team has done into distribution modelling for deep-sea species, fetch calculations, and some other code working with ocean data. These tools can be used for a variety of different purposes. I do warn you that the have relatively little protection against errors, don't catch problems very well and are abysmally commented, but I do have some developing notes in the [wiki](https://github.com/marbiouk/dsmtools/wiki).

The tools are largely maintained by Andy Davies of Bangor University. All tools are released under the MIT License, and no warranty is implied.

The tools are loosely grouped into the following:

* Data Tools
  * Tools for downloading, organising, extracting and converting spatial data.

* Deep-sea SDM Tools
  * Specific tools for working with vertically gridded datasets, at least three (xy, z(depth)) but sometimes four dimensional (xy, z(depth) and t(time)).

* Generic Tools
  * These tools are largely for batch processing of multiple files, and some linking scripts to popular tools such as Maxent.

* Intertidal Tools
  * These tools are focussed on shallow water species and patterns.

* Terrain Tools
  * Tools for calculating terrain parameters from bathymetric data.

#### Instructions
You can run these scripts in standalone mode, through PyCharm project or as an ArcGIS Toolbox with a GUI (add to ArcToolBox, and navigate to your required tool).

#### Funding

The development of this resource was supported by the SponGES project, which has received funding from the European Union’s Horizon 2020 research and innovation programme under grant agreement No 679849.
