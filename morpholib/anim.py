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
import morpholib.tools.dev
from morpholib.tools.dev import BoundingBoxFigure, makesubcopies, listselect, \
    _SubAttributeManager, _InPlaceSubAttributeManager, AmbiguousValueError
from morpholib.tools.img import surfaceSave

# Backward compatibility because these functions used to live in anim.py
from morpholib import screenCoords, physicalCoords, \
    pixelWidth, physicalWidth, pixelHeight, physicalHeight, \
    setupContext, clearContext, cairoJointStyle, object_hasattr, \
    applyFigureModifier

import math, cmath
import numpy as np
import os, tempfile, ctypes
import subprocess as sp
import pyperclip
from warnings import warn
from tempfile import TemporaryDirectory
from collections.abc import Iterable

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

class FrameMergeError(MergeError):
    pass

class LayerMergeError(MergeError):
    pass

class MaskConfigurationError(Exception):
    pass


### CLASS DECORATORS ###

# Decorator for Frame tween methods that implements subfigure
# tweening and splitting automatically for tween methods that
# ignore the `figures` tweenable.
def handleSubfigureTweening(tweenmethod):
    def splitter(t, beg, mid, fin):
        # First use the original splitter to split the tween method
        if morpho.tweenSplittable(tweenmethod):
            tweenmethod.splitter(t, beg, mid, fin)

        # Split subfigure tween methods
        for subbeg, submid, subfin in zip(beg.figures, mid.figures, fin.figures):
            # Split the tween methods of corresponding subfigure triplets
            if morpho.tweenSplittable(subbeg.tweenMethod):
                subbeg.tweenMethod.splitter(t, subbeg, submid, subfin)

    @morpho.TweenMethod(splitter=splitter)
    def wrapper(self, other, t, *args, **kwargs):
        if len(self.figures) != len(other.figures):
            raise ValueError("Can't tween Frames with different subfigure counts.")

        # Apply original tween method and assume it doesn't
        # affect the `figures` tweenable.
        twfig = tweenmethod(self, other, t, *args, **kwargs)

        # Tween subfigures
        twfig_figures = twfig.figures  # Saves on tweenable getattr time
        for n, (fig1, fig2) in enumerate(zip(self.figures, other.figures)):
            # Skip any static subfigures
            if fig1.static: continue
            twfig_figures[n] = fig1.tweenMethod(fig1, fig2, t)

        return twfig
    return wrapper

### CLASSES ###

# Enables Frame-like figures to apply an action to its subfigures
# via the syntax
#       myfilm.subaction.myaction(..., substagger=5)
# `myaction` should be a *standard* actor action, meaning it
# only modifies the latest keyfigure and possibly adds new
# future keyframes, as well as preserving a keyframe at the
# original latest keyframe. All standard actions like
# fadeIn/Out(), etc. follow this standard.
class _SubactionSummoner(object):
    def __init__(self, actor):
        self.actor = actor

    # Apply actor actions to subfigures in a Frame-like figure,
    # along with a substagger option. A subset of subfigures can
    # be selected by passing in indices/slices into the `select`
    # keyword parameter.
    @staticmethod
    def subaction(action, film, *args,
        substagger=0, select=None, **kwargs):

        now = film.lastID()

        substagger = aslist(substagger)

        if select is None:
            select = sel[:]
        elif isinstance(select, Iterable):
            select = tuple(select)

        initframe = film.last().copy()

        # Get a dict containing the selected indices
        selectedIndices = initframe._selectionMap(select)

        subactors = []
        for n,fig in enumerate(initframe.figures):
            fig_orig = fig
            fig = fig.copy()

            # Create a subactor that contains a copy of the full
            # history of the nth subfigure in the film.
            subactor = morpho.Actor(type(fig))
            # The `min()` expression here is to deal with the case
            # where the latest keyfigure has more subfigures than a
            # past keyfigure. In this case, the last subfigure of
            # the past keyfigure is used to match up with the extra
            # subfigures of the latest keyfigure.
            subactor.timeline = {f : keyfig.figures[min(n, len(keyfig.figures)-1)].copy() for f, keyfig in film.timeline.items()}
            subactor.update()
            if n in selectedIndices:
                # Transition is set to uniform because transitions are ignored
                # in frames and we want Actor.zip() to respect that.
                fig.transition = morpho.transitions.uniform
                if initframe.transition != morpho.transitions.uniform:
                    fig.tweenMethod = morpho.transitions.incorporateTransition(initframe.transition, fig.tweenMethod)
                # fig.static = False
                action(subactor, *args, **kwargs)
                # Restore tween method and transition to original
                # values for the final keyfigure in the subactor
                subactor.last().set(
                    tweenMethod=fig_orig.tweenMethod,
                    transition=fig_orig.transition
                    )
            # Remove past keyframes as they should not be
            # modified by a standard action.
            subactor = subactor.segment(start=now, rezero=True, seamless=False)
            subactors.append(subactor)

        # Apply substagger to the affected subactors
        offset = 0
        for count, n in enumerate(selectedIndices):
            subactors[n].shift(offset)
            offset += substagger[count % len(substagger)]

        # Delete current final keyfigure so that insertion
        # will overwrite it.
        film.delkey(now)
        template = initframe.copy().set(figures=[])
        zipped = morpho.Actor.zip(subactors, template=template)
        film.insert(zipped, atFrame=now)

    def __getattr__(self, name):
        action = getattr(morpho.action, name)

        return self.makeSubaction(action)

    def makeSubaction(self, action):
        def subaction(*args, substagger=0, **kwargs):
            return self.subaction(action, self.actor, *args, substagger=substagger, **kwargs)

        return subaction

    # The subaction property can be called by supplying
    # an actor action and other args/kwargs. This allows
    # one to use an unregistered action with `subaction`.
    def __call__(self, action, *args, **kwargs):
        return self.subaction(action, self.actor, *args, **kwargs)

# Enables MultiFigures to apply an action to its subfigures
# via the syntax
#   myfilm.subaction.myaction(..., substagger=5)
# Note that if substagger or select is used, the MultiFigure
# will have its toplevel tween method set to Frame.tweenLinear
# for the duration of the action.
class _SubactionSummonerForMultiFigures(_SubactionSummoner):
    @staticmethod
    def subaction(action, film, *args, substagger=0, select=None, **kwargs):
        # Need to temporarily use Frame's tweenLinear because
        # _SubactionSummoner.subaction() expects the toplevel
        # tween method to follow standard subfigure tweening rules,
        # specifically in that subfigure tween methods are used.
        # MultiFigure tween methods usually ignore subfigure
        # tween methods, meaning subaction() won't work correctly.
        origTweenMethod = film.last().tweenMethod
        film.last().tweenMethod = Frame.tweenLinear
        _SubactionSummoner.subaction(action, film, *args,
            substagger=substagger, select=select, **kwargs)
        film.last().tweenMethod = origTweenMethod

