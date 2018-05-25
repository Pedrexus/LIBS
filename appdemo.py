#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  2 23:42:56 2018

@author: pedro
"""

from pellet import Pellet, Magnifier
from nist import NIST
import time
import sys

start = time.time()

ubuntu = [r'/home/pedro/PythonProjects/LIBS/data/1',
          r'/home/pedro/PythonProjects/LIBS/data/18',
          r'/home/pedro/PythonProjects/LIBS/data/23']
windows = [r'C:\Users\Pedro\Google Drive\Iniciação Científica - EMBRAPA - 2017\Programas\LIBS\data\1', 
           r'C:\Users\Pedro\Google Drive\Iniciação Científica - EMBRAPA - 2017\Programas\LIBS\data\18',
           r'C:\Users\Pedro\Google Drive\Iniciação Científica - EMBRAPA - 2017\Programas\LIBS\data\23']    

paths = []
if 'linux' in sys.platform:
    for path in ubuntu:
        paths.append(path)
else:
    for path in windows:
        paths.append(path)

tb1 = Pellet(paths[0]) 
tb18 = Pellet(paths[1])
tb23 = Pellet(paths[2])
            
tb1.drop_outliers(reference = tb1.avg_spectra)
tb18.drop_outliers(reference = tb18.avg_spectra)
tb23.drop_outliers(reference = tb23.avg_spectra)

#tb3.outliers()
    
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

data_rel_int, db_rel_int = tb1.compare(db_table = db.table, element = 'Fe I', 
                                       pbty_df = psbty, peaks_intsty = height,
                                       unc_delta = unc)
    
end = time.time()
total_time = end - start#N = 5: 90s, N = 1: 43s PC - N = 1: 80s.

    #Pesquisar sobre multiprocessing.#