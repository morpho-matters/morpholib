'''
Contains the basic classes necessary for animation
including the Frame and Animation classes.
'''

import pyglet, PIL
pg = pyglet
import cairo
cr = cairo

import morpholib as morpho
import morpholib.transitions, morpholib.giffer
from morpholib.tools.basics import *
from morpholib.tools.ktimer import tic, toc

# Backward compatibility because these functions used to live in anim.py
from morpholib import screenCoords, physicalCoords, \
    pixelWidth, physicalWidth, pixelHeight, physicalHeight, \
    setupContext, clearContext, cairoJointStyle

import math, cmath
import numpy as np
import os, shutil, tempfile, ctypes
import subprocess as sp
import pyperclip
from warnings import warn

# # Get location of the Morpho directory.
# # pwd = os.sep.join(sys.argv[0].split(os.sep)[:-1])
# pwd = os.sep.join(os.path.dirname(os.path.abspath(__file__)).split(os.sep)[:-1])
# if os.sep not in pwd:
#     pwd = os.curdir
# # pwd += os.sep

# Get temp directory
tempdir = tempfile.gettempdir()

# Export signature is a string appended to the name
# of the temporary directory "Morpho-export" that is created
# whenever an MP4 of GIF animation is exported. Useful
# for doing parallel exports.
exportSignature = ""

### FFMPEG CONFIG ###

# Command to use to call the ffmpeg executable
ffmpeg = "ffmpeg"
# ffmpeg = pwd+os.sep+"morpho"+os.sep+"ffmpeg"+os.sep+"bin"+os.sep+"ffmpeg.exe"

# Dictionary containing some ffmpeg configuration parameters.
# For now, it only contains "crf", which gives some control of the quality
# of the final mp4. Default: crf = 23.
ffmpegConfig = {
    "crf" : 23  # Sensible range = [18, 28]; lower <=> better quality
}


### SPECIAL EXCEPTIONS ###

class FrameSaveError(Exception):
    pass

class MergeError(Exception):
    pass

class LayerMergeError(MergeError):
    pass

class MaskConfigurationError(Exception):
    pass

### CLASSES ###


# Frame class. Groups figures together for simultaneous drawing.
# Syntax: myframe = Frame(list_of_figures)
#
# TWEENABLES
# figures = List of figures in the frame. For tweening to work,
#           the figures list of both Frames must have corresponding
#           figure types. e.g. Frame([point, path]) can only tween with
#           another Frame([point, path]).
#
# Note that tweening a frame via tween() will tween the frame's
# attributes along with its underlying figure list, but calling
# a frame's tween method directly (via defaultTween) will only tween
# the frame's attributes and NOT the underlying figure list.
#
# Also note that the transition function supplied to a frame will NOT
# propagate down to the figures in the figures list. When tweening a frame,
# the individual transition functions of each figure are used.
class Frame(morpho.Figure):
    def __init__(self, figures=None):
        # By default, do what the superclass does.
        morpho.Figure.__init__(self)

        if figures is None: figures = []
        figures = morpho.Tweenable(
            name="figures", tags=["figures", "notween"], value=figures)
        # background = morpho.Tweenable(
        #     name="background", tags=["vector"], value=[0,0,0])
        # view = morpho.Tweenable(
        #     name="view", tags=["view"], value=[-5,5, -5,5])

        # Attach tweenable attributes
        self.update([figures])

        # Position of the frame in an animation's timeline.
        # It is in units of "frames" where 0 is the first frame, etc.
        # self.index = index

        # How many frames should the frame persist in an animation
        # if the frame is the final keyframe in a layer.
        # If set to oo (infinity), then the final frame will
        # never disappear in an animation.
        # Maybe in the future delay will also play a role for
        # intermediate keyframes, but for now, it's
        # only taken into account if it's the final keyframe.
        # self.delay = 0

        # # Other (non-tweenable) attributes
        # self.delay = 0  # number of frames to delay at keyframe

        # self.defaultTween = Frame.tweenLinear

    # # Returns True iff the "stylistic" attributes of two frames match
    # # i.e. their views, indices, and defaultTweens match.
    # # This can be used as a criterion on whether or not merging two frames
    # # can be done without affecting the other frame.
    # def matchesStyle(self, other):
    #     return self.defaultTween==other.defaultTween

    # Append the figure list of other to self in place.
    def merge(self, other):
        self.figures.extend(other.figures)

    # Draw all visible figures in the figure list.
    def draw(self, camera, ctx, *args, **kwargs):
        figlist = sorted(self.figures, key=lambda fig: fig.zdepth)

        for fig in figlist:
            if fig.visible:
                fig.draw(camera, ctx, *args, **kwargs)

    # Copies the frame. Supplying False to the optional arg "deep"
    # means the resulting frame copy will not make copies of the
    # figures in the figure list
    # (the python list object ITSELF will be copied, though)
    # The main time you'd use deep=False is to conserve memory if, say,
    # you have an animation containing many copies of the same frame,
    # and that frame has a lot of big figures (like hi-res paths).
    def copy(self, deep=True):
        # Copy the tweenables, default tween method and transition.
        new = morpho.Figure.copy(self)
        # new = super().copy()

        # Make copies of all the underlying figures.
        if deep:
            for i in range(len(new.figures)):
                new.figures[i] = new.figures[i].copy()
        return new

    # Perform an fimage on all non-static figures that possess
    # a method with the name "fimage".
    # Returns a new frame object that is the result.
    def fimage(self, func):
        S = self
        f = func
        fS = S.copy()
        for i in range(len(fS.figures)):
            fig = fS.figures[i]
            if not fig.static:
                fS.figures[i] = fig.fimage(func)
        return fS

    # Use the default tween method and transition to tween the frame.
    # Also auto-tweens all of the figures in the figure list.
    # Frame transition should only affect frame-specific tweenables.
    # It should not transfer down to the figures it contains.
    # Also note that tween() assumes the figure lists between
    # self and other are compatible i.e. of the same lengths AND
    # item-by-item having the same figure types. Trying to tween
    # figures of different types may result in a crash or
    # unpredictable behavior. So if you have two keyframes in an
    # animation that are one after the other in the same layer,
    # you should set the first keyframe to be static so that it
    # doesn't tween.
    def tween(self, other, t):
        frm = self.defaultTween(self, other, self.transition(t))

        # Now do stuff with the figures tweenable
        # Tween each figure according to its default tween method.
        for i in range(len(self.figures)):
            fig = self.figures[i]
            # Don't tween if the figure is static
            if fig.static: continue

            pig = other.figures[i]
            twig = fig.tween(pig, t)
            frm.figures[i] = twig
        return frm

# Blank frame used by the Animation class.
blankFrame = Frame()
blankFrame.static = True


# Base class for so-called "multifigures" which allow for groupings
# of figures all of the same class that can be tweened even if one group
# has a different number of member figures than the other.
# One of the main uses of this class is to
# implement the MultiImage and MultiText classes which allow for a
# primitive morphing between images and text via mutual opposite fading.
class MultiFigure(Frame):

    def __init__(self, *args, **kwargs):
        # Set the "_active" attribute to False using
        # object's setattr() method explicitly because
        # this class's setattr() is overridden and expects
        # the attribute "_active" to exist. When "_active" is
        # set to False, it doesn't do anything fancy and just
        # uses the default Figure's setattr() call.
        # When "_active" is True, it does some checks to see if
        # it should instead be setting the first member's attribute
        # or not.
        # The main purpose of _active is to disable the modified
        # setattr() during the construction phase, but then enable
        # its behavior once construction is finished.
        object.__setattr__(self, "_active", False)

        # Construct the figure.
        super().__init__(*args, **kwargs)

        # Construction is finished, so you can now enable the
        # modified setattr() method.
        self._active = True

    # Returns a StateStruct encapsulating all the tweenables
    # of all the figures in the MultiFigure.
    # Main example use case:
    # my_multifig.all().alpha = 0 changes all the subfigures'
    # alpha attribute to 0.
    # By default, the tweenables encapsulated are all the
    # tweenables contained in the zeroth figure in the list,
    # but this can be overridden, as well as exactly what figures
    # should be encapsulated.
    def all(self, tweenableNames=None, figures=None):
        raise NotImplementedError
        if len(self.figures) == 0:
            raise IndexError("Multifigure has no subfigures.")

        if tweenableNames is None:
            tweenableNames = list(self.figures[0]._state)
        if figures is None:
            figures = self.figures

        return StateStruct(tweenableNames, figures)


    # If attempted to access a non-existent attribute,
    # check if it's an attribute of the first figure in
    # the figure list and return that instead.
    def __getattr__(self, name):
        # First try using the superclass's built-in getattr()
        # which should grab any valid attribute returns in the
        # main class.
        try:
            return super().__getattr__(name)
        except AttributeError:
            pass

        # If you got to this point in the code, it means the
        # superclass's getattr() failed.

        # If figure list is empty, there's nothing more we can do, so
        # attempt to call the superclass's getattr() again, and this
        # time actually throw the error!
        if len(self.figures) == 0:
            # This line is guaranteed to fail because it failed
            # in the protected clause above. However, this time
            # I WANT the error to be thrown!
            return super().__getattr__(name)

        # Try to find the attribute in the first member figure
        # and if found, return it.
        fig = self.figures[0]
        try:
            # return fig.__getattribute__(name)
            return getattr(fig, name)
        # This attribute is nowhere to be found anywhere. So give up.
        except AttributeError:
            # raise AttributeError("First member figure of type '"+type(fig)+"'' does not have attribute '"+name+"'")
            raise AttributeError("Could not find attribute '"+name+"' in either the main class or the first member figure!")

    # Modified setattr() first checks if the requested attribute already
    # exists as a findable attribute in the main class. If it is, it just
    # sets it as normal. Otherwise it checks if the attribute exists in
    # the first member figure. If it does, it sets it instead of the
    # main class. But if it can't find this attribute in the first member
    # figure either, it will just assign the attribute as a new attribute
    # of the main class.
    def __setattr__(self, name, value):
        # Set the attribute as normal if the MultiFigure is not active yet, or
        # it's a concrete attribute of the main class,
        # or it's a tweenable in the main class.
        if not self._active or name in dir(self) or name in self._state.keys():
            # super().__setattr__(name, value)
            morpho.Figure.__setattr__(self, name, value)
        # If this attribute is NOT an already existent attribute of
        # the main class, check if it's an attribute of the first
        # member figure. If it is, set THAT.
        elif len(self.figures) != 0:
            fig = self.figures[0]
            try:
                # See if it already exists as an attribute
                # of the first member figure.
                # fig.__getattribute__(name)
                getattr(fig, name)

                # If you got here, we didn't get an attribute error,
                # so it should be a real attribute! Go ahead and set it!
                fig.__setattr__(name, value)

            # Got an attribute error, so the given attribute isn't
            # even in the first member figure. Therefore, just assign it
            # as a regular (but new) attribute of the main class.
            except AttributeError:
                # super().__setattr__(name, value)
                morpho.Figure.__setattr__(self, name, value)


    # This is needed because inherited tween() is Frame.tween()
    # which is a modified version of default Figure.tween()
    tween = morpho.Figure.tween

Multifigure = MultiFigure


# Class encapsulates all the tweenables of a list of figures of common
# type so that you can easily modify a single tweenable across all the
# figures in a single line of code.
# Mainly for internal use in the MultiFigure class and its derivatives.
class StateStruct(object):
    def __init__(self, tweenableNames, figures):
        raise NotImplementedError

        object.__setattr__(self, "_state", [tweenableNames, figures])

    # THE BELOW COMMENTED OUT BLOCKS ARE POTENTIALLY REALLY BAD IDEAS...
    # def __copy__(self):
    #     names, figures = self._state
    #     return type(self)(names[:], figures[:])

    # def __ioper__(self, value, optype):
    #     names, figures = self._state

    #     for fig in figures:
    #         for name in names:
    #             currentValue = getattr(fig, name)

    #             oper = getattr(type(currentValue), optype)
    #             setattr(fig, name, oper(currentValue, value))

    # def __add__(self, value):
    #     result = self.__copy__()
    #     names, figures = result._state

    #     for fig in figures:
    #         for name in names:
    #             currentValue = getattr(fig, name)
    #             setattr(fig, name, currentValue + value)

    #     return result

    # def __getattr__(self, name):
    #     names, figures = self._state

    #     if name not in names:
    #         raise AttributeError(f"Attribute '{name}' could not be found.")

    #     return type(self)([name], figures)

    # Modified setattr() first checks if the attribute is a native
    # attribute of StateStruct, and if so, handles it normally.
    # Else, it checks if the attribute is one of the special
    # attributes it's supposed to manage for its figure list.
    # If it is, it modifies that attribute across all figures
    # in the figure list.
    def __setattr__(self, name, value):

        # Extract the tweenable names and figure list from
        # the _state attribute
        names, figures = self._state

        if name in dir(self):
            object.__setattr__(self, name, value)
        elif name in names:
            for fig in figures:
                setattr(fig, name, value)
        else:
            # Guaranteed to throw an error, which is what I want to happen.
            object.__setattr__(self, name, value)



# 3D version of Frame which supports the primitives() method.
# This version should usually be used when making Frames containing
# space figures. However, there could be exceptions. See below.
#
# NOTE: Even if you intend to make a frame consisting of space figures,
# you shouldn't use SpaceFrame unless ALL the figures in the figure list
# support a primitives() method. This is because
# the default primitives() method of SpaceFrame assumes each figure
# it contains supports its own primitives() method.
# If you want to include figures that lack a primitives()
# method, you should just use an ordinary Frame instead.
# However, most space figures support primitives(), so you probably
# don't need to worry about this.
class SpaceFrame(Frame):
    def __init__(self, figures=None):
        if isinstance(figures, Frame):
            super().__init__(figures.figures)
        else:
            super().__init__(figures)

    # Only for frames consisting only of space figures
    # (i.e. figures possessing a primitives() method and a 5 input
    # draw() method)
    #
    # Calls the primitives() method on all figures and merges all of
    # the lists into one big list of primitives and returns it.
    def primitives(self, camera): # orient=np.identity(3), focus=np.array([0,0,0], dtype=float)):
        primlist = []
        for fig in self.figures:
            primlist.extend(fig.primitives(camera))

        return primlist

