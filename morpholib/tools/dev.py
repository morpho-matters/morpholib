'''
This submodule is mainly for internal use by the
classes/functions of Morpho and probably should not
be used by the regular end-user.
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
def typecastViewCtx(method):
    def wrapper(self, view, ctx, *args, **kwargs):
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
