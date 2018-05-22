# -*- coding: utf-8 -*-
"""
Created on Sat Apr 21 08:43:24 2018

@author: Pedro

previously: tablet.py
"""

import os, os.path, glob
import numpy as np
import pandas as pd
import peakutils as pu
from scipy.interpolate import CubicSpline
from extra_functions import magnitude

class Pellet:
    
    def __init__(self, data, **kwargs):
        self.data = data
        self.root = os.getcwd()
        self.spectms = np.array(
                [-1, 2047, 3976, 5935, 7893, 9835, 11771, 13591])
        self.spectrum = self.df_all_files(**kwargs)
        
    def interpolate(self, N, avg = False):
        """make spline interpolation of N times current number of data points
        and return the numeric result: demands heavy processing,
        try multiprocessing in the future."""
        wl = self.spectrum.index.values
        new_wl, step = np.linspace(wl[0], wl[-1], num = N*len(wl),
                                   endpoint = True, retstep = True)
        s = self.spectrum
        if avg: s = pd.DataFrame(s.mean(axis = 1))
        splines = (CubicSpline(s.index, s[col]) for col in s)

        #The spectms do not have a fixed step, this is just an aproximation.
        update = [int( (wl[i] - new_wl[0])/step ) for i in self.spectms[1:]]
        new_spectms = np.array([-1] + update)
        
        new_spectrum = pd.DataFrame( (f(new_wl) for f in splines),
                                    columns = new_wl ).T
        
        return step, new_spectms, new_spectrum
    
    
    def peak_possibilites(self, db_table, N = 1, ret_unknown = True, **kwargs):
        step, new_spectms, new_spectrum = self.interpolate(N, **kwargs)
        unc_delta = N*step
        flt_point = - magnitude(unc_delta)
                 
        *_, db_wl  = self.__get_from_db(db_table, keyword = 'wavelength')
        *_, db_ion = self.__get_from_db(db_table, keyword = 'ion')
        
        db_wl = db_wl.round(flt_point)
        
        sptm_unique_peaks = self.peaks_in_all_spectrum(
                 full_spectrum = new_spectrum, spectms = new_spectms, size = 2,
                 **kwargs).round(flt_point)
        
        new_spectrum.index = np.array(new_spectrum.index).round(flt_point)

        db_pblty = {}
        for peak in sptm_unique_peaks:
            if any(np.abs(db_wl - peak) < unc_delta):
                possibilities = np.where(np.abs(db_wl - peak) < unc_delta)[0]
                unq = np.unique(db_ion[possibilities])
                db_pblty[peak] = [tuple(unq), float(new_spectrum.loc[peak])]
            else:
                if ret_unknown: db_pblty[peak] = 'UNKNOWN'
                else:           pass
        
        pbty_df = pd.DataFrame(db_pblty, index = ['possibilities', 'height']).T
        
        return pbty_df

    def outliers(self, min_similarity = .99, pct_votes = .5, inliers = False,
                 **kwargs):
        """find outliers of the current Pellet.spectrum method."""
        similarity_matrix = self.correlation_matrix(**kwargs)
        avg_similarity = similarity_matrix.mean(axis = 1).mean(axis = 0)
        
        matrix_count = np.sum(
                similarity_matrix > max(min_similarity, avg_similarity))
        
        sptum_amount = len(similarity_matrix)
        votes_amount = sptum_amount*pct_votes
        
        outliers_idx = np.where((matrix_count <= votes_amount) == True)[0]
        outliers = similarity_matrix.columns[outliers_idx]
        
        if not inliers: return outliers
        elif inliers:   return matrix_count.index.drop(outliers)
        
    def drop_outliers(self, **kwargs):
        """EACH TIME this function is called it drops the found outliers of
        the current Pellet.spectrum method."""
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
        """builds the spectrum DataFrame based in Pellet.data location."""
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
        df = pd.DataFrame(full_spectrum)
        
        all_peaks = []
        for col in df:
            peaks_indexes, spta_peaks = self.peaks_in_spectra(
                spectra = df[col], **kwargs)
            all_peaks = np.concatenate([all_peaks, spta_peaks], axis = 0)
        
        sptm_unique_peaks = np.unique(all_peaks)
        
        return sptm_unique_peaks
    
    def correlation_matrix(self, reference, **kwargs):
        peaks_indexes, spta_peaks = self.peaks_in_spectra(reference, **kwargs)

        return self.spectrum.loc[spta_peaks].corr()
    
    def comparisson(self, *Tablets, full_output = True, **kwargs):
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
        

class DB_peaks:
    
    def __init__(self, series):
        self.data = series
        
    def __getitem__(self, keys):
        if keys == 'UNKNOWN':
            idx = np.where( self.data == keys )
        else:
            idx = range(len(self.data))
            for key in keys:
                loc = []
                for i, tupl in enumerate(self.data):
                    for value in tupl:
                        if key in value:
                            loc.append(i)
                            
                idx = list( filter(lambda x: x in loc, idx) )
                #idx = [x for x in idx if x in loc]
                        
        return self.data.iloc[idx]
    
    def __repr__(self):
        return repr(self.data)
                
        
        
        
        
        
        
        
        
                        
        
        
    
        
        