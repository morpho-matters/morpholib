
import morpholib as morpho
mo = morpho
import morpholib.tools.color, morpholib.anim, morpholib.transitions
from morpholib.matrix import mat
from morpholib.anim import MultiFigure
from morpholib.combo import TransformableFrame, FancyFrame
from morpholib.actions import wiggle
from morpholib.tools.basics import *
from morpholib.tools.dev import drawOutOfBoundsStartEnd, BoundingBoxFigure, \
    BackgroundBoxFigure, AlignableFigure, totalBox, shiftBox, \
    translateArrayUnderTransforms, handleBoxTypecasting, AmbiguousValueError

from morpholib import object_hasattr

import pyglet as pg
pyglet = pg
import cairo
cr = cairo

import math, cmath
import numpy as np
from collections.abc import Iterable


def dummy():
    pass
function = type(dummy)

root3over2 = math.sqrt(3)/2
ccw150 = cmath.exp(5*tau/12*1j)
cw150 = ccw150.conjugate()

I2 = np.identity(2)

### CLASSES ###


# Basic geometric point object.
#
# TWEENABLES
# pos = Position (complex number). Default: 0
# size = Diameter of point visually (pixels). Default: 15
# strokeWeight = Thickness of outer edge (pixels). Default: 1
# color = Edge color. Default: [0,0,0] (black)
# fill = Interior fill color. Default [1,0,0] (red)
# alpha = Overall opacity. Default: 1 (opaque)
# alphaEdge = Outer edge opacity. Default 1 (opaque)
# alphaFill = Interior opacity. Default: 1 (opaque)
# dash = Dash pattern. Works exactly like how it does in cairo. It's a list
#        of ints which are traversed cyclically and will alternatingly indicate
#        number of pixels of visibility and invisibility.
# dashOffset = Where along the dash pattern it will start. Default: 0
class Point(morpho.Figure):
    def __init__(self, pos=0, size=15, strokeWeight=1, color=(0,0,0), fill=(1,0,0),
        alpha=1):

        # Construct a default figure.
        # morpho.Figure.__init__(self)
        super().__init__()

        # Set parameters

        # Convert to complex if given as a tuple
        if type(pos) in (tuple, list):
            pos = pos[0] + 1j*pos[1]
        else:
            pos = complex(pos)

        # pos = morpho.Tweenable("pos", pos, tags=["complex", "position"])
        # strokeWeight = morpho.Tweenable("strokeWeight", strokeWeight, tags=["scalar"])
        # color = morpho.Tweenable("color", color, tags=["color"])
        # fill = morpho.Tweenable("fill", fill, tags=["color"])
        # alphaEdge = morpho.Tweenable(name="alphaEdge", value=1, tags=["scalar"])
        # alphaFill = morpho.Tweenable(name="alphaFill", value=1, tags=["scalar"])
        # alpha = morpho.Tweenable("alpha", alpha, tags=["scalar"])
        # self.style = "circle"
        # # size = diameter in pixels
        # size = morpho.Tweenable("size", size, tags=["size"])

        # # Initialize tweenables
        # self.update([pos, strokeWeight, color, fill, alphaEdge, alphaFill, alpha, size])

        self.Tweenable("pos", pos, tags=["complex", "position"])
        self.Tweenable("strokeWeight", strokeWeight, tags=["scalar", "pixel"])
        self.Tweenable("color", color, tags=["color"])
        self.Tweenable("fill", fill, tags=["color"])
        self.Tweenable(name="alphaEdge", value=1, tags=["scalar"])
        self.Tweenable(name="alphaFill", value=1, tags=["scalar"])
        self.Tweenable("alpha", alpha, tags=["scalar"])
        self.style = "circle"
        # size = diameter in pixels
        self.Tweenable("size", size, tags=["size", "pixel"])
        self.Tweenable("dash", [], tags=["scalar", "list", "pixel"])
        self.Tweenable("dashOffset", 0, tags=["scalar", "pixel"])


    # Draws the point on the given cairo context.
    def draw(self, camera, ctx):
        # Do nothing given invisible or zero-size point.
        if self.alpha <= 0 or self.size <= 0:
            return

        view = camera.view
        X,Y = morpho.anim.screenCoords(self.pos, view, ctx)
        R = self.size/2

        # Draw filled circle on context
        ctx.move_to(X+R,Y)
        ctx.arc(X, Y, R, 0, tau)
        ctx.close_path()

        ctx.set_source_rgba(*self.fill, self.alpha*self.alphaFill)
        ctx.fill_preserve()

        if self.strokeWeight < 0.5:  # Don't stroke if strokeWeight is too small
            ctx.new_path()
        else:
            ctx.set_source_rgba(*self.color, self.alpha*self.alphaEdge)
            ctx.set_line_width(self.strokeWeight)
            ctx.set_dash(self.dash, self.dashOffset)
            ctx.stroke()
            ctx.set_dash([])

@Point.action
def growIn(point, duration=30, atFrame=None):
    if atFrame is None:
        atFrame = point.lastID()

    point0 = point.last()
    size = point0.size
    point0.visible = False
    point1 = point.newkey(atFrame)
    point1.set(size=0, visible=True)
    point2 = point.newendkey(duration)
    point2.set(size=size)

# Alias for growIn()
@Point.action
def popIn(point, *args, **kwargs):
    return Point.actions["growIn"](point, *args, **kwargs)

@Point.action
def shrinkOut(point, duration=30, atFrame=None):
    if atFrame is None:
        atFrame = point.lastID()

    point.newkey(atFrame)
    point1 = point.newendkey(duration)
    point1.set(size=0, visible=False)

# Alias for shrinkOut()
@Point.action
def popOut(point, *args, **kwargs):
    return Point.actions["shrinkOut"](point, *args, **kwargs)

# Makes a point actor grow then shrink again.
# Scale factor of the growth can be specified by passing in
# a number into the `scale` keyword (Default: 2). Additional
# keyword inputs are set as attributes of the point at its
# point of maximum scale.
@Point.action
def pulse(point, duration=30, atFrame=None, *, scale=2, **kwargs):
    if atFrame is None:
        atFrame = point.lastID()

    point0 = point.newkey(atFrame)
    point1 = point.newkey(atFrame + duration/2)
    point1.size *= scale
    point1.set(**kwargs)
    point2 = point.newkey(atFrame + duration, point0.copy())

# DEPRECATED!
# Polar Point class. Identical to the Point class except it adds
# an attribute called "wind" which represents winding number about
# the origin with respect to the branch cut at 0 degs.
class PointPolar(Point):
    def __init__(self, pos=0, wind=0):
        raise NotImplementedError
        # Construct like the Point class
        Point.__init__(self, pos)

        # Add in attribute for winding number
        wind = morpho.Tweenable("wind", wind, tags=["integer", "winding number", "nolinear", "nospiral"])

        self.update(self.listState()+[wind])



# 3D version of the Point figure. See "Point" for more info.
class SpacePoint(Point):
    def __init__(self, pos=0, size=15, strokeWeight=1, color=(0,0,0), fill=(1,0,0),
        alpha=1):
        # Use superclass constructor
        super().__init__(0, size, strokeWeight, color, fill, alpha)

        # Redefine pos tweenable to be 3D.
        _pos = morpho.Tweenable("_pos", morpho.matrix.array(pos), tags=["nparray", "fimage", "3d"])
        self._state.pop("pos")
        self._state["_pos"] = _pos

        self.pos = pos

        # # Change the "pos" tweenable's "complex" tag to "nparray"
        # tags = self._state["pos"].tags
        # tags.remove("complex")
        # tags.remove("position")
        # tags.add("nparray")
        # tags.add("fimage")

        # # Handle supplied pos
        # if pos is None:
        #     pos = np.zeros(3)
        # else:
        #     pos = morpho.matrix.vector3d(pos)

        # self.pos = pos

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = morpho.matrix.array(value)


    def primitives(self, camera): # orient=np.identity(3), focus=np.zeros(3)):
        if self.alpha == 0:
            return []

        orient = camera.orient
        focus = camera.focus

        if np.allclose(focus, 0):
            pos3d = orient @ self.pos
        else:
            pos3d = orient @ (self.pos - focus) + focus
        pos3d = pos3d.tolist()

        pt = Point()
        pt.pos = pos3d[0] + 1j*pos3d[1]
        pt.zdepth = pos3d[2]
        pt.strokeWeight = self.strokeWeight
        pt.color = self.color
        pt.fill = self.fill
        pt.alpha = self.alpha
        pt.style = self.style
        pt.size = self.size

        return [pt]


    def draw(self, camera, ctx): #, orient=np.identity(3), focus=np.zeros(3)):
        primlist = self.primitives(camera)
        if len(primlist) == 0:
            return
        pt = primlist[0]
        pt.draw(camera, ctx)

Spacepoint = SpacePoint


# Wrapper around MultiFigure.Multi() which adds the effect
# of segmenting the added subpaths so that tweening between
# glyphs of different topological genus works better
# (e.g. morphing "B" to "O" doesn't have a fill discontinuity).
def PathlikeMulti(*args, **kwargs):
        base_tweenMethod = MultiFigure.Multi(*args, **kwargs)
        def tweenmethod(self, other, t, *args, **kwargs):
            tw = base_tweenMethod(self, other, t, *args, **kwargs)
            if len(tw.figures) > len(self.figures):
                # self's subfigures have been supplemented,
                # so apply segmentation to them
                diff = len(tw.figures) - len(self.figures)
                for n in range(diff):
                    tw.figures[n] = tw.figures[n].segment(0, t)
            elif len(tw.figures) > len(other.figures):
                # other's subfigures have been supplemented,
                # so apply segmentation to them
                diff = len(tw.figures) - len(other.figures)
                for n in range(diff):
                    tw.figures[n] = tw.figures[n].segment(0, 1-t)
            return tw
        return tweenmethod

# Decorator enables a Pathlike tween method to smoothly tween paths
# with non-matching deadends.
def handleDeadendInterp(tweenmethod):

    # Convert given tweenmethod into a MultiFigure tween method
    # so it can be applied to multiself and multiother.
    multiTweenMethod = PathlikeMulti(tweenmethod, morpho.Figure.tweenLinear)

    def wrapper(self, other, t, *args, **kwargs):
        # Do nothing fancy if both paths have identical deadends and node counts
        if len(self.deadends) == len(other.deadends) == 0 or \
            (len(self.deadends) == len(other.deadends) and \
            self.nodeCount() == other.nodeCount() and \
            self.deadends == other.deadends):

            return tweenmethod(self, other, t, *args, **kwargs)

        multiself = self.splitAtDeadends()
        multiother = other.splitAtDeadends()

        # Subpools are artificially set to 0 because PathlikeMulti()
        # assumes the supplemented subfigures are prepended to the
        # originals' figure lists, not evenly distributed which is
        # what is done by default. Not doing this will result in
        # certain morphs between different topological genuses failing
        # e.g. morphing PText("OO").toSpline() to PText("O").toSpline()
        multiself._subpool = [0]
        multiother._subpool = [0]

        multitweened = multiTweenMethod(multiself, multiother, t, *args, **kwargs)
        return multitweened.joinUsingDeadends()

    return wrapper

# Decorator modifies the tween methods of the Path class to support
# gradients for the color and alpha tweenables.
def handleGradients_old(twMethod):
    def wrapper(self, other, t, *args, **kwargs):
        # Use the original tween method as normal.
        # The given tween method should be designed to ignore
        # the color and alpha tweenables.
        tw = twMethod(self, other, t, *args, **kwargs)

        # Handle color tweenable

        # If both are gradients...
        if isinstance(self.color, morpho.color.Gradient) and isinstance(other.color, morpho.color.Gradient):
            tw.color = self.color.tweenLinear(other.color, t)
        # self is gradient but not other
        elif isinstance(self.color, morpho.color.Gradient):
            # othercopy = other.copy()
            othercopy_color = self.color.copy()
            for key in othercopy_color.data:
                othercopy_color[key] = list(other.color)
            tw.color = self.color.tweenLinear(othercopy_color, t)
        # other is gradient but not self
        elif isinstance(other.color, morpho.color.Gradient):
            # selfcopy = self.copy()
            selfcopy_color = other.color.copy()
            for key in selfcopy_color.data:
                selfcopy_color[key] = list(self.color)
            tw.color = selfcopy_color.tweenLinear(other.color, t)
        # neither are gradients
        else:
            tw.color = type(self.color)(map(morpho.numTween, self.color, other.color, (t,t,t)))

        # Handle alpha tweenable

        # If both are gradients...
        if isinstance(self.alpha, morpho.color.Gradient) and isinstance(other.alpha, morpho.color.Gradient):
            tw.alpha = self.alpha.tweenLinear(other.alpha, t)
        # self is gradient but not other
        elif isinstance(self.alpha, morpho.color.Gradient):
            # othercopy = other.copy()
            othercopy_alpha = self.alpha.copy()
            for key in othercopy_alpha.data:
                othercopy_alpha[key] = other.alpha
            tw.alpha = self.alpha.tweenLinear(othercopy_alpha, t)
        # other is gradient but not self
        elif isinstance(other.alpha, morpho.color.Gradient):
            # selfcopy = self.copy()
            selfcopy_alpha = other.alpha.copy()
            for key in selfcopy_alpha.data:
                selfcopy_alpha[key] = self.alpha
            tw.alpha = selfcopy_alpha.tweenLinear(other.alpha, t)
        # neither are gradients
        else:
            tw.alpha = morpho.numTween(self.alpha, other.alpha, t)

        return tw
    return wrapper


# Decorator modifies the tween methods of the Path class to support
# tweening between paths with different node counts.
def handlePathNodeInterp(tweenmethod):
    def wrapper(self, other, t, *args, **kwargs):
        len_self = len(self.seq)
        len_other = len(other.seq)

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
            other = other.copy()
            other.seq = insertNodesUniformlyTo(other.seq, len_self-len_other)
            return tweenmethod(self, other, t, *args, **kwargs)
        # Else other has more nodes, so insert extra nodes to a
        # copy of self before tweening
        else:
            selfcopy = self.copy()
            selfcopy.seq = insertNodesUniformlyTo(selfcopy.seq, len_other-len_self)
            # return super(Path, selfcopy).tweenLinear(other, t)
            return tweenmethod(selfcopy, other, t, *args, **kwargs)
    return wrapper

# Given an even-length dash pattern, returns a dash pattern
# of the same length which is equivalent to an empty (i.e. solid) dash
# pattern. Useful when tweening an empty dash with a non-empty dash.
def equivSolidDash(dash):
    if len(dash) % 2 == 1:
        raise IndexError("Given dash pattern must be even-length.")

    dash = np.array(dash, dtype=float)
    a = dash.copy()

    a[1::2] = 0
    a[::2] += dash[1::2]

    return a.tolist()


