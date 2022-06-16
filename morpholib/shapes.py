
import morpholib as morpho
import morpholib.tools.color, morpholib.grid, morpholib.matrix
from morpholib.tools.basics import *
from morpholib.matrix import mat

# Polygon and SpacePolygon can be accessed from the shapes
# submodule as well as grid.
from morpholib.grid import Polygon, SpacePolygon, Spacepolygon

import cairo
cr = cairo

import math, cmath
import numpy as np

I2 = np.identity(2)


# Decorator modifies the tween methods of the Spline class to support
# tweening between splines with different node counts.
def handleSplineNodeInterp(tweenmethod):
    def wrapper(self, other, t, *args, **kwargs):
        len_self = self.length()
        len_other = other.length()

        # Use standard tween if node counts are the same
        if len_self == len_other:
            return tweenmethod(self, other, t, *args, **kwargs)

        # Otherwise, do some interpolation!

        # If either self or other have no nodes, give up, throw error
        if len_self == 0 or len_other == 0:
            raise ValueError("Can't interpolate between empty path and non-empty path!")

        # If self has more nodes than other, artifically insert
        # nodes into a copy of other before tweening
        if len_self > len_other:
            othercopy = other.copy()
            othercopy.insertNodes(len_self - len_other)
            # other.seq = insertNodesUniformlyTo(other.seq, len_self-len_other)
            return tweenmethod(self, othercopy, t, *args, **kwargs)
        # Else other has more nodes, so insert extra nodes to a
        # copy of self before tweening
        else:
            selfcopy = self.copy()
            selfcopy.insertNodes(len_other - len_self)
            # selfcopy.seq = insertNodesUniformlyTo(selfcopy.seq, len_other-len_self)
            # return super(Path, selfcopy).tweenLinear(other, t)
            return tweenmethod(selfcopy, other, t, *args, **kwargs)

    return wrapper

