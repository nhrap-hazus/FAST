from subprocess import check_output, check_call, call, Popen
import os
import ctypes
import sys
import requests
import pkg_resources
import json
with open('./Python_env/config.json') as configFile:
    config = json.load(configFile)

release = config['release']

def setProxyEnv():
    newEnv = os.environ.copy()
    newEnv["HTTP_PROXY"] = config.proxies.fema
    newEnv["HTTPS_PROXY"] = config.proxies.fema
    return newEnv

def condaInstallHazus():
    messageBox = ctypes.windll.user32.MessageBoxW
    try:
        print('Checking for the conda environment hazus_env')
        # check_call('conda activate hazus_env', shell=True)
        check_call('conda activate hazus_env', shell=True)
    except:
        print('Creating the conda hazus_env')
        call('set HTTP_PROXY=' + config.proxies.fema, shell=True)
        call('set HTTPS_PROXY=' + config.proxies.fema, shell=True)
        call('echo y | conda create -y -n hazus_env', shell=True)
    try:
        print('Installing the hazus python package')
        check_call('conda activate hazus_env && echo y | conda install -c nhrap hazus', shell=True)
        messageBox(None,"The Hazus Python package was successfully installed. Please reopen the utility.","Hazus", 0)
    except:
        print('Adding proxies and retrying...')
        proxyEnv = setProxyEnv()
        check_call('conda activate hazus_env && echo y | conda install -c nhrap hazus', shell=True, env=proxyEnv)
        messageBox(None,"The Hazus Python package was successfully installed. Please reopen the utility.","Hazus", 0)

def installHazus():
    messageBox = ctypes.windll.user32.MessageBoxW
    returnValue = messageBox(None,"The Hazus Python package is required to run this tool. Would you like to install it now?","Hazus",0x40 | 0x4)
    if returnValue == 6:
        import os
        output = check_output('conda config --show channels')
        channels = list(map(lambda x: x.strip(), str(output).replace('\\r\\n', '').split('-')))[1:]
        if not 'anaconda' in channels:
            call('conda config --add channels anaconda')
            print('anaconda channel added')
        if not 'conda' in channels and not 'forge' in channels:
            call('conda config --add channels conda-forge')
            print('conda-forge channel added')
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 1)
        print('Installing the Hazus Python package, this could take a couple minutes...')
        try:
            print('Conda is installing hazus')
            condaInstallHazus()
        except:
            messageBox(None,"An error occured. The Hazus Python package was not installed. Please check your network settings and try again.","Hazus", 0)

def update():
    messageBox = ctypes.windll.user32.MessageBoxW
    returnValue = messageBox(None,"A newer version of the Hazus Python package was found. Would you like to install it now?","Hazus",0x40 | 0x4)
    if returnValue == 6:
        print('Conda is installing hazus')
        condaInstallHazus()

def checkForHazusUpdates():
    try:
        installedVersion = pkg_resources.get_distribution('hazus').version
        try:
            req = requests.get(config[release]['hazusInitUrl'], timeout=0.3)
        except:
            os.environ["HTTP_PROXY"] = config.proxies.fema
            os.environ["HTTPS_PROXY"] = config.proxies.fema
            req = requests.get(config[release]['hazusInitUrl'], timeout=0.3)
        newestVersion = parseVersionFromInit(req.text)
        if newestVersion != installedVersion:
            messageBox = ctypes.windll.user32.MessageBoxW
            returnValue = messageBox(None,"A newer version of the Hazus Python package was found. Would you like to install it now?","Hazus",0x40 | 0x4)
            if returnValue == 6:
                print('updating hazus')
                update()
        else:
            print('Hazus is up to date')
    except:
        installHazus()

def checkForToolUpdates():
    try:
        with open('__init__.py') as init:
            text = init.readlines()
            textBlob = ''.join(text)
            installedVersion = parseVersionFromInit(textBlob)
        try:
            req = requests.get(config[release]['toolInitUrl'], timeout=0.3)
        except:
            os.environ["HTTP_PROXY"] = config.proxies.fema
            os.environ["HTTPS_PROXY"] = config.proxies.fema
            req = requests.get(config[release]['toolInitUrl'], timeout=0.3)
        newestVersion = parseVersionFromInit(req.text)
        if newestVersion != installedVersion:
            messageBox = ctypes.windll.user32.MessageBoxW
            returnValue = messageBox(None,"A newer version of the tool was found. Would you like to install it now?","Hazus",0x40 | 0x4)
            if returnValue == 6:
                print('updating tool')
                updateTool()
        else:
            print('Tool is up to date')
    except:
        print('Something broke')

def updateTool():
    from distutils.dir_util import copy_tree
    from shutil import rmtree
    from io import BytesIO
    from zipfile import ZipFile
    r = requests.get(config[release]['repoZipfileUrl'])
    z = ZipFile(BytesIO(r.content))
    os.getcwd()
    z.extractall()
    fromDirectory  = z.namelist()[0]
    toDirectory = './'
    copy_tree(fromDirectory, toDirectory)
    rmtree(fromDirectory)


def parseVersionFromInit(textBlob):
    reqList = textBlob.split('\n')
    version = list(filter(lambda x: '__version__' in x, reqList))[0]
    replaceList = ['__version__', '=', "'", '"']
    for i in replaceList:
        version = version.replace(i, '')
    version = version.strip()
    return version

def internetConnected():
    print('Checking for internet connection')
    try: 
        try:
            requests.get('http://google.com', timeout=0.3)
        except:
            os.environ["HTTP_PROXY"] = config.proxies.fema
            os.environ["HTTPS_PROXY"] = config.proxies.fema
            requests.get('http://google.com', timeout=0.3)
        return True
    except:
        return False
