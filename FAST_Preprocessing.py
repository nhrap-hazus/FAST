# REM cd python_env - not needed because we are changing the directory while activating the conda env
# REM conda activate hazus_env & python .\python_env\FAST_PreProcess_run.py
# call conda.bat activate hazus_env & start /min python .\src\FAST_PreProcess_run.py && exit
"""from subprocess import call
import os
call('conda.bat activate hazus_env & start /min python ./src/FAST_PreProcess_run.py', shell=True)
if os.path.exists("FAST_Preprocessing.bat"):
    os.remove("FAST_Preprocessing.bat")
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
             ' && start /min python Python_env/gui_process.py', shell=True)
        call('CALL conda.bat activate '+virtual_env +
             ' && start /min python src/update.py', shell=True)
except:
    import ctypes
    import sys
    messageBox = ctypes.windll.user32.MessageBoxW
    error = sys.exc_info()[0]
    messageBox(0, u"Unexpected error: {er} | If this problem persists, contact hazus-support@riskmapcds.com.".format(er=error), u"HazPy", 0x1000)