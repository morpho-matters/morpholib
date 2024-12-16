'''
This submodule is mainly for internal use by the
classes/functions of Morpho and probably should not
be used by the regular end-user.

An assortment of useful functions and classes.
'''

import morpholib as morpho
import morpholib.anim
from morpholib.figure import object_hasattr
from morpholib.tools.basics import *
from morpholib.actions import wiggle

import cairo
import numpy as np
import math, cmath

### SPECIAL EXCEPTIONS ###

# Exception that should be thrown if a dynamically
# computed value cannot be given a single definite
# value. For example, trying to get the attribute
# `tipSize` for a Path whose headSize and tailSize
# differ.
class AmbiguousValueError(ValueError):
    pass


# Extracts viewbox from the given input object `view`.
#
# If `view` is a Layer, Camera actor, or Camera figure, it
# infers the viewbox. In the case of Layer or Camera actor,
# this is inferred by taking the latest keyfigure's viewbox.
def typecastView(view):
    # Handle Layer/Camera/Animation type inputs to view.
    if isinstance(view, morpho.Layer):
        view = view.camera.last().view
    elif isinstance(view, morpho.Actor):
        view = view.last().view
    elif isinstance(view, morpho.anim.Camera):
        view = view.view
    return view

# Extracts window shape from the given input object `window`.
#
# If `window` is an Animation or cairo context, it extracts
# the pixel dimensions as (width, height).
def typecastWindowShape(window):
    if isinstance(window, morpho.Animation):
        window = window.windowShape
    elif isinstance(window, cairo.Context):
        target = window.get_target()
        window = (target.get_width(), target.get_height())
    return window

# NOT IMPLEMENTED YET because I'm not sure it's functionality
# is all that important in light of typecastView/WindowShape().
# The idea is this function would do the job of checking thru
# the owner chain to infer a viewbox, whereas typecastView()
# deals with extracting the actual viewbox from a
# layer/camera/etc. Of note, this function would treat Camera
# figures and actors like any other figure, so it shouldn't
# be used as a replacement for typecastView().
#
# Tries to infer the viewbox the given figure is in.
# Returns None if unsuccessful.
def inferView(figure):
    raise NotImplementedError
    if isinstance(figure, morpho.Actor):
        figure = figure.last()
    # Try to find the layer this figure is a part of
    try:
        layer = figure.owner.owner
    except AttributeError:
        return None
    if layer is None:
        return None
    return typecastView(layer)

# NOT IMPLEMENTED YET because I'm not sure it's functionality
# is all that important in light of typecastView/WindowShape().
# The idea is this function would do the job of checking thru
# the owner chain to infer a window shape, whereas
# typecastWindowShape() deals with extracting the actual viewbox
# from a layer/camera/etc. Of note, this function would treat
# Camera figures and actors like any other figure, so it shouldn't
# be used as a replacement for typecastView().
#
# Tries to infer the window shape of the animation the figure
# belongs to. Returns None if unsuccessful.
def inferWindowShape(figure):
    raise NotImplementedError
    if isinstance(figure, morpho.Actor):
        figure = figure.last()
    # Try to find the Animation object this figure is a part of
    try:
        mation = figure.owner.owner.owner
    except AttributeError:
        return None
    if mation is None:
        return None
    return typecastWindowShape(mation)

# Goes up the owner chain of a Morpho object (e.g. Figure, Actor,
# Layer) searching for an owner of the given type. If it finds it,
# it returns the owner found, otherwise it returns None.
# Optionally, an iteration limit can be specified to ensure
# a very wrongly configured Morpho object that has a cycle in its
# owner chain doesn't result in an infinite loop. If the limit is
# reached, a RecursionError is thrown. The default limit is 5.
def findOwnerByType(obj, cls, *, iterLimit=5):
    for n in range(iterLimit):
        obj = getattr(obj, "owner", None)
        if isinstance(obj, cls) or obj is None:
            return obj
    raise RecursionError(f"Iteration limit of {iterLimit} reached.")

