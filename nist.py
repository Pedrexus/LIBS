# -*- coding: utf-8 -*-
"""
Created on Fri Apr 20 17:12:56 2018

@author: Pedro
"""
import requests
import pandas as pd
from bs4 import BeautifulSoup
import collections
import re

def remove_non_ascii(string):
    new_string = []
    for i in string:
        if ord(i) < 128:
             new_string.append(i)
        else: pass
    
    return ''.join(new_string)

def is_number(string):
    try:               float(string)
    except ValueError: return False
    return True

class Constants:
    
    def __init__(self):
        self.payload = {'spectra': '', #espécies quimicas
                        'limits_type': 0, #0 = wavelenght, 1 = wavenumber,        --> fixed
                        'low_w': 190, #lower wl
                        'upp_w': 250, #upper wl
                        'unit': 1, #0 = Angstrom, 1 = nm, 2 = um
                        'de': 0, #graphical options                               --> fixed
                        'format': 0, #0 = HTML, 1 = ASCII                         --> fixed 
                        'line_out': 0, #0 = all, 3 = only observed
                        'no_spaces': 'on', #no spaces between values              --> fixed
                        'remove_js': 'on', #remove javascript                     --> fixed
                        'en_unit': 1, #0 = cm-1, 1 = eV, 2 = Rydberg
                        'output': 0, #0 = entirety, 1 = in pages                  --> fixed
                        'bibrefs': 0, #0 = off, 1 = on                            --> fixed
                        'page_size': 15, #int                                     --> fixed
                        'show_obs_wl': 1, #wavelenght data option                 --> fixed
                        'unc_out': 1, #wavelenght data option
                        'order_out': 0, #0 = wavelenght, 1 = multiplet            --> fixed
                        'max_low_enrg': '',  #optional 
                        'show_av': 4, #[0 - 5] options wavelengths in
                        'max_upp_enrg': '',  #optional 
                        'tsb_value': 0, #optional - Transition strength bounds will apply to
                        'min_str': '', #optional
                        'A_out': 1, #0 = Ak, 1 = gkAk
                        'A8': 1, #0 = off, 1 = on units 10^8
                        'max_str': '', #optional
                        'allowed_out': 1, #Transition type Allowed (E1)
                        'forbid_out': 0, #Transition type Forbidden (M1, E2, ...)
                        'min_accur': '', #optional 
                        'min_intens': '', #optional
                        'conf_out': 'on', #level info  --> Só funcionam automaticamente
                        'term_out': '', #level info    --> se apenas um estiver em
                        'J_out': '', #level info       --> modo 'on'. Rever no futuro.
                        'intens_out': 'on',
                        'enrg_out': 1, #level info
                        'g_out': 1, #level info
                        'submit': 'Retrieve Data'
                    }
    
        self.uncertainty_dict = {'AAA':   .003,
                                 'AA':    .01,
                                 'A+':    .02,
                                 'A':     .03,
                                 " A' ":  .03,
                                 'B+':    .07,
                                 'B':     .10,
                                 " B' ":  .10,
                                 'C+':    .18,
                                 'C':     .25,
                                 " C' ":  .25,
                                 'D+':    .40,
                                 'D':     .50,
                                 " D' ":  .50,
                                 'E':     .50,
                                 " E' ":  .50,
                                 '':      .50}
    
class NIST( Constants ):
    """NIST Atomic Spectra Database Lines Data
    download from 'https://physics.nist.gov/PhysRefData/ASD/lines_form.html'"""
    
    def __init__(self, elements, **options):
        Constants.__init__(self)
        self.options = {**options}
        self.nist = 'https://physics.nist.gov/cgi-bin/ASD/lines1.pl' 
        for key, value in self.options.items():
            self.payload[key] = int(value)
        self.payload['spectra'] = ', '.join(elements)

        self.table = self.data      
        
    @property
    def data(self): 
        data = pd.DataFrame(self.organize_data())
        
        try:    data = self.__drop_empty_cols(data)
        except: pass
    
        try:    data['Acc.'] = self.__translate_uncertainty(
                        data['Acc.'], self.uncertainty_dict)
        except: pass
    
        try:    self.__convert_to_number(data)
        except: pass
    
        try:    self.__fill_with_zero(data)
        except: pass
        
        return data
                        
    def download_data(self):
        web_data = requests.get(self.nist, params = self.payload)
        
        soup = BeautifulSoup(web_data.content, 'lxml')
        whole_table = soup.find('table', rules='groups')
        
        columns = whole_table.find_all('th')
        sub_tbody = whole_table.find_all('tbody')
        
        return columns, sub_tbody, web_data.url
    
    def organize_data(self):
        columns, sub_tbody, url = self.download_data()
        
        table = collections.defaultdict(list)
        for tag in sub_tbody:
            if tag.find('tr').find('td'): 
                table_rows = tag.find_all('tr')
                for tag2 in table_rows:
                    if tag2.has_attr('class'):
                        td_tags = tag2.find_all('td')
                        for i, value in enumerate(td_tags):
                            table[columns[i].text.strip()].append(value.text)
            else:   pass
        
        return table
    
    @staticmethod
    def __drop_empty_cols(data):
        return data.drop(['', '-'], axis = 1)
    @staticmethod
    def __translate_uncertainty(data, dictionary):
        return [dictionary[key] for key in map(remove_non_ascii, data)]
    @staticmethod
    def __convert_to_number(data):
        for col in ['Ei\xa0\xa0(eV)', 'Ek\xa0\xa0(eV)', 'Rel.\xa0\xa0Int.']:
            values = []
            for i in data[col]:
                value = re.findall( r'[-+]?\d*\.\d+|\d+', i)
                if len(value) == 0: value = ['0']
                values.append(float(value[0]))
            data[col] = values
    @staticmethod
    def __fill_with_zero(data):
        col = 'gkAki\xa0(108 s-1)'
        values = [float(i)  if is_number(i) else 0 for i in data[col]]
        data[col] = values
        
    def __repr__(self):
        print(self.table)
                            
"""Example:
        A = NIST(elements = ['C I', 'B I'], conf_out = False, upp_w = 1000,
                 line_out = 3)    """                