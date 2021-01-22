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
        envYaml = './src/environment.yaml'
except:
    with open('./config.json') as configFile:
        config = json.load(configFile)
        tool_version_local = './__init__.py'
        envYaml = './environment.yaml'

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


def getCondaActivateDeactivate():
    # determine how to call conda and if it's in the system path
    if call('activate', shell=True) == 0:
        return 'activate', 'deactivate'
    if call('conda activate', shell=True) == 0:
        return 'conda activate', 'conda deactivate'
    if call('call conda activate', shell=True) == 0:
        return 'call conda activate', 'call conda deactivate'
    return None, None
conda_activate, conda_deactivate = getCondaActivateDeactivate()

# init message dialog box
messageBox = ctypes.windll.user32.MessageBoxW

def isCondaInPath():
    """
    """
    path = os.environ['PATH']
    condaPaths = [x for x in path.split(';') if 'conda' in x]
    if len(condaPaths) > 0:
        return True
    return False

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

    print(f'Checking for the conda environment {virtual_environment}')
    try:
        try:
            check_call(f'{conda_activate} {virtual_environment}', shell=True)
        except:
            try:
                print(f'Creating the conda {virtual_environment}')
                handleProxy()
                call(f'echo y | conda create -y -n {virtual_environment} python={python_version}', shell=True)
            except:
                call(f'{conda_deactivate} && conda env remove -n {virtual_environment}', shell=True)

        print(f'Installing {python_package}')
        handleProxy()
        try:
            check_call(f'{conda_activate} {virtual_environment} && echo y | conda env update -n {virtual_environment} --file {envYaml}', shell=True)
        except:
            call(f'echo y | conda create -y -n {virtual_environment} python={python_version}', shell=True)
            check_call(f'{conda_activate} {virtual_environment} && echo y | conda env update -n {virtual_environment} --file {envYaml}', shell=True)

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
            ctypes.windll.user32.ShowWindow(
                ctypes.windll.kernel32.GetConsoleWindow(), 1)
            print(f"Installing {python_package} - hold your horses, this could take a few minutes... but it's totally worth it")
            print(f'Conda is installing {python_package}')
            condaInstallHazPy()
    except:
        messageBox(0, u"An error occured. " + python_package +
                   u" was not installed. Please check your network settings and try again.", u"HazPy", 0x1000)


def checkForHazPyUpdates():
    try:
        installedVersion = pkg_resources.get_distribution(python_package).version
        try:
            handleProxy()
            req = requests.get(hazpy_version_url, timeout=http_timeout)
        except:
            removeProxy()
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
        try:
            handleProxy()
            req = requests.get(tool_version_url, timeout=http_timeout)
        except:
            removeProxy()
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

def removeProxy():
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''

def startApp(app_path, update_path):
    print('Opening the app and checking for updates')

    if isCondaInPath():
        if conda_activate != None:
            try:
                # check if the virtual environment has been created
                release = config['release']
                virtual_env = config[release]['virtualEnvironment']
                res = call(f'{conda_activate} {virtual_env}', shell=True)
                if res != 0:
                    # create the virtual environment
                    createHazPyEnvironment()
                else:
                    call(f'{conda_activate} {virtual_env} && start /min python {update_path}', shell=True)
                    call(f'{conda_activate} {virtual_env} && start python {app_path}', shell=True)             
            except Exception as e:
                error = str(sys.exc_info()[0])
                messageBox(0, u"Unexpected error: {er} | If this problem persists, contact hazus-support@riskmapcds.com.".format(er=error), u"HazPy", 0x1000)
                raise(e)
        else:
            messageBox(0, u"Error: Anaconda was found in your system PATH variable, but was unable to activate. Please check to make sure your system PATH variable is pointing to the correct Anaconda root, bin, and scripts directories and try again.\nIf this problem persists, contact hazus-support@riskmapcds.com.", u"HazPy", 0x1000)
    else:
        messageBox(0, u"Error: Unable to find conda in the system PATH variable. Add conda to your PATH and try again.\n If this problem persists, contact hazus-support@riskmapcds.com.", u"HazPy", 0x1000)