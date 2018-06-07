# -*- coding: utf-8 -*-
"""
Created on Thu Jun  7 10:13:02 2018

@author: Pedro
"""
import plotly.offline as py
import plotly.graph_objs as go
from extra_functions import slice_by_nearest

class Research:
    
    def __init__(self, *args):
        self.pellets = args
        self.__names = [plt.name for plt in self.pellets]
        
    def __repr__(self):
        visual = 'research(' + str(self.__names) + ')'
        return visual
    
    def plot_avg_spectrum(self, region = ''):
        
        fig = []
        for plt in self.pellets:
            data = plt.avg_spectra
            if bool(region):    
                data = slice_by_nearest(data, region)
            
            trace = go.Scatter(
                    x = data.index,
                    y = data,
                    mode = 'lines',
                    name = plt.name)
            fig.append(trace)
            
        filename = '_'.join(self.__names + [str(region)])
        
        py.plot(fig, filename = ''.join([filename, '.html']), validate = False)
        
    