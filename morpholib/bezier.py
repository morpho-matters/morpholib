'''
Various helper functions for dealing with cubic Bezier curves.
'''

# import math, cmath
# import numpy as np
from morpholib.base import lerp0, bezierInterp

# Splits the cubic Bezier curve described by p0...p3 at the
# parameter value t (in interval [0,1]), and returns the control
# points describing the first sub-Bezier curve: the part of the
# curve for lower parameter values than t.
def bezierFirstSlice(p0, p1, p2, p3, t):
    p01 = lerp0(p0, p1, t)
    p12 = lerp0(p1, p2, t)
    p012 = lerp0(p01, p12, t)
    p0123 = bezierInterp(p0, p1, p2, p3, t)

    return (p0, p01, p012, p0123)

# Splits the cubic Bezier curve described by p0...p3 at the
# parameter value t (in interval [0,1]), and returns the control
# points describing the last sub-Bezier curve: the part of the
# curve for higher parameter values than t.
def bezierLastSlice(p0, p1, p2, p3, t):
    return bezierFirstSlice(p3, p2, p1, p0, 1-t)[::-1]
bezierSecondSlice = bezierLastSlice

# Splits the cubic Bezier curve described by p0...p3 at the
# parameter value t (in interval [0,1]), and returns two 4-tuples
# of control points describing the two sub-Bezier curves on either
# side.
def splitBezier(p0, p1, p2, p3, t):
    slice1 = bezierFirstSlice(p0, p1, p2, p3, t)
    slice2 = bezierLastSlice(p0, p1, p2, p3, t)
    return slice1, slice2
