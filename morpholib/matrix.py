'''
This module contains various matrix tools.
It implements a 2x2 matrix class so that linear
transformations can also be animated.
Also contains helper functions for creating rotation/orientation
matrices.
'''


import math
import numpy as np

tol = 1.0e-9
tau = 2*math.pi

# # Special 2x2 matrix class for Morpho which can handle
# # multiplication on a complex number by treating it as
# # a 2D column vector.
# class _Mat_old(np.matrix):

#     def __mul__(self, other):
#         if type(other) is _Mat_old:
#             # Use the superclass to compute the matrix product
#             return np.matrix.__mul__(self, other)
#         else:
#             Z = np.matrix([[other.real], [other.imag]])
#             prod = np.matrix.__mul__(self, Z)
#             return float(prod[0,0]) + float(prod[1,0])*1j

#     # Convenience function: returns inverse of the mat
#     @property
#     def inv(self):
#         return self**(-1)

# Special 2x2 matrix class for Morpho which can handle
# multiplication on a complex number by treating it as
# a 2D column vector.
class Mat(object):
    def __init__(self, x1=0, x2=0, y1=0, y2=0):
        if isinstance(x1, list) or isinstance(x1, tuple) or \
            isinstance(x1, np.ndarray):

            array = np.array(x1, dtype=float)
        else:
            array = np.array([[x1,x2],[y1,y2]], dtype=float)
        self.array = array

    def __mul__(self, other):
        # If given a scalar, treat it as a 2D vector and do
        # matrix multiplication
        if isinstance(other, complex) or isinstance(other, float) or \
            isinstance(other, int) or isinstance(other, np.number) or \
            (isinstance(other, np.ndarray) and other.size == 1):

            # Convert to 2D vector, compute matrix product, and
            # convert back to complex
            Z = np.array([other.real, other.imag]).squeeze()
            prod = (self.array @ Z).tolist()
            return prod[0] + 1j*prod[1]

        # If given another matrix, do matrix multiplication directly
        # on the underlying arrays.
        elif isinstance(other, type(self)):
            return type(self)(self.array @ other.array)

        # Otherwise, use regular multiplication
        else:
            return self.array * other

    def __rmul__(self, other):
        return type(self)(self.array * other)

    @property
    def T(self):
        return type(self)(self.array.T)

    @property
    def inv(self):
        return type(self)(np.linalg.inv(self.array))

    def __repr__(self):
        prefix = type(self).__name__ + "("
        rep = repr(self.array)
        lines = rep.split("\n")
        lines[0] = prefix + lines[0]
        for n in range(1, len(lines)):
            lines[n] = " "*len(prefix) + lines[n]
        lines[-1] += ")"
        return "\n".join(lines)

    def __str__(self):
        return str(self.array)

mat = MAT = Mat  # Any case works.


# # Converts a numpy matrix into a Morpho _Mat
# # (Maybe unnecessary! numpy.matrix handles this somehow!)
# def matrix2Mat(matrix):
#     return Mat(matrix[0,0], matrix[0,1], matrix[1,0], matrix[1,1])

# # This is the ACTUAL constructor for the 2x2 matrix class _Mat_old.
# # Overriding the inherited __init__ from np.matrix turned out
# # to be more complicated than I thought, so this was a workaround.
# def Mat_old(x1=0, x2=0, y1=0, y2=0):
#     return _Mat_old([[x1, x2], [y1, y2]], dtype=float)


# Extracts the upper-left 2x2 submatrix of the given numpy matrix
# and returns it as a morpho Mat.
# Geometrically, this converts a 3D matrix transformation into the
# equivalent 2x2 transformation resulting from treating (x,y) as
# (x,y,0), performing the 3D transformation to it, and then
# flattening it back onto the xy-plane.
def flatten(npMat):
    return Mat(npMat[0,0], npMat[0,1], npMat[1,0], npMat[1,1])

# Returns numpy matrix that encodes a 3D rotation of
# theta radians about the vector u according to the right hand rule.
# If theta is unspecified, the magnitude of the u-vector is used.
def rotation(u, theta=None):
    # Type check the unit vector
    if type(u) not in (list, tuple, np.ndarray, np.matrix):
        raise TypeError("u must be list, tuple, numpy array or numpy matrix.")

    # Convert to np.array and append trailing zeros if needed
    new_u = np.zeros(3)
    new_u[:len(u)] = u
    u = new_u

    # Infer theta from magnitude of u if unspecified
    if theta is None:
        theta = np.linalg.norm(u)

    # Throw error if u is the zero vector AND theta is non-zero (mod tau)
    # If u = 0 AND theta = 0 (mod tau), then interpret this as the
    # identity rotation and return the identity matrix.
    if np.allclose(u, 0):
        if abs(theta % tau) < tol:
            return np.identity(3)
        else:
            raise ValueError("u must be a non-zero 3D vector")

    # Convert to unit vector
    u = u / np.linalg.norm(u)
    x,y,z = u

    # Compute useful constants
    c = math.cos(theta)
    c_c = 1 - c  # Complement of c
    s = math.sin(theta)

    # Return rotation matrix as numpy array
    return np.array([
        [c+x*x*c_c,   x*y*c_c-z*s,   x*z*c_c+y*s],
        [y*x*c_c+z*s, c+y*y*c_c,     y*z*c_c-x*s],
        [z*x*c_c-y*s, z*y*c_c+x*s,   c+z*z*c_c]
        ], dtype=float)


