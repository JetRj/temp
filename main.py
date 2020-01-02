import subprocess
import sys
import http.server
import webbrowser
import importlib.util
import threading
import os
import re
import subprocess
from os import system
import csv
import glob
import pickle
import time
import ctypes
import atexit

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import win32file
import win32con

import pickle
import time

import string
import random

portStr = '8000'
injectInterval = 5.0
writeToLogFileInterval = 3.0
integratedProjectHTMLURL = 'http://localhost:' + portStr + '/MainPage.html'
configFileGeneratedCount = 0
webDriverForChrome = None

chromeBinaryPath = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

timestr = time.strftime("%Y%m%d-%H%M%S")
randString = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
fileIdentifier = 'debug+' + timestr + '_' + randString


def openChromeWithoutCORS():
    currentWorkingDir = os.getcwd()
    chromedriver = currentWorkingDir + r"\\chromedriver.exe"
    chromeDownloadDir = currentWorkingDir + "\\FileProcessing"

    chromeOptions = Options()

    prefs = {"download.default_directory": chromeDownloadDir,
             "profile.default_content_setting_values.automatic_downloads": 1}
    chromeOptions.add_experimental_option("prefs", prefs)

    chromeOptions.add_argument("--disable-web-security")
    chromeOptions.add_argument("--open " + integratedProjectHTMLURL)
    chromeOptions.add_argument("--start-maximized")

    chromeOptions.binary_location = chromeBinaryPath

    global webDriverForChrome
    webDriverForChrome = webdriver.Chrome(chromedriver, options=chromeOptions,
                                          service_args=["--verbose", "--log-path="+ fileIdentifier+'chromeDriverLog' +".log"])

    pickleLogFileName = fileIdentifier + '.pcl'
    try:
        with open(pickleLogFileName, "wb") as f:
            pickle.dump(chromeOptions, f)
            pickle.dump(dogs_dict, f)
    except IOError:
        print("file could not be open")
    except ValueError:
        print("could not make list")
    except:
        print("some unknown error")
    else:
        print("successfully done!")

    # Or chrome would be shut down after 5s
    while True:
        time.sleep(10)

def getFullPath(relativePath):
    return os.path.realpath(relativePath)

def startPyListener():

    def triggerExeWithArg1(configFileName, datafileName):
        injectWaitingForResultFlag("true")
        global configFileGeneratedCount

        exePath = os.path.realpath(exeFilename)
        configFileRelativePath = 'FileProcessing\\' + configFileName
        configFilePathAsArg = os.path.realpath(configFileRelativePath)

        datafileRelativePath = 'FileProcessing\\' + datafileName
        datafileFullPath = os.path.realpath(datafileRelativePath)
        addDataAndOutputFilePathAndSaveToConfigFile(configFilePathAsArg, datafileFullPath, os.path.dirname(datafileFullPath))

        subprocess.run([exePath, " 1", configFilePathAsArg])
        configFileGeneratedCount = configFileGeneratedCount + 1

    def addDataAndOutputFilePathAndSaveToConfigFile(configFilePath, datafileFullPath, outputDir):
        datafileLine = ['datafile', datafileFullPath]
        outputfileLine = ['outputfile', outputDir+'\\output_GTWR' + str(configFileGeneratedCount) + '.shp']
        outputcsvfileLine = ['outputcsvfile', outputDir+'\\output_GTWR' + str(configFileGeneratedCount) + '.csv']

        with open(configFilePath, 'a', newline='') as csvFile:
            writer = csv.writer(csvFile)
            writer.writerow([])
            writer.writerow(datafileLine)
            writer.writerow(outputfileLine)
            writer.writerow(outputcsvfileLine)
        csvFile.close()


    ACTIONS = {
        1: "Created",
        2: "Deleted",
        3: "Updated",
        4: "Renamed from something",
        5: "Renamed to something"
    }

    # Thanks to Claudio Grondi for the correct set of numbers
    FILE_LIST_DIRECTORY = 0x0001

    path_to_watch = "FileProcessing\\"
    configFile_name_rep_to_watch = "config((.*)\(.*\))?.csv"
    dataFile_name_rep_to_watch = "datafile((.*)\(.*\))?.csv"

    exeFilename = "FileProcessing\\Armadillo_test1.exe"
    processedFilenames = []

    hDir = win32file.CreateFile(
        path_to_watch,
        FILE_LIST_DIRECTORY,
        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
        None,
        win32con.OPEN_EXISTING,
        win32con.FILE_FLAG_BACKUP_SEMANTICS,
        None
    )

    configFilePath = None
    datafilePath = None
    while 1:
        results = win32file.ReadDirectoryChangesW(
            hDir,
            1024,
            False,
            win32con.FILE_NOTIFY_CHANGE_FILE_NAME,
            None,
            None
        )
        action4 = [t for t in results if t[0]==4]

        for action, filename in action4:
            searchConfigFileResult = re.search(configFile_name_rep_to_watch, filename)
            searchDataFileResult = re.search(dataFile_name_rep_to_watch, filename)

            if searchConfigFileResult and searchConfigFileResult is not None:
                processedFilenames.append(filename)
                configFilePath = filename
                print('config file detected')

            elif searchDataFileResult and searchDataFileResult is not None:
                processedFilenames.append(filename)
                datafilePath = filename
                print('datafile detected')

            else:
                continue
        if (configFilePath is not None) and (datafilePath is not None):
            configFilePath = configFilePath.replace('.crdownload', '')
            datafilePath = datafilePath.replace('.crdownload', '')
            triggerExeWithArg1(configFilePath, datafilePath)
            configFilePath = None
            datafilePath = None
            print('Found Both config and data file')