# Decorator modifies a tween method of a Figure that possesses
# a "dash" tweenable and enables it to handle tweening dashes
# of different lengths.
def handleDash(tweenmethod):
    def dashWrapper(self, other, t, *args, **kwargs):
        # Save the original dashes in case we have
        # to change them temporarily later
        selfdash_old = self.dash
        otherdash_old = other.dash

        m = len(self.dash)
        n = len(other.dash)
        # Both dashes are non-empty
        if m > 0 and n > 0:
            # Handle (easy) case that they have the same non-zero length
            if m == n:
                return tweenmethod(self, other, t, *args, **kwargs)

            # Repeat each dash pattern until they have the same length
            lcm = (m*n) // math.gcd(m,n)
            self.dash = self.dash*(lcm//m)
            other.dash = other.dash*(lcm//n)
            tw = tweenmethod(self, other, t, *args, **kwargs)

            # Restore original dash patterns
            self.dash = selfdash_old
            other.dash = otherdash_old

            return tw

        # Only self is non-empty
        elif m > 0:
            # Make the dash length an equivalent even length dash
            # if it's odd. This is necessary for equivSolidDash()
            # to work.
            if m % 2 == 1:
                self.dash = self.dash*2
            other.dash = equivSolidDash(self.dash)
            tw = tweenmethod(self, other, t, *args, **kwargs)

            # Restore original dash pattern to other
            other.dash = otherdash_old

            return tw

        # Only other is non-empty
        elif n > 0:
            # Make the dash length an equivalent even length dash
            # if it's odd. This is necessary for equivSolidDash()
            # to work.
            if n % 2 == 1:
                other.dash = other.dash*2
            self.dash = equivSolidDash(other.dash)
            tw = tweenmethod(self, other, t, *args, **kwargs)

            # Restore original dash pattern to self
            self.dash = selfdash_old

            return tw

        # Both dashes are empty
        else:
            return tweenmethod(self, other, t, *args, **kwargs)

    return dashWrapper

# Path object. Consists of a sequence of complex number positions
# defining a polygonal path. Approximates a curve for large vertex count.
#
# TWEENABLES
# seq = Vertex sequence (list of complex numbers). Default: [0,1]
# start = Initial draw point; a number between 0 and 1 where 0 is seq[0]
#         and 1 is seq[-1]
# end = Final draw point; a number between 0 and 1 where 0 is seq[0]
#       and 1 is seq[-1]
# color = Path color (RGB vector-like). Default: [1,1,1] (white)
#         Can also be a Gradient object (see morpho.color.Gradient)
# alpha = Opacity. Default: 1 (opaque)
# width = Path stroke thickness (in pixels). Default: 3
# headSize = Size of arrow head (in pixels). Default: 0 (no arrow head)
# tailSize = Size of arrow tail (in pixels). Default: 0 (no arrow tail)
# alphaEdge = Path opacity independent of fill. Default: 1 (opaque)
# fill = Interior fill color (RGB vector-like). Default: [1,0,0] (red)
#        Can also be a GradientFill object (see morpho.color.GradientFill)
# alphaFill = Interior opacity. Default: 0 (invisible)
# dash = Dash pattern. Works exactly like how it does in cairo. It's a list
#        of ints which are traversed cyclically and will alternatingly indicate
#        number of pixels of visibility and invisibility.
#        Note: Effect will not appear if "color" is a gradient.
# dashOffset = Where along the dash pattern it will start. Default: 0
# outlineWidth = Thickness of path outline (in pixels). Default: 0 (no outline)
# outlineColor = Outline color (RGB vector-like). Default: [0,0,0] (black)
# outlineAlpha = Outline opacity. Default: 1 (opaque)
# origin = Translation value (complex number). Default: 0 (complex number).
# rotation = Path rotation about origin point (radians). Default: 0
# transform = Transformation matrix applied after all else. Default: np.eye(2)
# deadends = Set of ints specifying indices of seq that are "deadends". Meaning
#            no line segment will be drawn from the deadend index to the next index.
#            This is mainly used under the hood by helper functions like mathgrid()
#            to speed up rendering.
#
# NON-TWEENABLE ATTRIBUTES
# headExternal/tailExternal = Boolean controlling arrow triangle
#       placement. If set to True, the arrow triangle's base will be
#       drawn at the corresponding path endpoint instead of its tip.
#       Both can be set simultaneously by setting `tipExternal`.
#       Default: False.
# outlineMethod = String indicating the rendering technique that should
#       be used to render outlines on paths. Supports two options:
#       "classic", "cap". By default "classic" is used, which gives
#       the best results in most cases, but can mess up for dashed
#       paths with large tailSize compared to node spacing.
#       If "cap" is used, outlines are rendered by using cairo's square
#       line caps, which produces decent results even for large tailSize.
#       The default outline method for all paths can be set by setting
#       the class attribute `Path.defaultOutlineMethod`.
class Path(BackgroundBoxFigure, AlignableFigure):
    defaultOutlineMethod = "classic"
    outlineMethods = ("classic", "cap")  # List of all supported outline styles

    def __init__(self, seq=None, width=3, color=(1,1,1), alpha=1):
        if seq is None:
            seq = [0,1]
        # Convert to list if not list
        elif not isinstance(seq, list):
            seq = list(seq)

        # morpho.Figure.__init__(self)
        super().__init__()

        seq = morpho.Tweenable(name="seq", value=seq, tags=["complex", "list"])
        start = morpho.Tweenable(name="start", value=0, tags=["scalar"])
        end = morpho.Tweenable(name="end", value=1, tags=["scalar"])
        color = morpho.Tweenable(name="color", value=color, tags=["color", "gradient", "notween"])
        alphaEdge = morpho.Tweenable(name="alphaEdge", value=1, tags=["scalar"])
        fill = morpho.Tweenable(name="fill", value=[1,0,0], tags=["color", "gradientfill", "notween"])
        alphaFill = morpho.Tweenable(name="alphaFill", value=0, tags=["scalar"])
        alpha = morpho.Tweenable(name="alpha", value=alpha, tags=["scalar"])
        width = morpho.Tweenable(name="width", value=width, tags=["size", "pixel"])
        headSize = morpho.Tweenable("headSize", 0, tags=["scalar", "pixel"])
        tailSize = morpho.Tweenable("tailSize", 0, tags=["scalar", "pixel"])
        dash = morpho.Tweenable("dash", [], tags=["scalar", "list", "pixel"])
        dashOffset = morpho.Tweenable("dashOffset", 0, tags=["scalar", "pixel"])
        outlineWidth = morpho.Tweenable("outlineWidth", value=0, tags=["size", "pixel"])
        outlineColor = morpho.Tweenable("outlineColor", value=[0,0,0], tags=["color"])
        outlineAlpha = morpho.Tweenable("outlineAlpha", value=1, tags=["scalar"])
        origin = morpho.Tweenable("origin", value=0, tags=["complex", "nofimage"])
        rotation = morpho.Tweenable("rotation", value=0, tags=["scalar"])
        _transform = morpho.Tweenable("_transform", np.identity(2), tags=["nparray"])

        self.extendState([seq, start, end, color, alphaEdge, fill, alphaFill, alpha,
            width, headSize, tailSize, dash, dashOffset,
            outlineWidth, outlineColor, outlineAlpha, origin, rotation, _transform]
            )

        # Set of indices that represent where a path should terminate.
        self.Tweenable("deadends", set(), tags=["notween"])

        # How to interpolate between the points given in the seq.
        # For now, the only interp method is "linear", which  means
        # connect successive points in the seq by straight lines.
        # self.interp = "linear"
        self.NonTweenable("interp", "linear")

        # The dash pattern for this line. The format is identical to how
        # pycairo handles dash patterns: each item in the list is how long
        # ON and OFF dashes are, where the list is read cyclically.
        # Defaults to [] which means make the line solid.
        # Note that specifying only one value to the dash list is interpreted
        # as alternating that dash width ON and OFF.
        # Also note that dash pattern is ignored if gradient colors are used.
        # self.dash = []

        self.NonTweenable("headExternal", False)
        self.NonTweenable("tailExternal", False)

        # The technique that should be used to render outlines
        self.NonTweenable("outlineMethod", self.defaultOutlineMethod)

        # # Should strokes occur behind fills?
        # self.NonTweenable("backstroke", False)

        # For internal use.
        # The vertices of an arrow triangle will be expanded by this
        # amount. Mainly for use internally when rendering arrow
        # arrow outlines using the "cap" outline method.
        self.NonTweenable("_tipExpand", 0)

    # # Returns a (deep-ish) copy of the path
    # def copy(self):
    #     # C = morpho.Figure.copy(self)
    #     C = super().copy()
    #     C.interp = self.interp
    #     C.deadends = self.deadends.copy()
    #     # C.dash = self.dash.copy() if not isinstance(self.dash, tuple) else self.dash
    #     return C

    @property
    def transform(self):
        return self._transform

    @transform.setter
    def transform(self, value):
        self._transform = morpho.matrix.array(value)

    # Setting `tipSize` property sets both `headSize` and `tailSize
    # to the same value.
    @property
    def tipSize(self):
        if self.headSize != self.tailSize:
            raise AmbiguousValueError("headSize and tailSize are different!")
        return self.headSize

    @tipSize.setter
    def tipSize(self, value):
        self.headSize = value
        self.tailSize = value

    @property
    def tipExternal(self):
        if self.headExternal != self.tailExternal:
            raise AmbiguousValueError("headExternal and tailExternal have different truth values.")
        return self.headExternal

    @tipExternal.setter
    def tipExternal(self, value):
        self.headExternal = value
        self.tailExternal = value

    @property
    def pos(self):
        return self.origin

    @pos.setter
    def pos(self, value):
        self.origin = value

    @property
    def data(self):
        return self.seq

    @data.setter
    def data(self, value):
        self.seq = value


    # Returns number of nodes in the path.
    # Equivalent to len(self.seq)
    def nodeCount(self):
        return len(self.seq)

    # Applies all of the transformation attributes
    # origin, rotation, transform
    # to the actual seq list itself and then
    # resets the transformation attributes.
    def commitTransforms(self):
        rot = cmath.exp(self.rotation*1j)  # Rotator complex number
        vector = rot*np.array(self.seq)  # Apply rotation and convert to np.array
        # Break apart real and imag parts into rows
        array = np.zeros((2,len(self.seq)))
        array[0,:] = vector.real
        array[1,:] = vector.imag
        # Apply transformation, convert back to complex vector and add origin
        arrayTransformed = (self._transform @ array)
        vectorTransformed = arrayTransformed[0,:] + 1j*arrayTransformed[1,:] + self.origin
        newSeq = vectorTransformed.tolist()

        self.seq = newSeq
        self.origin = 0
        self.rotation = 0
        self.transform = np.identity(2)
        return self

    # Returns physical bounding box of path as
    # [xmin, xmax, ymin, ymax]
    #
    # If optional kwarg `raw` is set to True, the
    # bounding box is computed without applying
    # the transformation attributes origin, rotation, transform.
    def box(self, *, raw=False):
        if self.nodeCount() == 0:
            raise ValueError("Cannot find bounding box of a path with no nodes.")

        # The check for self.origin != 0 is done elsewhere because
        # it's by far the most common transformation attribute to
        # modify, and it's not worth making a copy and committing
        # transforms if the only transform is a translation.
        if not raw and not(self.rotation == 0 and np.array_equal(self._transform, I2)):
            temp = self.copy()
            temp.commitTransforms()
            return temp.box()
        array = np.array(self.seq)
        return _calculateBoxFromArray(array, self.origin if not raw else 0)

    # Rescales the path by the given scale factors.
    # If a single scale factor is omitted it will copy its partner.
    #
    # This is a "pre-rescaling", meaning the scale factors should
    # be interpreted as applying to the raw path data BEFORE the
    # transformation attributes are applied.
    #
    # This method acts on the figure IN PLACE.
    def rescale(self, scale_x=None, scale_y=None):
        if scale_x is None and scale_y is None:
            raise TypeError("No scale factor provided to rescale()")
        elif scale_x is None:
            scale_x = scale_y
        elif scale_y is None:
            scale_y = scale_x

        # Old technique where transform attribute was modified
        # instead of path data. Decided modifying path data was
        # the better approach for LaTeX rendering.
        # # Need to conjugate by the rotation matrix since
        # # rotational action is applied before transform action.
        # rotator = morpho.matrix.rotation2d(self.rotation)
        # self._transform = self._transform @ rotator @ morpho.matrix.scale2d(scale_x, scale_y) @ rotator.T

        # Transform underlying data by sneakily using commitTransforms().
        # This makes this method usable without modification by
        # the MultiPath class.
        origin_orig = self.origin         # Save
        rotation_orig = self.rotation     # original
        transform_orig = self._transform  # transform data
        self.origin = 0
        self.rotation = 0
        self._transform = morpho.matrix.scale2d(scale_x, scale_y)
        self.commitTransforms()
        self.origin = origin_orig         # Restore
        self.rotation = rotation_orig     # original
        self._transform = transform_orig  # transform data

        return self

    # Resizes the path so that its absolute bounding box matches
    # the dimensions given. If either dimension is omitted, the figure
    # will be resized so as to keep the aspect ratio the same.
    #
    # This is a "pre-resizing", meaning boxWidth and boxHeight
    # should be interepreted as referring to the path BEFORE
    # transformations are applied.
    #
    # Note this applies to the figure IN PLACE.
    # See also: rescale()
    def resize(self, boxWidth=None, boxHeight=None):
        if boxWidth is None and boxHeight is None:
            raise TypeError("No dimension provided to resize()")
        elif boxWidth is None:
            scale_x = scale_y = boxHeight / self.boxHeight(raw=True)
        elif boxHeight is None:
            scale_x = scale_y = boxWidth / self.boxWidth(raw=True)
        else:
            scale_x = boxWidth / self.boxWidth(raw=True)
            scale_y = boxHeight / self.boxHeight(raw=True)

        self.rescale(scale_x, scale_y)
        return self

    # Closes the path IN PLACE if it is not already closed.
    def close(self):
        if len(self.seq) == 0:
            return self
        if self.seq[0] != self.seq[-1]:
            self.seq.append(self.seq[0])
        return self

    # Breaks the path into a list of the specified number of subpaths.
    # Leaves the original path unchanged.
    def split(self, chunks):
        subpaths = []

        # Temporarily remove the sequence list and color from the current path
        # so that copying will not copy the seq or the color (in case it's a grad)
        origSeq = self.seq
        self.seq = []

        # Also temporarily replace the color attribute if it's a gradient
        # so that we avoid making bazillions of unnecessary copies of the gradient.
        origColor = self.color
        gradMode = (isinstance(origColor, morpho.color.Gradient))
        if gradMode:
            self.color = [0,0,0]

        len_seq = len(origSeq)
        segcount = len_seq - 1
        chunks = min(chunks, len_seq-1)  # Max chunks is segment count.
        for n in range(chunks):
            subpath = self.copy()
            # a = (n*len_seq) // chunks
            # b = ((n+1)*len_seq) // chunks
            a = (n*segcount) // chunks
            b = ((n+1)*segcount) // chunks
            subpath.seq = origSeq[a:b+1]
            if gradMode:
                # subpath.color = origColor.segment(a/len_seq, b/len_seq)
                subpath.color = origColor.segment(a/segcount, b/segcount)
                subpath.color.normalize()
            subpaths.append(subpath)

        # Restore the original sequence and color to the current path.
        self.seq = origSeq
        self.color = origColor

        return subpaths

    # Returns a MultiPath figure that consists of continuous
    # paths taken from splitting the Path at its deadends.
    def splitAtDeadends(self):

        # Sort the deadends in ascending order
        deadends = list(self.deadends)
        deadends.sort()

        nodeCount = self.nodeCount()
        segCount = nodeCount - 1
        # Append the final node to the list to ensure the final
        # segment is included.
        deadends.append(segCount)

        start = 0  # Current starting index of path slicing.
        subpaths = []
        for deadend in deadends:
            if deadend <= start:  # Skip consecutive deadends
                start = deadend + 1
                continue
            subpath = self.segment(start/segCount, deadend/segCount)
            subpath.deadends = set()
            subpaths.append(subpath)
            start = deadend + 1
        return self._multitype(subpaths)

    # Applies interpSeqLinear() to uniformly add nodes to the given
    # path IN PLACE.
    # See `morpho.grid.insertNodesUniformlyTo()` for more info.
    def insertNodesUniformly(self, *args, **kwargs):
        self.seq = insertNodesUniformlyTo(self.seq, *args, **kwargs)
        return self

    # Returns the interpolated position along the path corresponding to the
    # parameter t, where t = 0 is the path start and t = 1 is the path end.
    # NOTE: This method ignores deadends and the transformation tweenables
    # origin, rotation, transform, as well as the "start" and "end"
    # parameters!
    def positionAt(self, t):
        if not(0 <= t <= 1):
            raise ValueError(f"Index parameter must be between 0 and 1. Got t = {t}")
        T = t*(len(self.seq)-1)
        index = int(T)

        # If this is the final node, just return it
        if index == len(self.seq) - 1:
            return self.seq[index]

        return morpho.numTween0(self.seq[index], self.seq[index+1], T-index)

    # Mainly for internal use.
    # Shifts/removes deadends according to taking a slice.
    # This operation acts IN PLACE.
    def _shiftDeadends(self, floor_A):
        # Shift/remove deadends
        newDeadends = set()
        for deadend in self.deadends:
            if deadend >= floor_A:
                newDeadends.add(deadend-floor_A)
        self.deadends = newDeadends
        return self

    def _reverseDeadends(self):
        # Reverse deadends
        nodeCount = self.nodeCount()
        maxIndex = nodeCount - 1
        newDeadends = set()
        for deadend in self.deadends:
            newDeadend = maxIndex - 1 - deadend
            if newDeadend >= 0:
                newDeadends.add(newDeadend)
        self.deadends = newDeadends
        return self

    # Returns a segment of a path between parameters a and b,
    # where a,b = 0 means path start and a,b = 1 means path end.
    def segment(self, a, b):
        reverse = not(a <= b)
        if reverse:
            a,b = b,a

        if not(0 <= a <= b <= 1):
            raise ValueError("Segment endpoints must satisfy 0 <= a,b <= 1")

        subpath = self.copy()
        if a == b:
            # raise ValueError("Segment endpoints cannot be the same.")
            subpath.seq = [self.positionAt(a)]
            return subpath

        # Compute fractional index values
        maxIndex = len(self.seq)-1
        A = a*maxIndex
        B = b*maxIndex

        # Round the fractional indices if they are super close
        # to an integer.
        tol = 1e-9
        if abs(A-round(A)) < tol:
            A = round(A)
        if abs(B-round(B)) < tol:
            B = round(B)

        subpath.seq = subpath.seq[math.floor(A):math.ceil(B)+1]
        if A != int(A):
            subpath.seq[0] = self.positionAt(a)
        if B != int(B):
            subpath.seq[-1] = self.positionAt(b)

        # Handle splitting a gradient color
        if isinstance(subpath.color, morpho.color.Gradient):
            # Paths assume the gradients are normalized,
            # so the following line is commented out.
            # subpath.color.normalize()
            subpath.color = subpath.color.segment(a,b)
            subpath.color.normalize()
            if reverse:
                subpath.color.reverse()

        # Shift/remove deadends
        subpath._shiftDeadends(int(A))

        # Reverse order if needed
        if reverse:
            subpath.seq.reverse()
            subpath._reverseDeadends()

        return subpath

    def __getitem__(self, t):
        # Handle singleton subscript
        if not isinstance(t, slice):
            t = slice(t,t)

        if t.step is not None:
            raise TypeError("Slice steps are not supported for path slicing.")

        a = t.start
        b = t.stop

        if a is None:
            a = 0
        if b is None:
            b = 1

        return self.segment(a,b)

    def __iter__(self):
        raise TypeError("Paths are not iterable")


    # Returns the physical length of the path
    # NOTE: ignores deadends and pretends all nodes are connected!
    # Also ignores the transform attribute.
    def arclength(self):
        return sum(abs(self.seq[n+1]-self.seq[n]) for n in range(len(self.seq)-1))


    # Returns the arclength so-far, where t is an index parameter between [0,1]
    # More precisely, it returns the length of the path with start=0 and end=t.
    # NOTE: ignores deadends and pretends all nodes are connected!
    def s(self, t):
        if not(0 <= t <= 1):
            raise ValueError("Index parameter must be in the interval [0,1]")
        T = t*(len(self.seq)-1)
        index = int(T)

        L = sum(abs(self.seq[n+1]-self.seq[n]) for n in range(index))
        if index == len(self.seq)-1:
            return L

        # L += abs(self.seq[index] - morpho.numTween(self.seq[index], self.seq[index+1], T-index))
        L += (T-index)*abs(self.seq[index] - self.seq[index+1])
        return L

    # The inverse of the so-far arclength function.
    # Takes an arclength s as input and returns the index parameter t
    # that corresponds to that length.
    # NOTE: ignores deadends and pretends all nodes are connected!
    def s_inv(self, s):
        if s < 0:
            raise ValueError("Given length must be nonnegative!")
        if s == 0:
            return 0

        ell = 0
        n = 0
        while ell < s and n < len(self.seq)-1:
            n += 1
            ell += abs(self.seq[n] - self.seq[n-1])

        if ell < s:
            raise ValueError("Given length is longer than the path length!")
        # if n == len(self.seq) - 1:
        #     return 1

        # Segment that is split
        segment = abs(self.seq[n] - self.seq[n-1])
        T = n + (s-ell)/segment
        return T/(len(self.seq)-1)


    # Returns a transition function such that
    # tweening from start=0, end=0 to start=0, end=1
    # results in a constant speed drawing of the path.
    def constantSpeedTransition(self):
        L = self.arclength()
        return lambda t: self.s_inv(L*t)

    # Returns the center of mass of all nodes in the Path
    # ignoring transformation attributes.
    # That is, returns mean(path.seq)
    def centroid(self):
        return mean(self.seq)

    # Converts the Path into an equivalent Spline figure.
    # Note that some attributes cannot transfer over, such as
    # arrow tips and outlines, since Spline does not support
    # these features.
    def toSpline(self):
        import morpholib.shapes

        spline = morpho.shapes.Spline()
        spline._updateFrom(self, common=True)
        spline.newNodes(self.seq)

        return spline

    # NOTE: FOR INTERNAL USE ONLY! NOT WELL-MAINTAINED. USE AT OWN RISK!
    # Returns boolean on whether a path has the same
    # color and width as another. This method is useful
    # in optimizing how paths are drawn.
    # WARNING: matchesStyle() can return a false positive
    # when using gradients because self and other possessing
    # the same gradient does not imply their concatenation
    # would use the same gradient. Fix this in future.
    def matchesStyle(self, other):
        return (self.color == other.color and \
            self.alpha == other.alpha and \
            self.width == other.width and \
            self.static == other.static and \
            self.interp == other.interp and \
            self.dash == other.dash and \
            self.defaultTween == other.defaultTween)

    # PROBABLY OBSOLETE METHOD. DO NOT USE.
    # Convenience method that sets up the OpenGL lines
    # before glBegin(GL_LINES) is called.
    def setupStyle(self):
        R,G,B = self.color
        A = self.alpha
        pg.gl.glEnable(pyglet.gl.GL_BLEND)
        pg.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA, pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        pg.gl.glLineWidth(self.width)
        pg.gl.glColor4f(float(R), float(G), float(B), float(A))

    # Mainly for internal use.
    # Expands the triangle vertices of an arrow tip
    # evenly away from its centerpoint. Mainly used
    # in generating outlined arrows.
    # `amount` is the amount to expand (additively)
    # `size` is the length of one of the triangle's sides
    # (exists so that the function doesn't have to recompute it).
    @staticmethod
    def _expandVertices(vertices, amount, size):
        if amount == 0:
            return vertices

        size = abs(size)
        vertices = np.array(vertices, dtype=complex)
        factor = 1 + 4*root3over2*amount/size
        center = sum(vertices)/len(vertices)
        vertices = factor*(vertices-center) + center
        return vertices.tolist()

    # For internal use by the draw() method.
    # Adjusts the vertex sequence for an outline path being rendered
    # in the classic way so that the outline uniformly covers the original.
    # Also computes what the new arrow size should be and returns it.
    def _adjustSeqForOutline(back, camera, ctx, endIndex, prevIndex,
            outlineWidth, arrowDraw, arrowSize, arrowExternal,
            xRatio, yRatio, Tmat):

        diff = back.seq[endIndex] - back.seq[prevIndex]  # Ending segment vector
        diff_length = abs(diff)
        unit = diff/abs(diff) if diff != 0 else 1  # Endpoint direction vector
        UNIT = unit.real/xRatio + 1j*unit.imag/yRatio
        UNIT = UNIT/abs(UNIT)  # Pixel space direction vector
        dL = outlineWidth*UNIT  # Pixel outline thickness vector
        dX, dY = dL.real, dL.imag
        dx = morpho.physicalWidth(dX, camera.view, ctx)
        dy = morpho.physicalHeight(dY, camera.view, ctx)
        dl = abs(complex(dx,dy))  # Outline thickness physical vector
        if arrowDraw:
            sign = sgn(arrowSize)
            arrowSize += 4*root3over2*outlineWidth*sign
            if arrowExternal:
                shift = -sign*dl
            else:
                shift = sign*2*dl
        else:
            shift = dl
        # `shift` is the amount to shift the final node of the
        # outline path so that the outline evenly covers the
        # original path.

        # Rescale `shift` to account for scaling distortions
        # caused by transformations
        if diff != 0:
            shift *= abs(diff)/abs(Tmat*diff)

        # If the final node will be shifted basically on top of
        # the penultimate node, slightly perturb the shift value
        # to eliminate possible precision issues when calculating
        # tip direction.
        if shift < 0 and abs(shift + diff_length) < 1e-9*diff_length:
            shift += 1e-8*diff_length

        # Reverse tip direction if the final node is going to be
        # shifted behind the penultimate node.
        if shift < 0 and abs(shift) > diff_length:
            arrowSize *= -1

        # Shift the final node by the shift amount.
        back.seq[endIndex] += shift*unit

        return arrowSize

    # For internal use by the draw() method.
    # Draws the outline of a path.
    def _drawOutline(self, camera, ctx, init, final,
        headDraw, tailDraw, xRatio, yRatio):

        # Create a temporary copy of the path which will serve as
        # the outline
        back = self.copy()
        back.width = abs(self.width)

        # Take only a slice of the original sequence if needed
        if back.start != 0 or back.end != 1:
            back.seq = back.seq[init:final+1]
            # Shift deadend index set to account for new index 0
            deadends = set()
            for deadend in self.deadends:
                new = deadend - init
                if new >= 0:
                    deadends.add(new)
            back.deadends = deadends
            back.start = 0
            back.end = 1

        # Update back's style parameters
        back.color = self.outlineColor
        back.alpha = self.outlineAlpha*self.alpha
        back.alphaFill = 0  # Outline should never use a fill
        back.outlineWidth = 0
        # We double it because width represents diameter, and the outline
        # needs to appear on two sides. So an outlineWidth of 1px corresponds
        # to a widening by 2px (1px on each side)
        back.width += 2*self.outlineWidth

        if self.outlineMethod == "cap":
            ctx.set_line_cap(cairo.LINE_CAP_SQUARE)
            back._tipExpand = self.outlineWidth
        else:  # Classic rendering
            # Compute transformation factor matrix
            Tmat = morpho.matrix.Mat(self._transform @ morpho.matrix.rotation2d(self.rotation)) if not np.array_equal(self._transform, I2) else 1

            # Handle head
            back.headSize = back._adjustSeqForOutline(
                camera, ctx, -1, -2,
                self.outlineWidth, headDraw, self.headSize, self.headExternal,
                xRatio, yRatio, Tmat
                )

            # Handle tail
            back.tailSize = back._adjustSeqForOutline(
                camera, ctx, 0, 1,
                self.outlineWidth, tailDraw, self.tailSize, self.tailExternal,
                xRatio, yRatio, Tmat
                )
            # Offset the dash by the outline width if
            # tailSize is positive
            if self.tailSize > 0:
                back.dashOffset += 2*self.outlineWidth

            # Dash adjustment
            if len(back.dash) > 0:
                dash = list(back.dash)

                # If dash pattern is odd, make it an equivalent even
                # version by concatenating it with itself.
                if len(dash) % 2 == 1:
                    dash = dash*2

                adjust = 2*self.outlineWidth
                for i in range(len(dash)):
                    dash[i] += adjust
                    adjust *= -1

                # Check for negative dash steps and adjust accordingly
                for i in range(1, len(dash), 2):
                    # Only need to check odd indices since those are the ones
                    # that are reduced.
                    step = dash[i]
                    if step < 0:
                        dash[i-1] += step
                        dash[i] = 0

                back.dash = dash

        # I'm changing back.draw() to Path.draw(back) because
        # that seems to be the better convention based on how I've
        # used subclasses of Path before. But I'm not 100% sure this
        # is a good convention long-term as it forces subclasses
        # of Path to draw outlines only using the Path draw() method,
        # meaning the drawing of outlines may not be easily changed
        # by subclasses. At least for now, that's the behavior I want,
        # but consider changing it back if that seems better.
        Path.draw(back, camera, ctx)
        # back.draw(camera, ctx)
        ctx.set_line_cap(cairo.LINE_CAP_BUTT)

    # For internal use by the draw() method.
    # Computes the arrow triangle vertex triplet as well as
    # the modified location of the path's endpoint.
    def _computeArrowVerticesAndNewTip(
        self, camera, ctx, head, tail, arrowSize, arrowExternal,
        mat, mat_inv, rot, origin
        ):

        # Initialize arrow triangle base to the original head.
        base = head

        # Update head and tail according to transformations
        head = mat*(rot*head) + origin
        tail = mat*(rot*tail) + origin

        HEAD = vect2complex(morpho.anim.screenCoords(head, camera.view, ctx))
        TAIL = vect2complex(morpho.anim.screenCoords(tail, camera.view, ctx))
        BODY = HEAD - TAIL
        DIR = BODY/abs(BODY) if BODY != 0 else 1

        # Draw the arrowhead
        X,Y = morpho.screenCoords(head, camera.view, ctx)
        pxlA = X + 1j*Y
        if arrowExternal:
            pxlA += root3over2*arrowSize*DIR
        else:
            # Adjust the end node temporarily to be located at the
            # base of the arrowhead.
            D_head = -arrowSize*root3over2*DIR
            BASE = pxlA + D_head
            base = morpho.physicalCoords(BASE.real, BASE.imag, camera.view, ctx)

            # Undo transforms
            base = (mat_inv*(base - origin))/rot

        # Define the other two pixels and assemble them
        pxlB = pxlA + arrowSize*DIR*ccw150
        pxlC = pxlA + arrowSize*DIR*cw150

        vertices = (pxlA, pxlB, pxlC)

        # Expand vertices if needed
        vertices = Path._expandVertices(vertices, self._tipExpand, arrowSize)

        return vertices, base

    def _drawStroke(self, ctx, rgba):
        # Set line width & color & alpha
        width = abs(self.width)
        if width >= 0.5:  # Don't stroke if width is too small
            ctx.set_line_width(width)
            ctx.set_source_rgba(*rgba)
            ctx.set_dash(self.dash, self.dashOffset)
            ctx.stroke_preserve()
            ctx.set_dash([])  # Remove dash pattern and restore to solid strokes

    def _drawFill(self, camera, ctx):
        # Handle gradients
        if self.alphaFill > 0:
            if isinstance(self.fill, morpho.color.GradientFill):
                self.fill.draw(camera, ctx, self.alphaFill*self.alpha, pushPhysicalCoords=False)
            # Handle normal colors
            else:
                ctx.set_source_rgba(*self.fill, self.alphaFill*self.alpha)
                ctx.fill_preserve()

    def draw(self, camera, ctx):
        # This method is admittedly a mess. It should really be cleaned up and
        # streamlined, but I'm so scared of breaking it! There are so many cases
        # to test and the Path figure is a critically important figure.

        self._drawBackgroundBox(camera, ctx, self.origin, self.rotation, self._transform)

        # Don't bother drawing an invisible path.
        if self.alpha == 0:
            return

        tol = 1e-9  # Floating point error tolerance

        # Handle trivial length path and start >= end.
        len_seq = len(self.seq)
        maxIndex = len(self.seq) - 1
        if maxIndex < 1 or self.start + tol > self.end:
            return

        # Handle out-of-bounds start and end
        if not(0 <= self.start <= 1 and 0 <= self.end <= 1):
            backAlpha_orig = self.backAlpha
            self.backAlpha = 0
            drawOutOfBoundsStartEnd(self, camera, ctx)
            self.backAlpha = backAlpha_orig
            return

        # Set initial transformation values to be identities
        origin = self.origin
        rot = mat = 1
        mat_inv = 1

        # Compute new transformation values as needed
        if self.rotation != 0:
            rot = cmath.exp(self.rotation*1j)
        if not np.allclose(self.transform, I2):
            # If transform matrix is too distorted, don't draw.
            if morpho.matrix.thinness2x2(self.transform) < 1e-6:
                return
            mat = morpho.matrix.Mat(*self.transform.flatten().tolist())
            mat_inv = mat.inv

        # Compute index bounds.
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
        # if start is a deadend or in the void between visible nodes.
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

        # If, after the adjustment, we get an empty path,
        # do nothing.
        if start > end:
            return

        # Compute true initial and true final indices
        init = math.floor(start)
        final = math.ceil(end)

        # Save initial and final nodes because they may get
        # temporarily modified in the code below and need to be
        # restored later.
        oldTail = self.seq[init]
        oldHead = self.seq[final]

        # TEMPORARY FOR TESTING! COMMENT OUT OR DELETE LATER!
        # oldSeq = self.seq[:]

        # Temporarily modify self.seq in place to account
        # for non-integer start and end
        # oldStart = self.seq[int_start]
        if start != int_start:
            self.seq[init] = morpho.numTween(
                oldTail, self.seq[int_start+1], start-int_start
                )
        if end != int_end:
            # oldEnd = self.seq[int_end+1]
            self.seq[final] = morpho.numTween(
                (self.seq[int_end] if int_end != int_start else oldTail), oldHead, end-int_end
                )

        # CALCULATE BOOLEAN FLAGS FOR VARIOUS SITUATIONS

        # Should an outline path be drawn underneath the path?
        useOutline = (self.outlineWidth > 0 and self.outlineAlpha > 0)

        # Does an arrow head need to be drawn?
        headDraw = (self.headSize != 0 and \
            not isbadnum(self.seq[final-1]) and \
            not isbadnum(self.seq[final]) and \
            final not in self.deadends)

        # Does an arrow tail need to be drawn?
        tailDraw = (self.tailSize != 0 and \
            not isbadnum(self.seq[init]) and \
            not isbadnum(self.seq[init+1]) and \
            init not in self.deadends)

        # Compute some quantities that will be needed for
        # adjusting the start and end nodes to make the arrowheads
        # look better.
        view = camera.view
        if useOutline or self.headSize != 0 or self.tailSize != 0:
            xRatio = (view[1] - view[0])/ctx.get_target().get_width()
            yRatio = (view[3] - view[2])/ctx.get_target().get_height()
        else:
            xRatio = None
            yRatio = None

        # Draw outlined version if needed
        # (NOTE: This block may need to be re-implemented later because
        # it currently doesn't QUITE handle non-trivial transform
        # attribute. However, I'm not in a big rush, because
        # it doesn't look that off and modifying transform is a very
        # rare thing to do, esp. with outlines too.)
        if useOutline:
            self._drawOutline(camera, ctx, init, final,
                headDraw, tailDraw, xRatio, yRatio
                )


        # Setup color parameters
        if isinstance(self.color, morpho.color.Gradient):
            if len(self.color) == 0:
                raise ValueError("Color gradient is empty!")
        else:
            R,G,B = self.color
        A = self.alpha*self.alphaEdge


        # Populate RGBA lists with color depending on whether color
        # is a gradient or not
        if isinstance(self.color, morpho.color.Gradient):
            # Flag for if color gradient contains RGBA data, not RGB.
            RGBAmode = (len(list(self.color.data.values())[0]) == 4)

            # RGBA_start = list(self.color.value((start+0.5)/len(self.seq)))
            # RGBA_end = list(self.color.value((end+0.5)/len(self.seq)))
            RGBA_start = list(self.color.value(start/maxIndex))
            RGBA_end = list(self.color.value(end/maxIndex))
            if RGBAmode:
                RGBA_start[3] *= A
                RGBA_end[3] *= A
            else:
                RGBA_start.append(A)
                RGBA_end.append(A)
        else:
            RGBA_start = [R,G,B,A]
            RGBA_end = [R,G,B,A]

        # Draw arrows if necessary.
        # Compute head and tail nodes
        head = self.seq[final]
        head_prev = self.seq[final-1]
        tail = self.seq[init]
        tail_prev = self.seq[init+1]
        if headDraw:
            headVertices, newHead = self._computeArrowVerticesAndNewTip(
                camera, ctx,
                head, head_prev, self.headSize, self.headExternal,
                mat, mat_inv, rot, origin
                )
            self.seq[final] = newHead
        if tailDraw:
            tailVertices, newTail = self._computeArrowVerticesAndNewTip(
                camera, ctx,
                tail, tail_prev, self.tailSize, self.tailExternal,
                mat, mat_inv, rot, origin
                )
            self.seq[init] = newTail


        ### BEGIN DRAWING THE PATH IN CAIRO ###

        # Initialize starting point
        zn = self.seq[init]

        # Temporarily modify cairo coordinates to coincide with
        # physical coordinates.
        morpho.pushPhysicalCoords(view, ctx)  # Contains a ctx.save()

        # Handle possible other transformations
        if self.origin != 0:
            ctx.translate(self.origin.real, self.origin.imag)
        if not np.array_equal(self.transform, I2):
            xx, xy, yx, yy = self.transform.flatten().tolist()
            # Order is MATLAB-style: top-down, then left-right. So the matrix
            # specified below is:
            # [[xx  xy]
            #  [yx  yy]]
            mat = cairo.Matrix(xx, yx, xy, yy)
            # Apply to context
            ctx.transform(mat)
        if (self.rotation % tau) != 0:
            ctx.rotate(self.rotation)


        # X,Y = morpho.screenCoords(zn, view, ctx)
        x,y = zn.real, zn.imag
        # Convert width from pixels to physical
        p_width = morpho.physicalWidth(abs(self.width), view, ctx)
        p_semiwidth = p_width / 2
        p_semiwidth_i = 1j*p_semiwidth

        ctx.move_to(x,y)

        # Extract these objects so that we can save
        # on repeated Figure tweenable accesses (which
        # may be slow).
        self_seq = self.seq
        self_deadends = self.deadends
        self_color = self.color
        if isinstance(self.color, morpho.color.Gradient):
            pat = cairo.MeshPattern()
            ortho_prev = 0
            for n in range(init, final):
                # Get next node
                z = self_seq[n+1]
                # Get xy coords of both nodes
                xn, yn = zn.real, zn.imag
                x, y = z.real, z.imag

                # If previous node is a deadend, move to next node,
                # else draw a line to the next node.
                if n in self_deadends or isbadnum(z) or isbadnum(zn):
                    ctx.move_to(x,y)
                    ortho_prev = 0
                else:
                    ctx.line_to(x,y)

                    # Create patch
                    delta = z - zn
                    if abs(delta) != 0:
                        ortho = p_semiwidth_i * delta/abs(delta)

                        # Get colors from gradient
                        RGBA_zn = list(self_color.value(n/maxIndex))
                        RGBA_z = list(self_color.value((n+1)/maxIndex))
                        if RGBAmode:
                            RGBA_zn[3] *= A
                            RGBA_z[3] *= A
                        else:
                            RGBA_zn.append(A)
                            RGBA_z.append(A)

                        # Bowtie using previous ortho covers the
                        # seam from connecting two legs.
                        if ortho_prev != 0:
                            c0 = zn + ortho_prev
                            c1 = zn + ortho
                            c2 = zn - ortho
                            c3 = zn - ortho_prev

                            pat.begin_patch()
                            pat.move_to(c0.real, c0.imag)
                            pat.line_to(c1.real, c1.imag)
                            pat.line_to(c2.real, c2.imag)
                            pat.line_to(c3.real, c3.imag)

                            pat.set_corner_color_rgba(0, *RGBA_zn)
                            pat.set_corner_color_rgba(1, *RGBA_zn)
                            pat.set_corner_color_rgba(2, *RGBA_zn)
                            pat.set_corner_color_rgba(3, *RGBA_zn)
                            pat.end_patch()

                        # Add new gradient patch for the next leg.
                        c0 = zn + ortho
                        c1 = zn - ortho
                        c2 = z - ortho
                        c3 = z + ortho

                        pat.begin_patch()
                        pat.move_to(c0.real, c0.imag)
                        pat.line_to(c1.real, c1.imag)
                        pat.line_to(c2.real, c2.imag)
                        pat.line_to(c3.real, c3.imag)

                        pat.set_corner_color_rgba(0, *RGBA_zn)
                        pat.set_corner_color_rgba(1, *RGBA_zn)
                        pat.set_corner_color_rgba(2, *RGBA_z)
                        pat.set_corner_color_rgba(3, *RGBA_z)
                        pat.end_patch()

                        # Save copy of previous ortho
                        ortho_prev = ortho


                # Update zn to z
                zn = z

            ctx.set_source(pat)
            ctx.stroke()
            ctx.restore()

        # Color is not a gradient. Color as normal.
        else:
            for n in range(init, final):
                # if isinstance(self.color, morpho.color.Gradient):
                #     # Redefine color/alpha for gradients
                #     RGBA = list(self.color.value((n+0.5)/len_seq))
                #     RGBA.append(A)


                #     ctx.stroke()
                #     ctx.set_source_rgba(*RGBA)
                #     ctx.move_to(x,y)

                # Get next node
                z = self_seq[n+1]
                # X,Y = morpho.screenCoords(z, view, ctx)
                x,y = z.real, z.imag

                # If previous node is a deadend, move to next node,
                # else draw a line to the next node.
                if n in self_deadends or isbadnum(z) or isbadnum(zn):
                    ctx.move_to(x,y)
                else:
                    ctx.line_to(x,y)

                # Update zn to z
                zn = z

            # Auto-close path if the path has the simplest possible settings
            if self.seq[0] == self.seq[-1] and \
                self.start == 0 and self.end == 1 and \
                len(self.deadends) == 0 and \
                self.headSize == 0 and self.tailSize == 0:

                ctx.close_path()

            # Stroke and fill the path
            if self.width < 0:
                # Draw stroke first, then fill
                ctx.restore()
                self._drawStroke(ctx, RGBA_start)
                with morpho.pushPhysicalCoords(view, ctx):
                    self._drawFill(camera, ctx)
            else:
                # Fill first, then draw stroke
                self._drawFill(camera, ctx)
                ctx.restore()
                self._drawStroke(ctx, RGBA_start)
            ctx.new_path()  # Reset cairo path

        # Handle actually drawing head and tail now.
        # The delay is so that the triangles are drawn in front
        # of the path, which is important when the path is a gradient.
        if headDraw:
            cairo_triangle(ctx, *headVertices, RGBA_end)
        if tailDraw:
            cairo_triangle(ctx, *tailVertices, RGBA_start)

        # # Restore modified nodes if necessary
        # if end != int_end:
        #     self.seq[int_end+1] = oldEnd
        # elif headDraw:
        #     self.seq[final] = oldHead

        # if start != int_start:
        #     self.seq[int_start] = oldStart
        # elif tailDraw:
        #     self.seq[init] = oldTail

        # Restore initial and final nodes if they were
        # temporarily modified.
        self.seq[init] = oldTail
        self.seq[final] = oldHead

        # TEMPORARY FOR TESTING! COMMENT OUT OR DELETE LATER!
        # assert self.seq == oldSeq


    # Concatenates other to self in place. Does not modify other.
    # self retains its original style parameters, though.
    # Supplying False to the parameter "connectEnds" causes the
    # concatenated path to not connect the last node of self
    # to the first node of other.
    # Also ignores "origin", "rotation", and "transform" attributes
    # for now. Only use this method with paths that have the standard
    # transforms.
    def concat(self, other, connectEnds=True):
        # result = self.copy()
        old_len = len(self.seq)
        self.seq += other.seq
        # if isinstance(self, PathPolar) and isinstance(other, PathPolar):
        #     self.windSeq += other.windSeq
        if not connectEnds:
            self.deadends.add(old_len-1)

        # Merge deadends from other into self
        len_self = len(self.seq)
        for n in other.deadends:
            self.deadends.add(n+len_self)

        return self

        # return result

    # Notation: self + other
    # Returns a copy of self concatenated with other.
    # Assumes you want to connect ends.
    # Note using + will NOT modify self!
    def __add__(self, other):
        copy = self.copy()
        copy.concat(other)
        return copy

    ### TWEEN METHODS ###

    @morpho.TweenMethod
    @handleDeadendInterp
    @handleDash
    @morpho.color.handleGradients(["color"])
    @morpho.color.handleGradientFills(["fill"])
    @handlePathNodeInterp
    def tweenLinear(self, other, t):
        tw = super().tweenLinear(other, t)

        # # Linearly tween the node sequence manually
        # # BUT WHY???
        # tw.seq = type(tw.seq)(morpho.numTween(self.seq[n], other.seq[n], t) for n in range(len(self.seq)))
        return tw

    @classmethod
    def tweenPivot(cls, angle=tau/2):
        pivot = super().tweenPivot(angle)
        # Apply necessary decorators
        pivot = handlePathNodeInterp(pivot)
        pivot = morpho.color.handleGradientFills(["fill"])(pivot)
        pivot = morpho.color.handleGradients(["color"])(pivot)
        pivot = handleDash(pivot)
        pivot = handleDeadendInterp(pivot)
        # Enable splitting
        pivot = morpho.pivotTweenMethod(cls.tweenPivot, angle)(pivot)

        return pivot


    # Returns an interpolated path between itself and another path.
    @morpho.TweenMethod
    @handleDeadendInterp
    @handleDash
    @morpho.color.handleGradients(["color"])
    @morpho.color.handleGradientFills(["fill"])
    @handlePathNodeInterp
    def tweenSpiral(self, other, t, angle_tol=0.053):
        p = self
        q = other
        if p == q:
            return p.copy()
        # Check for invalid path seq lengths
        if len(p.seq) != len(q.seq):
            raise Exception("Can't tween paths of different seq lengths!")

        # T = p.copy()

        # Use standard figure linear tween to tween every tweenable
        # except color, alpha, and seq.
        T = morpho.Figure.tweenSpiral(self, other, t, ignore={"seq"})
        # T.color = morpho.tools.color.colorTween(p.color, q.color, t)
        # # Tween the stroke widths if necessary
        # if p.width != q.width:
        #     T.width = morpho.numTween(p.width, q.width, t)
        #     # T.width = p.width + t*(q.width - p.width)

        # # Integer tween the start and end.
        # T.start = morpho.intTween(p.start, q.start, t)
        # T.end = morpho.intTween(p.end, q.end, t)

        # # Perform spiral tween on the seq
        # dthList = []
        # for n in range(len(p.seq)):
        #     r1 = abs(p.seq[n])
        #     r2 = abs(q.seq[n])
        #     th1 = cmath.phase(p.seq[n]) % tau
        #     th2 = cmath.phase(q.seq[n]) % tau

        #     dr = r2-r1
        #     dth = argShift(th1, th2)
        #     dthList.append(dth)

        #     r = r1 + t*dr
        #     th = th1 + t*dth

        #     T.seq[n] = r*cmath.exp(th*1j)

        pseq = np.array(p.seq, dtype=complex)
        qseq = np.array(q.seq, dtype=complex)

        r1 = abs(pseq)
        r2 = abs(qseq)
        th1 = np.angle(pseq)
        th2 = np.angle(qseq)

        dr = r2 - r1
        dth = argShiftArray(th1, th2)

        r = r1 + t*dr
        th = th1 + t*dth

        T.seq = (r*np.exp(th*1j)).tolist()

        # This clause disconnects two nodes if they are
        # revolving in different directions too much.
        # The value angle_tol represents how far two oppositely
        # revolving nodes have to angularly differ before
        # we disconnect them.
        # if 0.01 < t and t < 0.99:
        #     for n in range(len(dthList)-1):
        #         dth1 = dthList[n]
        #         dth2 = dthList[n+1]
        #         if dth1*dth2 < 0 and abs(dth1-dth2) > angle_tol:
        #             T.deadends.add(n)

        # This clause disconnects two nodes if they are
        # revolving in different directions too much.
        # The value angle_tol represents how far two oppositely
        # revolving nodes have to angularly differ before
        # we disconnect them.
        if 0.01 < t < 0.99:
            dth1 = dth[:-1]
            dth2 = dth[1:]
            flagset = (dth1*dth2 < 0) * (abs(dth1-dth2) > angle_tol)
            T.deadends.update(np.where(flagset)[0].tolist())

        return T

# Animates a path actor appearing by "growing in" from a single point.
# The starting point is always the initial node in the sequence.
# See also: morpho.actions.fadeIn()
@Path.action
def growIn(path, duration=30, atFrame=None, *, reverse=False):
    if atFrame is None:
        atFrame = path.lastID()

    path0 = path.last()
    start, end, headSize, tailSize = path0.start, path0.end, path0.headSize, path0.tailSize
    path0.visible = False
    path1 = path.newkey(atFrame)
    path1.set(headSize=0, tailSize=0, visible=True)
    if reverse:
        path1.set(start=1, end=1)
    else:
        path1.set(start=0, end=0)
    path2 = path.newendkey(duration)
    path2.set(start=start, end=end, headSize=headSize, tailSize=tailSize)

@Path.action
def shrinkOut(path, duration=30, atFrame=None, *, reverse=False):
    if atFrame is None:
        atFrame = path.lastID()

    path.newkey(atFrame)
    path1 = path.newendkey(duration)
    path1.set(headSize=0, tailSize=0, visible=False)
    if reverse:
        path1.start = 1
    else:
        path1.end = 0

# Animates a Path actor appearing by enlarging from a focus point.
# By default the focus point is taken to be the origin position of
# the path, but this can be changed by passing in a position value
# to the `focus` optional kwarg. Note that the coordinates will be
# taken within the path's LOCAL coordinates (i.e. relative to
# the path's transformation attributes). Alternatively, an `align`
# parameter can be passed in by keyword to specify the focus point
# in terms of a location on the path's bounding box.
@Path.action
def popIn(path, duration=30, atFrame=None, *, align=None, focus=0):
    if atFrame is None:
        atFrame = path.lastID()

    path0 = path.last()
    final = path0.copy().set(visible=True)
    path0.visible = False
    if align is not None:
        focus = path0.anchorPoint(align, raw=True)
    path1 = path.newkey(atFrame, path0.fimage(lambda z: focus))
    path1.set(width=0, outlineWidth=0)
    path1.visible = True
    path.newendkey(duration, final)

# Animates a Path actor disappearing by shrinking to a focus point.
# By default the focus point is taken to be the origin position of
# the path, but this can be changed by passing in a position value
# to the `focus` optional kwarg. Note that the coordinates will be
# taken within the path's LOCAL coordinates (i.e. relative to
# the path's transformation attributes). Alternatively, an `align`
# parameter can be passed in by keyword to specify the focus point
# in terms of a location on the path's bounding box.
@Path.action
def popOut(path, duration=30, atFrame=None, *, align=None, focus=0):
    if atFrame is None:
        atFrame = path.lastID()

    if align is not None:
        focus = path.last().anchorPoint(align, raw=True)
    path.newkey(atFrame)
    path.newendkey(duration, path.last().fimage(lambda z: focus))
    path.last().set(width=0, outlineWidth=0)
    path.last().visible = False

# Highlights the Path actor
@Path.action
def highlight(actor, duration=15, atFrame=None, *,
    width=-3, fill=(1,1,0), color=(0,0,0), rescale=1,
    **kwargs):

    if atFrame is None:
        atFrame = actor.lastID()

    path0 = actor.last()

    # Leave values unchanged if specified as None
    if width is None:
        width = path0.width
    if fill is None:
        fill = path0.fill[:]
    if color is None:
        color = path0.color[:]

    path1 = actor.newkey(atFrame)
    path2 = actor.newendkey(duration)
    path2.set(width=width, color=color, **kwargs)
    if fill is not None:
        path2.set(fill=fill)
    if rescale != 1:
        path2.transform = morpho.matrix.scale2d(rescale) @ path2.transform

# Highlights then immediately de-highlights the Path actor.
# Optional keyword input `pause` can be used to specify a number
# of frames to pause after highlighting and before de-highlighting.
# Note that the `duration` parameter here refers to the time to take
# to get completely highlighted, not the duration for the entire
# animation. That is, `duration` really refers to the "half-duration"
# of the entire animation.
@Path.action
def flourish(actor, duration=15, atFrame=None, *, pause=0, **kwargs):

    if atFrame is None:
        atFrame = actor.lastID()

    path0 = actor.last()
    path1 = actor.newkey(atFrame)

    actor.highlight(duration, atFrame, **kwargs)
    if pause > 0:
        actor.newendkey(pause)
    actor.newendkey(duration, path1.copy())

# Draws in a Path actor Manim-style.
#
# OPTIONAL KEYWORD-ONLY INPUTS
# tempWidth = Temporary stroke width to use in the animation
#       if the stroke width is 0. Default: 3
# transition = Transition to use in the animation.
#       Note that this only applies to the portion of the actor's
#       timeline affected by this action. After the action
#       concludes, the original transition of this actor will
#       be used for future keyfigures.
#       Default: morpho.transition.default
@Path.action
def drawIn(actor, duration=30, atFrame=None, *,
    tempWidth=2, transition=None):

    if atFrame is None:
        atFrame = actor.lastID()
    if transition is None:
        transition = mo.transition.default

    path0 = actor.last()
    # Save current final state of the actor which should be
    # the same final state when this action is finished.
    final = path0.copy()
    path0.set(start=0, end=0, alphaFill=0, alphaEdge=1, static=False)
    path0.transition = transition
    # Give a temporary stroke width and color to the subpath
    # if its width is 0
    if path0.width == 0:
        path0.width = tempWidth
        if not isinstance(path0.fill, morpho.color.GradientFill):
            path0.color = path0.fill[:]
            final.color = path0.fill[:]

    path1 = actor.newkey(atFrame)
    path0.visible = False

    actor.newkey(atFrame + duration/2).set(start=final.start, end=final.end)
    actor.newkey(atFrame + duration, final)

Path.action(wiggle)


# Base class for MultiPath that exists to be inherited by MultiPath-like
# subclasses. It exists because if a proper SpaceMultiPath is ever
# implemented, it will need to have some features/methods/etc. removed
# from the 2D MultiPath, meaning a direct inheritance from MultiPath is
# undesirable.
@MultiFigure._modifyMethods(
    ["close"],
    Path, MultiFigure._applyToSubfigures
    )
@MultiFigure._modifyMethods(
    ["insertNodesUniformly", "concat"],
    Path, MultiFigure._returnOrigCaller
    )
class MultiPathBase(MultiFigure):

    _basetype = Path

    def __init__(self, seq=None, *args, **kwargs):
        if isinstance(seq, self._basetype):
            # Case: seq is a Path. Initialize as a singleton Frame.
            super().__init__([seq])
        elif isinstance(seq, (list, tuple)) and len(seq) > 0 and isinstance(seq[0], self._basetype):
            # Case: seq is a list of paths. Initialize like a Frame.
            super().__init__(seq)
        else:
            # Else: Assume seq represents an actual seq list.
            # Construct the path and append it as the first and only
            # subpath.
            path = self._basetype(seq, *args, **kwargs)
            super().__init__([path])

    @property
    def pos(self):
        return self.origin

    @pos.setter
    def pos(self, value):
        self.origin = value

    @property
    def boxWidth(self):
        return lambda *args, **kwargs: BoundingBoxFigure.boxWidth(self, *args, **kwargs)

    @property
    def boxHeight(self):
        return lambda *args, **kwargs: BoundingBoxFigure.boxHeight(self, *args, **kwargs)

    # Rescales the MultiPath by the given factors.
    # See Path.rescale() for more info.
    def rescale(self, *args, **kwargs):
        Path.rescale(self, *args, **kwargs)
        self.all.commitTransforms()
        return self

    resize = Path.resize

    # Joins all of the subpaths into a single Path
    # with the jumps between different subpaths being implemented
    # using Path deadends. In effect, this reverses the effects of
    # Path.splitAtDeadends().
    #
    # Note that since a single Path can have only one style,
    # the style of the joined multipath will be taken as the style
    # of its first subpath.
    def joinUsingDeadends(self):
        if len(self.figures) == 0:
            return self._basetype()

        path = self.figures[0].copy()
        for subpath in self.figures[1:]:
            path.deadends.add(path.nodeCount()-1)
            path.concat(subpath)

        return path

    # Removes subpaths IN PLACE whose node counts are less than 2
    # (and are therefore non-drawable).
    def squeeze(self):
        for path in self.figures[:]:
            if path.nodeCount() < 2:
                self.figures.remove(path)
        return self

    ### TWEEN METHODS ###

    tweenLinear = MultiFigure.Multi(Path.tweenLinear, morpho.Figure.tweenLinear)
    tweenSpiral = MultiFigure.Multi(Path.tweenSpiral, morpho.Figure.tweenSpiral)

    @classmethod
    def tweenPivot(cls, angle=tau/2, *args, **kwargs):
        pivot = MultiFigure.Multi(
            Path.tweenPivot(angle, *args, **kwargs),
            morpho.Figure.tweenPivot(angle, *args, **kwargs)
            )
        # Enable splitting for this tween method
        pivot = morpho.pivotTweenMethod(cls.tweenPivot, angle)(pivot)

        return pivot

@MultiPathBase.action
def popIn(actor, *args, **kwargs):
    actor.subaction.popIn(*args, **kwargs)

@MultiPathBase.action
def popOut(actor, *args, **kwargs):
    actor.subaction.popOut(*args, **kwargs)

# Highlights the MultiPath actor
@MultiPathBase.action
def highlight(actor, *args, **kwargs):
    actor.subaction.highlight(*args, **kwargs)

# Highlights then immediately de-highlights the MultiPath actor.
# Optional keyword input `pause` can be used to specify a number
# of frames to pause after highlighting and before de-highlighting.
# See also: Path.flourish()
@MultiPathBase.action
def flourish(actor, *args, **kwargs):
    actor.subaction.flourish(*args, **kwargs)

# Draws in a MultiPath actor Manim-style. Useful for making
# LaTeX appear on the screen.
#
# Note that if the stroke width of a subpath is 0, the
# subpath's fill will be assigned to its stroke color.
# This change will persist even after the action completes.
#
# INPUTS
# subduration = How long should drawing in one subpath take?
#       Default: 30 frames
# atFrame = Frame number at which to begin the action.
#       Default: None (Use frame of the last keyfigure)
#
# OPTIONAL KEYWORD-ONLY INPUTS
# tempWidth = Temporary stroke width to use in the animation
#       if the stroke width is 0. Default: 3
# transition = Transition to use in the animation.
#       Note that this only applies to the portion of the actor's
#       timeline affected by this action. After the action
#       concludes, the original transition of this actor will
#       be used for future keyfigures. Default: uniform.
# substagger = Time spacing between drawing adjacent subpaths (in frames).
#       Default: None (use half the subduration value).
# select = Slice or tuple of slices representing the selection of
#       subpaths to apply the action to.
@MultiPathBase.action
def drawIn(actor, subduration=30, atFrame=None, *,
    tempWidth=2, transition=morpho.transitions.uniform,
    substagger=None, select=None):

    lasttime = actor.lastID()
    if atFrame is None:
        atFrame = lasttime

    if substagger is None:
        substagger = subduration/2

    mpath0 = actor.last()
    final = mpath0.copy().set(visible=True)
    mpath0.static = False
    actor.subaction.drawIn(subduration, atFrame,
        tempWidth=tempWidth, transition=transition,
        substagger=substagger, select=select
        )

    # Hide lingering initial keyfigure if it exists.
    if atFrame > lasttime:
        mpath0.visible = False

    actor.fin = final


# True MultiPath class for end-users inherits from
# TransformableFrame too.

# MultiFigure version of Path.
# See "morpho.graphics.MultiImage" for more info on the basic idea here.
@TransformableFrame.modifyFadeActions
class MultiPath(MultiPathBase, FancyFrame):
    # Converts the MultiPath into an equivalent MultiSpline.
    # Note that some path attributes cannot be converted, such
    # as arrow tips and outlines, since Spline does not support
    # these features.
    def toSpline(self, *, _cls=None):
        # `_cls` is a hidden keyword parameter that can override
        # using MultiSpline as the container type. Mainly for use
        # by MultiPath3D so it can override it to be MultiSpline3D.
        if _cls is None:
            import morpholib.shapes
            _cls = morpho.shapes.MultiSpline

        mspline = _cls()
        mspline._updateFrom(self, common=True, ignore="figures")
        mspline.figures = [path.toSpline() for path in self.figures]

        return mspline

Multipath = MultiPath  # Alias

MultiPath.action(wiggle)

# Assign MultiPath as the Path class's dedicated multifigure version.
Path._multitype = MultiPath

# 3D version of MultiPath meant to enable 2D MultiPaths to be
# positionable and orientable in 3D space. This is NOT a full
# SpaceMultiPath class, which would be a MultiFigure of
# SpaceSplines! Rather, this is just a regular 2D MultiPath
# which can be rendered in a 3D space like SpaceImage can.
#
# The main differences from 2D MultiPaths is three new attributes:
# pos = 3D position as an np.array. Default: [0,0,0] (the origin)
# orient = Orientation in 3D space as a 3x3 rotation matrix.
#       Default: np.eye(3) (oriented on the xy-plane facing the
#       +z direction)
# orientable = Boolean denoting whether the MultiPath should be
#       treated as an orientable 3D object, or more like a
#       2D "sticker" object. Default: False
#
# Note that `pos` is not merely an alias for `origin` like it is
# for 2D MultiPaths. Here they are distinct: `pos` controls 3D
# position, whereas `origin` controls 2D position within the
# MultiPath's local plane.
class MultiPath3D(MultiPath, morpho.SpaceFrame):
    def __init__(self, seq=None, *args, **kwargs):
        if isinstance(seq, MultiPathBase):
            # Convert 2D MultiPath into 3D MultiPath
            mpath = seq
            super().__init__(None, *args, **kwargs)
            self._updateFrom(mpath)
        else:
            super().__init__(seq, *args, **kwargs)

        self.Tweenable("_pos", np.zeros(3), tags=["nparray", "nofimage", "3d"])
        self.Tweenable("_orient", np.eye(3), tags=["nparray", "orient"])

        self.NonTweenable("orientable", False)

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = morpho.matrix.array(value)

    @property
    def orient(self):
        return self._orient

    @orient.setter
    def orient(self, value):
        self._orient = morpho.matrix.array(value)

    # Converts the MultiPath3D figure into an equivalent
    # MultiSpline3D figure.
    # See `MultiPath.toSpline()` for more info.
    def toSpline(self, *, _cls=None):
        if _cls is None:
            import morpholib.shapes
            _cls = morpho.shapes.MultiSpline3D

        return super().toSpline(_cls=_cls)

    partition = morpho.SpaceFrame.partition

    def primitives(self, camera):
        pos3d = camera.orient @ (self.pos - camera.focus) + camera.focus
        pos3d = pos3d.tolist()

        mpath = MultiPath()
        mpath._updateFrom(self, common=True, copy=False)
        if self.orientable:
            totalOrientTransform = (camera.orient @ self.orient)[:2,:2]
            mpath._transform = totalOrientTransform @ mpath._transform
            mpath.origin = pos3d[0] + 1j*pos3d[1] + morpho.matrix.Mat(totalOrientTransform)*mpath.origin
        else:
            mpath.origin += pos3d[0] + 1j*pos3d[1]
        mpath.zdepth = pos3d[2]

        return [mpath]

    draw = morpho.SpaceFigure.draw

    ### TWEEN METHODS ###

    @classmethod
    def tweenPivot(cls, *args, **kwargs):
        raise NotImplementedError

MultiPath3d = MultiPath3D

# Fade actions are re-implemented partly because substaggering
# is not supported because subfigure jumps would be restricted
# to the plane of orientation.

@MultiPath3D.action
def fadeIn(mpath, duration=30, atFrame=None, jump=0, alpha=1):
    morpho.Frame.actions["fadeIn"](mpath, duration, atFrame, 0, alpha)
    jump = morpho.array(jump)
    if duration > 0:
        mpath.key[-2].pos = mpath.key[-2].pos - jump

@MultiPath3D.action
def fadeOut(mpath, duration=30, atFrame=None, jump=0):
    morpho.Frame.actions["fadeOut"](mpath, duration, atFrame, 0)
    jump = morpho.array(jump)
    if duration > 0:
        mpath.last().pos = mpath.last().pos + jump

# Inherited morphFrom() from 2D MultiPath doesn't work for
# 3D MultiPaths unfortunately, so default back to the original
# morphFrom() for all figures.
MultiPath3D.actions["morphFrom"] = morpho.Figure.actions["morphFrom"]

class Track(Path):
    '''Path with tick marks - like a train track: --|--|--|--

    TWEENABLES (in addition to those inherited from Path)
    tickWidth = Width of tickmarks in pixels. Default: self.width/2
    tickLength = Length of tickmarks in pixels. Default: 15
    tickColor = Tickmark color (RGB vector-like).
                Default: mirrors "color" tweenable
    tickAlpha = Tickmark opacity. Default: 1 (opaque)
    tickGap = Separation between adjacent tickmarks in pixels.
              Default: 35
    tickStart = Initial draw point for ticks. A number between 0 and 1.
                0 = Path beginning, 1 = Path end
                Default: 0
    tickEnd = Final draw point for ticks. A number between 0 and 1.
              0 = Path beginning, 1 = Path end
              Default: 1
    '''

    def __init__(self, seq=None, width=3, color=(1,1,1), alpha=1,
        tickWidth=None, tickColor=None, tickAlpha=1,
        tickLength=15, tickGap=35):

        # Set default tick width and color based on the
        # given values for path width and color
        if tickWidth is None:
            tickWidth = width/2
        if tickColor is None:
            tickColor = color[:]

        if isinstance(seq, Path):
            path = seq
            super().__init__(path.seq[:], path.width, path.color, path.alpha)
            self.start = path.start
            self.end = path.end
            self.alphaEdge = path.alphaEdge
            self.fill = path.fill[:]
            self.alphaFill = path.alphaFill
            self.headSize = path.headSize
            self.tailSize = path.tailSize
            self.outlineWidth = path.outlineWidth
            self.outlineColor = path.outlineColor[:]
            self.outlineAlpha = path.outlineAlpha
            self.origin = path.origin
            self.rotation = path.rotation
            self._transform = path._transform.copy()

            self.interp = path.interp
            self.deadends = path.deadends.copy()

            # # Make ticks have zero width intially so the track looks
            # # identical to the given Path figure.
            # # Actually, maybe nevermind. This could conflict with
            # # any user-specified tickAlpha in the constructor.
            # tickAlpha.value = 0

        else:
            super().__init__(seq, width, color, alpha)

        # New tweenables
        self.Tweenable("tickWidth", tickWidth, tags=["size", "pixel"])
        self.Tweenable("tickColor", tickColor, tags=["color"])
        self.Tweenable("tickAlpha", tickAlpha, tags=["scalar"])
        self.Tweenable("tickLength", tickLength, tags=["scalar", "pixel"])
        self.Tweenable("tickGap", tickGap, tags=["scalar", "pixel"])
        self.Tweenable("tickStart", 0, tags=["scalar"])
        self.Tweenable("tickEnd", 1, tags=["scalar"])
        self.Tweenable("tickOffset", 0, tags=["scalar"])



    # Generates the underlying path object which when drawn
    # makes the ticks appear.
    def makeTicks(self):
        backpath = Path(self.seq)
        backpath.color = self.tickColor
        backpath.alpha = self.tickAlpha*self.alphaEdge*self.alpha
        backpath.width = self.tickLength
        backpath.start = max(self.tickStart, self.start)
        backpath.end = min(self.tickEnd, self.end)
        # Prevent negative dash steps
        gap = self.tickGap-self.tickWidth
        if gap > 0:
            backpath.dash = [self.tickWidth, gap]
            backpath.dashOffset = self.tickOffset

        backpath.origin = self.origin
        backpath.rotation = self.rotation
        backpath._transform = self._transform

        backpath.interp = self.interp
        backpath.deadends = self.deadends

        return backpath

    def draw(self, camera, ctx):
        Path.draw(self, camera, ctx)
        # Only draw ticks if necessary
        if self.tickWidth > 0 and self.tickAlpha > 0 and \
            self.tickStart < self.tickEnd:

            backpath = self.makeTicks()
            backpath.draw(camera, ctx)

TickPath = Track  # Alternate name

# DEPRECATED!
# Polar Path class. Identical to the Path class except it adds
# an attribute called "wind" which represents winding number about
# the origin with respect to the branch cut at 0 degs.
class PathPolar(Path):
    def __init__(self, seq=None, windSeq=None):
        raise NotImplementedError
        # Construct like the Point class
        Path.__init__(self, seq)

        # windSeq defaults to a list of zeros
        if windSeq is None:
            windSeq = [0]*len(self.seq)

        # Add in attribute for winding number sequence
        windSeq = morpho.Tweenable("windSeq", windSeq, tags=["integer", "list", "nolinear", "nospiral"])

        self.update(self.listState()+[windSeq])

    ### TWEEN METHODS ###

    # Returns an interpolated path between itself and another polar path.
    @morpho.TweenMethod
    @handlePathNodeInterp  # Untested for this particular tween method.
    def tweenSpiral(self, other, t, angle_tol=0.053):
        p = self
        q = other
        if p == q:
            return p.copy()
        # Check for invalid path seq lengths
        if len(p.seq) != len(q.seq) or len(p.windSeq) != len(q.windSeq):
            raise Exception("Can't tween paths of different seq lengths!")

        T = p.copy()
        T.color = morpho.tools.color.colorTween(p.color, q.color, t)
        # Tween the stroke widths if necessary
        if p.width != q.width:
            T.width = morpho.numTween(p.width, q.width, t)
            # T.width = p.width + t*(q.width - p.width)

        # Perform spiral tween on the seq
        dthList = []
        for n in range(len(p.seq)):
            r1 = abs(p.seq[n])
            r2 = abs(q.seq[n])
            th1 = (cmath.phase(p.seq[n]) % tau) + self.windSeq[n]*tau
            th2 = (cmath.phase(q.seq[n]) % tau) + other.windSeq[n]*tau

            dr = r2-r1
            dth = th2 - th1
            dthList.append(dth)

            r = r1 + t*dr
            th = th1 + t*dth

            T.seq[n] = r*cmath.exp(th*1j)
            T.windSeq[n] = int(th // tau)

        # This clause disconnects two nodes if they are
        # revolving in different directions too much.
        # The value angle_tol represents how far two oppositely
        # revolving nodes have to angularly differ before
        # we disconnect them.
        if 0.01 < t and t < 0.99:
            for n in range(len(dthList)-1):
                dth1 = dthList[n]
                dth2 = dthList[n+1]
                if dth1*dth2 < 0 and abs(dth1-dth2) > angle_tol:
                    T.deadends.add(n)

        return T


# DEPRECATED! Use the outline tweenables in the standard Path class instead.
class OutlinedPath(Path):
    def __init__(self, seq=None):
        raise NotImplementedError

        if type(seq) is Path:
            super().__init__()
            self._state = seq.copy()._state.copy()
        else:
            super().__init__(seq)

        outlineWidth = morpho.Tweenable("outlineWidth", 0, tags=["size"])
        outlineColor = morpho.Tweenable("outlineColor", [0,0,0])

        self.extendState([outlineWidth, outlineColor])

    def draw(self, camera, ctx):
        # If outline is zero width, just draw like a normal Path
        if self.outlineWidth <= 0:
            super().draw(camera, ctx)
            return

        # Create a temporary copy of the path which will serve as
        # the outline
        back = self.copy()
        back.color = self.outlineColor
        # We double it because width represents diameter, and the outline
        # needs to appear on two sides. So an outlineWidth of 1px corresponds
        # to a widening by 2px (1px on each side)
        back.width += 2*self.outlineWidth
        if self.headSize != 0:
            back.headSize += self.outlineWidth*sgn(self.headSize)
        if self.tailSize != 0:
            back.tailSize += self.outlineWidth*sgn(self.tailSize)

        # Draw the backside path using the super draw() method
        super(__class__, back).draw(camera, ctx)

        # Now draw self using the supermethod
        super().draw(camera, ctx)


# Special modification of the list class so that whenever
# an item is set, it converts it into a np.array of floats.
class Arraylist(list):

    # These lines have been commented out because I think
    # the performance cost of looping over the array elements
    # in python is too high. Also, this class is really only
    # meant to be used internally, so it's fine if it doesn't
    # behave ideally.

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    #     # Reassign to convert to np.array() via modified __setitem__()
    #     for n in range(len(self)):
    #         self[n] = self[n]

    # def append(self, *args, **kwargs):
    #     super().append(*args, **kwargs)

    #     # Reassign to convert to np.array() via modified __setitem__()
    #     self[-1] = self[-1]

    # def extend(self, *args, **kwargs):
    #     super().extend(*args, **kwargs)

    #     # Reassign to convert to np.array() via modified __setitem__()
    #     for n in range(len(self)):
    #         self[n] = self[n]

    # def __add__(self, *args, **kwargs):
    #     result = super().__add__(*args, **kwargs)
    #     return type(self)(result)

    def __setitem__(self, key, value):
        super().__setitem__(key, morpho.matrix.array(value))

ArrayList = Arraylist



# 3D version of the Path class. See "Path" for more info.
# Only main difference syntactically is that seq is a list of np.arrays.
# Note that the transformation tweenables "rotation" and "transform"
# are unsupported.
class SpacePath(Path):
    def __init__(self, seq=None, width=3, color=(1,1,1), alpha=1):
        # Use normal Path constructor first
        super().__init__()

        self.width = width
        self.color = color
        self.alpha = alpha

        # # Change the "seq" tweenable's "complex" tag to "nparray"
        # tags = self._state["seq"].tags
        # tags.remove("complex")
        # tags.add("nparray")
        # tags.add("fimage")

        # The dash pattern for this line. The format is identical to how
        # pycairo handles dash patterns: each item in the list is how long
        # ON and OFF dashes are, where the list is read cyclically.
        # Defaults to [] which means make the line solid.
        # Note that specifying only one value to the dash list is interpreted
        # as alternating that dash width ON and OFF.
        # Also note that dash pattern is ignored if gradient colors are used.
        # self.dash = []

        origin = morpho.matrix.array([0,0,0])

        # Update the seq attribute's value
        if seq is None:
            seq = Arraylist([morpho.array(0), morpho.array(1)])
        elif type(seq) is Path:
            # Copy over state and all other attributes except `seq`
            # and `origin`
            self._updateFrom(seq, common=True, ignore={"seq", "origin"})
            origin = morpho.matrix.array(seq.origin)

            # FUTURE: Have SpacePath detect non-trivial rotation
            # and transform attributes and either modify the node
            # list, OR modify 3D rotation and transform if you ever
            # decide to implement those.

            # Reassign seq to the actual list of complex numbers
            seq = seq.seq

        # Redefine seq tweenable to be 3D.
        if not isinstance(seq, Arraylist):
            # This line could probably be optimized by converting into
            # a complex-type np.array and manipulating it into the correct
            # form and then typecasting it to Arraylist.
            seq = Arraylist(morpho.matrix.array(seq[n]) for n in range(len(seq)))
        _seq = morpho.Tweenable("_seq", seq, tags=["nparray", "list", "fimage", "nospiral"])
        self._state.pop("seq")
        self._state["_seq"] = _seq

        # Re-implement "origin" as a property so it will auto-convert
        # into np.array.
        self._state.pop("origin")
        _origin = morpho.Tweenable("_origin", origin, tags=["nparray", "nofimage"])
        self.extendState([_origin])

        # These transformation tweenables from 2D Path are currently
        # not supported for SpacePaths
        self._state.pop("rotation")
        self._state.pop("_transform")

        # How many chunks should the primitive path resulting from this
        # spacepath be split into?
        self.pchunks = 1

        # # If seq is a list of complex numbers, turn them into 3-vectors
        # seq0 = seq[0]
        # if type(seq0) in (int, float, complex):
        #     for n in range(len(seq)):
        #         z = seq[n]
        #         seq[n] = np.array([z.real, z.imag, 0], dtype=float)
        # elif isinstance(seq0, list) or isinstance(seq0, tuple):
        #     for n in range(len(seq)):
        #         v = seq[n]
        #         seq[n] = np.array(v, dtype=float)
        # self.seq = seq

        # # Setup new tweenables
        # if orient is None:
        #     orient = np.identity(3)
        # if focus is None:
        #     focus = np.array([0,0,0])
        # elif type(focus) in (int, float, complex):
        #     focus = np.array([focus.real, focus.imag, 0])
        # elif isinstance(focus, list) or isinstance(focus, tuple):
        #     focus = np.array(focus)
        # orient = morpho.Tweenable(name="orient", value=orient, tags=["nparray", "nofimage"])
        # focus = morpho.Tweenable(name="focus", value=focus, tags=["nparray", "nofimage"])
        # # FUTURE: Make orient and focus properties so that the user doesn't have
        # # to always remember to convert types into np.array.
        # # When setting, the property auto-converts the input to np.array.
        # # Consider doing the same for the seq attribute.

        # self.update(list(self._state.values()))  # + [orient, focus])

    @property
    def seq(self):
        return self._seq

    @seq.setter
    def seq(self, value):
        self._seq = Arraylist(morpho.matrix.array(value[n]) for n in range(len(value)))

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, value):
        self._origin = morpho.matrix.array(value)

    # Applies the origin transformation attribute
    # to the actual seq list itself and then
    # resets the transformation attribute.
    def commitTransforms(self):
        newSeq = self.fimage(lambda v: v+self.origin).seq
        self.seq = newSeq
        self.origin = 0
        return self

    def copy(self):
        new = super().copy()

        # Now copy all of the arrays because they were not
        # actually copied using the tweenable copy method.
        # for n in range(len(new.seq)):
        #     new.seq[n] = new.seq[n].copy()
        new.seq = Arraylist(np.array(new.seq, dtype=float).tolist())


        new.pchunks = self.pchunks

        return new

    # box() method for SpacePath is currently unimplemented.
    def box(self, *args, **kwargs):
        raise NotImplementedError("box() method is currently unimplemented for SpacePath.")

    # Closes the path if it is not already closed.
    def close(self):
        if len(self.seq) == 0:
            return self
        # if (self.seq[0] != self.seq[-1]).any():
        if not np.array_equal(self.seq[0], self.seq[-1]):
            self.seq.append(self.seq[0].copy())
        return self

    # Returns the physical length of the path
    # NOTE: ignores deadends and pretends all nodes are connected!
    # Also ignores the transform attribute.
    def arclength(self):
        return sum(np.linalg.norm(self.seq[n+1]-self.seq[n]) for n in range(len(self.seq)-1)).tolist()


    # Returns the arclength so-far, where t is an index parameter between [0,1]
    # More precisely, it returns the length of the path with start=0 and end=t.
    # NOTE: ignores deadends and pretends all nodes are connected!
    def s(self, t):
        if not(0 <= t <= 1):
            raise ValueError("Index parameter must be in the interval [0,1]")
        T = t*(len(self.seq)-1)
        index = int(T)

        L = sum(np.linalg.norm(self.seq[n+1]-self.seq[n]) for n in range(index))
        if index == len(self.seq)-1:
            return L.tolist()

        L += (T-index)*np.linalg.norm(self.seq[index] - self.seq[index+1])
        return L.tolist()

    # The inverse of the so-far arclength function.
    # Takes an arclength s as input and returns the index parameter t
    # that corresponds to that length.
    # NOTE: ignores deadends and pretends all nodes are connected!
    def s_inv(self, s):
        if s < 0:
            raise ValueError("Given length must be nonnegative!")

        ell = 0
        n = 0
        while ell < s and n < len(self.seq)-1:
            n += 1
            ell += np.linalg.norm(self.seq[n] - self.seq[n-1])

        if ell < s:
            raise ValueError("Given length is longer than the path length!")
        # if n == len(self.seq) - 1:
        #     return 1

        # Segment that is split
        segment = np.linalg.norm(self.seq[n] - self.seq[n-1])
        T = n + (s-ell)/segment
        return (T/(len(self.seq)-1)).tolist()

    def toSpline(self):
        raise NotImplementedError("toSpline() is currently not implemented for SpacePath")

    def primitives(self, camera): # orient=np.identity(3), focus=np.array([0,0,0], dtype=float)):
        # Path with fewer than 2 nodes is invisible, so return nothing.
        if self.alpha == 0 or len(self.seq) < 2:
            return []

        # If we should split the primitive into chunks, do so by splitting
        # the spacepath and collecting all of those primitives together.
        if self.pchunks > 1:
            primlist = []
            for subpath in self.split(self.pchunks):
                subpath.pchunks = 1  # Reset pchunks to avoid infinite recursion!
                primlist.extend(subpath.primitives(camera))
            return primlist

        orient = camera.orient
        focus = camera.focus

        # Transform spacepath seq using orient + focus:

        # # Discard final row. This matrix will only compute the x,y coords
        # # of the final vector and forget z.
        # orient_flat = orient[:2,:]
        focus = focus.flatten()  # Ensure single-dimensional so expand_dims() works as intended
        if not np.allclose(focus, 0):
            array = np.array(self.seq, dtype=float)
            if not np.allclose(self.origin, 0):
                array += self.origin
            array -= focus  # Translate so focus point is at the origin.
            array = orient @ array.T  # Apply orient rotation mat
            # array = array[:2,:]  # Extract x and y coords and discard z
            array = array + np.expand_dims(focus, axis=1)  # Translate back
        else:  # Easy case when focus is zero.
            array = np.array(self.seq, dtype=float)
            if not np.allclose(self.origin, 0):
                array += self.origin
            array = orient @ array.T
            # array = array[:2,:]  # Extract x and y coords and discard z

        # Convert into complex numbers
        # seq = [(array[0,n] + 1j*array[1,n]).tolist() for n in range(array.shape[1])]
        seq = (array[0,:] + 1j*array[1,:]).tolist()

        # Construct 2D path in the same style
        path = Path(seq)
        path._updateFrom(self, common=True, copy=False, ignore={"seq"}.union(morpho.METASETTINGS))

        # zdepth of the whole path is given by the mean visual zdepth.
        path.zdepth = np.mean(array[2,:]).tolist()
        # max_index = len(self.seq)-1
        # x = (max_index) // 2  # This is (the floor of) the median index
        # if max_index % 2 == 0:  # Even max index => easy median
        #     path.zdepth = float((orient[2,:] @ (self.seq[x]-focus)) + focus[2])
        # else:  # Odd max index => average the two nearest
        #     w1, w2 = self.seq[x:x+2]
        #     path.zdepth = float((orient[2,:] @ ((w1+w2)/2 - focus)) + focus[2])

        return [path]


    def draw(self, camera, ctx): #, orient=np.identity(3), focus=np.array([0,0,0], dtype=float)):
        primlist = self.primitives(camera)
        if len(primlist) == 0:
            return
        path = primlist[0]
        path.draw(camera, ctx)

    def split(self, chunks):
        subpaths = super().split(chunks)

        # Now copy all of the individual arrays because they were not
        # actually copied using the inherited split() method.
        for subpath in subpaths:
            # subpath.pchunks = 1  # Reset pchunks
            for n in range(len(subpath.seq)):
                subpath.seq[n] = subpath.seq[n].copy()

            # Also make a copy of the origin vector
            subpath.origin = self.origin.copy()

        return subpaths



    ### TWEEN METHODS ###

    @morpho.TweenMethod
    @handleDash
    @morpho.color.handleGradients(["color"])
    @morpho.color.handleGradientFills(["fill"])
    @handlePathNodeInterp
    def tweenLinear(self, other, t):
        # I'm not sure why this is implemented this way. I think
        # super().tweenLinear() should work fine, but I don't want
        # to take the risk right now to try changing it.

        tw = morpho.Figure.tweenLinear(self, other, t)

        # # Linearly tween the node sequence manually (why??)
        # tw.seq = type(tw.seq)(morpho.numTween1(self.seq[n], other.seq[n], t) for n in range(len(self.seq)))

        # # Linearly tween the orient matrix manually
        # if not np.array_equal(self.orient, other.orient):
        #     tw.orient = morpho.numTween1(self.orient, other.orient, t)

        # # Linearly tween the focus vector manually
        # if not np.array_equal(self.focus, other.focus):
        #     tw.focus = morpho.numTween1(self.focus, other.focus, t)

        return tw

    # 3D spiral tween method
    @morpho.TweenMethod
    @handleDash
    @morpho.color.handleGradients(["color"])
    @morpho.color.handleGradientFills(["fill"])
    @handlePathNodeInterp
    def tweenSpiral(self, other, t):

        # Tween everything except the node sequence.
        tw = morpho.Figure.tweenSpiral(self, other, t, ignore="_seq")

        pseq = np.array(self._seq, dtype=float)   # N x 3 array of nodes
        qseq = np.array(other._seq, dtype=float)  # N x 3 array of nodes

        result = morpho.spiralInterpArray3d(pseq, qseq, t, verbose=True)
        tw._seq = list(result["twseq"])

        # This clause disconnects two nodes if they are
        # revolving in different directions too much.
        # The value angle_tol represents how far two oppositely
        # revolving nodes have to angularly differ before
        # we disconnect them.
        if 0.01 < t < 0.99:
            crossProds = result["crossProds"]
            good = result["good"]

            crossProds1 = crossProds[:-1]
            crossProds2 = crossProds[1:]

            # Deadends should occur whenever the rotation axes of two
            # neighboring nodes are anti-aligned OR whenever a good node
            # is adjacent to a bad node. However, if either of the
            # two neighboring nodes matches its respective destination
            # node, then don't disconnect the node pair
            # (this last condition is to allow cases like arrows
            # where the tail sits at the origin (a "bad" node), but
            # the head moves).
            flagset = ((np.sum(crossProds1*crossProds2, axis=1) < -1e-10) | (good[:-1]^good[1:])) \
                & ~np.all(np.isclose(pseq[:-1], qseq[:-1]), axis=1) \
                & ~np.all(np.isclose(pseq[1:], qseq[1:]), axis=1)


            tw.deadends.update(np.where(flagset)[0].tolist())

        return tw



Spacepath = SpacePath  # Synonym for SpacePath


# 3D version of the Track class.
# See `Track` and `SpacePath` for more info.
class SpaceTrack(SpacePath, Track):
    def __init__(self, seq=None, width=3, color=(1,1,1), alpha=1,
        tickWidth=None, tickColor=None, tickAlpha=1,
        tickLength=15, tickGap=35):

        super().__init__(seq, width, color, alpha)

        # Set default tick width and color based on the
        # given values for path width and color
        if tickWidth is None:
            tickWidth = width/2
        if tickColor is None:
            tickColor = color[:]

        # Override default values
        self.tickWidth = tickWidth
        self.tickColor = tickColor
        self.tickAlpha = tickAlpha
        self.tickLength = tickLength
        self.tickGap = tickGap


    def primitives(self, camera):
        # Compute primitive 2D path
        primitives = SpacePath.primitives(self, camera)
        if len(primitives) == 0: return []
        path = primitives[0]
        # Turn it into a 2D Track figure
        track = Track()
        track.seq = path.seq  # No need to copy it.
        # Override its default values with those of self
        # (e.g. tickWidth, tickColor, etc.)
        track._updateFrom(self, copy=False, common=True)
        return [track]


# NOTE: FOR INTERNAL USE ONLY! NOT WELL-MAINTAINED. USE AT OWN RISK!
# Optimize a list of path figures in the sense of concatenating
# paths that have identical styles.
# Returns a new list of paths which are optimized.
# This function does not modify the paths in the original list.
def optimizePathList(paths):
    oldPaths = paths
    if len(oldPaths) == 0: return []
    paths = []
    basePath = oldPaths[0].copy()
    for n in range(1, len(oldPaths)):
        currentPath = oldPaths[n].copy()
        if basePath.matchesStyle(currentPath):
            basePath.concat(currentPath, connectEnds=False)
        else:
            paths.append(basePath)
            basePath = currentPath
    paths.append(basePath)
    return paths


### GRIDS ###

# Mainly for internal use.
# It's basically a two-node Track but where tickGap is interpreted
# in physical units, designed to make axes with physical tickmarks.
# It's designed to only work for a two node vertex sequence, but
# it can actually handle more, but it may look wrong when rendered
# in a non-proportional viewspace.
class Axis(Track):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove "pixel" tag since it is now a physical quantity.
        self._state["tickGap"].tags.remove("pixel")

    def draw(self, camera, ctx):
        # Handle simple case with no tickmarks
        if not(self.tickWidth > 0 and self.tickAlpha > 0 and \
            self.tickStart < self.tickEnd):

            Track.draw(self, camera, ctx)

        # Compute the physical direction unit vector of the axis.
        vector = self.seq[1] - self.seq[0]
        # Don't draw a zero length axis.
        if vector == 0:
            return

        # Apply transformations if needed
        if self.rotation != 0:
            vector *= cmath.exp(self.rotation*1j)
        if not np.array_equal(self._transform, I2):
            mat = morpho.matrix.Mat(self._transform)
            vector = mat*vector
        unit = vector/abs(vector)
        u,v = unit.real, unit.imag

        # Compute the horizontal and vertical scale factors
        # that convert physical width or height to pixel units.
        Sx = mo.pixelWidth(1, camera.view, ctx)
        Sy = mo.pixelHeight(1, camera.view, ctx)

        # If the viewbox is (essentially) square with the window shape,
        # don't use the fancy formula.
        if abs(Sx-Sy)/max(Sx,Sy) < 1e-9:
            scale = Sx
            # self.tickGap = self.tickGap*Sx
        else:
            scale = math.sqrt((Sx*u)**2 + (Sy*v)**2)
            # self.tickGap = self.tickGap*math.sqrt((Sx*u)**2 + (Sy*v)**2)

        # Temporarily modify self.tickGap to the pixel value and use
        # Track.draw() to render it before reverting tickGap back to
        # its original value.
        # Also temporarily adjust some other attributes to handle
        # centering the tickmarks.
        origGap = self.tickGap
        origTickOffset = self.tickOffset
        self.tickGap = self.tickGap*scale
        self.tickOffset = self.tickOffset*scale + self.tickWidth/2
        Track.draw(self, camera, ctx)
        # Restore original values
        self.tickGap = origGap
        self.tickOffset = origTickOffset


# Mainly for internal use.
# 3D version of the Axis class. See `Axis` for more info.
class SpaceAxis(SpaceTrack):
    def primitives(self, camera):
        primitives = SpaceTrack.primitives(self, camera)
        if len(primitives) == 0: return []
        track = primitives[0]
        axis = Axis()
        axis._updateFrom(track, copy=True, common=True)

        # Scale tick spacing based on how much the axis has
        # shrunk due to foreshortening.
        scale = abs(axis.seq[1]-axis.seq[0]) / np.linalg.norm(self.seq[1]-self.seq[0]).tolist()
        axis.tickGap *= scale
        axis.tickOffset *= scale

        return [axis]


# Special Frame figure for mathgrids
class MathGridBase(morpho.Frame):

    # Returns equivalent MultiPath figure of this MathGrid
    def toMultiPath(self):
        multipath = MultiPath(self.figures)
        return multipath

@MathGridBase.action
def growIn(grid, duration=30, atFrame=None, *, reverse=False, substagger=0):
    lasttime = grid.lastID()
    if atFrame is None:
        atFrame = lasttime

    grid0 = grid.last()
    gridfinal = grid0.copy().set(visible=True)
    grid0.all.static = False
    grid.subaction.growIn(duration, atFrame, reverse=reverse, substagger=substagger)

    # Hide lingering initial keyfigure if it exists.
    if atFrame > lasttime:
        grid0.visible = False

    # Ensure final keyfigure is really the original final figure.
    # Also restores all formerly static subfigures to being static
    # again.
    grid.fin = gridfinal

@MathGridBase.action
def shrinkOut(grid, *args, **kwargs):
    # Remember who was static so we can restore later
    staticRecord = [fig.static for fig in grid.last().figures]
    grid.last().all.static = False
    grid.subaction.shrinkOut(*args, **kwargs)
    grid.last().visible = False
    # Restore static attribute for subfigures that were originally
    # static. This is helpful in case the user wants to use the
    # grid again after shrink out is complete.
    for fig, static in zip(grid.last().figures, staticRecord):
        fig.static = static

@FancyFrame.modifyFadeActions
class MathGrid(MathGridBase, FancyFrame):
    pass

# Special SpaceFrame figure for 3D mathgrids
class SpaceMathGrid(MathGridBase, morpho.SpaceFrame):

    def toMultiPath(self, *args, **kwargs):
        raise NotImplementedError("toMultiPath() is not implemented for SpaceMathGrid.")

    ### TWEEN METHODS ###

    def tweenSpiral(self, other, t):
        raise NotImplementedError

    @classmethod
    def tweenPivot(cls, *args, **kwargs):
        raise NotImplementedError

# Returns a single Path figure that represents the axes for
# the given viewbox.
#
# INPUTS
# view = Bounding box for the axes ([xmin,xmax,ymin,ymax]).
#        Default: [-5,5, -5,5]
# KEYWORD-ONLY INPUTS
# width = Axes width (in pixels). Default: 5
# color = Axes color (RGB tuple). Default: (0,0,0) black
# alpha = Axes opacity. Default: 1 (opaque)
def axesPath(view=(-5,5, -5,5), *, width=5, color=(0,0,0), alpha=1):
    xmin,xmax,ymin,ymax = view
    path = mo.grid.Path([xmin,xmax, ymin*1j, ymax*1j]).set(
        width=width, color=color, alpha=alpha, deadends={1}
        )
    return path

# Returns a MathGrid of axes with possible tickmarks.
#
# The individual paths can also be accessed as named subfigures:
#   axes = mathaxes(...)
#   axes.xaxis, axes.yaxis
#
# INPUTS (all keyword-only except `view`)
# view = Bounding box of the grid ([xmin,xmax,ymin,ymax]).
#        Default: [-5,5, -5,5]
# axis = String containing the axis types to include.
#        Can be "x", "y", or "xy". Default "xy" (both axes)
# xwidth, ywidth = Axis thickness (in pixels). Default: 5
#       You can also specify `width` to set both to the same value.
# xcolor, ycolor = Color of the respective axes. Default: (1,1,1) (white)
#       You can also specify `color` to set both to the same value.
# alpha = Opacity. Default 1 (opaque)
# xtickLength, ytickLength = Length of tickmarks (in pixels).
#       Default: 0 (don't draw tickmarks).
#       You can also specify `tickLength` to set both to the same value.
# xtickWidth, ytickWidth = Thickness of tickmarks (in pixels).
#       Default: Half the axis thickness
# dx, dy = Tickmark spacing. Default: 1.
#          You can also specify `spacing` to set both to the same value.
# tweenMethod = Tween method to use. Must be a Path-compatible
#       tween method. Default: Axis.tweenLinear
# transition = Transition function to assign to all axes
#       Default: None (meaning it uses morpho.transition.default)
def mathaxes(
    view=(-5,5, -5,5), *,
    axis="xy",
    xwidth=5, ywidth=5, width=None,
    xcolor=(1,1,1), ycolor=(1,1,1), color=None, alpha=1,
    xtickLength=0, ytickLength=0, tickLength=None,
    xtickWidth=None, ytickWidth=None, tickWidth=None,
    xtickOffset=0, ytickOffset=0, tickOffset=None,
    dx=1, dy=1, spacing=None,
    tweenMethod=Axis.tweenLinear,
    transition=None):

    # Handle orientation-agnostic keyword inputs
    if spacing is not None:
        dx = dy = spacing
    if color is not None:
        xcolor = color[:]
        ycolor = color[:]
    if tickLength is not None:
        xtickLength = ytickLength = tickLength
    if tickWidth is not None:
        xtickWidth = ytickWidth = tickWidth
    if tickOffset is not None:
        xtickOffset = ytickOffset = tickOffset
    if width is not None:
        xwidth = ywidth = width

    if xtickWidth is None:
        xtickWidth = xwidth/2
    if ytickWidth is None:
        ytickWidth = ywidth/2
    if transition is None:
        transition = morpho.transition.default

    axis = axis.lower()

    frm = MathGrid()

    xmin, xmax, ymin, ymax = view
    if "x" in axis:
        xaxis = mo.grid.Axis([xmin, xmax]).set(
            width=xwidth, color=xcolor, alpha=alpha,
            tickLength=xtickLength, tickWidth=xtickWidth,
            tickGap=dx, tickColor=xcolor[:], tickOffset=xtickOffset,
            tweenMethod=tweenMethod,
            transition=transition
            )
        frm.figures.append(xaxis)
        frm.setName(xaxis=xaxis)

    if "y" in axis:
        yaxis = mo.grid.Axis([ymin*1j, ymax*1j]).set(
            width=ywidth, color=ycolor, alpha=alpha,
            tickLength=ytickLength, tickWidth=ytickWidth,
            tickGap=dy, tickColor=ycolor[:], tickOffset=ytickOffset,
            tweenMethod=tweenMethod,
            transition=transition
            )
        frm.figures.append(yaxis)
        frm.setName(yaxis=yaxis)

    frm.transition = transition

    return frm

# 3D version of mathaxes(). Creates a pair of axes in the xy-plane.
# See "mathaxes" for more info.
def mathaxes3d(*args, **kwargs):
    axes = mathaxes(*args, **kwargs)
    axes3d = SpaceMathGrid()

    # Convert subfigures to SpaceAxis type
    for subfig in axes.figures:
        newfig = SpaceAxis()
        newfig._updateFrom(subfig, copy=False, common=True)
        newfig.seq = subfig.seq  # This will convert 2D to 3D implicitly
        axes3d.figures.append(newfig)

    return axes3d



# Construct a grid-like frame figure.
#
# INPUTS (keyword-only except `view`)
# view = Bounding box of the grid ([xmin,xmax,ymin,ymax]). Default: [-5,5, -5,5]
# dx,dy = Grid spacing in physical units. Default: 1
#         You can also specify `spacing` to set both to the same value.
# hsteps, vsteps = Number of internal steps to take inside a single grid line.
#                  This is analogous to "steps" in the morpho.grid.line() function.
#                  Higher values mean a higher resolution grid, but possibly slower
#                  render time.
#                  hsteps refers to horizontal lines, vsteps to vertical lines.
#                  Default: 50 steps (equivalently: 51 vertices per grid line)
#                  You can also specify `steps` to set both to the same value.
# hnodes, vnodes = Number of internal vertices per grid line.
#                  Default: None (meaning use hsteps and/or vsteps instead),
#                  but if specified, it overrides hsteps and/or vsteps.
#                  Mathematically they relate as: nodes = steps + 1
#                  You can also specify `nodes` to set both to the same value.
# hcolor, vcolor = Color of the respective grid lines. Default: (0,0,1) (blue)
#                  You can also specify `color` to set both to the same value.
# hmidColor, vmidColor = Color of minor grid lines.
#       Default: None (meaning it will brighten the major color by 50%)
#       You can also specify `midColor` to set both to the same value.
# hwidth, vwidth = Thickness of major grid lines (in pixels). Default: 3
#                  You can also specify `width` to set both to the same value.
# hmidlines, vmidlines = How many minor grid lines between major grid lines.
#               Default: 1
#               You can also specify `midlines` to set both to the same value.
# hmidWidth, vmidWidth = Thickness of minor grid lines (in pixels). Default: 1
#               You can also specify `midWidth` to set both to the same value.
# BGgrid = Boolean indicating whether to draw a dimmer static background grid.
#          Useful when doing morphing animations that alter the grid.
#          Default: True
# axes = Boolean indicating whether to draw axes. Default: True
# axesColor = Color of axes if drawn. Default: (1,1,1) (white)
# xaxisWidth, yaxisWidth = Thickness of axes (in pixels). Default: 5
#           You can also specify `axisWidth` to set both to the same value.
# axesStatic = Boolean indicating whether axis paths should be static or not.
# polar = Deprecated. Should always be set to False. Will remove some day.
# tweenMethod = Tween method to be assigned to all constitutent paths in the
#               grid. Default: Path.tweenLinear
# transition = Transition function to assign to all constituent paths in the
#              grid. Default: None (meaning it uses morpho.transition.default)
# optimize = Boolean indicating whether the grid lines should be optimized to
#            speed up rendering. Default: True
#
# Note that hmidlines and vmidlines can also be nonnegative ints instead of
# bools, which then means how many midlines to place.
def mathgrid(
    view=(-5,5, -5,5), *,
    dx=1, dy=1, spacing=None,
    hsteps=50, vsteps=50, steps=None,
    hnodes=None, vnodes=None, nodes=None,
    hcolor=(0,0,1), vcolor=(0,0,1), color=None, alpha=1,
    hmidColor=None, vmidColor=None, midColor=None,
    hwidth=3, vwidth=3, width=None,
    hmidlines=True, vmidlines=True, midlines=None,
    hmidWidth=1, vmidWidth=1, midWidth=None,
    BGgrid=True, axes=True, axesColor=(1,1,1),
    xaxisWidth=5, yaxisWidth=5, axisWidth=None,
    axesStatic=True, polar=False,
    tweenMethod=Path.tweenLinear,
    transition=None,
    optimize=True):

    # Handle orientation-agnostic keyword inputs
    if spacing is not None:
        dx = dy = spacing
    if steps is not None:
        hsteps = vsteps = steps
    if nodes is not None:
        hnodes = vnodes = nodes
    if color is not None:
        hcolor = color[:]
        vcolor = color[:]
    if midColor is not None:
        hmidColor = midColor[:]
        vmidColor = midColor[:]
    if width is not None:
        hwidth = vwidth = width
    if midlines is not None:
        hmidlines = vmidlines = midlines
    if midWidth is not None:
        hmidWidth = vmidWidth = midWidth
    if axisWidth is not None:
        xaxisWidth = yaxisWidth = axisWidth

    # # hnodes and vnodes override hsteps and vsteps if specified.
    # if hnodes is not None:
    #     hsteps = hnodes - 1
    # if vnodes is not None:
    #     vsteps = vnodes - 1

    xmin, xmax, ymin, ymax = view
    xsteps = int((xmax-xmin) / dx + 1.0e-6)  # +epsilon to account for floating pt error
    ysteps = int((ymax-ymin) / dy + 1.0e-6)

    xmax = xmin + xsteps*dx
    ymax = ymin + ysteps*dy

    nvert = xsteps + 1
    nhorz = ysteps + 1

    view = [xmin, xmax, ymin, ymax]

    return standardGrid(
        view=view,
        nhorz=nhorz, nvert=nvert,
        hsteps=hsteps, vsteps=vsteps,
        hnodes=hnodes, vnodes=vnodes,
        hcolor=hcolor, vcolor=vcolor, alpha=alpha,
        hmidColor=hmidColor, vmidColor=vmidColor,
        hwidth=hwidth, vwidth=vwidth,
        hmidlines=hmidlines, vmidlines=vmidlines,
        hmidWidth=hmidWidth, vmidWidth=vmidWidth,
        BGgrid=BGgrid, axes=axes, axesColor=axesColor,
        xaxisWidth=xaxisWidth, yaxisWidth=yaxisWidth,
        axesStatic=axesStatic, polar=polar,
        tweenMethod=tweenMethod,
        transition=transition,
        optimize=optimize
        )
mathGrid = mathgrid  # Alternate camel-case name.

# 3D version of mathgrid(). Creates a grid in the xy-plane.
# See "mathgrid" for more info.
def mathgrid3d(
    view=(-5,5, -5,5), *,
    dx=1, dy=1, spacing=None,
    hsteps=50, vsteps=50, steps=None,
    hnodes=None, vnodes=None, nodes=None,
    hcolor=(0,0,1), vcolor=(0,0,1), color=None, alpha=1,
    hmidColor=None, vmidColor=None, midColor=None,
    hwidth=3, vwidth=3, width=None,
    hmidlines=True, vmidlines=True, midlines=None,
    hmidWidth=1, vmidWidth=1, midWidth=None,
    axes=True, axesColor=(1,1,1),
    xaxisWidth=5, yaxisWidth=5, axisWidth=None,
    tweenMethod=Spacepath.tweenLinear,
    transition=None,
    optimize=True):

    wire = mathgrid(
        view=view,
        dx=dx, dy=dy, spacing=spacing,
        hsteps=hsteps, vsteps=vsteps, steps=steps,
        hnodes=hnodes, vnodes=vnodes, nodes=nodes,
        hcolor=hcolor, vcolor=vcolor, color=color, alpha=alpha,
        hmidColor=hmidColor, vmidColor=vmidColor, midColor=midColor,
        hwidth=hwidth, vwidth=vwidth, width=width,
        hmidlines=hmidlines, vmidlines=vmidlines, midlines=midlines,
        hmidWidth=hmidWidth, vmidWidth=vmidWidth, midWidth=midWidth,
        BGgrid=False, axes=axes, axesColor=axesColor,
        xaxisWidth=xaxisWidth, yaxisWidth=yaxisWidth, axisWidth=axisWidth,
        axesStatic=False, polar=False,
        transition=transition,
        optimize=optimize
        )
    wire = SpaceMathGrid(wire)
    for n in range(len(wire.figures)):
        # wire.figures[n] = Spacepath(wire.figures[n], orient.copy(), offset)
        subfig = SpacePath(wire.figures[n])
        subfig.set(tweenMethod=tweenMethod)
        wire.figures[n] = subfig

    return wire

# Equivalent to mathgrid(), but hsteps/vsteps default to 1,
# and `BGgrid` and `axes` default to False.
# See mathgrid() for more info.
def basicgrid(*args,
    hsteps=1, vsteps=1,
    BGgrid=False, axes=False,
    **kwargs):

    return mathgrid(
        *args,
        hsteps=hsteps, vsteps=vsteps,
        BGgrid=BGgrid, axes=axes,
        **kwargs
        )

# Equivalent to mathgrid3d(), but hsteps/vsteps default to 1,
# and `axes` defaults to False.
# See mathgrid3d() for more info.
def basicgrid3d(*args,
    hsteps=1, vsteps=1,
    axes=False,
    **kwargs):

    return mathgrid3d(
        *args,
        hsteps=hsteps, vsteps=vsteps,
        axes=axes,
        **kwargs
        )

# Identical to mathgrid3d() except the "axes" argument
# defaults to False.
def wireframe(*args,
    axes=False, **kwargs
    # view=(-5,5, -5,5),
    # dx=1, dy=1,
    # hsteps=50, vsteps=50,
    # hnodes=None, vnodes=None,
    # hcolor=(0,0,1), vcolor=(0,0,1), alpha=1,
    # hmidColor=None, vmidColor=None,
    # hwidth=3, vwidth=3,
    # hmidlines=True, vmidlines=True,
    # hmidWidth=1, vmidWidth=1,
    # axes=False, axesColor=(1,1,1),
    # xaxisWidth=5, yaxisWidth=5,
    # tweenMethod=Spacepath.tweenLinear,
    # transition=None,
    # optimize=True
    ):

    return mathgrid3d(
        *args,
        axes=axes, **kwargs
        # view=view,
        # dx=dx, dy=dy,
        # hsteps=hsteps, vsteps=vsteps,
        # hnodes=hnodes, vnodes=vnodes,
        # hcolor=hcolor, vcolor=vcolor, alpha=alpha,
        # hmidColor=hmidColor, vmidColor=vmidColor,
        # hwidth=hwidth, vwidth=vwidth,
        # hmidlines=hmidlines, vmidlines=vmidlines,
        # hmidWidth=hmidWidth, vmidWidth=vmidWidth,
        # axes=axes, axesColor=axesColor,
        # xaxisWidth=xaxisWidth, yaxisWidth=yaxisWidth,
        # tweenMethod=tweenMethod,
        # transition=transition,
        # optimize=optimize
        )

# Generates a frame representing a standard Morpho grid.
# This function isn't usually used directly anymore, as mathgrid()
# has somewhat obsoleted it.
# See "mathgrid" for more info.
def standardGrid(
    view=(-5,5, -5,5), *,
    nhorz=11, nvert=11,
    hsteps=50, vsteps=50,
    hnodes=None, vnodes=None,
    hcolor=(0,0,1), vcolor=(0,0,1), alpha=1,
    hmidColor=None, vmidColor=None,
    hwidth=3, vwidth=3,
    hmidlines=True, vmidlines=True,
    hmidWidth=1, vmidWidth=1,
    BGgrid=True, axes=True, axesColor=(1,1,1),
    xaxisWidth=5, yaxisWidth=5,
    axesStatic=True, polar=False,
    tweenMethod=Path.tweenLinear,
    transition=None,
    optimize=True):

    # hnodes and vnodes determined by hsteps and vsteps if unspecified.
    if hnodes is None:
        hnodes = hsteps + 1
    if vnodes is None:
        vnodes = vsteps + 1

    if isinstance(hcolor, morpho.color.Gradient):
        raise TypeError("hcolor cannot be a gradient")
    if isinstance(vcolor, morpho.color.Gradient):
        raise TypeError("vcolor cannot be a gradient")

    hcolor = list(hcolor)
    vcolor = list(vcolor)

    if hmidColor is None:
        hmidColor = (1-0.5*(1-morpho.array(hcolor))).tolist()
    else:
        hmidColor = list(hmidColor)

    if vmidColor is None:
        vmidColor = (1-0.5*(1-morpho.array(vcolor))).tolist()
    else:
        vmidColor = list(vmidColor)

    # Minimum node count is 2
    hnodes = max(2, hnodes)
    vnodes = max(2, vnodes)

    if polar:
        raise NotImplementedError("Polar paths are deprecated and the option to specify them here will be removed in the future. Please set polar to False to continue.")

    PATH = Path

    xmin, xmax, ymin, ymax = view

    # Convert to ints if given bools
    hmidlines = int(hmidlines)
    vmidlines = int(vmidlines)

    if transition is None:
        transition = morpho.transition.default

    frm = MathGrid()
    # frm.view = view
    paths = []
    staticList = []
    if BGgrid:
        hDimColor = list(c/2 for c in hcolor)
        vDimColor = list(c/2 for c in vcolor)
        # BG horizontal lines
        for n in range(nhorz):
            y = ymin + n*(ymax-ymin)/(nhorz-1) if nhorz != 1 else (ymin+ymax)/2
            Line = PATH([xmin+y*1j, xmax+y*1j])
            Line.color = hDimColor
            Line.width = 1
            Line.alpha = alpha
            Line.static = True
            Line.defaultTween = tweenMethod
            Line.transition = transition
            staticList.append(Line)

        # BG vertical lines
        for n in range(nvert):
            x = xmin + n*(xmax-xmin)/(nvert-1) if nvert != 1 else (xmin+xmax)/2
            Line = PATH([x+ymin*1j, x+ymax*1j])
            Line.color = vDimColor
            Line.width = 1
            Line.alpha = alpha
            Line.static = True
            Line.defaultTween = tweenMethod
            Line.transition = transition
            staticList.append(Line)

    # Horizontal lines
    for n in range(nhorz):
        y = ymin + n*(ymax-ymin)/(nhorz-1) if nhorz != 1 else (ymin+ymax)/2
        Line = line(xmin+y*1j, xmax+y*1j, steps=hnodes-1)
        Line.color = hcolor
        Line.alpha = alpha
        Line.width = hwidth
        Line.defaultTween = tweenMethod
        Line.transition = transition
        paths.append(Line)

        if n == nhorz-1: break

        # if bool(hmidlines):
        for k in range(1, hmidlines+1):
            y = ymin + (n + k/(1+hmidlines))*(ymax-ymin)/(nhorz-1)
            Line = line(xmin+y*1j, xmax+y*1j, steps=hnodes-1)
            Line.color = hmidColor
            Line.alpha = alpha
            Line.width = hmidWidth
            Line.defaultTween = tweenMethod
            Line.transition = transition
            paths.insert(0, Line)

    # Vertical lines
    for n in range(nvert):
        x = xmin + n*(xmax-xmin)/(nvert-1) if nvert != 1 else (xmin+xmax)/2
        Line = line(x+ymin*1j, x+ymax*1j, steps=vnodes-1)
        Line.color = vcolor
        Line.alpha = alpha
        Line.width = vwidth
        Line.defaultTween = tweenMethod
        Line.transition = transition
        paths.append(Line)

        if n == nvert-1: break

        # if bool(vmidlines):
        for k in range(1, vmidlines+1):
            x = xmin + (n + k/(1+vmidlines))*(xmax-xmin)/(nvert-1)
            Line = line(x+ymin*1j, x+ymax*1j, steps=vnodes-1)
            Line.color = vmidColor
            Line.alpha = alpha
            Line.width = vmidWidth
            Line.defaultTween = tweenMethod
            Line.transition = transition
            paths.insert(0, Line)

    # Need to put in axes conditionally next!
    if axes:
        xAxis = PATH([xmin, xmax])
        xAxis.static = axesStatic
        xAxis.width = xaxisWidth
        xAxis.color = list(axesColor)
        xAxis.alpha = alpha
        xAxis.defaultTween = tweenMethod
        xAxis.transition = transition
        paths.append(xAxis)

        yAxis = PATH([ymin*1j, ymax*1j])
        yAxis.static = axesStatic
        yAxis.width = yaxisWidth
        yAxis.color = list(axesColor)
        yAxis.alpha = alpha
        yAxis.defaultTween = tweenMethod
        yAxis.transition = transition
        paths.append(yAxis)

    # Assemble the frame!
    frm.figures = staticList + paths
    frm.transition = transition

    # Optimize if necessary
    if optimize:
        frm.figures = optimizePathList(frm.figures)

    return frm


# Decorator modifies the tween methods of the Polygon class to support
# tweening between polygons with different vertex counts.
def handlePolyVertexInterp(tweenmethod):
    def wrapper(self, other, t, *args, **kwargs):
        len_self = len(self.vertices)
        len_other = len(other.vertices)

        # Use standard linear tween if node counts are the same
        if len_self == len_other:
            # return super().tweenLinear(other, t)
            return tweenmethod(self, other, t, *args, **kwargs)

        # Otherwise, do some interpolation!

        # If either self or other have no nodes, give up, throw error
        if len_self == 0 or len_other == 0:
            raise ValueError("Can't interpolate between empty path and non-empty path!")

        # If self has more nodes than other, artifically insert
        # nodes into a copy of other before tweening
        if len_self > len_other:
            other = other.copy()

            # Temporarily manually close the polygon so the
            # insertNodes...() func works correctly
            self.vertices.append(self.vertices[0])
            other.vertices.append(other.vertices[0])

            # Insert additional nodes to other
            other.vertices = insertNodesUniformlyTo(other.vertices, len_self-len_other)

            # Remove temporary nodes
            self.vertices.pop(-1)
            other.vertices.pop(-1)

            # tweened = super().tweenLinear(other, t)
            tweened = tweenmethod(self, other, t, *args, **kwargs)
            return tweened
        # Else other has more nodes, so insert extra nodes to a
        # copy of self before tweening
        else:
            selfcopy = self.copy()

            # Temporarily manually close the polygon so the
            # insertNodes...() func works correctly.
            selfcopy.vertices.append(selfcopy.vertices[0])
            other.vertices.append(other.vertices[0])

            # Insert additional nodes to selfcopy
            selfcopy.vertices = insertNodesUniformlyTo(selfcopy.vertices, len_other-len_self)

            # Remove temporary nodes
            other.vertices.pop(-1)
            selfcopy.vertices.pop(-1)

            # tweened = super(Polygon, selfcopy).tweenLinear(other, t)
            tweened = tweenmethod(selfcopy, other, t, *args, **kwargs)

            return tweened

    return wrapper

# Polygon figure with boundary and fill color. Can approximate curved shapes
# with high enough vertex count.
#
# TWEENABLES
# vertices = List of positions (complex numbers). Default: [] empty list
#            If supplied a path figure, it copies its "seq" attribute.
# width = Boundary edge thickness (in pixels). Default: 3
# color = Boundary color (RGB list). Default: [0,0,0] (black)
# alphaEdge = Boundary opacity. Default: 1 (opaque)
# fill = Interior fill color (RGB list). Default: [1,0,0] (red)
#        Can also be a GradientFill object (see morpho.color.GradientFill)
# alphaFill = Interior opacity. Default: 1 (opaque)
# alpha = Overall opacity. Multiplies alphaEdge and alphaFill when drawn.
#         Default: 1 (opaque)
# dash = Dash pattern for the polygon's edge.
#        Works exactly like how it does in cairo. It's a list
#        of ints which are traversed cyclically and will alternatingly indicate
#        number of pixels of visibility and invisibility.
# dashOffset = Where along the dash pattern it will start. Default: 0
# origin = Translation value (complex number). Default: 0
# rotation = Polygon rotation about origin point (radians). Default: 0
# transform = Transformation matrix applied after all else. Default: np.eye(2)
class Polygon(BoundingBoxFigure):
    def __init__(self, vertices=None, width=3, color=(1,1,1), alphaEdge=1,
        fill=(1,0,0), alphaFill=1,
        alpha=1):

        if isinstance(color, tuple):
            color = list(color)
        elif not isinstance(color, list):
            raise TypeError("Unsupported color input")

        if isinstance(fill, tuple):
            fill = list(fill)
        elif not isinstance(fill, list) and not isinstance(fill, morpho.color.QuadGrad):
            raise TypeError("Unsupported fill input")

        # morpho.Figure.__init__(self)
        super().__init__()

        if vertices is None:
            vertices = []
        elif not isinstance(vertices, list):
            vertices = list(vertices)
        elif isinstance(vertices, Path):
            vertices = vertices.seq.copy()

        vertices = morpho.Tweenable(name="vertices", value=vertices, tags=["complex", "list"])
        color = morpho.Tweenable(name="color", value=color, tags=["color"])
        alphaEdge = morpho.Tweenable(name="alphaEdge", value=alphaEdge, tags=["scalar"])
        # fill can be either an RGB list or a gradient fill.
        # Gradient transparency is not "officially" supported right now, but you
        # actually CAN do it by specifying an RGBA gradient fill to the fill
        # attribute. However, I'm not sure if this is how I want to implement
        # alpha gradients long-term, so this functionality MAY be replaced in a
        # future version! One important thing to note, though, is if you use an
        # RGBA gradient fill, you can ONLY tween between other RGBA gradient fills!
        # Trying to tween between an RGBA gradfill and an RGB gradfill will probably
        # fail, as will trying to tween an RGBA gradfill with an RGB list.
        # Also note that the transformation tweenables
        # origin, rotation, and transform
        # will ALSO visually modify a gradient fill. That is,
        # the gradient fill is "carried along" with the transforms.
        # To have the gradient fill independent, the easiest way is to
        # call commitTransforms() after setting all the transformation
        # tweenables.
        fill = morpho.Tweenable(name="fill", value=fill, tags=["color", "gradientfill", "notween"])
        alphaFill = morpho.Tweenable(name="alphaFill", value=alphaFill, tags=["scalar"])
        alpha = morpho.Tweenable(name="alpha", value=alpha, tags=["scalar"])
        width = morpho.Tweenable(name="width", value=width, tags=["size", "pixel"])
        dash = morpho.Tweenable("dash", [], tags=["scalar", "list", "pixel"])
        dashOffset = morpho.Tweenable("dashOffset", 0, tags=["scalar", "pixel"])
        origin = morpho.Tweenable("origin", value=0, tags=["complex", "nofimage"])
        rotation = morpho.Tweenable("rotation", value=0, tags=["scalar"])
        _transform = morpho.Tweenable("_transform", np.identity(2), tags=["nparray"])

        self.extendState([vertices, color, alphaEdge,
            fill, alphaFill, alpha, width, dash, dashOffset,
            origin, rotation, _transform])

        # If set to True, then if fill is a GradientFill,
        # the border will be stroked using the GradientFill
        # instead of self.color.
        # Mainly for use by the Quadmesh class to remove
        # seams when width is zero and fill is a color function.
        self.NonTweenable("_strokeGradient", False)
        # self._strokeGradient = False

    @property
    def transform(self):
        return self._transform

    @transform.setter
    def transform(self, value):
        self._transform = morpho.matrix.array(value)

    @property
    def seq(self):
        return self.vertices

    @seq.setter
    def seq(self, value):
        self.vertices = value

    # Returns number of nodes in the polygon.
    # Equivalent to len(self.vertices)
    def nodeCount(self):
        return len(self.vertices)

    # Applies all of the transformation attributes
    # origin, rotation, transform
    # to the actual vertices list itself and then
    # resets the transformation attributes.
    def commitTransforms(self):
        rot = cmath.exp(self.rotation*1j)
        mat = morpho.matrix.Mat(*self.transform.flatten().tolist())
        newVertices = self.fimage(lambda s: (mat*(rot*s))+self.origin).vertices
        self.vertices = newVertices
        self.origin = 0
        self.rotation = 0
        self.transform = np.identity(2)
        return self

    # Returns physical bounding box of polygon as
    # [xmin, xmax, ymin, ymax]
    # ignoring rotation and transform.
    def box(self, *args, **kwargs):
        return Path.box(self, *args, **kwargs)

    # Returns the center of mass of all vertices
    # ignoring transformation attributes.
    # That is, returns mean(polygon.vertices)
    def centroid(self):
        return mean(self.vertices)

    # Specifies which class to use in constructing the edge path.
    # Mainly useful under the hood with how SpacePolygon inherits from Polygon.
    _edgeType = Path

    # Returns a Path figure which represents the boundary of the polygon.
    def edge(self):
        path = type(self)._edgeType(self.vertices[:])
        path.close()

        # Match style
        path.color = self.color[:]
        path.alpha = self.alphaEdge * self.alpha
        path.width = self.width

        # Transformation tweenables (FUTURE)
        path.origin = self.origin if not object_hasattr(self.origin, "copy") else self.origin.copy()
        if "rotation" in self._state:
            path.rotation = self.rotation
        if "_transform" in self._state:
            path.transform = self.transform


        return path

    # Converts the Polygon into an equivalent Path figure.
    def toPath(self):
        path = type(self)._edgeType(self.vertices[:])
        path.close()

        path._updateFrom(self, common=True)

        return path

    def draw(self, camera, ctx):

        if len(self.vertices) < 2 or self.alpha == 0: return

        # # If determinant of the transform matrix is too small,
        # # don't attempt to draw.
        # if abs(np.linalg.det(self.transform)) < 1e-6:
        #     return

        view = camera.view

        ### FILL ###

        # X,Y = morpho.screenCoords(self.vertices[0], view, ctx)
        # Temporarily make cairo coords the same as physical coords.
        with morpho.pushPhysicalCoords(view, ctx):  # ctx.save() is called implicitly

            # Handle possible other transformations
            if self.origin != 0:
                ctx.translate(self.origin.real, self.origin.imag)
            if not np.array_equal(self.transform, I2):
                # If transform matrix is too distorted, don't draw.
                if morpho.matrix.thinness2x2(self.transform) < 1e-6:
                    return

                xx, xy, yx, yy = self.transform.flatten().tolist()
                # Order is MATLAB-style: top-down, then left-right. So the matrix
                # specified below is:
                # [[xx  xy]
                #  [yx  yy]]
                mat = cairo.Matrix(xx, yx, xy, yy)
                # Apply to context
                ctx.transform(mat)
            if (self.rotation % tau) != 0:
                ctx.rotate(self.rotation)

            z = self.vertices[0]
            zprev = z
            x,y = z.real, z.imag
            ctx.move_to(x,y)
            for n in range(1, len(self.vertices)):
                # X,Y = morpho.screenCoords(self.vertices[n], view, ctx)
                z = self.vertices[n]
                x,y = z.real, z.imag
                # ctx.line_to(X,Y)
                if isbadnum(z) or isbadnum(zprev):
                    ctx.move_to(x,y)
                else:
                    ctx.line_to(x,y)
                zprev = z
            ctx.close_path()
            # ctx.restore()

            # Fill the polygon if the fill isn't totally transparent.
            if self.alphaFill > 0:
                # Handle gradients
                if isinstance(self.fill, morpho.color.GradientFill):
                    self.fill.draw(
                        camera, ctx, self.alphaFill*self.alpha,
                        pushPhysicalCoords=False,
                        strokeToo=self._strokeGradient
                        )
                # Handle normal colors
                else:
                    ctx.set_source_rgba(*self.fill, self.alphaFill*self.alpha)
                    ctx.fill_preserve()

        # ctx.restore()

        ### EDGE ###

        # Do nothing if edge width is tiny, or alphaEdge is zero,
        # or if the gradient fill was used for the stroke.
        if self.width < 0.5 or self.alphaEdge == 0 or self._strokeGradient:
            ctx.new_path()
            return

        ctx.set_source_rgba(*self.color, self.alphaEdge*self.alpha)
        ctx.set_line_width(self.width)
        ctx.set_dash(self.dash, self.dashOffset)
        ctx.stroke()
        ctx.set_dash([])

    ### TWEEN METHODS ###

    @morpho.TweenMethod
    @handleDash
    @morpho.color.handleGradientFills(["fill"])
    @handlePolyVertexInterp
    def tweenLinear(self, other, t, *args, **kwargs):
        return super().tweenLinear(other, t, *args, **kwargs)

    @morpho.TweenMethod
    @handleDash
    @morpho.color.handleGradientFills(["fill"])
    @handlePolyVertexInterp
    def tweenSpiral(self, other, t):
        return super().tweenSpiral(other, t)

    @classmethod
    def tweenPivot(cls, angle=tau/2):
        pivot = super().tweenPivot(angle)
        # Apply necessary decorators
        pivot = handlePolyVertexInterp(pivot)
        pivot = morpho.color.handleGradientFills(["fill"])(pivot)
        pivot = handleDash(pivot)
        # Enable splitting
        pivot = morpho.pivotTweenMethod(cls.tweenPivot, angle)(pivot)

        return pivot

Polygon.action(wiggle)


# 3D version of the Polygon figure. Draws a flat polygon in 3D space.
# See "Polygon" for more info.
# Note that the "vertices" tweenable will be a list of np.arrays.
# The vertices in the list do not necessarily have to be coplanar, but
# the polygon may look incorrect when viewed from certain angles if not.
# This figure is primarily intended to draw planar polygons oriented in
# 3D space.
# Note that the transformation tweenables "rotation" and "transform"
# are unsupported.
class SpacePolygon(Polygon):
    def __init__(self, vertices=None, width=3, color=(1,1,1), alphaEdge=1,
        fill=(1,0,0), alphaFill=1,
        alpha=1):

        super().__init__(None, width, color, alphaEdge,
            fill, alphaFill, alpha)

        origin = morpho.matrix.array([0,0,0])

        # Update the vertices attribute's value
        if vertices is None:
            vertices = Arraylist([])
        elif type(vertices) is Polygon:
            # Copy over state and all other attributes except
            # `vertices` and `origin`
            self._updateFrom(vertices, common=True, ignore={"vertices", "origin"})
            origin = morpho.matrix.array(vertices.origin)

            # FUTURE: Have SpacePolygon detect non-trivial rotation
            # and transform attributes and either modify the vertex
            # list, OR modify 3D rotation and transform if you ever
            # decide to implement those.

            # Reassign vertices to the actual list of complex numbers
            vertices = vertices.vertices

        # Redefine vertices tweenable to be 3D.
        vertices = Arraylist(morpho.matrix.array(vertices[n]) for n in range(len(vertices)))
        _vertices = morpho.Tweenable("_vertices", vertices, tags=["nparray", "list", "fimage", "3d"])
        self._state.pop("vertices")
        self._state["_vertices"] = _vertices

        # Re-implement "origin" as a property so it will auto-convert
        # into np.array.
        self._state.pop("origin")
        _origin = morpho.Tweenable("_origin", origin, tags=["nparray", "nofimage"])
        self.extendState([_origin])

        # These transformation tweenables from 2D Polygon are currently
        # not supported for SpacePolygons
        self._state.pop("rotation")
        self._state.pop("_transform")

    # Specifies which class to use in constructing the edge path.
    # Mainly useful under the hood with how SpacePolygon inherits from Polygon.
    _edgeType = SpacePath

    @property
    def vertices(self):
        return self._vertices

    @vertices.setter
    def vertices(self, value):
        self._vertices = Arraylist(morpho.matrix.array(value[n]) for n in range(len(value)))

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, value):
        self._origin = morpho.matrix.array(value)

    # Applies the origin transformation attribute
    # to the actual vertices list itself and then
    # resets the transformation attribute.
    def commitTransforms(self):
        newVertices = self.fimage(lambda v: v+self.origin).vertices
        self.vertices = newVertices
        self.origin = 0
        return self

    def copy(self):
        new = super().copy()

        # Now copy all of the arrays because they were not
        # actually copied using the tweenable copy method.
        # for n in range(len(new.vertices)):
        #     new.vertices[n] = new.vertices[n].copy()

        new.vertices = Arraylist(np.array(new.vertices, dtype=float).tolist())

        return new

    # box() method for SpacePolygon is currently unimplemented.
    def box(self, *args, **kwargs):
        raise NotImplementedError("box() method is currently unimplemented for SpacePolygon.")

    # zdepth of the primitive polygon is taken to be the average of all
    # vertices of the space polygon.
    def primitives(self, camera): # orient=np.identity(3), focus=np.zeros(3)):
        if self.alpha == 0:
            return []

        orient = camera.orient
        focus = camera.focus

        # Transform spacepolygon vertices using orient + focus:
        # if not ((focus == 0).all()):
        focus = focus.flatten()  # Ensure single-dimensional so expand_dims() works as intended
        if not np.allclose(focus, 0):
            array = np.array(self.vertices, dtype=float)
            if not np.allclose(self.origin, 0):
                array += self.origin
            array -= focus
            array = orient @ array.T
            # array = orient @ (np.array(self.vertices, dtype=float).T - focusArray)
            # array = array[:2,:]  # Extract x and y coords and discard z
            # array = array + np.expand_dims(focus[:2], axis=1)
            array = array + np.expand_dims(focus, axis=1)
        else:  # Easy case when focus is zero.
            array = np.array(self.vertices, dtype=float)
            if not np.allclose(self.origin, 0):
                array += self.origin
            array = orient @ array.T
            # array = array[:2,:]  # Extract x and y coords and discard z

        # Convert into complex numbers
        # vertices = [(array[0,n] + 1j*array[1,n]).tolist() for n in range(array.shape[1])]
        vertices = (array[0,:] + 1j*array[1,:]).tolist()

        # Construct 2D polygon in the same style
        poly = Polygon(vertices)
        poly.color = self.color
        poly.alphaEdge = self.alphaEdge
        poly.fill = self.fill
        poly.alphaFill = self.alphaFill
        poly.alpha = self.alpha
        poly.width = self.width
        poly.dash = self.dash[:]
        poly.dashOffset = self.dashOffset

        # Compute zdepth as the average of all z-coords of vertices
        z_coords = array[2,:]
        # poly.zdepth = sum(z_coords) / z_coords.size
        poly.zdepth = np.mean(z_coords).tolist()

        return [poly]


    def draw(self, camera, ctx): #, orient=np.identity(3), focus=np.zeros(3)):
        primlist = self.primitives(camera)
        if len(primlist) == 0:
            return
        poly = primlist[0]
        poly.draw(camera, ctx)

Spacepolygon = SpacePolygon  # Synonym for camel-case haters


# Mesh of quadrilaterals. Approximates a curved surface in 3D space for high enough
# quad count. The constructor for this class is usually not invoked directly.
# You should generally use the quadgrid() function to construct this figure.
#
# TWEENABLES
# array = 3D array of dimensions (Nx, Ny, 3) denoting the vertex layout of
#         the quadmesh. Slicing along the 3rd index: array[i,j,:] results in
#         the 3D (x,y,z) coordinates of a single vertex of the quadmesh.
#         Default: Unit square in the xy-plane.
# width = Thickness of the mesh lines (in pixels). Default: 3
# color = Color of the mesh lines (RGB list). Default: (0,0,0) (black)
# alphaEdge = Opacity of the mesh lines. Default 1 (opaque)
# fill = Quadmesh interior color (RGB list). Default (1,0,0) (red)
#        Can also be a color function mapping (x,y,z) to RGB.
# alphaFill = Quadmesh interior opacity. Default: 1 (opaque)
# alpha = Overall opacity. Multiplies alphaEdge and alphaFill. Default: 1 (opaque)
# fill2 = Alternate fill used to create a checkerboard pattern (RGB list).
#         Ignored if primary fill is a color function.
#         Default: None (match primary fill; i.e. no checkerboard pattern)
#
# OTHER ATTRIBUTES
# shading = Boolean indicating whether to implement a shading effect.
#           Setting to True results in a more realistic surface, but slower render.
# colormapDomain = String indicating how a color function fill will
#                  map vertices to colors.
#   "physical" : (Default). Color function will be evaluated on
#                3D arrays of the form [x,y,z] representing vertex
#                positions in physical space.
#   "index" : Color function will be evaluated on 2D arrays of the form
#             [i,j] where i and j are the indices used to access the
#             quadmesh vertex array.
#   "parametric" : Color function will be evaluated on 2D arrays of the
#                  form [x,y] with 0 <= x,y <= 1 where x,y represent
#                  the indices of the quadmesh vertex array normalized
#                  to the range [0,1].
#                  So x=0 means i=0, and x=1 means i=i_max;
#                  and y=0 means j=0, and y=1 means j=j_max.
class Quadmesh(morpho.Figure):
    def __init__(self, array=None, width=3, color=(0,0,0), alphaEdge=1,
        fill=(1,0,0), alphaFill=1, alpha=1, fill2=None):

        if type(color) is tuple:
            color = list(color)
        elif type(color) is not list:
            raise TypeError("Unsupported color input")

        if type(fill) is tuple:
            fill = list(fill)
        elif type(fill) is not list and not callable(fill):
            raise TypeError("Unsupported fill input")

        if type(fill2) is tuple:
            fill = list(fill)
        elif type(fill2) is not list and fill2 is not None:
            raise TypeError("Unsupported fill2 input")

        # morpho.Figure.__init__(self)
        super().__init__()

        if array is None:
            array = np.zeros((2,2,3))
            array[0,0,:] = [0,0,0]
            array[1,0,:] = [1,0,0]
            array[0,1,:] = [0,1,0]
            array[1,1,:] = [1,1,0]

        # Convert array to a float array if it's not already
        if array.dtype is not np.dtype(float):
            array = np.array(array, dtype=float)

        _array = morpho.Tweenable(name="_array", value=morpho.matrix.array(array), tags=["nparray", "3d"])
        color = morpho.Tweenable(name="color", value=color, tags=["color"])
        alphaEdge = morpho.Tweenable(name="alphaEdge", value=alphaEdge, tags=["scalar"])
        fill = morpho.Tweenable(name="fill", value=fill, tags=["color", "nolinear"])
        fill2 = morpho.Tweenable(name="fill2", value=fill2, tags=["color", "nolinear"])
        alphaFill = morpho.Tweenable(name="alphaFill", value=alphaFill, tags=["scalar"])
        alpha = morpho.Tweenable(name="alpha", value=alpha, tags=["scalar"])
        width = morpho.Tweenable(name="width", value=width, tags=["size", "pixel"])

        self.extendState([_array, color, alphaEdge, fill, fill2, alphaFill, alpha, width])

        # Other attributes
        self.NonTweenable("shading", False)
        self.NonTweenable("colormapDomain", "physical")

    @property
    def array(self):
        return self._array

    @array.setter
    def array(self, value):
        self._array = morpho.matrix.array(value)

    # Returns a list containing all of the polygons to display when the quadmesh
    # is drawn with the given orient and focus. Packaging this list into
    # a frame and drawing the frame will render the quadmesh to the screen
    # as intended.
    def primitives(self, camera): # orient=np.identity(3), focus=np.array([0,0,0], dtype=float)):
        # If the quadmesh is fully transparent, don't bother
        # creating any primitives. Just return the empty list.
        if self.alpha == 0:
            return []

        orient = camera.orient
        focus = camera.focus

        array = self.array
        if not np.allclose(focus, 0):
            array = array - focus
            array = np.tensordot(array, orient, axes=((2),(1)))
            array = array + focus
        else:
            array = np.tensordot(array, orient, axes=((2),(1)))

        # Generate quads

        # Handle the case where self.fill is a color function
        # Note that fill2 is ignored in this case.
        if callable(self.fill):
            # Apply decorator to self.fill to ensure the output type
            # is always a python list of python floats
            fillfunc = handleColorTypeCasting(self.fill)
            W,H,D = array.shape

            # Create color array
            if self.colormapDomain == "physical":
                colorArray = np.array(list(map(fillfunc, self.array.reshape(-1,3))), dtype=float)
                colorArray.shape = self.array.shape
            else:
                indexArray = np.indices((W,H), dtype=float).transpose(1,2,0)
                if self.colormapDomain == "parametric":
                    indexArray[:,:,0] /= (W-1)
                    indexArray[:,:,1] /= (H-1)
                elif self.colormapDomain == "index":
                    pass
                else:
                    raise ValueError(f'Unrecognized colormap domain "{self.colormapDomain}"')
                colorArray = np.array(list(map(fillfunc, indexArray.reshape(-1,2))), dtype=float)
                colorArray.shape = self.array.shape

            quads = []
            for i in range(W-1):
                for j in range(H-1):
                    quadblock = array[i:i+2, j:j+2, :]
                    vertices = (quadblock[:,:,0] + 1j*quadblock[:,:,1]).flatten().tolist()
                    vertices[2], vertices[3] = vertices[3], vertices[2]

                    colorlist = colorArray[i:i+2, j:j+2].reshape(4,3)
                    # colorlist[[2,3]] = colorlist[[3,2]]
                    colorlist = colorlist.tolist()
                    colorlist[2], colorlist[3] = colorlist[3], colorlist[2]

                    fill = morpho.color.QuadGradientFill(
                        vertices=vertices, colors=colorlist
                        )
                    quad = Polygon(
                        vertices[:], self.width, self.color, self.alphaEdge,
                        fill, self.alphaFill, self.alpha
                        )
                    quad.zdepth = float(sum(quadblock[:,:,2].flatten())/4)
                    quads.append(quad)
        else:
            fill1 = self.fill
            fill2 = self.fill2 if self.fill2 is not None else fill1
            fills = [fill1, fill2]
            quads = []
            W,H,D = array.shape
            for i in range(W-1):
                for j in range(H-1):
                    quadblock = array[i:i+2, j:j+2, :]
                    vertices = (quadblock[:,:,0] + 1j*quadblock[:,:,1]).flatten().tolist()
                    vertices[2], vertices[3] = vertices[3], vertices[2]
                    fill = fills[(i+j)%2][:]
                    quad = Polygon(
                        vertices, self.width, self.color, self.alphaEdge,
                        fill, self.alphaFill, self.alpha
                        )
                    quad.zdepth = float(sum(quadblock[:,:,2].flatten())/4)
                    quads.append(quad)

        if self.shading:
            # if isinstance(self.fill, function):
            #     raise TypeError("Shading with color function fills is not yet supported.")
            k = np.array([0,0,1])
            n = 0  # Quad index
            gamma = 2.2  # Hard-coded for now. Prbly make it a tweenable later.
            gamma_inv = 1/gamma
            for i in range(W-1):
                for j in range(H-1):
                    quadblock = array[i:i+2, j:j+2, :]
                    # Get diagonal vectors
                    d1 = (quadblock[0,0,:] - quadblock[1,1,:]).flatten()
                    d2 = (quadblock[1,0,:] - quadblock[0,1,:]).flatten()

                    # Get normal vector to the quad
                    cross = np.cross(d1,d2)

                    # Compute absolute cosine of this normal with the
                    # camera line-of-sight vector, which is
                    # k = [0,0,1] in this case.
                    norm = np.linalg.norm(cross)
                    if norm == 0:
                        n += 1
                        continue

                    cos = abs(cross[2]/norm)

                    # Modify fill of corresponding quad
                    # according to Lambert's cosine law
                    # (with gamma adjustment)
                    quad = quads[n]
                    if callable(self.fill):
                        # quad.fill = quad.fill*cos**gamma_inv
                        RGB = np.array(quad.fill.colors, dtype=float)
                        RGBnew = RGB*cos**gamma_inv
                        # quad.fill.colors = [list(rgb) for rgb in RGBnew]
                        quad.fill.colors = RGBnew.tolist()
                        # if quad.width == 0:  # Doesn't always look good :P
                        #     quad.width = 1
                        #     quad.color = np.mean(RGBnew, axis=0).tolist()
                    else:
                        RGB = np.array(quad.fill, dtype=float)
                        RGBnew = RGB*cos**gamma_inv
                        quad.fill = type(quad.fill)(RGBnew)
                        # if quad.width == 0:
                        #     quad.width = 1
                        #     quad.color = quad.fill

                    n += 1

        # If the width is less than half a pixel, make the width of each
        # individual quad 1
        # and color it the same as the fill color. This helps avoid those
        # tiny "cracks" that form between adjacent quads with zero-widths.
        # However, this is not done with colorfunctions because we don't (yet)
        # have a way to make the edge of a polygon be a gradient, and doing
        # something like taking the average color doesn't seem to make it look
        # very good.
        if (self.width < 0.5 or self.alphaEdge == 0):  # and not callable(self.fill):
            for quad in quads:
                quad.width = 1
                quad.color = quad.fill
                # We square it to make the edges less conspicuous when the
                # quadmesh is drawn with some semi-transparency.
                quad.alphaEdge = (quad.alpha*quad.alphaFill)**2
                quad._strokeGradient = callable(self.fill)

        return quads

    def draw(self, camera, ctx): #, orient=np.identity(3), focus=np.array([0,0,0], dtype=float)):
        # Get list of polygons to draw
        quads = self.primitives(camera)

        # Package into frame and draw!
        frame = morpho.Frame(quads)
        frame.draw(camera, ctx)


    def fimage(self, func):
        newfig = self.copy()

        # Convert the array to float if needed
        if newfig.array.dtype is not np.dtype(float):
            newfig.array = np.array(newfig.array, dtype=float)

        W,H,D = newfig.array.shape
        for i in range(W):
            for j in range(H):
                newfig.array[i,j,:] = func(newfig.array[i,j,:])

        return newfig

    ### TWEEN METHODS ###

    def tweenLinear(self, other, t, *args, **kwargs):
        # Do standard tween first
        tw = morpho.Figure.tweenLinear(self, other, t, *args, **kwargs)

        # Handle tween fill if it's a color function
        if callable(self.fill):
            if not callable(other.fill):
                raise TypeError("Can't tween color function with non color function.")
            tw.fill = lambda v: (1-t)*morpho.matrix.array(self.fill(v)) + t*morpho.matrix.array(other.fill(v))
            return tw
        elif self.fill != other.fill:
            # Manually tween it since we've told base tweenLinear not to.
            sfill = np.array(self.fill)
            ofill = np.array(other.fill)
            tfill = morpho.numTween1(sfill, ofill, t)
            tw.fill = list(tfill)

        # Handle tweening fill2

        # Nothing needed if both starting and ending fill2's are None.
        if (self.fill2 is None and other.fill2 is None):
            return tw
        self_fill2 = self.fill if self.fill2 is None else self.fill2
        other_fill2 = other.fill if other.fill2 is None else other.fill2
        tw.fill2 = [morpho.numTween(self_fill2[n], other_fill2[n], t) for n in range(3)]
        return tw

    def tweenSpiral(self, other, t):
        tw = self.tweenLinear(other, t, ignore="_array")
        tw._array = morpho.spiralInterpArray3d(self._array.reshape(-1,3), other._array.reshape(-1,3), t).reshape(self._array.shape)
        return tw

QuadMesh = Quadmesh  # Synonym for Quadmesh class

# Decorator modifies a color function (map from numpy 3-vectors to RGB)
# to ensure the RGB vector-like thing it returns is a vanilla python
# list of python floats. Helps to ensure consistency in the types.
def handleColorTypeCasting(colorfunc):
    def wrapper(v):
        return morpho.matrix.floatlist(colorfunc(v))
    return wrapper


# Helper function sets up a basic rectangular Quadmesh in the xy-plane, which
# can then be manipulated with fimage().
#
# INPUTS
# view = Bounding box of the quadmesh ([xmin,xmax,ymin,ymax]). Default: [-5,5, -5,5]
# dx,dy = Horizontal or vertical spacing between vertices (physical units).
#         You can also specify `spacing` to set both to the same value.
#         Default: 1
# width = Thickness of mesh lines (in pixels). Default: 3
# color = Color of mesh lines (RGB list). Default (0,0,0) (black)
# alphaEdge = Opacity of mesh lines. Default 1 (opaque)
# fill = Quadmesh interior color (RGB list). Default (1,0,0) (red)
#        Can also be a color function mapping (x,y,z) to RGB.
# alphaFill = Quadmesh interior opacity. Default: 1 (opaque)
# alpha = Overall opacity. Multiplies alphaEdge and alphaFill. Default: 1 (opaque)
# fill2 = Alternate fill used to create checkerboard pattern (RGB list).
#         Ignored if primary fill is a color function.
#         Default: None (match primary fill; i.e. no checkerboard pattern)
# tweenMethod = Tween method to assign. Default: Quadmesh.tweenLinear
# transition = Transition function to assign. Default: morpho.transition.default
#
# Any additional keyword inputs are set as attributes of the returned
# Quadmesh.
def quadgrid(*,
    view=(-5,5, -5,5),
    dx=1, dy=1, spacing=None,
    width=3,
    color=(0,0,0), alphaEdge=1,
    fill=(1,0,0), alphaFill=1, alpha=1, fill2=None,
    tweenMethod=Quadmesh.tweenLinear,
    transition=None, **kwargs):

    # Handle orientation-agnostic keyword inputs
    if spacing is not None:
        dx = dy = spacing

    xmin, xmax, ymin, ymax = view
    xmax += 1.0e-6  # +epsilon to deal with floating point error
    ymax += 1.0e-6

    Nx = 1 + int((xmax-xmin) // dx)
    Ny = 1 + int((ymax-ymin) // dy)
    array = np.zeros((Nx, Ny, 3))
    for i in range(Nx):
        for j in range(Ny):
            array[i,j,:] = [xmin+i*dx, ymin+j*dy, 0]

    quadmesh = Quadmesh(
        array, width, color, alphaEdge,
        fill, alphaFill, alpha, fill2
        )
    quadmesh.tweenMethod = tweenMethod

    if transition is None:
        transition = morpho.transition.default
    quadmesh.transition = transition

    quadmesh.set(**kwargs)

    return quadmesh


# Pointy line segment. Kind of like path, but only supports two vertices
# (tail and head). But contains a few helpful methods/properties that
# calculate some useful vector properties (length, angle, etc.)
#
# TWEENABLES
# tail = Location of arrow tail (complex number). Default: 0
# head = Location of arrow head (complex number). Default: 1
# color = Arrow color (RGB list). Default: [1,1,1] (white)
#         Can also be a Gradient (see morpho.color.Gradient)
# alpha = Arrow opacity. Default: 1 (opaque)
# width = Arrow segment thickness (in pixels). Default: 3
# headSize = Size of arrow head (in pixels). Default: 25
# tailSize = Size of arrow tail (in pixels). Default: 0
# dash = Dash pattern. Works exactly like how it does in cairo. It's a list
#        of ints which are traversed cyclically and will alternatingly indicate
#        number of pixels of visibility and invisibility.
# outlineWidth = Thickness of arrow outline (in pixels). Default: 0 (no outline)
# outlineColor = Outline color (RGB vector-like). Default: [0,0,0] (black)
# outlineAlpha = Outline opacity. Default: 1 (opaque)
# origin = Translation value (complex number). Default: 0 (complex number).
# rotation = Arrow rotation about origin point (radians). Default: 0
# transform = Transformation matrix applied after all else. Default: np.eye(2)
#
# PROPERTIES
# length = Returns arrow length: myarrow.length -> abs(head - tail).
#          Can be set like an attribute: myarrow.length = real number.
#          Works by holding tail fixed and moving head to match specified length.
# angle = Returns arrow angle in complex plane (CCW from positive real axis in
#         radians) tail to head: myarrow.angle -> cmath.phase(head - tail)
#         Can be set like an attribute: myarrow.angle = radian value.
#         Works by holding tail fixed and rotating head around tail to
#         appropriate angle value.
class Arrow(Path):
    def __init__(self, tail=0, head=1, color=(1,1,1), alpha=1, width=3,
        headSize=25, tailSize=0):

        super().__init__()

        self.seq = [tail, head]
        self.color = color
        self.alpha = alpha
        self.width = width
        self.headSize = headSize
        self.tailSize = tailSize

    @property
    def head(self):
        return self.seq[-1]

    @head.setter
    def head(self, value):
        self.seq[-1] = value

    @property
    def tail(self):
        return self.seq[0]

    @tail.setter
    def tail(self, value):
        self.seq[0] = value

    # Return unit-length complex number whose direction
    # matches the direction of the arrow.
    def unit(self):
        Dir = self.head - self.tail
        Dir = Dir/abs(Dir) if Dir != 0 else 1
        return Dir

    @property
    def length(self):
        return abs(self.head - self.tail)

    @length.setter
    def length(self, value):
        Dir = self.unit()
        self.head = self.tail + value*Dir

    @property
    def angle(self):
        return cmath.phase(self.head - self.tail)

    @angle.setter
    def angle(self, value):
        self.head = self.tail + self.length*cmath.exp(value*1j)

    # Returns a complex number representing the
    # tail-to-head vector.
    @property
    def vector(self):
        return self.head - self.tail

    @vector.setter
    def vector(self, value):
        self.head = self.tail + value


    # Return midpoint between head and tail.
    def midpoint(self):
        return (self.head + self.tail) / 2


    def toPath(self):
        path = Path()
        path._updateFrom(self, common=True)
        return path


# 3D version of Arrow. See "Arrow" for more info.
# Note that the transformation tweenables "rotation" and "transform"
# are unsupported.
# Also note that the "angle" property is not implemented for this class.
class SpaceArrow(SpacePath, Arrow):
    def __init__(self, tail=0, head=1, color=(1,1,1), alpha=1, width=3,
        headSize=25, tailSize=0):

        # Use superclass constructor
        super().__init__()

        self.tail = tail
        self.head = head
        self.color = color
        self.alpha = alpha
        self.width = width
        self.headSize = headSize
        self.tailSize = tailSize


    def toPath(self):
        path = SpacePath()
        path._updateFrom(self, common=True)
        return path


    # Return unit-length vector (np.array) whose direction
    # matches the direction of the arrow.
    # Given the zero vector, returns the vector (1,0,0).
    def unit(self):
        Dir = self.head - self.tail
        # Dir = Dir/np.linalg.norm(Dir) if Dir != 0 else np.array([1,0,0])
        Dir = Dir/np.linalg.norm(Dir) if not np.allclose(Dir, 0) else np.array([1,0,0])
        return Dir

    @property
    def length(self):
        return np.linalg.norm(self.head - self.tail)

    @length.setter
    def length(self, value):
        Dir = self.unit()
        self.head = self.tail + value*Dir

    @property
    def angle(self):
        raise NotImplementedError

    @angle.setter
    def angle(self, value):
        raise NotImplementedError


### HELPERS ###

DEG2RAD = math.pi/180

# Mainly for internal use.
# Calculates the bounding box of a numpy array of
# complex number positional data.
def _calculateBoxFromArray(array, offset=0):
    reals = array.real
    imags = array.imag

    left = np.min(reals).tolist() + offset.real
    right = np.max(reals).tolist() + offset.real
    bottom = np.min(imags).tolist() + offset.imag
    top = np.max(imags).tolist() + offset.imag

    return [left, right, bottom, top]

# Draws an ellipse at the point (x,y) with width 2a
# and height 2b.
# Optionally you can specify dTheta to adjust the angle
# increment in which each vertex of the ellipse is drawn.
# Defaults to 5 degrees.
#
# Importantly: OpenGL_ellipse() assumes you have already specified
# the fill color and stroke width of the ellipse beforehand by
# calling pyglet.gl.glLineWidth() and pyglet.gl.glColor4f()
# def OpenGL_ellipse(x, y, a, b, dTheta=10):
#     pg.gl.glLineWidth(1)
#     pg.gl.glBegin(pyglet.gl.GL_TRIANGLE_FAN)
#     for th in range(0,360, dTheta):
#         th *= DEG2RAD
#         pg.gl.glVertex2f(x + a*math.cos(th), y + b*math.sin(th))
#     pg.gl.glEnd()

# def OpenGL_ellipse_border(x, y, a, b, dTheta=10):
#     pg.gl.glBegin(pg.gl.GL_LINES)
#     dTheta_rad = dTheta*DEG2RAD
#     for th in range(0,360, dTheta):
#         th *= DEG2RAD
#         pg.gl.glVertex2f(x + a*math.cos(th), y + b*math.sin(th))
#         pg.gl.glVertex2f(x + a*math.cos(th+dTheta_rad), y + b*math.sin(th+dTheta_rad))
#     pg.gl.glEnd()

# Draw a triangle path on the given context whose vertices are the
# complex numbers A,B,C (given in screen coords).
# Note that this will reset the given path!
def cairo_triangle(ctx, A, B, C, RGBA=(1,0,0,1)):
    ctx.new_path()
    ctx.move_to(A.real, A.imag)
    ctx.line_to(B.real, B.imag)
    ctx.line_to(C.real, C.imag)
    ctx.close_path()
    ctx.set_source_rgba(*RGBA)
    ctx.fill()


# # Draws a triangle whose vertices are the complex numbers a,b,c.
# # Otherwise behaves similarly to OpenGL_ellipse()
# def OpenGL_triangle(a, b, c):
#     pg.gl.glLineWidth(1)
#     pg.gl.glBegin(pg.gl.GL_TRIANGLE_FAN)

#     pg.gl.glVertex2f(a.real, a.imag)
#     pg.gl.glVertex2f(b.real, b.imag)
#     pg.gl.glVertex2f(c.real, c.imag)

#     pg.gl.glEnd()

# Generates a linear path between the complex numbers z1 and z2
# with the default style parameters.
# Optionally specify the number of steps to take between
# z1 and z2. Defaults to 50.
def line(z1, z2, steps=50):
    steps = int(steps)
    steps = max(1, steps)
    dz = (z2-z1)/steps
    # seq = [z1]
    ns = np.arange(0, steps+1, dtype=float)
    seq = z1 + ns*dz
    seq = seq.tolist()
    # for n in range(1,steps+1):
    #     seq.append(z1 + n*dz)
    # # seq.append(z2)

    return Path(seq)

# Old, unvectorized version of line()
def line_old(z1, z2, steps=50):
    steps = int(steps)
    steps = max(1, steps)
    dz = (z2-z1)/steps
    seq = [z1]
    for n in range(1,steps+1):
        seq.append(z1 + n*dz)
    # seq.append(z2)

    return Path(seq)

# Generates a linear spacepath between the vectors v1 and v2
# with the default style parameters.
# Optionally specify the number of steps to take between
# v1 and v2. Defaults to 50.
def spaceLine(v1, v2, steps=50):
    v1 = morpho.matrix.array(v1)
    v2 = morpho.matrix.array(v2)
    steps = int(steps)
    dz = (v2-v1)/steps
    dz.shape = (1,-1)
    # seq = [v1]
    ns = np.arange(0, steps+1, dtype=float).reshape(-1,1)
    seq = v1 + (ns @ dz)
    seq = list(seq)

    # for n in range(1,steps):
    #     seq.append(v1 + n*dz)
    # seq.append(v2)

    return SpacePath(seq)

spaceline = spaceLine

# Old, unvectorized version of spaceLine()
def spaceLine_old(v1, v2, steps=50):
    v1 = morpho.matrix.array(v1)
    v2 = morpho.matrix.array(v2)
    steps = int(steps)
    dz = (v2-v1)/steps
    seq = [v1]
    for n in range(1,steps):
        seq.append(v1 + n*dz)
    seq.append(v2)
    return SpacePath(seq)

# Returns a Path figure in the shape of a circular arc that connects
# the two complex numbers p and q by the given angle of arc.
# In essence, it returns a path in the shape of the trajectory traced
# out by tweenPivot().
# p,q = start, end complex numbers
# angle = arc angle (in radians) measured CCW from p to q. Defaults to pi.
# steps = Number of steps to use in constructing the path.
#         By default it tries to make adjacent nodes about 5 degs apart.
#
# If optional keyword input `relative` is set to True, the arc
# will be positioned using the `origin` attribute, where `origin`
# will receive the arc's centerpoint.
def arc(p,q, angle=pi, steps=None, *, relative=False):
    if steps is None:
        steps = round(72*abs(angle)/tau)
    steps = max(1, steps)  # Must have at least one step

    # Initialize path
    path = Path()

    c = arcCenter(p, q, angle)

    # Compute tweened value based on pivot
    ts = np.arange(0,steps+1, dtype=float)/steps
    seq = (p-c)*np.exp(ts*angle*1j)
    if relative:
        path.origin = c
    else:
        seq += c
    seq = seq.tolist()
    path.seq = seq

    return path

# Generates a generic polygon in the shape of an ellipse centered
# at the complex number z0 with semi-width a and
# semi-height b.
# Optionally specify the angular step dTheta to take
# between each node on the elliptical path (in radians).
# Defaults to 2pi/72 (so 72 steps for a full ellipse; equiv 5 degs).
# Optionally specify starting phase (in radians).
# Measured CCW from positive real axis. Defaults to 0 rad.
#
# If optional keyword input `relative` is set to True, the ellipse
# will be centered using the `origin` attribute.
def ellipse(z0, a, b=None, dTheta=tau/72, phase=0, *, relative=False):
    if b is None:
        b = a

    steps = int(math.ceil(tau / abs(dTheta)))
    # dTheta *= DEG2RAD  # convert dTheta to radians
    # phase *= DEG2RAD

    # Make unit circle
    seq = [cmath.exp(phase*1j)]
    for n in range(1, steps):
        # seq.append(z0 + math.cos(n*dTheta+phase) + b*1j*math.sin(n*dTheta+phase))
        seq.append(cmath.exp((phase+n*dTheta)*1j))
    # seq.append(seq[0])

    poly = Polygon(seq)

    # Stretch it into an ellipse and move it
    poly = poly.fimage(lambda z: mat(a,0,0,b)*z)
    if relative:
        poly.origin = z0
    else:
        poly = poly.fimage(lambda z: z + z0)
    return poly

# Like ellipse(), but returns a Path figure representing the
# ellipse's edge. See ellipse() for more info.
def ellipsePath(*args, **kwargs):
    return ellipse(*args, **kwargs).edge()

# Older version of the ellipse() function which returns a path figure instead
# of a polygon. I changed it because an ellipse is more naturally a polygon
# and you can get the path version by calling the Polygon edge() method.
def ellipse_old(z0, a, b, dTheta=5, phase=0, polar=False):
    steps = int(math.ceil(360 / abs(dTheta)))
    dTheta *= DEG2RAD  # convert dTheta to radians
    phase *= DEG2RAD

    # Make unit circle
    seq = [cmath.exp(phase*1j)]
    for n in range(1, steps):
        # seq.append(z0 + math.cos(n*dTheta+phase) + b*1j*math.sin(n*dTheta+phase))
        seq.append(cmath.exp((phase+n*dTheta)*1j))
    seq.append(seq[0])

    # Make the path
    if polar:
        raise NotImplementedError("Polar paths are deprecated and the option to specify them here will be removed in the future. Please set polar to False to continue.")
    path = Path(seq)

    # Stretch it into an ellipse and move it
    path = path.fimage(lambda z: mat(a,0,0,b)*z)
    path = path.fimage(lambda z: z + z0)
    return path

# Return a generic polygon figure in the shape of the given box.
# Box is specified as [xmin, xmax, ymin, ymax]
#
# If optional keyword input `relative` is set to True, the rect
# will be centered using the `origin` attribute.
@handleBoxTypecasting
def rect(box, pad=0, *, relative=False):
    a,b,c,d = box
    a -= pad
    b += pad
    c -= pad
    d += pad
    SW = a + c*1j
    NW = a + d*1j
    NE = b + d*1j
    SE = b + c*1j

    corners = [NW, SW, SE, NE]

    # Initialize polygon
    poly = Polygon()

    if relative:
        center = (a+b)/2 + 1j*(c+d)/2
        corners = [corner-center for corner in corners]
        poly.origin = center

    poly.vertices = corners
    return poly

# Like rect(), but returns a Path figure representing the
# rectangle's edge. See rect() for more info.
def rectPath(*args, **kwargs):
    return rect(*args, **kwargs).edge()

# Returns a generic path figure in the shape of an X.
# X is drawn in this corner order: NW, SE, NE, SW.
# Box is specified as [xmin, xmax, ymin, ymax]
#
# If optional keyword input `relative` is set to True, the path
# will be centered using the `origin` attribute.
@handleBoxTypecasting
def cross(box, pad=0, *, relative=False):
    box = padbox(box, pad)
    x_min, x_max, y_min, y_max = box

    path = morpho.grid.Path([x_min+y_max*1j, x_max+y_min*1j, x_max+y_max*1j, x_min+y_min*1j])
    path.deadends.add(1)
    if relative:
        path.alignOrigin([0,0])

    return path

# Returns a generic path figure in the shape of a line that slashes
# across a diagonal of a box. The initial corner of the slash can
# be controlled by specifying "NW", "NE", "SW", or "SE" to the
# `corner` keyword input.
#
# If optional keyword input `relative` is set to True, the path
# will be centered using the `origin` attribute.
@handleBoxTypecasting
def slash(box, pad=0, *, corner="NW", relative=False):
    box = padbox(box, pad)
    corners = boxCorners(box, initCorner=corner)
    path = Path(corners[::2])
    if relative:
        path.alignOrigin([0,0])
    return path


# Given a list of complex numbers and a (possibly non-integer)
# index t, linearly interpolates the sequence to give a point on the
# line segment between seq[floor(t)] and seq[floor(t)+1].
# Throws index error if t is out of the range [0, len(seq)-1]
def interpSeqLinear(seq, t):
    if not(0 <= t <= len(seq)-1):
        raise IndexError("Parameter t must be between 0 and len(seq)-1 inclusive.")
    if t == len(seq)-1:
        return seq[-1]

    n = int(t)
    a = seq[n]
    b = seq[n+1]
    return morpho.numTween1(a,b, t, start=n, end=n+1)

# Applies interpSeqLinear() to uniformly add nodes to the given
# list of complex numbers and returns a new list containing
# the additional interpolated nodes.
#
# Optionally specify a segment (a,b) where 0 <= a < b <= 1
# to insert the nodes only on a subsegment of the path.
# 0 = path beginning; 1 = path end.
#
# If optional argument close = True, then the first item in the
# sequence is temporarily appended to the end before interpolation
# occurs. After interpolation, the copy of the first item is
# removed from the end of the list.
# This is useful for interpolating loops like polygon vertex lists
# because it will insert vertices between the final and first
# vertices. By default, close = False.
def insertNodesUniformlyTo(seq, numNodes, segment=(0,1), *, close=False):
    # If path closure should be done, append seq[0] to the end
    # of a copy of seq
    if close:
        seq = list(seq)  # Create a copy as a list
        seq.append(seq[0])

    newseq = seq[:]
    len_seq = len(seq)
    t1, t2 = segment
    a = t1*(len_seq-1)  # Min fractional index
    b = t2*(len_seq-1)  # Max fractional index
    dt = (b-a)/(numNodes+1)  # Buffer between index endpoints

    if numNodes == 1:
        # Insert a new node exactly in the middle of the
        # index space.
        t = (a+b)/2
        node = interpSeqLinear(seq, t)
        newseq.insert(int(t)+1, node)
    else:
        for n in range(numNodes):
            # t = (n+1)/(numNodes+1)*(len_seq-1)
            t = mo.lerp0(a+dt, b-dt, n, start=0, end=numNodes-1)
            node = interpSeqLinear(seq, t)
            # +n because each insertion shifts all later indices up by 1.
            newseq.insert(int(t)+1+n, node)

    if close:
        # Remove final temporary element which matches init
        newseq.pop(-1)

    return newseq

