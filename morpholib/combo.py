'''
Contains classes useful for making composite figures.
'''

import morpholib as morpho
import morpholib.anim
from morpholib.anim import Frame, SpaceFrame, MultiFigure, SpaceMultiFigure, \
    SpaceMultifigure, Spacemultifigure
from morpholib import object_hasattr
from morpholib.tools.dev import listselect
from morpholib.tools.basics import *

import math, cmath
import numpy as np


# Used to save the state of a figure list's transformation
# attributes (origin, rotation, transform) so they can be
# temporarily modified (usually in a draw() method) and then
# restored. Note that this will fail if any figure transformations
# are modified IN PLACE (e.g. modifying the transform matrix in
# place). Transformations must be fully OVERWRITTEN.
class _FigureTransformMemory(object):
    def __init__(self, figures):
        # Initialize lists to store original origin/transform values
        # so they can be restored after being modified.
        self.figures = figures
        self.orig_origins = [fig.origin for fig in figures]
        self.orig_rotations = [fig.rotation for fig in figures]
        self.orig_transforms = [fig._transform for fig in figures]

    # Called upon entering a `with` block
    def __enter__(self):
        return self

    # Called upon exiting a `with` block
    def __exit__(self, type, value, traceback):
        # Restore original transformation values
        for fig, origin, rotation, transform in zip(self.figures, self.orig_origins, self.orig_rotations, self.orig_transforms):
            fig.origin = origin
            fig.rotation = rotation
            fig._transform = transform

# Mainly to be used as an inherited class.
# A Frame that is meant to take subfigures that possess the standard
# 2D transformation attributes origin, rotation, transform, but also
# takes toplevel transformation attributes and implements methods that
# allow toplevel and sublevel transformations to interact compatibly
# with each other.
class TransformableFrame(Frame):
    # It's tempting to make TransformableFrame inherit from
    # AlignableFigure and/or BackgroundBoxFigure, but I've
    # decided not to since a class like MultiImage may inherit
    # from this class, and AlignableFigure would be incompatible
    # with it (since it uses explicit align). As for
    # BackgroundBoxFigure, it doesn't automatically implement
    # DRAWING the background box; it has to be done manually, and
    # users may not want to implement that themselves.
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.Tweenable("rotation", 0, tags=["scalar"])
        self.Tweenable("_transform", np.eye(2), tags=["nparray"])

    @property
    def transform(self):
        return self._transform

    @transform.setter
    def transform(self, value):
        self._transform = morpho.matrix.array(value)

    # Computes the bounding box of the entire figure.
    # Returned as [xmin, xmax, ymin, ymax]
    #
    # If optional kwarg `raw` is set to True, the
    # bounding box is computed without applying
    # the transformation attributes origin, rotation, transform.
    def box(self, *args, raw=False, **kwargs):
        if not raw and not(self.rotation == 0 and np.array_equal(self._transform, I2)):
            temp = self.copy()
            temp.commitTransforms()
            return temp.box(*args, raw=True, **kwargs)
        return shiftBox(totalBox(subfig.box(*args, **kwargs) for subfig in self.figures), self.origin if not raw else 0)

    # Meant to be called in a `with` statement like follows:
    #   with myframe.TemporarySubfigureTransforms():
    #       ...
    # Within the `with` block, subfigure transformation attributes
    # can be safely overwritten (though not modified in place)
    # and when the block exits, the original subfigure transformation
    # values will be restored.
    def TemporarySubfigureTransforms(self):
        return _FigureTransformMemory(self.figures)

    # Mainly for internal use.
    # Applies toplevel transforms `rotation` and `transform`
    # (but not `origin`) to subfigures by modifying
    # the origin and transform attributes of subfigures.
    # Note that this method is applied IN PLACE and will
    # permanently modify subfigure transformations unless
    # called within a temporary transform context. So to
    # safely use this method, use the following template:
    #   with self.TemporarySubfigureTransforms():
    #       self._applyTransformsToSubfigures()
    #       ...
    #
    # Also note that unlike commitTransforms(), this method
    # does NOT reset the toplevel transformation attributes.
    def _applyTransformsToSubfigures(self):
        # Calculate as a single matrix the overall effect
        # of both the global rotation and transform.
        rotateAndTransform = self._transform @ morpho.matrix.rotation2d(self.rotation)
        rotateAndTransform_mat = morpho.matrix.Mat(rotateAndTransform)

        for fig in self.figures:
            # Temporarily modify origin and transform
            if fig.origin != 0:
                fig.origin = rotateAndTransform_mat * fig.origin
            fig._transform = rotateAndTransform @ fig._transform
        return self

    # Applies the toplevel transformation attributes to the
    # transformation attributes of the subfigures and resets
    # the toplevel transforms.
    def commitTransforms(self):
        # Apply rotation and transform to subfigures
        self._applyTransformsToSubfigures()

        # Apply translation to all subfigures
        for subfig in self.figures:
            # Doing it manually instead of using `iall` just in case
            # this method is used for space figures where `origin`
            # might be an np.array and so in-place addition is not
            # advisable.
            subfig.origin = subfig.origin + self.origin

        # Reset toplevel transformation tweenables
        self.origin = 0
        self.rotation = 0
        self._transform = np.eye(2)

        return self

    # Transformable version of Frame.partition().
    def partition(self, *args, cls=None, **kwargs):
        if cls is None:
            cls = TransformableFrame
        return super().partition(*args, cls=cls, **kwargs)

    # Given a Frame of subframes generated from calling partition(),
    # combine() recombines them back into a single TransformableFrame
    # figure. Note that this method leaves the original Frame figure
    # that called it unchanged.
    def combine(self):
        copy = self.copy()
        copy.commitTransforms()
        for subframe in copy.figures:
            if isinstance(subframe, TransformableFrame):
                subframe.commitTransforms()
        return super(TransformableFrame, copy).combine()

    # Merges another TransformableFrame into this one.
    # See Frame.merge() for more info.
    # Note that this version of the method automatically
    # attempts to commit the toplevel transforms of `other`
    # before merging so that the visual appearance will be
    # preserved.
    def merge(self, other, *args, **kwargs):
        if isinstance(other, TransformableFrame):
            other.commitTransforms()
        return super().merge(other, *args, **kwargs)

    def draw(self, camera, ctx):
        if not(self.rotation == 0 and np.array_equal(self._transform, I2)):
            # Temporarily apply additional transforms to subfigures if global
            # rotation/transform are non-identity
            with self.TemporarySubfigureTransforms():
                self._applyTransformsToSubfigures()
                Frame.draw(self, camera, ctx)
        else:
            Frame.draw(self, camera, ctx)

    ### OTHER STUFF ###

    # Decorator to be used on classes that inherit from
    # TransformableFrame. It modifies the `fadeIn()` and `fadeOut()`
    # actions so that the `jump` parameter acts independently of
    # the Frame's toplevel transformations. Without it, performing
    # a fade jump with the TFrame rotated, say, 45 degrees will result
    # in the jump direction be rotated by the same amount.
    @staticmethod
    def modifyFadeActions(cls):
        fadeIn_orig = cls.actions["fadeIn"]
        fadeOut_orig = cls.actions["fadeOut"]

        def fadeIn(actor, *args, **kwargs):
            return _modifiedFadeAction(actor, *args, _baseaction=fadeIn_orig, **kwargs)
        def fadeOut(actor, *args, **kwargs):
            return _modifiedFadeAction(actor, *args, _baseaction=fadeOut_orig, **kwargs)

        # Make a copy so that upstream actions dicts are not
        # affected by this modification.
        cls.actions = cls.actions.copy()

        cls.actions["fadeIn"] = fadeIn
        cls.actions["fadeOut"] = fadeOut

        return cls

