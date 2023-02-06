'''
Various helper functions for dealing with cubic Bezier curves.
'''

# import math, cmath
import numpy as np

from morpholib.base import lerp0, bezierInterp
from morpholib.tools import polyroots

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
def invertBezier2d(p0, p1, p2, p3, z, *, tol=1e-9):
    if np.allclose([p0, p1, p2, p3], p0):
        raise ValueError("Cannot invert a constant Bezier curve!")

    # Calculate coefficients of the polynomial equation
    # bezier(t) - z = 0
    coeffs = np.array([
        p0 - z,
        3*(p1 - p0),
        3*(p2 - 2*p1 + p0),
        p3 - 3*p2 + 3*p1 - p0
        ])

    coeffs_x = coeffs.real
    coeffs_y = coeffs.imag

    verticalCurve = np.allclose(coeffs_x, 0)
    horizontalCurve = np.allclose(coeffs_y, 0)
    # If one of the coeff lists is zero
    # (meaning it's a horizontal or vertical curve),
    # rotate all points by 45 degrees and try again.
    if horizontalCurve or verticalCurve:
        p0 = (1+1j)*p0
        p1 = (1+1j)*p1
        p2 = (1+1j)*p2
        p3 = (1+1j)*p3
        z = (1+1j)*z
        return invertBezier2d(p0, p1, p2, p3, z)


    # Solve for the roots
    txlist = polyroots(coeffs.real).tolist()
    tylist = polyroots(coeffs.imag).tolist()

    # Filter out any common real roots
    solns = []
    for tx in txlist:
        # Skip the tx solutions that are obviously non-real
        # or are out of the range [0,1]
        if abs(tx.imag) > tol or not(0 <= tx.real <= 1):
            continue
        for ty in tylist:
            if abs(tx - ty) < tol:
                solns.append(tx)

    return solns

# NOT IMPLEMENTED YET.
# Converts a list of Catmull-Rom spline control points to their
# equivalent Bezier spline control points.
def CatmullRomToBezier(pts):
    raise NotImplementedError
    bezierPts = list(pts)
    for n in range(0, len(pts)-1, 3):
        p0, p1, p2, p3 = pts[n: n+4]
        bezierPts[n: n+4] = (p1, p1 + (p2-p0)/6, p2 - (p3-p1)/6, p2)
    return bezierPts

# Converts a quadratic Bezier curve into the equivalent cubic
# Bezier curve.
#
# INPUTS:
# q0,q1,q2 = Quadratic Bezier curve control points
#
# RETURNS:
# p0,p1,p2,p3 = Equivalent cubic Bezier curve control points
def quad2cubic(q0, q1, q2):
    p0 = q0
    p1 = q0 + (2/3)*(q1 - q0)
    p2 = q2 + (2/3)*(q1 - q2)
    p3 = q2
    return (p0, p1, p2, p3)

# NOT IMPLEMENTED BECAUSE OF UNRESOLVED BUG
# Returns the tight bounding box of a cubic Bezier curve.
def cubicbox(p0, p1, p2, p3):
    raise NotImplementedError

    import svgelements as se
    xmin, ymin, xmax, ymax = np.array(se.CubicBezier(p0, p1, p2, p3).bbox()).tolist()
    return [xmin, xmax, ymin, ymax]
