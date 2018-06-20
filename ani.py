#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jun 20 16:32:01 2018

@author: pedro
"""

import requests
from bs4 import BeautifulSoup

URL = r'https://physics.nist.gov/PhysRefData/ASD/levels_form.html?'
payload = dict(
            spectrum = 'Ca II',
            conf_out = 0,
            term_out = 0,
            level_out = 0,
            unc_out = 0,
            j_out = 0,
            lande_out = 0,
            perc_out = 0,
            biblio = 0,
            splitting = 0,
            temp = 0.6
        )

session = requests.session()
r = requests.post(URL, data=payload)

page = BeautifulSoup(r.text)
txt = page.findall('p')