from mako.template import Template
from mako.runtime import Context
from StringIO import StringIO
import os
import pyDOE
import subprocess
import parse_utility
import numpy as np

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
             numSamples=5, numIterationsPerSample=10):
    xx = {}
    yy = {}

    # Initial exploration parameters
    new_xx = stateSpaceSampler(ranges, numSamples)
    simulationIter = 0
    while True:
        scrimmageProcesses = []
        newBatchStartingIter = simulationIter
        for params in new_xx:
            # Parse sample into template mission
            missionFile = generateMissionFile(templateFilename, ranges.keys(), params, logPath, simulationIter)

            # run scrimmage
            # missionFile = "/home/kbowers6/Documents/scrimmage/scrimmage/missions/straight.xml"
            scrimmageProcesses.append(subprocess.Popen(["scrimmage", missionFile]))
            xx[simulationIter] = params
            simulationIter+=1
        
        # Wait for all processes to finish
        for process in scrimmageProcesses:
            process.wait()

        # analysis for all mission results
        for iter in range(newBatchStartingIter,simulationIter):
            yy[iter] = postScrimmageAnalysis(logPath+'iter-'+iter)

        # Use f_hat to guess some optimal params
        xx = {'x': [-2, 2.6812, 1.6509, 10]}
        yy = {'target': [0.20166, 1.08328, 1.30455, 0.21180]}

        optimalParams = functionApproximator(xx, yy, ranges)
        new_xx = optimalParams

        # Stop when choosing a new_xx thats super close to an existing one

        break

    return new_xx

if __name__ == "__main__":
    # Demo
    test_ranges = {'w_pk': (0, 2), 'w_pr': (0, 2), 'w_dist': (0, 2), 'w_dist_decay': (700, 1300)}
    # test_ranges = [[0, 2], [0, 2], [0, 2], [700, 1300]]
    folder = os.getcwd() + '/scripts/parameter_analysis/'
    test_logPath = "~/swarm-log/analysis/"
    optimize(folder + 'task_assignment.xml', test_ranges, lhsSampler, GetAverageUtility, BayesianOptimizeArgmax, test_logPath)

    print 'Done'
