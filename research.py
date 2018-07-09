# -*- coding: utf-8 -*-
"""
Created on Thu Jun  7 10:13:02 2018

@author: Pedro
"""
import plotly.offline as py
import plotly.graph_objs as go
from extra_functions import slice_by_inside_interval, iterable_remove_non_ascii
from pellet import Magnifier
import os
import logging
from collections import defaultdict


class Research:

    def __init__(self, *args, dirname=''):
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

            try:
                os.chdir(self.path)
                output = func(self, *args, **kwargs)
                os.chdir(self.root)
                return output
            except Exception as X:
                os.chdir(self.root)
                raise Exception(X)

        return wrapper

    @repositioner
    def plot_avg_spectrum(self, elementslist, **kwargs):
        elements = iterable_remove_non_ascii(elementslist)
        graphdata = self.plotly_layout(elements, **kwargs)

        fig = go.Figure(data=graphdata['traces'], layout=graphdata['layout'])

        filename = 'plot_avg(' + '_'.join(
            list(graphdata['names']) + [str(graphdata['region'])]
        ) + ')'

        py.plot(fig, filename=''.join([filename, '.html']), validate=False,
                auto_open=True)

    def plotly_traces_and_notes(self, elementslist, region='', names=None):
        graphdata = defaultdict(list)

        if not names:   names = self.__names
        graphdata['names'] = names
        graphdata['region'] = region

        graphdata['notes'] = defaultdict(list)
        for plt in self.pellets:

            if plt.name not in names: continue

            data = plt.avg_spectra
            peaks_table = plt.peaks_table[0]

            if bool(region):
                data = slice_by_inside_interval(data, region)
                peaks_table = slice_by_inside_interval(
                    peaks_table, region)

            trace = go.Scatter(
                x=data.index,
                y=data,
                mode='lines',
                name=plt.name)

            graphdata['traces'].append(trace)

            magn_peaks_table = Magnifier(peaks_table)
            for element in elementslist:
                peaks_table = magn_peaks_table[element]

                for row, height in plt.peaks_table[1].loc[peaks_table.index] \
                        .iterrows():
                    textdata = iterable_remove_non_ascii(
                        plt.peaks_table[0][row],
                        ret='str')

                    graphdata['notes'][element].append(
                        self.annotations(row, float(height), textdata)
                    )

        return graphdata

    def plotly_layout(self, elementslist, **kwargs):
        graphdata = self.plotly_traces_and_notes(elementslist, **kwargs)

        for element in elementslist:
            graphdata['buttons'].append(
                self.button(label=element,
                            annotations=graphdata['notes'][element])
            )

        graphdata['layout'] = go.Layout(showlegend=True,
                                        updatemenus=self.updatemenus(
                                                 buttons=graphdata['buttons']
                                            )
                                       )

        return graphdata

    @staticmethod
    def updatemenus(buttons, type='dropdown'):
        updatemenus = list([
            dict(type=type,
                 active=-1,
                 showactive=True,
                 buttons=list(buttons),

                 direction='down',
                 pad={'r': 5, 't': 1},
                 x=0.1,
                 xanchor='left',
                 y=0.9,
                 yanchor='bottom',
                 bgcolor='#FFFFFF',
                 bordercolor='#111111',
                 font=dict(size=11)
                 ),
        ])
        return updatemenus

    @staticmethod
    def button(label, annotations=None, booleantraces=None):

        button = dict(
            label=label,
            method='update',
            args=[{'visible': [True]},
                  {'title': label,
                   'annotations': annotations}]
        )

        #if not booleantraces:
            #del button['args'][0]

        return button

    @staticmethod
    def annotations(x, y, text):
        notes = dict(
            x=x,
            y=y,
            xref='x',
            yref='y',
            text=text,
            showarrow=True,
            font=dict(
                family='Arial',
                size=12,
                color='#000000'
            ),
            align='center',
            arrowhead=7,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor='#636363',
            ax=0,
            ay=-40,
            bordercolor='#c7c7c7',
            borderwidth=4,
            borderpad=4,
            bgcolor='#ffffff',
            opacity=0.8
        )
        return notes

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
