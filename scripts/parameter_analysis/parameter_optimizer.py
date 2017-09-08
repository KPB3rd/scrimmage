from mako.template import Template
from mako.runtime import Context
from StringIO import StringIO
import os
import pyDOE

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


def generateMissionFile(template_filename, parameter_labels, parameter_values):
    if len(parameter_labels) != len(parameter_values):
        raise ValueError('Parameter Labels and Values are mismatched.')

    folder = os.path.dirname(os.path.abspath(template_filename))
    mytemplate = Template(filename=template_filename)

    parameters = dict(zip(parameter_labels, parameter_values))

    file = open(folder + '/testfile.txt', 'w')
    file.write(mytemplate.render(**parameters))
    file.close()


def optimize(template_filename, ranges, parameter_labels, state_space_sampler,
             post_scrimmage_analysis, function_approximator,
             numSamples=10, numIterationsPerSample=10):

    generateMissionFile(template_filename, parameter_labels, [.1, .2])

    xx = []
    yy = []

    new_xx = state_space_sampler(ranges, numSamples)
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
    ranges = [[0, 5], [0, 5], [0, 5], [700, 1300]]
    folder = os.getcwd() + '/scripts/parameter_analysis/'
    optimize(folder + 'task_assignment.xml', ranges, ['w_pk', 'w_pr'], lhsSampler, '', '')

    print 'done'
