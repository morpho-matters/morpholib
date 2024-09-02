
import morpholib as morpho
import morpholib.tools.color, morpholib.grid, morpholib.matrix
from morpholib.tools.basics import *
from morpholib.tools.dev import drawOutOfBoundsStartEnd, BoundingBoxFigure, \
    BackgroundBoxFigure, AlignableFigure, totalBox, shiftBox, \
    translateArrayUnderTransforms, handleBoxTypecasting, typecastView, \
    typecastWindowShape, findOwnerByType
from morpholib.matrix import mat
from morpholib.anim import MultiFigure
from morpholib.combo import TransformableFrame, FancyFrame
from morpholib.actions import wiggle

from morpholib import object_hasattr

# Import these names from grid module so they can optionally
# be accessed from the shapes module.
from morpholib.grid import Polygon, SpacePolygon, Spacepolygon, \
    Path, SpacePath, Spacepath, MultiPath, Multipath, MultiPath3D, \
    MultiPath3d, Arrow, SpaceArrow, Point, SpacePoint, Spacepoint, \
    Track, SpaceTrack, line, spaceLine, spaceline, rect, cross, \
    slash, rectPath, ellipsePath
from morpholib.grid import ellipse as ellipsePolygon

import cairo
cr = cairo

import svgelements as se
import io

