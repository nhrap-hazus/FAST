# REM cd python_env - not needed because we are changing the directory while activating the conda env
# REM start /min .\python_env\gui_program.bat
# REM start /min python .\python_env\FAST_run.py
# REM A single & sign executes the first command and moves forwards regardless
# call conda.bat activate hazus_env & start /min python .\src\FAST_run.py && exit
"""from subprocess import call
import os
call('CALL conda.bat activate hazus_env & start /min python ./src/FAST_run.py', shell=True)
if os.path.exists("FAST.bat"):
    os.remove("FAST.bat")
else:
    exit(0)"""

import json
from subprocess import call

try:
    # load config
    try:
        with open('./src/config.json') as configFile:
            config = json.load(configFile)
    except:
        with open('./config.json') as configFile:
            config = json.load(configFile)

    # check if the virtual environment has been created
    release = config['release']
    virtual_env = config[release]['virtualEnvironment']
    res = call('CALL conda.bat activate ' + virtual_env, shell=True)
    if res == 1:
        # create the virtual environment
        from src.manage import createHazPyEnvironment
        createHazPyEnvironment()
    else:
        call('CALL conda.bat activate '+virtual_env +
             ' && start /min python Python_env/gui_program.py', shell=True)
        call('CALL conda.bat activate '+virtual_env +
             ' && start /min python src/update.py', shell=True)
except:
    import ctypes
    import sys
    messageBox = ctypes.windll.user32.MessageBoxW
    error = sys.exc_info()[0]
    messageBox(0, u"Unexpected error: {er} | If this problem persists, contact hazus-support@riskmapcds.com.".format(er=error), u"HazPy", 0x1000)