# 3D version of the MultiFigure class. See "MultiFigure" for more info.
class SpaceMultiFigure(SpaceFrame):
    def __getattr__(self, name):
        return MultiFigure.__getattr__(self, name)

SpaceMultifigure = Spacemultifigure = SpaceMultiFigure


# Generates frame objects according to a time parameter.
# Useful because it allows you to avoid making a long
# sequence of keyframes, saving both computer memory
# and programming complexity.
#
# It is not designed to be a standalone figure, but
# a base class for other figures.
#
# The idea is a Skit subclass object has a tweenable time parameter t
# and a makeFrame() method which generates a frame object
# according to the time parameter. When draw() is called,
# a frame is generated according to makeFrame() and then drawn.
#
# Example usage:
# class Pendulum(morpho.Skit):
#     def makeFrame(self):
#         ... code to generate desired frame based on self.t value ...
#         return my_generated_frame
#
# pendulum = morpho.Actor(Pendulum())
# pendulum.newkey(90).t = final_t_value
class Skit(morpho.Figure):

    def __init__(self, *, t=0):
        super().__init__()

        t = morpho.Tweenable("t", t, tags=["scalar"])

        self.update([t])

    # Return a frame figure based on the t-value of the skit.
    # Generic skit just returns an empty frame.
    # Subclasses of Skit should define it however is necessary.
    # Although a skit is usually expected to return a frame figure
    # when makeFrame() is called, it should still work for any
    # figure, even for variable figure types.
    def makeFrame(self):
        return Frame()

    # Generate the frame and draw it.
    def draw(self, camera, ctx, *args, **kwargs):
        self.makeFrame().draw(camera, ctx, *args, **kwargs)


# 3D version of the Skit class which supports the primitives() method.
# This version should usually be used when making skits involving
# space figures. However, there could be exceptions. See below.
#
# NOTE: Even if you intend to make a skit involving space figures,
# you shouldn't use SpaceSkit unless the figure returned by the
# makeFrame() method supports primitives(). This is because
# the default primitives() method of SpaceSkit assumes makeFrame()
# returns a space figure supporting its own primitives() method.
# If the figure makeFigure() returns does not possess a primitives()
# method, you should just use an ordinary Skit instead.
# However, most space figures support primitives(), so you probably
# don't need to worry about this.
class SpaceSkit(Skit):

    def makeFrame(self):
        return SpaceFrame()

    # Only for use when the skit returns a space figure
    # possessing a primitives() method.
    def primitives(self, camera): # orient=np.identity(3), focus=np.array([0,0,0], dtype=float)):
        return self.makeFrame().primitives(camera)


# This is a decorator-maker that lets you change the skit parameter
# to something other than the default "t". It can also be used to
# make a multi-parameter skit.
#
# Usage:
# @morpho.SkitParameters(["x", "y", "z"])
# class Pendulum(morpho.Skit):
#     etc...
#
# By default the new parameters will have default values of 0,
# but you can optionally supply alternative default values like this:
# @morpho.SkitParameters(x=1, y=2, z=3)
# class Pendulum(morpho.Skit):
#     etc...
def SkitParameters(params=None, /, **kwargs):
    # assert isinstance(params, list) or isinstance(params, tuple) or isinstance(params, dict)

    if params is None:
        params = {}
    # Convert params to default dict if params is not a dict.
    elif not isinstance(params, dict):
        D = {}
        for varname in params:
            D[varname] = 0
        params = D

    # Check for duplicates in the params and kwargs dicts
    paramSet = set(params.keys())
    kwargSet = set(kwargs.keys())
    if not paramSet.isdisjoint(kwargSet):
        raise TypeError(f"Multiple values supplied for parameter(s) {paramSet.intersection(kwargSet)}")

    # Pool together params with kwargs
    params.update(kwargs)
    paramSet = set(params.keys())

    # Check it's not empty
    if len(params) == 0:
        raise TypeError("No parameters supplied.")

    def decorator(subSkit):
        def newInit(self, **kwargs):
            super(subSkit, self).__init__()

            # Check if any keyword arguments were given that are not
            # valid parameters
            kwSet = set(kwargs.keys())
            if not kwSet.issubset(paramSet):
                raise TypeError(f"Unexpected keyword argument(s): {kwSet-paramSet}")

            state = []
            for varname in params:
                if varname in kwargs:
                    tweenable = morpho.Tweenable(varname, kwargs[varname], tags=["scalar"])
                else:
                    tweenable = morpho.Tweenable(varname, params[varname], tags=["scalar"])
                state.append(tweenable)
            self.update(state)

        subSkit.__init__ = newInit
        return subSkit

    return decorator


# Non-drawable figure whose purpose is to record information about the current
# view of the complex plane that the Layer class should use to draw its actors.
#
# TWEENABLES
# view = Viewbox of the complex plane ([xmin,xmax,ymin,ymax]).
#        Default: [-5,5, -5,5]
class Camera(morpho.Figure):
    def __init__(self, view=None):
        if view is None:
            view = [-5,5, -5,5]

        morpho.Figure.__init__(self)

        view = morpho.Tweenable("view", view, tags=["view", "scalar", "list"])

        self.update([view])

        self.defaultTween = type(self).tweenZoom

    # Zoom out the camera IN PLACE by the specified factor.
    # Optionally specify a complex number as the "focus", meaning
    # that point will remain at the same pixel after the zoom.
    # Defaults to the center of the viewbox.
    # Returns the camera figure it just acted on (self).
    def zoomOut(self, scale, focus=None):
        if scale <= 0:
            raise ValueError("Zoom factor must be positive.")

        a,b,c,d = self.view
        if focus is None:
            focus = (a+b)/2 + (c+d)/2*1j

        A = scale*(a - focus.real) + focus.real
        B = scale*(b - focus.real) + focus.real
        C = scale*(c - focus.imag) + focus.imag
        D = scale*(d - focus.imag) + focus.imag
        self.view = [A,B,C,D]

        return self

    # Equivalent to self.zoomOut(1/factor, focus)
    # See zoomOut() for more info.
    def zoomIn(self, scale, focus=None):
        if scale <= 0:
            raise ValueError("Zoom factor must be positive.")

        return self.zoomOut(1/scale, focus)

    # Reposition the camera IN PLACE to be centered at the given complex number.
    # Returns self afterward.
    def centerAt(self, z):
        x,y = z.real, z.imag
        a,b,c,d = self.view
        semiwidth = (b - a)/2
        semiheight = (d - c)/2

        self.view = [x-semiwidth, x+semiwidth, y-semiheight, y+semiheight]

        return self

    # Shift the camera IN PLACE by the specified complex number.
    # Returns self afterward.
    def moveBy(self, z):
        x,y = z.real, z.imag
        a,b,c,d = self.view
        self.view = [a+x, b+x, c+y, d+y]

        return self

    # Rescales the width of the viewbox to make it match
    # the given aspect ratio.
    # Syntax: mycamera.rescaleWidth(aspectRatioWH)
    def rescaleWidth(self, aspectRatioWH):
        xmin, xmax, ymin, ymax = self.view
        xmid = mean([xmin, xmax])

        radius = (ymax-ymin)*aspectRatioWH/2
        xmin = xmid - radius
        xmax = xmid + radius

        self.view = [xmin, xmax, ymin, ymax]
        return self

    # Rescales the height of the viewbox to make it match
    # the given aspect ratio.
    # Syntax: mycamera.rescaleHeight(aspectRatioWH)
    def rescaleHeight(self, aspectRatioWH):
        xmin, xmax, ymin, ymax = self.view
        ymid = mean([ymin, ymax])

        radius = (xmax-xmin)/(2*aspectRatioWH)
        ymin = ymid - radius
        ymax = ymid + radius

        self.view = [xmin, xmax, ymin, ymax]
        return self

    # Modifies the view so that the current view will correspond
    # to the area of the window currently covered by the given box.
    # This can be useful for setting up a mini animation inside
    # a larger animation.
    def toSubview(self, box):
        a1, b1, c1, d1 = box
        a,b,c,d = self.view

        # Compute new a and b, called alpha, beta
        width1 = b1 - a1
        alpha = (a*b1 + (a-a1)*b - a**2) / width1
        beta = (a*b1 + b**2 - (a+a1)*b) / width1

        # Compute new c and d, called gamma, delta
        height1 = d1 - c1
        gamma = (c*d1 + (c-c1)*d - c**2) / height1
        delta = (c*d1 + d**2 - (c+c1)*d) / height1

        self.view = [alpha, beta, gamma, delta]


    # Returns width of the viewbox: view[1] - view[0]
    def width(self):
        return self.view[1] - self.view[0]

    # Returns height of the viewbox: view[3] - view[2]
    def height(self):
        return self.view[3] - self.view[2]

    # Returns the center of the view box as a complex number.
    def center(self):
        a,b,c,d = self.view
        return ((a+b) + 1j*(c+d)) / 2

    # Given a complex number "pos" representing a position, this method returns
    # a new complex number corresponding to this position had the camera's
    # view been the unit square [0,1] x [0,1].
    # In other words, returns the RELATIVE coordinates of a position with
    # respect to the this camera's viewbox.
    #
    # Usually used in conjunction with physicalCoords()
    def normalizedCoords(self, pos):
        a,b,c,d = self.view
        width = b - a
        height = d - c

        x,y = pos.real, pos.imag

        # Compute normalized coordinates
        X = (x-a)/width
        Y = (y-c)/height

        return X + 1j*Y


    # Given a position described in normalized coordinates for this camera's
    # viewbox, this method returns the physical position it corresponds to in
    # that viewbox window.
    # In other words, returns the TRUE coordinates of a position given RELATIVE
    # position coordinates to the camera's viewbox.
    #
    # Usually used in conjunction with normalizedCoords()
    def physicalCoords(self, pos):
        a,b,c,d = self.view
        width = b - a
        height = d - c

        X,Y = pos.real, pos.imag

        # Compute physical coordinates
        x = X*width + a
        y = Y*height + c

        return x + 1j*y

    # Given a physical width, returns the corresponding width in the
    # normalized coordinate system.
    # See normalizeCoords() for more info.
    def normalizedWidth(self, width):
        a,b,c,d = self.view
        return width / (b-a)

    # Given a physical height, returns the corresponding height in the
    # normalized coordinate system.
    # See normalizeCoords() for more info.
    def normalizedHeight(self, height):
        a,b,c,d = self.view
        return height / (d-c)

    # Given a normalized width, returns the corresponding width in the
    # physical coordinate system.
    # See physicalCoords() for more info.
    def physicalWidth(self, width):
        a,b,c,d = self.view
        return width*(b-a)

    # Given a normalized height, returns the corresponding height in the
    # physical coordinate system.
    # See physicalCoords() for more info.
    def physicalHeight(self, height):
        a,b,c,d = self.view
        return height*(d-c)

    # NOT IMPLEMENTED YET!
    # Converts a box [xmin,xmax,ymin,ymax] in physical coordinates
    # into the equivalent box in normalized coordinates.
    # See normalizedCoords() for more info.
    def normalizedBox(self, box):
        raise NotImplementedError

    # NOT IMPLEMENTED YET!
    # Converts a box [xmin,xmax,ymin,ymax] in normalized coordinates
    # into the equivalent box in physical coordinates.
    # See physicalCoords() for more info.
    def physicalBox(self, box):
        raise NotImplementedError


    ### TWEEN METHODS ###

    # Primary tween method for the Camera class. Zooms in an exponential fashion
    # as opposed to a linear fashion.
    # That is, it linearly tweens the zoom level in LOG space.
    # It's usually better than tweenLinear(), because if you zoom the camera
    # over several orders of magnitude, it goes thru them at a uniform speed.
    @morpho.TweenMethod
    def tweenZoom(self, other, t):
        tw = self.copy()
        if self.view == other.view:
            return tw

        # Do a special zoom tween for the view
        # Do both horz and vert
        for j in range(0, 3, 2):
            i0 = j
            i1 = j+1

            # Interval endpoints
            a0, b0 = self.view[i0], self.view[i1]
            a1, b1 = other.view[i0], other.view[i1]

            # Interval diameters
            d0 = b0 - a0
            d1 = b1 - a1

            # If the interval was basically only translated, just do a
            # linear tween. Otherwise, do a zoom tween
            if abs(d0/d1 - 1) < 1.0e-6:
                a = (a1-a0)*t + a0
                b = (b1-b0)*t + b0
            else:
                sigma = (b1-a1)/(b0-a0)  # Scale factor
                focus = (a0*b1 - a1*b0)/(b1-b0-a1+a0)  # Focal point

                a = focus + (a0 - focus)*sigma**t
                b = focus + (b0 - focus)*sigma**t

            tw.view[i0] = a
            tw.view[i1] = b

        return tw

# Alternate name for the Camera class for backward compatibility.
View = Camera