# Cubic Bezier Spline figure.
# Each node of the spline has three associated components:
# node position, inhandle position, outhandle position.
# where "inhandle" and "outhandle" refer to the two tangent
# control points associated with any node. "inhandle" means the handle
# that controls the curve's trajectory entering the node, and "outhandle"
# controls the curve's trajectory when exiting the node.
# See node(), inhandle(), and outhandle() for more info.
#
# inhandles and outhandles can also take on infinite values, in which
# case they are interpreted as being reflections of their counterpart
# handle. This allows two handles to be linked together, where one
# handle is implicitly controlled by the other. For example,
# inhandle = inf means its position is implicitly taken to be the
# reflection of the corresponding outhandle position about the node's
# position. If both inhandle AND outhandle are infinite, they are
# implicitly treated as if they coincide with the node position.
# NOTE: Values must be an infinite type! nans do not work and may
# break certain aspects of the Spline class!
#
# TWEENABLES
# data = Complex-valued matrix where rows index the nodes of the spline
#        and columns index the control point type:
#        (node, inhandle, outhandle)
#        This is not usually set directly. Instead use the methods
#        node(), inhandle(), outhandle(), etc. to define these.
#        Default: None (empty matrix)
# start = Initial draw point; a number between 0 and 1 where 0 is
#         the initial node and 1 is the final node.
# end = Final draw point; a number between 0 and 1 where 0 is
#       the initial node and 1 is the final node.
# color = Spline color (RGB vector-like). Default: (1,1,1) (white)
# alpha = Opacity. Default: 1 (opaque)
# width = Spline stroke thickness (in pixels). Default: 3
# alphaEdge = Path opacity independent of fill. Default: 1 (opaque)
# fill = Interior fill color (RGB vector-like). Default: [1,0,0] (red)
# alphaFill = Interior opacity. Default: 0 (invisible)
# dash = Dash pattern. Works exactly like how it does in cairo. It's a list
#        of ints which are traversed cyclically and will alternatingly indicate
#        number of pixels of visibility and invisibility.
# origin = Translation value (complex number). Default: 0 (complex number).
# rotation = Path rotation about origin point (radians). Default: 0
# transform = Transformation matrix applied after all else. Default: np.eye(2)
#
# OTHER ATTRIBUTES
# deadends = Set of ints specifying indices of seq that are "deadends". Meaning
#            no line segment will be drawn from the deadend index to the next index.
#            This is mainly used under the hood by helper functions like mathgrid()
#            to speed up rendering.
# showTangents = Boolean indicating whether to draw tangent line segments
#                at the node points of the spline. This is mainly for
#                debugging use while creating an animation.
#                Final animations should usually have showTangents = False.
#                By default, showTangents = False
class Spline(morpho.Figure):

    def __init__(self, data=None, width=3, color=(1,1,1), alpha=1):
        if data is None:
            # data = np.array([
            #     [0,-1j,oo],
            #     [1,1+1j,oo]
            #     ], dtype=complex)
            data = np.array([], dtype=complex)

        morpho.Figure.__init__(self)

        _data = morpho.Tweenable(name="_data", value=np.array(data, dtype=complex), tags=["nparray"])
        start = morpho.Tweenable(name="start", value=0, tags=["scalar"])
        end = morpho.Tweenable(name="end", value=1, tags=["scalar"])
        color = morpho.Tweenable(name="color", value=color, tags=["color"])
        alphaEdge = morpho.Tweenable(name="alphaEdge", value=1, tags=["scalar"])
        fill = morpho.Tweenable(name="fill", value=[1,0,0], tags=["color", "gradientfill", "nolinear", "nospiral"])
        alphaFill = morpho.Tweenable(name="alphaFill", value=0, tags=["scalar"])
        alpha = morpho.Tweenable(name="alpha", value=alpha, tags=["scalar"])
        width = morpho.Tweenable(name="width", value=width, tags=["size"])
        dash = morpho.Tweenable("dash", [], tags=["scalar", "list"])
        # headSize = morpho.Tweenable("headSize", 0, tags=["scalar"])
        # tailSize = morpho.Tweenable("tailSize", 0, tags=["scalar"])
        # outlineWidth = morpho.Tweenable("outlineWidth", value=0, tags=["size"])
        # outlineColor = morpho.Tweenable("outlineColor", value=[0,0,0], tags=["color"])
        # outlineAlpha = morpho.Tweenable("outlineAlpha", value=1, tags=["scalar"])
        origin = morpho.Tweenable("origin", value=0, tags=["complex", "nofimage"])
        rotation = morpho.Tweenable("rotation", value=0, tags=["scalar"])
        _transform = morpho.Tweenable("_transform", np.identity(2), tags=["nparray"])

        self.update([_data, start, end, color, alphaEdge, fill, alphaFill, alpha,
            width, dash, origin, rotation, _transform]
            )


        # The dash pattern for this line. The format is identical to how
        # pycairo handles dash patterns: each item in the list is how long
        # ON and OFF dashes are, where the list is read cyclically.
        # Defaults to [] which means make the line solid.
        # Note that specifying only one value to the dash list is interpreted
        # as alternating that dash width ON and OFF.
        # Also note that dash pattern is ignored if gradient colors are used.
        # self.dash = []

        # Set of indices that represent where a path should terminate.
        self.deadends = set()

        # Boolean indicates whether the control point tangents
        # should be shown. This is mainly for debugging purposes.
        self.showTangents = False


    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = np.array(value, dtype=complex)


    @property
    def transform(self):
        return self._transform

    @transform.setter
    def transform(self, value):
        self._transform = morpho.matrix.array(value)


    def copy(self):
        new = super().copy()
        # new.dash = self.dash.copy() if "copy" in dir(self.dash) else self.dash
        new.deadends = self.deadends.copy()
        new.showTangents = self.showTangents

        return new

    # Returns the node count of the spline
    def length(self):
        return self.data.shape[0]

    # Returns or sets the position of the node of given index.
    # Usage: myspline.node(n) -> position of nth node
    #        myspline.node(n, value) sets nth node position to value
    def node(self, index, value=None):
        if value is None:
            return self.data[index, 0].tolist()
        self.data[index, 0] = value
        return self

    # Returns or sets the position of the inward handle
    # of the node at the given index (see node() for more info).
    # Input and output values of this method are in absolute
    # physical coordinates of the plane (as a complex number).
    # See also: inhandleRel().
    #
    # If optional "raw" is set to True, the values are ripped
    # straight from the data array, including inf values;
    # but if set to False, it computes the current position
    # inf corresponds to.
    def inhandle(self, index, value=None, raw=False):
        if value is None:
            if raw:
                return self.data[index, 1].tolist()
            else:
                p, pin, pout = self.data[index,:].tolist()
                pin, pout = replaceInfHandles(p, pin, pout)
                return pin
        # Convert to oo given any non-finite value
        if isbadnum(value):
            value = oo
        self.data[index, 1] = value
        return self

    # Returns or sets the position of the outward handle
    # of the node at the given index (see node() for more info).
    # Input and output values of this method are in absolute
    # physical coordinates of the plane (as a complex number).
    # See also: outhandleRel().
    #
    # If optional "raw" is set to True, the values are ripped
    # straight from the data array, including inf values;
    # but if set to False, it computes the current position
    # inf corresponds to.
    def outhandle(self, index, value=None, raw=False):
        if value is None:
            if raw:
                return self.data[index, 2].tolist()
            else:
                p, pin, pout = self.data[index,:].tolist()
                pin, pout = replaceInfHandles(p, pin, pout)
                return pout
        # Convert to oo given any non-finite value
        if isbadnum(value):
            value = oo
        self.data[index, 2] = value
        return self

    # Returns (node, inhandle, and outhandle) of given index.
    # Equivalent to extracting a row of the data array, but
    # converts any inf handle values into their current corresponding
    # positions like how inhandle() and outhandle() would output
    # by default.
    # Optionally set argument raw=True to make it actually return
    # just a raw copy of a given row of the data array
    # (converted into python list).
    def nodeData(self, index, raw=False):
        # p = self.node(index)
        # pin = self.inhandle(index)
        # pout = self.outhandle(index)

        p, pin, pout = self._data[index,:].tolist()
        if not raw:
            pin, pout = replaceInfHandles(p, pin, pout)

        return [p, pin, pout]

    # Returns or sets the position of the inward handle
    # of the node at the given index relative to the node position.
    # See also: inhandle()
    # Equivalent names for this method:
    # inhandlerelative, inhandleRel, inhandlerel
    #
    # If optional "raw" is set to True, the values are ripped
    # straight from the data array, including inf values;
    # but if set to False, it computes the current position
    # inf corresponds to.
    def inhandleRel(self, index, value=None, raw=False):
        if value is None:
            return self.inhandle(index, value, raw) - self.node(index)
        # Convert to oo given any non-finite value
        if isbadnum(value):
            value = oo
        self.data[index, 1] = self.data[index, 0] + value
        return self

    # inhandlerel = inhandleRel = inhandlerelative = inhandleRelative

    # Returns or sets the position of the outward handle
    # of the node at the given index relative to the node position.
    # See also: outhandle()
    # Equivalent names for this method:
    # outhandlerelative, outhandleRel, outhandlerel
    #
    # If optional "raw" is set to True, the values are ripped
    # straight from the data array, including inf values;
    # but if set to False, it computes the current position
    # inf corresponds to.
    def outhandleRel(self, index, value=None, raw=False):
        if value is None:
            return self.outhandle(index, value, raw) - self.node(index)
            # return (self.data[index,2] - self.data[index,0]).tolist()
        # Convert to oo given any non-finite value
        if isbadnum(value):
            value = oo
        self.data[index, 2] = self.data[index, 0] + value
        return self

    # outhandlerel = outhandleRel = outhandlerelative = outhandleRelative


    # Creates a new node at the specified point.
    # Optionally also specify inhandle and outhandle which default to inf.
    # Also optionally specify where to insert the node in the sequence.
    # By default, places it after the current final node.
    def newNode(self, point, inhandle=oo, outhandle=oo, beforeIndex=oo):
        beforeIndex = min(beforeIndex, self.length())
        if beforeIndex < 0:
            beforeIndex = beforeIndex % self.length()

        if self.length() == 0:
            self._data = np.array([[point, inhandle, outhandle]], dtype=complex)
        else:
            # self._data = np.vstack((self.data, [point,inhandle,outhandle]))
            self._data = np.insert(self.data, beforeIndex, [point,inhandle,outhandle], axis=0)
        return self

    # Deletes the node at the specified index. The dangling nodes on
    # either side will then be connected assuming they aren't prevented
    # by deadends.
    # NOTE: Calling delNode() will NOT update the deadends attribute!
    def delNode(self, index):
        self._data = np.delete(self._data, index, axis=0)
        return self


    # Closes the path IN PLACE if it is not already closed.
    def close(self):
        if self.length() < 2 or self.node(0) == self.node(1):
            return self
        self._data = np.insert(self._data, self.length(), self._data[0].copy(), axis=0)
        return self


    # Returns the interpolated position along the path corresponding to the
    # parameter t, where t = 0 is the path start and t = 1 is the path end.
    # NOTE: This method ignores deadends and the transformation tweenables
    # origin, rotation, transform.
    def positionAt(self, t):
        length = self.length()
        if length < 2:
            raise IndexError("Spline must have at least 2 nodes!")
        segCount = length - 1
        T = t*segCount  # Global parameter value

        # Round to nearest node if within a billionth of it.
        tol = 1e-9
        if abs(T - round(T)) < tol:
            T = round(T)
            return self.node(T)

        index = int(T)  # Latest preceding node index
        param = T - index  # Local parameter value

        p0 = self.node(index)
        p1 = self.outhandle(index)
        p2 = self.inhandle(index+1)
        p3 = self.node(index+1)
        return morpho.bezierInterp(p0, p1, p2, p3, param)

    # Splits the spline at the parameter t (ranging from 0 to 1)
    # by inserting a new node at whatever point t corresponds to,
    # and auto-adjusting the handles of the adjacent nodes so that
    # the spline's shape is unchanged.
    # If optional "force" set to True, this method will split
    # the spline even at a node point. By default: force=False.
    def splitAt(self, t, force=False):
        segCount = self.length() - 1
        I = t*segCount  # Index value (possibly non-int)
        self.splitAtIndex(I, force=force)
        return self

        # length = self.length()
        # if length < 2:
        #     raise IndexError("Spline must have at least 2 nodes!")
        # segCount = length - 1
        # T = t*segCount  # Global parameter value

        # # Round to nearest node if within a billionth of it.
        # tol = 1e-9
        # if abs(T - round(T)) < tol:
        #     if force:
        #         T = round(T)
        #     else:
        #         # Do nothing if asked to split at a node point
        #         # and we're not forcing a split.
        #         return

        # index = int(T)  # Latest preceding node index
        # param = T - index  # Local parameter value
        # p0 = self.node(index)
        # p1 = self.outhandle(index)
        # p2 = self.inhandle(index+1)
        # p3 = self.node(index+1)
        # slice1, slice2 = morpho.bezier.splitBezier(p0, p1, p2, p3, param)

        # # Commit the handles of index and index+1 to ensure seamlessness
        # self.commitHandles(index, index+1)

        # # Modify starting and ending handles
        # self.outhandle(index, slice1[1])
        # self.inhandle(index+1, slice2[2])

        # # Define new node
        # p = slice2[0]
        # pin = slice1[2]
        # pout = slice2[1]

        # # Insert new node into data array between index and index+1
        # self._data = np.insert(self.data, index+1, [p,pin,pout], axis=0)

    # Similar to splitAt() except the input is a (possibly) non-integer
    # index value instead of a normalized parameter t between 0 and 1.
    # The given index can be any real number between 0 and
    # myspline.length()-1
    def splitAtIndex(self, I, force=False):
        length = self.length()
        if length < 2:
            raise IndexError("Spline must have at least 2 nodes!")
        segCount = length - 1

        # Round to nearest node if within a billionth of it.
        tol = 1e-9
        if abs(I - round(I)) < tol:
            if force:
                I = round(I)
                if I == segCount:
                    # self._data = np.insert(self._data, length, self._data[-1,:].copy(), axis=0)
                    self.outhandleRel(-1, 0)
                    self.newNode(self.node(-1))
                    return
            else:
                # Do nothing if asked to split at a node point
                # and we're not forcing a split.
                return

        index = int(I)  # Latest preceding node index
        param = I - index  # Local parameter value
        p0 = self.node(index)
        p1 = self.outhandle(index)
        p2 = self.inhandle(index+1)
        p3 = self.node(index+1)
        slice1, slice2 = morpho.bezier.splitBezier(p0, p1, p2, p3, param)

        # Commit the handles of index and index+1 to ensure seamlessness
        self.commitHandles(index, index+1)

        # Modify starting and ending handles
        self.outhandle(index, slice1[1])
        self.inhandle(index+1, slice2[2])

        # Define new node
        p = slice2[0]
        pin = slice1[2]
        pout = slice2[1]

        # Insert new node into data array between index and index+1
        self._data = np.insert(self._data, index+1, [p,pin,pout], axis=0)
        return self


    # NOT IMPLEMENTED!
    # Extract a subspline.
    # a and b are indices, but can also be non-integers.
    # Actually, not sure if I want to implement this.
    # Gonna keep it low priority for now.
    def sub(self, a, b):
        raise NotImplementedError


    # Inserts the specified number of additional nodes to the
    # spline by interpolating along it. For large numNodes, the new
    # nodes will tend to bunch around the original nodes.
    def insertNodes(self, numNodes):
        segCount = self.length() - 1
        for n in range(numNodes):
            x = (n+1)/(numNodes+1) * segCount
            t = (x + n)/(segCount + n)
            self.splitAt(t, force=True)
        return self

    def _insertNodesUniformly_old(self, numNodes):
        raise NotImplementedError
        # Length and segment count of original spline
        length = self.length()
        segCount = length - 1
        tol = 1e-9  # Snap to nearest int if within this

        # Original version of the data array which will not
        # undergo modification during the following loop
        data = self.data.copy()

        for n in range(numNodes):
            # Parameter value in original index space
            t = (n+1)/(numNodes+1) * segCount

            # Round to nearest node if within tolerance.
            # Helps prevent floating point precision problems.
            if abs(t - round(t)) < tol:
                t = round(t)

            # Latest node index from ORIGINAL data array coming before t
            index = int(t)
            # Represents the actual index that "index" corresponds to in
            # the CURRENT self.data array. This is because we are modifying
            # self.data in place by inserting a new node each loop, so all
            # future indices get shifted up by 1 each cycle.
            INDEX = index + n

            p, pin, pout = data[index,:].tolist()
            pin, pout = replaceInfHandles(p, pin, pout)

            q, qin, qout = data[index+1,:].tolist()
            qin, qout = replaceInfHandles(q, qin, qout)

            # p, pin, pout = self.nodeData(INDEX)
            # q, qin, qout = self.nodeData(INDEX+1)

            slice1, slice2 = morpho.bezier.splitBezier(p, pout, qin, q, t-index)

            # Commit the handles of index and index+1 to ensure seamlessness
            self.commitHandles(INDEX, INDEX+1)

            # Modify starting and ending handles
            self.outhandle(INDEX, slice1[1])
            self.inhandle(INDEX+1, slice2[2])

            # Insert new node
            self.newNode(point=slice2[0], inhandle=slice1[2], outhandle=slice2[1], beforeIndex=INDEX+1)



    # # NOT TESTED YET!
    # # Returns the reflection of the specified inhandle about its
    # # corresponding node. If inhandle is inf, returns outhandle.
    # # If inhandle AND outhandle are inf, returns inf.
    # def inhandleReflection(self, index):
    #     inhandle = self.inhandle(index)
    #     if isbadnum(inhandle):
    #         outhandle = self.outhandle(index)
    #         return outhandle
    #     return reflect(inhandle, about=self.node(index))

    # # NOT TESTED YET!
    # # Returns the reflection of the specified outhandle about its
    # # corresponding node. If outhandle is inf, returns inhandle.
    # # If inhandle AND outhandle are inf, returns inf.
    # def outhandleReflection(self, index):
    #     outhandle = self.outhandle(index)
    #     if isbadnum(outhandle):
    #         inhandle = self.inhandle(index)
    #         return inhandle
    #     return reflect(outhandle, about=self.node(index))


    # Replaces any inf handles with the current positions they
    # would correspond to.
    # Optionally specify index or index range to commit
    # These index values can be negative, whereby they will be treated
    # cyclically like in python list indexing.
    # Example usage:
    # myspline.commitHandles()  # Commits all handles
    # myspline.commitHandles(n)  # Commits the handles of the nth node only
    # myspline.commitHandles(a,b)  # Commits the handles of nodes a thru b (inclusive)
    def commitHandles(self, index=None, upper=None):
        commitSplineHandles(self.data, index, upper)
        return self
        # if index is None and upper is None:
        #     index = 0
        #     upper = -1
        # elif index is None:
        #     index = 0
        # elif upper is None:
        #     upper = index

        # if index < 0:
        #     index = index % self.length()
        # if upper < 0:
        #     upper = upper % self.length()

        # for n in range(index, upper+1):
        #     pin, pout = replaceInfHandles(*self.data[n,:])
        #     self._data[n,1:] = pin, pout

    # Applies all of the transformation attributes
    # origin, rotation, transform
    # to the actual data array itself and then
    # resets the transformation attributes.
    def commitTransforms(self):
        # Rotate all points
        self._data *= cmath.exp(self.rotation*1j)

        # Perform linear transformation
        mat = morpho.matrix.Mat(self._transform)
        for i in range(self.length()):
            for j in range(3):
                z = self._data[i,j]
                if not isbadnum(z):
                    self._data[i,j] = mat*z

        # Translate
        self._data += self.origin

        # Convert any possible nans that were produced into infs.
        nan2inf(self._data)

        # Reset transformation tweenables to identities
        self.origin = 0
        self.rotation = 0
        self._transform = np.eye(2)
        return self


    def draw(self, camera, ctx):
        # Need at least two nodes to draw
        if self.data.shape[0] < 2:
            return

        # Check bounds of start and end
        if not(0 <= self.start <= 1):
            raise ValueError("start parameter must be in the range [0,1] (inclusive).")
        if not(0 <= self.end <= 1):
            raise ValueError("end parameter must be in the range [0,1] (inclusive).")

        # Handle trivial length path and start >= end.
        len_seq = self.length()
        maxIndex = len_seq - 1
        if maxIndex < 1 or self.start >= self.end or self.alpha == 0:
            return

        # If determinant of the transform matrix is too small,
        # don't attempt to draw.
        if abs(np.linalg.det(self._transform)) < 1e-6:
            return

        # Compute index bounds
        tol = 1e-9  # Snap to nearest integer if within this much of an integer.
        start = self.start*maxIndex
        if abs(start - round(start)) < tol:
            start = round(start)
        int_start = int(start)
        end = self.end*maxIndex
        if abs(end - round(end)) < tol:
            end = round(end)
        int_end = int(end)

        # Adjust based on deadends

        # Propagate start and int_start forward
        # if start is a deadend or in the void.
        while int_start in self.deadends:
            int_start += 1
            start = int_start

        # If end is STRICTLY in the void, floor it to int_end
        if end != int_end and int_end in self.deadends:
            end = int_end
        if end == int_end:
            # Backpropagate int_end until it is no longer a deadstart.
            while int_end-1 in self.deadends:
                int_end -= 1
            end = int_end

        # If start and end are too close, just skip
        if abs(start - end) < tol:
            return

        # If, after the adjustment, we get an empty path,
        # do nothing.
        if start >= end:
            return

        # If we have non-integer starting and ending indices,
        # we will need to split the spline at at least one point.
        needSplits = (start != int_start or end != int_end)

        if needSplits:
            # Save a copy of the original data array because
            # we will temporarily replace it.
            # This technique should probably be re-implemented better
            # in the future because it's expensive to copy an entire
            # np.array every single frame draw, though I expect it's
            # not too bad for a spline without a huge number of nodes.
            oldData = self._data
            self._data = oldData.copy()

            # Non-integer starting index
            if start != int_start:
                self.splitAtIndex(start)

                # Shift all relevant indices up one
                # to compensate for new node inserted early
                start += 1
                int_start += 1

                end += 1
                int_end += 1

            # Non-integer ending index
            if end != int_end:
                if int_start == int_end and start != int_start:
                    # Adjust end index value because it is now
                    # with respect to the newly added node instead
                    # of the original node.
                    end = int_end + (end-start)/(int_end+1-start)
                self.splitAtIndex(end)

        # Compute true initial and true final indices
        init = math.floor(start)
        final = math.ceil(end)

        # # Temporarily modify self.data in place to account
        # # for non-integer start and end
        # oldStart = self._data[int_start,:]
        # if start != init:
        #     p, pin, pout = self.nodeData(int_start)
        #     q, qin, qout = self.nodeData(int_start+1)
        #     m0, m1, m2, m3 = morpho.bezier.bezierLastSlice(p, pout, qin, q, start-int_start)

        #     self._data[int_start,:] = [m0, m1, 0]
        # if end != int_end:
        #     oldEnd = self._data[int_end+1,:]

        #     p, pin, pout = self._data[int_end,:] if int_end != int_start else oldStart
        #     q, qin, qout = self.nodeData(int_end+1)
        #     m0, m1, m2, m3 = morpho.bezier.bezierFirstSlice(p, pout, qin, q, end-int_end)

        #     self._data[int_end+1] = [m3, m2, 0]

        #     # self.seq[int_end+1] = morpho.numTween(
        #     #     self.seq[int_end] if int_end != int_start else oldStart, oldEnd, end-int_end
        #     #     )

        # Temporarily modify cairo coordinates to coincide with
        # physical coordinates.
        morpho.pushPhysicalCoords(camera.view, ctx)  # Contains a ctx.save()

        # Handle possible other transformations
        morpho.applyTransforms(ctx, self.origin, self.rotation, self.transform)


        # if start == init:
        # Initialize starting point
        zprev, inprev, outprev = self.data[init,:].tolist()
        inprev, outprev = replaceInfHandles(zprev, inprev, outprev)
        # else:
        #     p, pin, pout = self.nodeData(init)
        #     q, qin, qout = self.nodeData(init+1)
        #     m0, m1, m2, m3 = morpho.bezier.bezierLastSlice(p, pout, qin, q, start-init)
        #     zprev = m0
        #     outprev = m1

        # Move to starting point
        x,y = zprev.real, zprev.imag
        ctx.move_to(x,y)

        # Draw each curve
        # for n in range(self.data.shape[0]-1):
        for n in range(init, final):
            # Get next node, inhandle, and outhandle
            z, inhandle, outhandle = self.data[n+1,:].tolist()
            # Update handles based on possible inf values
            inhandle, outhandle = replaceInfHandles(z, inhandle, outhandle)

            x,y = z.real, z.imag

            # If previous node is a deadend, or current or previous
            # nodes are bad, move to next node.
            # Else, draw a curve to the next node.
            if n in self.deadends or isbadnum(z) or isbadnum(zprev):
                ctx.move_to(x,y)
            else:
                x1,y1 = outprev.real, outprev.imag
                x2,y2 = inhandle.real, inhandle.imag
                ctx.curve_to(x1,y1, x2,y2, x,y)

            # Update previous values to current values
            zprev = z
            # inprev = inhandle
            outprev = outhandle

        # # Handle non-integer ending index
        # if end != final:
        #     x1,y1 = outprev.real, outprev.imag

        #     p, pin, pout = self.nodeData(final)
        #     q, qin, qout = self.nodeData(final-1)
        #     m0, m1, m2, m3 = morpho.bezier.bezierFirstSlice(p, pout, qin, q, end-(final-1))
        #     x2,y2 = m2.real, m2.imag
        #     x,y = m3.real, m3.imag

        #     ctx.curve_to(x1,y1, x2,y2, x,y)

        # Handle gradients
        if self.alphaFill > 0:
            if isinstance(self.fill, morpho.color.GradientFill):
                self.fill.draw(camera, ctx, self.alphaFill*self.alpha, pushPhysicalCoords=False)
            # Handle normal colors
            else:
                ctx.set_source_rgba(*self.fill, self.alphaFill*self.alpha)
                ctx.fill_preserve()

        ctx.restore()

        # Set line width & color & alpha
        ctx.set_line_width(self.width)
        ctx.set_source_rgba(*self.color, self.alpha*self.alphaEdge)
        ctx.set_dash(self.dash)
        ctx.stroke()
        ctx.set_dash([])

        # Restore original data array if splits occurred
        if needSplits:
            self._data = oldData

        if self.showTangents:
            self.drawTangents(camera, ctx)

    def drawTangents(self, camera, ctx):
        # Need at least two nodes to draw
        if self.data.shape[0] < 2:
            return

        # If determinant of the transform matrix is too small,
        # don't attempt to draw.
        if abs(np.linalg.det(self.transform)) < 1e-6:
            return

        # Draw each tangent
        width = max(self.width/2, 1)
        for n in range(self.data.shape[0]):
            # Get next node, inhandle, and outhandle
            z, inhandle, outhandle = self.data[n,:].tolist()

            if isbadnum(z):
                continue

            # Update handles based on possible inf values
            inhandle, outhandle = replaceInfHandles(z, inhandle, outhandle)

            x,y = z.real, z.imag
            inx, iny = inhandle.real, inhandle.imag
            outx, outy = outhandle.real, outhandle.imag

            ctx.set_line_width(width)
            ctx.set_source_rgba(*self.color, self.alpha)

            # Temporarily modify cairo coordinates to coincide with
            # physical coordinates.
            morpho.pushPhysicalCoords(camera.view, ctx)  # Contains a ctx.save()

            # Handle possible other transformations
            morpho.applyTransforms(ctx, self.origin, self.rotation, self.transform)

            ctx.move_to(inx, iny)
            ctx.line_to(x,y)
            ctx.line_to(outx, outy)

            ctx.restore()
            ctx.stroke()

    # def draw(self, camera, ctx):
    #     self.draw0(camera, ctx, False)
    #     if self.showTangents:
    #         self.draw0(camera, ctx, True)


    # Converts the Spline figure to a similar-looking Path figure.
    # Optionally specify "segsteps" which is how many path steps to
    # use in a single bezier curve segment of the spline.
    # Defaults to 30 steps per segment.
    def toPath(self, segsteps=30):
        path = morpho.grid.line(0,1, steps=segsteps*(self.length()-1))

        # Make path follow the spline
        path = path.fimage(self.positionAt)

        # Match other tweenables
        path.start = self.start
        path.end = self.end
        path.color = self.color[:]
        path.alphaEdge = self.alphaEdge
        path.fill = self.fill.copy() if "copy" in dir(self.fill) else self.fill
        path.alphaFill = self.alphaFill
        path.alpha = self.alpha
        path.width = self.width
        path.origin = self.origin
        path.rotation = self.rotation
        path._transform = self._transform.copy()

        return path



    # NOT IMPLEMENTED YET!!!
    # Takes the function image of the spline under the given func.
    # Note: This applies to ALL control points: both nodes AND
    # handles. This function will skip any control points that are
    # inf or nan.
    #
    # Currently thinking I'll change the default behavior on
    # handle points so that the tangent lines change based on
    # the numerical DERIVATIVE of the given func. That seems
    # like it would produce the most faithful fimage of a spline.
    # However, that behavior perhaps could be suppressed by
    # changing a flag parameter.
    # It would basically work by computing the local linear
    # transformation about a node and applying that linear
    # transformation to both inhandle and outhandle locally.
    def fimage(self, func):
        raise NotImplementedError
        newfig = self.copy()
        # newfig._data = newfig._data.copy()

        for i in range(newfig.length()):
            for j in range(3):
                value = newfig.data[i,j].tolist()
                if not isbadnum(value):
                    newfig._data[i,j] = func(value)

        return newfig

    # Interpolates the data array of self with other, but after
    # replacing inf values with concrete values where necessary
    # (but leaves the data arrays of self and other unmodified).
    # This is done whenever one node has an inf handle, but its
    # counterpart handle in the other spline is finite.
    def splineDataInterp(self, other, t):
        data1 = self.data.copy()
        data2 = other.data.copy()

        crossCommitHandles(data1, data2)

        # Interpolate normally.
        with np.errstate(all="ignore"):  # Suppress numpy warnings
            data = morpho.lerp0(data1, data2, t)
        nan2inf(data)

        return data


    ### TWEEN METHODS ###

    @morpho.tweenMethod
    @morpho.grid.handleDash
    @morpho.color.handleGradientFills(["fill"])
    @handleSplineNodeInterp
    def tweenLinear(self, other, t):
        # Handle interpolating everything but the data tweenable
        tw = morpho.Figure.tweenLinear(self, other, t, ignore="_data")

        # Handle interpolating data
        tw._data = self.splineDataInterp(other, t)

        return tw

    @morpho.tweenMethod
    @morpho.grid.handleDash
    @morpho.color.handleGradientFills(["fill"])
    @handleSplineNodeInterp
    def tweenSpiral(self, other, t):
        # Handle interpolating everything but the data tweenable
        tw = morpho.Figure.tweenLinear(self, other, t, ignore="_data")

        # Handle interpolating data
        data1 = self.data.copy()
        data2 = other.data.copy()

        crossCommitHandles(data1, data2)

        # Interpolate using spiral tween method
        data12 = morpho.spiralInterpArray(data1, data2, t)
        nan2inf(data12)

        tw._data = data12

        return tw


    @classmethod
    def tweenPivot(cls, angle=tau/2):

        @morpho.TweenMethod
        @morpho.grid.handleDash
        @morpho.color.handleGradientFills(["fill"])
        @handleSplineNodeInterp
        def pivot(self, other, t):
            # Handle interpolating everything but the data tweenable
            tw = morpho.Figure.tweenLinear(self, other, t, ignore="_data")

            # Handle interpolating data
            data1 = self.data.copy()
            data2 = other.data.copy()

            crossCommitHandles(data1, data2)

            # Interpolate using pivot tween method
            data12 = morpho.pivotInterpArray(data1, data2, t, angle=angle)
            nan2inf(data12)

            tw._data = data12

            return tw

        return pivot

