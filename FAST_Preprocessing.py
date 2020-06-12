# REM cd python_env - not needed because we are changing the directory while activating the conda env
# REM conda activate hazus_env & python .\python_env\FAST_PreProcess_run.py
# call conda.bat activate hazus_env & start /min python .\src\FAST_PreProcess_run.py && exit
from subprocess import call
import os
<<<<<<< HEAD
call('conda.bat activate hazus_env & start /min python ./src/FAST_PreProcess_run.py', shell=True)
=======
call('CALL conda.bat activate hazus_env & start /min python ./src/FAST_PreProcess_run.py', shell=True)
>>>>>>> 0fa523095caa118a9662c3efc82cf4a817bcb19c
if os.path.exists("FAST_Preprocessing.bat"):
    os.remove("FAST_Preprocessing.bat")
else:
    exit(0)