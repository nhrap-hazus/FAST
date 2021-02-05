from subprocess import check_output, check_call, call, Popen
import os
import ctypes
import sys
import requests
import pkg_resources
import json
import socket


class Manage:

    def __init__(self):

        try:
            with open('./src/config.json') as configFile:
                self.config = json.load(configFile)
                self.tool_version_local = './src/__init__.py'
                self.env_yaml = './src/environment.yaml'
        except:
            with open('./config.json') as configFile:
                self.config = json.load(configFile)
                self.tool_version_local = './__init__.py'
                self.env_yaml = './environment.yaml'

        # environmental variables
        self.proxy = self.config['proxies']['fema']
        self.release = self.config['release']
        self.hazpy_version_url = self.config[self.release]['hazpyInitUrl']
        self.tool_version_url = self.config[self.release]['toolInitUrl']
        self.tool_zipfile_url = self.config[self.release]['repoZipfileUrl']
        self.python_package = self.config[self.release]['pythonPackage']
        self.virtual_environment = self.config[self.release]['virtualEnvironment']
        self.http_timeout = self.config[self.release]['httpTimeout']  # in seconds

        self.conda_activate, self.conda_deactivate = self.getCondaActivateDeactivate()
        # init message dialog box
        self.messageBox = ctypes.windll.user32.MessageBoxW


    def getCondaActivateDeactivate(self):
        # determine how to call conda and if it's in the system path
        if call('activate', shell=True) == 0:
            return 'activate', 'deactivate'
        if call('conda activate', shell=True) == 0:
            return 'conda activate', 'conda deactivate'
        if call('call conda activate', shell=True) == 0:
            return 'call conda activate', 'call conda deactivate'
        return None, None

    def isCondaInPath(self):
        """
        """
        path = os.environ['PATH']
        condaPaths = [x for x in path.split(';') if 'conda' in x]
        if len(condaPaths) > 0:
            return True
        return False

    def createProxyEnv(self):
        """ Creates a copy of the os environmental variables with updated proxies

        Returns:
            newEnv: os.environ -- a copy of the os.environ that can be used in subprocess calls
        """
        newEnv = os.environ.copy()
        newEnv["HTTP_PROXY"] = self.proxy
        newEnv["HTTPS_PROXY"] = self.proxy
        return newEnv


    def setProxies(self):
        """ Temporarily updates the local environmental variables with updated proxies
        """
        call('set HTTP_PROXY=' + self.proxy, shell=True)
        call('set HTTPS_PROXY=' + self.proxy, shell=True)
        os.environ["HTTP_PROXY"] = self.proxy
        os.environ["HTTPS_PROXY"] = self.proxy


    def condaInstallHazPy(self):
        """ Uses conda to install the latest version of hazpy
        """

        print('Checking for the conda environment {ve}'.format(ve=self.virtual_environment))
        try:
            try:
                check_call('{ca} {vw}'.format(ca=self.conda_activate, ve=self.virtual_environment), shell=True)
            except:
                try:
                    print('Creating the conda virtual environment {ve}'.format(ve=self.virtual_environment))
                    self.handleProxy()
                    call('echo y | conda env create --file {ey}'.format(ey=self.env_yaml), shell=True)
                except:
                    call('{cd} && conda env remove -n {ve}'.format(cd=self.conda_deactivate, ve=self.virtual_environment), shell=True)

            print('Installing {pp}'.format(pp=self.python_package))
            self.handleProxy()
            try:
                check_call('{ca} {ve} && echo y | conda env update -n {ve} --file {ey}'.format(ca=self.conda_activate, ve=self.virtual_environment, ey=self.env_yaml), shell=True)
            except:
                call('echo y | conda env create --file {ey}'.format(ey=self.env_yaml), shell=True)
                check_call('{ca} {ve} && echo y | conda env update -n {ve} --file {ey}'.format(ca=self.conda_activate, ve=self.virtual_environment, ey=self.env_yaml), shell=True)

            self.messageBox(0, u'The ' + self.python_package +
                    u" python package was successfully installed! The update will take effect when the tool is reopened.", u"HazPy", 0x1000 | 0x4)
        except:
            self.messageBox(0, u'Unable to install ' + self.python_package +
                    u'. If this error persists, contact hazus-support@riskmapcds.com for assistance.', u"HazPy", 0x1000 | 0x4)


    def createHazPyEnvironment(self):

        returnValue = self.messageBox(None, u'The ' + self.python_package +
                                u" python package is required to run this tool. Would you like to install it now?", u"HazPy", 0x1000 | 0x4)
        try:
            if returnValue == 6:
                ctypes.windll.user32.ShowWindow(
                    ctypes.windll.kernel32.GetConsoleWindow(), 1)
                print("Installing {pp} - hold your horses, this could take a few minutes... but it's totally worth it".format(pp=self.python_package))
                print('Conda is installing {pp}'.format(pp=self.python_package))
                self.condaInstallHazPy()
        except:
            self.messageBox(0, u"An error occured. " + self.python_package +
                    u" was not installed. Please check your network settings and try again.", u"HazPy", 0x1000 | 0x4)


    def checkForHazPyUpdates(self):
        print('Checking for HazPy updates')
        if self.isCondaInPath(): # only create if conda in PATH
            try:
                installedVersion = pkg_resources.get_distribution(self.python_package).version
                try:
                    self.handleProxy()
                    req = requests.get(self.hazpy_version_url, timeout=self.http_timeout)
                except:
                    self.removeProxy()
                    req = requests.get(self.hazpy_version_url, timeout=self.http_timeout)
                status = req.status_code
                if status == 200:
                    newestVersion = self.parseVersionFromInit(req.text)
                    if newestVersion != installedVersion:
                        returnValue = self.messageBox(None, u"A new version of the " + self.python_package +
                                                u" python package was found. Would you like to install it now?", u"HazPy", 0x1000 | 0x4)
                        if returnValue == 6:
                            self.messageBox(
                                0, u'Updates are installing. We will let you know when its done!', u"HazPy", 0x1000 | 0x4)
                            self.condaInstallHazPy()
                    else:
                        print(self.python_package + ' is up to date')
                else:
                    print('Unable to connect to the url: ' + self.hazpy_version_url)
            except:
                self.createHazPyEnvironment()


    def checkForToolUpdates(self):
        print('Checking for tool updates')
        try:
            with open(self.tool_version_local) as init:
                text = init.readlines()
                textBlob = ''.join(text)
                installedVersion = self.parseVersionFromInit(textBlob)
            try:
                self.handleProxy()
                req = requests.get(self.tool_version_url, timeout=self.http_timeout)
            except:
                self.removeProxy()
                req = requests.get(self.tool_version_url, timeout=self.http_timeout)
            status = req.status_code

            if status == 200:
                newestVersion = self.parseVersionFromInit(req.text)
                if newestVersion != installedVersion:
                    returnValue = self.messageBox(
                        None, u"A new version of the tool was found. Would you like to install it now?", u"HazPy", 0x1000 | 0x4)
                    if returnValue == 6:
                        print('updating tool')
                        self.updateTool()
                else:
                    print('Tool is up to date')
            else:
                print('Unable to connect to url: ' + self.tool_version_url)
        except:
            self.messageBox(0, 'Unable to check for tool updates. If this error persists, contact hazus-support@riskmapcds.com for assistance.', "HazPy", 0x1000 | 0x4)


    def updateTool(self):

        try:
            from distutils.dir_util import copy_tree
            from shutil import rmtree
            from io import BytesIO
            from zipfile import ZipFile

            self.handleProxy()
            r = requests.get(self.tool_zipfile_url)

            z = ZipFile(BytesIO(r.content))
            z.extractall()
            fromDirectory = z.namelist()[0]
            toDirectory = './'
            copy_tree(fromDirectory, toDirectory)
            rmtree(fromDirectory)
            self.messageBox(
                0, u'The tool was successfully updated! I hope that was quick enough for you. The update will take effect when the tool is reopened.', u"HazPy", 0x1000 | 0x4)
        except:
            self.messageBox(
                0, u'The tool update failed. If this error persists, contact hazus-support@riskmapcds.com for assistance.', u"HazPy", 0x1000 | 0x4)


    def parseVersionFromInit(self, textBlob):
        reqList = textBlob.split('\n')
        version = list(filter(lambda x: '__version__' in x, reqList))[0]
        replaceList = ['__version__', '=', "'", '"']
        for i in replaceList:
            version = version.replace(i, '')
        version = version.strip()
        return version


    def internetConnected(self):
        cnxn = self.handleProxy()
        if cnxn == -1:
            return False
        else:
            return True


    def handleProxy(self):
        try:
            socket.setdefaulttimeout(self.http_timeout)
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
                self.setProxies()
                return True
        except:
            # 0 indicates there is no internet connection
            # or the method was unable to connect using the hosts and ports
            return -1

    def removeProxy(self):
        os.environ['HTTP_PROXY'] = ''
        os.environ['HTTPS_PROXY'] = ''

    def startApp(self, app_path, update_path):
        print('Opening the app and checking for updates')

        if self.isCondaInPath():
            if self.conda_activate != None:
                try:
                    # check if the virtual environment has been created
                    # release = self.config['release']
                    # virtual_env = self.config[release]['virtualEnvironment']
                    res = call('{ca} {ve}'.format(ca=self.conda_activate, ve=self.virtual_environment), shell=True)
                    if res != 0:
                        # create the virtual environment
                        self.createHazPyEnvironment()
                    else:
                        call('{ca} {ve} && start /min python {up}'.format(ca=self.conda_activate, ve=self.virtual_environment, up=update_path), shell=True)
                        call('{ca} {ve} && start python {ap}'.format(ca=self.conda_activate, ve=self.virtual_environment, ap=app_path), shell=True)             
                except Exception as e:
                    error = str(sys.exc_info()[0])
                    self.messageBox(0, u"Unexpected error: {er} | If this problem persists, contact hazus-support@riskmapcds.com.".format(er=error), u"HazPy", 0x1000 | 0x4)
                    raise(e)
            else:
                self.messageBox(0, u"Error: Anaconda was found in your system PATH variable, but was unable to activate. Please check to make sure your system PATH variable is pointing to the correct Anaconda root, bin, and scripts directories and try again.\nIf this problem persists, contact hazus-support@riskmapcds.com.", u"HazPy", 0x1000 | 0x4)
        else:
            self.messageBox(0, u"Error: Unable to find conda in the system PATH variable. Add conda to your PATH and try again.\n If this problem persists, contact hazus-support@riskmapcds.com.", u"HazPy", 0x1000 | 0x4)