# Animates a spline actor appearing by "growing in" from a single point.
# The starting point is always the initial node in the sequence.
# See also: morpho.actions.fadeIn()
@Spline.action
def growIn(spline, duration=30, atFrame=None):
    if atFrame is None:
        atFrame = spline.lastID()

    spline0 = spline.last()
    start, end = spline0.start, spline0.end
    spline0.visible = False
    spline1 = spline.newkey(atFrame)
    spline1.set(start=0, end=0, visible=True)
    spline2 = spline.newendkey(duration)
    spline2.set(start=start, end=end)


# Space version of Spline figure. See "Spline" for more info.
class SpaceSpline(Spline):
    def __init__(self, data=None, width=3, color=(1,1,1), alpha=1):

        # Use normal Spline constructor to start
        super().__init__(data=None, width=width, color=color, alpha=alpha)

        # Initialize origin triple
        origin = morpho.matrix.array([0,0,0])


        if data is None:
            # Use default data array supplied by superclass's constructor
            data = np.array([[[]]], dtype=float)
        elif type(data) is Spline:
            spline = data  # Rename so the following lines make more sense

            # Copy over state and all other attributes except data
            for name in self._state:
                if name != "_data":
                    self._state[name] = spline._state[name].copy()

            # Copy other attributes
            self.dash = spline.dash[:]
            self.deadends = spline.deadends.copy()
            origin = morpho.matrix.array(spline.origin)

            # Make "data" actually hold the 2D spline's data array
            # instead of mapping to the whole spline object.
            data = spline._data
        elif not isinstance(data, np.ndarray):
            raise TypeError("Unrecognized type for data array.")

        # Convert data array into a 3D array of real floats if
        # it lacks 3 dimensions
        if len(data.shape) < 3:
            # data3d = np.expand_dims(data.copy(), axis=2)

            # Convert data into empty 3D array of real floats
            # with same shape as data (just with 3 new slots)
            print(data.shape)
            Nrows, Ncols = data.shape
            data3d = np.zeros((Nrows, Ncols, 3))

            # Convert complex numbers into 3D vectors with
            # z-coordinate = 0.
            for i in range(Nrows):
                for j in range(Ncols):
                    s = data[i,j]
                    data3d[i,j,:] = [s.real, s.imag, 0]

            # Redefine data as data3d
            data = data3d

        # Convert all nans to infs before assigning the tweenable.
        nan2inf(data)
        _data = morpho.Tweenable("_data", data, tags=["nparray"])
        # Replace old _data tweenable that was inherited from
        # the superclass's constructor.
        self._state["_data"] = _data

        # Re-implement "origin" as a property so it will auto-convert
        # into np.array.
        self._state.pop("origin")
        _origin = morpho.Tweenable("_origin", origin, tags=["nparray", "nofimage"])
        self.extendState([_origin])

        # These transformation tweenables from 2D Spline are currently
        # not supported for SpaceSplines
        self._state.pop("rotation")
        self._state.pop("_transform")


    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = np.array(value, dtype=float)

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, value):
        self._origin = morpho.matrix.array(value)

    # "transform" tweenable is currently unsupported for SpaceSpline
    @property
    def transform(self):
        raise AttributeError

    @transform.setter
    def transform(self, value):
        raise AttributeError

    # Returns or sets the position of the node of given index.
    # Usage: myspline.node(n) -> position of nth node
    #        myspline.node(n, value) sets nth node position to value
    def node(self, index, value=None):
        if value is None:
            return self.data[index, 0, :].copy()
        self.data[index, 0, :] = morpho.array(value)
        return self

    # Returns or sets the position of the inward handle
    # of the node at the given index (see node() for more info).
    # Input and output values of this method are in absolute
    # physical coordinates of the plane (as a complex number).
    # See also: inhandleRel().
    #
    # If optional "raw" is set to True, the values are ripped
    # straight from the data array, including inf values;
    # but if set to False, it computes the current position
    # inf corresponds to.
    def inhandle(self, index, value=None, raw=False):
        if value is None:
            if raw:
                return self.data[index, 1, :]
            else:
                p, pin, pout = list(self.data[index,:,:])
                pin, pout = replaceInfHandles(p, pin, pout)
                return pin
        # Convert to oo given any non-finite value
        if isbadarray(value):
            value = oo
        else:
            value = morpho.array(value)
        self.data[index, 1, :] = value
        return self

    # Returns or sets the position of the outward handle
    # of the node at the given index (see node() for more info).
    # Input and output values of this method are in absolute
    # physical coordinates of the plane (as a complex number).
    # See also: outhandleRel().
    #
    # If optional "raw" is set to True, the values are ripped
    # straight from the data array, including inf values;
    # but if set to False, it computes the current position
    # inf corresponds to.
    def outhandle(self, index, value=None, raw=False):
        if value is None:
            if raw:
                return self.data[index, 2, :]
            else:
                p, pin, pout = list(self.data[index,:,:])
                pin, pout = replaceInfHandles(p, pin, pout)
                return pout
        # Convert to oo given any non-finite value
        if isbadarray(value):
            value = oo
        else:
            value = morpho.array(value)
        self.data[index, 2, :] = value
        return self

    # Returns the matrix fully describing the node of given index.
    # Equivalent to extracting the 2D matrix slice at a specified first
    # index value: self.data[index,:,:]
    # but converts any inf handle values into their current
    # corresponding positions like how inhandle() and outhandle()
    # would output by default.
    # Optionally set argument raw=True to make it actually return
    # just a raw copy of a given node index of the data array.
    def nodeData(self, index, raw=False):
        if raw:
            return self._data[index,:,:].copy()

        p, pin, pout = list(self._data[index,:,:])
        pin, pout = replaceInfHandles(p, pin, pout)

        return np.array([p, pin, pout], dtype=float)

    # Returns or sets the position of the inward handle
    # of the node at the given index relative to the node position.
    # See also: inhandle()
    # Equivalent names for this method:
    # inhandlerelative, inhandleRel, inhandlerel
    #
    # If optional "raw" is set to True, the values are ripped
    # straight from the data array, including inf values;
    # but if set to False, it computes the current position
    # inf corresponds to.
    def inhandleRel(self, index, value=None, raw=False):
        if value is None:
            return self.inhandle(index, value, raw) - self.node(index)
        # Convert to oo given any non-finite value
        if isbadarray(value):
            value = oo
        else:
            value = morpho.array(value)
        self.data[index, 1, :] = self.data[index, 0, :] + value
        return self

    # inhandlerel = inhandleRel = inhandlerelative = inhandleRelative

    # Returns or sets the position of the outward handle
    # of the node at the given index relative to the node position.
    # See also: outhandle()
    # Equivalent names for this method:
    # outhandlerelative, outhandleRel, outhandlerel
    #
    # If optional "raw" is set to True, the values are ripped
    # straight from the data array, including inf values;
    # but if set to False, it computes the current position
    # inf corresponds to.
    def outhandleRel(self, index, value=None, raw=False):
        if value is None:
            return self.outhandle(index, value, raw) - self.node(index)
        # Convert to oo given any non-finite value
        if isbadarray(value):
            value = oo
        else:
            value = morpho.array(value)
        self.data[index, 2, :] = self.data[index, 0, :] + value
        return self

    # outhandlerel = outhandleRel = outhandlerelative = outhandleRelative

    # Creates a new node at the specified point.
    # Optionally also specify inhandle and outhandle which default to inf.
    # Also optionally specify where to insert the node in the sequence.
    # By default, places it after the current final node.
    def newNode(self, point, inhandle=(oo,oo,oo), outhandle=(oo,oo,oo), beforeIndex=oo):
        beforeIndex = min(beforeIndex, self.length())
        if beforeIndex < 0:
            beforeIndex = beforeIndex % self.length()

        # Convert to np.arrays if needed
        point = morpho.array(point)
        inhandle = morpho.array(inhandle)
        outhandle = morpho.array(outhandle)

        if self._data.size == 0:
            self._data = np.array([[point, inhandle, outhandle]], dtype=float)
        else:
            self._data = np.insert(self.data, beforeIndex, [point,inhandle,outhandle], axis=0)
        return self


    # Closes the path IN PLACE if it is not already closed.
    def close(self):
        if self.length() < 2 or np.array_equal(self.node(0), self.node(1)):
            return self
        self._data = np.insert(self._data, self.length(), self._data[0,:,:].copy(), axis=0)
        return self


    # Translates the spline by the value of the "origin" attribute
    # and then resets the "origin" attribute to (0,0,0).
    def commitTransforms(self):
        self._data += self.origin
        self.origin = np.array([0,0,0], dtype=float)
        return self


    # Converts the Spline figure to a similar-looking SpacePath figure.
    # Optionally specify "segsteps" which is how many path steps to
    # use in a single bezier curve segment of the spline.
    # Defaults to 30 steps per segment.
    def toPath(self, segsteps=30):
        steps = segsteps*(self.length()-1)
        seq = []
        for n in range(0,steps+1):
            seq.append(self.positionAt(n/steps))

        path = morpho.grid.SpacePath(seq)

        # Match other tweenables
        path.start = self.start
        path.end = self.end
        path.color = self.color[:]
        path.alphaEdge = self.alphaEdge
        path.fill = self.fill.copy() if "copy" in dir(self.fill) else self.fill
        path.alphaFill = self.alphaFill
        path.alpha = self.alpha
        path.width = self.width
        path.origin = self.origin.copy()

        return path

    # toPath = toSpacepath = toSpacePath

    def primitives(self, camera):
        # If the spline is fully transparent, don't bother
        # creating any primitives. Just return the empty list.
        if self.alpha == 0:
            return []

        orient = camera.orient
        focus = camera.focus

        # Apply orient matrix transformation to all the vectors
        # along the final axis (axis 2)
        array = self._data
        if not np.allclose(self.origin, 0):
            # DON'T SIMPLIFY THIS LINE TO += !!!
            # We do NOT want this operation performed in place here!
            # It could end up modifying the original self._data!
            array = array + self.origin
        if not np.allclose(focus, 0):
            array = array - focus  # Do NOT simplify this to -= !!!
            array = np.tensordot(array, orient[:2,:], axes=((2),(1)))
            array += focus[:2]  # In place operation here is fine cuz array was replaced via arithmetic above
        else:
            array = np.tensordot(array, orient[:2,:], axes=((2),(1)))
        nan2inf(array)

        with np.errstate(all="ignore"):  # Suppress numpy warnings
            array2d = array[:,:,0] + 1j*array[:,:,1]
        spline = Spline(data=array2d)
        spline.start = self.start
        spline.end = self.end
        spline.color = self.color
        spline.alphaEdge = self.alphaEdge
        spline.fill = self.fill
        spline.alphaFill = self.alphaFill
        spline.alpha = self.alpha
        spline.width = self.width

        spline.dash = self.dash
        spline.deadends = self.deadends
        spline.showTangents = self.showTangents


        # zdepth of the whole spline is given by the median node's visual zdepth.
        max_index = self.length()-1
        x = (max_index) // 2  # This is (the floor of) the median index
        if max_index % 2 == 0:  # Even max index => easy median
            spline.zdepth = float((orient[2,:] @ (self._data[x,0,:]-focus)) + focus[2])
        else:  # Odd max index => average the two nearest
            w1, w2 = self._data[x:x+2, 0, :]
            spline.zdepth = float((orient[2,:] @ ((w1+w2)/2 - focus)) + focus[2])

        return [spline]


    def draw(self, camera, ctx):
        primlist = self.primitives(camera)
        if len(primlist) == 0:
            return
        path = primlist[0]
        path.draw(camera, ctx)

    def drawTangents(self, camera, ctx):
        raise NotImplementedError


    ### TWEEN METHODS ###

    def tweenSpiral(self, other, t):
        raise NotImplementedError

    @classmethod
    def tweenPivot(cls, angle=tau/2):
        raise NotImplementedError