# 3D version of the Camera class. See "Camera" for more info.
#
# TWEENABLES not found in Camera
# orient = Rotation matrix specifying orientation of the view (3x3 np.array).
#          To understand how it modifies the view, imagine applying the
#          orientation matrix to the figures on screen, NOT to some imaginary
#          camera object floating in space somewhere. So for example:
#          if orient is the 90 deg CCW rotation about the positive z-axis,
#          the result is all the objects on screen will visually rotate 90 degs
#          CCW, not the other way around.
# focus = 3D position specifying the origin of the orientation transformation.
#         (np.array([x,y,z])). For example, if focus = np.array([3.0,3.0,0.0]),
#         the 3D rotations will be applied with respect to that point instead
#         of the origin. The focus point is fixed in place under changes to
#         the orient matrix.
class SpaceCamera(Camera):
    def __init__(self, view=None, orient=None, focus=None):
        if view is None:
            view = [-5,5, -5,5]

        if orient is None:
            orient = np.identity(3)
        else:
            orient = morpho.matrix.array(orient)

        if focus is None:
            # focus = np.array([0,0,0])
            focus = np.zeros(3)
        else:
            focus = morpho.matrix.array(focus)
        # elif isinstance(focus, list) or isinstance(focus, tuple):
        #     focus = np.array(focus, dtype=float)
        # elif type(focus) in (int, float, complex):
        #     focus = np.array([focus.real, focus.imag, 0], dtype=float)

        morpho.Figure.__init__(self)

        view = morpho.Tweenable("view", view, tags=["view", "scalar", "list", "nolinear"])
        _orient = morpho.Tweenable("_orient", orient, tags=["nparray", "orient"])
        _focus = morpho.Tweenable("_focus", focus, tags=["nparray"])

        self.update([view, _orient, _focus])

        self.defaultTween = type(self).tweenZoom


    @property
    def orient(self):
        return self._orient

    @orient.setter
    def orient(self, value):
        self._orient = morpho.matrix.array(value)


    @property
    def focus(self):
        return self._focus

    @focus.setter
    def focus(self, value):
        self._focus = morpho.matrix.array(value)


    ### TWEEN METHODS ###

    @morpho.TweenMethod
    def tweenZoom(self, other, t):
        tw = super().tweenZoom(other, t)
        tw = morpho.Figure.tweenLinear(tw, other, t)

        return tw


    # @morpho.TweenMethod
    # def tweenRotate(self, other, t):
    #     # Handle view tweenable
    #     tw = super().tweenZoom(other, t)

    #     # Linearly tween the focus vector manually
    #     if not np.array_equal(self.focus, other.focus):
    #         tw.focus = morpho.numTween1(self.focus, other.focus, t)

    #     tw.orient = morpho.matrix.orientTween(self.orient, other.orient, t)

    #     # # Delta matrix is the rotation needed to turn self.orient into
    #     # # other.orient
    #     # # delta = np.linalg.inv(self.orient) @ other.orient
    #     # delta = other.orient @ self.orient.T  # Transpose is inverse for rotation mats

    #     # # Compute rotation vector for delta
    #     # u, theta = morpho.matrix.rotationVector(delta)

    #     # tw.orient = morpho.matrix.rotation(u, theta*t) @ self.orient

    #     return tw


    # OBSOLETE!
    # Idea is to assume orient is a rotation matrix.
    # Find the delta rotation matrix between self and other.
    # Find an eigenvector (i.e. axis) of that delta matrix,
    # and then compute the angular change. Then we can tween
    # using the morpho.matrix.rotation() matrix using the
    # eigenvector as an axis, and the angular separation.
    @morpho.TweenMethod
    def tweenRotate_old(self, other, t):
        raise NotImplementedError
        return self.copy()

        # Linearly tween the focus vector manually
        if not np.array_equal(self.focus, other.focus):
            tw.focus = morpho.numTween1(self.focus, other.focus, t)

        # Do a rotational tween on orient

        # Treat each column of the orient matrix as a 3-vector and
        # tween it rotationally by tweening its magnitude linearly,
        # and changing its direction along a geodesic of the unit sphere.
        for k in range(3):
            # Vectors from columns
            v1 = self.orient[:,k].squeeze()
            v2 = other.orient[:,k].squeeze()

            # Magnitudes
            R1 = np.linalg.norm(v1)
            R2 = np.linalg.norm(v2)

            # Unit vectors
            u1 = v1/R1
            u2 = v2/R2

            u1 = u1
            u2 = u2

            # Tween magnitudes
            R = morpho.numTween(R1, R2, t)

            # Tween direction
            print(u1.shape)
            print(u2.shape)
            axis = np.cross(u1, u2)
            theta = math.acos(np.dot(u1, u2))
            rot = morpho.matrix.rotation(tuple(axis), t*theta)
            u = rot @ u1

            v = R*u

            tw.orient[:,k] = v


    @morpho.TweenMethod
    def tweenLinear(self, other, t, *args, **kwargs):
        tw = super().tweenLinear(other, t, *args, **kwargs)

        # Manually tween the view box
        tw.view = type(tw.view)(morpho.numTween(self.view[n], other.view[n], t) for n in range(4))

        return tw

'''
Groups actors together and gives them a common camera actor.
This is used in the Animation class.

timeOffset denotes how much the indices should be offset to correspond
to actual indices while being played in an animation.

start and end denote a time window when the layer is visible.
They are measured in units of frames LOCAL to the layer itself.
i.e. the layer will show the same stuff regardless of timeOffset.
WARNING: Recommend against using start and end. Change the visibility
of the camera actor instead to control layer visibility dynamically.
start and end may be removed in a later update!!
'''

