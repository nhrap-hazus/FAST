from pathlib import Path
from subprocess import call, run

import ctypes
import json
import os
import requests
import socket
import sys


class Manage:
    def __init__(self):

        # Set script path
        parent_path = os.path.dirname(os.path.dirname(__file__))
        os.chdir(parent_path)

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
        # in seconds
        self.http_timeout = self.config[self.release]['httpTimeout']

        self.conda_activate, self.conda_deactivate = self.getCondaActivateDeactivate()
        # init message dialog box
        self.messageBox = ctypes.windll.user32.MessageBoxW

    def getCondaActivateDeactivate(self):
        """Determine how to call conda and if it's in the system path

        Returns:
            [type]: [description]
        """
        if call('activate', shell=True) == 0:
            return 'activate', 'deactivate'
        if call('conda activate', shell=True) == 0:
            return 'conda activate', 'conda deactivate'
        if call('call conda activate', shell=True) == 0:
            return 'call conda activate', 'call conda deactivate'
        return None, None

    def isCondaInPath(self):
        """Check if conda is in path

        Returns:
            [type]: [description]
        """
        path = os.environ['PATH']
        condaPaths = [x for x in path.split(';') if 'conda' in x or 'miniforge' in x]
        if len(condaPaths) > 0:
            return True
        else:
        # TODO: Download miniforge
            return False

    # TODO: See if this is still needed - BC
    def createProxyEnv(self):
        """Creates a copy of the os environmental variables with updated proxies

        Returns:
            newEnv: os.environ -- a copy of the os.environ that can be used in subprocess calls
        """
        newEnv = os.environ.copy()
        newEnv["HTTP_PROXY"] = self.proxy
        newEnv["HTTPS_PROXY"] = self.proxy
        return newEnv

    # TODO: Refactor/update this - BC
    def setProxies(self):
        """Temporarily updates the local environmental variables with updated proxies"""
        call('set HTTP_PROXY=' + self.proxy, shell=True)
        call('set HTTPS_PROXY=' + self.proxy, shell=True)
        os.environ["HTTP_PROXY"] = self.proxy
        os.environ["HTTPS_PROXY"] = self.proxy

    def create_conda_environment(self):
        """Uses conda to install the latest version of tool"""
        print(
            'Checking for the conda environment {ve}'.format(
                ve=self.virtual_environment
            )
        )
        try:
            print(
                'Creating the conda virtual environment {ve}'.format(
                    ve=self.virtual_environment
                )
            )
            self.handleProxy()
            call(
                'echo y | conda env create --file {ey}'.format(ey=self.env_yaml),
                shell=True,
            )
        except:
            # TODO: Remove this? - Will be replaced with self.update_environment() - BC
            call(
                '{cd} && conda env remove -n {ve}'.format(
                    cd=self.conda_deactivate, ve=self.virtual_environment
                ),
                shell=True,
            )
            self.messageBox(
                0,
                u'The Hazus FAST Tool was successfully installed! The update will take effect when the tool is reopened.',
                u"HazPy",
                0x1000 | 0x4,
            )

    def checkForUpdates(self):
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
                # Check if conda is in path
                if self.isCondaInPath():
                    res = run(
                        '{ca} {ve}'.format(
                            ca=self.conda_activate, ve=self.virtual_environment
                        ),
                        shell=True,
                        capture_output=True,
                    )
                    # Create environmnent if it does not exists (res.returncode == 1)
                    if newestVersion != installedVersion and res.returncode == 1:
                        returnValue = self.messageBox(
                            None,
                            u"A newer version of the tool was found. Would you like to install it now?",
                            u"HazPy",
                            0x1000 | 0x4,
                        )
                        if returnValue == 6:
                            print('Updating tool...')
                            self.updateTool()
                            print('Creating the virtual environment...')
                            self.create_conda_environment()
                    if newestVersion == installedVersion and (
                        res.returncode == 1 or b'Could not find' in res.stderr
                    ):
                        print('Creating the virtual environment...')
                        self.create_conda_environment()
                    # Update the environmnent if it already exists (res.returncode == 0)
                    if newestVersion != installedVersion and res.returncode == 0:
                        self.updateTool()
                        self.update_environment()
                else:
                    print('Conda is needed to run this application.')
                    # TODO: Add function to download miniforge
            else:
                print('Unable to connect to url: ' + self.tool_version_url)
        except:
            self.messageBox(
                0,
                'Unable to check for tool updates. If this error persists, contact hazus-support@riskmapcds.com for assistance.',
                "HazPy",
                0x1000 | 0x4,
            )

    def updateTool(self):
        try:
            from distutils.dir_util import copy_tree
            from io import BytesIO
            from shutil import rmtree
            from zipfile import ZipFile

            self.handleProxy()
            r = requests.get(self.tool_zipfile_url)

            z = ZipFile(BytesIO(r.content))
            z.extractall()
            fromDirectory = z.namelist()[0]
            toDirectory = './'
            copy_tree(fromDirectory, toDirectory)
            rmtree(fromDirectory)
        except:
            self.messageBox(
                0,
                u'The tool update failed. If this error persists, contact hazus-support@riskmapcds.com for assistance.',
                u"HazPy",
                0x1000 | 0x4,
            )

    def parseVersionFromInit(self, textBlob):
        """Parse tool version from src/__init__.py

        Args:
            textBlob ([type]): [description]

        Returns:
            [type]: [description]
        """
        reqList = textBlob.split('\n')
        version = list(filter(lambda x: '__version__' in x, reqList))[0]
        replaceList = ['__version__', '=', "'", '"']
        for i in replaceList:
            version = version.replace(i, '')
        version = version.strip()
        return version

    def internetConnected(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        cnxn = self.handleProxy()
        if cnxn == -1:
            return False
        else:
            return True

    def handleProxy(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        try:
            socket.setdefaulttimeout(self.http_timeout)
            port = 80
            try:
                # try without the proxy
                host = 'google.com'  # The remote host
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

    def startApp(self, app_path):
        """Start the application

        Args:
            app_path ([type]): [description]
            update_path ([type]): [description]
        """
        print('Starting the HAZUS FAST application...')
        if self.isCondaInPath():
            try:
                run(
                    '{ca} {ve} && python {ap}'.format(
                        ca=self.conda_activate, ve=self.virtual_environment, ap=app_path
                    ),
                    shell=True,
                )
            except Exception as e:
                print(e)
                error = str(sys.exc_info()[0])
                self.messageBox(
                    0,
                    u"Unexpected error: {er} | If this problem persists, contact hazus-support@riskmapcds.com.".format(
                        er=error
                    ),
                    u"HazPy",
                    0x1000 | 0x4,
                )
        else:
            self.messageBox(
                0,
                u"Error: Unable to find conda in the system PATH variable. Add conda to your PATH and try again.\n If this problem persists, contact hazus-support@riskmapcds.com.",
                u"HazPy",
                0x1000 | 0x4,
            )

    def update_environment(self):
        """Update Environment if version has changed"""
        try:
            res = run('conda deactivate', shell=True, capture_output=True)
            if res.returncode == 0:
                call(
                    'echo y | conda env update --file {ey}'.format(ey=self.env_yaml),
                    shell=True,
                )
        except Exception as e:
            print(e)
