import morpholib as morpho

import math, cmath
import numpy as np
from bisect import bisect_right, bisect_left
from collections.abc import Iterable

### CONSTANTS ###
pi = math.pi
tau = 2*pi
oo = inf = float("inf")
nan = float("nan")
# Basic unit vectors for 3D animations
ihat = np.array([1,0,0], dtype=float); ihat.flags.writeable = False
jhat = np.array([0,1,0], dtype=float); jhat.flags.writeable = False
khat = np.array([0,0,1], dtype=float); khat.flags.writeable = False
# Basic matrices
I2 = np.eye(2); I2.flags.writeable = False
I3 = np.eye(3); I3.flags.writeable = False

### DECORATORS ###

# Decorator for functions that operate on a box.
# Allows such a function to accept a Figure type input
# whereby it will attempt to infer a box by calling the
# figure's `box()` method, assuming it exists.
# If given an Actor object, it will use the latest keyfigure.
def handleBoxTypecasting(func):
    def wrapper(box, *args, **kwargs):
        box = inferBox(box)
        return func(box, *args, **kwargs)
    return wrapper

### FUNCTIONS ###

isbadnum_old = lambda x: math.isnan(abs(x)*0)

# Detect infinite or nan (real or complex)
def isbadnum(x):
    return cmath.isnan(x) or cmath.isinf(x)

# isbadnum() but for np.arrays. Returns True if and only if
# nan or inf is found ANYWHERE in the array.
# Actually, this function should also work on scalars (both numpy
# and python builtins), so it can totally replace isbadnum().
# However, it might run slower than isbadnum() on python scalars,
# so I'm keeping the original isbadnum() around anyway.
def isbadarray(x):
    return (np.any(np.isnan(x)) or np.any(np.isinf(x))).tolist()

# isequal(a,b) does a == b, but works even if a and/or b is
# a numpy array.
def isequal(a, b, /):
    if isinstance(a, np.ndarray) and isinstance(b, np.ndarray):
        return np.array_equal(a,b)
    elif isinstance(a, np.ndarray) != isinstance(b, np.ndarray):
        return False
    else:
        try:
            return (a == b)
        except ValueError:
            return np.array_equal(a,b)

# Conversion factors between degrees and radians.
deg = tau/360
rad = 1/deg

# Real cotangent function
PI_OVER_2 = pi/2
def cot(theta):
    return math.tan(PI_OVER_2 - theta)