# Decorator allows a method to extract the needed
# `view` and `ctx` parameters from Layer/Camera/Animation
# inputs allowing for syntax like
#   mytext.width(my_layer_or_camera, my_animation)
# whereby `view` will be taken as the latest viewbox in the
# layer and `windowShape` will be taken from the corresponding
# attribute in the animation object.
# If view/ctx is unspecified, an attempt will be made to infer
# them by going thru the figure's owner chain looking
# for a layer or animation object.
def typecastViewCtx(method):
    def wrapper(self, view=None, ctx=None, *args, **kwargs):
        # If view and/or ctx is unspecified, try to implicitly
        # determine the layer or animation object containing
        # the figure.
        if view is None:
            # Try to find the layer this figure is a part of
            try:
                view = self.owner.owner
                if view is None: raise AttributeError
            except AttributeError:
                raise TypeError("Figure is not owned by a layer. `view` cannot be inferred.")

            # # I DON'T THINK THIS IS A GOOD FEATURE ANYMORE!!!
            # # IT'S HERE FOR REFERENCE PURPOSES ONLY.
            # # Try to find the timeline position of this figure
            # # to find the appropriate camera view
            # try:
            #     time = self.owner.timeof(self)
            # except ValueError:  # self is somehow not in the timeline??
            #     pass  # Just use the layer itself.
            # else:
            #     view = view.viewtime(time)

        if ctx is None:
            try:
                ctx = self.owner.owner.owner
                if ctx is None: raise AttributeError
            except AttributeError:
                raise TypeError("Figure is not owned by an animation. `ctx` cannot be implictly determined.")

        # Handle Layer/Camera/Animation type inputs to
        # view and ctx.
        view = typecastView(view)
        if not isinstance(ctx, cairo.Context):
            ctx = typecastWindowShape(ctx)

        return method(self, view, ctx, *args, **kwargs)
    return wrapper


# Class decorator that adds the standard 2D transformation tweenables
# origin, rotation, and transform, along with implementing
# `transform` as a property so that setting its value auto-converts
# it into an np.array.
#
# Note that this decorator only adds the tweenables and the
# properties THEMSELVES. It does not automatically implement
# drawing or otherwise handling these tweenables.
#
# Also auto-implements the actor actions `wiggle`, `growIn`, and
# `shrinkOut` where applicable.
#
# Optionally, keyword parameters can be passed into the decorator
# as follows:
#   @Transformable2D(...)
#   class MyClass:
#       ...
# with these options:
# exclude = List of names of transformation tweenables to exclude.
#       Valid names are "origin", "rotation", and "transform"
#       (case-sensitive). Can also be inputted as a single string.
# usepos = Boolean if set to True renames the `origin` tweenable to
#       `pos` since some implementations use that name instead.
#       Default: False
def Transformable2D(cls=None, *, exclude=set(), usepos=False):
    # Case where additional arguments are passed in to
    # the decorator
    if cls is None:
        if isinstance(exclude, str):
            exclude = {exclude}
        else:
            exclude = set(exclude)

        def deco(cls):
            newcls = Transformable2D(cls, exclude=exclude, usepos=usepos)
            return newcls
        return deco

    # Name to use for `origin` tweenable
    oname = "origin" if not usepos else "pos"

    # Define new __init__() method
    oldInit = cls.__init__
    def __init__(self, *args, **kwargs):
        oldInit(self, *args, **kwargs)
        # Transformation tweenables
        if "origin" not in exclude:
            self.Tweenable(oname, getattr(self, oname, 0), tags=["complex", "nofimage"])
        if "rotation" not in exclude:
            self.Tweenable("rotation", getattr(self, "rotation", 0), tags=["scalar"])
        if "transform" not in exclude:
            self.Tweenable("_transform", getattr(self, "_transform", np.eye(2)), tags=["nparray"])
    cls.__init__ = __init__

    # Implement wiggle action if `rotation` attribute included.
    if "rotation" not in exclude:
        cls.action(wiggle)

    # Implement special properties for transform
    if "transform" not in exclude:
        def getter(self):
            return self._transform
        def setter(self, value):
            self._transform = morpho.array(value)
        cls.transform = property(getter, setter)

        @cls.action
        def popIn(actor, duration=30, atFrame=None):
            if atFrame is None:
                atFrame = actor.lastID()

            fig0 = actor.last()
            fig1 = actor.newkey(atFrame)
            fig0.visible = False
            fig2 = actor.newendkey(duration).set(visible=True)
            fig1.transform = np.array([[0,0],[0,0]])
        cls.actions["growIn"] = popIn

        @cls.action
        def popOut(actor, duration=30, atFrame=None):
            if atFrame is None:
                atFrame = actor.lastID()

            actor.newkey(atFrame)
            fig1 = actor.newendkey(duration)
            fig1.set(
                transform=np.array([[0,0],[0,0]]), visible=False
                )
        cls.actions["shrinkOut"] = popOut

    return cls