import math, cmath
import numpy as np
from collections.abc import Iterable

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
            if len_other == 1:
                # If other is a singleton spline, convert it into a
                # trivial 2-node spline with trivial handles
                othercopy.inhandleRel(0,0)
                othercopy.outhandleRel(0,0)
                othercopy.newNode(othercopy.node(0))
                len_other += 1
            othercopy.insertNodes(len_self - len_other)
            # other.seq = insertNodesUniformlyTo(other.seq, len_self-len_other)
            return tweenmethod(self, othercopy, t, *args, **kwargs)
        # Else other has more nodes, so insert extra nodes to a
        # copy of self before tweening
        else:
            selfcopy = self.copy()
            if len_self == 1:
                # If self is a singleton spline, convert it into a
                # trivial 2-node spline with trivial handles
                selfcopy.inhandleRel(0,0)
                selfcopy.outhandleRel(0,0)
                selfcopy.newNode(selfcopy.node(0))
                len_self += 1
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
# dashOffset = Where along the dash pattern it will start. Default: 0
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
class Spline(BackgroundBoxFigure, AlignableFigure):

    # Dummy headSize and tailSize so that functions that expect
    # them to exist don't crash
    # (e.g. morpho.tools.dev.drawOutOfBoundsStartEnd())
    headSize = 0
    tailSize = 0

    def __init__(self, data=None, width=3, color=(1,1,1), alpha=1):
        if data is None:
            # data = np.array([
            #     [0,-1j,oo],
            #     [1,1+1j,oo]
            #     ], dtype=complex)
            data = np.array([], dtype=complex).reshape(0,3)

        # morpho.Figure.__init__(self)
        super().__init__()

        self.Tweenable(name="_data", value=np.array(data, dtype=complex), tags=["nparray"])
        self.Tweenable(name="start", value=0, tags=["scalar"])
        self.Tweenable(name="end", value=1, tags=["scalar"])
        self.Tweenable(name="color", value=color, tags=["color"])
        self.Tweenable(name="alphaEdge", value=1, tags=["scalar"])
        self.Tweenable(name="fill", value=[1,0,0], tags=["color", "gradientfill", "notween"])
        self.Tweenable(name="alphaFill", value=0, tags=["scalar"])
        self.Tweenable(name="alpha", value=alpha, tags=["scalar"])
        self.Tweenable(name="width", value=width, tags=["size", "pixel"])
        self.Tweenable("dash", [], tags=["scalar", "list", "pixel"])
        self.Tweenable("dashOffset", 0, tags=["scalar", "pixel"])
        self.Tweenable("origin", value=0, tags=["complex", "nofimage"])
        self.Tweenable("rotation", value=0, tags=["scalar"])
        self.Tweenable("_transform", np.identity(2), tags=["nparray"])

        # Set of indices that represent where a path should terminate.
        self.Tweenable("deadends", set(), tags=["notween"])

        # The dash pattern for this line. The format is identical to how
        # pycairo handles dash patterns: each item in the list is how long
        # ON and OFF dashes are, where the list is read cyclically.
        # Defaults to [] which means make the line solid.
        # Note that specifying only one value to the dash list is interpreted
        # as alternating that dash width ON and OFF.
        # Also note that dash pattern is ignored if gradient colors are used.
        # self.dash = []

        # Boolean indicates whether the control point tangents
        # should be shown. This is mainly for debugging purposes.
        self.NonTweenable("showTangents", False)

        # Contains either `None` or a color value indicating the
        # color tangents should have if drawn. If `None`, just copies
        # the `color` value.
        self.NonTweenable("_tancolor", None)

        # # Should strokes occur behind fills?
        # self.NonTweenable("backstroke", False)


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

    @property
    def pos(self):
        return self.origin

    @pos.setter
    def pos(self, value):
        self.origin = value

    @property
    def tancolor(self):
        return self._tancolor if self._tancolor is not None else self.color[:]

    @tancolor.setter
    def tancolor(self, value):
        self._tancolor = value


    # Computes the loose bounding box of the spline.
    # That is, it returns the bounding box of all the
    # control points (positional and tangent) the spline contains.
    # This function may be improved in a future version to return
    # a tighter bounding box.
    #
    # If optional kwarg `raw` is set to True, the
    # bounding box is computed without applying
    # the transformation attributes origin, rotation, transform.
    def box(self, *, raw=False):
        if self.nodeCount() == 0:
            raise ValueError("Cannot find bounding box of a spline with no nodes.")

        # The check for self.origin != 0 is done elsewhere because
        # it's by far the most common transformation attribute to
        # modify, and it's not worth making a copy and committing
        # transforms if the only transform is a translation.
        if not raw and not(self.rotation == 0 and np.array_equal(self._transform, I2)):
            temp = self.copy()
            temp.commitTransforms()
            return temp.box()

        data = self._data.copy()
        commitSplineHandles(data)

        # Remove initial inhandle and final outhandle
        # from the calculation.
        data[0,1] = data[0,0]
        data[-1,2] = data[-1,0]

        # Remove tangent handles that do not participate
        # in defining the shape due to deadends.
        finalIndex = self.nodeCount() - 1
        for deadend in self.deadends:
            if deadend > finalIndex:
                continue
            data[deadend,2] = data[deadend,0]
            if deadend < finalIndex:
                data[deadend+1, 1] = data[deadend+1, 0]

        xdata = data.real
        ydata = data.imag

        xmin = np.min(xdata).tolist()
        xmax = np.max(xdata).tolist()
        ymin = np.min(ydata).tolist()
        ymax = np.max(ydata).tolist()

        return shiftBox([xmin, xmax, ymin, ymax], self.origin if not raw else 0)

        # The following code is probably a way to compute a tighter
        # bounding box, but it relies on the currently broken
        # morpho.bezier.cubicbox() function. If/when this function
        # is ever properly implemented, the below code can be
        # substituted (hopefully).

        # subboxes = []
        # for n in range(len(data)-1):
        #     p0 = data[n, 0].tolist()
        #     p1 = data[n, 2].tolist()
        #     p2 = data[n+1, 1].tolist()
        #     p3 = data[n+1, 0].tolist()
        #     subboxes.append(morpho.bezier.cubicbox(p0, p1, p2, p3))

        # return shiftBox(totalBox(subboxes), self.origin if not raw else 0)

    rescale = morpho.grid.Path.rescale
    resize = morpho.grid.Path.resize

    # Mainly for internal use by fromsvg().
    # Computes the needed translation vector for the raw spline
    # generated from an SVG file to make it conform to a given
    # alignment.
    @staticmethod
    def _inferTranslationFromAlign(svgbbox, align, flip):
        xmin, ymin, xmax, ymax = svgbbox
        anchor_x, anchor_y = align
        if flip:
            anchor_y *= -1
        origin_x = morpho.lerp0(xmin, xmax, anchor_x, start=-1, end=1)
        origin_y = morpho.lerp0(ymin, ymax, anchor_y, start=-1, end=1)
        return -complex(origin_x, origin_y)

    # Mainly for internal use by fromsvg().
    # Applies the necessary transformations to a spline to make it
    # fit the specifications outlined in the arguments of fromsvg(),
    # such as making it meet the given boxHeight.
    def _transformForSVG(self,
        svgbbox, boxWidth, boxHeight, svgOrigin, align, flip,
        view=None, windowShape=None):
        xmin, ymin, xmax, ymax = svgbbox
        if svgOrigin is None:
            # Infer origin from `align` parameter and bounding box
            self.origin = self._inferTranslationFromAlign(svgbbox, align, flip)
        else:
            self.origin = -svgOrigin if not flip else -svgOrigin.conjugate()
        self.commitTransforms()

        # Set scale factors based on box dimensions
        if boxWidth is None and boxHeight is None:
            scale_x = 1
            scale_y = 1
        elif boxWidth is None:
            scale_y = boxHeight / (ymax - ymin)
            scale_x = scale_y
        elif boxHeight is None:
            scale_x = boxWidth / (xmax - xmin)
            scale_y = scale_x
        else:
            scale_x = boxWidth / (xmax - xmin)
            scale_y = boxHeight / (ymax - ymin)

        # Rescale spline if needed
        if scale_x != 1 or scale_y != 1:
            self._transform = morpho.matrix.scale2d(scale_x, scale_y)
            self.commitTransforms()

        if flip:
            self._transform = morpho.matrix.scale2d(1, -1)
            self.commitTransforms()

        # Attempt to adjust the spline stroke width into pixel
        # values that correspond with the physical values given
        # by the SVG data.
        if view is not None:
            if windowShape is None:
                # Try to infer Animation object from view
                mation = findOwnerByType(view, morpho.Animation)
                if mation is not None:
                    windowShape = mation.windowShape
            if windowShape is not None:
                view = typecastView(view)  # Extract actual viewbox
                windowShape = typecastWindowShape(windowShape)
                # Convert physical width into pixel width by averaging
                WIDTH_X = morpho.pixelWidth(self.width, view, windowShape)
                WIDTH_Y = morpho.pixelHeight(self.width, view, windowShape)
                self.width = mean([WIDTH_X, WIDTH_Y])
                # Multiply by the geometric mean of the scale factors used.
                self.width *= math.sqrt(scale_x*scale_y)


    # Mainly for internal use.
    # Computes the svg bounding box of an svg path object, but
    # skips over Move and Close elements.
    @staticmethod
    def _tightbbox(svgpath):
        XMIN, YMIN, XMAX, YMAX = oo, oo, -oo, -oo
        for segment in svgpath.segments():
            if isinstance(segment, (se.Move, se.Close)):
                continue
            try:
                xmin, ymin, xmax, ymax = np.array(segment.bbox()).tolist()
            except TypeError:
                continue
            XMIN = min(XMIN, xmin)
            YMIN = min(YMIN, ymin)
            XMAX = max(XMAX, xmax)
            YMAX = max(YMAX, ymax)
        svgbbox = [XMIN, YMIN, XMAX, YMAX]

        if oo in svgbbox or -oo in svgbbox:
            raise TypeError("Given SVG has no well-defined tight bounding box.")

        return svgbbox

    # Generates a Spine figure by parsing an SVG file/stream
    # and taking the first SVG path element found.
    #
    # The stroke width and color, and fill color are also imported
    # from the SVG as well as their alpha values. All other style
    # attributes are ignored and the Spline default values are used.
    # However, future versions of this method may use this data,
    # so this behavior should not be depended on.
    #
    # Note that any circular arcs will be approximated with
    # cubic Bezier curves.
    #
    # Also note that any transforms that are part of the SVG data
    # will be committed (i.e. reified) and the returned Spline
    # will have identity transforms.
    #
    # INPUTS
    # source = SVG data source such as a filepath.
    #          Can also be an svgelements.Path object, though
    #          note that the element will be reified IN PLACE.
    #
    # OPTIONAL KEYWORD-ONLY INPUTS
    # view = Viewbox the figure will be visible in. This only
    #        needs to be specified if the imported SVG has
    #        non-zero stroke widths as they need to be converted
    #        into pixel widths in a Morpho Spline.
    #        Can optionally be a layer, camera, or camera actor
    #        in which case the viewbox will be inferred.
    # windowShape = A pair specifying the pixel width and height
    #       of the animation. Like `view`, it is only needed if
    #       importing an SVG with non-zero stroke widths. Even
    #       then it's optional to specify this, as specifying
    #       a Layer object to `view` will allow `windowShape` to
    #       infer the pixel dimensions.
    # svgOrigin = SVG coordinates that should be converted into
    #              (0,0) Morpho physical coordinates.
    #              Can be specified as tuple or complex number.
    #              Default: None (meaning infer it from `align`)
    # align = Tuple specifying origin point of SVG according to alignment
    #         within the SVG's bounding box. Note this value is
    #         ignored if a value is supplied to the `svgOrigin` input.
    #         Default: (0,0) (center of bounding box)
    # boxWidth/boxHeight = Desired physical dimensions of the bounding
    #       box. If one is unspecified, it will be inferred from the
    #       other. If neither are specified, the bounding box is taken
    #       from the raw SVG coordinates.
    # index = If the SVG contains multiple path elements, which
    #         one should it use? Default: 0 (the first path).
    # flip = Boolean indicating whether the SVG should be vertically
    #        flipped when converting into Morpho physical coordinates
    #        since positive y is up in Morpho, but down in SVG.
    #        Default: True
    # arcError = Controls the amount of error in approximating arcs
    #       as cubic Bezier curves. I believe it works by splitting
    #       each arc into a bunch of sub-arcs of a set size and
    #       approximating each sub-arc with a cubic curve.
    #       arcError (I believe) controls the approximate size of each
    #       sub-arc specified as a proportion of a full arc turn.
    #       For example: arcError=0.1 means all arcs will be split
    #       into sub-arcs that are 0.1*2pi (circular) radians wide.
    #       Default: 0.1
    # tightbox = Boolean which if set to True computes the bounding
    #       box of the source SVG path more tightly by skipping over
    #       Move and Close elements in the bounding box calculation.
    #       Setting it to False allows for isolated points (which are
    #       normally invisible) to contribute the bounding box.
    #       Default: False
    # Any additional keyword arguments are set as attributes of
    # the returned figure.
    @classmethod
    def fromsvg(cls, source, *, view=None, windowShape=None,
        svgOrigin=None, align=(0,0), boxWidth=None, boxHeight=None,
        index=0, flip=True, arcError=0.1, tightbox=False, **kwargs):

        if isinstance(source, se.Shape):
            svgpath = source
        else:
            svg = parseSVG(source)
            elems = list(svg.elements(lambda elem: isinstance(elem, se.Shape)))
            svgpath = elems[index]

        # Convert path data into spline
        svgpath.reify()  # Commit all transforms
        if not isinstance(svgpath, se.Path):
            shape = svgpath
            svgpath = se.Path(shape.segments())
            svgpath.stroke = shape.stroke
            svgpath.fill = shape.fill
        svgpath.approximate_arcs_with_cubics(arcError)
        spline = cls()

        # Assign style attributes
        if svgpath.stroke == None:  # don't use 'is None'
            spline.width = 0
        else:
            spline.width = svgpath.stroke_width
            spline.color = morpho.color.rgbNormalize(
                svgpath.stroke.red, svgpath.stroke.green, svgpath.stroke.blue
                )
            spline.alphaEdge = svgpath.stroke.opacity
        if svgpath.fill != None:  # don't use `is not`
            spline.fill = morpho.color.rgbNormalize(
                svgpath.fill.red, svgpath.fill.green, svgpath.fill.blue
                )
            spline.alphaFill = svgpath.fill.opacity

        try:
            # Extract initial point
            initpt = next(svgpath.as_points())
        except StopIteration:
            return spline  # Return empty spline if path is empty
        spline.newNode(complex(initpt))
        # prevpt = initpt
        for n,segment in enumerate(svgpath.segments()):
            if isinstance(segment, se.CubicBezier):
                spline.outhandle(-1, complex(segment.control1))
                spline.newNode(complex(segment.end), complex(segment.control2), relHandles=False)
            elif isinstance(segment, se.Line):
                spline.outhandleRel(-1, 0)
                spline.newNode(complex(segment.end), 0)
            elif isinstance(segment, se.Move):
                if n == 0: continue
                spline.deadends.add(spline.nodeCount()-1)
                spline.newNode(complex(segment.end), relHandles=False)
            elif isinstance(segment, se.Close):
                spline.close(local=True)
            elif isinstance(segment, se.QuadraticBezier):
                q0 = complex(segment.start)
                q1 = complex(segment.control)
                q2 = complex(segment.end)
                p0,p1,p2,p3 = morpho.bezier.quad2cubic(q0, q1, q2)
                spline.outhandle(-1, p1)
                spline.newNode(p3, p2, relHandles=False)
            else:
                raise ValueError(f'Cannot parse SVG path element "{type(segment)}"')

        if tightbox:
            svgbbox = Spline._tightbbox(svgpath)
        else:
            svgbbox = np.array(svgpath.bbox()).tolist()
        spline._transformForSVG(
            svgbbox, boxWidth, boxHeight, svgOrigin, align, flip,
            view, windowShape
            )

        spline.set(**kwargs)  # Pass any additional kwargs to set()
        return spline

    # Returns True if the compared spline has exactly the same size, shape,
    # and position as self, ignoring transformation attributes.
    def coincides(self, other):
        self = self.copy()
        other = other.copy()

        self.commitHandles()
        other.commitHandles()

        with np.errstate(all="ignore"):  # Suppress numpy warnings
            return self.deadends == other.deadends and \
                self._data.shape == other._data.shape and \
                np.allclose(self._data, other._data)

    # Returns a "normalized" version of the spline where
    # its box center is at the origin, all transformation attributes
    # have been reset, and its largest dimension has been resized to 1.
    # If the spline has zero size (i.e. both its box dimensions are 0),
    # this method will do no resizing.
    # Mainly for use by matchesShape() to compare different splines.
    def _normalizedShape(self):
        source = self.copy()
        source.rotation = 0
        source._transform = I2
        boxWidth, boxHeight = source.boxDimensions()
        if boxWidth == 0 and boxHeight == 0:
            pass
        elif boxWidth > boxHeight:
            source.resize(boxWidth=1)
        else:
            source.resize(boxHeight=1)
        source.origin -= source.center()
        if source.origin != 0:
            source.commitTransforms()
        return source

    # Checks if the given spline has the same shape as self,
    # but only differs by size, position, or transformation
    # attribute.
    def matchesShape(self, other):
        source = self._normalizedShape()
        target = other._normalizedShape()
        return source.coincides(target)

    # Returns the node count of the spline
    def length(self):
        return self.data.shape[0]

    # Returns the number of nodes
    def nodeCount(self):
        return self._data.shape[0]

    # Returns or sets the position of the node of given index.
    # Usage: myspline.node(n) -> position of nth node
    #        myspline.node(n, value) sets nth node position to value
    #
    # If setting a node, you can optionally supply inhandle and
    # outhandle values as well:
    #   myspline.node(n, node, inhandle, outhandle)
    # and optionally make them absolute by passing False to
    # relHandles:
    #   myspline.node(n, node, inhandle, outhandle, relHandles=False)
    def node(self, index, value=None, inhandle=None, outhandle=None,
        *, relHandles=True):

        if value is None:
            return self.data[index, 0].tolist()

        self.data[index, 0] = value
        if inhandle is not None:
            if relHandles:
                self.inhandleRel(index, inhandle)
            else:
                self.inhandle(index, inhandle)
        if outhandle is not None:
            if relHandles:
                self.outhandleRel(index, outhandle)
            else:
                self.outhandle(index, outhandle)

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

    # Mainly for internal use.
    # Returns a squeezed column of the data array and converts
    # it to a python list by default.
    def _getcol(self, k, *, aslist=True):
        col = self.data[:,k].squeeze()
        return col.tolist() if aslist else col

    # Returns a list of all the nodes in the Spline.
    # Set keyword `aslist=False` to return np.array.
    def nodes(self, *, aslist=True):
        return self._getcol(0, aslist=aslist)

    # # Returns a list of all the inhandles in the Spline.
    # # Set keyword `aslist=False` to return np.array.
    # def inhandles(self, *, aslist=True):
    #     return self._getcol(1, aslist=aslist)

    # # Returns a list of all the inhandles in the Spline,
    # # relative to their corresponding node positions.
    # # Set keyword `aslist=False` to return np.array.
    # def inhandlesRel(self, *, aslist=True):
    #     array = self.inhandles(aslist=False) - self.nodes(aslist=False)
    #     return array.tolist() if aslist else array

    # def outhandles(self, *, aslist=True):
    #     return self_getcol(2, aslist=aslist)

    # def outhandlesRel(self, *, aslist=True):
    #     array = self.outhandles(aslist=False) - self.nodes(aslist=False)
    #     return array.tolist() if aslist else array

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
    def newNode_old(self, point, inhandle=oo, outhandle=oo, beforeIndex=oo):
        beforeIndex = min(beforeIndex, self.length())
        if beforeIndex < 0:
            beforeIndex = beforeIndex % self.length()

        if self.length() == 0:
            self._data = np.array([[point, inhandle, outhandle]], dtype=complex)
        else:
            # self._data = np.vstack((self.data, [point,inhandle,outhandle]))
            self._data = np.insert(self.data, beforeIndex, [point,inhandle,outhandle], axis=0)
        return self


    # Creates a new node at the specified point.
    # Optionally also specify relative inhandle and outhandle
    # which default to inf (i.e. copy its counterpart).
    # Absolute coordinates can be set for in/outhandle by setting
    # the optional keyword argument `relHandles` to False.
    # Also optionally specify where to insert the node in the sequence
    # by setting the `beforeIndex` parameter.
    # By default, places it after the current final node.
    def newNode(self, point, inhandle=oo, outhandle=oo,
        beforeIndex=oo, *, relHandles=True):

        # Compute raw index value
        beforeIndex = min(beforeIndex, self.length())
        if beforeIndex < 0:
            beforeIndex = beforeIndex % self.length()

        # Sanitize inhandle and outhandle values
        if isbadnum(inhandle):
            inhandle = oo
        if isbadnum(outhandle):
            outhandle = oo

        if relHandles:
            inhandle = point + inhandle
            outhandle = point + outhandle

        if self.length() == 0:
            self._data = np.array([[point, inhandle, outhandle]], dtype=complex)
        else:
            self._data = np.insert(self.data, beforeIndex, [point,inhandle,outhandle], axis=0)
        return self

    # Adds a list of points to the spline instead of just one at a time.
    # See also: newNode()
    def newNodes(self, point, inhandle=oo, outhandle=oo,
        beforeIndex=oo, *args, **kwargs):

        # Handle out of bounds beforeIndex value.
        beforeIndex = min(beforeIndex, self.length())  # Clamp overflows
        if beforeIndex < 0:  # Cycle underflows
            beforeIndex = beforeIndex % self.length()

        # This is reversed so that all points are placed before
        # the specified beforeIndex value.
        for pt in reversed(point):
            self.newNode(pt, inhandle, outhandle, beforeIndex, *args, **kwargs)

        return self

    # Deletes the node at the specified index. The dangling nodes on
    # either side will then be connected assuming they aren't prevented
    # by deadends.
    # NOTE: Calling delNode() will NOT update the deadends attribute!
    def delNode(self, index):
        self._data = np.delete(self._data, index, axis=0)
        return self


    # Closes the spline IN PLACE if it is not already closed.
    # If optional kwarg `local` is set to True, the closure
    # is performed relative to the latest deadend.
    # If optional kwarg `straight` is set to False, the
    # closure will be made using the current initial
    # and final tangents.
    def close(self, *, local=False, straight=True):
        if self.length() < 2 or self.node(0) == self.node(-1):
            return self

        startIndex = max(self.deadends) + 1 if local and len(self.deadends) > 0 else 0
        self._data = np.insert(self._data, self.length(), self._data[startIndex].copy(), axis=0)

        # Flatten handles
        if straight:
            self.outhandleRel(-2, 0)
            self.inhandleRel(-1, 0)

        return self

    # Automatically sets the tangent handles of the splines
    # to interpolate between the node points according to a
    # Catmull-Rom spline. The first and last nodes are handled
    # by mirroring their neighbors about them.
    #
    # This is done by automatically setting the outhandles of
    # all nodes and setting the inhandles to inf (mirrored), but
    # this can be reversed by passing in `viaInhandles=True`.
    #
    # Optionally can specify a particular index or an index range:
    #   spline.autosetHandles(5)  # Sets handles for the node at index 5.
    #   spline.autosetHandles(3,7)  # Sets handles for nodes #3 thru #6
    #   spline.autosetHandles()  # Sets handles for all nodes.
    # You can optionally specify a non-zero tension value.
    #   spline.autosetHandles(tension=0.75)
    # By default, tension=1 for a standard Catmull-Rom spline.
    def autosetHandles(self, a=None, b=None, /, *, tension=1, viaInhandles=False):
        if a is None:
            a = 0
            b = self.nodeCount()
        elif b is None:
            b = a + 1

        if viaInhandles:
            # Use inhandleRel() as the primary handle setter.
            handleMethod = self.inhandleRel
            autoMethod = self.outhandleRel
            # Tension is negated so that the vector directions
            # get mirrored.
            tension *= -1
        else:
            handleMethod = self.outhandleRel
            autoMethod = self.inhandleRel


        nodeCount = self.nodeCount()
        for n in range(a, b):
            prevIndex = max(0, n-1)
            nextIndex = min(n+1, nodeCount-1)
            node = self.node(n)
            prevNode = self.node(prevIndex)
            nextNode = self.node(nextIndex)
            vector = (nextNode - prevNode)/(3*tension*(nextIndex-prevIndex))
            handleMethod(n, vector)
            autoMethod(n, oo)
        return self

    # Returns the interpolated position along the path corresponding to the
    # parameter t, where t = 0 is the path start and t = 1 is the path end.
    # NOTE: This method ignores deadends and the transformation tweenables
    # origin, rotation, transform.
    def positionAt(self, t):
        if not(0 <= t <= 1):
            raise ValueError(f"Index parameter must be between 0 and 1. Got t = {t}")
        length = self.length()
        if length < 2:
            raise IndexError("Spline must have at least 2 nodes!")
        segCount = length - 1
        T = t*segCount  # Global parameter value

        # Round to nearest node if within a billionth of it.
        tol = 1e-9
        if abs(T - round(T)) < tol:
            T = int(round(T))  # round(np.float) is still np.float
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

    splitAtDeadends = morpho.grid.Path.splitAtDeadends
    _shiftDeadends = morpho.grid.Path._shiftDeadends
    _reverseDeadends = morpho.grid.Path._reverseDeadends

    # Reverses the direction of the spline IN PLACE.
    def reverse(self):
        # Reverse node order
        self._data = self._data[::-1,:]
        # Swap inhandles and outhandles
        self._data[:, [2,1]] = self._data[:, [1,2]]
        self._reverseDeadends()
        return self

    # Extract a subspline.
    # a and b are parameters in the range [0,1]
    def segment(self, a, b):
        # raise NotImplementedError
        reverse = not(a <= b)
        if reverse:
            a,b = b,a

        if not(0 <= a <= b <= 1):
            raise ValueError("Segment endpoints must satisfy 0 <= a,b <= 1")

        subspline = self.copy()

        # Handle singleton case
        if a == b:
            subspline.data = np.array([[self.positionAt(a), oo, oo]], dtype=complex)
            return subspline

        # Calculate fractional indices
        segCount = subspline.length() - 1
        A = a*segCount
        B = b*segCount

        # Round fractional indices if very close to an int
        tol = 1e-9
        if abs(A-round(A)) < tol:
            A = round(A)
        if abs(B-round(B)) < tol:
            B = round(B)

        # Split at first endpoint
        subspline.splitAtIndex(A)

        # Adjust parameter value of B based on newly added
        # A node if B is in the second piece of the A split.
        int_A = int(A)
        int_B = int(B)
        if A != int_A and int_A == int_B:
            B = int_B + (B-A)/(int_A+1-A)

        # Increment B index if a new node was added.
        B += subspline.length() - self.length()
        subspline.splitAtIndex(B)

        # Slice the data array
        subspline._data = subspline._data[math.ceil(A):math.ceil(B)+1]

        # Shift/remove deadends
        subspline._shiftDeadends(int(A))

        if reverse:
            subspline.reverse()

        return subspline

    # Inherits the Path class's __getitem__()
    def __getitem__(self, t):
        return morpho.grid.Path.__getitem__(self, t)

    def __iter__(self):
        raise TypeError("Splines are not iterable")


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

    # NOT IMPLEMENTED YET!
    # Opposite of commitHandles().
    # Looks for any unlinked handle pairs and if they are
    # sufficiently close to being mirrored, sets outhandle
    # value to inf, meaning it will be treated as a mirror
    # of its partner. This is an in-place operation.
    #
    # OPTIONAL INPUTS
    # viaInhandles = Boolean. If set to True, inhandles will be
    #                set to inf instead of outhandles.
    #                Default: False
    # tol = How close do two handles need to be to being mirrored
    #       before they will be linked? Default: 1e-9
    def linkHandles(self, viaInhandles=False, tol=1e-9):
        raise NotImplementedError
        return self

    # Applies all of the transformation attributes
    # origin, rotation, transform
    # to the actual data array itself and then
    # resets the transformation attributes.
    def commitTransforms(self):
        # Rotate all points
        with np.errstate(all="ignore"):  # Suppress numpy warnings
            self._data *= cmath.exp(self.rotation*1j)

            vector = self._data.reshape(-1)
            array = np.zeros((2,len(vector)))
            array[0,:] = vector.real
            array[1,:] = vector.imag
            arrayTransformed = self._transform @ array
            vectorTransformed = arrayTransformed[0,:] + 1j*arrayTransformed[1,:] + self.origin
            self._data = vectorTransformed.reshape(self._data.shape)

        # Convert any possible nans that were produced into infs.
        nan2inf(self._data)

        # Reset transformation tweenables to identities
        self.origin = 0
        self.rotation = 0
        self._transform = np.eye(2)
        return self

    _drawStroke = morpho.grid.Path._drawStroke
    _drawFill = morpho.grid.Path._drawFill

    def draw(self, camera, ctx):

        self._drawBackgroundBox(camera, ctx, self.origin, self.rotation, self._transform)

        # Need at least two nodes to draw
        if self.data.shape[0] < 2:
            return

        tol = 1e-9  # Floating point error tolerance

        # Handle trivial length path and start >= end.
        len_seq = self.length()
        maxIndex = len_seq - 1
        if maxIndex < 1 or self.start + tol > self.end or self.alpha == 0:
            return

        # # If determinant of the transform matrix is too small,
        # # don't attempt to draw.
        # if abs(np.linalg.det(self._transform)) < 1e-6:
        #     return

        # If transform matrix is too distorted, don't draw.
        if morpho.matrix.thinness2x2(self.transform) < 1e-6:
            return

        # Handle out-of-bounds start and end
        if not(0 <= self.start <= 1 and 0 <= self.end <= 1):
            backAlpha_orig = self.backAlpha
            self.backAlpha = 0
            drawOutOfBoundsStartEnd(self, camera, ctx)
            self.backAlpha = backAlpha_orig
            return

        # Compute index bounds
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

        # Calculate physical distance corresponding to half a pixel.
        # If a handle and its corresponding node are within this
        # distance, the handle will be snapped to the node.
        # This is to get around an apparent bug in cairo in rendering
        # bezier curves with handles too close to (but not equal to)
        # their nodes.
        pixel_tol_x = morpho.physicalWidth(0.5, camera.view, ctx)
        pixel_tol_y = morpho.physicalHeight(0.5, camera.view, ctx)
        pixel_tol = max(pixel_tol_x, pixel_tol_y)

        # Temporarily modify cairo coordinates to coincide with
        # physical coordinates.
        with morpho.pushPhysicalCoords(camera.view, ctx):  # Contains a ctx.save()

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

            # Extract these objects so that we can save
            # on repeated Figure tweenable accesses (which
            # may be slow).
            self_data = self.data
            self_deadends = self.deadends
            # Draw each curve
            # for n in range(self.data.shape[0]-1):
            for n in range(init, final):
                # Get next node, inhandle, and outhandle
                z, inhandle, outhandle = self_data[n+1,:].tolist()
                # Update handles based on possible inf values
                inhandle, outhandle = replaceInfHandles(z, inhandle, outhandle)

                x,y = z.real, z.imag

                # If previous node is a deadend, or current or previous
                # nodes are bad, move to next node.
                # Else, draw a curve to the next node.
                if n in self_deadends or isbadnum(z) or isbadnum(zprev):
                    ctx.move_to(x,y)
                else:
                    # Snap handles to nodes if they are within
                    # half a pixel of each other.
                    if abs(outprev-zprev) < pixel_tol:
                        outprev = zprev
                    if abs(inhandle - z) < pixel_tol:
                        inhandle = z
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

        # Auto-close path if the path has the simplest possible settings
        if self.node(0) == self.node(-1) and \
            self.start == 0 and self.end == 1 and \
            len(self.deadends) == 0 and \
            self.headSize == 0 and self.tailSize == 0:
            # (checking for headSize and tailSize is technically unnecessary
            # since splines don't have arrow support, BUT THEY MIGHT IN THE FUTURE,
            # so that's why the checks are here)

            ctx.close_path()

        # Stroke and fill the path
        rgba = list(self.color) + [self.alpha*self.alphaEdge]
        if self.width < 0:
            # Draw stroke first, then fill
            self._drawStroke(ctx, rgba)
            with morpho.pushPhysicalCoords(camera.view, ctx):
                self._drawFill(camera, ctx)
        else:
            # Fill first, then draw stroke
            with morpho.pushPhysicalCoords(camera.view, ctx):
                self._drawFill(camera, ctx)
            self._drawStroke(ctx, rgba)
        ctx.new_path()  # Reset cairo path

        # Restore original data array if splits occurred
        if needSplits:
            self._data = oldData

        if self.showTangents:
            self.drawTangents(camera, ctx)

    def drawTangents(self, camera, ctx):
        # Need at least two nodes to draw
        if self.data.shape[0] < 2:
            return

        # # If determinant of the transform matrix is too small,
        # # don't attempt to draw.
        # if abs(np.linalg.det(self.transform)) < 1e-6:
        #     return

        # If transform matrix is too distorted, don't draw.
        if morpho.matrix.thinness2x2(self.transform) < 1e-6:
            return

        # Draw each tangent
        width = max(abs(self.width/2), 1)
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
            ctx.set_source_rgba(*self.tancolor, self.alpha)

            # Temporarily modify cairo coordinates to coincide with
            # physical coordinates.
            with morpho.pushPhysicalCoords(camera.view, ctx):  # Contains a ctx.save()

                # Handle possible other transformations
                morpho.applyTransforms(ctx, self.origin, self.rotation, self.transform)

                ctx.move_to(inx, iny)
                ctx.line_to(x,y)
                ctx.line_to(outx, outy)

            # ctx.restore()
            ctx.stroke()

    # def draw(self, camera, ctx):
    #     self.draw0(camera, ctx, False)
    #     if self.showTangents:
    #         self.draw0(camera, ctx, True)


    # Converts the Spline figure to a similar-looking Path figure.
    # Optionally specify "segsteps" which is how many path steps to
    # use in a single bezier curve segment of the spline.
    # Defaults to 30 steps per segment.
    #
    # Note that this method currently ignores deadends. This may be
    # resolved in a future version.
    def toPath(self, segsteps=30):
        path = morpho.grid.line(0,1, steps=segsteps*(self.length()-1))

        # Make path follow the spline
        path = path.fimage(self.positionAt)

        # Match other tweenables
        path._updateFrom(self, common=True, ignore="deadends")

        return path

    # Takes the function image of the spline under the given func.
    # Note: This applies to ALL control points: both nodes AND
    # handles. This function will skip any control points that are
    # inf or nan.
    def fimage(self, func):
        newfig = self.copy()

        # Convert to a single-dimensional array2d
        seq = newfig._data.reshape(-1)
        # Conditional array for finite values
        finite = np.logical_not(np.logical_or(np.isinf(seq), np.isnan(seq)))

        # Evaluate function on all finite values
        fseq = []
        for z in seq[finite].tolist():
            fseq.append(func(z))
        seq[finite] = fseq
        newfig._data = seq.reshape(newfig._data.shape)

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

    # Concatenates other to self in place. Does not modify other.
    # self retains its original style parameters, though.
    # Also ignores "origin", "rotation", and "transform" attributes
    # for now. Only use this method with paths that have the standard
    # transforms.
    def concat(self, other):
        self._data = np.insert(self._data, self._data.shape[0], other._data, axis=0)

        # Merge deadends from other into self
        nodeCount = self.nodeCount()
        for n in other.deadends:
            self.deadends.add(n+nodeCount)

        return self

    ### TWEEN METHODS ###

    @morpho.tweenMethod
    @morpho.grid.handleDeadendInterp
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
    @morpho.grid.handleDeadendInterp
    @morpho.grid.handleDash
    @morpho.color.handleGradientFills(["fill"])
    @handleSplineNodeInterp
    def tweenSpiral(self, other, t):
        # Handle interpolating everything but the data tweenable
        tw = morpho.Figure.tweenSpiral(self, other, t, ignore="_data")

        # Handle interpolating data
        data1 = self.data.copy()
        data2 = other.data.copy()

        crossCommitHandles(data1, data2)

        # Interpolate using spiral tween method
        with np.errstate(all="ignore"):  # Suppress numpy warnings
            data12 = morpho.spiralInterpArray(data1, data2, t)
        nan2inf(data12)

        tw._data = data12

        return tw


    @classmethod
    def tweenPivot(cls, angle=tau/2):

        # Performs a pivot tween on all tweenables EXCEPT the
        # data array which will be handled separately.
        mainPivot = morpho.Figure.tweenPivot(angle=angle, ignore="_data")

        @morpho.pivotTweenMethod(cls.tweenPivot, angle)  # Enable splitting
        @morpho.grid.handleDeadendInterp
        @morpho.grid.handleDash
        @morpho.color.handleGradientFills(["fill"])
        @handleSplineNodeInterp
        def pivot(self, other, t):
            # Handle interpolating everything but the data tweenable
            tw = mainPivot(self, other, t)

            # Handle interpolating data
            data1 = self.data.copy()
            data2 = other.data.copy()

            crossCommitHandles(data1, data2)

            # Interpolate using pivot tween method
            with np.errstate(all="ignore"):  # Suppress numpy warnings
                data12 = morpho.pivotInterpArray(data1, data2, t, angle=angle)
            nan2inf(data12)

            tw._data = data12

            return tw

        return pivot

