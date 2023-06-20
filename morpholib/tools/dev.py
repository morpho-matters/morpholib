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

import numpy as np
import math, cmath
from collections.abc import Iterable

### SPECIAL EXCEPTIONS ###

# Exception that should be thrown if a dynamically
# computed value cannot be given a single definite
# value. For example, trying to get the attribute
# `tipSize` for a Path whose headSize and tailSize
# differ.
class AmbiguousValueError(ValueError):
    pass


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
        if isinstance(view, morpho.Layer):
            view = view.camera.last().view
        elif isinstance(view, morpho.Actor):
            view = view.last().view
        elif isinstance(view, morpho.anim.Camera):
            view = view.view
        if isinstance(ctx, morpho.Animation):
            ctx = ctx.windowShape

        return method(self, view, ctx, *args, **kwargs)
    return wrapper

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

    # Only works for BoundingBoxFigures that have
    # background box tweenables `background`,
    # `backAlpha`, and `backPad` defined and the general
    # `alpha` tweenable, along with a box() method that
    # accepts the `raw` kwarg.
    #
    # Optionally, a kwarg `_alpha` can be passed in which
    # will bypass accessing the top-level `alpha` attribute
    # of self.
    def _drawBackgroundBox(self, camera, ctx, origin=0, rotation=0, transform=np.eye(2), *,
        _alpha=None):
        if self.backAlpha > 0:
            alpha = self.alpha if _alpha is None else _alpha
            # Draw background box
            brect = morpho.grid.rect(padbox(self.box(raw=True), self.backPad))
            brect.set(
                origin=origin, rotation=rotation,
                _transform=transform,
                width=0, fill=self.background, alpha=self.backAlpha*alpha
                )
            brect.draw(camera, ctx)

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

class Slicer(object):
    def __init__(self, getter=None, setter=None):
        self.getter = getter
        self.setter = setter

    def __getitem__(self, index):
        return self.getter(index)

    def __setitem__(self, index, value):
        self.setter(index, value)


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
# Optionally, an additional argument `itemfunc` can be supplied
# which is applied to the original list item before it is
# inserted as a duplicate back into the list. For example,
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
