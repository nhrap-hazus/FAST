REM - OBSOLETE because the gui_program.py is now called from the FAST_run.py so that the check for the tool
REM - is fired before the UI libraries are loaded 
@echo off
conda activate hazus_env && start python .\python_env\gui_program.py && exit