# Performs a fadeIn or fadeOut action but first adjusts the
# `jump` parameter based on the toplevel rotation and transform
# so that those transformations don't affect jump direction/length.
# A `_baseaction` keyword must be provided which is the original
# fade action that will be called after `jump` is modified.
def _modifiedFadeAction(actor, *args, _baseaction, jump=0, **kwargs):
    # Adjust jump based on toplevel transformations
    fig0 = actor.last()
    rotation = fig0.rotation
    transform = fig0.transform

    # Only adjust `jump` if it's non-zero AND transform is invertible.
    if jump != 0 and np.linalg.det(transform) != 0:
        # We can assume jump is meant to be complex since
        # TransformableFrame should not be used for SpaceFigures
        jump = cmath.exp(-rotation*1j) * (morpho.matrix.Mat(transform).inv*jump)
    return _baseaction(actor, *args, jump=jump, **kwargs)

@TransformableFrame.action
def fadeIn(*args, **kwargs):
    return _modifiedFadeAction(*args, _baseaction=Frame.actions["fadeIn"], **kwargs)

@TransformableFrame.action
def fadeOut(*args, **kwargs):
    return _modifiedFadeAction(*args, _baseaction=Frame.actions["fadeOut"], **kwargs)


# A Frame of figures that can be accessed with array index syntax.
# Normally this class is instantiated by calling figureGrid()
class FigureArray(Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.NonTweenable("_shape", (1, len(self.figures)))

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, value):
        try:
            array = np.array(self.figures, dtype=object)
            array.shape = value
        except ValueError:
            raise ValueError(f"Cannot arrange {len(self.figures)} subfigures into shape {value}.")
        self._shape = array.shape

    @property
    def figureArray(self):
        array = np.array(self.figures, dtype=object)
        array.shape = self.shape
        return array

    @figureArray.setter
    def figureArray(self, value):
        if not isinstance(value, np.ndarray):
            value = np.array(value, dtype=object)
        self.figures = value.reshape(-1).tolist()
        self.shape = value.shape

    # Update the positions of subfigures IN-PLACE to arrange them
    # in a grid. See figureGrid() for more info.
    def updatePositions(self, *, pos=0, align=(0,0), width=None, height=None):
        nrows, ncols = self.shape  # Don't use `shape` directly cuz it could have negatives
        anchor_x, anchor_y = align

        if width is None and height is None:
            raise ValueError("At least one of width or height must be specified.")
        elif width is None:
            width = ncols/nrows * height
        elif height is None:
            height = nrows/ncols * width

        xmin = pos.real - (anchor_x+1)/2*width if ncols > 1 else pos.real
        ymax = pos.imag - (anchor_y-1)/2*height if nrows > 1 else pos.imag

        dx = width/(ncols-1) if ncols > 1 else width
        dy = height/(nrows-1) if nrows > 1 else height

        figarray = self.figureArray
        posnames = ["pos", "_pos", "origin", "_origin"]
        for i in range(nrows):
            for j in range(ncols):
                subfig = figarray[i,j]
                # Find usable toplevel positional tweenable
                for posname in posnames:
                    if posname in subfig._state:
                        break
                    # Set posname to None so that if we escape the loop without
                    # finding a suitable positional tweenable, we can throw
                    # an error!
                    posname = None
                if posname is None:
                    raise AttributeError("Some subfigures do not possess toplevel positional tweenables.")
                setattr(subfig, posname, complex(xmin + j*dx, ymax - i*dy))
        return self

    def _select(self, index, *, _asFrame=False, **kwargs):
        result = super()._select(index, _asFrame=_asFrame, **kwargs)
        if _asFrame:
            # If extracting a subframe, compute its shape and assign it
            if not(isinstance(index, tuple) and len(index) == 2):
                raise IndexError("Subarray extraction requires index to be a single pair (row, col).")
            figarray = self.figureArray
            rowSlice, colSlice = index
            nrows = len(listselect(figarray, rowSlice).keys())
            ncols = len(listselect(figarray.T, colSlice).keys())
            result.shape = (nrows, ncols)
        return result

    def _selectionMap(self, index):
        # Handle case where index is simply the all-slice.
        if index == sel[:]:
            index = sel[:,:]
        elif not(isinstance(index, tuple) and len(index) % 2 == 0):
            raise IndexError("Given index must be a pair (row, col) or a sequence of such pairs.")

        # Convert given index list from a 1D sequence into
        # a list of pairs.
        indices = np.array(index, dtype=object)
        indices.shape = (-1, 2)
        indices = indices.tolist()

        selection = dict()
        for index in indices:
            rowSlice, colSlice = index
            figarray = self.figureArray
            # Extract the selected individual row and column indices
            rowIndices = list(listselect(figarray, rowSlice).keys())
            colIndices = list(listselect(figarray.T, colSlice).keys())
            # Convert into indices in the 1D figure list
            nrows, ncols = self.shape
            selection.update({i*ncols + j : figarray[i,j] for i in rowIndices for j in colIndices})
        return selection