# Groups actors together and gives them a common camera actor.
# This is used in the Animation class.
#
# ATTRIBUTES
# actors = List of actors that are part of this layer. Default: []
# view/camera = Camera actor associated with this layer. Default: Camera()
#               Note that layer visibility is linked to camera visibility.
#               Whenever the camera is invisible, so will the layer be.
# timeOffset = Number of frames the indices should be offset to line up
#              with the index system used by the Animation class. Basically
#              allows you to setup a local time axis offset from the global
#              Animation time axis. Increasing timeOffset causes the layer to
#              be animated at later points in the Animation.
# visible = Global visibility attribute. If set to False, the layer is never drawn
#           regardless of the state of the camera actor.
# start/end = Recommend not using these. These attributes may be deprecated later!
#             Specify a time window where the layer will be visible.
#             They are specified relative to the layer's LOCAL time axis.
# mask = Specify another layer object which will serve as the "mask" for this layer.
#        The mask layer basically serves as a window or opening in which the target
#        layer can appear thru. Only the parts of the target layer that overlap with
#        opaque portions of the mask layer will appear.
class Layer(object):

    def __init__(self, actors=None, view=(-5,5, -5,5), timeOffset=0, visible=True, start=-oo, end=oo):
        if actors is None:
            actors = []
        elif type(actors) is tuple:
            actors = list(actors)
        elif isinstance(actors, morpho.Figure):
            actors = [morpho.Actor(actors)]
        elif isinstance(actors, morpho.Actor):
            actors = [actors]
        elif type(actors) is not list:
            raise TypeError("Invalid input to actors!")
        # Convert any non-actors into actors
        for n in range(len(actors)):
            actor = actors[n]
            if not isinstance(actor, morpho.Actor):
                actors[n] = morpho.Actor(actor)
        self.actors = actors

        if type(view) is tuple:
            self.camera = morpho.Actor(Camera)
            self.camera.newkey(0)
            self.camera.time(0).view = list(view)
        elif type(view) is list:
            self.camera = morpho.Actor(Camera)
            self.camera.newkey(0)
            self.camera.time(0).view = view
        elif isinstance(view, morpho.Actor) and issubclass(view.figureType, Camera):
            self.camera = view
        else:
            raise TypeError("view must be list, tuple, or Camera actor.")

        self.timeOffset = timeOffset
        self.visible = visible
        self.start = start
        self.end = end
        self.mask = None

        # Hidden attributes for rendering with masks.
        # These are NOT copied with the copy() method, but it shouldn't
        # matter since these are refreshed whenever draw() is called with
        # masks involved.
        self._ctx1 = None
        self._ctx2 = None

    # "view" is an alternate name for the camera actor.
    # This is for backward-compatibility since the Camera class
    # was once called the View class.
    @property
    def view(self):
        return self.camera

    @view.setter
    def view(self, value):
        self.camera = value


    # Return a deep-ish copy of the layer by default.
    # Optionally specify deep=False to make a copy, but
    # none of the actors, the mask layer, or even the camera
    # actor are copied.
    def copy(self, deep=True):
        if deep:
            if self.maskChainFormsLoop():
                raise MaskConfigurationError("Can't make a deep copy of the layer because the mask chain loops!")
            new = type(self)(
                actors=[actor.copy() for actor in self.actors],
                view=self.camera.copy(),
                timeOffset=self.timeOffset,
                visible=self.visible,
                start=self.start,
                end=self.end
                )
            new.mask = self.mask.copy() if self.mask is not None else None
        else:
            new = type(self)(
                actors=self.actors[:],
                view=self.camera,
                timeOffset=self.timeOffset,
                visible=self.visible,
                start=self.start,
                end=self.end
                )
            new.mask = self.mask
        return new

    # Appends the actor list of other to self in place. However, it ignores
    # the camera actor and start/end indices of other.
    # However, it DOES take into account the difference in time offsets
    # between self and other and will modify the actors in other
    # IN PLACE so that the relative time offset carries over when merged.
    def merge(self, other, atFrame=0, beforeActor=oo):
        atFrame = round(atFrame)

        # Handle case that beforeActor is an actual Actor object
        if isinstance(beforeActor, morpho.Actor):
            if beforeActor not in self.actors:
                raise LayerMergeError("Given 'beforeActor' is not in this Layer!")
            else:
                beforeActor = self.actors.index(beforeActor)
        elif abs(beforeActor) != oo:
            beforeActor = round(beforeActor)

        if atFrame != int(atFrame):
            raise ValueError("atFrame parameter must be an integer!")
        if beforeActor != oo and beforeActor != int(beforeActor):
            raise ValueError("beforeActor parameter must be integer or +infinity!")

        atFrame = int(atFrame)

        # Convert beforeActor into proper format for indexing into actors list
        if beforeActor > len(self.actors):
            beforeActor = len(self.actors)
        elif beforeActor < 0:
            beforeActor %= len(self.actors)
        beforeActor = int(beforeActor)

        if type(other) in (list, tuple):
            numActorsAlreadyAdded = 0
            for n in range(len(other)):
                layer = other[n]
                self.merge(layer, atFrame, beforeActor + numActorsAlreadyAdded)
                numActorsAlreadyAdded += len(layer.actors)
        elif isinstance(other, morpho.Actor) or isinstance(other, morpho.Figure):
            other = type(self)(other)
            # Temp layer will inherit the time offset of self
            # since an actor has an unspecified time offset.
            other.timeOffset = self.timeOffset
            self.merge(other, atFrame, beforeActor)
        elif isinstance(other, Layer):
            # for actor in other.actors:
            for n in range(len(other.actors)):
                actor = other.actors[n]
                # Adjust all the indices based on the time offsets
                df = other.timeOffset - self.timeOffset + atFrame
                if df != 0:
                    timeline = {}
                    for keyID in actor.timeline:
                        timeline[keyID + df] = actor.timeline[keyID]
                    actor.timeline = timeline
                    actor.update()

                self.actors.insert(beforeActor + n, actor)
        else:
            raise TypeError("Attempted to merge non-layer object!")

        # Handle combining mask layers

        # These booleans record whether the corresponding layer's mask is
        # "external" meaning it exists and does not point to its partner.
        # This assumes that the user did not accidentally make a layer's
        # mask point to itself. If the user does have a self-pointing mask,
        # it will be treated as "external" nonetheless.
        selfExternal = self.mask is not None and self.mask is not other
        otherExternal = other.mask is not None and other.mask is not self

        # If both point to external layers, then crash.
        if selfExternal and otherExternal:
            raise LayerMergeError("Both layers have mask layers external to each other.")
        # Else if self is external, it can stay that way.
        elif selfExternal:
            pass
            # print("#2")
        # Else if other is external, self inherits other's mask.
        elif otherExternal:
            self.mask = other.mask
            # print("#3")
        # Else self should have no mask.
        else:
            self.mask = None
            # print("#4")


    # Convenience function. Behaves just like merge() except it always
    # merges at the maxkeyID of self.
    # If maxkeyID is -oo, then merges at frame 0.
    def append(self, other, timeOffset=0, beforeActor=oo):
        atFrame = self.lastID()
        if atFrame == -oo:
            atFrame = 0
        atFrame += timeOffset
        self.merge(other, atFrame, beforeActor)

    # Returns the minimum key index across all actors (including the camera).
    # If all actors have empty timelines, it returns +oo.
    # Note that this method ignores the mask.
    def firstID(self, useOffset=False):
        minkey = oo

        # Minimize over the camera actor
        minkey = min((minkey, self.camera.keyIDs[0] if len(self.camera.timeline) > 0 else minkey))

        # Minimize over all the regular actors
        for actor in self.actors:
            minkey = min((minkey, actor.keyIDs[0] if len(actor.timeline) > 0 else minkey))
        return minkey + self.timeOffset if useOffset else minkey
    # minkeyID = firstkeyID = firstID  # Synonyms for firstID()

    # Returns the maximum key index across all actors (including the camera).
    # The index value returned is in LOCAL time coordinates unless useOffset is True
    # If all actors have empty timelines, it returns -oo.
    # Note that this method ignores the mask unless ignoreMask is set to False.
    def lastID(self, useOffset=False, ignoreMask=True):
        maxkey = -oo

        # Maximize over the camera actor
        maxkey = max((maxkey, self.camera.keyIDs[-1] if len(self.camera.timeline) > 0 else maxkey))

        # Maximize over all the regular actors
        for actor in self.actors:
            maxkey = max((maxkey, actor.keyIDs[-1] if len(actor.timeline) > 0 else maxkey))

        # Maximize over the mask layer (if requested)
        # Check for loops if mask should be included in this calculation.
        if not ignoreMask and self.mask is not None:
            if self.maskChainFormsLoop():
                raise MaskConfigurationError("The mask chain of the layers form a loop. Can't compute lastID.")

            maxkey = max(maxkey, self.mask.lastID(ignoreMask=False) + self.mask.timeOffset - self.timeOffset)

        return maxkey + self.timeOffset if useOffset else maxkey

    # maxkeyID = lastkeyID = lastID  # Synonyms for lastID()

    # Return a frame of all the actors' states at index f.
    # Skips invisible actors.
    def time(self, f, useOffset=False):
        # Adjust for time offset
        if useOffset:
            f -= self.timeOffset

        # frm = self.view.time(f).copy(deep=False)
        frm = Frame()
        # if frm is None:
        #     if len(self.view.timeline) == 0:
        #         frm = Frame()
        #     elif f > self.view.keyIDs[-1]:
        #         frm = self.key(-1).copy()
        #     else:
        #         frm = self.key(0).copy()

        # Populate the figure list with the actor states.
        for actor in self.actors:
            if not actor.visible: continue
            fig = actor.time(f)
            if fig is not None:
                frm.figures.append(fig)
        return frm

    # Applies the actor pad() method to all the actors in the layer.
    # UNTESTED AND NOT IMPLEMENTED!!!
    def pad(self, a, b=None, numFrames=0, numBefore=0, numAfter=0, useOffset=False):
        raise NotImplementedError

        if b is None:
            b = a

        # Adjust for time offset
        if useOffset:
            a -= self.timeOffset
            b -= self.timeOffset

        for actor in self.actors:
            actor.pad(a,b, numFrames, numBefore, numAfter)

    # Convenience function that computes the current view 4-vector
    # of the layer camera at the specified time.
    #
    # Note that this is a READ-ONLY function; you can't use it
    # to MODIFY the camera state. To do that, you have to use
    # layer.camera.time(f).view = [a,b,c,d]
    #
    # Set returnCamera = True to make the function return
    # the actual camera figure instead of just the view 4-vector.
    def viewtime(self, f, useOffset=False, returnCamera=False):
        if len(self.camera.timeline) == 0:
            raise IndexError("Camera timeline is empty.")

        # Adjust for time offset
        if useOffset:
            f -= self.timeOffset

        # Compute current view
        viewFrame = self.camera.time(f)
        if viewFrame is None:
            # if len(self.camera.timeline) == 0:
            #     viewFrame = Frame()
            if f > self.camera.keyIDs[-1]:
                viewFrame = self.camera.key(-1)
            else:
                viewFrame = self.camera.key(0)

        if returnCamera:
            return viewFrame
        else:
            view = viewFrame.view
            return view

    # Shifts the timeline of the entire layer forward by the given
    # number of frames, but leaves the timeOffset unchanged.
    # This means it shifts the camera, all actors, and the start
    # and end attributes.
    # By default, ignoreMask = False, which means this method will
    # recusively shift all mask layers to keep everything in sync.
    # Setting ignoreMask = True makes shift() only act on self and
    # not on any masks.
    #
    # Note: This method has not been tested to my full standards yet,
    # but I feel pretty confident it works right now.
    def shift(self, numFrames, ignoreMask=False):
        numFrames = round(numFrames)
        self.camera.shift(numFrames)
        self.start += numFrames
        self.end += numFrames
        for actor in self.actors:
            actor.shift(numFrames)

        if self.mask is not None and not ignoreMask:
            # First check for loops
            if self.maskChainFormsLoop():
                raise MaskConfigurationError("Can't recusively shift mask layers because they form a loop.")
            self.mask.shift(numFrames, ignoreMask=False)

    # Shifts the timelines of all the actors in the layer (including
    # the camera actor) according to the timeOffset attribute and then
    # zeros the timeOffset attribute.
    def commitOffset(self, ignoreMask=False):
        # self.camera.shift(self.timeOffset)
        # self.start += self.timeOffset
        # self.end += self.timeOffset
        # for actor in self.actors:
        #     actor.shift(self.timeOffset)

        # ingoreMask should be True no matter what here, because
        # we'll handle the masks with recursive calls to
        # commitOffset() later in the code!
        self.shift(self.timeOffset, ignoreMask=True)

        # Reset time offset
        self.timeOffset = 0

        # Recursively commit mask offsets if requested.
        if self.mask is not None and not ignoreMask:
            # First check for loops
            if self.maskChainFormsLoop():
                raise MaskConfigurationError("Can't recusively commit mask offsets because they form a loop.")
            currentLayer = self
            while currentLayer.mask is not None:
                currentLayer.mask.commitOffset()
                currentLayer = currentLayer.mask


    # Speeds up all actors and the camera by the given factor.
    # If useOffset = False, timeOffset is NOT changed,
    # and the actor list and camera are speed changed interpreting
    # center in local layer time.
    # If useOffset = True, the actor list and camera are speed changed
    # centered about local layer time = 0, but the time offset is
    # scaled relative to the given center value interpreted as
    # external time. In the context of an animation, this should have
    # the effect of speed changing the layer as if the time offset
    # had been committed.
    # If ignoreMask is set to True, then this method will not act on
    # this layer's mask (if it exists).
    # If ignoreMask is set to False (which it is by default),
    # then speedUp() will act recursively on all mask layers.
    # This will always be done by modifying the timeOffsets of the masks
    # regardless of whether timeOffset is modified for the original calling
    # method.
    def speedUp(self, factor, center=0, useOffset=False, ignoreMask=False):

        if useOffset:
            # Speed up mask layer(s) recursively if present and requested.
            # This is always done by modifying the timeOffset of the mask layer.
            if self.mask is not None and not ignoreMask:
                # print("useOffset=True and doing it!")
                # First check for loops
                if self.maskChainFormsLoop():
                    raise MaskConfigurationError("Can't recusively speed change mask layers because they form a loop.")
                # # This line should come first because you want the
                # # timeOffset updated BEFORE you call speedUp() because
                # # speedUp() may recursively act on deeper mask layers!
                # self.mask.timeOffset = round(center + (self.mask.timeOffset - center)/factor)
                self.mask.speedUp(factor, center, useOffset=True, ignoreMask=False)


            for actor in self.actors:
                actor.speedUp(factor, center=0)

            self.camera.speedUp(factor, center=0)

            if abs(self.start) != oo:
                self.start = round(self.start/factor)
            if abs(self.end) != oo:
                self.end = round(self.end/factor)

            # Alter time offset according to factor
            self.timeOffset = round((self.timeOffset-center)/factor + center)

        else:
            # Speed up mask layer(s) recursively if present and requested.
            # This is always done by modifying the timeOffset of the mask layer.
            if self.mask is not None and not ignoreMask:
                # print("useOffset=False and doing it!")
                # First check for loops
                if self.maskChainFormsLoop():
                    raise MaskConfigurationError("Can't recusively speed change mask layers because they form a loop.")
                # # This line should come first because you want the
                # # timeOffset updated BEFORE you call speedUp() because
                # # speedUp() may recursively act on deeper mask layers!
                # self.mask.timeOffset = round(self.timeOffset + center + (self.mask.timeOffset - center - self.timeOffset)/factor)
                self.mask.speedUp(factor, center=self.timeOffset+center, useOffset=True, ignoreMask=False)

            for actor in self.actors:
                actor.speedUp(factor, center)

            self.camera.speedUp(factor, center)

            if abs(self.start) != oo:
                self.start = round((self.start - center)/factor + center)
            if abs(self.end) != oo:
                self.end = round((self.end - center)/factor + center)


    # OBSOLETE!
    # Speeds up all actors by the given factor.
    # Note that the time offset of the layer is unaffected by
    # speed changes. Only the actors, the camera, and start and end
    # are speed changed.
    # As usual, if useOffset = False, the center value is interpreted
    # as local layer time.
    def speedUp_old(self, factor, center=0, useOffset=False):
        if useOffset:
            center -= self.timeOffset

        for actor in self.actors:
            actor.speedUp(factor, center)

        # Don't forget the camera actor!!
        self.camera.speedUp(factor, center)

        # Don't forget about start and end!
        if abs(self.start) != oo:
            self.start = round((self.start - center)/factor + center)
        if abs(self.end) != oo:
            self.end = round((self.end - center)/factor + center)


    # Equivalent to speedUp(1/factor). See speedUp() for more info.
    def slowDown(self, factor, center=0, useOffset=False, ignoreMask=False):
        self.speedUp(1/factor, center, useOffset, ignoreMask)


    # Pretweens all the actors in the layer including the camera actor.
    # See Actor.pretween() for more info.
    # By default, masks are recursively pretweened as well, unless
    # ignoreMask = False
    def pretween(self, ignoreMask=False):
        # First pretween the camera.
        self.camera.pretween()

        # Now pretween the actors
        for actor in self.actors:
            actor.pretween()

        # Pretween the mask layer (if it exists and not ignored)
        if self.mask is not None and not ignoreMask:
            if self.maskChainFormsLoop():
                raise MaskConfigurationError("Can't pretween this layer because the mask chain forms a loop.")
            self.mask.pretween()

    # Check if the chain of layer masks forms a loop.
    # Return boolean indicating result. True: loop exists; False: no loop.
    def maskChainFormsLoop(self):
        layers = {self}
        mask = self.mask
        while mask is not None:
            if mask in layers:
                return True
            layers.add(mask)
            mask = mask.mask
        return False

    # Sets up the internal subcontexts used by the Layer class when
    # drawing with masking. Allows the draw() method to recycle subcontexts
    # as often as possible without having to generate new ones every draw,
    # which appears to slow down rendering a lot.
    def _setupInternalSubcontexts(self, ctx):
        # Extract surface's width and height
        surface = ctx.get_target()
        width = surface.get_width()
        height = surface.get_height()

        if self._ctx1 is None:
            # Setup contexts if they are undefined.
            self._ctx1 = setupContext(width, height, flip=False)
            self._ctx1.set_line_join(ctx.get_line_join())
        else:
            # Setup new contexts if dimensions are mismatched
            surf1 = self._ctx1.get_target()
            width1 = surf1.get_width()
            height1 = surf1.get_height()
            if (width, height) != (width1, height1):
                self._ctx1 = setupContext(width, height, flip=False)
                self._ctx1.set_line_join(ctx.get_line_join())
        if self._ctx2 is None:
            self._ctx2 = setupContext(width, height, flip=False)
            self._ctx2.set_line_join(ctx.get_line_join())
        else:
            # Setup new contexts if dimensions are mismatched
            surf2 = self._ctx2.get_target()
            width2 = surf2.get_width()
            height2 = surf2.get_height()
            if (width, height) != (width2, height2):
                self._ctx2 = setupContext(width, height, flip=False)
                self._ctx2.set_line_join(ctx.get_line_join())

        # Clear both subcontexts
        clearContext(self._ctx1, background=(0,0,0), alpha=0)
        clearContext(self._ctx2, background=(0,0,0), alpha=0)


    # Draw the layer at the specified index on the given cairo context
    # if the camera is visible at that index.
    # If useOffset is False, the f index is interpreted as LOCAL to the layer,
    # otherwise, the timeoffset is applied before f is used for anything.
    # That is, useOffset=False means we're using local time,
    # useOffset=True means we're using global (i.e. Animation class) time.
    def draw(self, f, ctx, useOffset=False):
        if useOffset:
            # Convert f to equivalent local time coordinates.
            f -= self.timeOffset

        # Compute current view
        cam = self.viewtime(f, returnCamera=True)  # Get camera figure
        if not cam.visible:
            return

        # Compile list of figures to draw
        figlist = []
        for actor in self.actors:
            if actor.visible:
                fig = actor.time(f)
                # if fig is None or not fig.visible:
                #     continue
                # else:
                #     figlist.append(fig)
                if fig is not None and fig.visible:
                    figlist.append(fig)

        # Sort based on zdepth
        figlist.sort(key=lambda fig: fig.zdepth) #, reverse=True)

        # NOTE: The "start" and "end" parameters of the masklayer are ignored
        # when drawing with masking!
        if self.mask is None or not self.mask.viewtime(f, returnCamera=True).visible:
            # Draw all figures
            for fig in figlist:
                fig.draw(cam, ctx)
        else:  # Layer has a mask, so draw with masking
            # # Extract surface's width and height
            # surface = ctx.get_target()
            # width = surface.get_width()
            # height = surface.get_height()

            # # Setup new context with a transparent target surface
            # ctxPrimary = setupContext(width, height, flip=False)

            self._setupInternalSubcontexts(ctx)

            # Draw all figures to this intermediate surface:
            for fig in figlist:
                fig.draw(cam, self._ctx1)

            # # Setup another intermediate context for the mask layer
            # # to be drawn on
            # ctxMask = setupContext(width, height, flip=False)

            # Draw the mask layer on the secondary subcontext
            self.mask.draw(f+self.timeOffset-self.mask.timeOffset, self._ctx2)

            # Now draw the primary surface with the mask surface applied
            # down on the original context
            ctx.set_source_surface(self._ctx1.get_target())
            ctx.mask_surface(self._ctx2.get_target())


