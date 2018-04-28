# -*- coding: utf-8 -*-
"""
Created on Fri Apr 20 17:12:56 2018

@author: Pedro
"""
import requests
import pandas as pd
from bs4 import BeautifulSoup
import collections

nist = 'https://physics.nist.gov/cgi-bin/ASD/lines1.pl'

elements = ['C I', 'B I']

payload = { 'spectra': ', '.join(elements), #espécies quimicas
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
            'unc_out': 0, #wavelenght data option
            'order_out': 0, #0 = wavelenght, 1 = multiplet
            'max_low_enrg': '',  #optional 
            'show_av': 2, #[0 - 5] options wavelengths in
            'max_upp_enrg': '',  #optional 
            'tsb_value': 0, #optional - Transition strength bounds will apply to
            'min_str': '', #optional
            'A_out': 1, #0 = Ak, 1 = gkAk
            'A8': 1, #0 = off, 1 = on units 10^8
            'max_str': '', #optional
            'allowed_out': 1, #Transition type Allowed (E1)
            'forbid_out': 1, #Transition type Forbidden (M1, E2, ...)
            'min_accur': '', #optional 
            'min_intens': '', #optional
            'conf_out': 'on', #level info
            'term_out': 'on', #level info
            'enrg_out': 'on', #level info
            'J_out': 'on', #level info
            'g_out': 'on', #level info
            'submit': 'Retrieve Data'
        }

r = requests.get(nist, params = payload)
#A = pd.read_html(r.url, attrs = {'class': "fix"})
soup = BeautifulSoup(r.content, 'lxml')
odd = soup.find_all('tr', attrs={'class': 'odd'})

whole_table = soup.find('table', rules='groups')
colums = whole_table.find_all('th') #--> Hard code columns names. Forget automatic behavior.
sub_tbody = whole_table.find_all('tbody')
# the two above lines are used to locate the table and the content    

# we then continue to iterate through sub-categories i.e. tbody-s > tr-s > td-s 
for tag in sub_tbody:
    if tag.find('tr').find('td'):
        table_rows = tag.find_all('tr')
        for tag2 in table_rows:
            if tag2.has_attr('class'):
                td_tags = tag2.find_all('td')
                print(td_tags[0].text, '<- Is the ion')
                print(td_tags[1].text, '<- Wavelength')
                print(td_tags[2].text, '<- Some formula gk Aki')
                # and so on...
                print('--'*40) # unecessary but does print ----------...

    else:
        pass

def payload_translator(payload):
    translation = list
    
    for key in payload.keys:
        
        if key == 'spectra':
            if len(payload[key].split(',')) > 1:
                translation.append('ion')
        if key == 'limits_type':
            if payload[key] == 0 and payload['unit'] == 0:
                translation.append('wavelength (\u212B)')
            elif payload[key] == 0 and payload['unit'] == 1:
                translation.append('wavelength (nm)')
            elif payload[key] == 0 and payload['unit'] == 2:
                translation.append('wavelength (\u03BCm)')
        if key == 'en_unit':
            if payload[key] == 0:
                translation.append(['E_i (cm\u207B\u00B9)', 'E_k (cm\u207B\u00B9)'])
            elif payload[key] == 1:
                translation.append(['E_i (eV)', 'E_k (eV)']) 
            elif payload[key] == 2:
                translation.append(['E_i (Ry)', 'E_k (Ry)'])   
        if key == 'unc_out':
            if payload[key] == 1:
                translation.append('Unc.') 
        
    
    
    