# Animates a spline actor appearing by "growing in" from a single point.
# The starting point is always the initial node in the sequence.
# See also: morpho.actions.fadeIn()
@Spline.action
def growIn(spline, duration=30, atFrame=None, *, reverse=False):
    if atFrame is None:
        atFrame = spline.lastID()

    spline0 = spline.last()
    start, end = spline0.start, spline0.end
    spline0.visible = False
    spline1 = spline.newkey(atFrame)
    spline1.visible = True
    if reverse:
        spline1.set(start=1, end=1)
    else:
        spline1.set(start=0, end=0)
    spline2 = spline.newendkey(duration)
    spline2.set(start=start, end=end)

@Spline.action
def shrinkOut(spline, duration=30, atFrame=None, *, reverse=False):
    if atFrame is None:
        atFrame = spline.lastID()

    spline.newkey(atFrame)
    spline1 = spline.newendkey(duration)
    spline1.visible = False
    if reverse:
        spline1.start = 1
    else:
        spline1.end = 0

@Spline.action
def popIn(actor, *args, **kwargs):
    return Path.actions["popIn"](actor, *args, **kwargs)

@Spline.action
def popOut(actor, *args, **kwargs):
    return Path.actions["popOut"](actor, *args, **kwargs)

@Spline.action
def highlight(actor, *args, **kwargs):
    return Path.actions["highlight"](actor, *args, **kwargs)