# 3D version of the Layer class. See "Layer" for more info.
# Used for actors of space figures
# (e.g. SpacePoint, SpacePath, SpacePolygon, Quadmesh)
# The main difference is that the camera actor here is a SpaceCamera,
# and so supports the "orient" and "focus" tweenables.
# You can specify the initial orient and focus values in the constructor.
# By default, they are np.eye(3) and np.array([0,0,0]) respectively.
#
# This class also has an attribute called "poolPrimitives" which specifies
# whether at each draw, the 2D primitive figures resulting from each space
# figure's primitives() method should be pooled together in a big list and
# sorted by zdepth before drawing. This basically results in more realistic
# 3D environments, and should usually be set equal to True (it is by default).
# If set to False, the space figures are drawn according to their intrinsic
# zdepth values, regardless of the current camera view. This can result
# in the draw order being incompatible with the current view in some cases.
class SpaceLayer(Layer):
    def __init__(
        self, actors=None, view=(-5,5, -5,5), orient=None, focus=None,
        timeOffset=0, visible=True, start=-oo, end=oo,
        poolPrimitives=True):
        # Use superclass's constructor to start
        super().__init__(actors, view, timeOffset, visible, start, end)

        if orient is None:
            orient = np.identity(3)
        else:
            orient = morpho.matrix.array(orient)

        if focus is None:
            # focus = np.array([0,0,0])
            focus = np.zeros(3)
        else:
            focus = morpho.matrix.array(focus)
        # elif isinstance(focus, list) or isinstance(focus, tuple):
        #     focus = np.array(focus, dtype=float)
        # elif type(focus) in (int, float, complex):
        #     focus = np.array([focus.real, focus.imag, 0], dtype=float)

        # Change the camera attribute to a spacecamera
        if type(view) is tuple:
            self.camera = morpho.Actor(SpaceCamera)
            self.camera.newkey(0)
            self.camera.time(0).view = list(view)
            self.camera.time(0).orient = orient
            self.camera.time(0).focus = focus
        elif type(view) is list:
            self.camera = morpho.Actor(SpaceCamera)
            self.camera.newkey(0)
            self.camera.time(0).view = view
            self.camera.time(0).orient = orient
            self.camera.time(0).focus = focus
        elif isinstance(view, morpho.Actor) and issubclass(view.figureType, SpaceCamera):
            self.camera = view
        else:
            raise TypeError("view must be list, tuple, or SpaceCamera actor.")

        # If set to True, when the layer is drawn, it makes use of the
        # primitives() method of any constituent space figures that have
        # that method. The primitives method returns a list of 2D figures
        # correctly transformed so that drawing them in the correct order
        # results in the desired 3D figure appearing on screen.
        # Critically, each 2D "primitive" figure
        # has its zdepth set so that it should be drawn (more or less) in
        # the correct order for the given camera orientation.
        # If set to False, the draw order for each space figure is inferred
        # in the classical way from its (otherwise ignored) zdepth.
        # Some space figures do not have a primitives() method such as the
        # SpacePath figure as it is difficult to assign a single sensible zdepth
        # to a path which may wind through many depths in space.
        # (UPDATE: SpacePath now supports primitives() )
        # If a layer contains some space figures supporting primitives() and others
        # that do not, the figures without primitives are always drawn behind those
        # that support them if poolPrimitives is set to True.
        # The bottom line for users of Morpho is setting this to True generally
        # results in a more realistic 3D rendering.
        self.poolPrimitives = poolPrimitives


    # Return a deep-ish copy of the layer by default.
    # Optionally specify deep=False to make a copy, but
    # none of the actors or even the camera actor are copied.
    def copy(self, deep=True):
        if deep:
            new = type(self)(
                actors=[actor.copy() for actor in self.actors],
                view=self.camera.copy(),
                # orient=self.orient.copy(),
                # focus=self.focus.copy(),
                timeOffset=self.timeOffset,
                visible=self.visible,
                start=self.start,
                end=self.end,
                poolPrimitives=self.poolPrimitives
                )
            new.mask = self.mask.copy() if self.mask is not None else None
        else:
            new = type(self)(
                actors=self.actors[:],
                view=self.camera,
                # orient=self.camera.orient.copy(),
                # focus=self.camera.focus.copy(),
                timeOffset=self.timeOffset,
                visible=self.visible,
                start=self.start,
                end=self.end,
                poolPrimitives=self.poolPrimitives
                )
            new.mask = self.mask
        return new


    # Draw the spacelayer at the specified index on the given cairo context
    # if the camera is visible at that index.
    def draw(self, f, ctx, useOffset=False):
        if useOffset:
            f -= self.timeOffset

        # Compute current view
        cam = self.viewtime(f, returnCamera=True)  # Get camera figure
        if not cam.visible:
            return

        # view = self.viewtime(f)
        # viewFrame = self.view.time(f)
        # if viewFrame is None:
        #     if len(self.view.timeline) == 0:
        #         viewFrame = Frame()
        #     elif f > self.view.keyIDs[-1]:
        #         viewFrame = self.view.key(-1)
        #     else:
        #         viewFrame = self.view.key(0)
        # view = viewFrame.view

        # Compile list of figures to draw
        figlist = []
        for actor in self.actors:
            if actor.visible:
                fig = actor.time(f)
                if fig is None or not fig.visible:
                    continue
                figlist.append(fig)

        # Sort based on zdepth
        figlist.sort(key=lambda fig: fig.zdepth) #, reverse=True)

        if self.poolPrimitives:
            primlist = []  # This list "pools" together all primitives across all figures
            for fig in figlist[:]:
                if "primitives" in dir(fig):
                    primlist.extend(fig.primitives(cam))
                    figlist.remove(fig)

        # NOTE: The "start" and "end" parameters of the masklayer are ignored
        # when drawing with masking!
        if self.mask is None or not self.mask.viewtime(f, returnCamera=True).visible:
            # Draw all non-primitive figures
            for fig in figlist:
                fig.draw(cam, ctx)
            # Draw all primitive 2D figures
            if self.poolPrimitives:
                frame = Frame(primlist)
                frame.draw(cam, ctx)
        else:  # There is a mask, so draw with masking!
            # # Extract surface's width and height
            # surface = ctx.get_target()
            # width = surface.get_width()
            # height = surface.get_height()

            # # Setup new context with a transparent target surface
            # ctxPrimary = setupContext(width, height, flip=False)

            self._setupInternalSubcontexts(ctx)

            # Draw all figures to this intermediate surface:

            # Draw all non-primitive figures
            for fig in figlist:
                fig.draw(cam, self._ctx1)
            # Draw all primitive 2D figures
            if self.poolPrimitives:
                frame = Frame(primlist)
                frame.draw(cam, self._ctx1)

            # # Setup another intermediate context for the mask layer
            # # to be drawn on
            # ctxMask = setupContext(width, height, flip=False)

            # Draw the mask layer on the secondary subcontext
            self.mask.draw(f+self.timeOffset-self.mask.timeOffset, self._ctx2)

            # Now draw the primary surface with the mask surface applied
            # down on the original context
            ctx.set_source_surface(self._ctx1.get_target())
            ctx.mask_surface(self._ctx2.get_target())