# Frame class. Groups figures together for simultaneous drawing.
# Syntax: myframe = Frame(list_of_figures, **kwargs)
#
# Note that arbitrary keyword arguments can be supplied to the
# Frame constructor, in which case they will be interpreted as
# name-subfigure pairs and will be appended to the end of the
# given figure list, but the associated names will be registered.
# See `Frame.setName()` for more info.
#
# TWEENABLES
# figures = List of figures in the frame. For tweening to work,
#           the figures list of both Frames must have corresponding
#           figure types. e.g. Frame([point, path]) can only tween with
#           another Frame([point, path]).
# origin = Translation value (complex number). Default: 0.
#
# If the frame consists of subfigures of exactly the same type, the
# subfigure attributes can be set all at once using the "all" syntax:
#   EXAMPLE: myframe.all.pos = 3+4j
# However, in-place operations can't be depended on to work
#   EXAMPLE: myframe.all.pos += 2j   # Doesn't dependably work
# This can be used to access subfigure attributes as well, but will
# throw an error if the value of the accessed subattribute is
# different across different subfigures
#   EXAMPLE: commonPosition = myframe.all.pos
#
# Note that tweening a frame via tween() will tween the frame's
# attributes along with its underlying figure list, but calling
# a frame's tween method directly (via defaultTween) will only tween
# the frame's attributes and NOT the underlying figure list.
#
# Note that subfigure transition functions are ignored when
# tweening a Frame. This behavior can still be circumnavigated
# by incorporating transitions directly into the subfigure
# tween methods using `morpho.transitions.incorporateTransition()`.
class Frame(BoundingBoxFigure):
    def __init__(self, figures=None, /, **kwargs):
        # By default, do what the superclass does.
        # morpho.Figure.__init__(self)
        super().__init__()

        if figures is None:
            figures = []
        elif not isinstance(figures, list):
            figures = list(figures)
        figures.extend(kwargs.values())

        self.Tweenable("figures", figures, tags=["figures", "notween"])
        self.Tweenable("origin", 0, tags=["complex", "nofimage"])
        # background = morpho.Tweenable(
        #     name="background", tags=["vector"], value=[0,0,0])
        # view = morpho.Tweenable(
        #     name="view", tags=["view"], value=[-5,5, -5,5])

        # # Attach tweenable attributes
        # self.update([figures])

        # dict maps name strings to figure list index positions.
        self.NonTweenable("_names", {})

        self.setName(**kwargs)

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

    @property
    def figures(self):
        return self._state["figures"].value

    @figures.setter
    def figures(self, value):
        if not isinstance(value, list):
            value = list(value)
        self._state["figures"].value = value

    @property
    def numfigs(self):
        return len(self.figures)

    # Computes the bounding box of the entire Frame,
    # assuming all of its subfigures have implemented `box()`.
    # Returned as [xmin, xmax, ymin, ymax].
    # Additional arguments are passed to the box() methods
    # of subfigures.
    def box(self, *args, raw=False, **kwargs):
        shift = 0 if raw else self.origin
        return shiftBox(totalBox(subfig.box(*args, **kwargs) for subfig in self.figures), shift)

    # Modified because checking if the two figure lists are
    # equal via vanilla Python list equality will not work.
    # Instead, it goes thru the figure lists of self and other
    # and checks if all corresponding figures appear equal.
    def _appearsEqual(self, other, ignore=(), *args,
        compareNonTweenables=False, compareSubNonTweenables=False, **kwargs):

        ignore = set(ignore)
        self_figures = self.figures
        other_figures = other.figures
        return morpho.Figure._appearsEqual(self, other, ignore=ignore.union({"figures"}), *args, compareNonTweenables=compareNonTweenables, **kwargs) and \
            len(self_figures) == len(other_figures) and \
            all(self_subfig._appearsEqual(other_subfig, ignore, *args, compareNonTweenables=(compareSubNonTweenables or compareNonTweenables), **kwargs) for self_subfig, other_subfig in zip(self_figures, other_figures))

    # # Returns True iff the "stylistic" attributes of two frames match
    # # i.e. their views, indices, and defaultTweens match.
    # # This can be used as a criterion on whether or not merging two frames
    # # can be done without affecting the other frame.
    # def matchesStyle(self, other):
    #     return self.defaultTween==other.defaultTween

    # Allows actor actions to be applied to subfigures with a
    # substagger parameter.
    @staticmethod
    def subaction(actor):
        return _SubactionSummoner(actor)

    # Append the figure list of other to self in place.
    # Also adds in the named subfigures of other into self's registry,
    # but skips any duplicate names so that self's names are
    # not overwritten.
    #
    # If given a list/tuple of figures, merges them one by one.
    #
    # By default, the figures are appended to the end of the figure list,
    # but this can be changed by passing in a value to the `beforeFigure`
    # parameter (either an index value or a figure object).
    def merge(self, other, beforeFigure=oo):

        # Handle case that beforeFigure is an actual Figure object
        if isinstance(beforeFigure, morpho.Figure):
            if beforeFigure not in self.figures:
                raise FrameMergeError("Given 'beforeFigure' is not in this Frame!")
            else:
                beforeFigure = self.figures.index(beforeFigure)
        elif abs(beforeFigure) != oo:
            beforeFigure = round(beforeFigure)

        # Handle abnormal indices
        if beforeFigure > len(self.figures):
            beforeFigure = len(self.figures)
        elif beforeFigure < 0:
            beforeFigure %= len(self.figures)

        # # Commit the transforms of `other` if it's transformable
        # # so that the toplevel transformations are not lost
        # # after the merge.
        # if isinstance(other, morpho.combo.TransformableFrame):
        #     # Don't put the following line in:
        #     #   other.origin = other.origin - self.origin
        #     # It's tempting to include this line for when merging
        #     # a Frame with a TFrame, but it will cause problems when
        #     # merging a TFrame with another TFrame because TFrame.merge()
        #     # calls Frame.merge()
        #     other.commitTransforms()

        if isinstance(other, (list, tuple)):
            # Convert beforeFigure index value into equivalent negative or
            # infinite form so that we don't have to update its value after
            # each merge in the for loop below.
            if beforeFigure == len(self.figures):
                beforeFigure = oo
            else:
                beforeFigure -= len(self.figures)
            for fig in other:
                self.merge(fig, beforeFigure)
            return self
        elif not isinstance(other, Frame) and isinstance(other, morpho.Figure):
            # Implicitly convert non-Frame figures into a singleton Frame
            # of the same subtype as self and then merge as normal.
            other = type(self)([other])

        # Shift ahead all indices in the _names dict that are
        # ahead or equal to beforeFigure index
        shift = len(other.figures)
        for name, selfindex in self._names.items():
            if selfindex >= beforeFigure:
                self._names[name] += shift

        # Append other's name registry to self's (skipping duplicate names),
        # but shift the index values by the number of names in self's
        # registry.
        for name, index in other._names.items():
            # Skip any duplicate names found in other's registry
            if name not in self._names:
                self._names[name] = index + beforeFigure

        # Extend the figure list
        for otherfig in reversed(other.figures):
            self.figures.insert(beforeFigure, otherfig)
        return self

    @property
    def all(self):
        return _SubAttributeManager(self.figures, self)

    # Version of .all that is only meant to be used for in-place
    # operations like `+=`.
    # Example: myframe.iall[:3].pos += 2j
    @property
    def iall(self):
        return _InPlaceSubAttributeManager(self.figures, self)

    def _select(self, index, *, _asFrame=False, _iall=False):
        seldict = self._selectionMap(index)
        selection = list(seldict.values())

        # Do an empty initialization first followed by assigning
        # to `figures` so that `select[]` does not assume anything
        # about how type(self).__init__() works.
        frm = type(self)()
        frm.figures = selection
        frm._updateFrom(self, ignore={"figures", "_names"})
        if _asFrame:
            # If self has named subfigures, ensure the names transfer over
            # to the returned subframe.
            if len(self._names) > 0:
                # Dict mapping selected indices in self to indices in the subframe.
                # Eliminates the need to use list.index() which is slow.
                subIDpositions = {subID : n for n, subID in enumerate(seldict.keys())}

                # Go thru self's names dict and map names for subfigures
                # that self has in common with the subframe
                for name, subID in self._names.items():
                    if subID in seldict:
                        frm._names[name] = subIDpositions[subID]
            return frm
        elif _iall:
            return _InPlaceSubAttributeManager(frm.figures, self)
        else:
            return _SubAttributeManager(frm.figures, self)

    def _iselect(self, *args, **kwargs):
        return self._select(*args, _iall=True, **kwargs)

    # Returns a dict mapping indices in the figure list
    # to their figures. Mainly for internal use by the
    # _select() method.
    def _selectionMap(self, index):
        return listselect(self.figures, index)


    # Allows the modification of a subset of the subfigures
    # with the syntax:
    #   myframe.select[1:4].set(...)
    # You can also specify a choice function. That is, a function
    # that takes a subfigure as input and returns a boolean on
    # whether that figure should be selected.
    #   myframe.select[lambda fig: fig.width==0].set(...)
    @property
    def select(self):
        return morpho.tools.dev.Slicer(getter=self._select)

    # Version of .select[] that is only meant to be used for in-place
    # operations like `+=`.
    # Example: myframe.iselect[:3].pos += 2j
    @property
    def iselect(self):
        return morpho.tools.dev.Slicer(getter=self._iselect)

    def _sub(self, index):
        return self._select(index, _asFrame=True).copy()

    # Extracts a subframe of subfigures from the Frame.
    # Subfigures can be selected either via slice notation
    #   subframe = myframe.sub[1:4]
    # Or by choice function:
    #   subframe = myframe.sub[lambda fig: fig.width==0]
    # Note that the subfigures selected will be copied.
    @property
    def sub(self):
        return morpho.tools.dev.Slicer(getter=self._sub)

    def _cut(self, index):

        # Using _select() instead of sub[] here because
        # we do NOT want to make copies of the subfigures
        # in this case.
        subframe = self._select(index, _asFrame=True)
        figures = list(self.figures)
        for subfig in subframe.figures:
            while subfig in figures:
                figures.remove(subfig)
        self.figures = figures

        # Remove cut subfigure names from self's names dict
        for name in subframe._names:
            del self._names[name]

        return subframe

    # Basically the same as sub[], but it also removes the selected
    # subfigures from self's figure list. The selected subfiures
    # are NOT copied since they are removed from self's figure list.
    @property
    def cut(self):
        return morpho.tools.dev.Slicer(getter=self._cut)


    # Partitions the Frame into a Frame of subframes
    # splitting at the given list of indices.
    #
    # For example, `frm.partition([3, 6, 10])`
    # will return a new Frame consisting of the 4 subframes
    # frm.sub[:3], frm.sub[3:6], frm.sub[6:10], frm.sub[10:]
    # in that order.
    #
    # Negative indices will be interpreted cyclically.
    # Index values can also be filter functions, in which
    # case they will be converted into the indices of the first
    # subfigures they match in the partition so far. This is done
    # relative to subfigures that haven't been partitioned yet,
    # so, for example, passing in two identical filter functions
    # will result in partition points at the first match and the
    # second match. An error is thrown if no matches are found
    # at any point in the process.
    #
    # Note that partition() will leave the original Frame figure
    # that called it unchanged, and will return a new Frame
    # of copies of the underlying subfigures per chunk.
    #
    # If optional keyword `relative` is set to True, the
    # indices will be interpreted as offsets from the previous
    # partition point in the index sequence.
    #
    # An optional keyword `cls` can be supplied to change
    # the Frame subtype used in the return value. By default,
    # it's a vanilla Frame.
    def partition(self, *indices, relative=False, cls=None):
        # Default Frame type to use is vanilla Frame
        if cls is None:
            cls = Frame

        if len(indices) == 0:
            return Frame([self.sub[:]])
        if len(indices) == 1 and isinstance(indices[0], (Iterable, slice)):
            indices = indices[0]

        # Convert to list if needed
        if isinstance(indices, slice):
            indices = list(listselect(range(self.numfigs), indices).keys())
        if not isinstance(indices, list):
            indices = list(indices)

        # Preprocess any non-standard index values.

        # Initialize index head. It's used to keep track of the remaining
        # indices that haven't been accounted for in the partition yet.
        head = 0
        for n, index in enumerate(indices):
            if callable(index):
                # Convert any filter functions into indices
                func = index  # Rename to make reading code easier
                selection = listselect(self.figures[head:], func)
                if len(selection) == 0:
                    raise ValueError(f"Filter function {func.__name__} could not find a match in the remaining subfigures.")
                # Grab earliest matching index (offset by n to correct for
                # slicing self.figures above)
                index = next(iter(selection.keys())) + head
            elif relative and n > 0:
                index = indices[n-1] + index
            elif index < 0:
                # Divide any negative indices mod len(self.figures)
                # so they will be in the correct order relative to
                # positive indices.
                index = index % len(self.figures)
            indices[n] = index
            # Head index is taken to be 1 after the current partition point.
            head = index + 1

        chunks = []
        chunks.append(self.sub[:indices[0]])
        for n in range(1,len(indices)):
            chunks.append(self.sub[indices[n-1] : indices[n]])
        chunks.append(self.sub[indices[n]:])

        # Separate construction from subfigure assignment in case
        # the Frame sub-type uses a weird constructor.
        parts = cls()
        parts.figures = chunks

        return parts

    # Given a Frame of subframes generated from calling partition(),
    # combine() recombines them back into a single Frame figure
    # and returns the result. Note that this method creates copies
    # of all subfigures and leaves the original Frame figure that
    # called it unchanged.
    #
    # This method may not combine them perfectly if transformation
    # tweenables of the underlying subframes were modified
    # (e.g. `origin`) since these may not be transferred to the
    # subfigures of those subframes.
    def combine(self):
        root = self.figures[0].copy()
        for chunk in self.figures[1:]:
            chunk = chunk.copy()
            root.merge(chunk)
        root.origin = self.origin
        return root

    # Attempts to convert a copy of the Frame into the given
    # frame type.
    #
    # Note that tween method and modifier will NOT be
    # transferred to the new type.
    def toType(self, frameType, *args, **kwargs):
        return self._toType_basic(frameType, *args, **kwargs)

    # Allows you to give a name to a figure in the Frame that can
    # be referenced later using attribute access syntax.
    # This name mapping will persist even for a copy made of the
    # Frame figure.
    #
    # EXAMPLE:
    # frm = Frame([pt, path, poly])
    # frm.setName(pt=pt, path=path, poly=poly)
    #
    # Or equivalently, you can use the figure list stack index:
    # frm.setName(pt=0, path=1, poly=2)
    #
    # Then you can modify a subfigure with this syntax:
    # frm.path.width = 4
    # frm.poly.fill = [1,1,0]
    #
    # When the Frame is turned into an actor, it enables subfigure
    # manipulation after creating new keyfigures:
    # frm.newendkey(30)
    # frm.last().pt.pos = 3+3j
    def setName(self, **kwargs):
        for name, index in kwargs.items():
            if isinstance(index, morpho.Figure):
                try:
                    index = self.figures.index(index)
                except ValueError:
                    raise ValueError("Given figure is not in the Frame's figure list.")
            elif not isinstance(index, int):
                raise TypeError(f"Value associated with name must be Figure or int, not `{type(index).__name__}`")

            self._names[name] = index
        return self

    # Returns the subfigure of the given name.
    def getName(self, name):
        return self.figures[self._names[name]]

    def __getattr__(self, name):
        # First try using the superclass's built-in getattr()
        try:
            # return morpho.Figure.__getattr__(self, name)
            return super().__getattr__(name)
        except AttributeError:
            pass

        # If you got to this point in the code, it means the
        # superclass's getattr() failed.

        # Search the `_names` dict if the given name is in it
        try:
            return self.figures[self._names[name]]
        except KeyError:
            # This line should DEFINITELY throw an error,
            # since to get to this point in the code,
            # AttributeError must have been thrown above.
            super().__getattr__(name)
            # morpho.Figure.__getattr__(self, name)


    # Modified setattr() method for Frame checks if the given
    # name is in the list of subfigure names and if it is,
    # replaces the subfigure with the given `value`.
    # Otherwise, just sets an attribute like any other Figure.
    def __setattr__(self, name, value):
        if object_hasattr(self, "_names") and name in self._names:
            self.figures[self._names[name]] = value
        else:
            # morpho.Figure.__setattr__(self, name, value)
            super().__setattr__(name, value)

    # Applies the origin translation of the Frame to the given
    # cairo context and returns a SavePoint object, thus enabling
    # context manager syntax:
    #
    #   with self._pushTranslation(camera, ctx):
    #       ...
    def _pushTranslation(self, camera, ctx):
        savept = morpho.SavePoint(ctx)

        # If origin is zero, don't do anything
        if self.origin == 0:
            return savept

        a,b,c,d = camera.view

        surface = ctx.get_target()
        WIDTH = surface.get_width()
        HEIGHT = surface.get_height()

        scale_x = WIDTH/(b-a)
        scale_y = HEIGHT/(d-c)
        dx, dy = self.origin.real, self.origin.imag

        ctx.scale(scale_x, scale_y)
        ctx.translate(dx, dy)
        ctx.scale(1/scale_x, 1/scale_y)

        return savept


    # Draw all visible figures in the figure list.
    def draw(self, camera, ctx, *args, **kwargs):
        figlist = sorted(self.figures, key=lambda fig: fig.zdepth)

        with self._pushTranslation(camera, ctx):
            for fig in figlist:
                if fig.visible:
                    fig = applyFigureModifier(fig)
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
        # new = morpho.Figure.copy(self)
        new = super().copy()
        # new = super().copy()

        # Make copies of all the underlying figures.
        if deep:
            new_figures = new.figures  # Saves on tweenable getattr time loss
            for i, fig in enumerate(new_figures):
                new_figures[i] = fig.copy()
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

    ### TWEEN METHODS ###

    tweenLinear = handleSubfigureTweening(morpho.Figure.tweenLinear)
    tweenSpiral = handleSubfigureTweening(morpho.Figure.tweenSpiral)

    @classmethod
    def tweenPivot(cls, angle=tau/2):
        pivot = morpho.Figure.tweenPivot(angle)
        # Enable splitting
        pivot = morpho.pivotTweenMethod(cls.tweenPivot, angle)(pivot)
        pivot = handleSubfigureTweening(pivot)

        return pivot

