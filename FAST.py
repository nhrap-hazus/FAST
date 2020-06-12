# REM cd python_env - not needed because we are changing the directory while activating the conda env
# REM start /min .\python_env\gui_program.bat
# REM start /min python .\python_env\FAST_run.py
# REM A single & sign executes the first command and moves forwards regardless
# call conda.bat activate hazus_env & start /min python .\src\FAST_run.py && exit
from subprocess import call
import os
<<<<<<< HEAD
call('conda.bat activate hazus_env & start /min python ./src/FAST_run.py', shell=True)
=======
call('CALL conda.bat activate hazus_env & start /min python ./src/FAST_run.py', shell=True)
>>>>>>> 0fa523095caa118a9662c3efc82cf4a817bcb19c
if os.path.exists("FAST.bat"):
    os.remove("FAST.bat")
else:
    exit(0)