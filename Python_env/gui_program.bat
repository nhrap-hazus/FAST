@echo off

cd ..\

SET PATH=%cd%\GDAL;%cd%\python_env;%SystemRoot%\system32;%PATH%;



cd python_env
python gui_program.py && exit