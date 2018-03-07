from mako.template import Template
from mako.runtime import Context
from StringIO import StringIO
import os
from settings_parser import *
import subprocess
import numpy as np
from collections import OrderedDict
from bayesian_optimization import BayesianOptimizeArgmax
import json
import shutil
import os.path
import logging
import threading
import time
import os
import signal
import time
import argparse
import sys
import xml.etree.ElementTree as ET

import queue
from concurrent import futures

startingSeed = 0

def generateMissionFileWithSeed(templateFullFilename, seed):
    return generateMissionFile(templateFullFilename, ['input_seed'], [seed], None, seed)


def generateMissionFile(templateFullFilename, parameterLabels, parameterValues,
                        logPath, missionIteration):
    print parameterLabels, parameterValues

    if len(parameterLabels) != len(parameterValues):
        raise ValueError(
            'Parameter Labels and Values are mismatched. (Labels=',
            len(parameterLabels), 'values=', len(parameterValues))
        quit()

    # Load the mission file
    myTemplate = Template(filename=templateFullFilename)

    try:
        # Add log path
        if logPath is None:
            parameters = dict(zip(parameterLabels, parameterValues))

        else:
            parameters = dict(zip(parameterLabels + ['log_path'],parameterValues + [logPath + 'iter-' + str(missionIteration)]))

        # Parse in the params
        missionData = myTemplate.render(**parameters)

        # Save the file
        folder = os.path.dirname(os.path.abspath(templateFullFilename))
        filename = os.path.splitext(os.path.basename(templateFullFilename))[0]
        fullFilePath = folder + '/' + filename + '-' + str(missionIteration) + '.xml'
        file = open(fullFilePath, 'w')
        file.write(missionData)
        file.close()

        return fullFilePath
    except NameError:
        print 'Detected incorrect or missing parameters in mission xml.'
        quit()


# Return xx and yy parsed from file
def parseSamples(file):
    xx = []
    yy = []
    if os.path.isfile(file):
        with open(file) as f:
            f.readline()  # skip the header

            for iter, line in enumerate(f):
                values = line.strip().split('=')
                print values
                xx.append([float(i) for i in values[0].split(',')])
                yy.append(float(values[1]))
    return xx, yy


def saveSamples(file, xx, yy, header):
    # Write header if first time writing to file (it's a new file)
    if not os.path.isfile(file):
        with open(file, "a") as myfile:
            myfile.write(",".join((str(x) for x in header)) + '\n')

    # Write the known data points
    with open(file, "a") as myfile:
        myfile.write(",".join((str(x) for x in xx)) + '=' + str(yy) + '\n')


def RunScrimmage(missionFile):
    # Run the same params multiple times (in order to get a better average result)
    scrimmageProcesses = []
    fullFileNames = []
    for paramScrimmageIter in range(numIterationsPerSample):
        seedMissionFile = generateMissionFileWithSeed(missionFile, paramScrimmageIter + startingSeed)
        filename = os.path.basename(seedMissionFile)

        mydir = os.path.dirname(os.path.realpath(__file__))
        shutil.copy2(seedMissionFile, mydir)

        # run scrimmage
        logging.info('Executing Mission File')
        scrimmageProcesses.append(subprocess.Popen(["scrimmage", filename]))
        time.sleep(1) # give this process a head start

        fullFileNames.append(mydir + '/' + filename)
        fullFileNames.append(seedMissionFile)

    # Wait for all processes to finish
    for process in scrimmageProcesses:
        process.wait()

    # Delete all mission files in mission file and local file
    for fullFileName in fullFileNames:
        os.remove(fullFileName)

    logging.info('Completed Scrimmage Simulations')