# Signum function. Returns x/abs(x) unless x = 0, in which case,
# return 0
def sgn(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0

# Constrains x to being in the interval [low, high].
# If x is above high, constrain() returns high.
# If x is below low, constrain() returns low.
# Equivalent to min(max(x,low), high)
def constrain(x, low, high):
    return min(max(x, low), high)
clamp = constrain  # Alternate name

# Computes the mean of a vector-like thing.
def mean(a):
    if len(a) == 0:
        raise IndexError("Can't take mean of an empty list-like object!")
    return sum(a)/len(a)

# Rounds a float x to an int if the float is sufficiently
# close to an int. By default, it rounds if x is within
# 1e-9 of an int.
def snapround(x, tol=1e-9):
    n = round(x)
    return n if abs(n-x) < tol else x

# Like round(), but truncates instead of rounding at the decimal digit you
# specify
def truncate(num, ndigits):
    decshift = 10**ndigits
    return int(num*decshift)/decshift

# Rounding function for complex numbers. Applies round() to the
# real and imaginary parts independently.
def cround(z, ndigits=None):
    return complex(round(z.real, ndigits), round(z.imag, ndigits))

def _rounder(x, roundfunc):
    # Convert to np.array if needed
    array = np.array(x) if not isinstance(x, np.ndarray) else x
    array = np.sign(array)*roundfunc(np.abs(array))
    array = np.array(array, dtype=int)  # Convert to int array
    if isinstance(x, np.ndarray):
        return array
    else:
        return array.tolist()

# Rounds the input away from zero.
# Supports lists and np.arrays as input.
#   roundOut(1.1) --> 2
#   roundOut(-1.1) --> -2
def roundOut(x):
    return _rounder(x, np.ceil)

# Rounds the input toward zero.
# Supports lists and np.arrays as input.
#   roundIn(1.9) --> 1
#   roundIn(-1.9) --> -1
def roundIn(x):
    return _rounder(x, np.floor)

# If a float is equal to an int, converts it into an int.
def squeezeFloat(number):
    try:
        integer = int(number)
    except OverflowError:
        return number
    except ValueError:
        return number

    if number == integer:
        return integer
    else:
        return number

flattenFloat = squeezeFloat

# Used in the spiral tween method.
# Computes the correct amount to shift an angle th1 so that it
# becomes th2 in the shortest possible path
# i.e. a path that does not traverse more than pi radians
# The value returned is called "dth" and should be used in
# expressions like this: th(t) = th1 + t*dth
# However, before using the above expression, make sure th1 and th2
# are modded 2pi.
# (Actually, maybe it's okay if they're not?)
def argShift(th1, th2):
    th1 = th1 % tau
    th2 = th2 % tau

    dth = th2 - th1
    if abs(dth) > pi + 1.189e-12:
        dth = dth - math.copysign(tau, dth)
    return dth

# Identical to argShift(), but works on np.arrays
def argShiftArray(th1, th2):
    th1 = th1 % tau
    th2 = th2 % tau

    dth = th2 - th1

    flagset = abs(dth) > pi + 1.189e-12
    subset = dth[flagset]
    dth[flagset] = subset - np.copysign(tau, subset)

    return dth

# Computes the total winding angle of a complex-valued function
# around the origin on a specified interval of its parameter.
# Divide the output of this function by 2pi to obtain the winding
# number.
#
# INPUTS
# f = Complex-valued function. Should be non-zero on the
#     closed interval given.
# a = Lowerbound of the input interval
# b = Upperbound of the input interval
# step = The step size to use when computing the angle sum.
#        It should be chosen so that the winding angle traveled
#        from any f(t) to f(t+step) is strictly less than pi radians.
def windingAngle(f, a, b, step):
    if b < a:
        return -windingAngle(f, b, a, step)

    length = b-a
    if length == 0:
        return 0
    # if step is None:
    #     step = length/10

    N = math.ceil(length/step)
    step = length/N
    angleSum = 0
    z0 = f(a)
    for n in range(1,N+1):
        z = f(a+n*step)
        angleSum += cmath.phase(z/z0)
        z0 = z

    return angleSum

# Given two points in the complex plane and the angle (in radians)
# of the circular arc that is supposed to go between them,
# returns the center point of the arc (as a complex number).
# Note that the angle is signed. Positive means the arc
# travels CCW from p to q.
# Also note that the angle cannot be 0 or a multiple of 2pi.
def arcCenter(p, q, angle):
    if angle % tau == 0:
        raise ValueError("Angle is 0 or a multiple of 2pi. Center point is undefined!")

    m = (p+q)/2  # midpoint
    return m + 1j*(m-p)*cot(angle/2)  # center point

# Array version of arcCenter()
def arcCenterArray(p, q, angle):
    if np.any(angle % tau == 0):
        raise ValueError("Angle is 0 or a multiple of 2pi. Center point is undefined!")

    m = (p+q)/2  # midpoint
    halfangle = angle/2
    return m + 1j*(m-p)*(np.cos(halfangle)/np.sin(halfangle))

# Converts a 2D tuple/list into a complex number
def vect2complex(v):
    return complex(*v)

# Converts a complex number into an ordered pair
# (z.real, z.imag)
def complex2vect(z):
    return (z.real, z.imag)
cparts = complex2vect  # Alias

# Given a sorted list of numbers a and value x,
# returns the highest index i such that a[i] <= x.
# If all the numbers in a are larger than x, it returns -1.
def listfloor(a, x):
    return bisect_right(a,x)-1

# Given a sorted list of numbers a and value x,
# returns the lowest index i such that a[i] >= x.
# If all the numbers in a are less than x, it returns len(a).
def listceil(a, x):
    if x in a:
        return a.index(x)
    else:
        return listfloor(a,x) + 1

# Returns a dictionary mapping indices to items representing a
# selection of items in a list. The `index` parameter can either
# be an index, a slice, a choice function, or a combination of
# these expressed as a tuple/iterable.
#
# One of the main features of this function is it won't return
# duplicates when the indices in a multi-selection overlap.
# And by using dicts, it is hopefully still a very speedy
# function.
def listselect(lst, index, /):
    if callable(index):
        condition = index
        return dict((i,item) for i,item in enumerate(lst) if condition(item))
    # Handle case of multiple index ranges provided
    elif isinstance(index, Iterable):
        pieces = index
        selection = dict()
        for piece in pieces:
            selection.update(listselect(lst, piece))
        return selection
    else:
        # Turn index into a slice if it's just a single int
        if isinstance(index, int):
            if index < 0:
                index = index % len(lst)
            index = sel[index:index+1]
        return dict(zip(range(len(lst))[index], lst[index]))

# Removes duplicate items in a sequence, keeping only the first
# occurrence of each item, and returns the result as a new list
# (the original sequence will not be modified).
#
# Optionally, a key function may be passed in to optional keyword
# input `key` which will apply the function once to each item in
# the sequence and use the results as the basis to remove duplicates.
#
# Assumes the items in the sequence (or their key function values)
# are hashable.
def removeDuplicates(seq, /, *, key=lambda item: item):
    d = dict()
    for item in seq:
        # Assign new key-value pair only if key(item) ISN'T
        # already in the dict.
        d.setdefault(key(item), item)
    return list(d.values())

# # If x is a float that is really an integer, returns int(x).
# # Otherwise, just returns back x unchanged.
# def flattenFloat(x):
#     if type(x) is float and x == int(x):
#         x = int(x)
#     return x

# Returns the functional composition of all the functions provided.
# e.g. Given compose(f,g,h), returns f o g o h = f(g(h(*)))
def compose(*funcs):
    if len(funcs) == 0:
        raise ValueError("No functions to compose!")
    def composition(*args, **kwargs):
        value = funcs[-1](*args, **kwargs)
        for n in range(len(funcs)-2,-1,-1):
            value = funcs[n](value)
        return value

    return composition

# Returns the functional composition of f with g: (f o g)
def compose2(f,g):
    return lambda *args, **kwargs: f(g(*args, **kwargs))


# Finds the roots of the polynomial defined as a list of
# coefficients in ascending order of degree.
# e.g. [-4, 0, 1] represents the polynomial -4 + x^2
# The answer is returned as a numpy array.
def polyroots(coeffs):
    polynom = np.polynomial.Polynomial(coeffs)
    return polynom.roots()


# Given a standard viewbox [xmin,xmax, ymin,ymax],
# returns the corners of the box as a list of complex numbers.
# Useful for passing into a Path or Polygon figure's seq or vertices.
# By default, it does so starting at the northwest corner and
# going counter-clockwise, but this can be modified by altering
# the "initCorner" and "CCW" parameters. By default:
# initCorner = "NW"
# CCW = True
@handleBoxTypecasting
def boxCorners(box, initCorner="NW", CCW=True):
    initCorner = initCorner.upper()
    dirs = ["NW", "SW", "SE", "NE"]
    if initCorner not in dirs:
        raise ValueError('initCorner must be "NW", "SW", "SE", or "NE".')

    left = box[0]
    right = box[1]
    bottom = box[2]
    top = box[3]

    corners = [left+1j*top, left+1j*bottom, right+1j*bottom, right+1j*top]

    # Reverse order if done clockwise
    if not CCW:
        corners = corners[::-1]
        dirs = dirs[::-1]

    # Find the index of the starting corner
    i = dirs.index(initCorner)

    # Order the corners according to the starting corner and direction
    corners = corners[i:] + corners[:i]

    return corners

# Computes the box 4-item list [xmin, xmax, ymin, ymax]
# given the positions of two of its opposite corners
# (specified as complex numbers).
def boxFromDiagonal(c1, c2, /):
    x1, y1 = c1.real, c1.imag
    x2, y2 = c2.real, c2.imag

    xmin = min(x1, x2)
    xmax = max(x1, x2)
    ymin = min(y1, y2)
    ymax = max(y1, y2)

    return [xmin, xmax, ymin, ymax]

# Pads a bounding box by the given pad amount.
# Usage: padbox(box, pad) -> paddedBox
# where `box` is a 4-tuple defining the bounding box in the format
#       [xmin, xmax, ymin, ymax]
# Optionally, a ypad value can be specified, allowing the box to be
# padded differently vertically vs horizontally:
#       padbox(box, xpad, ypad) -> paddedBox
@handleBoxTypecasting
def padbox(box, xpad, ypad=None, /):
    if ypad is None:
        ypad = xpad

    box = list(box)
    box[0] -= xpad
    box[1] += xpad
    box[2] -= ypad
    box[3] += ypad

    return box
padBox = padbox  # Alias

# Shifts a bounding box of the form [xmin,xmax,ymin,ymax]
# by the given 2d vector `shift` expressed as a complex number.
# Returns the modified box.
@handleBoxTypecasting
def shiftBox(box, shift):
    left, right, bottom, top = box
    # Adjust by origin
    left += shift.real
    right += shift.real
    bottom += shift.imag
    top += shift.imag
    return [left, right, bottom, top]

# Computes the total bounding box of a list of boxes.
def totalBox(boxes, pad=0):
    XMIN, YMIN, XMAX, YMAX = oo, oo, -oo, -oo
    for box in boxes:
        if isinstance(box, morpho.Actor):
            box = box.last().box()
        elif isinstance(box, morpho.Figure):
            box = box.box()
        xmin, xmax, ymin, ymax = box
        XMIN = min(XMIN, xmin)
        YMIN = min(YMIN, ymin)
        XMAX = max(XMAX, xmax)
        YMAX = max(YMAX, ymax)

    bigbox = [XMIN, XMAX, YMIN, YMAX]
    if isbadarray(bigbox):
        raise ValueError("Total box is unbounded or undefined.")

    return padbox(bigbox, pad)

# Attempts to infer the bounding box of an Actor or Figure.
# Given a figure, calls its box() method and returns the result.
# Given an Actor, calls the box() method of its latest keyfigure
# and returns the result.
# Otherwise returns the original input unchanged.
def inferBox(obj):
    if isinstance(obj, morpho.Actor):
        obj = obj.last()
    if isinstance(obj, morpho.Figure):
        if not hasattr(obj, "box"):
            raise TypeError(f"`{type(obj).__name__}` type figure does not support box() method.")
        box = obj.box()
    else:
        box = obj
    return box

# Converts minutes with seconds into just seconds.
# minsec(m,s) --> 60*m + s
#
# If given only a single decimal number as input, it treats
# it as (minutes).(seconds) and converts it to seconds.
# Example: minsec(2.05) --> 125 (within rounding error)
def minsec(mins, secs=None, /):
    if secs is None:
        value = mins
        mins = int(value)
        secs = (value-mins)/0.6 * 60
    return 60*mins + secs

# Concatenates several sequences into a single list.
# No underlying sequence is modified in the process.
def concat(*seqs):
    total = []
    for seq in seqs:
        total.extend(seq)
    return total

# Converts an iterable object into a list, but if it's not
# iterable, returns a singleton list containing the object.
def aslist(x, /):
    try:
        x = list(x)
    except TypeError:
        x = [x]
    return x

# Allows one to easily define a Python slice object
# using slice syntax.
# Example: sel[1:3] --> slice(1,3)
sel = np.s_