# Helper mainly for Spline class. Computes the reflection of "point"
# about the base point called "about".
def reflect(point, about):
    return 2*about - point

# Given the data triplet describing a node in a spline,
# replaces inf handle values
# with the current position values they correspond to based on
# their partner handle.
# The results are returned as a pair (new_inhandle, new_outhandle)
# This function does NOT operate in place: the inputs are unmodified.
def replaceInfHandles(point, inhandle, outhandle):
    # Get booleans indicating badness of handles
    inbad, outbad = isbadarray(inhandle), isbadarray(outhandle)
    # Reflect handles if necessary
    if inbad and outbad:
        inhandle = outhandle = 1*point  # 1* makes a copy if it's np.array
    elif outbad:
        outhandle = reflect(inhandle, about=point)
    elif inbad:
        inhandle = reflect(outhandle, about=point)
    else:
        # This makes copies of np.arrays if they are np.arrays,
        # but leaves complex numbers unchanged.
        inhandle = 1*inhandle
        outhandle = 1*outhandle

    return inhandle, outhandle


# Given spline data array,
# replaces any inf handles with the current positions they
# would correspond to.
# Optionally specify index or index range to commit.
# NOTE: This function modifies the data array IN PLACE!
def commitSplineHandles(data, index=None, upper=None):
    length = data.shape[0]

    if index is None and upper is None:
        index = 0
        upper = -1
    elif index is None:
        index = 0
    elif upper is None:
        upper = index

    if index < 0:
        index = index % length
    if upper < 0:
        upper = upper % length

    for n in range(index, upper+1):
        pin, pout = replaceInfHandles(*data[n,:])
        data[n,1:] = (pin, pout)