@Spline.action
def flourish(actor, *args, **kwargs):
    return Path.actions["flourish"](actor, *args, **kwargs)

@Spline.action
def drawIn(actor, *args, **kwargs):
    return Path.actions["drawIn"](actor, *args, **kwargs)

Spline.action(wiggle)


# MultiFigure version of Spline.
# See "morpho.graphics.MultiImage" for more info on the basic idea here.
#
# Notably, this class can import an SVG file and render it.
# See MultiSpline.fromsvg()
@MultiFigure._modifyMethods(
    ["autosetHandles", "close", "commitHandles",
    "reverse", "linkHandles"],
    Spline, MultiFigure._applyToSubfigures
    )
@MultiFigure._modifyMethods(
    ["node", "inhandle", "outhandle", "inhandleRel", "outhandleRel",
    "newNode_old", "newNode", "newNodes", "delNode",
    "splitAt", "splitAtIndex", "insertNodes"],
    Spline, MultiFigure._returnOrigCaller
    )
class MultiSplineBase(morpho.grid.MultiPathBase):

    _basetype = Spline

    def __init__(self, data=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)

    # Parses an SVG file/stream to construct a MultiSpline
    # representation of it. See Spline.fromsvg() for more info.
    #
    # By default it constructs a Spline from every SVG Path element
    # found within the source, but this can be changed by passing
    # in an index, a tuple of indices, a slice, or a tuple of slices
    # into the `index` keyword.
    # Any additional keyword arguments not explicitly listed here
    # are set as attributes of the returned figure or its subfigures.
    @classmethod
    def fromsvg(cls, source, *, view=None, windowShape=None,
        svgOrigin=None, align=(0,0), boxWidth=None, boxHeight=None,
        index=sel[:], flip=True, arcError=0.1, tightbox=False,
        **kwargs):

        svg = parseSVG(source)
        svgpaths = list(svg.elements(lambda elem: isinstance(elem, se.Shape)))

        # Return empty MultiSpline if SVG source has no paths.
        if len(svgpaths) == 0:
            return cls()

        # Generate raw Spline figures
        splines = []
        for svgpath in listselect(svgpaths, index).values():
            spline = Spline.fromsvg(svgpath,
                svgOrigin=0, flip=False, arcError=arcError, tightbox=tightbox)
            splines.append(spline)

        # Compute overall bounding box
        XMIN, YMIN, XMAX, YMAX = oo, oo, -oo, -oo
        for svgpath in svgpaths:
            try:
                xmin, ymin, xmax, ymax = np.array(svgpath.bbox()).tolist() if not tightbox else np.array(Spline._tightbbox(svgpath)).tolist()
            except TypeError:
                continue
            XMIN = min(XMIN, xmin)
            YMIN = min(YMIN, ymin)
            XMAX = max(XMAX, xmax)
            YMAX = max(YMAX, ymax)
        svgbbox = [XMIN, YMIN, XMAX, YMAX]

        if oo in svgbbox or -oo in svgbbox:
            raise TypeError("Given SVG has no well-defined bounding box.")

        for spline in splines:
            spline._transformForSVG(
                svgbbox, boxWidth, boxHeight, svgOrigin, align, flip,
                view, windowShape
                )

        multispline = cls(splines)
        multispline.squeeze()  # Remove empty and singleton splines
        multispline.set(**kwargs)  # Pass additional kwargs to set()
        return multispline

    # Converts the MultiSpline into a similar looking MultiPath figure.
    # See also: Spline.toPath()
    def toPath(self, segsteps=30, *, _cls=morpho.grid.MultiPath):
        # `_cls` is a hidden keyword parameter that can override
        # using MultiPath as the container type. Mainly for use
        # by MultiSpline3D so it can override it to be MultiPath3D.
        subpaths = [subspline.toPath(segsteps) for subspline in self.figures]
        multipath = _cls(subpaths)
        multipath._updateFrom(self, common=True, ignore="figures")
        return multipath

    # For internal use by replaceTex().
    # Given a gauge string and a match function, returns the
    # first subfigure that matches the gauge. Raises KeyError
    # if no matches found.
    def _findGaugeMatch(self, gauge, matches):
        for glyph in self.figures:
            if matches(glyph):
                return glyph
        raise KeyError(f"Could not find gauge {repr(gauge)+' ' if isinstance(gauge, str) else ''}among subfigures.")

    # Replaces the MultiSpline with a MultiSpline generated
    # from morpho.latex.parse(). Intended to provide an easier
    # way to morph one LaTeX spline into another one, like this:
    #   myTexSpline.newendkey(30).replaceTex(r"E = mc^2")
    #
    # If a string is passed in to the optional keyword `gauge`,
    # the glyph corresponding to the string will be used as a
    # reference to rescale the final MultiSpline so that the
    # gauge glyph's size remains unchanged. If the MultiSpline
    # contains multiple glyphs that match the given gauge, the
    # first instance is always used in both the old and new
    # MultiSplines. The `gauge` can also be specified as a
    # Spline or MultiSpline figure directly.
    #
    # Optionally, parameter `align` can be set to `morpho.GAUGE`
    # to align the final MultiSpline to keep the gauge glyph in
    # the same position after replacement.
    def replaceTex(self, tex, *, pos=None, align=None,
            boxWidth=None, boxHeight=None,
            gauge=None, **kwargs):

        # Set new flag `alignGauge` so that `align` is freed
        # to be a normal value.
        if align is morpho.GAUGE:
            if gauge is None:
                raise ValueError("Cannot align gauge because no gauge is set.")
            alignGauge = True
            align = None
        else:
            alignGauge = False

        if gauge is not None:
            if not(boxWidth is None and boxHeight is None):
                raise ValueError("A gauge cannot be used when a boxWidth/boxHeight is also specified.")
            # Extract box height of symbol
            if isinstance(gauge, str):
                matchfunc = morpho.latex.matches(gauge)
            elif isinstance(gauge, Spline):
                matchfunc = lambda glyph, target=gauge: glyph.matchesShape(target)
            elif isinstance(gauge, MultiSpline):
                if len(gauge.figures) != 1:
                    raise ValueError("MultiSpline `gauge` must contain exactly one subspline.")
                target = gauge.figures[0]
                matchfunc = lambda glyph, target=target: glyph.matchesShape(target)
            else:
                raise TypeError(f"Unexpected type {repr(type(gauge).__name__)} used for gauge.")
            gaugeGlyph_old = self._findGaugeMatch(gauge, matchfunc)

        box = shiftBox(self.box(raw=True), self.origin)
        if align is None:
            align = self.boxAlign(box=box, invalidValue=0)
        if boxWidth is None and boxHeight is None:
            boxHeight = box[-1] - box[-2]
        multispline = morpho.latex.parse(tex,
            align=align, boxWidth=boxWidth, boxHeight=boxHeight,
            **kwargs
            )
        self.figures = multispline.figures
        if pos is not None:
            # Using self.pos is intentional here! Don't replace with self.origin!
            # This is because self.pos means something different for MultiSpline3D!
            self.pos = pos

        if gauge is not None:
            # Extract new height of symbol and rescale the whole
            # MultiSpline so it stays the same as the old height.
            gaugeGlyph_new = self._findGaugeMatch(gauge, matchfunc)
            self.rescale(gaugeGlyph_old.boxHeight()/gaugeGlyph_new.boxHeight())
            if alignGauge:
                # Shift by amount gauge moved.
                self.iall.origin += gaugeGlyph_old.center() - gaugeGlyph_new.center()

        return self

    # Checks if every corresponding subfigure between self and other
    # coincides. See Spline.coincides() for more info.
    def coincides(self, other):
        return len(self.figures) == len(other.figures) and \
            self.origin == other.origin and \
            self.rotation == other.rotation and \
            np.array_equal(self._transform, other._transform) and \
            all(self_fig.coincides(other_fig) for self_fig, other_fig in zip(self.figures, other.figures))

    # Checks if every corresponding subfigure between self and other
    # have matching shapes. See Spline.matchesShape() for more info.
    def matchesShape(self, other):
        return len(self.figures) == len(other.figures) and \
            all(self_fig.matchesShape(other_fig) for self_fig, other_fig in zip(self.figures, other.figures))


    ### TWEEN METHODS ###

    tweenLinear = MultiFigure.Multi(Spline.tweenLinear, morpho.Figure.tweenLinear)
    tweenSpiral = MultiFigure.Multi(Spline.tweenSpiral, morpho.Figure.tweenSpiral)

    @classmethod
    def tweenPivot(cls, angle=tau/2, *args, **kwargs):
        pivot = MultiFigure.Multi(
            Spline.tweenPivot(angle, *args, **kwargs),
            morpho.Figure.tweenPivot(angle, *args, **kwargs)
            )
        # Enable splitting for this tween method
        pivot = morpho.pivotTweenMethod(cls.tweenPivot, angle)(pivot)

        return pivot

