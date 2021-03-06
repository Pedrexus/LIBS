# -*- coding: utf-8 -*-#
"""
Created on Sat Apr 21 08:43:24 2018

@author: Pedro

previously: tablet.py
"""
import logging
import os, os.path, glob
import numpy as np
import pandas as pd
import peakutils as pu
from scipy.interpolate import CubicSpline
import extra_functions as xf
import scipy.signal as signal
<<<<<<< HEAD
import lmfit.models as fitmodels
=======
>>>>>>> e8cb411e7eaf8b25bb7df41cb8636df21373b8f1


class Pellet:

    def __init__(self, data, name='', **kwargs):
        self.data = data
        self.name = name
        self.root = os.getcwd()
        self.spectms = self.origsptms = np.array(
            [-1, 2047, 3976, 5935, 7893, 9835, 11771, 13591])
        self.spectrum = self.origsptum = self.df_all_files(**kwargs)
        self.N = 1

    def __getitem__(self, wavelength):
        if isinstance(wavelength, float) or isinstance(wavelength, int):
            return self.__getfloat(wavelength)
        elif isinstance(wavelength, slice):
            return self.__getslice(wavelength)
        else:
            raise TypeError(
                'index must be int or slice, not {}'.format(
                    type(wavelength).__name__))

    def __getfloat(self, wavelength):
        true_wl = xf.find_nearest(self.origsptum.index, wavelength)
        return self.origsptum.loc[true_wl]

    def __getslice(self, wavelength):
        start, stop, step = wavelength.start, wavelength.stop, wavelength.step
        true_start = xf.find_nearest(self.origsptum.index, start)
        true_stop = xf.find_nearest(self.origsptum.index, stop)
        if step is None or isinstance(step, int):
            return self.origsptum.loc[true_start:true_stop:step]
        else:
            raise ValueError("float step assignment not allowed (yet).")

    def __best_peak_function(self, element_data):
        """abstract function yet."""
        return element_data.index[0]

    def peaks_table(self, db_table, *args, **kwargs):
        """abstract function yet."""
        psbty_df, peaks_height, _ = self.peak_possibilites(db_table,
                                                           ret_unknown=True,
                                                           avg=True,
                                                           **kwargs)
        self.peaks_table = [psbty_df, peaks_height]

    def __data_rel_int(self, element, pbty_df, pks_itsty):
        elmt_in_data = Magnifier(pbty_df)(1)[element].data
        best_peak = self.__best_peak_function(elmt_in_data)  ###
        data_best_peak_intsty = pks_itsty.loc[best_peak]

        data_rel_int = pks_itsty.loc[
                           elmt_in_data.index] / data_best_peak_intsty

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

        *_, wl_col = self.__get_from_db(db_table, keyword='wavelength')
        db_table.set_index(wl_col, inplace=True)

        _, ion_name, *_ = self.__get_from_db(db_table, keyword='ion')
        db_elmt_wvlgth = Magnifier(db_table[ion_name])[element].index

        wl_cnx = self.__element_wavelenght_conection(
            db_wvlgth=db_elmt_wvlgth,
            data_wvlgth=data_wvlgth)

        _, int_name, *_ = self.__get_from_db(db_table, keyword='int')
        db_int_elmt_in = db_table[int_name].loc[wl_cnx.index]
        db_best_peak_intsty = db_int_elmt_in.iloc[
            np.where(wl_cnx == best_peak)[0][0]]

        db_rel_int = db_int_elmt_in / db_best_peak_intsty

        return db_rel_int, wl_cnx

    def compare(self, db_table, element, pbty_df, pks_itsty):
        unc_delta = self.unc_delta

        data_rel_int, best_peak = self.__data_rel_int(
            element, pbty_df, pks_itsty)

        db_rel_int, wl_cnx = self.__db_rel_int(db_table, element, best_peak,
                                               data_wvlgth=data_rel_int.index)

        new_db_rel_int = self._merge(db_rel_int, unc_delta, kind='sum')
        new_data_rel_int = self._merge(data_rel_int.mean(axis=1), unc_delta,
                                       kind='max')

        return new_data_rel_int, new_db_rel_int

    @staticmethod
    def _merge(series, unc_delta, kind):
        s_name = series.name
        series = series.reset_index(name='values')
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
                else:
                    break
            i_0 = i_1
            wl_0 = wl_1

            new_series[wl / counter] = intsty

        return pd.Series(new_series, name=s_name)

    def interpolate(self, N, avg=False):
        """make spline interpolation of N times current number of data points
        and return the numeric result: demands heavy processing,
        try multiprocessing in the future."""
        wl = self.spectrum.index.values
        new_wl, step = np.linspace(wl[0], wl[-1], num=N * len(wl),
                                   endpoint=True, retstep=True)
        s = self.spectrum
        if avg: s = pd.DataFrame(self.avg_spectrum)
        splines = (CubicSpline(s.index, s[col]) for col in s)

        # The spectms do not have a fixed step, this is just an aproximation.
        update = [int((wl[i] - new_wl[0]) / step) for i in self.spectms[1:]]
        new_spectms = np.array([-1] + update)

        new_spectrum = pd.DataFrame((f(new_wl) for f in splines),
                                    columns=new_wl).T

        self.N, self.spectms, self.spectrum = N, new_spectms, new_spectrum

        return step

    def peak_possibilites(self, db_table, N=1, ret_unknown=True, **kwargs):
        if self.N == 1:
            step = self.interpolate(N, **kwargs)
        if self.N != 1 and self.N != N:
            raise RuntimeWarning

        self.unc_delta = unc_delta = N * step
        flt_point = - xf.magnitude(unc_delta)

        *_, db_wl = self.__get_from_db(db_table, keyword='wavelength')
        *_, db_ion = self.__get_from_db(db_table, keyword='ion')

        db_wl = db_wl.round(flt_point)

        sptm_unique_peaks = self.peaks_in_all_spectrum(
            full_spectrum=self.spectrum, spectms=self.spectms, size=2,
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
                if ret_unknown:
                    db_pblty[peak] = ('UNKNOWN',)
                else:
                    pass

        pbty_df = pd.Series(db_pblty)
        peaks_height = self.spectrum.loc[pbty_df.index]

        return pbty_df, peaks_height, db_wl_in

    def outliers(self, min_similarity=.99, pct_votes=.5, inliers=False,
                 **kwargs):
        """find outliers of the current Pellet.spectrum method."""
        similarity_matrix = self.correlation_matrix(**kwargs)
        avg_similarity = similarity_matrix.mean(axis=1).mean(axis=0)

        matrix_count = np.sum(
            similarity_matrix > max(min_similarity, avg_similarity))

        sptum_amount = len(similarity_matrix)
        votes_amount = sptum_amount * pct_votes

        outliers_idx = np.where((matrix_count <= votes_amount) == True)[0]
        outliers = similarity_matrix.columns[outliers_idx]

        if not inliers:
            return outliers
        elif inliers:
            return matrix_count.index.drop(outliers)

    def drop_outliers(self, **kwargs):
        """EACH TIME this function is called it drops the found outliers of
        the current Pellet.spectrum method."""
        return self.spectrum.drop(self.outliers(**kwargs), axis=1,
                                  inplace=True)

    def repositioner(func):
        """To be used as a decorator on functions requiring file management."""

        def wrapper(self, *args, **kwargs):
            os.chdir(self.data)
            output = func(self, *args, **kwargs)
            os.chdir(self.root)
            return output

        return wrapper

    @repositioner
    def df_all_files(self, file_format='.ols', drop_empty=True):
        """builds the spectrum DataFrame based in Pellet.data location."""
        files = glob.glob1(self.data, ''.join(["*", file_format]))
        df = pd.Series()
        for n, file in enumerate(files):
            df = pd.concat(
                [df,
                 pd.read_csv(file,
                             skiprows=8,
                             sep="\t",
                             dtype=float,
                             names=[n])],
                axis=1)
        if drop_empty:
            df.dropna(axis=1, inplace=True)

        return df

    @property
<<<<<<< HEAD
    def avg_spectrum(self):
        avg = self.spectrum.mean(axis=1)
        avg.name = 'avg_spectrum'
        return avg

    def peakutils(self, array, **kwargs):
        base = pu.baseline(array, deg=2, max_it=500, tol=0.0001)
        indexes = pu.indexes(array - base, thres=0.13, min_dist=2 * self.N)
=======
    def avg_spectra(self):
        return self.spectrum.mean(axis=1)

    def peakutils(self, array, **kwargs):
        base = pu.baseline(array, deg=2, max_it=500, tol=0.0001)
        indexes = pu.indexes(array - base, thres=0.13, min_dist=10 * self.N)
>>>>>>> e8cb411e7eaf8b25bb7df41cb8636df21373b8f1

        return indexes

    def peaks_in_spectra(self, spectra, spectms=None, size=10,
                         size_unit='points', **kwargs):
        """Recieves a spectra and returns its regions filled with peaks."""
        if spectms is None:
            spectms = self.spectms
        else:
            pass

        spta_wavelenght = spectra.index.values
        spta_intensity = spectra.values

        peaks_indexes = []
        for start, end in zip(spectms + 1, spectms[1:]):
            sptm_intensity = spta_intensity[start:end]
            indexes = self.peakutils(sptm_intensity, **kwargs)

            Lattices = np.array([range(i - size // 2 + 1, i + size // 2) for i
                                 in indexes if i > size / 2]).flatten()

            peaks_indexes = np.concatenate(
                [peaks_indexes, Lattices + start]).astype(np.int64)

        spta_peaks = spta_wavelenght[peaks_indexes]

        return peaks_indexes, spta_peaks

    def peaks_in_all_spectrum(self, full_spectrum, **kwargs):
        df = pd.DataFrame(full_spectrum)

        all_peaks = []
        for col in df:
            peaks_indexes, spta_peaks = self.peaks_in_spectra(
                spectra=df[col], **kwargs)
            all_peaks = np.concatenate([all_peaks, spta_peaks], axis=0)

        sptm_unique_peaks = np.unique(all_peaks)

        return sptm_unique_peaks

    def correlation_matrix(self, reference, **kwargs):
        peaks_indexes, spta_peaks = self.peaks_in_spectra(reference, **kwargs)

        return self.spectrum.loc[spta_peaks].corr()

    def comparisson(self, *Pellets, full_output=True, **kwargs):
        peaks_indexes, spta_peaks = self.peaks_in_spectra(self.avg_spectrum,
                                                          **kwargs)
        out_sptm = [s.avg_spectrum.loc[spta_peaks] for s in [self, *Pellets]]

        total_sptm = pd.concat(out_sptm, axis=1)

        corr_matrix = total_sptm.corr()
        if full_output:
            return corr_matrix
        else:
            corrs = np.array(corr_matrix[0][1:])
            return corrs

    @staticmethod
    def __get_from_db(db_table, keyword):
        col_pos = np.where(
            [(keyword.lower() in col.lower()) for col in db_table.columns])[0][
            0]
        col_name = db_table.columns[col_pos]

        db_col = db_table.iloc[:, col_pos].values

        return col_pos, col_name, db_col

    def __repr__(self):
        return 'Pellet(' + str(self.name) + ')'

    @staticmethod
    def peak_baseline(spectrum_region, **kwargs):
        array = spectrum_region.values.flatten()
        baseline = pu.baseline(array, deg=1, **kwargs)
        return baseline

    def trimming_region(self, spectrum_region, wavelength, thres=0.87,
                        n_filter=10):
        # possibly will need to smooth
        array = spectrum_region.values.flatten()

        # the higher the n_filter, the smoother the data:
        a, b = 1, [1 / n_filter] * n_filter
        array = signal.lfilter(b, a, array)

        # OBS.: the "thres" argument don't influence in the result.
        valleys_indexes = self.peakutils(1 - array / array.max(), deg=0,
                                         thres=thres, min_dist=5)

        valleys = spectrum_region.index[valleys_indexes]

        trim_1 = xf.find_nearest(valleys, wavelength)
        trim_2 = xf.find_nearest(valleys.drop(trim_1), wavelength)

        if 0 < trim_1 < trim_2:
            region = slice(trim_1, trim_2)
        elif 0 < trim_2 < trim_1:
            region = slice(trim_2, trim_1)
        else:
            raise ValueError(
                "{} and {} do not build valid region".format(trim_1, trim_2))

        if region.start < wavelength < region.stop:
            return region
        else:
            raise ArithmeticError(
                "{} not in {}: could not isolate peak.".format(wavelength,
                                                               region))

    def confine_peak__by_inversion(self, spectrum_region_series, wavelength,
                                   **kwargs):
        """This method attempts to confine/isolate a peak given a valid peak
         wavelength using the inverted array to find the trimming points.
         This algorithm works better with small width peaks. DO NOT USE with
         peaks such as Hydrogen (656.45nm) or under high influence of Stark
         effect."""
        # assert its a series:
        if isinstance(spectrum_region_series, pd.DataFrame) and len(
                spectrum_region_series) == 1:
            spectrum_region_series = spectrum_region_series.T.iloc[0]
        elif isinstance(spectrum_region_series, pd.Series):
            pass
        else:
            raise TypeError(
                'spectrum_region must be Series, not {}'.format(
                    type(spectrum_region_series).__name__))

        trimmed_region = self.trimming_region(spectrum_region_series,
                                              wavelength, **kwargs)
        trimmed_spectrum = spectrum_region_series.loc[trimmed_region]
        baseline = self.peak_baseline(trimmed_spectrum)

        return trimmed_spectrum.sub(baseline)

    def confine_peak(self, wavelength, kind='inversion', spectra='all',
                     **kwargs):
        if spectra == 'all':
            spectra = self.origsptum
        elif spectra == 'avg':
            avg = self.avg_spectrum
            spectra = pd.DataFrame(avg, columns=[avg.name])
        else:
            pass

        if kind == 'inversion':
            trimmed_sptum = {}
            for sample, spectrum in spectra.items():
            samples = self.origsptum.columns
        else:
            samples = xf.build_iterable(spectra)

        if kind == 'inversion':
            trimmed_origsptum = {}
            for sample in samples:
                spectrum = self.origsptum[sample]
                try:
                    trimmed_spectrum = self.confine_peak__by_inversion(
                        spectrum,
                        wavelength,
                        **kwargs)
                    trimmed_sptum[sample] = trimmed_spectrum
                    trimmed_origsptum[sample] = trimmed_spectrum
                except Exception as X:
                    logging.debug(
                        "Sample {} raised: ".format(sample) + X.args[0])

        else:
            raise ValueError("{} is not valid kind.".format(kind))

        return trimmed_sptum

    def peakfit(self, wavelength, spectra='avg', model='lorentzian',
                kind='inversion'):

        fitting_region = self.confine_peak(wavelength, kind, spectra)

        fits = {}
        for name, spectrum in fitting_region.items():
            fits[name] = self.lmfit(spectrum, model)

        return fits
        # fit(fitting_region, model)

    def plotfit(self, wavelength, plotter='mpl', **kwargs):
        fits = self.peakfit(wavelength, **kwargs)
        if not len(fits):
            raise ArithmeticError(
                "Not able to confine or fit the peak in {}nm.".format(
                    wavelength))
        outs = [fit for fit in fits.values()]
        plot_data = dict(all_data=[out.data for out in outs],
                         best_fits=[out.best_fit for out in outs],
                         residuals=[out.residual for out in outs],
                         plots=[out.plot() for out in outs])
        if plotter == 'plotly':
            pass
        elif plotter == 'mpl':
            import matplotlib.pyplot as plotter
            plotter.show()

    def lmfit(self, spectrum, model: str):
        mod = self.build_full_model(spectrum, model)

        return mod.fit(data=spectrum.values, x=spectrum.index)

    @staticmethod
    def choose_model(model: str):
        if model.lower() in 'LorentzianModel()'.lower():
            return fitmodels.LorentzianModel
        elif model.lower() in 'GaussianModel()'.lower():
            return fitmodels.GaussianModel
        elif model.lower() in 'VoigtModel()'.lower():
            return fitmodels.VoigtModel
        elif model.lower() in 'PseudoVoigtModel()'.lower():
            return fitmodels.PseudoVoigtModel
        else:
            raise ValueError(
                "{} is not a valid input LIBS fitting model".format(model))

    def make_model(self, num, center, model):
        pref = "f{0}_".format(num)
        model = self.choose_model(model)(prefix=pref)
        model.set_param_hint(pref + 'center', value=center,
                             min=center - 0.1, max=center + 0.1)
        return model

    def build_full_model(self, spectrum, model):
        peaks_in_interval_indexes = self.peakutils(spectrum.values)
        peaks_in_interval = spectrum.iloc[peaks_in_interval_indexes].index

        mod = None
        for num, center in enumerate(peaks_in_interval):
            this_mod = self.make_model(num, center, model)
            if mod is None:
                mod = this_mod
            else:
                mod = mod + this_mod

        return mod
        return trimmed_origsptum


class Magnifier:
    """A tool made to be used in deeper analysis of the 
    Pellet.peak_possibilities()"""

    def __init__(self, series):
        self.data = series
        self.index = self.data.index

    def __getitem__(self, keys):
        """Magnifier['C I', 'Ti I'] -> all peaks with both possible elements."""
        if keys == None or keys == 'all':
            return self.__class__(self.data)
        else:
            if type(keys) == str:   keys = [keys]  # review:  not pythonic.
            if keys == [('UNKNOWN',)]:
                idx = np.where(self.data == keys)
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
                        else:
                            pass

                    idx = xf.intersection(idx, loc)

            return self.__class__(self.data.iloc[idx])

    def __call__(self, integer):
        """Magnifier(2) -> all peaks with 2 possible elements."""
        if integer == None:
            return self.__class__(self.data)
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
