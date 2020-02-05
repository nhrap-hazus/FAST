REM - OBSOLETE because the gui_process.py is now called from the FAST_PreProcess_run.py so that the check for the tool
REM - is fired before the UI libraries are loaded 
@echo off

rem cd ..\

rem SET PATH=%cd%\python_env
rem SET PATH=%cd%\GDAL;%PATH%
rem SET GDAL_DATA=%PATH%;%cd%\GDAL\gdal-data
rem SET GDAL_DRIVER_PATH=%PATH%;%cd%\GDAL\gdalplugins

rem cd python_env
conda activate hazus_env && start python .\python_env\gui_process.py && exit