@TransformableFrame.modifyFadeActions
class MultiSpline(MultiSplineBase, FancyFrame):
    pass

MultiSpline.action(wiggle)

Multispline = MultiSpline  # Alias

# Assign MultiSpline as the dedicated multifigure version of Spline.
Spline._multitype = MultiSpline


# 3D version of MultiSpline meant to enable 2D MultiSplines to be
# positionable and orientable in 3D space. Its main use case is
# for rendering 3D LaTeX expressions via morpho.latex.parse3d().
#
# Note that this is NOT a full SpaceMultiSpline class, which would
# be a MultiFigure of SpaceSplines! Rather, this is just a regular
# 2D MultiSpline which can be rendered in a 3D space like SpaceImage
# can.
#
# The main differences from 2D MultiSplines is three new attributes:
# pos = 3D position as an np.array. Default: [0,0,0] (the origin)
# orient = Orientation in 3D space as a 3x3 rotation matrix.
#       Default: np.eye(3) (oriented on the xy-plane facing the
#       +z direction)
# orientable = Boolean denoting whether the MultiSpline should be
#       treated as an orientable 3D object, or more like a
#       2D "sticker" object. Default: False
#
# Note that `pos` is not merely an alias for `origin` like it is
# for 2D MultiSplines. Here they are distinct: `pos` controls 3D
# position, whereas `origin` controls 2D position within the
# MultiSpline's local plane.
class MultiSpline3D(morpho.grid.MultiPath3D, MultiSplineBase):

    # Converts the MultiSpline3D figure into a similar looking
    # MultiPath3D figure.
    # See also: MultiSpline.toPath()
    def toPath(self, segsteps=30, *, _cls=morpho.grid.MultiPath3D):
        return super().toPath(segsteps, _cls=_cls)

    ### TWEEN METHODS ###

    tweenLinear = MultiSplineBase.tweenLinear


