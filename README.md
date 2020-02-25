# FAST - Flood Assessment Structure Tool

The Flood Assessment Structure Tool is used to analyze site-specific flood losses.

## To Use

1. Download zip folder of tool from GitHub, unzip it. Rename the base folder to FAST (from FAST-FAST or FAST-master)

2. Double-click "FAST.bat" (under the FAST folder). if you already have a pre-processed dataset or select "FAST_Preprocessing.bat" if you need to prepare one.

3. FAST will install the Hazus Python Library (HazPy) if not all ready installed. (Please refer to Requirements to see dendencies for HazPy and follow the guidelines)

4. Place your input .csv file in the "UDF" folder under your install. Place your rasters (.tiff) under the "rasters" folder under your install.

4. For details on the two .bat files please go to the Help folder and use the FAST_ReadMe.pdf

## Requirements

The Flood Assessment Structure Tool requires Anaconda as a pre-requisite to setup HazPy. Please follow the link to set up Ananconda - https://fema-ftp-snapshot.s3.amazonaws.com/Hazus/hazpy/build/html/index.html and then download FAST which will automatically set up the HazPy environment. This is a python based tool and uses GDAL libraries to process the GIS data. It does not require ArcGIS or Hazus pre-installed.  

## Documentation

Please refer to the Help folder for the case studies for Minot,ND and NYC,NY

## Contact

Issues can be reported through the repository on Github (https://github.com/nhrap-dev/FAST/issues)

For questions contact us at hazus-support@riskmapcds.com
