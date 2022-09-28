'''
Various helper functions for dealing with cubic Bezier curves.
'''

# import math, cmath
import numpy as np
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

# Inverts the bezier function to find the parameter t value
# for a given 2d point z (as a complex number) that is
# assumed to be on the bezier curve.
#
# Returns all solutions found as a list.
# Usually the list will just contain a single solution,
# but it could contain two (self-intersecting curve)
# or none (given point not on the curve).
def invertBezier2d(p0, p1, p2, p3, z):
    # Calculate coefficients of the polynomial equation
    # bezier(t) - z = 0
    coeffs = np.array([
        p3 - 3*p2 + 3*p1 - p0,
        3*(p2 - 2*p1 + p0),
        3*(p1 - p0),
        p0 - z
        ])

    # Solve for the roots
    txlist = np.roots(coeffs.real).tolist()
    tylist = np.roots(coeffs.imag).tolist()

    # Filter out any common real roots
    tol = 1e-9
    solns = []
    for tx in txlist:
        # Skip the tx solutions that are obviously non-real
        if abs(tx.imag) > tol:
            continue
        for ty in tylist:
            if abs(tx - ty) < tol:
                solns.append(tx)

    return solns
