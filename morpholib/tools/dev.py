'''
This submodule is mainly for internal use by the
classes/functions of Morpho and probably should not
be used by the regular end-user.

An assortment of useful functions and classes.
'''

import morpholib as morpho
import morpholib.anim
from morpholib.tools.basics import *

import numpy as np
import math, cmath

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
