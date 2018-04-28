# -*- coding: utf-8 -*-
"""
Created on Sat Apr 21 08:43:24 2018

@author: Pedro
"""

import os, os.path, glob
import numpy as np
import pandas as pd
import peakutils as pu

class Tablet:
    
    def __init__(self, data, **kwargs):
        self.data = data
        self.root = os.getcwd()
        self.spectms = np.array(
                [-1, 2047, 3976, 5935, 7893, 9835, 11771, 13591])
        self.spectrum = self.df_all_files(**kwargs)
    
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
        return self.spectrum.drop(self.outliers(**kwargs), axis = 1, inplace = True)
    
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
        indexes = pu.indexes(array - base, thres = 0.05, min_dist = 10)
        
        return indexes
    
    def peaks_in_spectra(self, spectra, size = 10, size_unit = 'points', 
                         **kwargs):
        """Recieves a spectra and returns its regions filled with peaks."""
        
        spta_wavelenght = spectra.index.values
        spta_intensity = spectra.values
        
        peaks_indexes = []
        for start, end in zip(self.spectms + 1, self.spectms[1:]):
            
            sptm_intensity = spta_intensity[start:end]
            indexes = self.peakutils(sptm_intensity, **kwargs)
            
            Lattices = np.array([range(i - size//2, i + size//2) for i 
                                 in indexes if i > size/2]).flatten()
            
            peaks_indexes = np.concatenate(
                    [peaks_indexes, Lattices + start]).astype(np.int64)
            
        spta_peaks = spta_wavelenght[peaks_indexes]
            
        return peaks_indexes, spta_peaks
    
    
    def correlation_matrix(self, reference, **kwargs):
        peaks_indexes, spta_peaks = self.peaks_in_spectra(reference, **kwargs)

        return self.spectrum.loc[spta_peaks].corr()
    
    def comparisson(self, *Tablets, **kwargs):
        peaks_indexes, spta_peaks = self.peaks_in_spectra(self.avg_spectra,
                                                          **kwargs)
        out_sptm = [s.avg_spectra.loc[spta_peaks] for s in [*Tablets, self]]
        total_sptm = pd.concat(out_sptm, axis = 1)
        
        return total_sptm.corr()
        

if __name__ == '__main__':
    path1 = r'C:\Users\Pedro\Google Drive\Iniciação Científica - EMBRAPA - 2017\Programas\Fase 3\data\1'
    tb1 = Tablet(path1)
    
    path2 = r'C:\Users\Pedro\Google Drive\Iniciação Científica - EMBRAPA - 2017\Programas\Fase 3\data\18'
    tb2 = Tablet(path2)
    
    path3 = r'C:\Users\Pedro\Google Drive\Iniciação Científica - EMBRAPA - 2017\Programas\Fase 3\data\23'
    tb3 = Tablet(path3)
    
    C1 = tb2.comparisson(tb1, tb3)
            
    tb1.drop_outliers(reference = tb1.avg_spectra)
    tb2.drop_outliers(reference = tb2.avg_spectra)
    tb3.drop_outliers(reference = tb3.avg_spectra)

    C2 = tb2.comparisson(tb1, tb3)
    
    #Rever a ordem que os resultados estão surgindo.
        
        
        
        
        
        
        
        
        
                        
        
        
    
        
        