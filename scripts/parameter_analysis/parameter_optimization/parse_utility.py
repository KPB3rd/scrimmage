import os
import matplotlib.pyplot as plt


def GetUtility(fileName):
    f = open(fileName, 'r')
    # Get last line
    for line in f:
        pass
    lastLine = line.split(',')

    utility = lastLine[-1]

    return utility

def GetAverageUtility(directory):
    files = os.listdir(directory)

    sumUtility = 0
    for file in files:
        utility = GetUtility(directory + '/' + file + '/summary.csv')
        sumUtility += float(utility)

    avgUtility = sumUtility / len(files)
    return avgUtility

if __name__ == "__main__":
    dir = '/home/kbowers6/swarm-log/pw-p2'
    print GetAverageUtility(dir)

    # example plot
    plt.plot([0, .1, .2, .3, .5, 1, 2, 3], [0.35, 0.55, .76, .85, .97, 1, 1, 1.08], 'ro')
    plt.xlabel('Priority Weight')
    plt.ylabel('Utility')
    plt.show()