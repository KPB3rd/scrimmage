from mako.template import Template
from mako.runtime import Context
from StringIO import StringIO
import os
import pyDOE
import subprocess
from parse_utility import GetAverageUtility
import numpy as np

from bayesian_optimization import BayesianOptimizeArgmax

import os.path
import logging
import threading
import time
import os
import signal
import sys
import xml.etree.ElementTree as ET

import queue
from concurrent import futures

def lhsSampler(ranges, numSamples):
    if numSamples == 0:
        return []

    paramSamples = pyDOE.lhs(len(ranges), samples=numSamples)

    # Vectorize to make faster
    normalizedSamples = []
    for iter, sample in enumerate(paramSamples):
        normalizedParams = []
        for range, param in zip(ranges.values(), sample):
            normalizedParam = float(range[1] - range[0]) * param + range[0]
            normalizedParams.append(normalizedParam)
        normalizedSamples.append(normalizedParams)
    return normalizedSamples

def generateMissionFile(templateFullFilename, parameterLabels, parameterValues, logPath, missionIteration):
    print parameterLabels, parameterValues

    if len(parameterLabels) != len(parameterValues):
        raise ValueError('Parameter Labels and Values are mismatched. (Labels=', len(parameterLabels), 'values=', len(parameterValues))
        quit()

    # Load the mission file
    myTemplate = Template(filename=templateFullFilename)

    try:
        # Add log path
        parameters = dict(zip(parameterLabels + ['log_path'], parameterValues + [logPath + 'iter-' + str(missionIteration)]))

        # Parse in the params
        missionData = myTemplate.render(**parameters)

        # Save the file
        folder = os.path.dirname(os.path.abspath(templateFullFilename))
        filename = os.path.splitext(os.path.basename(templateFullFilename))[0]
        fullFilePath = folder + '/' + filename + str(missionIteration) + '.xml'
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
            f.readline() # skip the header

            for iter, line in enumerate(f):
                values = line.strip().split('=')
                print values
                xx.append([float(i) for i in values[0].split(',')])
                yy.append([float(i) for i in values[1].split(',')])
    return xx, yy

def saveSamples(file, xx, yy, header):
    # Write header if first time writing to file (it's a new file)
    if not os.path.isfile(file):
        with open(file, "a") as myfile:
            myfile.write(",".join((str(x) for x in header)))

    # Write the known data points            
    with open(file, "a") as myfile:
        myfile.write(",".join((str(x) for x in xx)) + '=' + str(yy))

# postScrimmageAnalysis gets called on a directory of mission files, not a specific mission, returning only 1 value
# numIterationsPerSample not supported yet, TODO
# ranges is a dict of tuple ranges keyed by param name
def optimize(templateFilename, ranges, stateSpaceSampler,
             postScrimmageAnalysis, functionApproximator, logPath,
             numInitialSamples=1, numIterationsPerSample=1, numSamples=1):
    folder = os.path.dirname(os.path.abspath(templateFilename))
    logName = os.path.splitext(os.path.basename(templateFilename))[0]
    samplesFile = folder + '/' + logName + '_samples.log'
    logFile = folder + '/' + logName + '.log'
    logging.basicConfig(filename=logFile, filemode='w', level=logging.DEBUG)

    xx, yy = parseSamples(samplesFile)
    if len(xx) > 0 and len(yy) > 0:
        logging.info('Samples from file'+samplesFile)
        logging.info('Initial xx: ' + ','.join((str(x) for x in xx)))
        logging.info('Initial yy: ' + ','.join((str(x) for x in yy)))

    # Initial new exploration parameters
    logging.info('Sampling State Space')
    new_xx = stateSpaceSampler(ranges, numInitialSamples)
    simulationIter = len(xx)

    for loopIter in range(numSamples+1):
        newBatchStartingIter = simulationIter
        for params in new_xx:
            # Parse sample into template mission
            logging.info('Generating Mission File with params: ' + ','.join((str(x) for x in zip(ranges.keys(),params))))
            missionFile = generateMissionFile(templateFilename, ranges.keys(), params, logPath, simulationIter)

            xx.append(params)

            # Run the same params multiple times (in order to get a better average result)
            scrimmageProcesses = []
            for paramScrimmageIter in range(numIterationsPerSample):
                # run scrimmage
                logging.info('Executing Mission File')
                scrimmageProcesses.append(subprocess.Popen(["scrimmage", missionFile]))

                # Wait for all processes to finish
                for process in scrimmageProcesses:
                    process.wait()

                logging.info('Completed Scrimmage Simulations')

            simulationIter+=1

        # analysis for all mission results
        logging.info('Parsing Results')
        for iter in range(newBatchStartingIter,simulationIter):
            yy.append(postScrimmageAnalysis(logPath+'iter-'+str(iter)))

            # Append the new params and output
            saveSamples(samplesFile, xx[iter], yy[iter], ranges.keys())

        # Use f_hat to guess some optimal params
        logging.info('Approximating function')
        knownArgmax, expectedValue, nextArgmax = functionApproximator(xx, yy, ranges)
        logging.debug('knownArgmax' + knownArgmax)
        logging.debug('expectedValue' + expectedValue)
        logging.debug('nextArgmax' + nextArgmax)

        new_xx = nextArgmax

    return knownArgmax, expectedValue

if __name__ == "__main__":
    # Demo
    test_ranges = {'w_pk': (0, 2), 'w_pr': (0, 2), 'w_dist': (0, 2), 'w_dist_decay': (700, 1300)}
    # folder = os.getcwd() + '/scripts/parameter_analysis/'
    test_logPath = "/home/kbowers6/swarm-log/analysis/"
    optimize(
        'task_assignment.xml',
        test_ranges, lhsSampler, GetAverageUtility, BayesianOptimizeArgmax,
        test_logPath)

    print 'Done'
