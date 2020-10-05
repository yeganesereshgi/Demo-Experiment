from psychopy import visual, event, core, logging
from psychopy.preferences import prefs
from psychopy.core import getTime, wait 
from psychopy.data import importConditions#, TrialHandler
from psychopy.iohub.constants import (EventConstants, EyeTrackerConstants
                             )
from psychopy.iohub import (ioHubExperimentRuntime)
from psychopy.iohub.util import getCurrentDateTimeString
import os
import random
import site
#site.addsitedir('C:\Users\yegan\AppData\Programs\Python\Python36\Local\Lib\site-packages')
from psynteract import Connection 
import psynteract
import socket
import csv
import eventtxt
import subprocess
import time
import math
import numpy as np
subject_id ='0'
tsv_dir = 'input.tsv'
Csv_dir = '_Calib_DTA.csv'



tsv_file = open(tsv_dir)
read_tsv = csv.reader(tsv_file, delimiter="\t")
for row in read_tsv:
    replaced = row.replace('nan','-88') 
    row = replaced
    writer.writerow(row)

data = list(csv.reader(tsv_file, delimiter="\t"))
with open(csv_dir, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerows(data)
        #for row in read_tsv:
            #print(row)
            #writer.writerow(row)
            #np.savetxt("alo.csv", np.array(row), fmt='%s', delimiter="\t")
        #    writer.writerow(row)

