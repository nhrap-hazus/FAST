@echo off

rem cd ..\

rem SET PATH=%cd%\python_env
rem SET PATH=%cd%\GDAL;%PATH%
rem SET GDAL_DATA=%PATH%;%cd%\GDAL\gdal-data
rem SET GDAL_DRIVER_PATH=%PATH%;%cd%\GDAL\gdalplugins

rem cd python_env
conda activate hazus_env && start python .\python_env\gui_process.py && exit