Full ready-to-run demo package available here: https://drive.google.com/file/d/1XMXR9M5yCRFBKvJ0WdbXHVgl3-qLlwYr/view?usp=sharing


Prerequisites:


Packages: OSGEO/GDAL, numpy, utm, tkinter 

Folders:

Rasters
In the directory you run this script, the program will look for a folder titled 'rasters' for the raster selection. Create a folder and place .tif based raster files within this folder and they will appear in the raster selection in the gui.

Lookup Tables
In the directory you run this script, the program will look for a folder titled lookuptables for reference tables in a .csv format for DDF values if they are not found in the input .csv file. Create the folder and load it with the required .csv files IF the folder is not included.


The GUI:


The GUI of the program allows for custom field mapping and checking. If an input .csv is not selected, the fields will be color coded as RED.

If an input .CSV is selected the, the program will search through the input .CSV's field names and cross-check them against what is currently in the corresponding text entry box. It also checks against the default name of the field, according to its field name on the left of the entry box. 

Input:


CSV file with fields corresponding to program requirements.
You will be asked to browse for this file.

Raster file in '.tif' format.
You will be given a selection from the rasters found in the rasters folder in the base directory. You may add or remove raster options as you see fit.

Output:


If the program runs succesfully, you will find the final product in .csv file-format in the same location of the original input .csv file. The name should be the original name of the .csv file with an added _RASTERNAME to the end.



Troubleshooting:

If the input UDF file is open in another program, this program will not run.

If the required fields aren't found using either the given or default field names, the run button will be grayed out and will not work.

If a depth-grid is selected that does not correspond to the coordinates of the input UDF file, the program will fail. 