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
        return self.settings['MissionFilePath']


    def getLogPath(self):
        return os.path.join(self.settings['LogPath'] ,'') # add a '/' to the end if not there already


    def getStateSpaceSampler(self):
        if self.settings['StateSpaceSampler'] == 'LHS':
            return lhsSampler
        elif self.settings['StateSpaceSampler'] == 'GridSearch':
            return gridSearch
        else:
            print 'Please select a valid state space sampler'
            quit()

    def getPostMissionAnalyzer(self):
        params = {}
        params['columnName'] = self.settings['UtilityColumnName']
        return partial(GetAverageUtility, **params)


    def getFunctionApproximator(self):
        if self.settings['FunctionApproximator'] == 'BO':
            params = {}
            params['acq'] = self.settings['FunctionApproximatorParameters']['acq']
            params['kappa'] = self.settings['FunctionApproximatorParameters']['kappa']

            return partial(BayesianOptimizeArgmax, **params)
        else:
            print 'Please select a valid function approximator (and verify optional parameters).'
            quit()


    def getNumExploreSamples(self):
        return self.settings['NumExploreSamples']


    def getNumIterationsPerSample(self):
        return self.settings['NumIterationsPerSample']


    def getNumExploitSamples(self):
        return self.settings['NumExploitSamples']


    def getRanges(self):
        ranges = OrderedDict()
        for key, value in self.settings['Ranges'].items():
            ranges[key] = (value[0],value[1])
        return ranges
