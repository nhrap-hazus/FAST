# FAST - Flood Assessment Structure Tool

The Flood Assessment Structure Tool is used to analyze site-specific flood losses.

## To Use

1. Download zip folder of tool from GitHub, unzip it. Rename the base folder to FAST (from FAST-master)

2. Double-click "FAST.bat" (under the FAST folder), if you already have a pre-processed dataset. If not, please select "FAST_Preprocessing.bat" to prepare one.

3. Place your input .csv file in the "UDF" folder under your install. Place your rasters (.tiff) under the "rasters" folder under your install.

4. Please refer to the FAST_ReadMe.pdf under the Help folder for additional details on the .bat files.

## Requirements

The Flood Assessment Structure Tool requires Anaconda to be installed on your computer. Anaconda is a free software that automatically manages all Python packages required to run Hazus open source tools - including the Hazus Python package: https://fema-nhrap.s3.amazonaws.com/Hazus/Python/build/html/index.html

Go to https://www.anaconda.com/distribution/

Download Anaconda for Python 3

Complete the installation. During installation, make sure the following options are checked:

 - [x] Add Anaconda to my PATH environment variable
 - [x] Register Anaconda as my default Python
 - [x] Install Anaconda for local user, rather than all users

## Documentation

Please refer to the Help folder for the case studies for Minot,ND and NYC,NY. 
FAST is based on the Hazus Python Library which is installed/updated automatically when the tool is used.

## Contact

Issues can be reported through the repository on Github (https://github.com/nhrap-dev/FAST/issues)

For questions contact us at hazus-support@riskmapcds.com
