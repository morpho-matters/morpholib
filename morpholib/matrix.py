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
            isinstance(other, int) or isinstance(other, np.number):

            # Convert to 2D vector, compute matrix product, and
            # convert back to complex
            Z = np.array([other.real, other.imag])
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
        return self.array * other

    @property
    def T(self):
        return type(self)(self.array.T)

    @property
    def inv(self):
        return type(self)(np.linalg.inv(self.array))

    def __repr__(self):
        return repr(self.array)

    def __str__(self):
        return str(self.array)




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

mat = MAT = Mat  # Any case works.
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