# Abstract base class for figures that are meant to have
# a bounding box (e.g. Image and Text).
# Currently its main function is to automatically implement
# the box direction methods left(), right(), etc. automatically
# based on the particular subclass's implementation of the
# corners() method.
# In the future, this base class may be used to further refactor
# repeated code shared among Image, Text and their subclasses.
class BoundingBoxFigure(morpho.Figure):
    # Needs to be implemented in subclasses
    # Returns the bounding box of the figure in the form
    # [xmin, xmax, ymin, ymax]
    def box(self, *args, **kwargs):
        pass

    # Returns the four physical corners of the figure's
    # bounding box as complex numbers in the order
    # NW, SW, SE, NE.
    # Takes the same parameters as box().
    def corners(self, *args, **kwargs):
        a,b,c,d = self.box(*args, **kwargs)

        NW = a + d*1j
        SW = a + c*1j
        SE = b + c*1j
        NE = b + d*1j

        return [NW,SW,SE,NE]

    # Returns the physical center of the figure's
    # bounding box. Takes the same parameters as box().
    def center(self, *args, **kwargs):
        NW, SW, SE, NE = self.corners(*args, **kwargs)
        return mean([NW, SE])

    # Returns the leftmost position in the middle of the
    # bounding box.
    def left(self, *args, **kwargs):
        NW, SW, SE, NE = self.corners(*args, **kwargs)
        return mean([NW,SW])

    # Returns the rightmost position in the middle of the
    # bounding box.
    def right(self, *args, **kwargs):
        NW, SW, SE, NE = self.corners(*args, **kwargs)
        return mean([NE,SE])

    # Returns the topmost position in the middle of the
    # bounding box.
    def top(self, *args, **kwargs):
        NW, SW, SE, NE = self.corners(*args, **kwargs)
        return mean([NW,NE])

    # Returns the bottommost position in the middle of the
    # bounding box.
    def bottom(self, *args, **kwargs):
        NW, SW, SE, NE = self.corners(*args, **kwargs)
        return mean([SW,SE])

    # Returns the northwest corner of the bounding box.
    def northwest(self, *args, **kwargs):
        NW, SW, SE, NE = self.corners(*args, **kwargs)
        return NW

    # Returns the northeast corner of the bounding box.
    def northeast(self, *args, **kwargs):
        NW, SW, SE, NE = self.corners(*args, **kwargs)
        return NE

    # Returns the southwest corner of the bounding box.
    def southwest(self, *args, **kwargs):
        NW, SW, SE, NE = self.corners(*args, **kwargs)
        return SW

    # Returns the southeast corner of the bounding box.
    def southeast(self, *args, **kwargs):
        NW, SW, SE, NE = self.corners(*args, **kwargs)
        return SE

    @property
    def topleft(self):
        return self.northwest

    @property
    def topright(self):
        return self.northeast

    @property
    def bottomleft(self):
        return self.southwest

    @property
    def bottomright(self):
        return self.southeast

    # Returns the corresponding physical position of an
    # alignment parameter with respect to the bounding box.
    def anchorPoint(self, align, *args, **kwargs):
        anchor_x, anchor_y = align
        left, right, bottom, top = self.box(*args, **kwargs)
        x = morpho.lerp(left, right, anchor_x, start=-1, end=1)
        y = morpho.lerp(bottom, top, anchor_y, start=-1, end=1)
        return complex(x,y)

    # Converts a complex number position into box coordinates
    # where the bounds of the box are -1,1.
    # Essentially the inverse of anchorPoint().
    def boxCoords(self, pos, *args, **kwargs):
        x,y = pos.real, pos.imag
        left, right, bottom, top = self.box(*args, **kwargs)

        anchor_x = morpho.lerp(-1, 1, x, start=left, end=right)
        anchor_y = morpho.lerp(-1, 1, y, start=bottom, end=top)
        return (anchor_x, anchor_y)

    def boxWidth(self, *args, **kwargs):
        box = self.box(*args, **kwargs)
        return box[1] - box[0]

    def boxHeight(self, *args, **kwargs):
        box = self.box(*args, **kwargs)
        return box[-1] - box[-2]

    # Returns both boxWidth and boxHeight as a tuple.
    def boxDimensions(self, *args, **kwargs):
        box = self.box(*args, **kwargs)
        return (box[1] - box[0], box[-1] - box[-2])

    # This is commented out for now because I'm not sure
    # whether aspect ratio should be with respect to the
    # raw box or the true box.
    # # Returns box width / box height.
    # # If box height == 0, returns nan.
    # @property
    # def aspectRatioWH(self):
    #     width, height = self.boxDimensions()
    #     if height == 0:
    #         return nan
    #     return width/height

    # Returns the bounding box of a box that is being subjected
    # to a shift, rotation, and transformation.
    @staticmethod
    def _transformedBox(box, shift=0, rotation=0, transform=np.eye(2), pad=0):
        a,b,c,d = box
        corners = [complex(x,y) for x in [a,b] for y in [c,d]]
        rotator = cmath.exp(rotation*1j)
        mat = morpho.matrix.Mat(transform)

        newcorners = [mat*(rotator*z) + shift for z in corners]
        A = min(z.real for z in newcorners)
        B = max(z.real for z in newcorners)
        C = min(z.imag for z in newcorners)
        D = max(z.imag for z in newcorners)

        return [A-pad, B+pad, C-pad, D+pad]

    # Mainly for use by subclasses that implement box()
    # using relbox(). Computes bounding box using relbox()
    # and the `origin` transformation attribute. Also
    # assumes relbox() possess a `raw` keyword.
    # Currently this is used to implement box() for both
    # the Text class and the Image class.
    def _boxFromRelbox(self, *args, raw=False, **kwargs):
        relbox = self.relbox(*args, raw=raw, **kwargs)
        if raw:
            return relbox
        else:
            a,b,c,d = relbox
            x,y = self._oripos.real, self._oripos.imag
            return [a+x, b+x, c+y, d+y]


