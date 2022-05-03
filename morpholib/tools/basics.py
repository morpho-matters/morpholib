import math, cmath
import numpy as np
from bisect import bisect_right, bisect_left

### CONSTANTS ###
pi = math.pi
tau = 2*pi
oo = inf = float("inf")
nan = float("nan")


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

# Computes the mean of a vector-like thing.
def mean(a):
    if len(a) == 0:
        raise IndexError("Can't take mean of an empty list-like object!")
    return sum(a)/len(a)

# Like round(), but truncates instead of rounding at the decimal digit you
# specify
def truncate(num, ndigits):
    decshift = 10**ndigits
    return int(num*decshift)/decshift

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
    return v[0] + 1j*v[1]

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

# Given a standard viewbox [xmin,xmax, ymin,ymax],
# returns the corners of the box as a list of complex numbers.
# Useful for passing into a Path or Polygon figure's seq or vertices.
# By default, it does so starting at the northwest corner and
# going counter-clockwise, but this can be modified by altering
# the "initCorner" and "CCW" parameters. By default:
# initCorner = "NW"
# CCW = True
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
