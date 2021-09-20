from datetime import datetime
import time
import json
import os
import copy


# from multiprocessing import Process
from threading import Thread

class Base:
    """
    Intialize a common module instance
     
    Keyword arguments: \n
    name: str = name of the scenario or instance
    """
    def __init__(self):
        # class variables
        self.dateCreated = datetime.now()
        self.meta = {
            'dateCreated': self.dateCreated
        }
    # class methods
    def info(self):
        print(self.meta)

class Logger():
    """Initalizes a Json logger class

    """
    def __init__(self):
        self.callbackArg = ''
        self.monitorSeconds = 1
        self.monitorActive = False
        self.logFile = ''
    
    def create(self, logDirectory):
        """create log file"""
        if not logDirectory.endswith('/'):
            self.logFile = logDirectory + '/' + 'log.json'
        else:
            self.logFile = logDirectory + 'log.json'
        with open(self.logFile, "w+") as l:
            json.dump({"log": []}, l)

    def destroy(self):
        """delete log file"""   
        os.remove(self.logFile)
    
    def log(self, msg):
        """add message to log"""   
        with open(self.logFile, 'r') as l:
            info = json.loads(l.read())
            info['log'].append({'id': str(len(info['log'])), 'message': msg, 'datetime': str(datetime.now())})
        with open(self.logFile, 'w') as l:
            json.dump(info, l)

    def callback(self):
        """callback function when changes occur"""
        print('assign callback function')
        print('logger.callback = yourFunction')

    def monitor(self):
        """monitors changes"""
        try:
            lastmtime = os.path.getmtime(self.logFile)
        except:
            logDirectory = self.logFile.replace('log.json', '')
            self.create(logDirectory)
            lastmtime = os.path.getmtime(self.logFile)
        while self.monitorActive:
            time.sleep(self.monitorSeconds)
            mtime = os.path.getmtime(self.logFile)
            if mtime != lastmtime:
                self.callback()
                lastmtime = mtime
        self.process.stop()
        # self.process.terminate()

    def monitorStart(self, logFile):
        """starts thread for monitoring changes in the background"""
        self.logFile = logFile
        self.monitorActive = True
        # self.process = Process(target=self.monitor)
        self.process = Thread(target=self.monitor)
        self.process.start()
        # self.process.join()
    
    def monitorStop(self):
        """stops the loop in the thread"""
        self.monitorActive = False