# Returns pair (u, theta) characterizing the rotation matrix mat.
# u is a unit vector and theta is the rotation angle according to the
# right hand rule.
# Note: This function assumes mat is a rotation matrix. It may behave
# unpredictably if given a non-rotation matrix.
def rotationVector(mat):
    R = np.array(mat, dtype=float)
    A = (R-R.T)/2
    rho = np.array([A[2,1], A[0,2], A[1,0]], dtype=float)
    s = np.linalg.norm(rho)
    c = (R.trace() - 1)/2
    if abs(s) < tol:
        if abs(c-1) < tol:
            return (np.array([1,0,0], dtype=float), 0)
        else:
            mat = R + np.identity(3)
            for j in range(3):
                v = mat[:,j]
                if not np.allclose(v, 0):
                    break
            return (v/np.linalg.norm(v), math.pi)

    return (rho/s, math.atan2(s,c))

# Returns the wedge product as a skew-symmetric matrix.
# That is, returns outer(u,v) - outer(v,u)
def wedge(u, v):
    outprod = np.outer(u,v)
    return outprod - outprod.T

# Returns the tilt product of u and v.
# That is, returns outer(v,u) - outer(u,v)
# or equivalently: wedge(v,u)
def tilt(u, v):
    return wedge(v,u)

# Given two N-dimensional vectors u,v and an angle theta,
# returns the rotation matrix that rotates theta radians in the
# direction from u toward v.
#
# If theta is unspecified, it defaults to the angle between u and v.
#
# Optionally the keyword `orthonormal=True` may be passed in to
# tell the function to assume u and v are orthogonal unit vectors,
# thus bypassing an unneccessary initial computation.
def rotationNd(u, v, theta=None, *, orthonormal=False):
    if theta is None:
        # Normalize u,v
        unorm = np.linalg.norm(u)
        vnorm = np.linalg.norm(v)
        if unorm == 0 or vnorm == 0:
            raise ZeroDivisionError("u and v must be non-zero vectors.")
        u = u / unorm
        v = v / vnorm

        G = tilt(u,v)
        return np.eye(*G.shape) + G + (G@G)/(1+(u@v))

    G = tilt(u,v)
    if not orthonormal:
        mag = np.sqrt((u@u)*(v@v) - (u @ v)**2)  # ||u tilt v||_2
        G = G / mag

    # Apply General Euler's Formula
    return np.eye(*G.shape) + G*np.sin(theta) + (G@G)*(1-np.cos(theta))

# Returns the 2D rotation matrix associated with the
# input angle.
def rotation2d(angle):
    c = math.cos(angle)
    s = math.sin(angle)

    return np.array([[c, -s], [s, c]], dtype=float)

# Tweens two 3D rotation matrices (orient matrices).
def orientTween(A, B, t, start=0, end=1):
    # If A and B are basically equal, just return a copy of A.
    if np.allclose(A, B):
        return A.copy()

    return orientTween1(A, B, t, start, end)


# Functionally equivalent to orientTween(), but doesn't check
# if A and B are close before applying the tween. This function
# can slightly speed up the code if you know in advance that
# A and B are meaningfully different from each other.
def orientTween1(A, B, t, start=0, end=1):
    # Delta matrix is the rotation needed to turn self.orient into
    # other.orient
    # delta = np.linalg.inv(self.orient) @ other.orient
    delta = B @ A.T  # Transpose is inverse for rotation mats

    # Compute rotation vector for delta
    u, theta = rotationVector(delta)

    # Normalize t if start and end are different from default.
    if not(start == 0 and end == 1):
        t = (t - start)/(end - start)
    return rotation(u, theta*t) @ A


# Returns the 2D scaling matrix associated with the input
# scale factor. Optionally, two scale factors can be
# inputted, (horizontal scale, vertical scale)
def scale2d(x, y=None):
    if y is None:
        y = x
    return np.array([[x, 0], [0, y]], dtype=float)