# Given two data arrays of the same shape,
# checks for entries where one array has inf but the other has finite,
# and then replaces the infinite entry with its corresponding
# reflected finite value FOR ALL entries that share a row with that one.
# This operation is done IN PLACE to both data arrays.
# This function is mainly used to help tween two splines in which
# one spline has an implicit handle (inf) and the other has an explicit
# handle (finite).
def crossCommitHandles(data1, data2):
    # Find all rows where one entry is +oo but the other is finite.
    # These are the rows where we will have to replace the infinities
    # with concrete values.
    # rows = set(np.where(np.isinf(abs(data1) - abs(data2)).any(axis=1))[0].tolist())
    with np.errstate(all="ignore"):  # Suppress numpy warnings
        rows = set(np.where(np.isinf(abs(data1) - abs(data2)).any(axis=tuple(range(1,len(data1.shape)))))[0].tolist())
    for r in rows:
        commitSplineHandles(data1, r)
        commitSplineHandles(data2, r)

# def crossCommitHandles3D(data1, data2):
#     # Find all node matrices where one entry is +oo but the other
#     # is finite. These are the indices where we have to replace the
#     # inf values with concrete values.
#     nodeIndices = set(np.where(np.isinf(abs(data1) - abs(data2)).any(axis=(1,2)))[0].tolist())
#     for n in nodeIndices:
#         commitSplineHandles(data1, n)
#         commitSplineHandles(data2, n)


