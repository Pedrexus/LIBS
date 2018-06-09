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

start = time.time()

ubuntu = r'/home/pedro/PythonProjects/LIBS/data'
windows = r'C:\Users\Pedro\Google Drive\Iniciação Científica - EMBRAPA - 2017\Programas\LIBS\data'   

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
    pellets.append(Pellet(path, name = d))

for plt in pellets:
    plt.drop_outliers(reference = plt.avg_spectra)

Experiment = Research(*pellets, dirname = 'Research')
Experiment.plot_avg_spectrum(names = ['1', '3', '5'], region = [190, 195])

#tb3.outliers()

"""    
C1 = tb18.comparisson(tb1)
C2 = tb18.comparisson(tb23)
C_all = tb18.comparisson(tb1, tb23)
   
db = NIST(elements = ['C I', 'B I', 'K I', 'P I', 'N I', 'H I', 'Cu I',
                      'Al I', 'Al II', 'Fe I', 'Fe II', 'Ti I', 'Ti II',
                      'Na I', 'Ca I', 'Zn I', 'O I', 'Pb I', 'Mg I', 'Mg II',
                      'Si I', 'C II', 'O II', 'Ca II', 'Pb II', 'S II'],
          conf_out = False, upp_w = 1000, line_out = 3, g_out = False)   
    
    #É importante notar que um mesmo pico será contado mais de uma vez, pois,
    #como ele "anda" ao longo das amostras, ele aparece como um intervalo e não
    #como um ponto, mas equivale ao mesmo pico efetivamente. Apesar disso, não 
    #tem um erro acontecendo, confira fazendo n_picos/n_pontos do espectro.

psbty, height, unc = tb1.peak_possibilites(db.table, N = 1, avg = 1, ret_unknown = 1)
study_object = Magnifier(psbty) #-> rename Glasses

do_i_have_both = study_object['C I', 'Ti I']
which_ones_are_unique = study_object(1) #-> esse objeto possui um resultado 
                                        #muito valioso para findar as disputas

new_data_rel_int, new_db_rel_int = tb1.compare(db_table = db.table, element = 'Fe I', 
                                       pbty_df = psbty, pks_itsty = height)
    
end = time.time()
total_time = end - start#N = 5: 90s, N = 1: 43s PC - N = 1: 80s.

    #Pesquisar sobre multiprocessing.#
    #criar pasta para salvar gráficos, pq eles estão se perdendo nas pastas.
    #em experiment, o usuario eve ser capaz de escolhr quais subgrupos de pellets ele quer analisar.]
    #reescrever compare com slice_by_nearest
"""