# Base class for AlignableFigure.
# Implements some methods related to aligning figures with
# respect to their bounding boxes. Assumes the inheriting
# class has already implemented an `align` property.
#
# To use, the inheriting class must implement an `origin` or `pos`
# attribute, and a box() method capable of accepting the keyword
# parameter `raw=True`.
# Implementing `rotation` and `transform` should be optional.
class PreAlignableFigure(BoundingBoxFigure):

    # Note that many of the methods here accept *args, **kwargs
    # which are (eventually) passed down to the underlying
    # box() method. A big reason for this is to allow non-physical
    # figure types (like Text/MultiText) to use these classes,
    # since their box() methods need additional arguments to
    # function correctly and can't be called empty.

    # Transforms the figure so that the `origin` attribute
    # is in the physical position indicated by the alignment
    # parameter. The figure should be visually unchanged after
    # this transformation.
    def alignOrigin(self, align, *args, **kwargs):
        anchor = self.anchorPoint(align, *args, raw=True, **kwargs)

        self.align = align

        # The usage of default values here is in case the
        # class that inherits this method doesn't have
        # `rotation` and/or `transform` implemented.
        rotation = getattr(self, "rotation", 0)
        transform = getattr(self, "transform", np.eye(2))

        # Now translate the final origin value, which must be
        # subjected to the transformations first.
        rotator = cmath.exp(rotation*1j)
        transformer = morpho.matrix.Mat(transform)
        # Use manual += here in case origin is a np.array.
        self._oripos = self._oripos + transformer*(rotator*anchor)

        return self

    # Moves the `origin` attribute to the specified position
    # without moving the figure itself.
    #
    # Note that this method will throw an error if the
    # figure possesses a `transform` attribute set to a
    # singular matrix.
    def placeOrigin(self, pos, *args, **kwargs):
        # The usage of default values here is in case the
        # class that inherits this method doesn't have
        # `rotation` and/or `transform` implemented.
        rotation = getattr(self, "rotation", 0)
        transform = getattr(self, "transform", np.eye(2))

        try:
            pos = cmath.exp(-rotation*1j) * (morpho.matrix.Mat(transform).inv*(pos-self._oripos))
        except np.linalg.LinAlgError:
            raise ValueError("Figure transform matrix is singular. Cannot place origin.")
        return self.alignOrigin(self.boxCoords(pos, *args, raw=True, **kwargs), *args, **kwargs)

    # Returns the alignment of the figure's origin relative
    # to its bounding box.
    #
    # If the bounding box is degenerate (i.e. width or height is 0),
    # the alignment value for the offending dimension will be set to nan.
    # This can be changed by passing a value into the `invalidValue`
    # optional keyword argument.
    #
    # Optionally, the bounding box may be provided to the function
    # so that it doesn't have to be computed on the fly.
    # If given, this bounding box must be raw except for translation.
    # That is, the box ignores `rotation` and `transform` but not
    # `origin`.
    def boxAlign(self, *args, box=None, invalidValue=nan, **kwargs):
        if box is None:
            box = shiftBox(self.box(*args, raw=True, **kwargs), self._oripos)
        xmin, xmax, ymin, ymax = box
        anchor_x = invalidValue if xmin == xmax else morpho.lerp(-1, 1, self._oripos.real, start=xmin, end=xmax)
        anchor_y = invalidValue if ymin == ymax else morpho.lerp(-1, 1, self._oripos.imag, start=ymin, end=ymax)
        return (anchor_x, anchor_y)

