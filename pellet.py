# -*- coding: utf-8 -*-#
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
import extra_functions as xf

class Pellet:
    
    def __init__(self, data, name = '', **kwargs):
        self.data = data
        self.name = name
        self.root = os.getcwd()
        self.spectms = self.origsptms = np.array(
                [-1, 2047, 3976, 5935, 7893, 9835, 11771, 13591])
        self.spectrum = self.origsptum = self.df_all_files(**kwargs)
        self.N = 1
    
    def __best_peak_function(self, element_data):
        """abstract function yet."""
        return element_data.index[0]
    
    def peaks_table(self, db_table, *args, **kwargs):
        """abstract function yet."""
        psbty_df, peaks_height, _ = self.peak_possibilites(db_table, 
                                              ret_unknown = True, avg = True,
                                              **kwargs)
        self.peaks_table = [psbty_df, peaks_height]
    
    def __data_rel_int(self, element, pbty_df, pks_itsty):
        elmt_in_data = Magnifier(pbty_df)(1)[element].data
        best_peak = self.__best_peak_function(elmt_in_data) ###
        data_best_peak_intsty = pks_itsty.loc[best_peak]
        
        data_rel_int = pks_itsty.loc[elmt_in_data.index]/data_best_peak_intsty
        
        return data_rel_int, best_peak  

    def __element_wavelenght_conection(self, db_wvlgth, data_wvlgth):
        
        wl_cnx = {}
        for wl in db_wvlgth:
            distances = np.abs(data_wvlgth - wl)
            condition = distances <= self.unc_delta
            if any(condition):
                idx = np.argmin(distances)
                wl_cnx[wl] = data_wvlgth[idx]
        
        return pd.Series(wl_cnx)
        
    def __db_rel_int(self, db_table, element, best_peak, data_wvlgth):
        
        *_, wl_col = self.__get_from_db(db_table, keyword = 'wavelength')
        db_table.set_index(wl_col, inplace = True)
        
        _, ion_name, *_ = self.__get_from_db(db_table, keyword = 'ion')
        db_elmt_wvlgth = Magnifier(db_table[ion_name])[element].index                      
        
        wl_cnx = self.__element_wavelenght_conection(
                    db_wvlgth = db_elmt_wvlgth,
                    data_wvlgth = data_wvlgth)
        
        _, int_name, *_ = self.__get_from_db(db_table, keyword = 'int')
        db_int_elmt_in = db_table[int_name].loc[wl_cnx.index] 
        db_best_peak_intsty = db_int_elmt_in.iloc[
                np.where(wl_cnx == best_peak)[0][0] ]        
        
        db_rel_int = db_int_elmt_in/db_best_peak_intsty
        
        return db_rel_int, wl_cnx
        
    def compare(self, db_table, element, pbty_df, pks_itsty):
        unc_delta = self.unc_delta
        
        data_rel_int, best_peak = self.__data_rel_int(
                element, pbty_df, pks_itsty)
        
        db_rel_int, wl_cnx = self.__db_rel_int(db_table, element, best_peak,
                                        data_wvlgth = data_rel_int.index)
        
        new_db_rel_int = self._merge(db_rel_int, unc_delta, kind = 'sum')
        new_data_rel_int = self._merge(data_rel_int.mean(axis = 1), unc_delta,
                                       kind = 'max')
        
        return new_data_rel_int, new_db_rel_int  
    
    @staticmethod
    def _merge(series, unc_delta, kind):
        s_name = series.name
        series = series.reset_index(name = 'values')
        new_series = dict()
        iterator = iter(series.index)
        
        i_0 = next(iterator)
        wl_0 = series['index'][i_0]
        while not xf.iterator_is_empty(iterator):
            i_1 = next(iterator)
            wl_1 = series['index'][i_1]
            
            counter = 1
            wl = series['index'][i_0]
            intsty = series['values'][i_0]
            
            while np.abs(wl_1 - wl_0) <= unc_delta:
                counter += 1
                wl += wl_1
                if kind == 'sum':
                    intsty += series['values'][i_1]
                if kind == 'max':
                    intsty = max(intsty, series['values'][i_1])
                
                if not xf.iterator_is_empty(iterator):   
                    i_1 = next(iterator)
                    wl_1 = series['index'][i_1]
                else:   break 
            i_0 = i_1
            wl_0 = wl_1
            
            new_series[wl/counter] = intsty
            
        return pd.Series(new_series, name = s_name)

    def interpolate(self, N, avg = False):
        """make spline interpolation of N times current number of data points
        and return the numeric result: demands heavy processing,
        try multiprocessing in the future."""
        wl = self.spectrum.index.values
        new_wl, step = np.linspace(wl[0], wl[-1], num = N*len(wl),
                                   endpoint = True, retstep = True)
        s = self.spectrum
        if avg: s = pd.DataFrame(self.avg_spectra)
        splines = (CubicSpline(s.index, s[col]) for col in s)
    
        #The spectms do not have a fixed step, this is just an aproximation.
        update = [int( (wl[i] - new_wl[0])/step ) for i in self.spectms[1:]]
        new_spectms = np.array([-1] + update)
            
        new_spectrum = pd.DataFrame( (f(new_wl) for f in splines),
                                      columns = new_wl ).T
        
        self.N, self.spectms, self.spectrum = N, new_spectms, new_spectrum
        
        return step
    
    def peak_possibilites(self, db_table, N = 1, ret_unknown = True, **kwargs):
        if self.N == 1:
            step = self.interpolate(N, **kwargs)
        if self.N != 1 and self.N != N:
            raise RuntimeWarning
        
        self.unc_delta = unc_delta = N*step
        flt_point = - xf.magnitude(unc_delta)
                 
        *_, db_wl  = self.__get_from_db(db_table, keyword = 'wavelength')
        *_, db_ion = self.__get_from_db(db_table, keyword = 'ion')
        
        db_wl = db_wl.round(flt_point)
        
        sptm_unique_peaks = self.peaks_in_all_spectrum(
               full_spectrum = self.spectrum, spectms = self.spectms, size = 2,
               **kwargs).round(flt_point)
        
        self.spectrum.index = np.array(self.spectrum.index).round(flt_point)

        db_pblty = {}
        db_wl_in = []
        for peak in sptm_unique_peaks:
            if any(np.abs(db_wl - peak) < unc_delta):
                possibilities = np.where(np.abs(db_wl - peak) < unc_delta)[0]
                unq = np.unique(db_ion[possibilities])
                db_pblty[peak] = tuple(unq)
                db_wl_in.append(np.unique(db_wl[possibilities]))
            else:
                if ret_unknown: db_pblty[peak] = ('UNKNOWN',)
                else:           pass
        
        pbty_df = pd.Series(db_pblty)
        peaks_height = self.spectrum.loc[pbty_df.index]
        
        return pbty_df, peaks_height, db_wl_in

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
            output = func(self, *args, **kwargs)
            os.chdir(self.root)
            return output
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
        base = pu.baseline(array, deg = 2, max_it = 500, tol = 0.0001)
        indexes = pu.indexes(array - base, thres = 0.13, min_dist = 10*self.N)
        
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
            
            Lattices = np.array([range(i - size//2 + 1, i + size//2) for i 
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
          [(keyword.lower() in col.lower()) for col in db_table.columns])[0][0]
        col_name = db_table.columns[col_pos]
        
        db_col = db_table.iloc[:, col_pos].values
        
        return col_pos, col_name, db_col
    
    def __repr__(self):
        return 'Pellet(' + str(self.name) + ')'
        

class Magnifier:
    """A tool made to be used in deeper analysis of the 
    Pellet.peak_possibilities()"""
    
    def __init__(self, series):
        self.data = series
        self.index = self.data.index
        
    def __getitem__(self, keys):
        """Magnifier['C I', 'Ti I'] -> all peaks with both possible elements."""
        if keys == None: return self.__class__(self.data)
        else:            
            if type(keys) == str:   keys = [keys] #review:  not pythonic.
            if keys == [('UNKNOWN',)]:
                idx = np.where( self.data == keys )
            else:
                idx = range(len(self.data))
                for key in keys:
                    loc = []
                    for i, tupl in enumerate(self.data):
                        if type(tupl) == tuple:
                            for value in tupl:
                                if key == xf.remove_non_ascii(value):
                                    loc.append(i)
                        elif type(tupl) == str:
                                if key == xf.remove_non_ascii(tupl):
                                    loc.append(i)
                        else:   pass
                                
                    idx = xf.intersection(idx, loc)
                            
            return self.__class__(self.data.iloc[idx])
    
    def __call__(self, integer):
        """Magnifier(2) -> all peaks with 2 possible elements."""
        if integer == None: return self.__class__(self.data)
        else:
            idx = []
            for i, tupl in enumerate(self.data):
                if len(tupl) == integer:
                    idx.append(i)
                    
            return self.__class__(self.data.iloc[idx]) 
            
    
    def __repr__(self):
        return repr(self.data)
    
    def value_counts(self, **kwargs):
        """Counts values based on pandas.Series.value_counts() method."""
        return self.data.value_counts(**kwargs)
                
        
        
        
        
        
        
        
        
                        
        
        
    
        
        