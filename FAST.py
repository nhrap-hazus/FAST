import json
from subprocess import call

# load config
try:
    with open('./src/config.json') as configFile:
        config = json.load(configFile)
        from src.manage import getCondaActivate
except:
    with open('./config.json') as configFile:
        config = json.load(configFile)
        from manage import getCondaActivate

conda_activate = getCondaActivate()
if len(conda_activate) > 0: 
    try:

        # check if the virtual environment has been created
        release = config['release']
        virtual_env = config[release]['virtualEnvironment']
        res = call(f'{conda_activate} {virtual_env}', shell=True)
        if res != 0:
            # create the virtual environment
            try:
                from src.manage import createHazPyEnvironment
            except:
                from manage import createHazPyEnvironment
            createHazPyEnvironment()
        else:
            call(f'{conda_activate} {virtual_env} && start /min python src/update.py', shell=True)
            call(f'{conda_activate} {virtual_env} && start /min python Python_env/gui_program.py', shell=True)             
    except Exception as e:
        import ctypes
        import sys
        messageBox = ctypes.windll.user32.MessageBoxW
        error = str(sys.exc_info()[0])
        messageBox(0, u"Unexpected error: {er} | If this problem persists, contact hazus-support@riskmapcds.com.".format(er=error), u"HazPy", 0x1000)
        raise(e)
else:
    import ctypes
    messageBox = ctypes.windll.user32.MessageBoxW
    messageBox(0, u"Error: Unable to find conda in the system PATH variable. Add conda to your PATH and try again.\n If this problem persists, contact hazus-support@riskmapcds.com.".format(er=error), u"HazPy", 0x1000)