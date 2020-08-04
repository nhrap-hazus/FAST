from subprocess import check_output, check_call, call, Popen
import os
import ctypes
import sys
import requests
import pkg_resources
import json
import socket

try:
    with open('./src/config.json') as configFile:
        config = json.load(configFile)
except:
    with open('./config.json') as configFile:
        config = json.load(configFile)

# environmental variables
release = config['release']
proxy = config['proxies']['fema']
hazus_version_url = config[release]['hazusInitUrl']
tool_version_url = config[release]['toolInitUrl']
tool_zipfile_url = config[release]['repoZipfileUrl']
tool_version_local = './src/__init__.py'
conda_env = 'hazus_env'
conda_channel = 'nhrap-dev'
python_package = 'hazpy'

def createProxyEnv():
    newEnv = os.environ.copy()
    newEnv["HTTP_PROXY"] = proxy
    newEnv["HTTPS_PROXY"] = proxy
    return newEnv

def setProxies():
    call('set HTTP_PROXY=' + proxy, shell=True)
    call('set HTTPS_PROXY=' + proxy, shell=True)
    os.environ["HTTP_PROXY"] = proxy
    os.environ["HTTPS_PROXY"] = proxy

def activateEnv():
    try:
        try:
            check_call('conda activate ' + conda_env, shell=True)
        except:
            check_call('activate ' + conda_env, shell=True)
    except:
        print("Can't activate " + conda_env)

def condaInstallHazus():
    messageBox = ctypes.windll.user32.MessageBoxW
    print('Checking for the conda environment '+ conda_env)
    try:
        try:
            check_call('conda activate ' + conda_env, shell=True)
        except:
            print('Creating the conda ' + conda_env)
            try:
                call('echo y | conda create -y -n ' + conda_env, shell=True)
            except:
                setProxies()
                call('echo y | conda create -y -n ' + conda_env, shell=True)
        try:
            print('Installing ' + python_package)
            # TODO replace this message box with a cmd that brings the terminal to the foreground
            # messageBox(0, python_package + " will be installed silently in the minimized Python prompt. Feel free to continue whatever you're doing. We will let you know when it's complete.","Hazus", 0x1000)
            try:
                check_call('conda activate ' + conda_env + ' && echo y | conda install ' + python_package, shell=True)
            except:
                check_call('activate ' + conda_env + ' && echo y | conda install ' + python_package, shell=True)
        except:
            setProxies()
            try:
                check_call('conda activate ' + conda_env + ' && echo y | conda install ' + python_package, shell=True)
            except:
                check_call('activate ' +conda_env+ ' && echo y | conda install ' + python_package, shell=True)
        messageBox(0, python_package + " was successfully installed!","Hazus", 0x1000)
    except:
        messageBox(0, 'Unable to install ' + python_package + '. If this error persists, contact hazus-support@riskmapcds.com for assistance.',"Hazus", 0x1000)

def installHazus():
    messageBox = ctypes.windll.user32.MessageBoxW
    returnValue = messageBox(None, 'The ' + python_package + " Python package is required to run this tool. Would you like to install it now?","Hazus",0x1000 | 0x4)
    if returnValue == 6:
        output = check_output('conda config --show channels')
        channels = list(map(lambda x: x.strip(), str(output).replace('\\r\\n', '').split('-')))[1:]
        if not 'anaconda' in channels:
            call('conda config --add channels anaconda')
            print('anaconda channel added')
        if not 'conda' in channels and not 'forge' in channels:
            call('conda config --add channels conda-forge')
            print('conda-forge channel added')
        if not conda_channel in channels:
            call('conda config --add channels ' + conda_channel)
            print(conda_channel + ' channel added')
        if not 'nsls2forge' in channels:
            call('conda config --add channels nsls2forge')
            print('nsls2forge channel added')
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 1)
        print("Installing " + python_package + " - hold your horses, this could take a few minutes... but it's totally worth it")
        try:
            print('Conda is installing ' + python_package)
            condaInstallHazus()
        except:
            messageBox(0,"An error occured. " + python_package + " was not installed. Please check your network settings and try again.","Hazus", 0x1000)