# Given a vector-like thing (tuple, list, complex number, np.array),
# converts a copy of it into a np.array with dtype=float.
# If given an np.array that is already dtype=float, does nothing
# and returns the original np.array uncopied.
# Note: if given a complex number, returns a 3-vector with z = 0.
def array(v):
    if isinstance(v, np.ndarray):
        if v.dtype is np.dtype(float):
            return v
        else:
            return np.array(v, dtype=float)
    elif isinstance(v, list) or isinstance(v, tuple):
        return np.array(v, dtype=float)
    elif type(v) in (int, float, complex):
        return np.array([v.real, v.imag, 0], dtype=float)
    else:
        raise TypeError("Unable to convert given vector-like object to np.array!")

# Given a vector-like thing in Morpho like a tuple, list,
# or complex number, converts it into a numpy 3-vector
# (i.e. np.array with 3 items).
# Interprets complex numbers as 2d vectors [x,y]
def vector3d(v):
    if type(v) in (complex, float, int):
        v = np.array([v.real, v.imag, 0], dtype=float)
    # if isinstance(v, list) or isinstance(v, tuple):
    else:
        # v = np.array(v, dtype=float)
        # Convert to np.array and append trailing zeros if needed
        new_v = np.zeros(3)
        new_v[:len(v)] = v
        v = new_v

    return v

# An extension of numpy.interp() that can handle fp as a list
# of vectors instead of a list of scalars. However, I believe
# scipy.interp1() fulfills this role, so this function will
# probably be obsolete if/when scipy is ever added as a
# dependency to Morpho.
#
# Note: the individual vectors in fp should not have a very
# large number of components. This function is designed for
# relatively low-dimension fp vectors.
def interpVectors(x, xp, fp, left=None, right=None):
    try:
        ndim = len(fp[0])
        isvector = True
    except TypeError:
        isvector = False

    if isvector:
        fmat = np.array(fp) if not isinstance(fp, np.ndarray) else fp
        interpMat = np.zeros((len(x), ndim))
        for j in range(ndim):
            interpMat[:,j] = np.interp(x, xp, fmat[:,j], left=left, right=right)
        return interpMat
    else:
        return np.interp(x, xp, fp, left=left, right=right)

def positionArray(domain, res):
    xmin, xmax, ymin, ymax = domain
    xres, yres = res
    if xres < 2 or yres < 2:
        raise ValueError("Resolution values must be > 1")
    dx = (xmax-xmin)/(xres-1) # if xres > 1 else (xmax-xmin)
    dy = (ymax-ymin)/(yres-1) # if yres > 1 else (ymax-ymin)

    # Note: I think you could also have implemented this by
    # adding a column linspace to a row linspace. Numpy broadcasting
    # would (I think) result in this creating a cartesian addition
    # of the two. Something to consider if you ever want to change
    # this implementation.
    array = np.mgrid[xmin:xmax+dx/2:dx, ymin:ymax+dy/2:dy]
    zarray = array[0] + 1j*array[1]
    return zarray

# Opposite of array(). Takes an iterable and converts it to a
# standard python list of python floats. Useful for turning
# numpy arrays back into native python types.
# NOTE: This function has been mostly obsoleted since np.arrays
# have a tolist() method that basically does this.
def floatlist(v):
    return [float(item) for item in v]

# Like floatlist(), but turns all items into complex type.
# NOTE: This function has been mostly obsoleted since np.arrays
# have a tolist() method that basically does this.
def complexlist(v):
    return [complex(item) for item in v]

# Like floatlist(), but turns all items into ints via int().
# NOTE: This function has been mostly obsoleted since np.arrays
# have a tolist() method that basically does this.
def intlist(v):
    return [int(item) for item in v]

# Like intlist(), but rounds instead of floors.
# Optionally specify ndigits (same optional arg that round() takes)
# NOTE: This function has been mostly obsoleted since np.arrays
# have a tolist() method that basically does this.
def roundlist(v, ndigits=None):
    return [int(round(item, ndigits)) for item in v]

### VARIOUS OTHER CONSTANTS AND FUNCTIONS ###

det = lambda M: np.linalg.det(M)  # For mats only

# Returns a measure of how "thin" the matrix transformation is.
# What it actually does is takes the unit square, applies M to it,
# and then computes the height of the parallelogram the unit square
# turns in to, where the base of the parallelogram is taken to be
# its longest edge.
# This function is only designed to work for 2x2 matrices.
def thinHeight2x2(M):
    det = np.linalg.det(M)
    if det == 0:
        return 0
    else:
        return abs(det/max(np.linalg.norm(M[:,0]), np.linalg.norm(M[:,1])))

# Returns a relative measure of how "thin" the matrix transformation is.
# A number in the range [0,1].
# It applies the matrix M to the unit square, and then returns the ratio
# of the resulting parallelogram's height to its width, where "width"
# is taken to mean the parallelogram's longest side length.
def thinness2x2(M):
    det = np.linalg.det(M)
    if det == 0:
        return 0
    else:
        return abs(det/max(np.linalg.norm(M[:,0]), np.linalg.norm(M[:,1]))**2)