# Collects layers into a single animation and a unified timeline.
# This class is where the animation can be played or exported.
#
# PRIMARY ATTRIBUTES
# layers = List of layers contained in this animation. Layers late in the list
#          are drawn in front of layers early in the list. Default: []
# windowShape = Tuple specifying window dimensions (width, height) in pixels.
#               Default: (600, 600)
# frameRate = Frames per second (fps). Default: 30
# firstIndex/start = Starting frame of the animation.
#           Default: None (meaning it will use mation.firstID() )
# finalIndex/end = Ending frame of animation.
#           Default: None (meaning it will use mation.lastID() )
# delays = Dict mapping index values to delay duration (in frames).
#          Animation will pause for the specified durations at the given indices.
#          Specifying infinite duration will pause animation indefinitely until
#          screen is clicked.
# background = Background color (RGB list). Default: (0,0,0) (black)
# alpha = Background opacity. Default: 1 (opaque)
# resizable = Boolean indicating whether window can be resized during playback.
#             Default: False
# fullscreen = Boolean indicating whether animation should be played fullscreen.
#              Default: False
# screen = int denoting which monitor to display on (0 is primary monitor).
#          Default: 0
# locaterLayer = Given layer or layer list index, prints the physical coordinates
#                of a mouse click relative to that layer whenever the animation
#                playback is clicked. Default: None
# clickTime = Boolean if set to True, prints current frame index to console
#             whenever animation is clicked to pause.
#             Options: "frames", "seconds"
#             Note: This ignores animation delays.
# clickCopy = Boolean if set to True and locaterLayer is set, then every click
#             will copy the complex coordinates of the click to the
#             clipboard.
# clickRound = Boolean if set to int N, the coordinates of a locater layer
#              click round to N decimal places. By default it's set to None,
#              meaning no rounding will take place.
# transition = Global transition function applied to all figures in the animation.
#              Default: morpho.transitions.uniform
# antialiasText = Boolean indicating whether text should be antialiased.
#                 Default: True
class Animation(object):

    def __init__(self, layers=None, windowShape=(600, 600)):

        # Layers list.
        # Later layers are drawn in front of earlier layers.
        if layers is None:
            self.layers = []
        elif type(layers) is tuple:
            self.layers = list(layers)
        elif type(layers) is list:
            self.layers = layers
        # elif type(layers) is Layer:
        elif isinstance(layers, Layer):
            self.layers = [layers]
        elif type(layers) is morpho.Actor:
            self.layers = [Layer(layers)]
        elif isinstance(layers, morpho.Figure):
            self.layers = [Layer(morpho.Actor(layers))]
        else:
            raise TypeError("layers must be list/tuple of Layer objects or else a single actor.")


        # Frame rate of the animation in frames per second (fps)
        self.frameRate = 30

        # Tells the animation which frame index to start playing at.
        self.firstIndex = None

        # Tells the animation which frame index to stop playing at.
        self.finalIndex = None

        # Pause dict maps indices to delays (in units of frames).
        # Given delay value of oo means pause the animation until
        # clicked. Note: The indices MUST be ints or float("inf")!
        self.delays = {}

        # Background color and alpha for the animation.
        # Specified as RGB in the range [0,1]
        self.background = (0,0,0)
        self.alpha = 1

        # Dimensions of the animation window in pixels (width x height)
        self.windowShape = tuple(windowShape)

        # Is animation window resizable?
        self.resizable = False

        # Is animation window fullscreen?
        self.fullscreen = False

        # If the window is fullscreen, which screen should be used?
        # 0 = Main screen
        self.screen = 0

        # Given a layer, or an int representing the index of a layer
        # in the layer list, when the animation is clicked during playback,
        # it will print the physical coordinates of the click location
        # relative to the specified layer.
        self.locaterLayer = None

        # Makes the animation print the current frame/time when
        # clicked to pause.
        # Options: "frames", "seconds"
        # Note: This ignores animation delays.
        self.clickTime = "none"

        # If set to True and locaterLayer is set, then every click
        # will copy the complex coordinates of the click to the
        # clipboard.
        self.clickCopy = False

        # If set to int N, the coordinates of a locater layer click
        # round to N decimal places. By default it's set to None,
        # meaning no rounding will take place.
        self.clickRound = None

        # transition governs how tweening animation proceeds.
        # It is a function that takes a time parameter in the
        # range [0,1] and returns a time parameter in the same
        # range that denotes the interpolation time value for
        # input into the tween() functions.
        self.transition = morpho.transitions.uniform

        # Antialiasing for text.
        # Set to False if you think animation rendering is being
        # slowed by text rendering.
        self.antialiasText = True

        # Set the style to use for joining line segments together.
        # Options are "bevel", "miter", and "round". Default: "round"
        self.jointStyle = "round"

        # Active animation variables
        self.active = False
        self.context = None
        self.window = None
        self.renderData = None
        self.renderTexture = None
        self.update = None
        self.paused = False
        self.delay = 0
        self.skipPauseIndex = None
        self.currentIndex = 0
        # self._keyIDs = None  # This var is only used once play() is called.

    @property
    def background(self):
        return self._background

    @background.setter
    def background(self, value):
        if len(value) > 3:
            self.alpha = value[3]
        elif len(value) < 3:
            value += ((0,)*(3-len(value)))

        self._background = value[:3]

    # Alternate name for the locater layer using "o" instead of "e".
    @property
    def locatorLayer(self):
        return self.locaterLayer

    @locatorLayer.setter
    def locatorLayer(self, value):
        self.locaterLayer = value

    @property
    def start(self):
        return self.firstIndex

    @start.setter
    def start(self, value):
        self.firstIndex = value

    @property
    def end(self):
        return self.finalIndex

    @end.setter
    def end(self, value):
        self.finalIndex = value

    @property
    def delays(self):
        return self._delays

    @delays.setter
    def delays(self, value):
        self._delays = IntDict(value)



    # Returns a (deep-ish) copy of the animation.
    # If deep=False, then the animation will not make copies of the
    # underlying figures in the layers.
    # Note that copy will not copy over the window attribute, so you will
    # have to manually associate the window to the copied animation.
    def copy(self, deep=True):
        ani = Animation()

        # Make copies of all the layers.
        ani.layers = [layer.copy(deep=deep) for layer in self.layers]

        # Copy other attributes
        ani.frameRate = self.frameRate
        ani.firstIndex = self.firstIndex
        ani.finalIndex = self.finalIndex
        ani.delays = self.delays.copy()
        ani.background = self.background
        ani.alpha = self.alpha
        ani.windowShape = self.windowShape[:]
        ani.resizable = self.resizable
        ani.fullscreen = self.fullscreen
        ani.screen = self.screen
        ani.locaterLayer = self.locaterLayer
        ani.clickTime = self.clickTime
        ani.transition = self.transition
        ani.currentIndex = self.currentIndex
        ani.antialiasText = self.antialiasText
        ani.jointStyle = self.jointStyle
        ani.clickCopy = self.clickCopy
        ani.clickRound = self.clickRound

        # # Relink mask layers to the copy's layer list whenever possible
        # for n in range(len(ani.layers)):
        #     layer = ani.layers[n]
        #     if layer.mask is not None and layer.mask in self.layers:
        #         layer.mask = ani.layers[self.layers.index(layer.mask)]

        return ani

    # Append the layers of other on top of self.
    # Optionally specify a frame offset which represents
    # the frame when the other animation starts.
    # Merging two animations of differing frame rates will cause
    # the other animation to be modified subject to self.
    # For example, more or fewer tweened frames may be added
    # to compensate so that the overall speed and timing of the
    # animations plays correctly.
    # Also note that merging is done in place, and the transition
    # of the other animation is NOT taken into account when merging.
    # However, transitions of the individual frames ARE taken into
    # account and preserved.
    def merge(self, other, atFrame=0, beforeLayer=oo):
        if not self.verify() or (isinstance(other, Animation) and not other.verify()):
            raise Exception("Can't merge: One or both animations are configured badly.")

        atFrame = round(atFrame)

        # Handle case that beforeLayer is an actual Layer object
        if isinstance(beforeLayer, morpho.Layer):
            if beforeLayer not in self.layers:
                raise MergeError("Given 'beforeLayer' is not in the Layer list!")
            else:
                beforeLayer = self.layers.index(beforeLayer)
        elif abs(beforeLayer) != oo:
            beforeLayer = round(beforeLayer)

        if atFrame != int(atFrame):
            raise ValueError("atFrame parameter must be an integer!")
        if beforeLayer != oo and beforeLayer != int(beforeLayer):
            raise ValueError("beforeLayer parameter must be integer or +infinity!")

        atFrame = int(atFrame)

        # Convert beforeLayer into proper format for indexing into layers list.
        if beforeLayer > len(self.layers):
            beforeLayer = len(self.layers)
        elif beforeLayer < 0:
            beforeLayer %= len(self.layers)
        beforeLayer = int(beforeLayer)

        # Convert other into an animation if they are some other type.

        # Converts actor into animation in its own layer, with camera
        # inherited from the layer underneath where it is being
        # inserted in self if such a layer exists.
        # Else uses default view = [-5,5, -5,5].
        # Note that this is done rotationally, so inserting the actor
        # before the bottommost layer inherits the camera from the
        # topmost layer.
        # frameRate is set to whatever self's is.
        if isinstance(other, morpho.Figure):
            other = morpho.Actor(other)
        if isinstance(other, morpho.Actor):
            other = Animation(other)
            other.frameRate = self.frameRate

            # Inherit camera from below and adjust based on time offsets.
            # I just thought hard about this, and I believe the second line IS CORRECT!
            other.layers[0].camera = self.layers[beforeLayer-1].camera.copy() if len(self.layers) > 0 else morpho.Actor(Camera([-5,5, -5,5]))
            other.layers[0].camera.shift((self.layers[beforeLayer-1].timeOffset if len(self.layers) > 0 else 0)-atFrame)

            self.merge(other, atFrame, beforeLayer)
            return
        # Converts layer into animation with same framerate as self.
        elif isinstance(other, Layer):
            other = Animation(other)
            other.frameRate = self.frameRate
            self.merge(other, atFrame, beforeLayer)
            return

        # If the framerates differ, change other subject to self.
        if self.frameRate != other.frameRate:
            other.newFrameRate(self.frameRate)

        # If given non-zero atFrame, go thru all the layers and offset
        # their indices by the specified amount. This will have the
        # effect of making the other animation play just as it
        # normally would, but starting at the specified frame index of
        # self.
        if atFrame != 0:
            for layer in other.layers:
                layer.timeOffset += atFrame

                # Recursively update mask chain time offsets
                # (NOT TESTED YET!!!)
                if layer.maskChainFormsLoop():
                    raise MergeError("Layer masks form a loop! Can't recursively update mask time offsets!")
                currentLayer = layer
                while currentLayer.mask is not None:
                    currentLayer.mask.timeOffset += atFrame
                    currentLayer = currentLayer.mask

            # Also shift other's delays
            newDelays = {}
            for keyID in other.delays:
                newDelays[keyID+atFrame] = other.delays[keyID]
            other.delays = newDelays

        # Insert other's layers to self's.
        # self.layers.extend(other.layers)
        self.layers[beforeLayer:beforeLayer] = other.layers

        # Add on other's delays
        for keyID in other.delays:
            # Handle collision of keyIDs: the delays stack.
            if keyID in self.delays:
                self.delays[keyID] += other.delays[keyID]
            else:
                self.delays[keyID] = other.delays[keyID]


    # OBSOLETE
    def merge_old(self, other, atFrame=0, beforeLayer=oo):
        if not self.verify() or (isinstance(other, Animation) and not other.verify()):
            raise Exception("Can't merge: One or both animations are configured badly.")

        if atFrame != int(atFrame):
            raise ValueError("atFrame parameter must be an integer!")
        if beforeLayer != oo and beforeLayer != int(beforeLayer):
            raise ValueError("beforeLayer parameter must be integer or +infinity!")

        atFrame = int(atFrame)

        # Convert beforeLayer into proper format for indexing into layers list.
        if beforeLayer > len(self.layers):
            beforeLayer = len(self.layers)
        elif beforeLayer < 0:
            beforeLayer %= len(self.layers)
        beforeLayer = int(beforeLayer)

        # Convert other into an animation if they are some other type.

        # Converts actor into animation in its own layer, with camera
        # inherited from the layer underneath where it is being
        # inserted in self if such a layer exists.
        # Else uses default view = [-5,5, -5,5].
        # Note that this is done rotationally, so inserting the actor
        # before the bottommost layer inherits the camera from the
        # topmost layer.
        # frameRate is set to whatever self's is.
        if isinstance(other, morpho.Figure):
            other = morpho.Actor(other)
        if isinstance(other, morpho.Actor):
            other = Animation(other)
            other.frameRate = self.frameRate
            # other.layers[0].camera = self.layers[-1].camera.copy() if len(self.layers) > 0 else morpho.Actor(Camera([-5,5, -5,5]))
            # other.layers[0].camera.shift((self.layers[-1].timeOffset if len(self.layers) > 0 else 0)-atFrame)
            other.layers[0].camera = self.layers[beforeLayer-1].camera.copy() if len(self.layers) > 0 else morpho.Actor(Camera([-5,5, -5,5]))
            other.layers[0].camera.shift((self.layers[beforeLayer-1].timeOffset if len(self.layers) > 0 else 0)-atFrame)

            self.merge(other, atFrame, beforeLayer)
            return
        # Converts layer into animation with same framerate as self.
        elif isinstance(other, Layer):
            other = Animation(other)
            other.frameRate = self.frameRate
            self.merge(other, atFrame, beforeLayer)
            return

        # other = other.copy()

        # If the framerates differ, change other subject to self.
        if self.frameRate != other.frameRate:
            for layer in other.layers:
                for actor in layer.actors:
                    timeline = {}  # New timeline
                    for keyID in actor.keyIDs:
                        keyfig = actor.timeline[keyID]
                        # Convert this actor's keyIDs into units
                        # consistent with self's framerate.
                        f = round(self.frameRate*keyID / other.frameRate)
                        # Also convert keyfig delays
                        if keyfig.delay != oo:
                            keyfig.delay = round(self.frameRate*keyfig.delay / other.frameRate)

                        # (Overwriting is ok and desired :) )
                        timeline[f] = keyfig
                    actor.timeline = timeline
                    actor.update()

            # Also modify animation delays
            # CAUTION: THIS IS STILL UNTESTED!! USE AT OWN RISK!!!
            newDelays = {}
            for keyID in other.delays:
                delay = other.delays[keyID]
                newID = round(self.frameRate*keyID / other.frameRate)
                newDelay = round(self.frameRate*keyID / other.frameRate) # I think this line has a mistake: keyID should be newDelay

                # The complication is because dropping frame rates could cause
                # a collision among keyIDs. Add them instead of replacing!
                newDelays[newID] = newDelay if newID not in newDelays else newDelays[newID] + newDelay
            other.delays = newDelays

        # If given non-zero atFrame, go thru all the layers and offset
        # their indices by the specified amount. This will have the
        # effect of making the other animation play just as it
        # normally would, but starting at the specified frame index of
        # self.
        if atFrame != 0:
            for layer in other.layers:
                layer.timeOffset += atFrame

            # Also shift other's delays
            newDelays = {}
            for keyID in other.delays:
                newDelays[keyID+atFrame] = other.delays[keyID]
            other.delays = newDelays

        # Insert other's layers to self's.
        # self.layers.extend(other.layers)
        self.layers[beforeLayer:beforeLayer] = other.layers

        # Add on other's delays
        for keyID in other.delays:
            # Handle collision of keyIDs
            if keyID in self.delays:
                self.delays[keyID] += other.delays[keyID]
            else:
                self.delays[keyID] = other.delays[keyID]

    # Convenience function. Behaves just like merge() except it always
    # merges at the maxkeyID of self.
    # If maxkeyID is -oo, merges at frame 0 (+timeOffset).
    def append(self, other, timeOffset=0, beforeLayer=oo):
        atFrame = self.lastID()
        if atFrame == -oo:
            atFrame = 0
        # self.merge(other, atFrame=self.lastID()+timeOffset, beforeLayer=beforeLayer)
        self.merge(other, atFrame+timeOffset, beforeLayer)

    # Pretweens all layers. See Layer.pretween() and Actor.pretween() for more info.
    def pretween(self, ignoreMask=False):
        for layer in self.layers:
            layer.pretween(ignoreMask)

    # NOT IMPLEMENTED!
    # Returns a copy of the animation in which there are no gaps between
    # successive keyframes: all of the tweening has been done to "fill in
    # the gaps".
    def pretweened(self):
        raise NotImplementedError

        if not self.verify():
            raise Exception("Can't pretween the animation because it is not configured properly!")

        currentIndex = 0
        ani = self.copy()
        finalIndex = max(frm.index for layer in self.layers for frm in layer)

        for i in range(len(self.layers)):
            layer = self.layers[i]
            len_layer = len(layer)

            if len_layer == 0:
                ani.layers[i] = []
                continue

            timeline = [frm.index for frm in layer]
            newLayer = []
            keyID = 0
            keyframe = layer[0]
            for currentIndex in range(layer[0].index, layer[-1].index):
                # Update previous keyframe ID if needed.
                if keyID < len_layer-1 and currentIndex == layer[keyID+1].index:
                    keyID += 1
                    keyframe = layer[keyID]  # Grab latest keyframe
                    newLayer.append(keyframe)
                    continue

                # # Grab most recent keyframe
                # keyframe = layer[keyID]

                # Skip if the last keyframe is invisible or static
                # or within the keyframe's delay period.
                if not keyframe.visible or keyframe.static or \
                    currentIndex <= keyframe.index + keyframe.delay:
                    continue
                #     frm = blankFrame.copy()
                # # Make a copy of the previous keyframe if static
                # elif keyframe.static or keyID == len_layer-1:
                #     frm = keyframe.copy()
                # Tween as usual
                else:
                    t = morpho.numTween(0,1, currentIndex,
                        start=keyframe.index + keyframe.delay,
                        end=layer[keyID+1].index)
                    frm = layer[keyID].tween(layer[keyID+1], self.transition(t))

                frm.index = currentIndex
                newLayer.append(frm)
            # Append a copy of the final keyframe
            newLayer.append(layer[-1].copy())
            ani.layers[i] = newLayer  # Replace layer with newLayer

        return ani

    # Flattens an animation IN PLACE by merging all layers with the
    # bottommost layer. Note this means the camera actor of all other
    # layers will be ignored.
    # Optionally specify which layer indices to do.
    # Returns self.
    def flatten(self, start=0, end=-1):
        len_layers = len(self.layers)
        if len_layers == 0: return

        start = start % len_layers
        end = end % len_layers
        layer0 = self.layers[start]
        for i in range(start+1, end+1):
            layer0.merge(self.layers[i])
        self.layers = self.layers[:start] + [layer0] + self.layers[end+1:]
        return self

    # NOT IMPLEMENTED!
    # Returns a new animation which is the result of flattening layers
    # whose frames all have the same view.
    def flattened(self):
        raise NotImplementedError
        return
        ani = self.pretweened()
        layers = []
        firstIndex = ani.start
        finalIndex = ani.end

        for currentIndex in range(firstIndex, finalIndex+1):
            # now will contain all frames across all layers that have
            # index equal to the currentIndex.
            now = []  # This list is guaranteed non-empty
            for layer in ani.layers:
                # Skip empty layer
                if len(layer) == 0:
                    continue
                # Skip layers whose index windows don't contain currentIndex
                if not(layer[0].index <= currentIndex <= layer[-1].index):
                    continue
                # Grab the frame in this layer whose index == currentIndex.
                frm = layer[currentIndex-layer[0].index]
                # Double check this is right
                assert frm.index == currentIndex

                now.append(frm)

            # Merge the frames in now that have matching styles.
            frm = now[0]
            for frm in now:
                pass

        # for i in range(len(layers)-1):
        #     # Find a non-empty layer
        #     if len(layers[i]) == 0: continue
        #     view = layers[i][0]
        #     # If the frames in this layer DON'T have uniform views, skip.
        #     if not all(view==frm.view for frm in layers[i]):
        #         continue
        #     # If any frame in the next layer disagrees with the view, skip.
        #     if not all(view==frm.view for frm in layers[i+1]):
        #         continue
        #     # Ok, so these two layers share the same uniform view. Merge them!

    # Commits all of the time offsets of all the layers in the animation.
    # See Layer.commitOffset() for more info.
    def commitLayerOffsets(self):
        for layer in self.layers:
            layer.commitOffset()


    # Shifts the entire animation timeline forward by the given numFrames.
    # If viaOffset=False, then the timeline is shifted at the actor level
    # and leaves any existing layer time offsets unchanged.
    def shift(self, numFrames, viaOffset=False):
        # NOT FULLY VERIFIED YET!
        # It seems to work, but we are pending verification of the layer shift()
        # method to be sure! If you verify Layer.shift(), this method should be
        # good to go!
        numFrames = round(numFrames)
        if viaOffset:
            for layer in self.layers:
                layer.timeOffset += numFrames
        else:
            for layer in self.layers:
                layer.shift(numFrames)
                # layer.camera.shift(numFrames)
                # layer.start += numFrames
                # layer.end += numFrames
                # for actor in layer.actors:
                #     actor.shift(numFrames)

        # Shift firstIndex and finalIndex
        if self.firstIndex is not None:
            self.firstIndex += numFrames
        if self.finalIndex is not None:
            self.finalIndex += numFrames

        # Shift delays
        newDelays = {}
        for t in self.delays:
            newDelays[t+numFrames] = self.delays[t]
        self.delays = newDelays

    # Speed up all layers by the specified factor.
    # See Layer.speedUp() for more info.
    def speedUp(self, factor): #, center=0):
        # FUTURE: Implement different centers for animation speedUp()/slowDown()
        for layer in self.layers:
            layer.speedUp(factor, center=0, useOffset=True, ignoreMask=False)

        newDelays = {}
        for keyID in self.delays:
            delay = self.delays[keyID]
            newID = round(keyID/factor)
            newDelay = round(delay/factor) if delay != oo else oo

            # The complication is because dropping frame rates could cause
            # a collision among keyIDs. Add them instead of replacing!
            newDelays[newID] = newDelay if newID not in newDelays else newDelays[newID] + newDelay
        self.delays = newDelays

        # Adjust firstIndex and finalIndex
        if self.firstIndex is not None:
            self.firstIndex = round(self.firstIndex/factor)
        if self.finalIndex is not None:
            self.finalIndex = round(self.finalIndex/factor)

    # Equivalent to speedUp(1/factor). See speedUp() for more info.
    def slowDown(self, factor): #, center=0):
        self.speedUp(1/factor)

    # Updates the frame rate of the animation to the given fps,
    # but it adjusts the animation to preserve the original timing.
    # e.g. after changing the frame rate, a 10 second animation
    # will still be 10 seconds long.
    def newFrameRate(self, fps):
        factor = fps/self.frameRate
        self.slowDown(factor)
        self.frameRate = fps

    # Returns the lowest index amongst all keyfigures in all layers.
    def firstID(self):
        return min(layer.firstID(useOffset=True) for layer in self.layers) if len(self.layers) > 0 else 0
    # minkeyID = firstkeyID = firstID  # Synonyms for firstID()

    # Returns the highest index amongst all keyfigures in all layers.
    # By default, this also includes all mask layers, whether or not those
    # mask layers are included in the layer list.
    def lastID(self, ignoreMasks=False):
        return max(layer.lastID(useOffset=True, ignoreMask=ignoreMasks) for layer in self.layers) if len(self.layers) > 0 else 0
    # maxkeyID = lastkeyID = lastID  # Synonyms for lastID()

    # Return length of animation in units of frames.
    # Takes firstIndex and finalIndex into account and also
    # factors in finite animation delays between the
    # first and final indices. Ignores infinite delays.
    def length(self):
        start = self.firstID() if self.firstIndex is None else self.firstIndex
        end = self.lastID() if self.finalIndex is None else self.finalIndex
        delays = 0
        for index in self.delays:
            if start <= index <= end:
                delay = self.delays[index]
                if delay != oo:
                    delays += delay

        return end - start + 1 + delays

    # Returns the animation length in units of seconds.
    def seconds(self):
        return self.length() / self.frameRate

    # Convenience function sets the firstIndex attr to
    # the final key index.
    def gotoEnd(self):
        firstIndex = self.lastID()
        if firstIndex == oo:
            self.firstIndex = None
        else:
            self.firstIndex = firstIndex

    # NOT IMPLEMENTED!
    # Moves the firstIndex to the next key index.
    def nextkey(self):
        raise NotImplementedError

    # NOT IMPLEMENTED!
    # Moves the firstIndex to the previous key index.
    def prevkey(self):
        raise NotImplementedError

    # Convenience function makes the animation delay for the
    # given number of frames at whichever index is currently
    # its lastID. Defaults to infinity.
    # Optionally specify a timeOffset. Positive means after lastID,
    # negative means before lastID.
    def endDelay(self, f=oo, timeOffset=0):
        end = self.lastID() + timeOffset
        if end == -oo:
            raise IndexError("End of animation is undefined.")
        self.delays[end] = f

        # # Remove delay if it is shorter than half of a single frame.
        # if f < 0.5:
        #     self.delays.pop(end)

    # Makes the animation delay at its current final frame for
    # however long is needed until the specified frame f is reached.
    # This is usually equivalent to self.endDelay(f - self.length())
    def endDelayUntil(self, f=oo):
        f = f - self.length()
        if abs(f) != oo:
            f = round(f)

        if f < 0:
            raise ValueError(f"Until frame occurs {-f} frames before animation's end.")

        # If the animation already has a delay at its final frame,
        # add that delay to the current frame difference, so it's
        # taken into account when assigning the new end delay.
        end = self.lastID()
        if end == -oo:
            raise IndexError("End of animation is undefined.")
        if end in self.delays:
            currentEndDelay = self.delays[end]
            if currentEndDelay == oo and f != oo:
                raise Exception("Final frame already has infinitely long delay.")
            f += currentEndDelay

        self.endDelay(f)

    # Convert all infinite delays to the specified delay (units=frames).
    def finitizeDelays(self, delay):
        for time in self.delays:
            if self.delays[time] == oo:
                self.delays[time] = delay

    # Offsets the layers times by the given number of frames.
    # mation.offsetLayers(30)
    # Optionally, you can specify a single layer:
    # mation.offsetLayers(30, 5)
    # Optionally, you can specify a range:
    # mation.offsetLayers(30, 3, 9)
    # offsets the times of the third thru the ninth (inclusive) layers.
    def offsetLayers(self, time, start=None, end=None):
        if start is None and end is None:
            start = 0
            end = -1
        elif start is None:
            start = 0
        elif end is None:
            end = start

        start = start % len(self.layers)
        end = end % len(self.layers)

        for i in range(start, end+1):
            self.layers[i].timeOffset += time

    # Convenience function for user. Creates a pyglet window of specified (or not)
    # width and height and automatically associates the animation with that window.
    def setupWindow(self):
        width, height = self.windowShape
        if self.window is not None:
            raise Exception("Animation is still associated with an open window!")
        # screen = pg.window.get_platform().get_default_display().get_screens()[self.screen]
        screen = pg.canvas.get_display().get_screens()[self.screen]
        self.window = pg.window.Window(width, height,
            resizable=self.resizable, fullscreen=self.fullscreen,
            screen=screen
            )

    # Sets up the cairo context and prepares it for rendering to a pyglet window
    # NOTE: A lot of this code is mirrored in morpho.base.setupContext().
    # To reduce redundancy, consider calling that function in this one.
    def setupContext(self, flip=True):
        # Prepare data object to allow cairo contexts to be rendered
        # on the pyglet window.
        # I owe some of this code to stuaxo of github.
        # The code itself is taken from
        # stuaxo/cairo_pyglet.py
        # within github
        width, height = self.windowShape
        self.renderData = (ctypes.c_ubyte * (width*height*4))()
        stride = width*4
        surface = cr.ImageSurface.create_for_data(self.renderData, cr.FORMAT_ARGB32,
            width, height, stride
            )
        self.renderTexture = pg.image.Texture.create_for_size(pg.gl.GL_TEXTURE_2D, width, height, pg.gl.GL_RGBA)

        # Setup cairo context
        self.context = cr.Context(surface)
        # Setup text antialiasing
        if self.antialiasText:
            fontops = self.context.get_font_options()
            fontops.set_antialias(cr.Antialias.GOOD)
            self.context.set_font_options(fontops)
        # Put origin in lower-left
        if flip:
            self.context.translate(0, height)
            self.context.scale(1, -1)
        # Setup line join style
        self.context.set_line_join(cairoJointStyle[self.jointStyle])
        # Paint background
        self.clearContext()

    # Convenience function for user. Creates a cairo context of specified (or not)
    # width and height and automatically associates the animation with that context.
    def setupContext_old(self):
        width, height = self.windowShape
        if self.context is not None:
            raise Exception("Animation is still associated with an old context!")

        surface = cr.ImageSurface(cr.FORMAT_ARGB32, width, height)
        self.context = cr.Context(surface)

        # Put origin in lower-left
        self.context.translate(0, height)
        self.context.scale(1, -1)

        # Paint background
        self.clearContext()

    # Clears the current context and fills it with the background color
    def clearContext(self):
        clearContext(self.context, self.background, self.alpha)
        # # This extra stuff is to ensure that we can actually paint WITH
        # # transparency.
        # self.context.save()
        # self.context.set_source_rgba(*self.background, self.alpha)
        # self.context.set_operator(cr.OPERATOR_SOURCE)
        # self.context.paint()
        # self.context.restore()

    # Draws the animation in its active window at its current index.
    def draw(self):
        # print(self.currentIndex)
        # Clear the screen if we're drawing a brand new total frame
        # clearWindow(self.background)
        if self.window is not None:
            self.window.clear()
        self.clearContext()

        # Draw one layer at a time.
        for i in range(len(self.layers)):
            layer = self.layers[i]
            f = self.currentIndex - layer.timeOffset
            if not layer.visible or not(layer.start <= f <= layer.end):
                continue

            # Draw layer to current context
            layer.draw(f, self.context)

    # Export animation to file.
    # Can either be MP4, GIF animation, or PNG sequence depending on
    # the file extension given in the filepath.
    # Optional argument scale is a scale factor that scales the entire
    # animation window shape before exporting. Useful for downscaling an
    # animation while exporting test animations to speed up rendering.
    # Note: scaling seems to be done at the final pixel level, so specifying
    # scale > 1 will not actually increase the resolution of your animation.
    def export(self, filepath, scale=1):
        # # Handle non-trivial scale factor.
        # if scale != 1:
        #     # Save original window shape
        #     windowShape = self.windowShape[:]
        #     # Scale window shape and export
        #     self.windowShape = tuple(map(lambda x: round(scale*x), windowShape))
        #     self.export(filepath)
        #     # Restore original window shape.
        #     self.windowShape = windowShape
        #     return

        if scale > 1:
            warn("scale > 1 will not actually improve resolution.")

        # Get first and final indices if specified.
        if self.finalIndex is None:
            finalIndex = self.lastID()
        else:
            finalIndex = self.finalIndex

        if self.firstIndex is None:
            firstIndex = self.firstID()
        else:
            firstIndex = self.firstIndex

        # Remove trivial delays
        for t in list(self.delays):
            if self.delays[t] < 1:
                self.delays.pop(t)

        # Test for trivial exports
        if finalIndex < firstIndex:
            raise IndexError("finalIndex < firstIndex. Nothing to export!")
        if len(self.layers) == 0:
            raise ValueError("Animation contains no layers. Nothing to export!")

        # Get output directory and base filename and extension
        filepath = filepath.replace("/", os.sep).replace("\\", os.sep)
        filename = filepath.split(os.sep)[-1]
        extension = filename.split(".")[-1]
        filename = ".".join(filename.split(".")[:-1])  # Filename without extension
        Dir = os.sep.join(filepath.split(os.sep)[:-1])

        if extension.lower() in ("gif", "mp4"):
            # Make temp directory for PNG files
            tempDir = tempdir.replace("/", os.sep).replace("\\", os.sep) + os.sep + "Morpho-export"+exportSignature
            try:
                if os.path.isdir(tempDir):
                    shutil.rmtree(tempDir)
                os.makedirs(tempDir)
            except Exception:
                raise PermissionError

            try:

                # Prepare to compile GIF by defining gifDelays.
                # It describes the delay of each gif frame of animation.
                # It is equal to 1/frameRate unless there's an animation delay.

                # Initialize gifDelays to just be based on the framerate
                # for all frames
                gifDelays = [1.0/self.frameRate]*(finalIndex - firstIndex + 1)

                # Look into the mation.delays dict to decide what
                # indices of gifDelays need to be changed to.
                for index in self.delays:
                    # Skip if delay index is out of range OR
                    # the delay is only one frame long or shorter.
                    if not(firstIndex <= index <= finalIndex) or self.delays[index] <= 1:
                        continue

                    # Update gifDelays with the delay value
                    # (converted into units of seconds)
                    gifDelays[index - firstIndex] += self.delays[index]/self.frameRate

                if extension.lower() == "mp4":
                    # Check for infinite delays
                    if max(gifDelays) == oo:
                        raise ValueError("Animation contains infinitely-long pauses. You must finitize them before exporting to mp4.")

                # Export PNG sequence to temp dir
                print("Exporting temporary PNG sequence...")
                self.export(tempDir + os.sep + filename.replace("'", "_") + ".png", scale)

                if extension.lower() == "gif":
                    # Compile GIF with delays
                    # Make and optimize the GIF.
                    print("Compiling frames into GIF...")
                    morpho.giffer.makegif(directory=tempDir, saveas=filepath, duration=gifDelays)
                    print("Optimizing GIF...")
                    morpho.giffer.optimizegif(filepath)
                elif extension.lower() == "mp4":
                    # Generate concat demuxer instructions
                    demux = []
                    for n in range(firstIndex, finalIndex+1):
                        demux.append("file '" + tempDir + os.sep + filename.replace("'", "_") + "_" +
                            int2fixedstr(n-firstIndex, digits=numdigits(finalIndex-firstIndex))
                        + ".png'")
                        demux.append("duration " + str(gifDelays[n-firstIndex]))
                    demux.append(demux[-2])  # Needed to handle end delay for some reason
                    demux = "\n".join(demux)
                    with open(tempDir + os.sep + "demux.txt", "w") as file:
                        file.write(demux)

                    # Use ffmpeg to create initial mp4 via concat
                    # cmd = [
                    #     "ffmpeg",
                    #     "-y",  # Overwrite existing file without warning
                    #     "-safe", "0",  # Don't complain too much about filenames
                    #     "-f",
                    #     "concat",
                    #     "-i", tempDir + os.sep + "demux.txt",
                    #     "-vsync", "vfr",
                    #     "-vcodec", "libx264",
                    #     "-crf", str(ffmpegConfig["crf"]),  # Quality 18 generally highest quality
                    #     "-pix_fmt", "yuv420p",
                    #     tempDir + os.sep + "temp.mp4"
                    # ]

                    cmd = [
                        ffmpeg,
                        "-y",  # Overwrite existing file without warning
                        "-safe", "0",  # Don't complain too much about filenames
                        "-f",
                        "concat",
                        "-i", tempDir + os.sep + "demux.txt",
                        # "-vsync", "vfr",
                        # "-vf", "fps="+str(self.frameRate),
                        "-r", str(self.frameRate),
                        "-vcodec", "libx264",
                        "-crf", str(ffmpegConfig["crf"]),  # Quality 18 generally highest quality
                        "-pix_fmt", "yuv420p",
                        # tempDir + os.sep + "temp.mp4"
                        filepath
                    ]
                    print("Creating mp4...")
                    sp.call(cmd)
                    print()

                    # # Re-encode the mp4 to make it easier to play and manipulate.
                    # cmd = [
                    #     "ffmpeg",
                    #     "-y",
                    #     "-r", str(self.frameRate),
                    #     "-i", tempDir + os.sep + "temp.mp4",
                    #     "-vcodec", "libx264",
                    #     filepath
                    # ]
                    # print("Re-encoding...")
                    # sp.call(cmd)
                    # print()

            finally:
                # Clean up temp dir
                print("Cleaning up temp directory...")
                try:
                    if os.path.isdir(tempDir):
                        shutil.rmtree(tempDir)
                except Exception:
                    raise PermissionError
                print("DONE!")

        elif extension.lower() == "png":
            if scale != 1:
                # Make a fake secondary animation which will house the scaled version
                # of each frame.
                anim2 = Animation()
                anim2.windowShape = tuple(round(scale*coord) for coord in self.windowShape)
                anim2.background = self.background
                anim2.alpha = self.alpha

                anim2.setupContext(flip=False)
                anim2.context.scale(scale, scale)

            # Prepare to "play" animation
            self.currentIndex = firstIndex
            self.setupContext()
            while self.currentIndex <= finalIndex:
                self.draw()

                # If the animation is just one frame, don't
                # label the file by frame number.
                if firstIndex == finalIndex:
                    imgfile = Dir+os.sep+filename+".png"
                else:
                    imgfile = Dir+os.sep+filename \
                        + "_" + int2fixedstr(self.currentIndex-firstIndex,
                            digits=numdigits(finalIndex-firstIndex)) \
                        + ".png"

                if scale == 1:
                    self.context.get_target().write_to_png(imgfile)
                else:
                    # # Setup a modified standard context and scale it.
                    # anim2.setupContext()
                    # anim2.context = cr.Context(anim2.context.get_target())
                    # anim2.context.scale(scale, scale)

                    # Grab target surface from real animation and set it as source
                    # then paint it onto the secondary animation and export!
                    anim2.context.set_source_surface(self.context.get_target())
                    anim2.context.paint()
                    anim2.context.get_target().write_to_png(imgfile)

                self.currentIndex += 1

            # Clean up animation variables
            self.resetMation()

        # Unrecognized type. Throw error
        else:
            raise Exception("Unrecognized file type to export.")

    # Plays the animation in a separate window or possibly fullscreen.
    #
    # Optional arguments "window" and "autoclose" are mostly just holdovers
    # from a much older version of Morpho, and should probably just be left
    # alone. In the future, one or both of them may be removed.
    #
    # KNOWN ISSUE: Morpho may sometimes crash if you attempt to call play()
    # multiple times in a single run of your code. To avoid, make sure you
    # only play one animation per execution of your code.
    def play(self, window=None, autoclose=False):
        # Verify the animation can be played.
        # if not self.verify():
        #     raise Exception("Animation can't be played because it is not configured properly!")
        self.sanityCheck()

        if self.finalIndex is None:
            finalIndex = self.lastID()
        else:
            finalIndex = self.finalIndex

        if self.firstIndex is None:
            firstIndex = self.firstID()
        else:
            firstIndex = self.firstIndex

        self.currentIndex = firstIndex

        # Remove trivial delays.
        # Actually, this clause may no longer be necessary since the delays
        # dict was re-implemented using IntDict which should prevent
        # 0 delays from being entered. Consider removing in future.
        for t in list(self.delays):
            if self.delays[t] < 1:
                self.delays.pop(t)

        # # Set background color and alpha
        # BG = self.background

        # Handle unspecified window parameter
        if window is None:
            # If animation is just paused, treat play() like resume()
            if self.paused:
                self.resume()
                return

            # If the animation has no associated window, set up one.
            if self.window is None: self.setupWindow()
        else:
            # Throw error if the animation is already associated to an
            # open window, and the user is trying to play it in a different
            # window without first closing the original.
            if self.window is not None and self.window != window:
                raise Exception("Animation already associated with an open window. Close it first before reassociating.")
            self.window = window

        self.active = True
        self.window.switch_to()  # Focus on this window for rendering.

        # Setup context for rendering to a pyglet window
        self.setupContext()


        # This function gets called on every frame draw.
        def update(dt, mation=self, finalIndex=finalIndex): #, BG=BG):

            # Increment current index immediately!
            mation.currentIndex += 1

            # Handle animation returning after delay.
            if mation.delay > 0:
                pg.clock.unschedule(mation.update)
                pg.clock.schedule_interval(mation.update, 1.0/mation.frameRate)
                mation.delay = 0
                # self.currentIndex -= 1  # This is a hack to overcome a weird glitch.

            # Handle pauses.
            mation.doDelay()

            # If we've reached the end of the animation, either
            # stop or autoclose.
            if mation.currentIndex >= finalIndex:
                mation.currentIndex = finalIndex
                # if mation.keyframes[-1].visible:
                #     mation.keyframes[-1].draw(mation.view, mation.window)
                mation.active = False
                pg.clock.unschedule(mation.update)
                if autoclose:
                    pg.app.exit()
                    mation.window.close()
                    mation.resetMation()

                # Print latest runtime split
                if morpho.DEBUG_MODE:
                    print("Runtime Split:", toc(), "seconds")
                    print()

        # Bind updater to the animation so it can be found later.
        self.update = update

        @self.window.event
        def on_draw(mation=self):

            # Draw to the given context
            mation.draw()

            # Render the context to the window
            # I owe much of this code to stuaxo of github.
            # The code itself is taken from
            # stuaxo/cairo_pyglet.py
            # within github
            width, height = self.windowShape
            self.window.clear()

            pg.gl.glEnable(pg.gl.GL_TEXTURE_2D)

            pg.gl.glBindTexture(pg.gl.GL_TEXTURE_2D, self.renderTexture.id)
            pg.gl.glTexImage2D(
                pg.gl.GL_TEXTURE_2D, 0, pg.gl.GL_RGBA, width, height, 0, pg.gl.GL_BGRA,
                pg.gl.GL_UNSIGNED_BYTE, self.renderData
                )

            pg.gl.glBegin(pg.gl.GL_QUADS)
            pg.gl.glTexCoord2f(0.0, 1.0)
            pg.gl.glVertex2i(0, 0)
            pg.gl.glTexCoord2f(1.0, 1.0)
            pg.gl.glVertex2i(width, 0)
            pg.gl.glTexCoord2f(1.0, 0.0)
            pg.gl.glVertex2i(width, height)
            pg.gl.glTexCoord2f(0.0, 0.0)
            pg.gl.glVertex2i(0, height)
            pg.gl.glEnd()


        # Reset animation when closed.
        @self.window.event
        def on_close(mation=self):
            # Reset active animation attributes
            mation.resetMation()

        # If clicked, pause the animation.
        # If at the end of the animation, clicking restarts it.
        @self.window.event
        def on_mouse_press(X, Y, button, modifiers, mation=self):
            # Replay animation if clicked after animation finishes
            if not mation.active:
                mation.active = True
                mation.paused = False
                # mation.delay = 0
                mation.currentIndex = mation.firstIndex if mation.firstIndex is not None else mation.firstID()
                # mation._keyID = listfloor([frm.index for frm in self.keyframes],
                #     mation.currentIndex)
                # mation._keyIDs = [listfloor([frm.index for frm in layer],
                #     mation.currentIndex) for layer in mation.layers]

                # blankFrame.draw(mation.view, mation.window)

                # Only schedule updater for animations with more than 1 frame.
                if finalIndex - firstIndex > 0:
                    # If the first frame is a delay frame, manually call
                    # the doDelay() method because the updater won't see it.
                    if self.currentIndex in self.delays:
                        self.doDelay()
                    else:
                        # Draw frames at specified framerate
                        pg.clock.schedule_interval(self.update, 1.0/self.frameRate)
                else:
                    mation.active = False
            elif mation.paused:
                mation.resume()
            else:
                mation.pause()

            # Print mouse coordinates if a locater layer is specified.
            if mation.locaterLayer is not None:
                # Search the layer list if given an int
                if isinstance(mation.locaterLayer, int) or isinstance(mation.locaterLayer, float):
                    view = mation.layers[int(mation.locaterLayer)].viewtime(mation.currentIndex)
                else:
                    # Treat it as an actual layer object
                    view = mation.locaterLayer.viewtime(mation.currentIndex)

                z = physicalCoords(X, Y, view, mation.context)

                # Round the real and imag components of z if needed.
                if self.clickRound is not None:
                    x,y = z.real, z.imag
                    x = round(x, self.clickRound)
                    y = round(y, self.clickRound)
                    z = x + y*1j

                # Copy to the clipboard if needed
                if self.clickCopy:
                    pyperclip.copy(str(z))

                print((z.real, z.imag))

                # sign = " + " if z.imag >= 0 else " - "
                # print(z.real, sign, abs(z.imag), "j", sep="")

            tic()  # Reset runtime timer


        # Schedule drawing at the specified frame rate.
        # Only schedule the updater for animations that are more
        # than a single frame.
        if finalIndex - firstIndex > 0:
            # If the first frame is a delay frame, manually call
            # the doDelay() method because the updater won't see it.
            if self.currentIndex in self.delays:
                self.doDelay()
            else:
                # Draw frames at specified framerate
                pg.clock.schedule_interval(self.update, 1.0/self.frameRate)
        else:
            self.active = False

        tic()  # Start runtime timer
        pg.app.run()
        pg.app.exit()


    def pause(self):
        if not self.active: return
        self.paused = True
        self.delay = 0
        pg.clock.unschedule(self.update)

        if self.clickTime != "none":
            if self.clickTime == "second" or self.clickTime == "seconds":
                print("Time:", self.currentIndex/self.frameRate)
            else:
                print("Frame:", self.currentIndex)
            if morpho.DEBUG_MODE:
                print("Runtime Split:", toc(), "seconds")
            print()

    def resume(self):
        if not self.active: return
        self.paused = False
        pg.clock.schedule_interval(self.update, 1.0/self.frameRate)
        tic()  # Reset runtime timer

    # For use in the play() method.
    # Checks if the current index is a delay index.
    # If so, it implements the delay.
    def doDelay(self):
        if self.currentIndex in self.delays:
            delay = self.delays[self.currentIndex]
            if delay == oo:
                self.pause()
            elif delay > 0:
                self.delay = delay
                pg.clock.unschedule(self.update)
                pg.clock.schedule_interval(self.update, \
                    delay/self.frameRate)

    def resetMation(self):
        # Reset active animation attributes
        self.active = False
        self.window = None
        self.context = None
        self.update = None
        self.paused = False
        self.currentIndex = 0
        self._keyIDs = None  # This var is only used once play() is called.

    # This function verifies whether or not the animation is playable.
    # It's probably not perfect yet, so animations could still break
    # even if this function returns True, but it may help a little.
    def verify(self):
        try:
            self.sanityCheck()
        except Exception:
            return False
        return True

    # Identical to verify() except that instead of returning a boolean,
    # it will actually raise an appropriate exception if it detects
    # something wrong.
    def sanityCheck(self):
        # Check strict increasingness of the keyframe indices
        for layer in self.layers:
            for actor in layer.actors:
                if not strictly_increasing(actor.keyIDs):
                    raise KeyError("At least one actor's keyIDs list is not in increasing order.")

        # Check that layer mask pointers do not form a loop
        for layer in self.layers:
            if layer.maskChainFormsLoop():
                raise MaskConfigurationError("The mask chain of the layers form a loop.")
        # masks = set()
        # for n in range(len(self.layers)):
        #     layer = self.layers[n]
        #     if layer.mask is not None:
        #         if layer.mask in masks:
        #             raise MaskConfigurationError("The mask pointers of the layers form a loop.")
        #         masks.add(layer.mask)

        return