# Space version of Spline figure. See "Spline" for more info.
class SpaceSpline(Spline):
    def __init__(self, data=None, width=3, color=(1,1,1), alpha=1):

        # Use normal Spline constructor to start
        super().__init__(data=None, width=width, color=color, alpha=alpha)

        # Initialize origin triple
        origin = morpho.matrix.array([0,0,0])


        if data is None:
            # Use default data array supplied by superclass's constructor
            data = np.array([], dtype=float).reshape(0, 3, 3)
        elif type(data) is Spline:
            spline = data  # Rename so the following lines make more sense

            # Copy over state and all other attributes except data
            self._updateFrom(spline, common=False, ignore={"_data"}.union(morpho.METASETTINGS))

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
            # print(data.shape)
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

    def fimage(self, func):
        newfig = self.copy()

        # Convert to a list of 3-vectors
        seq = newfig._data.reshape(-1, 3)

        # Evaluate function on all finite vectors
        for n,v in enumerate(seq):
            if isbadarray(v):
                continue
            seq[n] = func(v)
        newfig._data = seq.reshape(newfig._data.shape)

        return newfig

    # box() method for SpaceSpline is currently unimplemented.
    def box(self, *args, **kwargs):
        raise NotImplementedError("box() method is currently unimplemented for SpaceSpline.")

    # fromsvg() is currently not implemented for SpaceSplines.
    def fromsvg(self, *args, **kwargs):
        raise NotImplementedError
        # Cannot simply inherit because 2D fromsvg() uses
        # the `transform` attribute to scale and flip the spline.
        # This attribute does not exist for SpaceSplines.

    # Returns or sets the position of the node of given index.
    # Usage: myspline.node(n) -> position of nth node
    #        myspline.node(n, value) sets nth node position to value
    #
    # If setting a node, you can optionally supply inhandle and
    # outhandle values as well:
    #   myspline.node(n, node, inhandle, outhandle)
    # and optionally make them absolute by passing False to
    # relHandles:
    #   myspline.node(n, node, inhandle, outhandle, relHandles=False)
    def node(self, index, value=None, inhandle=None, outhandle=None,
        *, relHandles=True):

        if value is None:
            return self.data[index, 0, :].copy()

        self.data[index, 0, :] = morpho.array(value)
        if inhandle is not None:
            if relHandles:
                self.inhandleRel(index, inhandle)
            else:
                self.inhandle(index, inhandle)
        if outhandle is not None:
            if relHandles:
                self.outhandleRel(index, outhandle)
            else:
                self.outhandle(index, outhandle)

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
    def newNode(self, point, inhandle=(oo,oo,oo), outhandle=(oo,oo,oo),
        beforeIndex=oo, *, relHandles=True):

        # Handle out of bounds beforeIndex value.
        beforeIndex = min(beforeIndex, self.length())  # Clamp overflows
        if beforeIndex < 0:  # Cycle underflows
            beforeIndex = beforeIndex % self.length()

        # Convert to np.arrays if needed
        point = morpho.array(point)
        inhandle = morpho.array(inhandle)
        outhandle = morpho.array(outhandle)

        if relHandles:
            inhandle = point + inhandle
            outhandle = point + outhandle

        if self._data.size == 0:
            self._data = np.array([[point, inhandle, outhandle]], dtype=float)
        else:
            self._data = np.insert(self.data, beforeIndex, [point,inhandle,outhandle], axis=0)
        return self


    # Closes the path IN PLACE if it is not already closed.
    # If optional kwarg `local` is set to True, the closure
    # is performed relative to the latest deadend.
    # If optional kwarg `straight` is set to False, the
    # closure will be made using the current initial
    # and final tangents.
    def close(self, *, local=False, straight=True):
        if self.length() < 2 or np.array_equal(self.node(0), self.node(-1)):
            return self

        startIndex = max(self.deadends) + 1 if local and len(self.deadends) > 0 else 0
        self._data = np.insert(self._data, self.length(), self._data[startIndex,:,:].copy(), axis=0)

        # Flatten handles
        if straight:
            self.outhandleRel(-2, 0)
            self.inhandleRel(-1, 0)

        return self


    # Translates the spline by the value of the "origin" attribute
    # and then resets the "origin" attribute to (0,0,0).
    def commitTransforms(self):
        with np.errstate(all="ignore"):  # Suppress numpy warnings
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
        path.fill = self.fill.copy() if object_hasattr(self.fill, "copy") else self.fill
        path.alphaFill = self.alphaFill
        path.alpha = self.alpha
        path.width = self.width
        path.origin = self.origin.copy()
        path._updateSettings(self)

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
        spline._updateFrom(self, common=True, copy=False, ignore={"_data"}.union(morpho.METASETTINGS))

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

    def __init__(self, pos=0, xradius=1, yradius=None,
        strokeWeight=3, color=(1,1,1), fill=(1,0,0),
        alphaEdge=1, alphaFill=1, alpha=1):

        super().__init__()

        if yradius is None:
            yradius = xradius

        self.Tweenable("pos", pos, tags=["complex", "position"])
        self.Tweenable("xradius", xradius, tags=["scalar"])
        self.Tweenable("yradius", yradius, tags=["scalar"])
        self.Tweenable("strokeWeight", strokeWeight, tags=["scalar", "pixel"])
        self.Tweenable("color", list(color), tags=["color"])
        self.Tweenable("fill", list(fill), tags=["color"])
        self.Tweenable("alphaEdge", alphaEdge, tags=["scalar"])
        self.Tweenable("alphaFill", alphaFill, tags=["scalar"])
        self.Tweenable("alpha", alpha, tags=["scalar"])
        self.Tweenable("dash", [], tags=["scalar", "list", "pixel"])
        self.Tweenable("dashOffset", 0, tags=["scalar", "pixel"])
        self.Tweenable("rotation", 0, tags=["scalar"])
        self.Tweenable("_transform", np.identity(2), tags=["nparray"])

    @property
    def origin(self):
        return self.pos

    @origin.setter
    def origin(self, value):
        self.pos = value

    @property
    def transform(self):
        return self._transform

    @transform.setter
    def transform(self, value):
        self._transform = morpho.matrix.array(value)

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

    @property
    def eccentricity(self):
        a = self.xradius
        b = self.yradius
        if a < b:
            a,b = b,a
        return math.sqrt(1-(b/a)**2)

    @property
    def majorRadius(self):
        return max(self.xradius, self.yradius)

    @property
    def minorRadius(self):
        return min(self.xradius, self.yradius)

    # Converts the Ellipse into an approximate Path figure.
    # Specify `dTheta` keyword to control angle difference
    # between adjacent vertices. By default: 2pi/72 rad (5 deg).
    def toPath(self, **kwargs):
        return self.toPolygon(**kwargs).toPath()

    # Converts the Ellipse into an approximate Polygon figure.
    # Specify `dTheta` keyword to control angle difference
    # between adjacent vertices. By default: 2pi/72 rad (5 deg).
    def toPolygon(self, **kwargs):
        poly = morpho.grid.ellipse(self.pos, self.xradius, self.yradius, relative=True, **kwargs)
        poly._updateFrom(self, common=True)
        poly.set(
            width=self.strokeWeight,
            origin=self.pos
            )
        return poly

    def draw(self, camera, ctx):
        # Don't draw if radii values are zero.
        if self.xradius == 0 or self.yradius == 0:
            return

        # # If determinant of the transform matrix is too small,
        # # don't attempt to draw.
        # if abs(np.linalg.det(self.transform)) < 1e-6:
        #     return

        # If transform matrix is too distorted, don't draw.
        if morpho.matrix.thinness2x2(self.transform) < 1e-6:
            return

        view = camera.view

        # X,Y = morpho.screenCoords(self.pos, view, ctx)

        # ctx.save()
        # ctx.translate(X,Y)
        # WIDTH = morpho.pixelWidth(self.xradius, view, ctx)
        # HEIGHT = morpho.pixelHeight(self.yradius, view, ctx)

        # # Zero is not allowed. Constrain to 0.1
        # WIDTH = max(WIDTH, 0.1)
        # HEIGHT = max(HEIGHT, 0.1)

        with morpho.pushPhysicalCoords(view, ctx):
            # Translate ellipse center to corresponding point
            ctx.translate(self.pos.real, self.pos.imag)

            # Apply transformation tweenables
            if not np.array_equal(self.transform, I2):
                xx, xy, yx, yy = self.transform.flatten().tolist()
                # Order is MATLAB-style: top-down, then left-right. So the matrix
                # specified below is:
                # [[xx  xy]
                #  [yx  yy]]
                mat = cairo.Matrix(xx, yx, xy, yy)
                # Apply to context
                ctx.transform(mat)
            if self.rotation != 0:
                ctx.rotate(self.rotation)

            # Stretch unit circle into the correct ellipse
            # dimensions
            ctx.scale(self.xradius, self.yradius)

            # Draw unit circle
            ctx.move_to(1,0)
            ctx.arc(0,0, 1, 0, tau)
        # ctx.restore()

        ctx.set_source_rgba(*self.fill, self.alphaFill*self.alpha)
        ctx.fill_preserve()
        if self.strokeWeight < 0.5:  # Don't stroke if strokeWeight is too small
            ctx.new_path()
        else:
            ctx.set_source_rgba(*self.color, self.alphaEdge*self.alpha)
            ctx.set_line_width(self.strokeWeight)
            ctx.set_dash(self.dash, self.dashOffset)
            ctx.stroke()
            ctx.set_dash([])

