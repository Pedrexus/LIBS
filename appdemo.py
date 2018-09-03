"""
Created on Wed May  2 23:42:56 2018

@author: pedro
"""

from pellet import Pellet, Magnifier
from nist import NIST
from research import Research
import time
import sys, glob, os
from extra_functions import timing

import logging

logging.Logger.root.setLevel('WARNING')

ubuntu = r'/home/pedro/PythonProjects/LIBS/data\Pedro'
windows = r'C:\Users\Pedro\Google Drive\Iniciação Científica - EMBRAPA - 2017\Programas\LIBS\data\Pedro'

"""
NIST(elements=['C I', 'B I', 'K I', 'P I', 'N I', 'H I', 'Cu I',
               'Al I', 'Al II', 'Fe I', 'Fe II', 'Ti I', 'Ti II',
               'Na I', 'Ca I', 'Zn I', 'O I', 'Pb I', 'Mg I', 'Mg II',
               'Si I', 'C II', 'O II', 'Ca II', 'Pb II', 'S II'],
     conf_out=False, upp_w=1000, line_out=3, g_out=False).save('nist_cris_db')
"""
db = NIST(load_file='nist_cris_db.json')

paths = []
if 'linux' in sys.platform:
    dirs = glob.glob1(ubuntu, '*')
    for d in dirs:
        path = os.path.join(ubuntu, d)
        paths.append(path)
else:
    dirs = glob.glob1(windows, '*')
    for d in dirs:
        path = os.path.join(windows, d)
        paths.append(path)

pellets = []
for path, d in zip(paths, dirs):
    pellets.append(Pellet(path, name=d))


@timing
def func(plt, N):
    plt.peaks_table(db.table, N=N)


for plt in pellets:
    print(len(plt.outliers(reference=plt.avg_spectra))/len(plt.origsptum.columns))
    plt.drop_outliers(reference=plt.avg_spectra)
    func(plt, N=1)

Experiment = Research(*pellets, dirname='FResearch')