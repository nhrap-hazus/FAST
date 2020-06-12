try:
    from manage import internetConnected, checkForHazusUpdates, checkForToolUpdates

    if internetConnected():
        checkForHazusUpdates()
        checkForToolUpdates()

    from subprocess import check_call
    try:
<<<<<<< HEAD
        check_call('CALL conda activate hazus_env && python .\Python_env\gui_program.py', shell=True)
=======
        check_call('conda activate hazus_env && python .\Python_env\gui_program.py', shell=True)
>>>>>>> 0fa523095caa118a9662c3efc82cf4a817bcb19c
    except:
        check_call('activate hazus_env && python .\Python_env\gui_program.py', shell=True)
except: 
    import ctypes
    messageBox = ctypes.windll.user32.MessageBoxW
    messageBox(0,"The tool was unable to open. You need internet connection for this tool to update. If this problem persists, contact hazus-support@riskmapcds.com","Hazus", 0x1000)