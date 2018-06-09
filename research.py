# -*- coding: utf-8 -*-
"""
Created on Thu Jun  7 10:13:02 2018

@author: Pedro
"""
import plotly.offline as py
import plotly.graph_objs as go
from extra_functions import slice_by_nearest
import os
import logging

class Research:
    
    def __init__(self, *args, dirname = ''):
        self.pellets = args
        self.__names = tuple(plt.name for plt in self.pellets)
        self.makedirs(dirname)
    
    def __str__(self):
        return 'Research' + str(self.__names)
        
    def __repr__(self):
        return 'Research' + str(self.__names)
         
    def repositioner(func):
        """To be used as a decorator on functions requiring file management."""
        def wrapper(self, *args, **kwargs):
            os.chdir(self.path)
            output = func(self, *args, **kwargs)
            os.chdir(self.root)
            return output
        return wrapper
    
    @repositioner
    def plot_avg_spectrum(self, region = '', names = None):
        if not names:   names = self.__names
        
        fig = []
        for plt in self.pellets:
            if plt.name not in names:   continue
            data = plt.avg_spectra
            if bool(region):    
                data = slice_by_nearest(data, region)
            
            trace = go.Scatter(
                    x = data.index,
                    y = data,
                    mode = 'lines',
                    name = plt.name)
            fig.append(trace)
            
        filename = 'plot_avg(' + '_'.join(list(names) + [str(region)]) + ')'
        
        py.plot(fig, filename = ''.join([filename, '.html']), validate = False)
        
    def makedirs(self, directory):
        self.root = os.getcwd()
        path = os.path.join(self.root, directory)
        if directory != '':
            if not os.path.exists(path):
                self.path = path
                self.directory = directory
                os.makedirs(self.directory)
            else:
                logging.warning(
                        "directory already exists. Files may be overwritten.")
                self.path = path
        else:
            self.directory = self.__repr__()
            path = os.path.join(self.root, self.directory)
            if not os.path.exists(path):
                self.path = path
                os.makedirs(self.directory)
            else:
                logging.warning(
                        "directory already exists. Files may be overwritten.")
                self.path = path
                
        os.chdir(self.path)
   