# Tweens a Frame actor (or a subset of its subfigures) to a target
# Frame, possibly with substaggering.
#
# Note that this action will ignore toplevel attributes (such as
# `origin`) of the target.
#
# INPUTS
# target = Target Frame figure. Must have same figure count as source.
# subduration = Duration in frames to animate each subfigure.
#       Default: 30
#
# KEYWORD-ONLY INPUTS
# substagger = Frame offset between animating adjacent subfigures
#       in the selection. Default: 0
# select = Selection of subfigures to apply the action to.
#       Default: sel[:] (all subfigures in the usual order).
#
# Example usage:
#   myframe.subtween(target, 20, substagger=3)
@Frame.action
def subtween(film, target, subduration=30, *,
        substagger=0, select=sel[:]
        ):

    source = film.last()
    selection = listselect(source.figures, select)
    if source.numfigs != target.numfigs:
        raise TypeError(f"Source and target have differing subfigure counts ({source.numfigs} vs {target.numfigs})")

    target = target.copy()  # Use a copy to be on the safe side.

    # Generator automatically selects the correct target subfigure as
    # the subaction iteration progresses so that subactionfunc()
    # doesn't have to know where in the subaction iteration we are.
    indices = listselect(source.figures, select).keys()
    subtargets = iter(listselect(target.figures, sorted(indices)).values())
    def subactionfunc(actor):
        subtarget = next(subtargets)
        actor.newendkey(subduration, subtarget)

    film.subaction(subactionfunc, select=select, substagger=substagger)


# Blank frame used by the Animation class.
blankFrame = Frame()
blankFrame.static = True

# Special fadeIn() for Frame-like actors supports a `substagger`
# parameter that applies a staggered fade in to the subfigures.
#
# Note: For substagger to work, the tween method of the latest
# keyfigure must delegate subfigure tweening to the subfigures'
# individual tween methods. This condition is always satisfied
# if using one of the built-in tween methods, but if using a
# custom one, make sure to decorate it with
# @handleSubfigureTweening.
@Frame.action
def fadeIn(film, duration=30, atFrame=None, jump=0, alpha=1, *, substagger=0, select=None):
    lasttime = film.lastID()
    if atFrame is None:
        atFrame = lasttime

    frame0 = film.last()
    frame0.visible = True
    finalframe = frame0.copy()
    frame0.all.static = False

    substagger = aslist(substagger)

    if substagger == [0] and select is None:
        # Do traditional fade in action. The traditional way exists
        # since using the subaction feature on MultiFigures incurs
        # some drawbacks that I would like to not have to deal with
        # if substagger is 0.
        frame1 = film.newkey(atFrame)
        frame1.visible = True
        frame2 = film.newendkey(duration)

        for n,fig in enumerate(frame1.figures):
            # fig.static = False
            actor = morpho.Actor(fig)
            actor.fadeIn(duration=duration, jump=jump)
            frame1.figures[n] = actor.first()
            frame2.figures[n] = actor.last()
    else:
        film.subaction.fadeIn(duration, atFrame, jump=jump, alpha=alpha, substagger=substagger, select=select)

    # Hide lingering initial keyfigure if it exists.
    if atFrame > lasttime:
        frame0.visible = False

    # Ensure final frame really is the original final frame,
    # but with adjusted alpha
    film.fin = finalframe
    film.fin.select[select if select is not None else sel[:]].set(
        alpha=alpha, visible=(alpha > 0)
        )

@Frame.action
def fadeOut(film, duration=30, atFrame=None, jump=0, *, substagger=0, select=None):

    substagger = aslist(substagger)

    # Record of who was static so we can restore this later
    staticRecord = [fig.static for fig in film.last().figures]
    film.last().all.static = False
    if substagger == [0] and select is None:
        # Do traditional fade out action. The traditional way exists
        # since using the subaction feature on MultiFigures incurs
        # some drawbacks that I would like to not have to deal with
        # if substagger is 0.
        if atFrame is None:
            atFrame = film.lastID()

        frame0 = film.last()
        frame1 = film.newkey(atFrame)
        frame2 = film.newendkey(duration)
        frame2.visible = False

        for n,fig in enumerate(frame1.figures):
            # fig.static = False
            actor = morpho.Actor(fig)
            actor.fadeOut(duration=duration, jump=jump)
            frame1.figures[n] = actor.first()
            frame2.figures[n] = actor.last()
    else:
        film.subaction.fadeOut(duration, atFrame, jump=jump, substagger=substagger, select=select)

    if select is None or select == sel[:]:
        film.last().visible = False

    # Restore static attribute for subfigures that were originally
    # static. This is helpful in case the user wants to use the
    # Frame again after fade out is complete.
    for fig, static in zip(film.last().figures, staticRecord):
        fig.static = static

