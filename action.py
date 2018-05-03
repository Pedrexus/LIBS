#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  2 23:42:56 2018

@author: pedro
"""

from tablet import Tablet
from nist import NIST
import time
start = time.time()
    
path1 = r'/home/pedro/PythonProjects/LIBS/data/1'
tb1 = Tablet(path1)
    
path2 = r'/home/pedro/PythonProjects/LIBS/data/18'
tb2 = Tablet(path2)
    
path3 = r'/home/pedro/PythonProjects/LIBS/data/23'
tb3 = Tablet(path3)
            
tb1.drop_outliers(reference = tb1.avg_spectra)
tb2.drop_outliers(reference = tb2.avg_spectra)
tb3.drop_outliers(reference = tb3.avg_spectra)
    
C1 = tb2.comparisson(tb1)
C2 = tb2.comparisson(tb3)
C_all = tb2.comparisson(tb1, tb3)
    

db = NIST(elements = ['C I', 'B I', 'K I', 'P I', 'N I', 'H I', 'Cu I',
                      'Al I', 'Fe I', 'Ti I', 'Na I', 'Ca I', 'Zn I'], conf_out = False, upp_w = 1000,
          line_out = 3, g_out = False)   
    
    #É importante notar que um mesmo pico será contado mas de uma vez, pois,
    #como ele "anda" ao longo das amostras, ele aparece como um intervalo e não
    #como um ponto, mas equivale ao mesmo pico efetivamente. Apesar disso, não 
    #tem um erro acontecendo, confira fazendo n_picos/n_pontos do espectro.

psbty1 = tb1.peak_possibilites(db.table, N = 1, ret_unknown = 0)
psbty1_count = psbty1.value_counts(normalize = True)
    
end = time.time()
total_time = end - start#N = 5: 90s, N = 1: 43s PC - N = 1: 80s.

    #Pesquisar sobre multiprocessing.