# Animates an Ellipse actor appearing by growing its
# radii from zero.
@Ellipse.action
def popIn(ellipse, duration=30, atFrame=None):
    if atFrame is None:
        atFrame = ellipse.lastID()

    ellipse0 = ellipse.last()
    ellipse0.visible = False
    ellipse1 = ellipse.newkey(atFrame)
    ellipse1.visible = True
    ellipse.newendkey(duration)
    ellipse1.radius = 0
    ellipse1.set(strokeWeight=0)

# Animates an Ellipse actor disappearing by shrinking
# its radii to zero.
@Ellipse.action
def popOut(ellipse, duration=30, atFrame=None):
    if atFrame is None:
        atFrame = ellipse.lastID()

    ellipse.newkey(atFrame)
    ellipse1 = ellipse.newendkey(duration)
    ellipse1.set(radius=0, strokeWeight=0, visible=False)

Ellipse.action(wiggle)


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

    def __init__(self, pos=0, xradius=1, yradius=None, theta0=0, theta1=None,
        strokeWeight=3, color=(1,1,1), alpha=1):

        if yradius is None:
            yradius = xradius
        if theta1 is None:
            theta1 = theta0 + tau

        super().__init__()

        pos = morpho.Tweenable("pos", pos, tags=["complex", "position"])
        xradius = morpho.Tweenable("xradius", xradius, tags=["scalar"])
        yradius = morpho.Tweenable("yradius", yradius, tags=["scalar"])
        theta0 = morpho.Tweenable("theta0", theta0, tags=["scalar"])
        theta1 = morpho.Tweenable("theta1", theta1, tags=["scalar"])
        strokeWeight = morpho.Tweenable("strokeWeight", strokeWeight, tags=["scalar", "pixel"])
        color = morpho.Tweenable("color", list(color), tags=["color"])
        alpha = morpho.Tweenable("alpha", alpha, tags=["scalar"])

        self.extendState([pos, xradius, yradius, theta0, theta1, strokeWeight, color, alpha])

        self.Tweenable("dash", [], tags=["scalar", "list", "pixel"])
        self.Tweenable("dashOffset", 0, tags=["scalar", "pixel"])

    @property
    def origin(self):
        return self.pos

    @origin.setter
    def origin(self, value):
        self.pos = value

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

        # steps = int(math.ceil(360 / abs(dTheta)))
        # dTheta *= tau/360  # convert dTheta to radians
        thetaSpan = theta1 - theta0
        steps = math.ceil(abs(thetaSpan / dTheta))

        # Adjust dTheta so all steps are of uniform angular size.
        dTheta = thetaSpan/steps

        # Make unit circle arc
        z0 = cmath.exp(theta0*1j)
        z1 = cmath.exp(theta1*1j)
        seq = [z0]
        for n in range(1, steps):
            seq.append(cmath.exp((theta0+n*dTheta)*1j))
        seq.append(z1)

        path = morpho.grid.Path(seq)

        # Stretch it into an ellipse and move it
        path = path.fimage(lambda z: mat(self.xradius,0,0,self.yradius)*z)
        # path = path.fimage(lambda z: z + self.pos)

        path._updateFrom(self, common=True)
        path.origin = self.pos
        path.width = self.strokeWeight

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
            theta1 = theta0 + sgn(theta1-theta0)*tau

        Z0 = cmath.exp(theta0*1j)
        ctx.move_to(Z0.real, Z0.imag)
        if theta0 <= theta1:
            ctx.arc(0,0, 1, theta0, theta1)
        else:
            ctx.arc_negative(0,0, 1, theta0, theta1)
        ctx.restore()

        if self.strokeWeight < 0.5:  # Don't stroke if strokeWeight is too small
            ctx.new_path()
        else:
            ctx.set_source_rgba(*self.color, self.alpha)
            ctx.set_line_width(self.strokeWeight)
            ctx.set_dash(self.dash, self.dashOffset)
            ctx.stroke()
            ctx.set_dash([])