# Special modified dict for the delays dict.
# Rounds all values to be positive ints (except for +inf).
# Ignores zeros, and throws errors at negatives (after rounding).
class IntDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Use modified __setitem__() to make all the values correct
        for key in list(self.keys()):
            self[key] = self[key]
            # # Remove zeros
            # if self[key] < 1:
            #     self.pop(key)

    def __setitem__(self, key, value):
        # Given finite value, round it to an int.
        if abs(value) != oo:
            value = round(value)

        # Don't record zero delays. Delete key if it exists.
        if value == 0:
            if key in self:
                self.pop(key)
            return
        # Negative delays are disallowed.
        elif value < 0:
            raise ValueError(f"Delay values cannot be negative: {value}")

        super().__setitem__(key, value)

### HELPERS ###

# Draws an ellipse at the point (x,y) with width 2a
# and height 2b.
# Optionally you can specify dTheta to adjust the angle
# increment in which each vertex of the ellipse is drawn.
# Defaults to 5 degrees.
#
# Importantly: OpenGL_ellipse() assumes you have already specified
# the fill color and stroke width of the ellipse beforehand by
# calling pyglet.gl.glLineWidth() and pyglet.gl.glColor4f()
DEG2RAD = math.pi/180
def OpenGL_ellipse(x, y, a, b, dTheta=10):
    pg.gl.glLineWidth(1)
    pg.gl.glBegin(pyglet.gl.GL_TRIANGLE_FAN)
    for th in range(0,360, dTheta):
        th *= DEG2RAD
        pg.gl.glVertex2f(x + a*math.cos(th), y + b*math.sin(th))
    pg.gl.glEnd()

