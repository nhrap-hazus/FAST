# Hazus Flood Assessment Structure Tool

The Hazus Flood Assessment Structure Tool (FAST) calculates building-level flood impacts with user-provided building and flood depth data. FAST uses the Hazus Flood model methodology to assign depth damage functions to buildings according to their occupancy type, first floor elevation, foundation type, and number of stories. Flood depth is then extracted at every building and used as a depth damage function parameter to calculate flood losses in dollars. Flood-generated debris is estimated using building area in square feet. For more information about how FAST cacluates flood impacts, please refer to the Hazus Flood Technical Manual: 

Building data must be formatted as a .csv file according to the specifications outlined here: Flood depth data must be formatted as a .tiff raster.

Sample building data for Honolulu, HI are included in the "UDF" folder.

## To Use

**Must have Anaconda Python 3.7 installed. Please read requirements**

1. Download zip folder from GitHub, unzip. Rename unzipped folder from "FAST-master" to "FAST".

2. Place your formatted building data in the "UDF" subfolder. Place your flood depth data in the "Rasters" subfolder.

3. Double-click "FAST.py"
*To review the default assignment of damage functions prior to running FAST, double-click "FAST-Preprocessing.py" and supply your building data. Damage function parameters can be edited using the DDF spreadsheets in the "Lookuptables" subfolder.*

4. Click "Browse to Inventory Input (.csv)" to select your formatted building data.

5. Select "Riverine", "CoastalA", or "CoastalV" from the "Coastal Flooding Attribute" window according to your analysis requirements. Select a flood depth dataset from the "Depth Grid" window.

6. Click "Execute"

## Requirements

The Flood Assessment Structure Tool requires Anaconda to be installed on your computer. Anaconda is a free software that automatically manages all Python packages required to run Hazus open source tools - including the Hazus Python package: https://fema-nhrap.s3.amazonaws.com/Hazus/Python/build/html/index.html

1. Go to https://www.anaconda.com/distribution/

2. Download Anaconda for Python 3

3. Complete the installation. During installation, make sure the following options are checked:

   - [x] **Add Anaconda to my PATH environment variable**
   - [x] Register Anaconda as my default Python
   - [x] Install Anaconda for local user, rather than all users

## Documentation

Please refer to the Help folder for the case studies for Minot,ND and NYC,NY. 
FAST is based on the Hazus Python Library which is installed/updated automatically when the tool is used.

To run the .py extension files on double-click

1. Right Click the script file and go to properties. 
2. Select the option 'Opens with:' in General tab, and select the python from list, if its not available then browse to the installation directory of python and select the python.exe from there.
3. Now when you double click on the file it will run automatically.

## Contact

Issues can be reported through the repository on Github (https://github.com/nhrap-dev/FAST/issues)

For questions contact us at hazus-support@riskmapcds.com