# Converts all entries of the array that are nan into inf
# IN PLACE!
def nan2inf(array):
    array[np.isnan(array)] = oo



# NOT IMPLEMENTED YET!!!
# Parses an SVG string that describes a Bezier spline and then
# returns a data array
def SVGdata(string):
    raise NotImplementedError



# A pure ellipse object independent of the Polygon class.
# Note: Cannot be tweened into a polygon.
#
# TWEENABLES
# pos = Ellipse center (complex number). Default: 0
# xradius, yradius = Horizontal and vertical radii (physical units). Default: 1
# strokeWeight = Border thickness (in pixels). Default: 3
# color = Border color (RGB list). Default: [1,1,1] (white)
# fill = Interior fill color (RGB list). Default [1,0,0] (red)
# alphaEdge = Border opacity. Default: 1 (opaque)
# alphaFill = Interior opacity. Default: 1 (opaque)
# alpha = Overall opacity. Multiplies alphaEdge and alphaFill.
#         Default: 1 (opaque)
class Ellipse(morpho.Figure):

    def __init__(self, pos=0, xradius=1, yradius=1,
        strokeWeight=3, color=(1,1,1), fill=(1,0,0),
        alphaEdge=1, alphaFill=1, alpha=1):

        super().__init__()

        pos = morpho.Tweenable("pos", pos, tags=["complex", "position"])
        xradius = morpho.Tweenable("xradius", xradius, tags=["scalar"])
        yradius = morpho.Tweenable("yradius", yradius, tags=["scalar"])
        strokeWeight = morpho.Tweenable("strokeWeight", strokeWeight, tags=["scalar"])
        color = morpho.Tweenable("color", list(color), tags=["color"])
        fill = morpho.Tweenable("fill", list(fill), tags=["color"])
        alphaEdge = morpho.Tweenable("alphaEdge", alphaEdge, tags=["scalar"])
        alphaFill = morpho.Tweenable("alphaFill", alphaFill, tags=["scalar"])
        alpha = morpho.Tweenable("alpha", alpha, tags=["scalar"])

        self.update([pos, xradius, yradius, strokeWeight, color, fill, alphaEdge, alphaFill, alpha])

    # Setting `radius` property sets both `xradius` and `yradius` to
    # the same value.
    @property
    def radius(self):
        if self.xradius != self.yradius:
            raise ValueError("xradius does not equal yradius. No common radius.")
        return self.xradius

    @radius.setter
    def radius(self, value):
        self.xradius = value
        self.yradius = value

    # NOT IMPLEMENTED YET!!!
    def toPolygon(self, dTheta=tau/72):
        raise NotImplementedError

    def draw(self, camera, ctx):
        view = camera.view

        X,Y = morpho.screenCoords(self.pos, view, ctx)

        ctx.save()
        ctx.translate(X,Y)
        WIDTH = morpho.pixelWidth(self.xradius, view, ctx)
        HEIGHT = morpho.pixelHeight(self.yradius, view, ctx)

        # Zero is not allowed. Constrain to 0.1
        WIDTH = max(WIDTH, 0.1)
        HEIGHT = max(HEIGHT, 0.1)

        ctx.scale(WIDTH, HEIGHT)

        ctx.move_to(1,0)
        ctx.arc(0,0, 1, 0, tau)
        ctx.restore()

        ctx.set_source_rgba(*self.fill, self.alphaFill*self.alpha)
        ctx.fill_preserve()
        ctx.set_source_rgba(*self.color, self.alphaEdge*self.alpha)
        ctx.set_line_width(self.strokeWeight)
        ctx.stroke()


