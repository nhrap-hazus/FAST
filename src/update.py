try:
    from manage import internetConnected, checkForHazPyUpdates, checkForToolUpdates
    checkForHazPyUpdates()
    print(3)
    checkForToolUpdates()

except:
    import ctypes
    import sys
    messageBox = ctypes.windll.user32.MessageBoxW
    messageBox(0, "Unexpected error:" + sys.exc_info()[0] + " | If this problem persists, contact hazus-support@riskmapcds.com.", "HazPy", 0x1000)