# -*- coding: utf-8 -*-
"""
Created on Fri Apr 20 17:12:56 2018

@author: Pedro
"""
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import collections
import re
from extra_functions import remove_non_ascii, is_number, timing

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
                                 "A+'":   .02,
                                 'A':     .03,
                                 "A'":    .03,
                                 'B+':    .07,
                                 "B+'":   .07,
                                 'B':     .10,
                                 "B'":    .10,
                                 'C+':    .18,
                                 "C+'":   .18,
                                 'C':     .25,
                                 "C'":    .25,
                                 'D+':    .40,
                                 "D+'":   .40,
                                 'D':     .50,
                                 "D'":    .50,
                                 'E':     .50,
                                 "E'":    .50,
                                 '':      .50}


class NIST( Constants ):
    """NIST Atomic Spectra Database Lines Data
    download from 'https://physics.nist.gov/PhysRefData/ASD/lines_form.html'"""

    def __init__(self, load_file=False, elements = [], **options):
        super().__init__()

        if not load_file:
            self.options = {**options}
            self.nist = 'https://physics.nist.gov/cgi-bin/ASD/lines1.pl'
            for key, value in self.options.items():
                self.payload[key] = int(value)
            self.payload['spectra'] = ', '.join(elements)

            self.table = self.data
            self.elements = set(elements)
        else:
            self.table, self.elements = self.load(load_file)

    @property
    def data(self):
        data = pd.DataFrame(self.organize_data())

        try:    self.__drop_empty_cols(data)
        except: pass

        try:    data['Acc.'] = self._translate_uncertainty(
                        data['Acc.'], self.uncertainty_dict)
        except: pass

        try:    self.__convert_to_number(data)
        except: pass

        try:    self.__fill_with_zero(data)
        except: pass

        try:    self.__remove_type_col(data)
        except: pass


        return data

    @timing
    def download_data(self):

        #the requests.get(..) takes 85% of the time to be run. For this, I do not believe there is actual gain in
        #changing optimizing the rest of the code. The idea to spare time is using Pickle.
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

    @timing
    def save(self, filename, compression=None):
        filename = ''.join([filename, '.json'])
        try:
            self.table.to_json(path_or_buf=filename, orient='records', double_precision=15,
                               force_ascii=True, compression=compression)
            return True
        except Exception as x:
            print('An Error has happened. Details: {}'.format(x))

    @timing
    def load(self, filepath):
        table = pd.read_json(path_or_buf=filepath)
        elements = set(table[self.__find_col_name_in_table(table, 'Ion')])
        return table, elements

    @staticmethod
    def __drop_empty_cols(data):
        data.drop([''], axis = 1, inplace = True)
        data.drop(['-'], axis = 1, inplace = True)

    @staticmethod
    def _translate_uncertainty(data, dictionary):
        return [dictionary[key] for key in map(remove_non_ascii, data)]

    @staticmethod
    def __convert_to_number(data):
        for col in ['Ei\xa0\xa0(eV)', 'Ek\xa0\xa0(eV)', 'Rel.\xa0\xa0Int.',
                    'Observed\xa0\xa0Wavelength\xa0\xa0Air (nm)']:
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

    @staticmethod
    def __find_col_name_in_table(table, keyword):
        col_pos = np.where(
            [(keyword.lower() in col.lower()) for col in table.columns])[0][0]
        col_name = table.columns[col_pos]

        return col_name

    def __remove_type_col(self, data):
        col = self.__find_col_name_in_table(data, 'typ')
        data.drop(col, axis=1, inplace=True)

    def __getitem__(self, keyword):
            col_name = self.__find_col_name_in_table(self.table, keyword)
            return self.table[col_name]

    def __repr__(self):
        return repr(self.table)


if __name__ == '__main__':
    A = NIST(elements=['C I', 'B I'], conf_out=False, upp_w=1000,
             line_out=3)