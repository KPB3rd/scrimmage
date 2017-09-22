from mako.template import Template
from mako.runtime import Context
from StringIO import StringIO
import os
import pyDOE
import subprocess
import parse_utility
import numpy as np

import bayesian_optimization

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
        parameters = dict(zip(parameterLabels + ['log_path'], parameterValues + [logPath + 'iter-' + missionIteration]))

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



# postScrimmageAnalysis gets called on a directory of mission files, not a specific mission, returning only 1 value
# numIterationsPerSample not supported yet, TODO
# ranges is a dict of tuple ranges keyed by param name
def optimize(templateFilename, ranges, stateSpaceSampler,
             postScrimmageAnalysis, functionApproximator, logPath
             numInitialSamples=5, numIterationsPerSample=10, numSamples=10):
    xx = {}
    yy = {}

    folder = os.path.dirname(os.path.abspath(templateFilename))
    logName = os.path.splitext(os.path.basename(templateFilename))[0]
    logFile = folder + '/' + logName + '.log'
    logging.basicConfig(filename=logFile, filemode='w', level=logging.DEBUG)

    # Initial exploration parameters
    logging.info('Sampling State Space')
    new_xx = stateSpaceSampler(ranges, numInitialSamples)
    simulationIter = 0

    for loopIter in range(numSamples):
        scrimmageProcesses = []
        newBatchStartingIter = simulationIter
        for params in new_xx:
            # Parse sample into template mission
            logging.info('Generating Mission File')
            missionFile = generateMissionFile(templateFilename, ranges.keys(), params, logPath, simulationIter)

            # run scrimmage
            # missionFile = "/home/kbowers6/Documents/scrimmage/scrimmage/missions/straight.xml"
            logging.info('Executing Mission Files')
            scrimmageProcesses.append(subprocess.Popen(["scrimmage", missionFile]))
            xx[simulationIter] = params
            simulationIter+=1
        
        # Wait for all processes to finish
        for process in scrimmageProcesses:
            process.wait()

        logging.info('Completed Scrimmage Simulation')

        # analysis for all mission results
        logging.info('Parsing Results')
        for iter in range(newBatchStartingIter,simulationIter):
            yy[iter] = postScrimmageAnalysis(logPath+'iter-'+iter)

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
    folder = os.getcwd() + '/scripts/parameter_analysis/'
    test_logPath = "~/swarm-log/analysis/"
    optimize(folder + 'task_assignment.xml', test_ranges, lhsSampler, GetAverageUtility, BayesianOptimizeArgmax, test_logPath)

    print 'Done'
