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
        tool_version_local = './src/__init__.py'
except:
    with open('./config.json') as configFile:
        config = json.load(configFile)
        tool_version_local = './__init__.py'

# environmental variables
proxy = config['proxies']['fema']
release = config['release']
hazpy_version_url = config[release]['hazpyInitUrl']
tool_version_url = config[release]['toolInitUrl']
tool_zipfile_url = config[release]['repoZipfileUrl']
conda_channel = config[release]['condaChannel']
python_package = config[release]['pythonPackage']
python_version = config[release]['pythonVersion']
virtual_environment = config[release]['virtualEnvironment']
http_timeout = config[release]['httpTimeout']  # in seconds

# init message dialog box
messageBox = ctypes.windll.user32.MessageBoxW


def createProxyEnv():
    """ Creates a copy of the os environmental variables with updated proxies
    Returns:
        newEnv: os.environ -- a copy of the os.environ that can be used in subprocess calls
    """
    newEnv = os.environ.copy()
    newEnv["HTTP_PROXY"] = proxy
    newEnv["HTTPS_PROXY"] = proxy
    return newEnv


def setProxies():
    """ Temporarily updates the local environmental variables with updated proxies
    """
    call('set HTTP_PROXY=' + proxy, shell=True)
    call('set HTTPS_PROXY=' + proxy, shell=True)
    os.environ["HTTP_PROXY"] = proxy
    os.environ["HTTPS_PROXY"] = proxy


def condaInstallHazPy():
    """ Uses conda to install the latest version of hazpy
    """

    print('Checking for the conda environment ' + virtual_environment)
    try:
        try:
            check_call('CALL conda.bat activate ' +
                       virtual_environment, shell=True)
        except:
            try:
                print('Creating the conda ' + virtual_environment)
                handleProxy()
                call('echo y | conda create -y -n {ve} python={pv}'.format(ve=virtual_environment, pv=python_version), shell=True)
            except:
                call('conda deactivate && conda env remove -n ' +
                     virtual_environment, shell=True)

        print('Installing ' + python_package)
        handleProxy()
        try:
            check_call('CALL conda.bat activate {ve} && echo y | conda install -c {c} {p} --force-reinstall'.format(ve=virtual_environment, c=conda_channel, p=python_package), shell=True)
        except:
            call('echo y | conda create -y -n {ve} python={pv}'.format(ve=virtual_environment, pv=python_version), shell=True)
            check_call('CALL conda.bat activate {ve} && echo y | conda install -c {c} {p} --force-reinstall'.format(ve=virtual_environment, c=conda_channel, p=python_package), shell=True)

        messageBox(0, u'The ' + python_package +
                   u" python package was successfully installed! The update will take effect when the tool is reopened.", u"HazPy", 0x1000)
    except:
        messageBox(0, u'Unable to install ' + python_package +
                   u'. If this error persists, contact hazus-support@riskmapcds.com for assistance.', u"HazPy", 0x1000)


def createHazPyEnvironment():

    returnValue = messageBox(None, u'The ' + python_package +
                             u" python package is required to run this tool. Would you like to install it now?", u"HazPy", 0x1000 | 0x4)
    try:
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
            if not 'nsls2forge' in channels and not 'forge' in channels:
                call('conda config --add channels nsls2forge')
                print('nsls2forge channel added')
            if not conda_channel in channels:
                call('conda config --add channels ' + conda_channel)
                print(conda_channel + ' channel added')
            ctypes.windll.user32.ShowWindow(
                ctypes.windll.kernel32.GetConsoleWindow(), 1)
            print("Installing " + python_package +
                  " - hold your horses, this could take a few minutes... but it's totally worth it")
            print('Conda is installing ' + python_package)
            condaInstallHazPy()
    except:
        messageBox(0, u"An error occured. " + python_package +
                   u" was not installed. Please check your network settings and try again.", u"HazPy", 0x1000)


def checkForHazPyUpdates():

    try:
        installedVersion = pkg_resources.get_distribution(python_package).version
        handleProxy()
        req = requests.get(hazpy_version_url, timeout=http_timeout)
        status = req.status_code

        if status == 200:
            newestVersion = parseVersionFromInit(req.text)
            if newestVersion != installedVersion:
                returnValue = messageBox(None, u"A new version of the " + python_package +
                                        u" python package was found. Would you like to install it now?", u"HazPy", 0x1000 | 0x4)
                if returnValue == 6:
                    messageBox(
                        0, u'Updates are installing. We will let you know when its done!', u"HazPy", 0x1000)
                    condaInstallHazPy()
            else:
                print(python_package + ' is up to date')
        else:
            print('Unable to connect to the url: ' + hazpy_version_url)
    except:
        createHazPyEnvironment()


def checkForToolUpdates():

    try:
        with open(tool_version_local) as init:
            text = init.readlines()
            textBlob = ''.join(text)
            installedVersion = parseVersionFromInit(textBlob)

        handleProxy()
        req = requests.get(tool_version_url, timeout=http_timeout)
        status = req.status_code

        if status == 200:
            newestVersion = parseVersionFromInit(req.text)
            if newestVersion != installedVersion:
                returnValue = messageBox(
                    None, u"A new version of the tool was found. Would you like to install it now?", u"HazPy", 0x1000 | 0x4)
                if returnValue == 6:
                    print('updating tool')
                    updateTool()
            else:
                print('Tool is up to date')
        else:
            print('Unable to connect to url: ' + tool_version_url)
    except:
        messageBox(0, 'Unable to check for tool updates. If this error persists, contact hazus-support@riskmapcds.com for assistance.', "HazPy", 0x1000)


def updateTool():

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
            0, u'The tool was successfully updated! I hope that was quick enough for you. The update will take effect when the tool is reopened.', u"HazPy", 0x1000)
    except:
        messageBox(
            0, u'The tool update failed. If this error persists, contact hazus-support@riskmapcds.com for assistance.', u"HazPy", 0x1000)


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
        socket.setdefaulttimeout(http_timeout)
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