# def update():
#     messageBox = ctypes.windll.user32.MessageBoxW
#     returnValue = messageBox(None,"A newer version of the Hazus Python package was found. Would you like to install it now?","Hazus",0x1000 | 0x4)
#     if returnValue == 6:
#         print('Conda is installing hazus')
#         condaInstallHazus()

def checkForHazusUpdates():
    messageBox = ctypes.windll.user32.MessageBoxW
    try:
        installedVersion = pkg_resources.get_distribution(python_package).version
        try:
            req = requests.get(hazus_version_url, timeout=0.5)
        except:
            setProxies()
            req = requests.get(hazus_version_url, timeout=0.5)
        newestVersion = parseVersionFromInit(req.text)
        if newestVersion != installedVersion:
            returnValue = messageBox(None,"A newer version of " + python_package + " was found. Would you like to install it now?","Hazus",0x1000 | 0x4)
            if returnValue == 6:
                messageBox(0, 'Hazus updates are installing. We will let you know when its done!',"Hazus", 0x1000)
                condaInstallHazus()
        else:
            print(python_package + ' is up to date')
    except:
        installHazus()

def checkForToolUpdates():
    messageBox = ctypes.windll.user32.MessageBoxW
    try:
        with open(tool_version_local) as init:
            text = init.readlines()
            textBlob = ''.join(text)
            installedVersion = parseVersionFromInit(textBlob)
        try:
            req = requests.get(tool_version_url, timeout=0.5)
        except:
            setProxies()
            req = requests.get(tool_version_url, timeout=0.5)
        newestVersion = parseVersionFromInit(req.text)
        if newestVersion != installedVersion:
            returnValue = messageBox(None,"A newer version of the tool was found. Would you like to install it now?","Hazus",0x1000 | 0x4)
            if returnValue == 6:
                print('updating tool')
                updateTool()
        else:
            print('Tool is up to date')
    except:
        messageBox(0, 'Unable to check for tool updates. If this error persists, contact hazus-support@riskmapcds.com for assistance.',"Hazus", 0x1000)

def updateTool():
    messageBox = ctypes.windll.user32.MessageBoxW
    try:
        from distutils.dir_util import copy_tree
        from shutil import rmtree
        from io import BytesIO
        from zipfile import ZipFile
        try:
            r = requests.get(tool_zipfile_url)
        except:
            setProxies()
            r = requests.get(tool_zipfile_url)
        z = ZipFile(BytesIO(r.content))
        z.extractall()
        fromDirectory  = z.namelist()[0]
        toDirectory = './'
        copy_tree(fromDirectory, toDirectory)
        rmtree(fromDirectory)
        messageBox(0, 'Tools was successfully updated! I hope that was quick enough for you.',"Hazus", 0x1000)
    except:
        messageBox(0, 'The tool update failed. If this error persists, contact hazus-support@riskmapcds.com for assistance.',"Hazus", 0x1000)


def parseVersionFromInit(textBlob):
    reqList = textBlob.split('\n')
    version = list(filter(lambda x: '__version__' in x, reqList))[0]
    replaceList = ['__version__', '=', "'", '"']
    for i in replaceList:
        version = version.replace(i, '')
    version = version.strip()
    return version

def internetConnected():
    # http://zetcode.com/python/socket/
    print('Checking for internet connection')
    socket.setdefaulttimeout(0.5)
    try: 
        try:
            # try with normal connections
            hostname = 'google.com'
            host = socket.gethostbyname(hostname)
        except:
            # adds DHS proxies and retries
            print('retrying with proxies')
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                host = "proxy.apps.dhs.gov" #proxy server IP
                port = 80            #proxy server port
                s.connect((host , port))
                s.sendall(b"GET / HTTP/1.1\r\nHost: www.google.com\r\nAccept: text/html\r\nConnection: close\r\n\r\n")
        print('Found connection')
        return True
    except:
        print('Unable to find connection')
        return False