# Creates a window that animations can take place in.
def createWindow(width=800, height=800):
    return pg.window.Window(width, height)

# Clears the active pyglet window to prepare for a
# new frame to be drawn. More precisely, it erases
# everything currently on the window and replaces it
# with this frame's background color.
# In the future, I think this function will be obsoleted,
# or at least need to be modified.
def clearWindow(RGBA=None):
    if RGBA is None:
        R,G,B,A = BG
    else:
        R,G,B,A = RGBA
    pg.gl.glClearColor(R,G,B,A)
    pg.gl.glClear(pg.gl.GL_COLOR_BUFFER_BIT)

BG = (0,0,0,0)

# Converts an int into a string of fixed length given by the
# parameter digits. Works by prepending zeros if the string
# is too short.
def int2fixedstr(n, digits=3):
    str_n = str(n)
    return "0"*(digits-len(str_n)) + str_n

# Returns number of digits required to represent the integer
# in the given base (default=10)
def numdigits(n, base=10):
    n = abs(int(n))
    d = 0
    while n > 0:
        n = n // base
        d += 1
    return max(1,d)

# Tests whether a list is strictly increasing.
# Thanks to User 6502 on StackOverflow.
# https://stackoverflow.com/a/4983359
def strictly_increasing(L):
    return all(x<y for x, y in zip(L, L[1:]))
