REM cd python_env - not needed because we are changing the directory while activating the conda env
REM start /min .\python_env\gui_program.bat
REM start /min python .\python_env\FAST_run.py
REM A single & sign executes the first command and moves forwards regardless
call conda.bat activate hazus_env & start /min python .\src\FAST_run.py && exit