# -*- coding: utf-8 -*-#
"""
Created on Mon Apr 30 12:20:27 2018

@author: Pedro

Useful extra functions
"""

import numpy as np

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

def magnitude(number):
    return int( np.floor( np.log10( number )) )

def intersection(A, B):
    return [x for x in A if x in B]