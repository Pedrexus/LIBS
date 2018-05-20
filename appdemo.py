#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  2 23:42:56 2018

@author: pedro
"""

from pellet import Pellet
from nist import NIST
import time
start = time.time()
    
path1 = r'/home/pedro/PythonProjects/LIBS/data/1'
tb1 = Pellet(path1)
    
path2 = r'/home/pedro/PythonProjects/LIBS/data/18'
tb18 = Pellet(path2)
    
path3 = r'/home/pedro/PythonProjects/LIBS/data/23'
tb23 = Pellet(path3)
            
tb1.drop_outliers(reference = tb1.avg_spectra)
tb18.drop_outliers(reference = tb18.avg_spectra)
tb23.drop_outliers(reference = tb23.avg_spectra)

#tb3.outliers()
    
C1 = tb18.comparisson(tb1)
C2 = tb18.comparisson(tb23)
C_all = tb18.comparisson(tb1, tb23)
   
db = NIST(elements = ['C I', 'B I', 'K I', 'P I', 'N I', 'H I', 'Cu I',
                      'Al I', 'Al II', 'Fe I', 'Fe II', 'Ti I', 'Ti II',
                      'Na I', 'Ca I', 'Zn I'],
          conf_out = False, upp_w = 1000, line_out = 3, g_out = False)   
    
    #É importante notar que um mesmo pico será contado mais de uma vez, pois,
    #como ele "anda" ao longo das amostras, ele aparece como um intervalo e não
    #como um ponto, mas equivale ao mesmo pico efetivamente. Apesar disso, não 
    #tem um erro acontecendo, confira fazendo n_picos/n_pontos do espectro.

psbty1 = tb1.peak_possibilites(db.table, N = 1, avg = 1, ret_unknown = 1)
#psbty1_count = psbty1.value_counts()
    
end = time.time()
total_time = end - start#N = 5: 90s, N = 1: 43s PC - N = 1: 80s.

    #Pesquisar sobre multiprocessing.