# Mainly to be used as a base class to inherit from.
# When inherited, it implements an implicit `align` property.
#
# To use, the inheriting class must implement an `origin` or `pos`
# attribute, a box() method capable of accepting the keyword
# parameter `raw=True`, and a commitTransforms() method.
# Implementing `rotation` and `transform` should be optional.
class AlignableFigure(PreAlignableFigure):
    # Translates the figure so that the current positional point
    # agrees with the given alignment parameter.
    # Can also be invoked by setting the `align` property:
    #   myfig.align = [-1,1]
    def realign(self, align, *args, **kwargs):
        anchor = self.anchorPoint(align, *args, raw=True, **kwargs)

        # Creating a new one each time just in case
        # commitTransforms() modifies matrices in place.
        I2 = np.eye(2)

        # Store original transformation values.
        # The usage of default values here is in case the
        # class that inherits this method doesn't have
        # `rotation` and/or `transform` implemented.
        origin_orig = self._oripos
        rotation_orig = getattr(self, "rotation", 0)
        transform_orig = getattr(self, "transform", I2)

        # Reset transformations temporarily so we can apply
        # a translation via commitTransforms()
        self._oripos = 0
        # These conditionals are here in case `self` does not
        # implement rotation or transform attributes.
        if rotation_orig != 0: self.rotation = 0
        if transform_orig is not I2: self.transform = I2

        # Use try block to ensure that even if an error is thrown,
        # we reset the transformation values!
        try:
            self._oripos = -anchor
            self.commitTransforms()
        finally:
            # Restore original transformation values
            self._oripos = origin_orig
            if rotation_orig != 0: self.rotation = rotation_orig
            if transform_orig is not I2: self.transform = transform_orig

        return self

    @property
    def align(self):
        return self.boxAlign()

    @align.setter
    def align(self, value):
        self.realign(value)

    def commitTransforms(self):
        # Should be implemented by a subclass.
        pass


