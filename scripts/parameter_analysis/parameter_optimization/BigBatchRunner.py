import os
import time

path = '/home/kbowers6/Documents/scrimmage/bioswarm/plugins/autonomy/BeeWave/BeeWave.xml'

begTag = '<truthThreshold>'
endTag = '</truthThreshold>'
parseIter = ['0.50', '0.80', '0.90', '0.95']
parseIter = ['0.0']
# parseIter = ['0.80', '0.90', '0.95']


def UpdateFile(path, currText, newText):
    # Read in the file
    with open(path, 'r') as file:
        filedata = file.read()

    # Replace the target string
    filedata = filedata.replace(currText, newText)

    # Write the file out again
    with open(path, 'w') as file:
        file.write(filedata)





for iter, value in enumerate(parseIter):
    # Next param set
    if iter > 0:
        UpdateFile(path, begTag + parseIter[iter - 1] + endTag, begTag + parseIter[iter] + endTag)

    # Run sims
    os.system('python parameter_optimizer.py --SettingsFile settings_batch0.json')
    os.system('python parameter_optimizer.py --SettingsFile settings_batch10.json')
    os.system('python parameter_optimizer.py --SettingsFile settings_batch30.json')
    os.system('python parameter_optimizer.py --SettingsFile settings_batch50.json')
    os.system('python parameter_optimizer.py --SettingsFile settings_batch80.json')
    os.system('python parameter_optimizer.py --SettingsFile settings_batch100.json')
    os.system('python parameter_optimizer.py --SettingsFile settings_batch110.json')
    os.system('python parameter_optimizer.py --SettingsFile settings_batch120.json')
    os.system('python parameter_optimizer.py --SettingsFile settings_batch150.json')
