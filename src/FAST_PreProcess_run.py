try:
    from manage import internetConnected, checkForHazusUpdates, checkForToolUpdates
   
    if internetConnected():
        checkForHazusUpdates()
        checkForToolUpdates()

    from subprocess import check_call
    try:
        check_call('CALL conda activate hazus_env && python .\Python_env\gui_process.py', shell=True)
    except:
        check_call('activate hazus_env && python .\Python_env\gui_process.py', shell=True)
except: 
    import ctypes
    messageBox = ctypes.windll.user32.MessageBoxW
    messageBox(0,"The tool was unable to open. You need internet connection for this tool to update. If this problem persists, contact hazus-support@riskmapcds.com","Hazus", 0x1000)