# Implements methods that allow the figure to have a background
# box drawn behind it. Mainly meant as a base class to be inherited
# from. To be used correctly, the `box()` method must implement the
# `raw` keyword argument that returns the bounding box without
# transformation attributes applied, and the figure must also possess
# an `origin` attribute (at least implicitly).
class BackgroundBoxFigure(BoundingBoxFigure):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.Tweenable("background", (1,1,1), tags=["color"])
        self.Tweenable("backAlpha", 0, tags=["scalar"])
        self.Tweenable("backPad", 0, tags=["scalar"])

    # Only works for BoundingBoxFigures that have
    # a general `alpha` tweenable, along with a box() method that
    # accepts the `raw` kwarg.
    #
    # Optionally, a kwarg `_alpha` can be passed in which
    # will bypass accessing the top-level `alpha` attribute
    # of self.
    def _drawBackgroundBox(self, camera, ctx,
            origin=None, rotation=None, transform=None, *args,
            _alpha=None, **kwargs):

        if self.backAlpha <= 0:
            # No need to attempt to draw invisible background box
            return

        # Infer transformation attributes if not specified.
        if origin is None:
            origin = self._oripos
        if rotation is None:
            rotation = getattr(self, "rotation", 0)
        if transform is None:
            transform = getattr(self, "transform", I2)
        if _alpha is None:
            _alpha = getattr(self, "alpha", 1)
            # alpha = self.alpha if _alpha is None else _alpha

        # Draw background box
        brect = morpho.grid.rect(padbox(self.box(*args, raw=True, **kwargs), self.backPad))
        brect.set(
            origin=origin, rotation=rotation,
            _transform=transform,
            width=0, fill=self.background, alpha=self.backAlpha*_alpha
            )
        brect.draw(camera, ctx)


# Mainly for internal use by the Frame class (and its derivatives)
# for implementing the `all`, `select`, `sub`, and `cut` features.
# Allows one to modify the attributes of a collection of objects
# all at once.
class _SubAttributeManager(object):
    # `objects` is the sequence of objects whose attributes are
    # getting accessed/modified en masse.
    # `origCaller` is the original object that should be returned by
    # the set() method (usually a Frame object).
    def __init__(self, objects, origCaller, /):
        # Bypass native setattr() because it's overridden below.
        object.__setattr__(self, "_subattrman_objects", objects)
        object.__setattr__(self, "_subattrman_origCaller", origCaller)

    # Returns a function that when called will call the
    # corresponding method across all subfigures in the
    # Frame and collect their return values into a list
    # which will then be returned.
    def _subattrman_createSubmethod(self, name):
        def submethod(*args, **kwargs):
            outputs = []
            for obj in self._subattrman_objects:
                outputs.append(getattr(obj, name)(*args, **kwargs))
            return outputs
        return submethod

    def __getattr__(self, name):
        objects = self._subattrman_objects

        # Extract initial value for the attribute (if possible)
        try:
            commonValue = getattr(objects[0], name)
        except AttributeError:
            raise AttributeError(f"Objects do not all possess attribute `{name}`")
        except IndexError:
            raise IndexError("No objects to find attributes for.")

        commonValue_is_list_or_tuple = isinstance(commonValue, (list, tuple))

        # Check if the attribute is common to all the
        # objects and having the same value
        for obj in objects:
            try:
                value = getattr(obj, name)
            except AttributeError:
                raise AttributeError(f"Objects do not all possess attribute `{name}`")

            if commonValue_is_list_or_tuple and isinstance(value, (list, tuple)):
                # Convert value to commonValue's type so that cross-container
                # comparison with commonValue will work
                value = type(commonValue)(value)
            # Check if they are unequal
            if not isequal(value, commonValue):  # isequal() handles np.arrays too
                if callable(commonValue):
                    return self._subattrman_createSubmethod(name)
                raise AmbiguousValueError(f"Objects do not have a common value for attribute `{name}`")

        return commonValue if not isinstance(commonValue, (list, np.ndarray)) else commonValue.copy()

    def __setattr__(self, name, value):
        # Handle ordinary attribute sets if self possesses
        # the attribute.
        if object_hasattr(self, name):
            object.__setattr__(self, name, value)

        # Set every attribute of the given objects
        objects = self._subattrman_objects
        for obj in objects:
            setattr(obj, name, value)

    def set(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)
        return self._subattrman_origCaller


class _MetaArray(np.ndarray):
    """Array with metadata.
    Thanks to @Bertrand L on StackOverflow for this!
    https://stackoverflow.com/a/34967782"""

    def __new__(cls, array, dtype=None, order=None, **kwargs):
        obj = np.asarray(array, dtype=dtype, order=order).view(cls)
        obj.metadata = kwargs
        return obj

    def __array_finalize__(self, obj):
        if obj is None: return
        self.metadata = getattr(obj, 'metadata', None)