# postScrimmageAnalysis gets called on a directory of mission files, not a specific mission, returning an output value
# ranges is a dict of tuple ranges keyed by param name
def execute(templateFilePath,
            ranges,
            stateSpaceSampler,
            postScrimmageAnalysis,
            functionApproximator,
            logPath,
            numExploreSamples=0,
            numIterationsPerSample=1,
            numExploitSamples=0,
            noOptimization=False):
    # Initialize Logging
    folder = os.path.dirname(templateFilePath)
    filename = os.path.basename(templateFilePath)
    filenameNoExt = os.path.splitext(filename)[0]
    samplesFile = folder + '/' + filenameNoExt + '_samples.log'
    logging.basicConfig(filename=filenameNoExt + '.log', filemode='w', level=logging.DEBUG)

    # Run a simple batch run if no parameter ranges are found in settings
    if len(ranges) == 0:
        logging.info('No parameter ranges specified. Starting batch runs.')
        noOptimization = True

        RunScrimmage(templateFilePath)
        return -1, -1

    xx, yy = parseSamples(samplesFile)
    if len(xx) > 0 and len(yy) > 0:
        logging.info('Samples from file' + samplesFile)
        logging.info('Initial xx: ' + ','.join((str(x) for x in xx)))
        logging.info('Initial yy: ' + ','.join((str(x) for x in yy)))

    # Initial new exploration parameters
    logging.info('Sampling State Space')
    new_xx = stateSpaceSampler(ranges, numExploreSamples)
    simulationIter = len(xx)

    if noOptimization:
        numExploitSamples = 0  # being explicit- dont exploit because we arent optimizing

    for loopIter in range(numExploitSamples + 1):
        newBatchStartingIter = simulationIter
        for params in new_xx:
            # Parse sample into template mission
            logging.info('Generating Mission File with params: ' + ','.join(
                (str(x) for x in zip(ranges.keys(), params))))
            missionFile = generateMissionFile(templateFilePath, ranges.keys(),
                                              params, logPath, simulationIter)

            RunScrimmage(missionFile)

            xx.append(params)
            simulationIter += 1

        # analysis for all mission results
        for iter in range(newBatchStartingIter, simulationIter):
            if noOptimization:
                yy.append(-1)
            else:
                logging.info('Parsing Results')
                yy.append(postScrimmageAnalysis(logPath + 'iter-' + str(iter)))

            # Append the new params and output
            saveSamples(samplesFile, xx[iter], yy[iter], ranges.keys())

        if not noOptimization:  # yes optimize
            # Use f_hat to guess some optimal params
            logging.info('Approximating function')
            knownArgmax, expectedValue, nextArgmax = functionApproximator(
                xx, yy, ranges)
            logging.debug('knownArgmax: ' + json.dumps(knownArgmax))
            logging.debug('expectedValue: ' + json.dumps(expectedValue))
            logging.debug('nextArgmax: ' + json.dumps(nextArgmax))

            new_xx = [nextArgmax.values()]
        else:
            knownArgmax = -1
            expectedValue = -1
            break  # dont loop again, because we are not optimizing

    logging.info('Analysis complete.')
    return knownArgmax, expectedValue


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--SettingsFile", dest="settingsFile")
    args = parser.parse_args()
    logPath = args.settingsFile

    # Parse the configuration from the settings file
    parser = SettingsParser(logPath)
    missionFile = parser.getMissionFile()
    logPath = parser.getLogPath()
    noOptimizationFlag = parser.getNoOptimization()
    sampler = parser.getStateSpaceSampler()
    postMissionAnalyzer = parser.getPostMissionAnalyzer()
    fApprox = parser.getFunctionApproximator()
    numExploreSamples = parser.getNumExploreSamples()
    numIterationsPerSample = parser.getNumIterationsPerSample()
    numExploitSamples = parser.getNumExploitSamples()
    ranges = parser.getRanges()

    knownArgmax, expectedValue = execute(
        missionFile,
        ranges,
        sampler,
        postMissionAnalyzer,
        fApprox,
        logPath,
        numExploreSamples=numExploreSamples,
        numIterationsPerSample=numIterationsPerSample,
        numExploitSamples=numExploitSamples,
        noOptimization=noOptimizationFlag)

    if not noOptimizationFlag:
        print 'Known Argmax:', knownArgmax
        print 'Expected Value:', expectedValue
