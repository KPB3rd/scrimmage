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
        for range, param in zip(ranges, sample):
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



def optimize(templateFilename, ranges, parameterLabels, stateSpaceSampler,
             postScrimmageAnalysis, functionApproximator, logPath
             numSamples=5, numIterationsPerSample=10):

    xx = []
    yy = []

    # Exploration parameters
    new_xx = stateSpaceSampler(ranges, numSamples)
    simulationIter = 0
    while True:
        scrimmageProcesses = []
        newBatchStartingIter = simulationIter
        for params in new_xx:
            # Parse sample into template mission
            missionFile = generateMissionFile(templateFilename, parameterLabels, params, logPath, simulationIter)

            # run scrimmage
            # TODO REMOVE
            # missionFile = "/home/kbowers6/Documents/scrimmage/scrimmage/missions/straight.xml"
            scrimmageProcesses.append(subprocess.Popen(["scrimmage", missionFile]))
            simulationIter+=1
        
        # Wait for all processes to finish
        for process in scrimmageProcesses:
            process.wait()



        # post_scrimmage_analysis for all mission results
        # append results to yy
        xx.append(new_xx)
        # yy.append(post_scrimmage_analysis('path'))

        # Use f_hat to guess some optimal params
        # optimal_params = function_approximator(xx, yy)
        # new_xx = optimal_params

        # When to stop? When f_hat is "confident"?
        break

    return new_xx

if __name__ == "__main__":
    # Demo
    test_ranges = [[0, 2], [0, 2], [0, 2], [700, 1300]]
    test_labels = ['w_pk', 'w_pr', 'w_dist', 'w_dist_decay']
    folder = os.getcwd() + '/scripts/parameter_analysis/'
    pathPath = "~/swarm-log/analysis/"
    optimize(folder + 'task_assignment.xml', test_ranges, test_labels, lhsSampler, GetUtility, '', logPath)

    print 'Done'
