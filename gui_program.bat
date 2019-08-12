@echo off

cd ..\

SET PATH=%cd%\python_env
SET PATH=%cd%\GDAL;%PATH%
SET GDAL_DATA=%PATH%;%cd%\GDAL\gdal-data
SET GDAL_DRIVER_PATH=%PATH%;%cd%\GDAL\gdalplugins

cd python_env

python gui_program.py && exit