# Special version of _SubAttributeManager which in the case of an
# AmbiguousValueError, returns a MetaArray of the values across all
# subfigures. Mainly used for enabling the .iall and .iselect
# features for subfigure in-place operations.
class _InPlaceSubAttributeManager(_SubAttributeManager):
    def __getattr__(self, name):
        try:
            return _SubAttributeManager.__getattr__(self, name)
        except AmbiguousValueError:
            # A MetaArray is used in order to distinguish these object arrays
            # from regular numpy object arrays just in case a user is trying
            # to update a value that is already natively an object array.
            return _MetaArray([getattr(obj, name) for obj in self._subattrman_objects], dtype=object)

    def __setattr__(self, name, value):
        if isinstance(value, _MetaArray):
            for obj, subvalue in zip(self._subattrman_objects, value.tolist()):
                setattr(obj, name, subvalue)
        else:
            _SubAttributeManager.__setattr__(self, name, value)

# Draw a figure whose start or end attribute is outside the interval
# [0,1] according to the cyclic rules.
def drawOutOfBoundsStartEnd(fig, camera, ctx):
    diff = fig.end - fig.start
    if diff <= 0:
        return

    # Store original start and end values so that
    # start and end can be temporarily changed if needed.
    start_orig = fig.start
    end_orig = fig.end
    if diff >= 1:
        # Draw the entire path by temporarily setting
        # start=0 and end=1 and redrawing
        fig.start = 0
        fig.end = 1
        fig.draw(camera, ctx)
        fig.start = start_orig
        fig.end = end_orig
        return

    # Calculate local versions of start and end relative
    # to the interval [0,1]
    start_local = fig.start - math.floor(fig.start)
    # end_local is 1 if end is an integer
    end_local = fig.end - (math.ceil(fig.end)-1)
    if start_local > end_local:
        # Draw a two-segment path

        # Save head and tail sizes
        headSize_orig = fig.headSize
        tailSize_orig = fig.tailSize

        # Draw first path component
        fig.start = 0
        fig.end = end_local
        fig.tailSize = 0
        fig.draw(camera, ctx)
        fig.tailSize = tailSize_orig

        # Draw second path component
        fig.start = start_local
        fig.end = 1
        fig.headSize = 0
        fig.draw(camera, ctx)
        fig.headSize = headSize_orig

        # Restore original values
        fig.start = start_orig
        fig.end = end_orig
    else:
        fig.start = start_local
        fig.end = end_local
        fig.draw(camera, ctx)
        fig.start = start_orig
        fig.end = end_orig

# Mainly for use by the select[] feature of Frames/MultiFigures.
# Packages the methods for getting, setting, and deleting
# slices of indices into an object whereby the python bracket
# syntax works.
class Slicer(object):
    def __init__(self, getter=None, setter=None, deller=None):
        self.getter = getter
        self.setter = setter
        self.deller = deller

    def __getitem__(self, index):
        return self.getter(index)

    def __setitem__(self, index, value):
        self.setter(index, value)

    def __delitem__(self, index):
        self.deller(index)


def translateArrayUnderTransforms(array, shift, rotator, transformer):
    try:
        array += (transformer.inv*shift)/rotator
    except np.linalg.LinAlgError:
        raise ValueError("transform is singular.")
    return array

# Duplicates specific items in a list as uniformly as possible.
# Given a list, a sorted list (`slots`) of indices, and the number
# of duplicates to create, the function inserts duplicates of the
# items identified by `slots` in the same position in the list as
# the original items. For example,
#   makesubcopies([10,20,30,40,50], [0,2,3], 5)
# produces [10,10,10, 20, 30,30,30, 40,40, 50]
#
# Optionally, an additional function `itemfunc` can be supplied
# which is applied to each original list item and its return value
# is inserted as a duplicate back into the list. For example,
# supplying `lambda item: item.copy()` will cause each item
# to have its `copy()` method called before being inserted into
# the list as a duplicate, in order to produce a deep copy
# of the duplicated item.
def makesubcopies(lst, slots, number, itemfunc=lambda item: item):
    copiesPerSlot, remainder = divmod(number, len(slots))
    for i, index in enumerate(reversed(slots)):
        item = lst[index]
        i = len(slots) - 1 - i
        for n in range(copiesPerSlot+int(i < remainder)):
            lst.insert(index, itemfunc(item))
    return lst
