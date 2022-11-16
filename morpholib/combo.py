'''
Contains classes useful for making composite figures.
'''

import morpholib as morpho
import morpholib.anim
from morpholib.anim import Frame, SpaceFrame, MultiFigure, SpaceMultiFigure, \
    SpaceMultifigure, Spacemultifigure
from morpholib import object_hasattr
from morpholib.tools.basics import *

import math, cmath
import numpy as np

# NOT IMPLEMENTED YET
# Makes an array of figures.
class FigureGrid(Frame):
    def __init__(self, figure, shape):
        raise NotImplementedError
