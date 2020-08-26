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
conda_channel = 'nhrap'
python_package = 'hazus'
httpTimeout = 0.6  # in seconds


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


def condaInstallHazus():
    messageBox = ctypes.windll.user32.MessageBoxW
    print('Checking for the conda environment ' + conda_env)
    try:
        try:
            check_call('CALL conda.bat activate ' + conda_env, shell=True)
        except:
            print('Creating the conda ' + conda_env)
            handleProxy()
            call('echo y | conda create -y -n ' + conda_env, shell=True)

        print('Installing ' + python_package)
        handleProxy()
        try:
            check_call('CALL conda.bat activate ' + conda_env +
                       ' && echo y | conda install ' + python_package, shell=True)
        except:
            call('echo y | conda create -y -n ' + conda_env, shell=True)
            check_call('CALL conda.bat activate ' + conda_env +
                       ' && echo y | conda install ' + python_package, shell=True)

        messageBox(0, python_package +
                   " was successfully installed!", "Hazus", 0x1000)
    except:
        messageBox(0, 'Unable to install ' + python_package +
                   '. If this error persists, contact hazus-support@riskmapcds.com for assistance.', "Hazus", 0x1000)


def installHazus():
    messageBox = ctypes.windll.user32.MessageBoxW
    returnValue = messageBox(None, 'The ' + python_package +
                             " Python package is required to run this tool. Would you like to install it now?", "Hazus", 0x1000 | 0x4)
    if returnValue == 6:
        output = check_output('conda config --show channels')
        channels = list(map(lambda x: x.strip(), str(
            output).replace('\\r\\n', '').split('-')))[1:]
        if not 'anaconda' in channels:
            call('conda config --add channels anaconda')
            print('anaconda channel added')
        if not 'conda' in channels and not 'forge' in channels:
            call('conda config --add channels conda-forge')
            print('conda-forge channel added')
        if not conda_channel in channels:
            call('conda config --add channels ' + conda_channel)
            print(conda_channel + ' channel added')
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 1)
        print("Installing " + python_package +
              " - hold your horses, this could take a few minutes... but it's totally worth it")
        try:
            print('Conda is installing ' + python_package)
            condaInstallHazus()
        except:
            messageBox(0, "An error occured. " + python_package +
                       " was not installed. Please check your network settings and try again.", "Hazus", 0x1000)


def checkForHazusUpdates():
    messageBox = ctypes.windll.user32.MessageBoxW
    try:
        installedVersion = pkg_resources.get_distribution(
            python_package).version

        handleProxy()
        req = requests.get(hazus_version_url, timeout=httpTimeout)

        newestVersion = parseVersionFromInit(req.text)
        if newestVersion != installedVersion:
            returnValue = messageBox(None, "A newer version of " + python_package +
                                     " was found. Would you like to install it now?", "Hazus", 0x1000 | 0x4)
            if returnValue == 6:
                messageBox(
                    0, 'Hazus updates are installing. We will let you know when its done!', "Hazus", 0x1000)
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

        handleProxy()
        req = requests.get(tool_version_url, timeout=httpTimeout)

        newestVersion = parseVersionFromInit(req.text)
        if newestVersion != installedVersion:
            returnValue = messageBox(
                None, "A newer version of the tool was found. Would you like to install it now?", "Hazus", 0x1000 | 0x4)
            if returnValue == 6:
                print('updating tool')
                updateTool()
        else:
            print('Tool is up to date')
    except:
        messageBox(0, 'Unable to check for tool updates. If this error persists, contact hazus-support@riskmapcds.com for assistance.', "Hazus", 0x1000)


def updateTool():
    messageBox = ctypes.windll.user32.MessageBoxW
    try:
        from distutils.dir_util import copy_tree
        from shutil import rmtree
        from io import BytesIO
        from zipfile import ZipFile

        handleProxy()
        r = requests.get(tool_zipfile_url)

        z = ZipFile(BytesIO(r.content))
        z.extractall()
        fromDirectory = z.namelist()[0]
        toDirectory = './'
        copy_tree(fromDirectory, toDirectory)
        rmtree(fromDirectory)
        messageBox(
            0, 'Tools was successfully updated! I hope that was quick enough for you.', "Hazus", 0x1000)
    except:
        messageBox(
            0, 'The tool update failed. If this error persists, contact hazus-support@riskmapcds.com for assistance.', "Hazus", 0x1000)


def parseVersionFromInit(textBlob):
    reqList = textBlob.split('\n')
    version = list(filter(lambda x: '__version__' in x, reqList))[0]
    replaceList = ['__version__', '=', "'", '"']
    for i in replaceList:
        version = version.replace(i, '')
    version = version.strip()
    return version


def internetConnected():
    cnxn = handleProxy()
    if cnxn == -1:
        return False
    else:
        return True


def handleProxy():
    try:
        socket.setdefaulttimeout(httpTimeout)
        port = 80
        try:
            # try without the proxy
            host = 'google.com'    # The remote host
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            s.close()
            return False
        except:
            # try with the fema proxy
            host = "proxy.apps.dhs.gov"  # proxy server IP
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            s.close()
            setProxies()
            return True
    except:
        # 0 indicates there is no internet connection
        # or the method was unable to connect using the hosts and ports
        return -1
