# -*- coding: utf-8 -*-#
"""
Created on Mon Apr 30 12:20:27 2018

@author: Pedro

Useful extra functions
"""

import numpy as np
import math
import itertools
import copy
from functools import wraps
import logging, time

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

def iterator_is_empty(iterator):
    iterator_copy = copy.copy(iterator)
    try:
        next(iterator_copy)
    except StopIteration:
        return True
    else:
        #iterator_copy = itertools.chain([first], iterator)
        return False 
    
def is_sorted(x, key = lambda x: x):
    return all([key(x[i]) <= key(x[i + 1]) for i in range(len(x) - 1)])
    
def find_nearest(array, value):
    array = np.asarray(array)
    
    if is_sorted(array):
        idx = np.searchsorted(array, value, side="left")
        if idx > 0 and (idx == len(array) or 
            math.fabs(value - array[idx - 1]) < math.fabs(value - array[idx])):
                return array[idx - 1]
        else:
                return array[idx]
    else:    
        idx = (np.abs(array - value)).argmin()
        return array[idx - 1]
    
def slice_by_nearest(data, interval):
    a = find_nearest(data.index, interval[0])
    b = find_nearest(data.index, interval[1])
    return data[a:b]

def timing(func):
    """This decorator prints the execution time for the decorated function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logging.debug("{} ran in {}s".format(
                func.__name__, round(end - start, 2)
                ))
        return result
    return wrapper
    