#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

logging.Logger.root.setLevel('DEBUG')

ubuntu = r'/home/pedro/PythonProjects/LIBS/data'
windows = r'C:\Users\Pedro\Google Drive\Iniciação Científica - EMBRAPA - 2017\Programas\LIBS\data'

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
    plt.drop_outliers(reference=plt.avg_spectra)
    func(plt, N=1)

Experiment = Research(*pellets, dirname='FResearch')
# Experiment.plot_avg_spectrum(names = ['7', '18'], elements = 'B I')
# Experiment.plot_avg_spectrum(names = ['23','24', '50'], region = [840, 856])
# Experiment.plot_avg_spectrum(names = ['1', '4', '7', '28', '30', '32'], region = [204, 210])

Experiment.plot_avg_spectrum(elementslist=db.elements, names = ['18', '21', '23', '25', '28', '30', '32', ])
#Usando o plotly, é possível melhorar muit o plot, colocando botões, nos quais o usuário escolhe os elemento no html
#e não no código python.
# tb3.outliers()

# É importante notar que um mesmo pico será contado mais de uma vez, pois,
# como ele "anda" ao longo das amostras, ele aparece como um intervalo e não
# como um ponto, mas equivale ao mesmo pico efetivamente. Apesar disso, não
# tem um erro acontecendo, confira fazendo n_picos/n_pontos do espectro.

"""
psbty, height, unc = tb1.peak_possibilites(db.table, N = 1, avg = 1, ret_unknown = 1)
study_object = Magnifier(psbty) #-> rename Glasses

do_i_have_both = study_object['C I', 'Ti I']
which_ones_are_unique = study_object(1) #-> esse objeto possui um resultado 
                                        #muito valioso para findar as disputas

new_data_rel_int, new_db_rel_int = tb1.compare(db_table = db.table, element = 'Fe I', 
                                       pbty_df = psbty, pks_itsty = height)
"""

# Pesquisar sobre multiprocessing.#
# reescrever compare com slice_by_nearest
# o efeito dopller no pico de HI está superando unc_delta.
# N muito elevado está resultando em pontos diferentes com mesmo lambda após
# round. É peciso rever isso.
#mudar opcoes do peakutils