# Animates an e-arc actor appearing by "growing in" from theta0
# toward theta1 unless reverse=True whereby it will grow from
# theta1 toward theta0.
#
# See also: morpho.actions.fadeIn()
@EllipticalArc.action
def growIn(arc, duration=30, atFrame=None, *, reverse=False):
    if atFrame is None:
        atFrame = arc.lastID()

    arc0 = arc.last()
    theta0, theta1 = arc0.theta0, arc0.theta1
    arc0.visible = False
    arc1 = arc.newkey(atFrame)
    arc1.set(visible=True)
    if reverse:
        arc1.set(theta0=theta1)
    else:
        arc1.set(theta1=theta0)
    arc2 = arc.newendkey(duration)
    arc2.set(theta0=theta0, theta1=theta1)

@EllipticalArc.action
def shrinkOut(arc, duration=30, atFrame=None, *, reverse=False):
    if atFrame is None:
        atFrame = arc.lastID()

    arc0 = arc.last()
    theta0, theta1 = arc0.theta0, arc0.theta1
    arc.newkey(atFrame)
    arc1 = arc.newendkey(duration)
    arc1.set(visible=False)
    if reverse:
        arc1.theta0 = theta1
    else:
        arc1.theta1 = theta0


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

        if self.strokeWeight < 0.5:  # Don't stroke if strokeWeight is too small
            ctx.new_path()
        else:
            ctx.set_source_rgba(*self.color, self.alphaEdge*self.alpha)
            ctx.set_line_width(self.strokeWeight)
            ctx.set_dash(self.dash, self.dashOffset)
            ctx.stroke()
            ctx.set_dash([])

    # Converts the figure into an equivalent Path figure.
    # Optionally specify the angular steps (in rads).
    # Default: 2pi/72 (5 degrees)
    # NOTE: Arc center will be assigned using the `origin`
    # transformation attribute.
    # You will need to call commitTransforms() on the resulting
    # Path if you want the vertex list to perfectly reflect
    # points on the arc in true space.
    def toPath(self, dTheta=tau/72):
        return self.toPolygon(dTheta).toPath()

    # Converts the figure into an equivalent Polygon figure.
    # Optionally specify the angular steps (in rads).
    # Default: 2pi/72 (5 degrees)
    # NOTE: Arc center will be assigned using the `origin`
    # transformation attribute.
    # You will need to call commitTransforms() on the resulting
    # Polygon if you want the vertex list to perfectly reflect
    # points on the arc in true space.
    def toPolygon(self, dTheta=tau/72):
        theta0, theta1 = self.theta0, self.theta1
        # If angular span is greater than tau,
        # just draw a circle
        if abs(theta1 - theta0) >= tau:
            theta1 = theta0 + tau

        # steps = int(math.ceil(360 / abs(dTheta)))
        # dTheta *= tau/360  # convert dTheta to radians
        thetaSpan = theta1 - theta0
        steps = math.ceil(abs(thetaSpan / dTheta))

        # Adjust dTheta so all steps are of uniform angular size.
        dTheta = thetaSpan/steps

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

        # Stretch it into an ellipse and move it
        poly = poly.fimage(lambda z: mat(self.xradius,0,0,self.yradius)*z)
        # poly = poly.fimage(lambda z: z + self.pos)

        poly._updateFrom(self, common=True)
        poly.origin = self.pos
        poly.width = self.strokeWeight

        return poly

### HELPERS ###

# Parses a string of SVG data using svgelements.SVG.parse()
# and returns the resulting SVG object.
def parseSVGstring(svgstring):
    # Open a data stream and load the svg data into it,
    # then pass the stream into the svgelements parser.
    with io.StringIO() as stream:
        stream.write(svgstring)
        stream.seek(0)
        svg = se.SVG.parse(stream)
    return svg


# Wrapper around svgelements.SVG.parse() which enables
# it to parse raw SVG code as a string.
#
# Note this function first attempts to open the source
# string as a file and upon failure attempts to parse it
# as raw SVG data. Therefore this function may be slow
# if it needs to be called every frame draw.
def parseSVG(source):
    try:
        svg = se.SVG.parse(source)
    except FileNotFoundError:
        svg = parseSVGstring(source)
    return svg


### GADGETS ###

# These functions can be found here as well as grid.
line = morpho.grid.line
spaceLine = morpho.grid.spaceLine
rect = morpho.grid.rect
arc = morpho.grid.arc

# Return a generic spline in the shape of a rectangle with rounded
# corners. Note that the rounded corners will be approximate
# circular arcs, but not perfect.
#
# INPUTS
# box = Box region specified as [xmin, xmax, ymin, ymax]
# radius = Radius of rounded corners.
#       Default: Infinity (clamp to max possible radius)
# KEYWORD-ONLY INPUTS
# pad = Padding to apply to box. Default: 0
# corner = Which corner should the animation start at?
#       Values are given as diagonal compass directions:
#       "NW", "SW", "SE", "NE". Default: "NW"
# CCW = Boolean specifying draw direction being counter-clockwise or not.
#       Default: True
# relative = Boolean which if set to True, makes the rounded
#       rectangle centered using its `origin` attribute.
@handleBoxTypecasting
def roundedRect(box, radius=oo, *, pad=0, corner="NW", CCW=True, relative=False):
    a,b,c,d = box
    a -= pad
    b += pad
    c -= pad
    d += pad
    SW = a + c*1j
    NW = a + d*1j
    NE = b + d*1j
    SE = b + c*1j
    width = b - a
    height = d - c
    semiwidth = width/2
    semiheight = height/2

    # Radius cannot be bigger than the smallest semi-dimension
    radius = min(radius, semiwidth, semiheight)

    # Lengths of the flat sections of the rounded rect
    flatwidth = width - 2*radius
    flatheight = height - 2*radius
    # Handle floating point precision issues when radius
    # exactly equals one of the semi-dimensions.
    if abs(flatwidth) < 1e-8*width:
        flatwidth = 0
    if abs(flatheight) < 1e-8*height:
        flatheight = 0

    # Corners in the standard order
    corners = [NW, SW, SE, NE]

    spline = Spline()
    if relative:
        center = (a+b)/2 + 1j*(c+d)/2
        corners = [corner-center for corner in corners]
        spline.origin = center

    # Calculate corner number
    corner = corner.upper()
    try:
        cornerID = ["NW", "SW", "SE", "NE"].index(corner)
    except ValueError:
        raise ValueError('corner must be "NW", "SW", "SE", or "NE".')

    unit = 1j**(cornerID-1)  # Current direction spline is flowing
    # Alternating list of flat segment lengths. The order changes
    # depending on the initial corner.
    flatdists = [flatheight, flatwidth]*2 if cornerID % 2 == 0 else [flatwidth, flatheight]*2

    if not CCW:
        corners = corners[::-1]
        cornerID = 3 - cornerID
        unit *= 1j
        flatdists = flatdists[::-1]
    # Calculate corner ordering for construction of the
    # rounded rectangle.
    corners = corners[cornerID:] + corners[:cornerID]

    for corner, flatdist in zip(corners, flatdists):
        spline.newNode(corner+radius*unit, -radius*tau/12*unit, flatdist/3*unit)
        if flatdist == 0:
            spline.newNode(corner+radius*unit, 0, radius*tau/12*unit)
        else:
            spline.newNode(corner+(radius+flatdist)*unit, -flatdist/3*unit, radius*tau/12*unit)
        unit *= 1j if CCW else -1j
    spline.close(straight=False)

    return spline


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
