from mako.template import Template
from mako.runtime import Context
from StringIO import StringIO
import os
import pyDOE
import subprocess


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


def generateMissionFile(template_full_filename, parameter_labels, parameter_values, missionIteration):
    if len(parameter_labels) != len(parameter_values):
        raise ValueError('Parameter Labels and Values are mismatched.')
        quit()

    # Load the mission file
    mytemplate = Template(filename=template_full_filename)

    # Parse in the params
    try:
        parameters = dict(zip(parameter_labels, parameter_values))
        missionData = mytemplate.render(**parameters)

        # Save the file
        folder = os.path.dirname(os.path.abspath(template_full_filename))
        filename = os.path.splitext(os.path.basename(template_full_filename))[0]
        file = open(folder + '/' + filename + str(missionIteration) + '.xml', 'w')
        file.write(missionData)
        file.close()
    except NameError:
        print 'Detected incorrect or missing parameters in mission xml.'
        quit()



def optimize(template_filename, ranges, parameter_labels, state_space_sampler,
             post_scrimmage_analysis, function_approximator,
             numSamples=5, numIterationsPerSample=10):

    xx = []
    yy = []

    # Exploration parameters
    new_xx = state_space_sampler(ranges, numSamples)

    # Create mission files for initial exploration
    for iter, params in enumerate(new_xx):
        generateMissionFile(template_filename, parameter_labels, params, iter)

    print 'Samples generated.'

    while True:
        for sample in new_xx:
            # Parse sample into template mission

            # run scrimmage for numIterationsPerSample times

            pass

        # post_scrimmage_analysis for all mission results
        # append results to yy
        xx.append(new_xx)
        # yy.append(post_scrimmage_analysis('path'))

        # Use f_hat to guess some optimal params
        # optimal_params = function_approximator(xx, yy)
        # new_xx = optimal_params

        # When to stop? When f_hat is confident?
        break

    return new_xx

if __name__ == "__main__":
    # Demo
    ranges = [[0, 2], [0, 2], [0, 2], [700, 1300]]
    labels = ['w_pk', 'w_pr', 'w_dist', 'w_dist_decay']
    folder = os.getcwd() + '/scripts/parameter_analysis/'
    optimize(folder + 'task_assignment.xml', ranges, labels, lhsSampler, '', '')

    print 'Done'