# Creates an arc of an ellipse.
# Angles should be interpreted as if the ellipse were a circle.
# That is, angles refer to a circular arc BEFORE being stretched
# into an ellipse. They are in units of radians.
#
# TWEENABLES
# pos = Ellipse center (complex number). Default: 0
# xradius, yradius = Horizontal and vertical radii (physical units). Default: 1
#                    If yradius is unspecified, copies xradius.
# theta0, theta1 = Angles (in rad) defining the angular span.
#                  The arc is always drawn starting from theta0 and going
#                  toward theta1, covering all angles between theta0 and theta1.
#                  Default: 0,2pi
# strokeWeight = Border thickness (in pixels). Default: 3
# color = Border color (RGB list). Default: [1,1,1] (white)
# alpha = Opacity. Default: 1 (opaque)
class EllipticalArc(morpho.Figure):

    def __init__(self, pos=0, xradius=1, yradius=None, theta0=0, theta1=tau,
        strokeWeight=3, color=(1,1,1), alpha=1):

        if yradius is None:
            yradius = xradius

        super().__init__()

        pos = morpho.Tweenable("pos", pos, tags=["complex", "position"])
        xradius = morpho.Tweenable("xradius", xradius, tags=["scalar"])
        yradius = morpho.Tweenable("yradius", yradius, tags=["scalar"])
        theta0 = morpho.Tweenable("theta0", theta0, tags=["scalar"])
        theta1 = morpho.Tweenable("theta1", theta1, tags=["scalar"])
        strokeWeight = morpho.Tweenable("strokeWeight", strokeWeight, tags=["scalar"])
        color = morpho.Tweenable("color", list(color), tags=["color"])
        alpha = morpho.Tweenable("alpha", alpha, tags=["scalar"])

        self.update([pos, xradius, yradius, theta0, theta1, strokeWeight, color, alpha])

    # Setting `radius` property sets both `xradius` and `yradius` to
    # the same value.
    @property
    def radius(self):
        if self.xradius != self.yradius:
            raise ValueError("xradius does not equal yradius. No common radius.")
        return self.xradius

    @radius.setter
    def radius(self, value):
        self.xradius = value
        self.yradius = value

    # Converts the figure into an equivalent Path figure.
    # Optionally specify the angular steps (in rad).
    # Default: 2pi/72 (5 degrees)
    # NOTE: Arc center will be assigned using Path.origin.
    # You will need to call commitTransforms() on the resulting
    # path figure if you want the vertex list to perfectly reflect
    # points on the arc in true space.
    def toPath(self, dTheta=tau/72):

        theta0, theta1 = self.theta0, self.theta1
        # If angular span is greater than tau,
        # just draw a circle
        if abs(theta1 - theta0) >= tau:
            theta1 = theta0 + tau
        # Ensure theta0 <= theta1
        elif theta1 < theta0:
            # theta0, theta1 = theta1, theta0
            dTheta *= -1

        # steps = int(math.ceil(360 / abs(dTheta)))
        # dTheta *= tau/360  # convert dTheta to radians
        steps = math.ceil(abs((theta1 - theta0) / dTheta))

        # Make unit circle arc
        z0 = cmath.exp(theta0*1j)
        z1 = cmath.exp(theta1*1j)
        seq = [z0]
        for n in range(1, steps):
            seq.append(cmath.exp((theta0+n*dTheta)*1j))
        seq.append(z1)

        path = morpho.grid.Path(seq)
        path.width = self.strokeWeight
        path.color = self.color[:]
        path.alpha = self.alpha

        # Stretch it into an ellipse and move it
        path = path.fimage(lambda z: mat(self.xradius,0,0,self.yradius)*z)
        # path = path.fimage(lambda z: z + self.pos)
        path.origin = self.pos

        return path


    def draw(self, camera, ctx):
        view = camera.view

        X,Y = morpho.screenCoords(self.pos, view, ctx)

        ctx.save()
        ctx.translate(X,Y)
        WIDTH = max(morpho.pixelWidth(self.xradius, view, ctx), 0.1)
        HEIGHT = max(morpho.pixelHeight(self.yradius, view, ctx), 0.1)
        ctx.scale(WIDTH, HEIGHT)

        theta0, theta1 = self.theta0, self.theta1
        # If angular span is greater than tau,
        # just draw a circle
        if abs(theta1 - theta0) >= tau:
            theta0 = 0
            theta1 = tau
        elif theta1 < theta0:
            theta0, theta1 = theta1, theta0

        Z0 = cmath.exp(theta0*1j)
        ctx.move_to(Z0.real, Z0.imag)
        ctx.arc(0,0, 1, theta0, theta1)
        ctx.restore()

        ctx.set_source_rgba(*self.color, self.alpha)
        ctx.set_line_width(self.strokeWeight)
        ctx.stroke()


