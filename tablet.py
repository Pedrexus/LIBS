# -*- coding: utf-8 -*-
"""
Created on Sat Apr 21 08:43:24 2018

@author: Pedro
"""

import os, os.path, glob
import numpy as np
import pandas as pd
import peakutils as pu
import nist
from scipy.interpolate import CubicSpline
from extra_functions import magnitude

class Tablet:
    
    def __init__(self, data, **kwargs):
        self.data = data
        self.root = os.getcwd()
        self.spectms = np.array(
                [-1, 2047, 3976, 5935, 7893, 9835, 11771, 13591])
        self.spectrum = self.df_all_files(**kwargs)
        
    def interpolate(self, N, ):
        """make spline interpolation of N times current number of data points
        and return the numeric result: demands heavy processing,
        try multiprocessing in the future."""
        wl = self.spectrum.index.values
        new_wl, step = np.linspace(wl[0], wl[-1], num = N*len(wl),
                                   endpoint = True, retstep = True)
        s = self.spectrum
        splines = (CubicSpline(s.index, s[col]) for col in s)

        #The spectms do not have a fixed step, this is just an aproximation.
        update = [int( (wl[i] - new_wl[0])/step ) for i in self.spectms[1:]]
        new_spectms = np.array([-1] + update)
        
        new_spectrum = pd.DataFrame( (f(new_wl) for f in splines),
                                    columns = new_wl ).T
        
        return step, new_spectms, new_spectrum
    
    
    def peak_possibilites(self, db_table, N = 1, ret_unknown = True, **kwargs):
        step, new_spectms, new_spectrum = self.interpolate(N)
        unc_delta = N*step
                 
        *_, db_wl  = self.__get_from_db(db.table, keyword = 'wavelength')
        *_, db_ion = self.__get_from_db(db.table, keyword = 'ion')
        
        db_wl = db_wl.round(- magnitude(unc_delta))
        
        sptm_unique_peaks = self.peaks_in_all_spectrum(
                 full_spectrum = new_spectrum, spectms = new_spectms, size = 2,
                 **kwargs).round(- magnitude(unc_delta))

        db_pblty = {}
        for peak in sptm_unique_peaks:
            if any(np.abs(db_wl - peak) < unc_delta):
                possibilities = np.where(np.abs(db_wl - peak) < unc_delta)[0]
                unq = np.unique(db_ion[possibilities])
                db_pblty[peak] = tuple(unq)
            else:
                if ret_unknown: db_pblty[peak] = 'UNKNOWN'
                else:           pass
        
        pblty_df = pd.Series(db_pblty, name = 'peak possibilities')
        
        return pblty_df

    def outliers(self, min_similarity = .99, pct_votes = .5, inliers = False,
                 **kwargs):
        """find outliers of the current Tablet.spectrum method."""
        similarity_matrix = self.correlation_matrix(**kwargs)
        avg_similarity = similarity_matrix.mean(axis = 1).mean(axis = 0)
        
        matrix_count = np.sum(
                similarity_matrix > max(min_similarity, avg_similarity))
        
        sptum_amount = len(similarity_matrix)
        votes_amount = sptum_amount*pct_votes
        
        outliers = np.where((matrix_count <= votes_amount) == True)[0]
        
        if not inliers: return outliers
        elif inliers:   return matrix_count.index.drop(outliers)
        
    def drop_outliers(self, **kwargs):
        """EACH TIME this function is called it drops the found outliers of
        the current Tablet.spectrum method."""
        return self.spectrum.drop(self.outliers(**kwargs), axis = 1,
                                  inplace = True)
    
    def repositioner(func):
        """To be used as a decorator on functions requiring file management."""
        def wrapper(self, *args, **kwargs):
            os.chdir(self.data)
            return func(self, *args, **kwargs)
            os.chdir(self.root) 
        return wrapper
    
    @repositioner    
    def df_all_files(self, file_format = '.ols', drop_empty = True):
        """builds the spectrum DataFrame based in Tablet.data location."""
        files = glob.glob1(self.data, ''.join(["*", file_format]) )
        df = pd.Series()
        for n, file in enumerate(files):
            df = pd.concat(
                        [df,
                         pd.read_csv(file,
                                     skiprows = 8,
                                     sep = "\t",
                                     dtype = float,
                                     names = [n])],
                        axis = 1)
        if drop_empty:  
            df.dropna(axis = 1, inplace = True)
    
        return df
    
    @property
    def avg_spectra(self):
        return self.spectrum.mean(axis = 1)
    
    def peakutils(self, array, **kwargs):
        base = pu.baseline(array, deg = 2, max_it = 100, tol = 0.001)
        indexes = pu.indexes(array - base, thres = 0.13, min_dist = 10)
        
        return indexes
    
    def peaks_in_spectra(self, spectra, spectms = None, size = 10,
                         size_unit = 'points', **kwargs):
        """Recieves a spectra and returns its regions filled with peaks."""
        if spectms is None: spectms = self.spectms
        else:   pass   
        
        spta_wavelenght = spectra.index.values
        spta_intensity = spectra.values
        
        peaks_indexes = []
        for start, end in zip(spectms + 1, spectms[1:]):
            
            sptm_intensity = spta_intensity[start:end]
            indexes = self.peakutils(sptm_intensity, **kwargs)
            
            Lattices = np.array([range(i - size//2, i + size//2) for i 
                                 in indexes if i > size/2]).flatten()
            
            peaks_indexes = np.concatenate(
                    [peaks_indexes, Lattices + start]).astype(np.int64)
            
        spta_peaks = spta_wavelenght[peaks_indexes]
            
        return peaks_indexes, spta_peaks
    
    def peaks_in_all_spectrum(self, full_spectrum, **kwargs):
        
        all_peaks = []
        for col in full_spectrum:
            peaks_indexes, spta_peaks = self.peaks_in_spectra(
                spectra = full_spectrum[col], **kwargs)
            all_peaks = np.concatenate([all_peaks, spta_peaks], axis = 0)
        
        sptm_unique_peaks = np.unique(all_peaks)
        
        return sptm_unique_peaks
    
    def correlation_matrix(self, reference, **kwargs):
        peaks_indexes, spta_peaks = self.peaks_in_spectra(reference, **kwargs)

        return self.spectrum.loc[spta_peaks].corr()
    
    def comparisson(self, full_output = False, *Tablets, **kwargs):
        peaks_indexes, spta_peaks = self.peaks_in_spectra(self.avg_spectra,
                                                          **kwargs)
        out_sptm = [s.avg_spectra.loc[spta_peaks] for s in [self, *Tablets]]
        total_sptm = pd.concat(out_sptm, axis = 1)
        
        corr_matrix = total_sptm.corr()
        if full_output: 
            return corr_matrix
        else:   
            corrs = np.array(corr_matrix[0][1:])
            return corrs
        
    @staticmethod
    def __get_from_db(db_table, keyword):
        col_pos = np.where(
             [(keyword.lower() in col.lower()) for col in db_table.columns])[0]
        col_name = db_table.columns[col_pos]
        
        db_col = db_table.iloc[:, col_pos].values
        
        return col_pos, col_name, db_col
        

if __name__ == '__main__':
    import time
    start = time.time()
    
    path1 = r'C:\Users\Pedro\Google Drive\Iniciação Científica - EMBRAPA - 2017\Programas\Fase 3\data\1'
    tb1 = Tablet(path1)
    
    path2 = r'C:\Users\Pedro\Google Drive\Iniciação Científica - EMBRAPA - 2017\Programas\Fase 3\data\18'
    tb2 = Tablet(path2)
    
    path3 = r'C:\Users\Pedro\Google Drive\Iniciação Científica - EMBRAPA - 2017\Programas\Fase 3\data\23'
    tb3 = Tablet(path3)
            
    tb1.drop_outliers(reference = tb1.avg_spectra)
    tb2.drop_outliers(reference = tb2.avg_spectra)
    tb3.drop_outliers(reference = tb3.avg_spectra)
    
    C1 = tb2.comparisson(tb1)
    C2 = tb2.comparisson(tb3)
    C_all = tb2.comparisson(tb1, tb3)
    
    db = nist.NIST(elements = ['C I', 'B I', 'K I', 'P I', 'N I', 'H I', 'Cu I',
                               'Al I', 'Fe I', 'Ti I', 'Na I', 'Ca I', 'Zn I'], conf_out = False, upp_w = 1000,
                 line_out = 3, g_out = False)   
    
    #É importante notar que um mesmo pico será contado mas de uma vez, pois,
    #como ele "anda" ao longo das amostras, ele aparece como um intervalo e não
    #como um ponto, mas equivale ao mesmo pico efetivamente. Apesar disso, não 
    #tem um erro acontecendo, confira fazendo n_picos/n_pontos do espectro.

    psbty1 = tb1.peak_possibilites(db.table, N = 1, ret_unknown = 0)
    psbty1_count = psbty1.value_counts(normalize = True)
    
    
    end = time.time()
    total_time = end - start#N = 5: 90s, N = 1: 43s.
        
        
        
        
        
        
        
        
                        
        
        
    
        
        