@Frame.action
def rollback(frame, duration=30, atFrame=None):
    if atFrame is None:
        atFrame = frame.lastID()

    frame1 = frame.newkey(atFrame)
    for fig in frame1.figures:
        fig.static = False
    frame.newendkey(duration, frame.first().copy()).visible = False

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

        # Prevent the `origin` tweenable inherited from the Frame
        # class from being jumped in an actor action like fadeOut().
        # Jumping will instead be handled by individually jumping
        # each subfigure in the multifigure.
        self._state["origin"].tags.add("nojump")

        # List of indices for subfigures that can be used for
        # making subfigure copies as part of a tween. This can
        # be a specific index value, or a slice object, or a
        # filter function, or a list of all these types.
        self.NonTweenable("_subpool", [])

    @property
    def subpool(self):
        return self._subpool

    @subpool.setter
    def subpool(self, value):
        if not isinstance(value, (list, tuple, set)):
            # Convert into singleton list if the value is not
            # a common sequence type.
            value = [value]
        self._subpool = value if type(value) is list else list(value)

    # Returns a dict_keys list of the indices in the subpool
    def _getSubpoolIndices(self):
        return listselect(self.figures, self._subpool).keys()

    # Parses the data in the `subpool` attribute and turns
    # it into the final sorted sequence of raw indices that it
    # represents.
    def _parseSubpool(self):
        subpool = sorted(self._getSubpoolIndices())
        if len(subpool) == 0:
            return range(len(self.figures))
        else:
            return sorted(subpool)

    def _appearsEqual(self, other, *args, compareSubNonTweenables=True, **kwargs):
        return morpho.Frame._appearsEqual(self, other, *args, compareSubNonTweenables=compareSubNonTweenables, **kwargs)

    # Allows actor actions to be applied to subfigures with a
    # substagger parameter.
    @staticmethod
    def subaction(actor):
        return _SubactionSummonerForMultiFigures(actor)

    # # NOT IMPLEMENTED!!!
    # # Returns a StateStruct encapsulating all the tweenables
    # # of all the figures in the MultiFigure.
    # # Main example use case:
    # # my_multifig.all().alpha = 0 changes all the subfigures'
    # # alpha attribute to 0.
    # # By default, the tweenables encapsulated are all the
    # # tweenables contained in the zeroth figure in the list,
    # # but this can be overridden, as well as exactly what figures
    # # should be encapsulated.
    # def all(self, tweenableNames=None, figures=None):
    #     raise NotImplementedError
    #     if len(self.figures) == 0:
    #         raise IndexError("Multifigure has no subfigures.")

    #     if tweenableNames is None:
    #         tweenableNames = list(self.figures[0]._state)
    #     if figures is None:
    #         figures = self.figures

    #     return StateStruct(tweenableNames, figures)

    # If attempted to access a non-existent attribute,
    # check if it's an attribute of the first figure in
    # the figure list and return that instead.
    def __getattr__(self, name):
        # First try using the superclass's built-in getattr()
        # which should grab any valid attribute returns in the
        # main class.
        try:
            # I now think a super() call is correct, instead of
            # directly invoking Frame.__getattr__() since it's possible
            # a multi-inheritance defines its own special __getattr__(),
            # and we don't want that modification to get lost.
            return super().__getattr__(name)
            # return morpho.Frame.__getattr__(self, name)
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
            # return morpho.Frame.__getattr__(self, name)

        # Try to find the attribute as a common subfigure attribute,
        # and if found, return it.
        # fig = self.figures[0]
        try:
            # return fig.__getattribute__(name)
            # return getattr(fig, name)
            return getattr(self.all, name)
        # This attribute is nowhere to be found anywhere. So give up.
        except AttributeError:
            # raise AttributeError("First member figure of type '"+type(fig)+"'' does not have attribute '"+name+"'")
            raise AttributeError(f"Could not find attribute '{name}' in either the main class or as a common attribute of all subfigures.")

    # Modified setattr() first checks if the requested attribute already
    # exists as a findable attribute in the main class. If it is, it just
    # sets it as normal. Otherwise it checks if the attribute exists in
    # the first member figure. If it does, it sets to subfigures instead of the
    # main class. But if it can't find this attribute in the first member
    # figure either, it will just assign the attribute as a new attribute
    # of the main class.
    def __setattr__(self, name, value):
        # Set the attribute as normal if the MultiFigure is not active yet,
        # or it's a concrete attribute of the main class,
        # or it's a tweenable in the main class.

        if not self._active:
            super().__setattr__(name, value)
            return

        try:
            # Attempt to access attribute `name` according to
            # both of the Figure class's getattrs.
            # This should handle getting both regular attributes
            # and tweenables / intangible attributes
            try:
                morpho.Figure.__getattribute__(self, name)
            except AttributeError:
                super().__getattr__(name)
            selfHasName = True
        except AttributeError:
            selfHasName = False
        if selfHasName:
            super().__setattr__(name, value)
        # If this attribute is NOT an already existent attribute of
        # the main class, check if it's an attribute of the first
        # member figure. If it is, set the attribute to all subfigures.
        # elif len(self.figures) != 0:
        else:
            try:
                # Get first component figure (if possible)
                fig = self.figures[0]

                # See if it already exists as an attribute
                # of the first member figure.
                # fig.__getattribute__(name)
                try:
                    getattr(fig, name)
                except AmbiguousValueError:
                    # Ignore AmbiguousValueError since it just
                    # means the getattr() failed because of conflicting
                    # values, but that's okay, because all we
                    # are using getattr() for is to loosely check for
                    # attribute existence!
                    pass

                # If you got here, we didn't get an attribute error,
                # so it should be a real attribute! Go ahead and set it!
                self.all.__setattr__(name, value)
                # fig.__setattr__(name, value)

            # Got an attribute error, so the given attribute isn't
            # even in the first member figure. Therefore, just assign it
            # as a regular (but new) attribute of the main class.
            except (AttributeError, IndexError):
                super().__setattr__(name, value)

    # Sets all given keyword inputs as toplevel attributes if they
    # already exist as toplevel attributes. Any others are assigned
    # as attributes of the subfigures.
    def set(self, **kwargs):
        # Dictionary holds all attribute mappings that don't
        # correspond to toplevel attributes BUT DO correspond to
        # subfigure attributes. These attributes will be assigned
        # at the subfigure level
        subset = dict()
        if len(self.figures) > 0:
            fig0 = self.figures[0]
            for name in kwargs.copy():
                if not object_hasattr(self, name) and name not in self._state \
                and hasattr(fig0, name):
                    subset[name] = kwargs.pop(name)
        morpho.Figure.set(self, **kwargs)
        self.all.set(**subset)
        return self


    # Decorator for the tween methods in a MultiFigure subclass.
    # Reworks ordinary base class tween methods so that they work
    # in a multifigure setting.
    #
    # INPUTS
    # baseMethod = The method from the base class that should be
    #              modified. This method will be applied to the
    #              subfigures during a tween.
    # mainMethod = The corresponding method in the MultiFigure subclass.
    #              e.g. Figure.tweenLinear. This method handles
    #              tweening all the "main" tweenables of the multifigure
    #              object itself (as opposed to subfigures), but it
    #              should NOT act on the `figures` tweenable!
    #              Defaults to Figure.tweenLinear.
    @staticmethod
    def Multi(baseMethod, mainMethod=morpho.Figure.tweenLinear):

        def wrapper(self, other, t, *args, **kwargs):
            # wrapper function for a MultiFigure tween method

            # Temporarily extend the figure list of self or other
            # so that both have exactly the same number of subfigures.
            len_self_figures = len(self.figures)
            len_other_figures = len(other.figures)
            if len_self_figures == 0 or len_other_figures == 0:
                raise IndexError(f"Cannot tween empty {type(self).__name__}.")

            diff = len_self_figures - len_other_figures

            target = other if diff > 0 else self
            if diff != 0:
                # Temporarily extend the figure list of target with copies of
                # target's subfigures

                # Generate the sorted pool of indices from which
                # subfigure copies are allowed to be drawn.
                subpool = target._parseSubpool()

                # Make the copies and insert them uniformly
                # amongst the original subfigures they came from.
                orig_figures = target.figures
                target.figures = target.figures[:]
                makesubcopies(target.figures, subpool, abs(diff))
                tw = wrapper(self, other, t, *args, **kwargs)
                # Restore target to its original state
                target.figures = orig_figures
                return tw

            # Tween each subfigure in self with its partner in other
            figures = []
            for fig, pig in zip(self.figures, other.figures):
                twig = baseMethod(fig, pig, t, *args, **kwargs)
                figures.append(twig)

            # Create final tweened multifigure object
            tw = mainMethod(self, other, t)
            tw.figures = figures

            return tw

        return wrapper

    # Mainly for internal use.
    # Decorator maker made to be used on a MultiFigure subclass.
    # Takes in the baseclass of the MultiFigure class
    # (e.g. Image for MultiImage) and a list of method names
    # from the baseclass and then creates modified versions of
    # them for the multifigure class according to a `modifier`
    # decorator that takes a baseclass method as input and returns
    # a new modified method. Note that `modifier` should NOT modify
    # the baseclass method in place, but merely return a new version
    # reflecting the modifications.
    #
    # The main use case for this is to modify baseclass methods
    # that would return self to instead return the multifigure
    # that called them. This can accomplished with the syntax
    #   @MultiFigure._modifyMethods(names, baseclass, MultiFigure._returnOrigCaller)
    #   class SubMultiFigure(MultiFigure):
    #       ...
    #
    # This was created to solve the problem whereby invoking
    # a subfigure method from the multifigure (e.g. calling
    # scaleByHeight() on a multiimage) would return the
    # image subfigure instead of returning the object that
    # originally invoked the method (the multifigure).
    # I still consider this decorator as a bit of a bandaid
    # fix to this problem (since it requires the programmer
    # to manually list out all self-returning method names),
    # so this decorator should be considered an implementation
    # detail and shouldn't be depended on it to exist in
    # future versions of Morpho.
    def _modifyMethods(names, baseclass, modifier):
        def decorator(cls):
            for name in names:
                basemethod = getattr(baseclass, name)
                multifigureMethod = modifier(basemethod)
                setattr(cls, name, multifigureMethod)
            return cls
        return decorator

    # Mainly for internal use.
    # Method modifier meant to be used in conjunction with
    # _modifyMethods(). It modifies a baseclass method to
    # return the original caller object instead of the
    # subfigure. See _modifyMethods() for more info.
    #
    # Note that this method first checks if the base method
    # returns the subfigure before overriding the return value.
    # If the base method does NOT return the subfigure, it will
    # not override it, and the modified method will simply return
    # the base method's original return value.
    @staticmethod
    def _returnOrigCaller(basemethod):
        def modifiedMethod(self, *args, **kwargs):
            try:
                fig0 = self.figures[0]
            except IndexError:
                raise AttributeError("Multifigure is empty. Cannot access subfigure methods.")
            baseOutput = basemethod(fig0, *args, **kwargs)
            # Only override basemethod return value if fig0 is being returned.
            if baseOutput is fig0:
                return self
            else:
                return baseOutput
        return modifiedMethod

    # Mainly for internal use.
    # Method modifier to be used with _modifyMethods().
    # It applies the basemethod to ALL subfigures and then
    # returns the original caller (the multifigure object).
    # Best used for subfigure methods that modified the figure
    # in place and returned self.
    @staticmethod
    def _applyToSubfigures(basemethod):
        def modifiedMethod(self, *args, **kwargs):
            for fig in self.figures:
                basemethod(fig, *args, **kwargs)
            return self
        return modifiedMethod

