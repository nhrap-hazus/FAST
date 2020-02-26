# FAST - Flood Assessment Structure Tool

The Flood Assessment Structure Tool is used to analyze site-specific flood losses.

## To Use

1. Download zip folder of tool from GitHub, unzip it. Rename the base folder to FAST (from FAST-FAST or FAST-master)

2. Double-click "FAST.bat" (under the FAST folder). if you already have a pre-processed dataset or select "FAST_Preprocessing.bat" if you need to prepare one.

3. If you don't have the Hazus Python Library installed, follow the prompt to install, then double-click "FAST.bat" again

4. Place your input .csv file in the "UDF" folder under your install. Place your rasters (.tiff) under the "rasters" folder under your install.

4. For details on the two .bat files please go to the Help folder and use the FAST_ReadMe.pdf

## Requirements

The Flood Assessment Structure Tool requires Anaconda to be installed on your computer. Anaconda is a free software that automatically manages all Python packages required to run Hazus open source tools - including the Hazus Python package: https://fema-nhrap.s3.amazonaws.com/Hazus/Python/build/html/index.html

Go to https://www.anaconda.com/distribution/

Download Anaconda for Python 3

Complete the installation. During installation, make sure the following options are checked:

 Add Anaconda to my PATH environment variable
 Register Anaconda as my default Python
 Install Anaconda for local user, rather than all users

## Documentation

Please refer to the Help folder for the case studies for Minot,ND and NYC,NY

## Contact

Issues can be reported through the repository on Github (https://github.com/nhrap-dev/FAST/issues)

For questions contact us at hazus-support@riskmapcds.com
