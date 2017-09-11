from mako.template import Template
from mako.runtime import Context
from StringIO import StringIO
import os
import pyDOE
import subprocess
import threading
import time
import os
import signal
import sys
import xml.etree.ElementTree as ET

import numpy as np
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


def generateMissionFile(templateFullFilename, parameterLabels, parameterValues, missionIteration):
    if len(parameterLabels) != len(parameterValues):
        raise ValueError('Parameter Labels and Values are mismatched.')
        quit()

    # Load the mission file
    myTemplate = Template(filename=templateFullFilename)

    # Parse in the params
    try:
        parameterLabels.append('iter')
        parameterValues.append(missionIteration)
        parameters = dict(zip(parameterLabels, parameterValues))
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
             postScrimmageAnalysis, functionApproximator,
             numSamples=5, numIterationsPerSample=10):

    xx = []
    yy = []

    # Exploration parameters
    new_xx = stateSpaceSampler(ranges, numSamples)

    while True:
        for iter, params in enumerate(new_xx):
            # Parse sample into template mission
            missionFile = generateMissionFile(templateFilename, parameterLabels, params, iter)

            # run scrimmage
            print missionFile
            scrimmage_process = subprocess.Popen(["scrimmage", missionFile])
            print 'Running Simulation', iter

            pass

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
    ranges = [[0, 2], [0, 2], [0, 2], [700, 1300]]
    labels = ['w_pk', 'w_pr', 'w_dist', 'w_dist_decay']
    folder = os.getcwd() + '/scripts/parameter_analysis/'
    optimize(folder + 'task_assignment.xml', ranges, labels, lhsSampler, '', '')

    print 'Done'