Multifigure = MultiFigure

@MultiFigure.action
def fadeIn(actor, duration=30, atFrame=None, jump=0, alpha=1, *,
        substagger=0, select=None, **kwargs):

    substagger = aslist(substagger)

    actor.last().visible = True
    finalkey = actor.last().copy()
    if substagger != [0] or select is not None:
        actor.last().tweenMethod = Frame.tweenLinear
    Frame.actions["fadeIn"](actor, duration, atFrame, jump, alpha,
        substagger=substagger, select=select, **kwargs)
    actor.fin = finalkey
    actor.fin.select[select if select is not None else sel[:]].set(
        alpha=alpha, visible=(alpha > 0)
        )

@MultiFigure.action
def fadeOut(actor, *args, substagger=0, select=None, **kwargs):

    substagger = aslist(substagger)

    origTweenMethod = actor.last().tweenMethod
    if substagger != [0] or select is not None:
        actor.last().tweenMethod = Frame.tweenLinear
    Frame.actions["fadeOut"](actor, *args, substagger=substagger, select=select, **kwargs)
    actor.last().tweenMethod = origTweenMethod

# Like regular morphFrom(), except the source can optionally
# be a list of actors/figures, in which case, the morph will
# be performed from all of those figures.
@MultiFigure.action
def morphFrom(actor, source, *args, **kwargs):
    if isinstance(source, (list, tuple)):
        if len(source) == 0:
            raise TypeError("Source to morph from is empty.")
        # Prepare the list of figures to morph from
        subfigs = [subfig.last().copy() if isinstance(subfig, morpho.Actor) else subfig.copy() for subfig in source]
        if hasattr(actor.figureType, "commitTransforms"):
            from morpholib.combo import TFrame
            frm = TFrame(subfigs)
        else:
            frm = Frame(subfigs)

        # Combine into a single multifigure
        combined = frm.combine()

        return actor.morphFrom(combined, *args, **kwargs)
    else:
        return morpho.Figure.actions["morphFrom"](actor, source, *args, **kwargs)


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

        # if name in dir(self):
        if object_hasattr(self, name):
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
#
# Also note that if a SpaceFrame is used in a layer which is not
# pooling primitives, the `origin` attribute will be ignored.
# This is the default scenario, so it's not recommended to mess
# with SpaceFrame's `origin` attribute unless you really know
# what you're doing.
class SpaceFrame(Frame):
    def __init__(self, figures=None, /, **kwargs):
        if isinstance(figures, Frame):
            # super().__init__(figures.figures)
            super().__init__()
            self._updateFrom(figures, common=True)
            if not isinstance(self.figures, list):
                self.figures = list(self.figures)

            self.figures.extend(kwargs.values())
            self.setName(**kwargs)
        else:
            super().__init__(figures, **kwargs)

    # Space version of Frame.partition().
    def partition(self, *args, cls=None, **kwargs):
        if cls is None:
            cls = SpaceFrame
        return super().partition(*args, cls=cls, **kwargs)

    # Only for frames consisting only of space figures
    # (i.e. figures possessing a primitives() method)
    #
    # Calls the primitives() method on all figures and merges all of
    # the lists into one big list of primitives and returns it.
    def primitives(self, camera): # orient=np.identity(3), focus=np.array([0,0,0], dtype=float)):
        primlist = []
        for fig in self.figures:
            if fig.visible:
                primlist.extend(fig.primitives(camera))

        return primlist

# THIS CLASS MAY BE BROKEN! USE AT YOUR OWN RISK!
# 3D version of the MultiFigure class. See "MultiFigure" for more info.
class SpaceMultiFigure(SpaceFrame):
    # Use MultiFigure's actions instead of SpaceFrame's
    actions = MultiFigure.actions.copy()

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

        self.Tweenable("t", t, tags=["scalar"])

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
        origInit = subSkit.__init__
        def newInit(self, **kwargs):
            # Do basic init
            # super(subSkit, self).__init__()
            origInit(self)

            # Check if any keyword arguments were given that are not
            # valid parameters
            kwSet = set(kwargs.keys())
            if not kwSet.issubset(paramSet):
                raise TypeError(f"Unexpected keyword argument(s): {kwSet-paramSet}")

            for varname in params:
                if varname in kwargs:
                    self.Tweenable(varname, kwargs[varname], tags=["scalar"])
                else:
                    self.Tweenable(varname, params[varname], tags=["scalar"])

        subSkit.__init__ = newInit
        return subSkit

    return decorator