def removeFilesInFileProcessingWithPattern(pattern):
    for filename in glob.glob("FileProcessing\\" + pattern ):
        os.remove(filename)

def injectConfigFileGeneratedCountToWebSideSuccessCount():
    def printit():
        threading.Timer(injectInterval, printit).start()

        updateWebForSuccessCountCode = "configGeneratedCountFromPython = " + str(configFileGeneratedCount) + ";"
        webDriverForChrome.execute_script(updateWebForSuccessCountCode)
        updateWebForOutputFileNameCode = "updateOutputFilenameForFirstRunAfterRefresh();"
        webDriverForChrome.execute_script(updateWebForOutputFileNameCode)
        print("injected")

    printit()

def injectWaitingForResultFlag(waitingForResultFlag):
    waitingForResultFlagCode = "waitingForResultFlag = " + waitingForResultFlag + ";"
    webDriverForChrome.execute_script(waitingForResultFlagCode)

def runPythonFileServerAndRemoveOldFiles():
    removeFilesInFileProcessingWithPattern("output_*")
    removeFilesInFileProcessingWithPattern("config*")
    removeFilesInFileProcessingWithPattern("datafile*")
    subprocess.call([sys.executable, "-m", "http.server", portStr])

if __name__ == '__main__':

    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    print(os.getcwd())

    # make a copy of original stdout route
    stdout_backup = sys.stdout
    # define the log file that receives your log info
    log_file = open("debug_message.log", "w")
    # redirect print output to log file
    sys.stdout = log_file

    def writeLogFile():
        print('triggered saved file')
        log_file.flush()
        # typically the above line would do. however this is used to ensure that the file is written
        os.fsync(log_file.fileno())

    threading.Timer(writeToLogFileInterval, writeLogFile).start()

    print("All print info will be written to message.log")


    def exit_handler():
        print('My application is ending!')
        log_file.close()
        # restore the output to initial pattern
        sys.stdout = stdout_backup

    atexit.register(exit_handler)

    threadRunPythonFileServer = threading.Thread(target=runPythonFileServerAndRemoveOldFiles)
    threadRunPythonFileServer.start()

    threadOpenChromeWithoutCORS = threading.Thread(target=openChromeWithoutCORS)
    threadOpenChromeWithoutCORS.start()

    threadStartPyListener = threading.Thread(target=startPyListener)
    threadStartPyListener.start()

    threadInject = threading.Thread(target=injectConfigFileGeneratedCountToWebSideSuccessCount)
    threadInject.start()


