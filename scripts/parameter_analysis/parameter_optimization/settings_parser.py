import json
from bayesian_optimization import BayesianOptimizeArgmax
from samplers import *
from parse_utility import GetAverageUtility
from collections import OrderedDict
from functools import partial
import os


class SettingsParser:
    def __init__(self, file):
        with open(file) as data_file:
            self.settings = json.load(data_file)

    def getMissionFile(self):
        if 'MissionFilePath' in self.settings:
            return self.settings['MissionFilePath']
        else:
            print 'Please specify the MissionFilePath.'
            quit()


    def getLogPath(self):
        if 'LogPath' in self.settings:
            return os.path.join(self.settings['LogPath'], '')  # add a '/' to the end if not there already
        else:
            print 'Please specify the LogPath.'
            quit()

    def getNoOptimization(self):
        if 'NoOptimization' in self.settings:
            return self.settings['NoOptimization']
        else:
            return False

    def getStateSpaceSampler(self):
        if self.getNoOptimization():
            return gridSearch

        if self.settings['StateSpaceSampler'] == 'LHS':
            if self.getNoOptimization():
                print "Please set the State Space Sampler to 'GridSearch'."
                quit()
            else:
                return lhsSampler
        elif self.settings['StateSpaceSampler'] == 'GridSearch':
            return gridSearch
        else:
            print 'Please select a valid state space sampler.'
            quit()

    def getPostMissionAnalyzer(self):
        if 'UtilityColumnName' not in self.settings:
            if self.getNoOptimization(
            ):  # can only be excluded if not optimizing
                return None
            else:
                print 'Please specify the UtilityColumnName, or enable NoOptimization.'
                quit()
        else:
            params = {}
            params['columnName'] = self.settings['UtilityColumnName']
            return partial(GetAverageUtility, **params)


    def getFunctionApproximator(self):
        if 'FunctionApproximatorParameters' not in self.settings:
            return None
        if self.settings['FunctionApproximator'] == 'BO':
            params = {}
            params['acq'] = self.settings['FunctionApproximatorParameters']['acq']
            params['kappa'] = self.settings['FunctionApproximatorParameters']['kappa']

            return partial(BayesianOptimizeArgmax, **params)
        else:
            print 'Please select a valid function approximator (and verify optional parameters).'
            quit()


    def getNumExploreSamples(self):
        if 'NumExploreSamples' in self.settings:
            return self.settings['NumExploreSamples']
        else:
            print 'Please specify NumExploreSamples.'
            quit()

    def getNumIterationsPerSample(self):
        if 'NumIterationsPerSample' in self.settings:
            return self.settings['NumIterationsPerSample']
        else:
            return 1


    def getNumExploitSamples(self):
        if 'NumExploitSamples' in self.settings:
            return self.settings['NumExploitSamples']
        else:
            return 0


    def getRanges(self):
        ranges = OrderedDict()
        if 'Ranges' in self.settings:
            for key, value in self.settings['Ranges'].items():
                ranges[key] = (value[0],value[1])
        return ranges