# Returns a FigureArray of the given figures.
#
# INPUTS
# figures = List of figures to combine into a FigureArray.
#           If given a figure object (not as part of a list),
#           it will make copies of the figure to create an
#           array of the given shape.
# KEYWORD-ONLY INPUTS
# shape = Tuple specifying the shape of the grid (rows, cols)
#         Like in numpy, negative values can be supplied to
#         infer a missing dimension. Default: (1,-1) a single row.
# pos = Position of the grid as a complex number. Default: 0 (origin)
# align = Alignment of the grid with respect to the `pos` value.
#         Default: (0,0) (center alignment)
# width, height = Width and height of the grid. If one is unspecified,
#   it will be inferred from the other and the grid shape. However,
#   at least one of width or height must be specified.
# cls = FigureArray subtype to use to construct the grid.
#       Default: FigureArray.
def figureGrid(figures, *,
        shape=(1,-1),
        pos=0, align=(0,0),
        width=None, height=None,
        cls=FigureArray):

    if len(shape) != 2:
        raise TypeError("Given shape must be a pair (nrows, ncols).")

    if isinstance(figures, morpho.Figure):
        figure = figures
        figures = [figure.copy() for n in range(abs(shape[0]*shape[1]))]
        figgrid = cls(figures)
    elif isinstance(figures, dict):
        figgrid = cls(**figures)
    else:
        figgrid = cls(figures)

    figgrid.shape = shape

    figgrid.updatePositions(pos=pos, align=align, width=width, height=height)
    return figgrid