# Non-drawable figure whose purpose is to record information about the current
# view of the complex plane that the Layer class should use to draw its actors.
#
# TWEENABLES
# view = Viewbox of the complex plane ([xmin,xmax,ymin,ymax]).
#        Default: [-5,5, -5,5]
class Camera(BoundingBoxFigure):
    def __init__(self, view=None):
        if view is None:
            view = [-5,5, -5,5]

        super().__init__()

        self.Tweenable("view", view, tags=["view", "scalar", "list"])
        self.Tweenable("rotation", 0, tags=["scalar"])

        self.defaultTween = type(self).tweenZoom

    # Returns the current viewbox.
    def box(self, *, raw=False):
        if not raw and self.rotation != 0:
            # Use the bounding box of the rotated corners
            # of the original viewbox.
            corners = boxCorners(self.view)
            center = mean(corners)
            rot = cmath.exp(-self.rotation*1j)

            corners = [(z-center)*rot + center for z in corners]
            xmin = min(z.real for z in corners)
            xmax = max(z.real for z in corners)
            ymin = min(z.imag for z in corners)
            ymax = max(z.imag for z in corners)

            return [xmin, xmax, ymin, ymax]
        return self.view[:]


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

    # Rotates the camera counter-clockwise by the given
    # angle (in radians).
    def rotate(self, angle):
        self.rotation += angle
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
        return self


    # Returns width of the viewbox: view[1] - view[0]
    def width(self):
        return self.boxWidth()

    # Returns height of the viewbox: view[3] - view[2]
    def height(self):
        return self.boxHeight()

    # Returns the dimensions of the viewbox as a tuple
    # (width, height)
    def dimensions(self):
        return (self.width(), self.height())

    # Returns the width/height aspect ratio of the current camera's
    # view.
    def aspectRatioWH(self):
        width, height = self.dimensions()
        return width/height

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

    # Converts position coordinates from one camera system to another.
    # Given complex position `pos`, this method returns the
    # corresponding complex position in the camera system of `other`.
    # See also: convertCoordsFrom()
    def convertCoords(self, other, pos):
        return other.physicalCoords(self.normalizedCoords(pos))

    # Converts position coordinates from one camera system to another.
    # Given complex position `pos` in `other`'s coordinate system,
    # this method returns the corresponding complex position in the
    # self's camera system.
    # Identical to convertCoords(), but self and `other` are swapped.
    def convertCoordsFrom(self, other, pos):
        return self.physicalCoords(other.normalizedCoords(pos))

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

    # Converts physical width from one camera system to another.
    # Given `width`, this method returns the corresponding width
    # in the camera system of `other`.
    def convertWidth(self, other, width):
        return other.physicalWidth(self.normalizedWidth(width))

    # Converts physical width from another camera system to self's.
    # Similar to convertWidth(), but reverses the roles of self
    # and other.
    def convertWidthFrom(self, other, width):
        return self.physicalWidth(other.normalizedWidth(width))

    # Converts physical height from one camera system to another.
    # Given `height`, this method returns the corresponding height
    # in the camera system of `other`.
    def convertHeight(self, other, height):
        return other.physicalHeight(self.normalizedHeight(height))

    # Converts physical height from another camera system to self's.
    # Similar to convertHeight(), but reverses the roles of self
    # and other.
    def convertHeightFrom(self, other, height):
        return self.physicalHeight(other.normalizedHeight(height))

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


    # Rotates the coordinate system by the camera's rotation
    # value. Returns a SavePoint object that can be used with
    # a `with` statement:
    #
    #   with mycamera._pushRotation(ctx):
    #       ...
    def _pushRotation(self, ctx):
        savept = morpho.SavePoint(ctx)
        if self.rotation != 0:
            # Calculate quantities useful for performing camera rotation
            center = self.center()
            rot = cmath.exp(self.rotation*1j)
            translation = (1-rot)*center

            morpho.pushPhysicalCoords(self.view, ctx, save=False)
            ctx.translate(translation.real, translation.imag)
            ctx.rotate(self.rotation)
            morpho.pushPhysicalCoords(self.view, ctx, save=False, invert=True)
        return savept


    ### TWEEN METHODS ###

    # Primary tween method for the Camera class. Zooms in an exponential fashion
    # as opposed to a linear fashion.
    # That is, it linearly tweens the zoom level in LOG space.
    # It's usually better than tweenLinear(), because if you zoom the camera
    # over several orders of magnitude, it goes thru them at a uniform speed.
    @morpho.TweenMethod
    def tweenZoom(self, other, t):
        # tw = self.copy()
        tw = morpho.Figure.tweenLinear(self, other, t, ignore=("view",))
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

    # Generates a modified version of the tweenZoom() tween method
    # that multiplies the zoom amount by the given multiplier function.
    # Syntax:
    #   mycamera.tweenMethod = mycamera.tweenZoomWithMultiplier(multfunc)
    @classmethod
    def tweenZoomWithMultiplier(cls, multiplierFunc):
        def splitter(tmid, beg, mid, fin):
            one_minus_tmid = 1 - tmid
            M_tmid = multiplierFunc(tmid)
            def mult1(t):
                return multiplierFunc(tmid*t) / M_tmid**t

            def mult2(t):
                return multiplierFunc(tmid + one_minus_tmid*t)/M_tmid**(1-t)

            beg.tweenMethod = cls.tweenZoomWithMultiplier(mult1)
            mid.tweenMethod = cls.tweenZoomWithMultiplier(mult2)

        @morpho.TweenMethod(splitter=splitter)
        def multzoom(self, other, t):
            return self.tweenZoom(other, t).zoomOut(multiplierFunc(t))
        return multzoom

    # Generates a modified version of the tweenZoom() tween method
    # in which the camera is zoomed out by the given factor halfway
    # thru the tween. For example, setting
    #   mycamera.tweenMethod = mycamera.tweenZoomJump(2)
    # will cause the camera to zoom out by a factor of 2 halfway
    # thru a tween between adjacent keyframes. This is useful
    # if you want to have the camera move from one point to another,
    # but have it zoom out and then back in again as it's traveling.
    @classmethod
    def tweenZoomJump(cls, midscale=1):

        def multiplierFunc(t):
            return 4*t*(1-t)*(midscale-1) + 1

        return cls.tweenZoomWithMultiplier(multiplierFunc)

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

        super().__init__()

        self.Tweenable("view", view, tags=["view", "scalar", "list"])
        self.Tweenable("_orient", orient, tags=["nparray", "orient"])
        self.Tweenable("_focus", focus, tags=["nparray"])

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

    # @morpho.TweenMethod
    # def tweenZoom(self, other, t):
    #     tw = Camera.tweenZoom(self, other, t)
    #     tw = morpho.Figure.tweenLinear(tw, other, t)

    #     return tw


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
# timeOffset = (DEPRECATED)
#              Number of frames the indices should be offset to line up
#              with the index system used by the Animation class. Basically
#              allows you to setup a local time axis offset from the global
#              Animation time axis. Increasing timeOffset causes the layer to
#              be animated at later points in the Animation.
# visible = Global visibility attribute. If set to False, the layer is never drawn
#           regardless of the state of the camera actor.
# start/end = (DEPRECATED)
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
        elif isinstance(view, Camera):
            self.camera = morpho.Actor(view)
        elif isinstance(view, morpho.Actor) and issubclass(view.figureType, Camera):
            self.camera = view
        else:
            raise TypeError("view must be list, tuple, or Camera actor.")

        # Assign this layer as the `owner` attribute of each actor
        self._updateOwnerships()

        self.timeOffset = timeOffset
        self.visible = visible
        self.start = start
        self.end = end
        self.mask = None
        self.owner = None

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

    @property
    def mask(self):
        return self._mask

    @mask.setter
    def mask(self, value):
        self._mask = value
        self._updateMaskOwners()

    @property
    def camera(self):
        return self._camera

    @camera.setter
    def camera(self, value):
        self._camera = value
        self._camera.owner = self

    # Assigns this layer to the `owner` attribute of all
    # component actors (and the camera actor).
    def _updateOwnerships(self):
        for actor in self.actors:
            actor.owner = self
        self.camera.owner = self

    # Recursively goes thru the mask chain and updates each mask layer's
    # owner to be self's owner.
    def _updateMaskOwners(self):
        if self.maskChainFormsLoop():
            raise MaskConfigurationError("Cannot update mask ownerships because the mask chain loops.")
        currentLayer = self.mask
        while currentLayer is not None:
            currentLayer.owner = self.owner
            currentLayer = currentLayer.mask

    # Return a deep-ish copy of the layer by default.
    # Optionally specify deep=False to make a copy, but
    # none of the actors, the mask layer, or even the camera
    # actor are copied, and the actor ownership will not be changed.
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
            # new._updateOwnerships()
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

        # if atFrame != int(atFrame):
        #     raise ValueError("atFrame parameter must be an integer!")
        # if beforeActor != oo and beforeActor != int(beforeActor):
        #     raise ValueError("beforeActor parameter must be integer or +infinity!")

        # atFrame = int(atFrame)

        # Convert beforeActor into proper format for indexing into actors list
        if beforeActor > len(self.actors):
            beforeActor = len(self.actors)
        elif beforeActor < 0:
            beforeActor %= len(self.actors)
        # beforeActor = int(beforeActor)

        if isinstance(other, list) or isinstance(other, tuple):
            # numActorsAlreadyAdded = 0
            # for n in range(len(other)-1,-1,-1):
            for layer in reversed(other):
                self.merge(layer, atFrame, beforeActor)
        elif isinstance(other, morpho.Actor) or isinstance(other, morpho.Figure):
            other = type(self)(other)
            # Temp layer will inherit the time offset of self
            # since an actor has an unspecified time offset.
            other.timeOffset = self.timeOffset
            self.merge(other, atFrame, beforeActor)
        elif isinstance(other, Layer):
            # Compute time offset
            df = other.timeOffset - self.timeOffset + atFrame

            # Set other owner's to self's owner just in case
            # user wants to keep accessing `other` after the merge.
            other.owner = self.owner

            # for actor in other.actors:
            # for n in range(len(other.actors)):
            for actor in reversed(other.actors):
                # Adjust all the indices based on the time offsets
                if df != 0:
                    timeline = {}
                    for keyID in actor.timeline:
                        timeline[keyID + df] = actor.timeline[keyID]
                    actor.timeline = timeline
                    actor.update()

                actor.owner = self
                self.actors.insert(beforeActor, actor)

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

        else:
            raise TypeError("Attempted to merge non-layer object!")


    # Convenience function. Behaves just like merge() except it always
    # merges at the maxkeyID of self.
    # If maxkeyID is -oo, then merges at frame 0.
    # If optional keyword-only argument `glob` is set to True,
    # the object will be appended to the end of the global timeline.
    # See also: `Layer.affix()`
    def append(self, other, timeOffset=0, beforeActor=oo, *, glob=False):
        atFrame = self.lastID() if not glob else self.glastID()
        if atFrame == -oo:
            atFrame = 0
        if glob:
            # Adjust by layer time offset so that local times coincide
            # with global times.
            atFrame -= self.timeOffset
        atFrame += timeOffset
        self.merge(other, atFrame, beforeActor)

    # Equivalent to append() except that it appends at the
    # end of the GLOBAL timeline.
    # Equivalent to append(..., glob=True)
    def affix(self, *args, **kwargs):
        return self.append(*args, **kwargs, glob=True)

    # Creates an Actor from the given figure and then immediately
    # affixes it to the layer at the end of the global timeline
    # and returns the newly created Actor
    # Roughly equivalent to: self.affix(Actor(figure))
    # but its return value is Actor(figure).
    # This allows figure/actor creation and layer merge to be
    # be condense into a single line like this:
    #   newactor = mylayer.Actor(myfigure)
    #
    # Any additional arguments are passed in to the affix()
    # method. But if optional keyword argument `atFrame` is
    # passed in, merge() will be used instead of affix().
    def Actor(self, figure, *args, atFrame=None, **kwargs):
        if isinstance(figure, (morpho.Actor, Layer)):
            actor = figure
        else:
            actor = morpho.Actor(figure)

        if atFrame is not None:
            self.merge(actor, atFrame=atFrame, **kwargs)
        else:
            self.affix(actor, *args, **kwargs)

        return actor

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

    # Returns the first index in the global timeline.
    # Requires the layer to be owned by an Animation.
    def gfirstID(self):
        if self.owner is None:
            return self.firstID(useOffset=True, ignoreMask=False)
        else:
            return self.owner.gfirstID()

    # Returns the last index in the global timeline.
    # Requires the layer to be owned by an Animation.
    def glastID(self):
        if self.owner is None:
            return self.lastID(useOffset=True, ignoreMask=False)
        else:
            return self.owner.glastID()

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
    def viewtime(self, f, useOffset=False, returnCamera=False, *,
            _skipTrivialTweens=False, **kwargs):
        if len(self.camera.timeline) == 0:
            raise IndexError("Camera timeline is empty.")

        # Adjust for time offset
        if useOffset:
            f -= self.timeOffset

        # Compute current view
        viewFrame = self.camera.time(f, _skipTrivialTweens=_skipTrivialTweens, **kwargs)
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

    # Optimizes the Layer's actors for animation playback.
    # See morpho.Actor._optimize() for more info.
    def _optimize(self):
        self.camera._optimize()
        for actor in self.actors:
            actor._optimize()

    def _deoptimize(self):
        self.camera._deoptimize()
        for actor in self.actors:
            actor._deoptimize()

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
        cam = self.viewtime(f, returnCamera=True, keepOwner=True, _skipTrivialTweens=True)  # Get camera figure
        if not cam.visible:
            return
        cam = applyFigureModifier(cam)
        if not cam.visible:
            return

        # Compile list of figures to draw
        figlist = []
        for actor in self.actors:
            if not actor.visible: continue

            fig = actor.time(f, keepOwner=True, _skipTrivialTweens=True)
            if fig is None: continue

            if fig.visible:
                fig = applyFigureModifier(fig)
                if fig.visible:
                    figlist.append(fig)

        # Sort based on zdepth
        figlist.sort(key=lambda fig: fig.zdepth) #, reverse=True)

        # NOTE: The "start" and "end" parameters of the masklayer are ignored
        # when drawing with masking!
        if self.mask is None or not self.mask.visible or not self.mask.viewtime(f, returnCamera=True, _skipTrivialTweens=True).visible:
            # Draw all figures
            with cam._pushRotation(ctx):  # Apply camera rotation
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

            with cam._pushRotation(self._ctx1):  # Apply camera rotation
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
        new = super().copy(deep=deep)
        new.poolPrimitives = self.poolPrimitives
        return new


    # Draw the spacelayer at the specified index on the given cairo context
    # if the camera is visible at that index.
    def draw(self, f, ctx, useOffset=False):
        if useOffset:
            f -= self.timeOffset

        # Compute current view
        cam = self.viewtime(f, returnCamera=True, keepOwner=True, _skipTrivialTweens=True)  # Get camera figure
        if not cam.visible:
            return
        cam = applyFigureModifier(cam)
        if not cam.visible:
            return

        # Compile list of figures to draw
        figlist = []
        for actor in self.actors:
            if not actor.visible: continue

            fig = actor.time(f, keepOwner=True, _skipTrivialTweens=True)
            if fig is None: continue

            if fig.visible:
                fig = applyFigureModifier(fig)
                if fig.visible:
                    figlist.append(fig)

        # Sort based on zdepth
        figlist.sort(key=lambda fig: fig.zdepth) #, reverse=True)

        if self.poolPrimitives:
            primlist = []  # This list "pools" together all primitives across all figures
            for fig in figlist[:]:
                # if "primitives" in dir(fig):
                if object_hasattr(fig, "primitives"):
                    primlist.extend(fig.primitives(cam))
                    figlist.remove(fig)

        # NOTE: The "start" and "end" parameters of the masklayer are ignored
        # when drawing with masking!
        if self.mask is None or not self.mask.visible or not self.mask.viewtime(f, returnCamera=True, _skipTrivialTweens=True).visible:
            with cam._pushRotation(ctx):  # Apply camera rotation
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

            with cam._pushRotation(self._ctx1):  # Apply camera rotation
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
# locaterModifier = Complex to complex function which modifies
#       complex number positions generated from the locater layer.
#       The generated locator layer positions are passed into this
#       function and the return value is printed to the console instead.
#       Default: Identity (do nothing) function z |--> z
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

        # Set this animation as the owner of all component layers
        self._updateOwnerships()

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

        # Function that will be applied to the complex number
        # position computed from the locater layer. By default
        # it's the identity function z |--> z
        self.locaterModifier = lambda z: z

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

        # If set to True, the animation window will not be refreshed
        # before drawing a new frame, meaning previous frames will
        # not be erased before drawing a new one on top of it.
        self.overdraw = False

        # Active animation variables
        self.active = False
        self.running = True
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
    def windowShape(self):
        return self._windowShape

    @windowShape.setter
    def windowShape(self, pair):
        self._windowShape = tuple(round(item) for item in pair)

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

    # Alternate name for the locater modifier using "o" instead of "e".
    @property
    def locatorModifier(self):
        return self.locaterModifier

    @locatorModifier.setter
    def locatorModifier(self, value):
        self.locaterModifier = value

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

    @property
    def aspectRatioWH(self):
        WIDTH, HEIGHT = self.windowShape
        return WIDTH/HEIGHT


    # Returns a (deep-ish) copy of the animation.
    # If deep=False, then the animation will not make copies of the
    # underlying figures in the layers.
    # Note that copy will not copy over the window attribute, so you will
    # have to manually associate the window to the copied animation.
    def copy(self, deep=True):
        ani = Animation()

        # Make copies of all the layers.
        ani.layers = [layer.copy(deep=deep) for layer in self.layers]

        # Reassign ownerships
        ani._updateOwnerships()

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
        ani.locaterModifier = self.locaterModifier
        ani.clickTime = self.clickTime
        ani.transition = self.transition
        ani.currentIndex = self.currentIndex
        ani.antialiasText = self.antialiasText
        ani.jointStyle = self.jointStyle
        ani.overdraw = self.overdraw
        ani.clickCopy = self.clickCopy
        ani.clickRound = self.clickRound

        # # Relink mask layers to the copy's layer list whenever possible
        # for n in range(len(ani.layers)):
        #     layer = ani.layers[n]
        #     if layer.mask is not None and layer.mask in self.layers:
        #         layer.mask = ani.layers[self.layers.index(layer.mask)]

        return ani

    # Assigns this Animation to the `owner` attribute of all
    # component layers (and their masks).
    def _updateOwnerships(self):
        for layer in self.layers:
            layer.owner = self
            layer._updateMaskOwners()

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

        # Update layer ownerships
        self._updateOwnerships()


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

    # Identical to append() for the Animation class.
    # Exists for consistency with Layer.affix(), which behaves
    # differently than Layer.append().
    def affix(self, *args, **kwargs):
        return self.append(*args, **kwargs)

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
        drift = 0  # Cumulative round-off error of delay frames.
        for keyID in self.delays:
            delay = self.delays[keyID]
            newID = round(keyID/factor)
            newDelay = round(delay/factor) if delay != oo else oo

            # Update drift value and then correct newDelay if drift
            # is now more than half a frame.
            if delay != oo:
                drift += round(delay/factor) - delay/factor
                if abs(drift) > 0.5:
                    correction = -round(drift)
                    newDelay += correction
                    drift += correction

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

    # Equivalent to mation.firstID(ignoreMasks=False)
    def gfirstID(self):
        return self.firstID(ignoreMasks=False)

    # Equivalent to mation.lastID(ignoreMasks=False)
    def glastID(self):
        return self.lastID(ignoreMasks=False)

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

    # Returns the location on the timeline (in frames) corresponding
    # to the given number of seconds after the animation's start
    # taking into account animation delays.
    # Note that `seconds` is relative to whatever the current
    # animation's `start` value is. If None, uses firstID().
    # Also note that if `seconds` corresponds to the middle of
    # an animation delay, the returned timeline coordinate will
    # be the frame at which the delay BEGUN.
    def timelineCoord(self, seconds):
        if seconds < 0:
            raise ValueError("`seconds` cannot be negative.")
        # True time coordinate (relative to animation beginning)
        T = round(self.frameRate * seconds)
        # Timeline coordinate of animation beginning
        beg = self.firstID() if self.firstIndex is None else self.firstIndex

        # Get a sorted list of all delay coordinates that occur
        # at or after beg.
        delayCoords = sorted(self.delays.keys())
        delayCoords = delayCoords[listceil(delayCoords, beg):]

        # If there are no remaining delays, true time coordinates and
        # timeline coordinates will align, so simply return
        # a shifted version of T.
        if len(delayCoords) == 0:
            return T + beg

        # Find the most recent delay coordinate that occurs before T
        # relative to the T-axis and store it as `d_rel`.

        # Each new adjusted delay coordinate is offset by the total
        # amount of delay incurred so far. The formula is
        #   d_n' = d_n - beg + sum(D_k for 0 <= k <= n-1)
        # where d_n' is the nth delay coordinate relative to the T-axis,
        #   d_n is the nth delay coordinate simply (delayCoords[n])
        #   D_k is the kth delay value at delay coordinate d_k
        #       (D_k = self.delays[d_k])
        cumulativeDelaySoFar = 0
        for N,d in enumerate(delayCoords):
            d_new = d - beg + cumulativeDelaySoFar
            if d_new > T:
                # Subtract 1 so that N records the index
                # of the last delay coordinate that worked!
                N -= 1
                break
            d_rel = d_new
            cumulativeDelaySoFar += self.delays[d]
        # N records the index d_rel corresponds to in the
        # delayCoords list.

        if N == -1:
            # There are no delays that occur before T, so just
            # return a shifted T.
            return T + beg

        if T - d_rel < self.delays[delayCoords[N]]:
            # If within the window of the most recent delay,
            # T is adjusted by subtracting off all prior delays
            # and subtracting the overlap portion with the latest
            # delay window
            return T + beg - (T - d_rel) - sum(self.delays[delayCoords[n]] for n in range(N))
        else:
            # If outside the most recent delay window, then T is
            # adjusted by subtracting off all prior delays including
            # the entirety of the most recent delay window.
            return T + beg - sum(self.delays[delayCoords[n]] for n in range(N+1))

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
    # its lastID. This can be overridden to any index by passing
    # in the frame index into the optional keyword `atFrame`.
    # By default, the delay duration is infinite.
    # Optionally specify a timeOffset as well.
    def wait(self, f=oo, timeOffset=0, *, atFrame=None):
        if atFrame is None:
            atFrame = self.lastID()
        end = atFrame + timeOffset
        if end == -oo:
            raise IndexError("End of animation is undefined.")
        self.delays[end] = f

    @property
    def endDelay(self):
        return self.wait

    # Makes the animation delay at its current final frame for
    # however long is needed until the specified frame f is reached.
    # This is usually equivalent to self.wait(f - self.length())
    def waitUntil(self, f=oo):
        f = f - self.length()
        if abs(f) != oo:
            f = round(f)

        if f < 0:
            raise ValueError(f"Wait point occurs {-f} frames ({round(-f/self.frameRate, 2)} sec) before animation's end.")

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

        self.wait(f)

    @property
    def endDelayUntil(self):
        return self.waitUntil

    # Same as waitUntil(), but the delay duration is specified in
    # seconds instead of frames. See: waitUntil() for more info.
    def waitUntilSec(self, seconds=oo, /, *args, **kwargs):
        f = self.frameRate*seconds
        return self.waitUntil(f, *args, **kwargs)

    # Convert all infinite delays to the specified delay (units=frames).
    def finitizeDelays(self, delay):
        # Convert to list so that delay = 0 works
        # (since delay = 0 will cause keys from the dict
        # to be deleted, which would cause a RuntimeError)
        for time in list(self.delays.keys()):
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

    # Returns a generator that yields all the layers (including their
    # masks) in the animation via a depth-first search.
    def allLayers(self):
        for layer in self.layers:
            if layer.maskChainFormsLoop():
                raise MaskConfigurationError("The mask chain of the layers form a loop.")
            currentLayer = layer
            while currentLayer is not None:
                yield currentLayer
                currentLayer = currentLayer.mask

    # Multiplies all the pixel values of all the tweenables of all
    # the keyfigures in the animation across all layers by the given
    # scale factor, e.g. the `width` attribute of a Path figure.
    #
    # Useful when changing an animation's resolution
    # so that it pixel-dependent attributes of actors remain unchanged
    # after the resolution change.
    #
    # Note that this method may not help if a pixel-valued tweenable
    # is determined directly via a modifier.
    def rescalePixels(self, scale):
        for layer in self.allLayers():
            for actor in list(layer.actors) + [layer.camera]:
                for keyfig in actor.keys():
                    keyfig._rescalePixels(scale)

    # Rescales the window shape by the given scale factor,
    # while also rescaling all the pixel units of all the keyfigures
    # in the animation, meaning attributes like stroke widths will
    # look the same even after rescaling the window shape.
    #
    # Note that this may not work as intended if a pixel-valued
    # attribute is determined directly via a modifier.
    def rescale(self, scale):
        self.windowShape = tuple(round(scale*item) for item in self.windowShape)
        self.rescalePixels(scale)

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
        if not self.overdraw:
            self.clearContext()

        # Draw one layer at a time.
        for i in range(len(self.layers)):
            layer = self.layers[i]
            f = self.currentIndex - layer.timeOffset
            if not layer.visible or not(layer.start <= f <= layer.end):
                continue

            # Draw layer to current context
            layer.draw(f, self.context)

    # Optimizes the animation for playback by optimizing
    # all its actors.
    # See morpho.Actor._optimize() for more info.
    def _optimize(self):
        for layer in self.layers:
            layer._optimize()

    def _deoptimize(self):
        for layer in self.layers:
            layer._deoptimize()

    # Clears all time caches for all actors in all layers.
    # Used when beginning to play/export an animation to make
    # sure it renders with a clean cache.
    def _clearAllTimeCaches(self):
        for layer in self.layers:
            for actor in layer.actors:
                actor.timeCache.clear()

    # Export animation to file.
    # Can either be MP4, GIF animation, or PNG/JPG sequence depending on
    # the file extension given in the filepath.
    # Optional argument scale is a scale factor that scales the entire
    # animation window shape before exporting. Useful for downscaling an
    # animation while exporting test animations to speed up rendering.
    # Note: scaling seems to be done at the final pixel level, so specifying
    # scale > 1 will not actually increase the resolution of your animation.
    # Use Animation.rescale() instead to increase resolution.
    #
    # OPTIONAL KEYWORD-ONLY INPUTS
    # imageOptions = Dict providing additional options passed to the
    #       PIL image writer when exporting in a format other than PNG.
    #       If an option is unrecognized, it is silently ignored.
    #       Default: dict(quality=85), meaning JPEG quality is
    #       set to 85 by default.
    # tempType = Image type to use when generating the temporary
    #       image sequence as part of exporting to mp4 or gif.
    #       Can be useful to speed up exports at the expense of
    #       quality. For example, setting tempType="jpg" can
    #       significantly speed up exports with small loss to quality.
    #       Default: "png"
    # optimize = Boolean which if set to False will prevent the
    # animation from being optimized. This will probably rarely be
    # desired.
    def export(self, filepath, scale=1, *,
            imageOptions=dict(), tempType="png", optimize=True):

        tempType = tempType.strip()
        # Check that the tempType is NOT gif.
        if tempType.lower() == "gif":
            raise TypeError("GIF cannot be used as a tempType.")

        imgopts = imageOptions
        imageOptions = dict(quality=85)
        imageOptions.update(imgopts)

        if scale > 1:
            warn("scale > 1 will not actually improve resolution. Use Animation.rescale() instead.")

        if optimize:
            self._optimize()
        self._clearAllTimeCaches()

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
            print(f"Exporting temporary {tempType.upper()} sequence...")
            with TemporaryDirectory(exportSignature) as tempDir:
                self.export(tempDir + os.sep + filename.replace("'", "_") + f".{tempType}", scale,
                    imageOptions=imageOptions, optimize=optimize
                    )

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
                        + f".{tempType}'")
                        demux.append(f"duration {round(gifDelays[n-firstIndex], 8)}")
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
                        "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",  # Handles odd window dimensions
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

                # Clean up temp dir
                print("Cleaning up temp directory...")
            print("DONE!")

        elif extension.lower() in ("png", "jpg", "jpeg"):
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
            self.running = True
            while self.currentIndex <= finalIndex:
                self.draw()

                # If the animation is just one frame, don't
                # label the file by frame number.
                if firstIndex == finalIndex:
                    imgfile = Dir+os.sep+filename+"."+extension
                else:
                    imgfile = Dir+os.sep+filename \
                        + "_" + int2fixedstr(self.currentIndex-firstIndex,
                            digits=numdigits(finalIndex-firstIndex)) \
                        + "." + extension

                if scale == 1:
                    surfaceSave(self.context.get_target(), imgfile, options=imageOptions)
                else:
                    # # Setup a modified standard context and scale it.
                    # anim2.setupContext()
                    # anim2.context = cr.Context(anim2.context.get_target())
                    # anim2.context.scale(scale, scale)

                    # Grab target surface from real animation and set it as source
                    # then paint it onto the secondary animation and export!
                    anim2.context.set_source_surface(self.context.get_target())
                    anim2.context.paint()
                    surfaceSave(anim2.context.get_target(), imgfile, options=imageOptions)

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
    # Optional argument "optimize" can be set to False to prevent
    # the animation from being optimized. This will probably rarely be
    # desired.
    #
    # KNOWN ISSUE: Morpho may sometimes crash if you attempt to call play()
    # multiple times in a single run of your code. To avoid, make sure you
    # only play one animation per execution of your code.
    def play(self, window=None, autoclose=False, *, optimize=True):
        # Verify the animation can be played.
        # if not self.verify():
        #     raise Exception("Animation can't be played because it is not configured properly!")
        self.sanityCheck()

        if optimize:
            self._optimize()
        self._clearAllTimeCaches()

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
        self.running = True
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
            # Print mouse coordinates if a locater layer is specified.
            if mation.locaterLayer is not None:
                # Search the layer list if given an int
                if isinstance(mation.locaterLayer, int) or isinstance(mation.locaterLayer, float):
                    cam = mation.layers[int(mation.locaterLayer)].viewtime(mation.currentIndex, returnCamera=True)
                else:
                    # Treat it as an actual layer object
                    cam = mation.locaterLayer.viewtime(mation.currentIndex, returnCamera=True)
                view = cam.view

                z = physicalCoords(X, Y, view, mation.context)
                z *= cmath.exp(-1j*cam.rotation)  # Adjust by camera rotation

                # Apply modifier
                z = mation.locaterModifier(z)

                # Round the real and imag components of z if needed.
                if self.clickRound is not None:
                    x,y = z.real, z.imag
                    x = round(x, self.clickRound)
                    y = round(y, self.clickRound)
                    z = x + y*1j

                # Copy to the clipboard if needed
                if self.clickCopy:
                    pyperclip.copy(str(z))

                # print((z.real, z.imag))

                # sign = " + " if z.imag >= 0 else " - "
                # print(z.real, sign, abs(z.imag), "j", sep="")
                sign = "+" if z.imag >= 0 else ""
                print(f"({z.real} {sign}{z.imag}j)")

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
                    # Extra clearContext() call in case overdraw=True.
                    mation.clearContext()
                else:
                    mation.active = False
            elif mation.paused:
                mation.resume()
            else:
                mation.pause()

            tic()  # Reset runtime timer


        # Schedule drawing at the specified frame rate.
        # Only schedule the updater for animations that are more
        # than a single frame.
        # UPDATE: pyglet will occasionally crash when trying to
        # play a 1-frame animation. Disabling the `else` clause
        # here seems to fix it. In the future, this if-else
        # clause may be fully removed, but I'm keeping this funny
        # `if True` to preserve the previous behavior in case
        # I want to revert.
        if True or finalIndex - firstIndex > 0:
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
        self.running = False
        self.window = None
        self.context = None
        self.update = None
        self.paused = False
        self.currentIndex = 0
        self._keyIDs = None  # This var is only used once play() is called.
        self._deoptimize()

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
        key = round(key)
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