# Creates a segment of an ellipse: a rectangle in polar coordinate space.
# Parameters are essentially identical to EllipticalArc, but with new parameter
# "innerFactor" which is a number between 0 and 1 representing where the inner arc
# should appear relative to the outer arc. So setting innerFactor = 0.25 means
# the inner arc will appear 25 percent of the way from the origin to the outer arc.
class Pie(EllipticalArc):
    def __init__(self, pos=0, xradius=1, yradius=None, innerFactor=0, theta0=0, theta1=tau,
        strokeWeight=3, color=(1,1,1), alphaEdge=1, fill=(1,0,0), alphaFill=1, alpha=1):

        super().__init__(pos, xradius, yradius, theta0, theta1, strokeWeight,
            color, alpha)

        innerFactor = morpho.Tweenable("innerFactor", innerFactor, tags=["scalar"])
        alphaEdge = morpho.Tweenable("alphaEdge", alphaEdge, tags=["scalar"])
        fill = morpho.Tweenable("fill", fill, tags=["color"])
        alphaFill = morpho.Tweenable("alphaFill", alphaFill, tags=["scalar"])
        self.extendState([innerFactor, alphaEdge, fill, alphaFill])

    def draw(self, camera, ctx):
        view = camera.view

        X,Y = morpho.screenCoords(self.pos, view, ctx)

        ctx.save()
        ctx.translate(X,Y)
        WIDTH = max(morpho.pixelWidth(self.xradius, view, ctx), 0.1)
        HEIGHT = max(morpho.pixelHeight(self.yradius, view, ctx), 0.1)
        ctx.scale(WIDTH, HEIGHT)

        theta0, theta1 = self.theta0, self.theta1
        # If angular span is greater than tau,
        # just draw a circle
        if abs(theta1 - theta0) >= tau:
            theta1 = theta0 + tau
        elif theta1 < theta0:
            theta0, theta1 = theta1, theta0

        Z0 = cmath.exp(theta0*1j)
        Z1 = cmath.exp(theta1*1j)
        W0 = self.innerFactor*Z0
        W1 = self.innerFactor*Z1
        ctx.move_to(Z0.real, Z0.imag)
        ctx.arc(0,0, 1, theta0, theta1)
        ctx.line_to(W1.real, W1.imag)
        ctx.arc_negative(0,0, self.innerFactor, theta1, theta0)
        ctx.close_path()
        ctx.restore()

        # Draw the fill
        ctx.set_source_rgba(*self.fill, self.alphaFill*self.alpha)
        ctx.fill_preserve()

        ctx.set_source_rgba(*self.color, self.alphaEdge*self.alpha)
        ctx.set_line_width(self.strokeWeight)
        ctx.stroke()

    def toPath(self, dTheta=tau/72):
        raise NotImplementedError

    # Converts the figure into an equivalent polygon figure
    # Optionally specify the angular steps (in rads).
    # Default: 2pi/72 (5 degrees)
    # NOTE: Arc center will be assigned using Polygon.origin.
    # You will need to call commitTransforms() on the resulting
    # path figure if you want the vertex list to perfectly reflect
    # points on the arc in true space.
    def toPolygon(self, dTheta=tau/72):

        theta0, theta1 = self.theta0, self.theta1
        # If angular span is greater than tau,
        # just draw a circle
        if abs(theta1 - theta0) >= tau:
            theta1 = theta0 + tau
        # Ensure theta0 <= theta1
        elif theta1 < theta0:
            # theta0, theta1 = theta1, theta0
            dTheta *= -1

        # steps = int(math.ceil(360 / abs(dTheta)))
        # dTheta *= tau/360  # convert dTheta to radians
        steps = math.ceil(abs((theta1 - theta0) / dTheta))

        # Make unit circle
        z0 = cmath.exp(theta0*1j)
        z1 = cmath.exp(theta1*1j)
        w0 = self.innerFactor * z0
        w1 = self.innerFactor * z1
        seq = [z0]
        for n in range(1, steps):
            seq.append(cmath.exp((theta0+n*dTheta)*1j))
        seq.append(z1)

        if self.innerFactor > 0:
            innerSeq = seq[::-1]
            innerSeq = np.array(innerSeq, dtype=complex)
            innerSeq *= self.innerFactor
            innerSeq = innerSeq.tolist()
        else:
            innerSeq = [0]

        seq.extend(innerSeq)

        # Make the polygon
        poly = morpho.grid.Polygon(seq)

        # Style parameters
        poly.width = self.strokeWeight
        poly.color = self.color[:]
        poly.fill = self.fill[:]
        poly.alphaEdge = self.alphaEdge
        poly.alphaFill = self.alphaFill
        poly.alpha = self.alpha

        # Stretch it into an ellipse and move it
        poly = poly.fimage(lambda z: mat(self.xradius,0,0,self.yradius)*z)
        # poly = poly.fimage(lambda z: z + self.pos)
        poly.origin = self.pos
        return poly



### GADGETS ###

# These functions can be found here as well as grid.
line = morpho.grid.line
spaceLine = morpho.grid.spaceLine
rect = morpho.grid.rect
arc = morpho.grid.arc




### SCRAPS ###

'''
The following is the old work-in-progress notes for developing the
Spline class. I'm keeping it for now because it had a lot of ideas
and I'm not completely sure yet if I want to just discard it all.

NOT FULLY IMPLEMENTED YET!
    Cubic Bezier spline figure.
    We have a tweenable called "data" which is a list of triplets, where
    each triplet (called a node) describes a single node along the spline.
    node[0] = Position of node
    node[1] = Inward control point/handle
    node[2] = Outward control point/handle
    For the first node triplet, the inward handle is ignored, and similarly
    for the last node triplet, the outward handle is ignored.
    The handles can also take on "nan" values, which means when drawn, they
    will be interpreted as reflections of the complement handle, or if its
    complement is nan, it will be set equal to the node position.
    QUESTION: Should "data" be a python matrix? or a np.array?
    Currently thinking np.array is best. See fimage() discussion below.
    - Also, it would make extending this class to SpaceSpline easier, I think.
      tweenLinear() will treat all np.arrays alike, and similarly for fimage()

    Also consider having a "deadends" attribute which indicates which splines
    end at a deadend.

    Double-check that tweenLinear() can properly handle what will
    essentially be a python matrix of complex numbers! Also carefully
    check over how it will handle the positions being np.arrays when
    we eventually implement this in 3D.

    Perhaps have some helper methods/properties that allow the user to
    edit the spline data more easily?
    - Like these: They return the corresponding value unless value is
      other than python None, in which case, it SETS the value and the
      function returns python None
      + node(nodenum, value=None)
      + inhandle(nodenum, value=None)
      + outhandle(nodenum, value=None)
    - Maybe also have a method that can parse an SVG description of a
      spline path? Maybe implement this as part of the constructor?
      But have the meat of the SVG parser in its own outside helper
      function.

    Also, how should fimage() work? Currently thinking default behavior is fine,
    meaning handles are subjected to fimage() just like nodes are. If this is
    the desired behavior, then I think implementing the "data" tweenable as a
    complex-valued np.array makes the most sense.
    - However, you might slightly modify fimage() so that it just skips nan
      values instead of evaluating the function on them.
'''
