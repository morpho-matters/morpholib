'''
This is the base module of the figures package.
All the classes, functions, constants, etc. found here are imported
into the morpho.figures namespace when
import morpho.figure
is called.

To avoid name conflicts, please avoid using names in the
outermost scope that could be names of subpackages.
This can be done by avoiding names that are nothing but
lowercase letters since convention has it that package
names are all lowercase letters.
'''


import morpholib as morpho
import morpholib.matrix
import morpholib.actions
import morpholib.transitions
from morpholib.tools.basics import *

import math, cmath
import numpy as np

# Alias for `set` because the name gets overridden
# in the Figure class
pyset = set

# Set of all Figure metasetting names
METASETTINGS = {"transition", "visible", "static", "delay", "_static_acute"}


### CLASSES ###


# The superclass of all drawable objects in Morpho.
# All subclasses like Point, Path, etc. derive from this.
# To make a figure subclass, note that the constructor must
# be able to handle a void call like
# foo = mySubFigure()
# because tweening requires this kind of call.
# This doesn't stop you from having optional arguments,
# but all subclasses of Figure must be allowed to call
# the constructor with no inputs.
class Figure(object):
    # Takes a list of tweenables as input.
    # By default, the constructor makes an attribute sharing the name
    # of each tweenable in the list (unless it conflicts with an existing
    # attribute name).
    def __init__(self, tweenables=None, zdepth=0):

        # super() call for sake of possible multi-inheritance
        # by subclasses
        super().__init__()

        if tweenables is None: tweenables = {}

        # self._state = {}
        object.__setattr__(self, "_state", {})

        # zdepth indicates how close the figure is to the camera.
        # Figures with higher zdepths will be drawn in front of figures with
        # lower zdepths.
        # If zdepths match, draw order is inferred from order of figure list.
        # Later figures are drawn in front.
        # zdepth can be int or float, but should be finite.
        # Also note that zdepth only works local to a single layer.
        # zdepth will not affect draw order ACROSS layers.
        zdepth = morpho.Tweenable("zdepth", zdepth, tags=["scalar"])
        self._state["zdepth"] = zdepth
        self._nontweenables = set()

        self.update(tweenables)

        # Actor that this figure is a part of.
        self.owner = None

        ### META-SETTINGS ###

        # Tells higher-level structures whether or not to draw this figure.
        # Note this attribute can always be overridden by manually
        # calling the figure's draw() method. It just means it won't
        # be automatically drawn when embedded as part of a higher-level
        # structure like an Actor or Frame.
        self.visible = True

        # Tells the Actor class (or any higher structure) whether to
        # tween this figure between keyframes or just keep it static.
        # Also tells the Frame class whether or not to apply
        # fimage() to this figure.
        # Note that the static attribute can always be overridden
        # by manually calling the figure's tween() or fimage() methods.
        # It just means they won't be automatically called when
        # embedded as parts of frames, animations, or other higher
        # structures that incorporate figures.
        self.static = False

        # Special hidden attribute only meant to be used during
        # animation playback. Helps to make animations run more
        # quickly when tweening between equal keyfigures.
        self._static_acute = False

        # (DEPRECATED)
        # How many frames should the figure persist in an animation.
        # If set to oo (infinity), then the figure will
        # never disappear until the next keyfigure (if any).
        # If the delay period ends before the next keyfigure appears,
        # tweening will be done as if the figure were placed
        # at the frame where the delay ended.
        # i.e. there will be a smooth tween and not a jerk between
        # the end of the starting figure's delay and an intermediate
        # tweened figure.
        self.delay = 0

        # Current tween method used by tween().
        self.defaultTween = type(self).tweenLinear

        # Current transition. Default: uniform transition T(t) = t
        # tween() will automatically apply the transition before applying
        # the default tween method.
        self.transition = morpho.transitions.default

        # A function that modifies (a copy of) the figure before
        # its draw() method is called in an animation.
        self.modifier = None


    # Alternate name for the "defaultTween" attribute.
    @property
    def tweenMethod(self):
        return self.defaultTween

    @tweenMethod.setter
    def tweenMethod(self, value):
        self.defaultTween = value

    @property
    def modifier(self):
        return self._modifier

    @modifier.setter
    def modifier(self, value):
        self._modifier = value

    # Returns True iff self and other are both invisible, OR are
    # exactly the same type AND their tweenables compare equal.
    # Used to determine whether tweening will be required between
    # two keyfigures in an Actor.
    #
    # Optionally, keyword `compareNonTweenables` can be set to True
    # to make the check stricter by also checking that corresponding
    # non-tweenables match between both figures.
    def _appearsEqual(self, other, ignore=(), *, compareNonTweenables=False):
        return not(self.visible or other.visible) or \
            (type(self) is type(other) and \
            all(self._state[name] == other._state[name] for name in self._state if name not in ignore)) and \
            (not compareNonTweenables or all(isequal(getattr(self, name), getattr(other, name)) for name in self._nontweenables if name not in ignore))

    # Actor actions registry.
    # Maps action names to the action functions themselves.
    actions = {}

    # Action decorator adds an action function to
    # the figure's registry.
    @classmethod
    def action(cls, actionFunc):
        # Create copy so that overriding class attr actions works
        # in subclasses
        cls.actions = cls.actions.copy()
        cls.actions[actionFunc.__name__] = actionFunc
        return actionFunc

    # If the user requested an attribute that doesn't technically exist,
    # check if the attribute name is a tweenable's name. If so,
    # return the tweenable's value, otherwise, raise the standard
    # AttributeError.
    def __getattr__(self, name):
        # Test for the existence of these attributes.
        # If they don't exist, there's nothing else to check,
        # raise an error.
        throwError = False
        try:
            # object.__getattribute__(self, "_tweenableNames")
            # object.__getattribute__(self, "_stateN")
            object.__getattribute__(self, "_state")
        except AttributeError:
            # Since we're within the __getattr__ method, the following
            # command is doomed to fail, but it will return the desired
            # error message.
            throwError = True

        if throwError:
            object.__getattribute__(self, name)

            # The below error should never be reached, because the above line is
            # supposed to raise an error before getting here.
            raise Exception("Special Exception! I'm never supposed to appear. Something's wrong with the code!")

        # If you got to this point, then "_state" is an
        # attribute of self, so we may safely get them without risk
        # of recursive explosion.

        # Check if the name is in the set of tweenable names.
        # If not, then attempt to access the name as a regular attribute
        # (this is guaranteed to fail since we're in the __getattr__ method,
        # which is intentional. I want the AttributeError raised).
        if name in self._state:
            return self._state[name].value
        else:
            # This line should throw a guaranteed error of the sort I want.
            object.__getattribute__(self, name)

            raise Exception("object.__getattribute__ did NOT throw an error when it was supposed to! You've found a bug in Morpho!")

    # Set attributes as normal unless it is the name of a tweenable.
    def __setattr__(self, name, value):
        # If the given attribute name already exists, proceed normally.
        # if name in dir(self):
        if object_hasattr(self, name):
            object.__setattr__(self, name, value)
        # Else if the given name is a tweenable's name, modify the tweenable's
        # value instead of setting a new attribute.
        elif name in self._state:
            # elif "_state" in dir(self) and name in self._state:
            self._state[name].value = value
        # Else set the new attribute normally.
        else:
            object.__setattr__(self, name, value)

    # Sets attributes of the figure according to the keyword arguments given
    # and returns the figure that called it.
    #
    # EXAMPLE USAGE:
    # fig.set(pos=0, alpha=1)  # equivalent to fig.pos = 0; fig.alpha = 1
    #
    # Or with actors:
    # actor.newkey(30).set(pos=0, alpha=1, etc=stuff)
    #
    # Since this method returns the calling figure, it enables one liners
    # like this:
    # fig = MyFigureClass().set(pos=0, alpha=1, etc=stuff)
    def set(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)
        return self

    # `_oripos` is a hidden property that accesses/sets a figure's
    # `origin` attribute if it exists, otherwise tries to do so
    # for its `pos` attribute. If neither exists, throws an
    # AttributeError.
    #
    # Its purpose is to provide a unified way to get/set a
    # figure's "origin" transformation attribute even if the
    # figure uses `pos` for that purpose (e.g. Image)
    @property
    def _oripos(self):
        try:
            return self.origin
        except AttributeError:
            pass

        try:
            return self.pos
        except AttributeError:
            raise AttributeError("Figure possesses neither `origin` nor `pos` attribute.")

    @_oripos.setter
    def _oripos(self, value):
        if hasattr(self, "origin"):
            self.origin = value
        elif hasattr(self, "pos"):
            self.pos = value
        else:
            raise AttributeError("Figure possesses neither `origin` nor `pos` attribute.")

    # Multiplies the value of any tweenable possessing a "pixel"
    # tag by the given scale factor. If the tweenable also possesses
    # a "list" tag, it will multiply item-wise.
    #
    # Will also recursively apply to subfigures if a tweenable has
    # the "figures" tag.
    #
    # Mainly for use by Animation.rescalePixels()
    def _rescalePixels(self, scale):
        for tweenable in self._state.values():
            if "pixel" in tweenable.tags:
                if "list" in tweenable.tags:
                    tweenable.value = type(tweenable.value)([scale*item for item in tweenable.value])
                else:
                    tweenable.value = scale*tweenable.value
            elif "figures" in tweenable.tags:
                for subfig in tweenable.value:
                    subfig._rescalePixels(scale)
        return self

    # # Creates a struct representation of the object.
    # def Struct(self):
    #     st = ps.Struct()
    #     for name in self._state:
    #         setattr(st, name, self._state[name].value)
    #     return st

    # Returns a deep-ish copy of the figure.
    # This method copies all of the tweenables and any registered nontweenables
    # even for subclasses,
    # but it doesn't handle any other attributes not built-in to the
    # Figure class.
    # Any optional arguments are passed to the constructor of the
    # figure's class when a copy is made.
    def copy(self, *args, **kwargs):
        # Copy tweenables
        tweenables = self._state.values()
        newTweenables = []
        for tweenable in tweenables:
            newTweenables.append(tweenable.copy())

        # Create the new figure
        new = type(self)(*args, **kwargs)  # Call constructor
        new.update(newTweenables)

        # Copy registered nontweenables
        # new._nontweenables = self._nontweenables.copy()
        # Make deep copy
        for name in self._nontweenables:
            value = getattr(self, name)
            try:
                setattr(new, name, value.copy())
            except Exception:  # Upon failure, just reassign and hope for the best.
                setattr(new, name, value)  # NOT redundant!

        new._updateSettings(self, includeTweenMethod=True, includeModifier=True)

        # Note that the `owner` attribute should NOT be copied
        # since the copied figure may not be used within an
        # actor.

        return new

    # Like copy, but the returned figure has default metasettings,
    # i.e. settings like `visible`, `static`, `tweenMethod`,
    # `transition`, `modifier`, `delay` will all be set to their
    # default values.
    def dup(self, *args, **kwargs):
        defaultFigure = type(self)()
        copy = self.copy(*args, **kwargs)
        copy._updateSettings(defaultFigure, includeTweenMethod=True, includeModifier=True)
        return copy

    # Updates the standard "meta-settings" of the figure with those
    # of the target figure. Mainly for use when converting one figure
    # type to another (e.g. SpaceText.toText() method).
    #
    # By default, this method doesn't update self's tween method
    # or modifier with the target's because those are often strongly
    # tied to the given figure's type, but to force transferral
    # of these attributes, set the optional kwargs
    # `includeTweenMethod` and/or `includeModifier` to True.
    #
    # Optionally, a set of setting names to ignore can be passed in
    # like this:
    #   myfig._updateSettings(target, ignore={"visible", "static"})
    def _updateSettings(self, target, *,
        includeTweenMethod=False, includeModifier=False,
        ignore=pyset()):

        # Typecast ignore into a singleton set if it is not
        # a standard python iterable.
        if not isinstance(ignore, (pyset, tuple, list)):
            ignore = {ignore}

        if includeTweenMethod:
            self.defaultTween = target.defaultTween
        if includeModifier:
            self.modifier = target.modifier

        for name in METASETTINGS:
            if name not in ignore:
                setattr(self, name, getattr(target, name))

        return self

    # Copies over all tweenables, registered non-tweenables,
    # and meta-settings from the target figure over to self.
    # Mainly for use when converting between figure types.
    #
    # If optional argument `copy` is set to False, the target
    # figure will not be internally copied, and the attributes
    # of the given target will be transferred directly to self.
    #
    # If optional argument `common` is set to True, self will
    # only copy over attributes from the target that are in
    # common with self. No new attributes will be added to self
    # from the target.
    #
    # Optionally, a set of attribute names to ignore can be passed in
    # like this:
    #   myfig._updateFrom(target, ignore={"pos", "color"})
    def _updateFrom(self, target, *, copy=True, common=False,
        includeTweenMethod=False, includeModifier=False,
        ignore=pyset()):

        # Typecast ignore into a singleton set if it is not
        # a standard python iterable.
        if not isinstance(ignore, (pyset, tuple, list)):
            ignore = {ignore}

        if copy:
            target = target.copy()

        # Update tweenables
        for name in target._state:
            if ((not common) or (name in self._state)) and name not in ignore:
                self._state[name] = target._state[name] if copy else target._state[name].copy(deep=False)
        # Update non-tweenables
        for name in target._nontweenables:
            if ((not common) or (name in self._nontweenables)) and name not in ignore:
                self._nontweenables.add(name)
                setattr(self, name, getattr(target, name))

        # Update meta-settings
        self._updateSettings(target,
            includeTweenMethod=includeTweenMethod, includeModifier=includeModifier,
            ignore=ignore)

        return self

    # Attempts to convert a copy of the figure into the given
    # figure type by copying over all common tweenables and
    # non-tweenables.
    #
    # Note that tween method and modifier will NOT be
    # transferred to the new type.
    #
    # This method is currently hidden from the end-user
    # because type conversions are too messy a process in the
    # general case to handle using this basic technique.
    # However, this method may be useful in performing PART of
    # type conversions for many figures, and therefore may be
    # useful under the hood as part of toType() methods
    # implemented by subclasses.
    def _toType_basic(self, figureType):
        fig = figureType()
        fig._updateFrom(self, common=True)
        return fig

    # Update the state with a new set of tweenables.
    def update(self, tweenables):
        if "zdepth" not in self._state:
            raise KeyError('figure state dict somehow lacks "zdepth". Cannot update!')
        zdepth = self._state["zdepth"]  # Grab the old zdepth tweenable

        # if type(tweenables) is dict:
        if isinstance(tweenables, dict):
            self._state = tweenables
        else:
            self._state = {}
            for tweenable in tweenables:
                if tweenable.name in self._state:
                    raise KeyError("Two tweenables have the same name '"+tweenable.name+"'")
                self._state[tweenable.name] = tweenable

        # Use old zdepth if user did not supply it.
        if "zdepth" not in self._state:
            self._state["zdepth"] = zdepth

    # Similar to update(), but doesn't clear the old state away and instead
    # extends the original with new (or updated) tweenables.
    def extendState(self, tweenables):
        if isinstance(tweenables, dict):
            self._state.update(tweenables)
        else:
            for tweenable in tweenables:
                self._state[tweenable.name] = tweenable

    # Creates a new tweenable object and assigns it to the figure state.
    # Equivalent to self.extendState([morpho.Tweenable(...)])
    def Tweenable(self, name, value=0.0, tags=None, metadata=""):
        tweenable = morpho.Tweenable(name, value, tags, metadata)
        self._state[tweenable.name] = tweenable
        return tweenable

    # Registers a name as a non-tweenable attribute of the figure.
    # This enables the built-in Figure.copy() method to automatically
    # copy non-tweenable attributes.
    def NonTweenable(self, name, value):
        setattr(self, name, value)
        self._nontweenables.add(name)

    # Lists all the tweenables of a state.
    def listState(self):
        return list(self._state.values())

    def allTags(self):
        return set(tag for tweenable in self.listState() for tag in tweenable.tags)

    # NOT IMPLEMENTED!
    # Returns Actor(self)
    def toActor(self, *args, **kwargs):
        raise NotImplementedError
        return Actor(self, *args, **kwargs)

    # NOT IMPLEMENTED!
    # Creates Actor out of self, and then merges it to the specified
    # target (a layer or animation), and returns the actor.
    def mergeTo(self, target, *args, **kwargs):
        raise NotImplementedError
        actor = Actor(self)
        actor.mergeTo(target, *args, **kwargs)
        return actor

    # NOT IMPLEMENTED!
    # Creates Actor out of self, and then appends it to the specified
    # target (a layer or animation), and returns the actor.
    def appendTo(self, target, *args, **kwargs):
        raise NotImplementedError
        actor = Actor(self)
        actor.appendTo(target, *args, **kwargs)
        return actor

    # Uses whatever the default tween method is, but applies the
    # transition function first.
    # To tween WITHOUT taking the transition function into account,
    # call self.tween(other, t, ignoreTransition=True)
    def tween(self, other, t, ignoreTransition=False):
        if ignoreTransition:
            return self.defaultTween(self, other, t)
        else:
            return self.defaultTween(self, other, self.transition(t))

    # Template for the draw() method (subclasses actually implement it).
    # It takes two required inputs:
    # camera = Camera figure encapsulating viewbox and other info.
    # ctx    = cairo context object on which to draw
    def draw(self, camera, ctx):
        pass

    # Function image. Returns a new figure whose tweenables that contain
    # the tags "complex" or "fimage" become the result of evaluating the
    # given func.
    def fimage(self, func):
        newfig = self.copy()

        for tweenable in self._state.values():
            if "nofimage" in tweenable.tags:
                continue
            # Handle scalars
            if "complex" in tweenable.tags or "fimage" in tweenable.tags:
                if "list" in tweenable.tags:
                    A = tweenable.value
                    for i in range(len(A)):
                        newfig._state[tweenable.name].value[i] = func(tweenable.value[i])
                else:
                    newfig._state[tweenable.name].value = func(tweenable.value)

        return newfig

    # Applies a keyfigure's modifier in place according to its current
    # position in the timeline. Optionally a specific frame index can
    # be given instead.
    #
    # Optional keyword `inplace` can be set to False to apply the
    # modifier to a copy of the keyfigure instead and return the
    # result.
    def applyModifier(self, f=None, *, inplace=True):
        fig = self if inplace else self.copy()
        if self.modifier is None:
            return fig

        # Attempt to find animation owner
        animation = morpho.tools.dev.findOwnerByType(self, morpho.Animation)
        if animation is None:
            raise TypeError(f"Could not find Animation owner for `{type(self).__name__}` figure.")

        if f is None:
            # Attempt to find Actor owner
            actor = morpho.tools.dev.findOwnerByType(self, Actor)
            if actor is None:
                raise TypeError(f"Could not find Actor owner for `{type(self).__name__}` figure.")
            f = actor.timeof(self)

        # Temporarily set the animation's current time index to
        # be the frame index `f` before applying the modifier.
        # Enables `now()` calls to work correctly.
        origIndex = animation.currentIndex
        animation.currentIndex = f
        try:
            fig.modifier(fig)
        finally:
            animation.currentIndex = origIndex

        return fig

    # Applies a keyfigure's modifier IN PLACE and resets its
    # `modifier` attribute to None.
    # See also: actualized(), applyModifier()
    def actualize(self, *args, **kwargs):
        self.applyModifier(*args, **kwargs)
        self.modifier = None
        return self

    # Applies a keyfigure's modifier TO A COPY OF the keyfigure,
    # resets the copy's `modifier` attribute to None, and then
    # returns it.
    # See also: actualize(), applyModifier()
    def actualized(self, *args, **kwargs):
        fig = self.applyModifier(*args, inplace=False, **kwargs)
        fig.modifier = None
        return fig


    # BUILT-IN TWEEN METHODS

    # Linear tween method. This linearly tweens pretty much all tweenables
    # that are number-like, including arrays and lists of numbers, but also
    # number to number functions.
    # This tween method can be suppressed for a specific tweenable by including
    # the tag "nolinear" in the tweenable.
    #
    # This tween method expects data that are instances of the following types:
    # float, complex, int, np.ndarray, list, tuple, python function
    #
    # Tweening lists or tuples is generally done by converting into np.array
    # to speed up computation, but this behavior can be suppressed by including
    # the "loop" tag, which will result in a regular python loop to tween the
    # elements of your list/tuple.
    #
    # "ignore" is an optional argument where you can specify a list of
    # tweenable names that should NOT be acted on even though they may qualify
    # to be tweened under tweenLinear(). Mainly used when other tween
    # methods invoke tweenLinear() in order to avoid unnecessarily tweening
    # an attribute that is otherwise handled.
    # NOTE: This optional argument is a COURTESY, and is only required to be
    # supported by the generic tween methods found in this class.
    # (e.g. tweenLinear, tweenSpiral, tweenPivot)
    # Derivative tween methods may (or may not) support this option.
    # Thus, you should be wary of using super().tweenLinear(other, t, ignore=foo)
    # unless you are sure every superclass's linear tween supports "ignore".
    # Otherwise, to use "ignore", invoke this method directly via
    # morpho.Figure.tweenLinear(self, other, t, ignore=foo)
    @morpho.TweenMethod
    def tweenLinear(self, other, t, ignore=()):
        # Note that this tween method always assumes that the two data types
        # it is tweening between are the same. It does not necessarily check
        # that the data types of self and other are compatible before
        # attempting a tween, so cryptic errors may arise if you're not
        # careful!

        # Defaults to the empty tuple.
        if ignore is None:
            ignore = ()
        # Convert string to tuple containing string
        elif isinstance(ignore, str):
            ignore = (ignore,)

        # Numerical tags this tween method acts on
        tags = {"linear", "scalar", "magnitude", "size", "color",
            "complex", "integer", "nparray", "function"}

        # Figure copy is made as opposed to brand new figure
        # because this will ensure that tweenables that are
        # not affected by this method will default to self's.
        newfig = self.copy()
        # newfig = type(self)()

        for tweenable in self._state.values():
            # Skip this tweenable if it contains the "nolinear" tag,
            # or if none of the target tags are present, or if
            # the tweenable's name is in the ignore list.
            if "nolinear" in tweenable.tags or "notween" in tweenable.tags or tweenable.tags.isdisjoint(tags) \
                or tweenable.name in ignore:
                continue

            # Extract the data to tween from the tweenables
            A = tweenable.value
            B = other._state[tweenable.name].value

            # Tween the list the old-fashioned way with python loops
            # if the "loop" tag is present.
            if "loop" in tweenable.tags:
                # A = tweenable.value
                # B = other._state[tweenable.name].value
                newB = list(B)  # Make a new list which copies B
                for i in range(len(A)):
                    a = A[i]
                    b = B[i]
                    if "nparray" in tweenable.tags:
                        if np.array_equal(a,b):
                            tw = a.copy()
                        # Handle orient tween
                        elif a.shape == (3,3) and "orient" in tweenable.tags:
                            tw = morpho.matrix.orientTween(a,b,t)
                        # Handle regular nparray tween
                        else:
                            tw = morpho.numTween1(a,b,t)

                        if "integer" in tweenable.tags:
                            tw = tw.round()

                    # elif isinstance(a, function) or "function" in tweenable.tags:
                    elif callable(a) or "function" in tweenable.tags:
                        if a == b:
                            tw = a
                        else:
                            # Homotopy tween!!
                            def tw(*args, _tween_funcA=a, _tween_funcB=b, _tween_t=t, **kwargs):
                                return (1-_tween_t)*_tween_funcA(*args, **kwargs) + _tween_t*_tween_funcB(*args, **kwargs)

                    else:
                        # Assume basic numeric type
                        tw = morpho.numTween(a, b, t)
                        if "integer" in tweenable.tags:
                            tw = round(tw)
                    newB[i] = tw

                # Handles both lists and tuples
                newfig._state[tweenable.name].value = type(A)(newB)
                continue

            # Handle python lists and tuples
            elif isinstance(A, list) or isinstance(A, tuple):
                # a = tweenable.value
                # b = other._state[tweenable.name].value

                if "complex" in tweenable.tags:
                    a = np.array(A, dtype=complex)
                    b = np.array(B, dtype=complex)
                else:
                    a = np.array(A, dtype=float)
                    b = np.array(B, dtype=float)

                if np.array_equal(a,b):
                    tw = a.copy()
                # Handle orient tween
                elif a.shape == (3,3) and "orient" in tweenable.tags:
                    tw = morpho.matrix.orientTween(a,b,t)
                # Handle regular nparray tween
                else:
                    tw = morpho.numTween1(a,b,t)

                # Convert back to original type
                if "nparray" in tweenable.tags:
                    # Assume we originally had a list/tuple of np.arrays, so
                    # don't try to convert back into python types.
                    if "integer" in tweenable.tags:
                        tw = type(A)(tw.round())
                    else:
                        tw = type(A)(tw)
                else:
                    # # Convert back into a list of python types
                    # if "integer" in tweenable.tags:
                    #     tw = morpho.matrix.roundlist(tw)
                    # elif "complex" in tweenable.tags:
                    #     tw = morpho.matrix.complexlist(tw)
                    # else:
                    #     tw = morpho.matrix.floatlist(tw)
                    tw = tw.tolist()
                    # Convert to tuple if originally a tuple.
                    if isinstance(A, tuple):
                        tw = tuple(tw)

            # Data type is np.ndarray
            elif isinstance(A, np.ndarray):
                if np.array_equal(A,B):
                    tw = A.copy()
                # Handle orient tween
                elif A.shape == (3,3) and "orient" in tweenable.tags:
                    tw = morpho.matrix.orientTween(A,B,t)
                # Handle regular nparray tween
                else:
                    tw = morpho.numTween1(A,B,t)
                    if "integer" in tweenable.tags:
                        tw = tw.round()

            # Data type is callable
            # elif isinstance(A, function) or "function" in tweenable.tags:
            elif callable(A) or "function" in tweenable.tags:
                if A == B:
                    tw = A
                else:
                    # Homotopy tween!!
                    def tw(*args, _tween_funcA=A, _tween_funcB=B, _tween_t=t, **kwargs):
                        return (1-_tween_t)*_tween_funcA(*args, **kwargs) + _tween_t*_tween_funcB(*args, **kwargs)

            # All other types (assume it's a python numeric type)
            else:
                tw = morpho.numTween(A,B,t)
                if "integer" in tweenable.tags:
                    tw = round(tw)

            # Assign the new tweened value to the new figure in progress
            newfig._state[tweenable.name].value = tw

        return newfig

    # # Linear tween method. This linearly tweens all tweenables with the tags
    # # x, y, z, vector, scalar, magnitude, size
    # # FUTURE: This tween method should be able to handle vectors that have
    # # immutable types like tuple.
    # @morpho.TweenMethod
    # def tweenLinear_old(self, other, t):
    #     # Numerical tags this tween method acts on
    #     tags = {"linear", "x", "y", "z", "scalar", "magnitude", "size",
    #         "complex", "integer", "nparray", "function"}
    #     # Vector tags this tween method acts on
    #     vtags = {"vector", "position", "color"}

    #     # Figure copy is made as opposed to brand new figure
    #     # because this will ensure that tweenables that are
    #     # not affected by this method will default to self's.
    #     newfig = self.copy()
    #     # newfig = type(self)()

    #     for tweenable in self._state.values():
    #         # Skip this tweenable if it contains the "nolinear" tag.
    #         if "nolinear" in tweenable.tags: continue
    #         # Handle scalars
    #         if not tweenable.tags.isdisjoint(tags):
    #             if "list" in tweenable.tags:
    #                 A = tweenable.value
    #                 B = other._state[tweenable.name].value
    #                 newB = list(B)  # Make a new list which copies B
    #                 for i in range(len(A)):
    #                     a = A[i]
    #                     b = B[i]
    #                     if "nparray" in tweenable.tags:
    #                         # Handle orient tween
    #                         if a.shape == (3,3) and "orient" in tweenable.tags:
    #                             tw = morpho.matrix.orientTween(a,b,t)
    #                         # Handle regular nparray tween
    #                         else:
    #                             if np.array_equal(a, b):
    #                                 tw = a.copy()
    #                             else:
    #                                 tw = morpho.numTween1(a,b,t)
    #                     elif "function" in tweenable.tags:
    #                         if a == b:
    #                             continue
    #                         tw = lambda x, t=t: (1-t)*a(x) + t*b(x)
    #                     else:
    #                         tw = morpho.numTween(a, b, t)
    #                     if "integer" in tweenable.tags:
    #                         tw = round(tw)
    #                     newB[i] = tw
    #                 # Handles both lists and tuples
    #                 newfig._state[tweenable.name].value = type(A)(newB)
    #             # elif "list" in tweenable.tags:
    #             #     A = tweenable.value
    #             #     B = other._state[tweenable.name].value
    #             #     T = newfig._state[tweenable.name].value
    #             #     for i in range(len(A)):
    #             #         tw = morpho.numTween(A[i], B[i], t)
    #             #         if "integer" in tweenable.tags:
    #             #             tw = round(tw)
    #             #         # newfig._state[tweenable.name].value[i] = tw
    #             #         T[i] = tw
    #             else:
    #                 a = tweenable.value
    #                 b = other._state[tweenable.name].value
    #                 if "nparray" in tweenable.tags:
    #                     # Handle orient tween
    #                     if a.shape == (3,3) and "orient" in tweenable.tags:
    #                         tw = morpho.matrix.orientTween(a,b,t)
    #                     # Handle regular nparray tween
    #                     else:
    #                         if np.array_equal(a,b):
    #                             tw = a.copy()
    #                         else:
    #                             tw = morpho.numTween1(a,b,t)
    #                 elif "function" in tweenable.tags:
    #                     if a == b:
    #                         tw = a
    #                     else:
    #                         tw = lambda x, a=a, b=b, t=t: (1-t)*a(x) + t*b(x)
    #                 else:
    #                     tw = morpho.numTween(a,b,t)
    #                 if "integer" in tweenable.tags:
    #                     tw = round(tw)
    #                 newfig._state[tweenable.name].value = tw
    #         # Handle vectors
    #         elif not tweenable.tags.isdisjoint(vtags):
    #             if "list" in tweenable.tags:
    #                 '''
    #                 NOTE: This if-clause still needs to be updated to account
    #                 for vector lists that are of the form tuple x tuple.
    #                 Currently it only supports list x list.
    #                 Ideally it should support arbitrary vector-like x vector-like.
    #                 '''
    #                 A = tweenable.value
    #                 B = other._state[tweenable.name].value
    #                 for n in range(len(A)):
    #                     for i in range(len(A[n])):
    #                         a = A[n][i]
    #                         b = B[n][i]
    #                         tw = morpho.numTween(a,b,t)
    #                         if "integer" in tweenable.tags:
    #                             tw = round(tw)
    #                         newfig._state[tweenable.name].value[n][i] = tw
    #             else:
    #                 TW = list(tweenable.value)  # Create a copy in list format
    #                 for i in range(len(tweenable.value)):
    #                     a = tweenable.value[i]
    #                     b = other._state[tweenable.name].value[i]
    #                     tw = morpho.numTween(a,b,t)
    #                     if "integer" in tweenable.tags:
    #                         tw = round(tw)
    #                     # newfig._state[tweenable.name].value[i] = tw
    #                     TW[i] = tw
    #                 # Handles both tuples and lists
    #                 newfig._state[tweenable.name].value = type(tweenable.value)(TW)

    #     return newfig

    # Spiral tween method. Generally used to create transformations that
    # kind of make a "spiraling" motion.
    #
    # Operates on tweenables that contain the tags "complex" or "spiral".
    # Suppressed by the tags "nospiral" or "notween".
    @morpho.TweenMethod
    def tweenSpiral(self, other, t, ignore=None):
        ig = ignore
        # Convert None to an empty list
        if ig is None:
            ig = []
        # Convert string to tuple containing string
        elif isinstance(ig, str):
            ig = [ig]
        elif not isinstance(ig, list):
            ig = list(ig)

        # These tags are affected by the Spiral tween
        tags = {"spiral", "complex", "3d"}

        # Create new figure which will be the tweened figure
        # Initialize it to a copy of self.
        newfig = self.copy()

        # Perform spiral tween on all relevant tweenables
        for tweenable in self._state.values():
            # Skip this tweenable if it contains the "nospiral" tag,
            # or is in the ignore list, or is not in the tag list.
            if tweenable.tags.isdisjoint(tags) or "nospiral" in tweenable.tags or "notween" in tweenable.tags \
                or tweenable.name in ig:
                continue

            # Since tweenSpiral() is acting, prevent tweenLinear() from acting
            # on this tweenable later on.
            ig.append(tweenable.name)

            P = tweenable.value
            Q = other._state[tweenable.name].value

            # Convert into np.arrays with at least 1 dimension
            P = np.array(P)
            Q = np.array(Q)
            if P.size == 1:
                P.shape = 1
            if Q.size == 1:
                Q.shape = 1

            # Perform spiral tween
            if "3d" in tweenable.tags:
                tw = morpho.spiralInterpArray3d(P, Q, t).squeeze()
            else:
                tw = morpho.spiralInterpArray(P, Q, t).squeeze()

            if isinstance(tweenable.value, (list, tuple)):
                tw = type(tweenable.value)(tw)
            newfig._state[tweenable.name].value = tw

        # Use tweenLinear() on the remaining tweenables that this tween method
        # did not act on (e.g. scalars)
        # print(ig)
        # newfig = newfig.tweenLinear(other, t, ignore=ig)
        newfig = Figure.tweenLinear(newfig, other, t, ignore=ig)

        return newfig

    # DEPRECATED!
    @morpho.TweenMethod
    def tweenSpiral_old(self, other, t):
        # First do a linear tween, so that scalars and whatnot are handled.
        newfig = self.tweenLinear(other, t)

        # These tags are affected by the Spiral tween
        tags = {"complex", "position", "vector"}

        # Check if this figure has a winding number tweenable
        if "winding number" in self.allTags() \
            and "winding number" in other.allTags():
            for name in self._state:
                tweenable = self._state[name]
                if "winding number" in tweenable.tags:
                    self_wind = tweenable.value
                    other_wind = other._state[name].value
                    windName = name
                    break
        else:
            self_wind = None
            other_wind = None

        for tweenable in self._state.values():
            # Skip this tweenable if it contains the "nospiral" tag.
            if "nospiral" in tweenable.tags: continue
            # If the tweenable contains some of the target tags, then...
            if not tweenable.tags.isdisjoint(tags):
                if "list" not in tweenable.tags:
                    listMode = False
                    P = [tweenable.value]
                    Q = [other._state[tweenable.name].value]
                else:
                    listMode = True
                    P = tweenable.value
                    Q = other._state[tweenable.name].value

                for i in range(len(P)):
                    p = P[i]
                    q = Q[i]
                    if type(p) in (list, tuple):
                        p = p[0] + 1j*p[1]
                    if type(q) in (list, tuple):
                        q = q[0] + 1j*q[1]
                    p = complex(p)
                    q = complex(q)

                    r1 = abs(p)
                    r2 = abs(q)

                    # Compute angle changes
                    if self_wind is not None:
                        th1 = (cmath.phase(p) % tau) + self_wind*tau
                        th2 = (cmath.phase(q) % tau) + other_wind*tau
                        dth = th2 - th1
                    else:
                        th1 = cmath.phase(p) % tau
                        th2 = cmath.phase(q) % tau
                        dth = argShift(th1, th2)

                    dr = r2 - r1

                    r = morpho.numTween(r1, r2, t)
                    th = th1 + t*dth

                    # FUTURE: Complex should be converted back into whatever
                    # vectory type it was in originally.
                    if listMode:
                        newfig._state[tweenable.name].value[i] = r*cmath.exp(th*1j)
                    else:
                        newfig._state[tweenable.name].value = r*cmath.exp(th*1j)
                        # Compute new winding number
                        if self_wind is not None:
                            newfig._state[windName].value = int(th // tau)

        return newfig

    # This is not *technically* a tween method, but rather a tween method generator.
    # Given an angle (in radians), it returns a tween method that results in a
    # "pivoting" motion of the figure. The higher the angle, the wider the arc it
    # travels. Positive angle means counter-clockwise movement, negative means
    # clockwise.
    #
    # By default, angle = tau/2 = pi radians which means the movement is along
    # a counter-clockwise, semicircular path.
    # Specifying a negative angle will make the movement clockwise.
    #
    # The tween method generated will act on all tweenables containing the tags
    # "complex" or "pivot".
    # Including the tag "nopivot" in a tweenable results in tweenPivot()
    # ignoring that tweenable, but that tweenable will instead be acted upon
    # by tweenLinear() as a non-pivotable tag, unless tweenLinear() is also
    # prevented from acting on that tweenable. To prevent a tweenable from
    # being acted on AT ALL by tweenPivot() (including downstream tween methods),
    # use the "notween" tag.
    @classmethod
    def tweenPivot(cls, angle=tau/2, ignore=None):

        # @morpho.TweenMethod(splitter=pivotSplit)
        @pivotTweenMethod(cls.tweenPivot, angle, ignore)
        def pivot(self, other, t):

            # If angle is 0, then throw error
            if angle % tau == 0:
                raise ValueError("Angle is a multiple of 2pi. Can't tween!")

            # # First do a linear tween, so that scalars and whatnot are handled.
            # if linearIgnore is None:
            #     newfig = self.tweenLinear(other, t)
            # else:
            #     newfig = self.tweenLinear(other, t, linearIgnore)

            # "ig" is used instead of reassigning "ignore" because otherwise
            # Python will not read the ignore variable from the outer scope
            # and will instead throw a "referenced before assignment" error.
            ig = ignore
            # Convert None to an empty list
            if ig is None:
                ig = []
            # Convert string to tuple containing string
            elif isinstance(ig, str):
                ig = [ig]
            elif not isinstance(ig, list):
                ig = list(ig)

            # # Convert linearIgnore into a list (not a tuple!).
            # # "linIg" is used like "ig" to prevent referencing before assignment.
            # linIg = linearIgnore
            # if linIg is None:
            #     linIg = []
            # elif isinstance(linIg, str):
            #     linIg = [linIg]
            # elif not isinstance(linIg, list):
            #     linIg = list(linIg)

            # # linIg will keep track of the tweenables tweenPivot() acts on, so that
            # # they are not acted on by tweenLinear() later on in the code.
            # linIg = []

            # These tags are affected by the Pivot tween
            tags = {"pivot", "complex"}

            # Create new figure which will be the tweened figure
            # Initialize it to a copy of self.
            newfig = self.copy()

            for tweenable in self._state.values():
                # Skip this tweenable if it contains the "nopivot" tag,
                # or is in the ignore list, or is not in the tag list.
                if tweenable.tags.isdisjoint(tags) or "nopivot" in tweenable.tags or "notween" in tweenable.tags \
                    or tweenable.name in ig:
                    continue

                # Since tweenPivot() is acting, prevent tweenLinear() from acting
                # on this tweenable later on.
                ig.append(tweenable.name)

                P = tweenable.value
                Q = other._state[tweenable.name].value
                if isinstance(P, list) or isinstance(P, tuple) \
                    or isinstance(P, np.ndarray):
                    listMode = True
                else:
                    listMode = False
                    P = [P]
                    Q = [Q]

                # if "list" not in tweenable.tags:
                #     listMode = False
                #     P = [tweenable.value]
                #     Q = [other._state[tweenable.name].value]
                # else:
                #     listMode = True
                #     P = tweenable.value
                #     Q = other._state[tweenable.name].value

                # Perform pivot tween on each component
                for i in range(len(P)):
                    p = P[i]
                    q = Q[i]
                    if type(p) in (list, tuple):
                        p = p[0] + 1j*p[1]
                    if type(q) in (list, tuple):
                        q = q[0] + 1j*q[1]
                    p = complex(p)
                    q = complex(q)

                    # m = (p+q)/2
                    # c = m + 1j*(m-p)*cot(angle/2)  # Center of pivot

                    c = arcCenter(p, q, angle)

                    # Compute tweened value based on pivot
                    tw = (p-c)*cmath.exp(t*angle*1j) + c

                    # FUTURE: Complex should be converted back into whatever
                    # vectory type it was in originally.
                    if listMode:
                        newfig._state[tweenable.name].value[i] = tw
                    else:
                        newfig._state[tweenable.name].value = tw

            # Use tweenLinear() on the remaining tweenables that this tween method
            # did not act on (e.g. scalars)
            # print(ig)
            # newfig = newfig.tweenLinear(other, t, ignore=ig)
            newfig = Figure.tweenLinear(newfig, other, t, ignore=ig)

            return newfig

        return pivot

    # Simplest tween method. Is constantly the original self until t=1 is
    # reached, where it instantly becomes the new figure: other.
    @morpho.TweenMethod
    def tweenInstant(self, other, t):
        if t < 1:
            return self.copy()
        else:
            return other.copy()

    # tweenStep = tweenJump = tweenInstant  # Alternate names

### BUILT-IN ACTIONS ###

# Actions from morpho.actions supported as native methods
# of the Actor class.
# Future: Maybe find some way to auto-create these methods
# from the morpho.actions module? For now, they're hard-coded in.

# Equivalent to morpho.actions.fadeIn(self)
@Figure.action
def fadeIn(self, *args, **kwargs):
    morpho.actions.fadeIn(self, *args, **kwargs)

    # Yes, I really mean None. I think returning self
    # here may be a bad convention. I think a good convention
    # is no method that adds new keys to the timeline should
    # return self.
    return None

# Equivalent to morpho.actions.fadeOut(self)
@Figure.action
def fadeOut(self, *args, **kwargs):
    morpho.actions.fadeOut(self, *args, **kwargs)
    return None

# Equivalent to morpho.actions.rollback(self)
@Figure.action
def rollback(self, *args, **kwargs):
    morpho.actions.rollback(self, *args, **kwargs)
    return None

# Causes the actor to vanish and reappear the specified
# number of times for the specifed total duration.
@Figure.action
def blink(actor, duration=15, atFrame=None, *, times=1):
    if atFrame is None:
        atFrame = actor.lastID()

    for n in range(2*times):
        fig = actor.newkey(atFrame + n*duration/(2*times-1))
        fig.visible = not fig.visible  # Toggle visibility

# Moves a figure by a given displacement vector (given as a
# complex number for 2D figures, else a numpy 3-vector).
# Additionally, the duration of the animation can be specified.
# Default: 30 frames.
#
# Note this action assumes the target actor's figure type
# possesses either a `pos` or `origin` attribute.
# If a figure possesses both, only `pos` will be used.
@Figure.action
def move(actor, vector, duration=30):
    # if vector is None:
    #     raise ValueError("No movement vector given.")

    fig = actor.newendkey(duration)
    if hasattr(fig, "pos"):
        fig.pos = fig.pos + vector  # Don't use += for sake of np.arrays!
    elif hasattr(fig, "origin"):
        fig.origin = fig.origin + vector  # Don't use += for sake of np.arrays!
    else:
        raise TypeError(f"`{type(fig).__name__}` figure has neither `pos` nor `origin` attribute.")

# Animates the current latest keyfigure in the actor morphing
# into itself from a given source figure. Useful as an opening
# animation to create a new figure morphing out of a copy of
# another figure.
#
# `source` can also be an actor, in which case, its latest
# keyfigure is taken as the source figure.
@Figure.action
def morphFrom(actor, source, duration=30, atFrame=None):
    if duration < 2:
        raise ValueError("Duration must be at least 2 frames.")
    if atFrame is None:
        atFrame = actor.lastID()
    if isinstance(source, Actor):
        source = source.last()

    # Save a copy of the latest keyfigure to use as the
    # target ending figure.
    fig0 = actor.last()
    target = fig0.copy()
    fig0.visible = False

    # Create new key for the start of the morph.
    # It should be equal to the given source figure
    # except for the metasettings (tween method, transition, etc.)
    fig1 = actor.newkey(atFrame, source.copy())
    fig1._updateSettings(fig0, includeTweenMethod=True, includeModifier=True)
    fig1.set(visible=True)

    # Set destination figure to be the original last keyfigure.
    actor.newendkey(duration, target)

    # Keep only the first frame AFTER atFrame.
    # We take a copy of the intial keyframe because we're not
    # going to rely on creating perfectly seamless intermediate
    # keyfigures (e.g. MultiText doesn't split tweens seamlessly).
    actor.newkey(atFrame+1, actor.time(atFrame).copy())
    # Doing invisibility instead of delkey because preserving
    # the initial keyframe can be important for puppet skits.
    actor.time(atFrame).visible = False
    # actor.delkey(atFrame)


# Base class for certain space figures.
class SpaceFigure(Figure):
    # Default draw method of a SpaceFigure is to assume the
    # primitives() method exists, call it, get all the primitives,
    # and if it's not an empty list, package into a frame and draw.
    def draw(self, camera, ctx):
        primlist = self.primitives(camera)
        if len(primlist) == 0:
            return

        # Package into frame and draw!
        frame = morpho.Frame(primlist)
        frame.draw(camera, ctx)

        # prim = primlist[0]
        # prim.draw(camera, ctx)


### OTHER RELATED FUNCTIONS ###

# Decorator generator returns a decorator that can be used on
# a custom angle-specific pivot tween method. Mainly for use
# in enabling custom tweenPivot() methods to be splittable.
#
# Example usage:
#   @classmethod
#   def tweenPivot(cls, angle=pi):
#       @morpho.Figure.pivotTweenMethod(cls.tweenPivot, angle)
#       def customPivot(self, other, t):
#           ...
#       return customPivot
#
# Any additional arguments passed to pivotTweenMethod() will be
# passed to the methodGenerator as part of the splitter function.
def pivotTweenMethod(methodGenerator, angle, *args, **kwargs):
    # This decorator will be returned and should be used to
    # decorate a custom angle-specific pivot tween method.
    def decorator(pivotTween):
        # This is the splitter function that will be attached
        # to the provided angle-specific pivot tween method.
        def pivotSplitter(t, beg, mid, fin):
            # Split the angles
            angle1 = t*angle
            angle2 = (1-t)*angle

            # Generate the corresponding angle-specific
            # pivot tween methods specific to the provided
            # bound pivot tween method generator.
            beg.tweenMethod = methodGenerator(angle1, *args, **kwargs)
            mid.tweenMethod = methodGenerator(angle2, *args, **kwargs)
        pivotTween = morpho.TweenMethod(pivotTween, splitter=pivotSplitter)
        return pivotTween
    return decorator


# A higher-level structure that collects figures of a common type and
# places them into a timeline.
#
# Construction usually works like this:
# myactor = Actor(myfigure)
#
# which will result in myfigure being assigned to index 0.
# Alternatively, the primary input to the Actor constructor can be
# a figure type, such as: myactor = Actor(Point)
# in which case, the timeline will be empty, but the figureType will
# be set to, in this case, Point.
#
# ATTRIBUTES
# timeline = dict mapping indices to figures (called "keyfigures")
#            Shouldn't be accessed or modified directly most of the time.
#            If the indices are manually modified, you should call update()
# keyIDs   = Internal sorted list of all the key indices. Updated when
#            update() is called.
# figureType = Records the type of figure this actor is constructed from
#              e.g. Point, Path, Polygon, etc.
# visible = Boolean indicating whether the actor should be drawn by
#           higher level structures like layers. Default: True
#
# CLASS ATTRIBUTES
# persist = Boolean indicating whether the actor should continue to be
#           drawn for indices after its last index. Default: True
class Actor(object):

    def __init__(self, figure, visible=True):

        # A dict of figures indexed by figure index (i.e. frame number).
        # NOTE: Normally, you should treat timeline indices as read-only,
        # and only modify it using methods like newkey(). However, if you
        # need to modify the timeline indices directly, be sure to call
        # the update() method afterward so that self.keyIDs is updated.
        self.timeline = {}
        self.keyIDs = []  # A sorted list of the timeline's keyindices.

        # If supplied an actual figure, initialize the Actor by
        # assigning the given figure to index zero.
        if isinstance(figure, Figure):
            self.figureType = type(figure)
            self.newkey(0, figure, seamless=False)
        # Else if supplied an actual figure subclass, assign it to
        # the figureType attribute.
        elif issubclass(figure, Figure):
            self.figureType = figure
        # Otherwise, throw error.
        else:
            raise TypeError("Actor() takes either a figure or a figure class.")

        self.visible = visible
        self.owner = None
        # Dict mapping time index to a figure. Mainly used
        # by the now() method to be more efficient when
        # multiple now() calls are made at a single point
        # in the timeline.
        self.timeCache = dict()

    # Updates the keyIDs list according to the timeline.
    # This method is mainly for internal use by other methods that may
    # modify the timeline in unpredictable ways.
    def update(self):
        self.keyIDs = list(self.timeline.keys())
        self.keyIDs.sort()
        self._updateOwnerships()

    # Assigns this actor to the `owner` attribute of all
    # component figures.
    def _updateOwnerships(self):
        for fig in self.keys():
            fig.owner = self

    # Makes a deep-ish copy of the actor.
    # Assumes all figures in the timeline are distinct.
    def copy(self):
        new = Actor(self.figureType, self.visible)
        for f in self.timeline:
            new.timeline[f] = self.timeline[f].copy()
        new.update()
        return new

    # If attribute doesn't exist, searches the figure type's
    # registry of action names. Upon failure, searches thru
    # the entire MRO in order until a match is found.
    def __getattr__(self, name):
        for cls in self.figureType.mro():
            try:
                actionFunc = cls.actions[name]
                return lambda *args, **kwargs: actionFunc(self, *args, **kwargs)
            except (AttributeError, KeyError):
                continue

        # Should throw error
        object.__getattribute__(self, name)


    # Returns the i-th keyfigure in the timeline.
    def _keyno(self, i):
        return self.timeline[self.keyIDs[i]]

    # Returns the i-th keyfigure in the timeline when subscripted:
    # firstkey = myactor.key[0]
    # Also can replace keys either by key number or by object:
    #   myactor.key[0] = newfig  # Replace first key
    #   myactor.key[keyfig] = newfig  # Replace keyfig with newfig
    # Segments of actors can also be extracted with this syntax:
    # myactor.key[i:j]
    # which extracts a subactor starting from the i-th keyfigure
    # and ending with the (j-1)-st keyfigure, inclusive.
    @property
    def key(self):
        return _KeyContainer(self)

    # Same as self.timeline.values()
    def keys(self):
        return self.timeline.values()

    # Returns the first keyID coming before the given index.
    # If given index IS a key, finds the preceding one.
    # If does not exist, returns -inf.
    def prevkeyID(self, f):
        k = listfloor(self.keyIDs, f-1)
        if k == -1:
            return -oo
        return self.keyIDs[k]

    # Returns the first keyfigure coming before the given index.
    # If given index IS a key, finds the preceding one.
    # If does not exist, returns None.
    def prevkey(self, f):
        keyID = self.prevkeyID(f)
        if keyID == -oo:
            return None
        return self.timeline[keyID]

    # Returns the first keyID coming after the given index.
    # If given index IS a key, finds the next one.
    # If does not exist, returns inf.
    def nextkeyID(self, f):
        k = listceil(self.keyIDs, f+1)
        if k == len(self.keyIDs):
            return oo
        return self.keyIDs[k]

    # Returns the first keyfigure coming after the given index.
    # If given index IS a key, finds the next one.
    # If does not exist, returns None.
    def nextkey(self, f):
        keyID = self.nextkeyID(f)
        if keyID is oo:
            return None
        return self.timeline[keyID]

    # Property returns the first keyfigure in the timeline.
    # Equivalent to self.first(), but supports assignment.
    @property
    def beg(self):
        return self.key[0]

    @beg.setter
    def beg(self, value):
        self.key[0] = value


    # Returns keyfigure with lowest index.
    # Equivalent to calling self.key(0)
    def first(self):
        return self.key(0)

    # # Synonyms for firstkey()
    # minkey = firstkey
    # start = firstkey
    # first = firstkey

    # Property returns the last keyfigure in the timeline.
    # Equivalent to self.last(), but supports assignment.
    @property
    def fin(self):
        return self.key[-1]

    @fin.setter
    def fin(self, value):
        self.key[-1] = value

    # Returns keyfigure with highest index.
    # Equivalent to calling self.key(-1)
    def last(self):
        return self.key(-1)

    # # Synonyms for lastkey()
    # maxkey = lastkey
    # end = lastkey
    # last = lastkey

    # Returns the i-th keyfigure's index in the timeline
    def _keyIDno(self, i):
        return self.keyIDs[i]

    @property
    def keyID(self):
        return _KeyIDContainer(self)

    def haskeyID(self, f):
        # if type(f) is not int:
        #     raise TypeError("Specified index is not an int!")
        return (f in self.timeline)

    def haskey(self, figure):
        return figure in self.timeline.values()

    # Deletes the keyfigure located at index f.
    # Throws error if no keyframe exists at the specified index.
    def delkey(self, f):
        # if type(f) is not int:
        #     raise TypeError("Specified index is not an int!")
        if f not in self.timeline:
            raise KeyError("No keyfigure at given index.")

        # Reset owner attribute
        self.timeline[f].owner = None

        del self.timeline[f]
        self.keyIDs.remove(f)

    # Returns the given keyfigure's position in the timeline.
    # Equivalent: myactor.keyID[keyfig]
    def timeof(self, keyfig):
        try:
            IDno = list(self.timeline.values()).index(keyfig)
            return list(self.timeline.keys())[IDno]
        except ValueError:
            raise ValueError("Given keyfigure is not in the timeline.")

    # Splits tween method and transition to make inserting a new
    # intermediate keyfigure seamless.
    @staticmethod
    def _splitTweenAndTransition(t, beg, mid, fin):
        # Split the tween method
        if morpho.tweenSplittable(beg.tweenMethod):
            beg.tweenMethod.splitter(beg.transition(t), beg, mid, fin)
        # Split the transition function
        func1, func2 = morpho.transitions.split(beg.transition, t)
        beg.transition = func1
        mid.transition = func2

    # Creates a new keyfigure at index f and returns it.
    # If f is ahead of the last keyframe, the new keyfigure
    # will be a copy of the latest keyfigure. If f is before
    # the first keyfigure (or the timeline is empty), the
    # new keyfigure will be the default figure for the actor's
    # figure type. If f is between the first and last
    # keyframes, the new keyfigure will be determined by
    # tweening. This behavior can be overridden by passing
    # a figure as a second argument to newkey(), in which
    # case the given figure will be used as the new keyfigure.
    #
    # In the case of creating a new intermediate keyfigure,
    # newkey() will by default modify the transition functions
    # of the new keyfigure and the previous keyfigure in
    # order to maintain a seamless tween between the original
    # two neighboring keyfigures. This behavior can be
    # disabled by passing in the keyword argument
    # `seamless=False`
    # Also note that this will only work for strictly increasing
    # transition functions.
    #
    # If optional keyword `instant=True` is specified, then the
    # keyfigure immediately preceding the newly created keyfigure
    # will have its static attribute set to True, meaning when played,
    # the actor will jump instantly to the newly created keyfigure
    # and won't do any tweening. However, `instant=True` will be
    # ignored if a keyfigure already exists at the given frame.
    def newkey(self, f, figure=None, *, seamless=True, instant=False):
        f = round(f)

        if f in self.timeline:
            instant = False

        if figure is None:
            # Default new keyfigure is given by tweening.
            figure = self.time(f, copykeys=True)

            # If tweening fails somehow, then new keyfigure
            # is a copy of the previous keyfigure if it exists,
            # else just use the default figure.
            if figure is None:
                k = listfloor(self.keyIDs, f)
                if k == -1:  # If before first keyfigure
                    figure = self.figureType()
                else:  # Else use latest keyfigure
                    # keyID = self.keyIDs[k]
                    figure = self.key(k).copy()
        elif type(figure) is not self.figureType:
            raise TypeError("Given figure is not of actor's figure type.")
        elif figure in self.timeline.values():
            # Copy the figure if it's already in the timeline.
            figure = figure.copy()

        # Adjust transition of previous keyfig so that the
        # insertion of a new keyfigure does not modify the playback
        # of the animation. But only do this if the index is a
        # genuinely new index that is in the middle of the timeline
        if seamless and self.firstID() < f < self.lastID() and f not in self.timeline:
            # raise NotImplementedError
            keyfig1 = self.prevkey(f)
            keyfig2 = self.nextkey(f)
            a,b = self.prevkeyID(f), self.nextkeyID(f)
            t_split = (f-a)/(b-a)
            Actor._splitTweenAndTransition(t_split, keyfig1, figure, keyfig2)

        # Add the figure to the timeline
        self.timeline[f] = figure
        self.update()

        if instant:
            # Set previous key to be static (assuming it exists)
            prevkey = self.prevkey(f)
            if prevkey is not None:
                prevkey.static = True

        return figure

    # Create a new key df-many frames after the current final key.
    # See newkey() for more info.
    # Calling newendkey() without any arguments creates a new key
    # at the end of the GLOBAL timeline.
    # If optional keyword-only argument `glob` is set to True,
    # the new key is created relative to the final frame of the
    # global timeline. This is implicitly done when calling
    # newendkey() argumentless.
    def newendkey(self, df=None, figure=None, *, glob=False, **kwargs):
        # If no df is given, treat it as a global call with df = 0
        if df is None:
            if self.owner is None:
                raise TypeError("newendkey() cannot be called inputless on ownerless actors.")
            glob = True
            df = 0

        # In global mode, use glastID() to find the last index
        if glob:
            lastID = self.glastID()
            # Adjust by time offset because actor timeline is tied
            # to the local timeline of the layer, but we're trying
            # to specify a global time value here.
            if self.owner is not None:
                lastID -= self.owner.timeOffset
        else:
            lastID = self.lastID()

        df = round(df)
        f = lastID + df
        if f == -oo:
            raise IndexError("Actor has no keyframes! End key is undefined.")
        return self.newkey(f, figure, **kwargs)

    # # Adds the given figure to the timeline at the specified index.
    # # Throws error if the given index is already a keyID.
    # def add(self, figure, f):
    #     # Throw error if the given figure's index is already in the
    #     # timeline.
    #     if f in self.timeline:
    #         raise ValueError("Actor already has keyfigure at this index!")

    #     self.timeline[f] = figure
    #     self.keyIDs.insert(1+listfloor(self.keyIDs, f), f)

    # Replace a keyfigure with a different figure.
    # Throws error if specified keyID is not in the timeline.
    # (That's the only difference between it and newkey() )
    def replacekey(self, f, figure, *args, **kwargs):
        if f not in self.timeline:
            raise KeyError("No keyfigure at given index.")
        return self.newkey(f, figure, *args, **kwargs)

    # Changes the index of the keyfig at index old to index new.
    # Throws error if old is not a current key index.
    def movekey(self, old, new):
        old = round(old)
        new = round(new)
        if old not in self.timeline:
            raise KeyError("No keyfigure at given old index.")
        if type(new) is not int:
            raise KeyError("New index is NOT an int.")
        if old == new:
            return
        if new in self.timeline:
            raise ValueError("Target index already has a keyfigure.")
        figure = self.timeline[old]
        self.delkey(old)
        self.newkey(new, figure, seamless=False)

    # reindex = movekey  # Alternative name for movekey()

    # Swaps two keyfigures' indices.
    def swapkeys(self, t1, t2):
        if t1 not in self.keyIDs:
            raise KeyError("First index is not a keyindex.")
        if t2 not in self.keyIDs:
            raise KeyError("Second index is not a keyindex.")

        self.timeline[t1], self.timeline[t2] = self.timeline[t2], self.timeline[t1]

    def firstID(self):
        if len(self.timeline) == 0:
            return oo
        return min(self.timeline)

    # minkeyID = firstkeyID = firstID  # Synonyms for firstID()

    def lastID(self):
        if len(self.timeline) == 0:
            return -oo
        return max(self.timeline)

    # maxkeyID = lastkeyID = lastID  # Synonyms for lastID()

    # Returns the first index in the global timeline.
    # Requires the actor to be owned by a Layer.
    def gfirstID(self):
        if self.owner is None:
            return self.firstID()
        else:
            return self.owner.gfirstID()

    # Returns the last index in the global timeline.
    # Requires the actor to be owned by a Layer.
    def glastID(self):
        if self.owner is None:
            return self.lastID()
        else:
            return self.owner.glastID()

    def __len__(self):
        return max(self.lastID() - self.firstID() + 1, 0)

    # Shifts all keyIDs after but not including the given frame f up.
    # Given f = -oo, shifts every keyID up.
    def shiftAfter(self, f, numFrames):
        if abs(f) != oo:
            f = round(f)
        numFrames = round(numFrames)
        if not isinstance(numFrames, int):
            raise TypeError("numFrames must be an int!")
        if numFrames < 0:
            raise ValueError("numFrames must be a positive int!")

        f += 1
        keyIDs = list(self.timeline)
        keyIDs.sort()
        a = listceil(keyIDs, f)
        for i in range(len(keyIDs)-1, a-1, -1):
            keyID = keyIDs[i]
            self.movekey(keyID, keyID + numFrames)

        return self

    # Shifts all keyIDs before but not including the given frame down.
    # Given f = oo, shifts every keyID down.
    def shiftBefore(self, f, numFrames):
        if abs(f) != oo:
            f = round(f)
        numFrames = round(numFrames)
        if not isinstance(numFrames, int):
            raise TypeError("numFrames must be an int!")
        if numFrames < 0:
            raise ValueError("numFrames must be a positive int!")

        f -= 1
        keyIDs = list(self.timeline)
        keyIDs.sort()
        b = listfloor(keyIDs, f)
        for i in range(0, b+1):
            keyID = keyIDs[i]
            self.movekey(keyID, keyID - numFrames)

        return self

    # Shifts ALL the keyIDs by the given number of frames.
    # numFrames can be a positive or negative int.
    def shift(self, numFrames):
        if numFrames > 0:
            self.shiftAfter(-oo, numFrames)
        elif numFrames < 0:
            self.shiftBefore(oo, -numFrames)
        return self

    # Shifts the timeline so that the lowest keyID is zero.
    def rezero(self):
        if len(self.timeline) > 0:
            self.shift(-self.firstID())
        return self

    # Reverses the order of keyindices, making the actor
    # play in reverse.
    # This is done in place to the actor, and the actor's position
    # in its timeline is unaffected.
    #
    # However, note that this method does not modify any keyfigure's
    # transition or tween method, so the actor may not play
    # perfectly in reverse depending on the nature of these settings.
    def reverse(self):
        if len(self.keys()) <= 1:
            return
        newTimeline = {}
        start = self.firstID()
        end = self.lastID()
        for keyID, keyfig in self.timeline.items():
            newTimeline[start+end-keyID] = keyfig
        self.timeline = newTimeline
        self.update()

    # Compresses or expands keyIDs so as to slow down or speed up playback.
    # Optionally specify parameter "center" which denotes an index that
    # will be unaffected by the speed change.
    def speedUp(self, factor, center=0):
        # Note: Remember keyIDs are always ints, so you'll need to round!
        # Implement this by going thru the sorted list of key indices
        # and building a new timeline with the adjusted indices.
        # It's important to go thru the key indices IN ORDER so that
        # if there is an index collision, the LATER index is favored.
        timeline = {}
        for keyID in self.keyIDs:
            newID = round((keyID - center)/factor + center)
            timeline[newID] = self.timeline[keyID]

        self.timeline = timeline
        self.update()

        return self


    # Inverse of speedUp()
    def slowDown(self, factor, center=0):
        self.speedUp(1/factor, center)
        return self


    # Inserts "padding" time before and after a given time interval.
    # What it really does is shift all the keyIDs below and above the
    # given time segment [a,b] (inclusive) by the specified number
    # of frames.
    # If b is unspecified, it defaults to a.
    # numBefore & numAfter are optional args whereby you can specify
    # asymmetric padding. This can be done on top of symmetric
    # padding.
    def pad(self, a, b=None, numFrames=0, numBefore=0, numAfter=0):
        if b is None:
            b = a

        self.shiftBefore(a, numFrames + numBefore)
        self.shiftAfter(b, numFrames + numAfter)

    # Returns a "subactor" copy of the original actor between
    # the specified start and end time indices (inclusive).
    # If unspecified, `start` and `end` will be set to the
    # first and last keyindices respectively.
    #
    # OPTIONAL KEYWORD-ONLY INPUTS
    # seamless = Boolean which if set to True, modifies the
    #       starting and ending keyfigures of the resulting subactor
    #       so that it plays (hopefully) exactly like the original
    #       actor. Default: True.
    # rezero = Boolean determining whether the subactor will be
    #       rezeroed before being returned. Default: True.
    def segment(self, start=None, end=None, *, seamless=True, rezero=True):
        # POSS FUTURE: Implement this via python's slicing commands.
        # But keep in mind, we already have a slicing feature
        # using the syntax key[a:b]

        if len(self.timeline) == 0:
            return Actor(self.figureType)

        if start is None:
            start = self.firstID()
        if end is None:
            end = self.lastID()

        if start > end:
            raise ValueError("Start time must be before end time.")

        start = round(start)
        end = round(end)

        # Get the smallest possible "clean" subactor containing
        # `start` and `end` (i.e. subactor bounded by keyfigures).
        a = max(0, listfloor(self.keyIDs, start))
        b = min(len(self.keyIDs)-1, listceil(self.keyIDs, end))

        # Create a new actor with the keys found in self between
        # the times a and b.
        subactor = Actor(self.figureType)
        for keyID in self.keyIDs[a:b+1]:
            subactor.newkey(keyID, self.time(keyID).copy(), seamless=False)

        # Trim the subactor if start or end does not correspond to
        # a keyindex.
        if start > self.keyIDs[a]:
            subactor.newkey(start, self.time(start, copykeys=True), seamless=seamless)
            del subactor.key[0]
        if end < self.keyIDs[b]:
            subactor.newkey(end, self.time(end, copykeys=True), seamless=seamless)
            del subactor.key[-1]

        if rezero:
            subactor.rezero()

        return subactor

    # subactor = segment  # Alternate name for segment()

    # NOT IMPLEMENTED!
    # Like segment(), but removes the given subactor from
    # the given actor.
    def remove(self, start=None, end=None, *args, **kwargs):
        raise NotImplementedError

    # NOT IMPLEMENTED!
    # Does both segment() and remove() simult.
    def cut(self, start=None, end=None, *args, **kwargs):
        raise NotImplementedError

    # Inserts the given actor into self.
    # By default it appends it to the end, but this can be changed
    # with the optional argument afterFrame.
    # Optionally, the keyword-only argument `atFrame` can be set
    # instead, which will insert the actor BEFORE the specified frame.
    # Optional keyword-only `timeOffset` can be set to an integer
    # to offset the target index by a certain number of frames.
    def insert(self, actor, afterFrame=None, *, atFrame=None, timeOffset=0):
        # Check type compatibility
        if actor.figureType is not self.figureType:
            raise TypeError("Can't insert actor of different figure type!")

        # atFrame overwrites afterFrame if specified.
        if atFrame is not None:  # and afterFrame is None:
            afterFrame = atFrame - 1

        # afterFrame defaults to maxkeyID, or zero in case self is
        # an empty actor.
        if afterFrame is None:
            afterFrame = self.lastID()
            if afterFrame == -oo:
                afterFrame = 0

        afterFrame += timeOffset

        # Make some room for the incoming actor!
        self.shiftAfter(afterFrame, len(actor))

        start = actor.firstID()
        for keyID in actor.timeline:
            self.newkey(keyID-start+afterFrame+1, actor.timeline[keyID], seamless=False)

    # Alternate name for insert() is paste()
    # paste = insert

    # For internal use only by Films (Frame Actors).
    # Merges a given film into self IN PLACE.
    # Note that the secondary film may get modified by this function.
    def _mergeFilm(self, film):
        # film = film.copy()

        # Aliases to save on function calls and that remember
        # the original state of the actors before modification
        # in the code below.
        self_firsttime = self.firstID()
        self_lasttime = self.lastID()
        film_firsttime = film.firstID()
        film_lasttime = film.lastID()

        # Manually create a new initial keyframe. This is to
        # prevent the default behavior of newkey() to create a
        # default (i.e. blank) keyfigure if it occurs before
        # the earliest keyframe in the timeline.
        mintime = min([self_firsttime, film_firsttime])
        self.newkey(mintime, self.first().copy())
        film.newkey(mintime, film.first().copy())

        # Sorting is useful to prevent unnecessary tween method
        # splitting for later keyfigures.
        keytimes = sorted(set(self.keyIDs).union(film.keyIDs))

        # Create the "trivial" new keyfigures that occur before
        # and after the original first keyfigure and final keyfigure
        # in both self and film. This is done in such a way as to
        # only call Actor.update() once after it's over, thereby
        # providing a time save.
        # Note that this clause may obsolete the earlier clause
        # where we manually created a new initial keyframe, but
        # I'm keeping it just to be on the safe side.
        for keytime in keytimes:
            if not(self_firsttime <= keytime <= self_lasttime) and keytime not in self.timeline:
                self.timeline[keytime] = self.timeline[constrain(keytime, self_firsttime, self_lasttime)].copy()
            if not(film_firsttime <= keytime <= film_lasttime) and keytime not in film.timeline:
                film.timeline[keytime] = film.timeline[constrain(keytime, film_firsttime, film_lasttime)].copy()
        self.update()
        film.update()

        # Seamlessly introduce new keyframes into secondary film
        # corresponding to the keyframes of self. This
        # way, the secondary film will still animate identically
        # after being merged into the (possibly crowded) timeline
        # of self.
        for keytime in keytimes:
            # These conditional checks actually provide a
            # significant time save if there are many keytimes!
            if keytime not in self.timeline: self.newkey(keytime)
            if keytime not in film.timeline: film.newkey(keytime)
        # Likewise, add new keyframes to self from those
        # uniquely in film and then merge keyframes across the
        # two films.
        for keytime in keytimes:
            # Manual merge is done here instead of calling `merge()`
            # because all we really want to do here is extend the
            # figure list and not do any special merge effects like
            # taking top-level transformations into account and
            # adjusting subfigures (e.g. in TransformableFrame).
            self.time(keytime).figures.extend(film.time(keytime).figures)

        return self

    # Combines all the given actors into a single Frame actor.
    # Optional keyword `stagger` can be specified to offset each
    # actor from the previous in the sequence by a certain number of
    # frames.
    # Optional keyword `template` is an empty Frame or Frame subtype
    # instance that will be used to construct the Actor.
    # Default: morpho.Frame()
    @classmethod
    def zip(cls, *actors, stagger=0, template=None):
        if len(actors) == 0:
            raise TypeError("No actors to zip.")
        if isinstance(actors[0], (list, tuple)):
            actors = actors[0]
        if template is None:
            template = morpho.Frame()

        stagger = aslist(stagger)

        # Turn each individual actor into a singleton Frame Actor
        # (aka "Film") before combining them all into a single Film.
        films = []
        offset = 0
        for n, actor in enumerate(actors):
            actor = actor.copy()
            film = cls(type(template))
            for time, keyfig in actor.timeline.items():
                # Incorporate non-uniform transitions into tween methods
                # since Frame tweening ignores subfigure transitions.
                if keyfig.transition != morpho.transitions.uniform:
                    keyfig.tweenMethod = morpho.transitions.incorporateTransition(keyfig.transition, keyfig.tweenMethod)
                    keyfig.transition = morpho.transitions.uniform
                # Transitions are handled within the tween methods of
                # subfigures, so the toplevel transition of the film
                # should be uniform.
                film.newkey(time+offset, template.copy()).set(figures=[keyfig], transition=morpho.transitions.uniform)
            offset += stagger[n % len(stagger)]
            films.append(film)

        # Combine all the individual singleton films into
        # a single film.
        finalFilm = films[0]
        for film in films[1:]:
            finalFilm._mergeFilm(film)
        # Ensure state of the subfigures of the final keyframe exactly
        # matches the state of the final keys of the supplied actors.
        # Also ensure other settings of the final keyframe matches the
        # template.
        finalFilm.fin = template.copy().set(figures=[actor.last().copy() for actor in actors])

        return finalFilm

    @property
    def subaction(self):
        return self.figureType.subaction(self)

    # NOT IMPLEMENTED!
    # Like insert(), except it overwrites the original actor
    # at the target frame going into the future.
    def overwrite(self, afterFrame=None):
        raise NotImplementedError

    # Returns the first keyID coming before or equal to the given index.
    # If given index IS a key, finds the preceding one.
    # If does not exist, returns -inf.
    def latestkeyID(self, f):
        return self.prevkeyID(f+1)

    # Returns the first keyfigure coming before or equal to the given index.
    # If given index IS a key, finds the preceding one.
    # If does not exist, returns None.
    def latestkey(self, f):
        return self.prevkey(f+1)

    # Returns a figure interpolated based on the given frame index f
    # and the actor's timeline. If f is a key index, it will return
    # the key figure.
    # Optionally specify the latest key index. This is mainly used
    # internally for performance reasons. You probably don't need
    # to worry about it.
    # If optional keyword argument copykeys is set to True,
    # if a keyfigure is returned, a copy will be returned instead.
    # Also mainly for internal use.
    #
    # `_skipTrivialTweens` is a hidden keyword-only argument mainly
    # for internal use which tells time() to use the
    # _static_acute attribute
    # of a figure to decide whether tweening is necessary.
    # By default, it's False so tweening behaves exactly as
    # expected.
    #
    # If `keepOwner` is set to True, the returned figure will
    # be guaranteed to possess the same owner as its principle
    # keyfigure. This is mainly for internal use.
    def time(self, f, keyID=None, *,
            copykeys=False, _skipTrivialTweens=False,
            keepOwner=False):
        # If f is a float, but it's really an int, make it an int.
        # This is so searching the timeline dict is done correctly
        # because all the keys in the dict are ints.
        # NOTE: Just learned that keys that are compared as equal are
        # treated as the same key in a dict! So maybe this line is
        # not necessary after all!
        if type(f) is float and f == int(f):
            f = int(f)

        # If the given index is a keyindex, just return the keyfig.
        if f in self.timeline:
            keyfig = self.timeline[f]
            return keyfig if not copykeys else keyfig.copy().set(owner=(keyfig.owner if keepOwner else None))

        # Compute the latest keyID on the fly if not provided.
        if keyID is None:
            k = listfloor(self.keyIDs, f)
            if k == -1: return None
            keyID = self.keyIDs[k]
        else:
            k = self.keyIDs.index(keyID)

        # Grab latest keyfigure.
        keyfig = self.timeline[keyID]

        # If we're within the latest keyfig's endlag, just
        # return that keyfig.
        if f <= keyID + keyfig.delay:
            return keyfig if not copykeys else keyfig.copy().set(owner=(keyfig.owner if keepOwner else None))
        # Special case if the latest keyfig is the last keyfig
        # in the timeline. Return None unless actors persist.
        elif keyID == self.keyIDs[-1]:
            if Actor.persist:
                return keyfig if not copykeys else keyfig.copy().set(owner=(keyfig.owner if keepOwner else None))
            else:
                return None
        # If the latest keyframe is static, don't tween.
        elif (_skipTrivialTweens and keyfig._static_acute) or keyfig.static:
            return keyfig if not copykeys else keyfig.copy().set(owner=(keyfig.owner if keepOwner else None))
            # return keyfig.copy()
        else:
            # keyfig2 = self.timeline[keyID+1]
            keyfig2 = self.key(k+1)
            T = morpho.numTween(0, 1, f,
                start=keyID + keyfig.delay,
                end=self.keyIDs[k+1]
                )
            # assert 0 <= T <= 1  # Temporary for testing purposes
            return keyfig.tween(keyfig2, T).set(owner=(keyfig.owner if keepOwner else None))

    # Alternate name for the time method.
    # frame = time

    # Global configuration setting telling whether to use
    # time caching. Mainly for internal use by now() to be
    # more efficient.
    useTimeCache = True

    # Returns the current figure of the actor at the current time
    # index on the global timeline. Only possible if the actor's
    # owner is a Layer whose owner is an Animation object.
    # Mainly for use in puppet Skits to extract the current figure
    # state of the puppeteer actor at the current time index of
    # the animation.
    # Also note that if now() returns a keyfigure, it will be
    # copied before returned, so it is always safe to modify
    # the attributes of a figure returned by now().
    #
    # By default, modifiers will be applied to the returned
    # figure, but this can be disabled by setting the
    # optional keyword input `useModifier` to False.
    def now(self, *, useModifier=True):
        try:
            mation = self.owner.owner
            currentIndex = mation.currentIndex
        except AttributeError:
            raise TypeError("No global timeline to reference.")

        f = currentIndex - self.owner.timeOffset
        # Check if cache can be used
        if Actor.useTimeCache and mation.running and f in self.timeCache \
                and self.timeCache["useModifier"] == useModifier:
            fig = self.timeCache[f].copy()
        else:
            fig = self.time(f, copykeys=True)  # Make a copy in case it's a keyfigure
            if useModifier:
                # No need to make a copy since `fig` is guaranteed
                # to be either a copy or a new figure.
                fig = applyFigureModifier(fig, forceOrig=True)
            if Actor.useTimeCache and mation.running:
                # Replace stored time index.
                self.timeCache.clear()
                self.timeCache[f] = fig.copy()
                self.timeCache["useModifier"] = useModifier

        # Lie and say that self owns this figure so that methods like
        # Text.box() work correctly. I think it's okay for it to lie here since
        # the primary use case of now() is within Skit.makeFrame(), so this lie
        # is unlikely to cause harm.
        fig.owner = self

        return fig

    # Optimizes the Actor for playback by setting keyfigures to be
    # acutely static if it looks like there's no reason to tween
    # them e.g. the starting and ending keyfigures appear equal, or
    # the current keyfigure is invisible (whereby the tweened figure
    # will inherit the invisibility).
    def _optimize(self):
        for n in range(len(self.timeline)-1):
            keyfig = self.key[n]
            keyfigNext = self.key[n+1]
            if not keyfig.visible or keyfig._appearsEqual(keyfigNext):
                keyfig._static_acute = True

    def _deoptimize(self):
        for keyfig in self.keys():
            keyfig._static_acute = False

    # Should the final keyfigure persist after the final frame?
    # If set to True, to make an actor vanish, you will need to
    # make a new final keyframe with visibility attribute set to
    # False.
    persist = True

    # Return a list of all the keyfigures in the timeline in order.
    def listkeys(self):
        return list(self.timeline.values())

    # Return a list of all the indices of all keyfigs in the timeline
    # in order.
    def listkeyIDs(self):
        return self.keyIDs[:]

    # Returns a list of the same length as the number of keyfigs
    # but its items are the given tweenable of all the keyfigs.
    # i.e. it "slices" the actor according to a target tweenable.
    def slice(self, tweenable):
        if isinstance(tweenable, morpho.Tweenable):
            name = tweenable.name
        elif type(tweenable) is str:
            name = tweenable
        else:
            raise ValueError("Tweenable must be either a tweenable or a tweenable's name.")
        return [self.timeline[f]._state[name] for f in self.keyIDs]

    # Tweens all of the non keyindices in advanced.
    # For example, if you have an actor with keyindices at 0 and 30,
    # calling pretween() will pre-compute all the tweened figures
    # between 0 and 30 and insert them into the timeline for the indices
    # 1 thru 29.
    def pretween(self):
        if len(self.timeline) == 0: return

        newfigs = {}
        for f in range(self.keyIDs[0]+1, self.keyIDs[-1]):
            # Get latest keyID and keyfigure
            keyID = self.keyIDs[listfloor(self.keyIDs, f)]
            keyfig = self.timeline[keyID]

            # Compute the tweened figure at time(f).
            # If it is different from the latest keyfigure,
            # add it to the dict of new figures.
            twfig = self.time(f)
            if twfig is not keyfig:
                newfigs[f] = twfig

        # Now put in the new figures!
        for f in newfigs:
            self.newkey(f, figure=newfigs[f], seamless=False)


    # Draws the actor at the specified time.
    def draw(self, f, camera, ctx):
        # Check if previous keyID is visible.
        k = listfloor(self.keyIDs, f)
        if k == -1: return

        keyID = self.keyIDs[k]
        keyfig = self.timeline[keyID]

        # Don't bother drawing anything if previous keyfig is invisible.
        if not keyfig.visible:
            return

        # Previous keyfig exists AND is visible, so proceed normally.
        figure = self.time(f, keyID)
        if figure is None:
            return
        figure.draw(camera, ctx)

    ### MERGING CONVENIENCE METHODS ###

    # NOT IMPLEMENTED!
    # Merges the actor to the given target object (a layer or animation)
    # and then returns self.
    # Equivalent to target.merge(self)
    def mergeTo(self, target, *args, **kwargs):
        raise NotImplementedError
        target.merge(self, *args, **kwargs)
        return self

    # NOT IMPLEMENTED!
    # Appends the actor to the given target object (a layer or animation)
    # and then returns self.
    # Equivalent to target.append(self)
    def appendTo(self, target, *args, **kwargs):
        raise NotImplementedError
        target.append(self, *args, **kwargs)
        return self



class _KeyContainer(object):
    def __init__(self, actor):
        self.actor = actor

    def __getitem__(self, i):
        # Handle slice
        if isinstance(i, slice):
            start = i.start
            stop = i.stop
            step = i.step
            if step is not None:
                raise TypeError("Slice steps are not supported for actor slicing.")
            if start is None:
                start = 0
            if stop is None:
                stop = -1
            return self.actor.segment(self.actor.keyID[start], self.actor.keyID[stop-1])

        return self.actor._keyno(i)

    def __setitem__(self, i, value):
        if isinstance(i, Figure):
            self.actor.replacekey(self.actor.timeof(i), value)
            return
        self.actor.replacekey(self.actor.keyID(i), value)

    def __delitem__(self, i):
        if isinstance(i, Figure):
            self.actor.delkey(self.actor.timeof(i))
            return
        self.actor.delkey(self.actor.keyID[i])

    def __call__(self, i):
        return self[i]

class _KeyIDContainer(object):
    def __init__(self, actor):
        self.actor = actor

    def __getitem__(self, i):
        if isinstance(i, Figure):
            return self.actor.timeof(i)

        return self.actor._keyIDno(i)

    def __delitem__(self, i):
        self.actor.delkey(self.actor.keyID[i])

    def __call__(self, i):
        return self[i]


### HELPERS ###

# Mainly for internal use.
# Applies a figure's modifier to (a copy of) itself if it
# exists and returns the modified figure.
# By default, if the figure has no modifier, it is returned
# without being copied. Otherwise, a copy is created,
# modified, and returned.
# But if optional keyword `forceOrig=True`, then a copy will
# not be made, and the original figure will be modified.
def applyFigureModifier(fig, *, forceOrig=False):
    if fig.modifier is None:
        return fig

    if not forceOrig:
        # Figure is copied because we don't want the
        # modifier to actually modify the original
        # keyfigures of the actor.
        # This can alternatively be solved by setting
        # `copykeys=True` in the time() call in Layer.draw(),
        # but I think that is less efficient, since
        # copying complex figures like LaTeX MultiSplines
        # can be slow.
        fig_orig = fig
        fig = fig.copy()
        # Assign copy's owner to be the original figure's owner.
        # This is technically a lie, but it's important to make
        # things like Text.box() work. I think it's okay to lie
        # here since this copy's only job is to be drawn and then
        # deleted. It won't persist.
        fig.owner = fig_orig.owner
    fig.modifier(fig)
    return fig

# Flattens a list of lists into a single list.
# Thanks to Alex Martelli on StackOverflow
# https://stackoverflow.com/a/952952
def flattenList(L): return [item for sublist in L for item in sublist]

# Checks if `obj` has `name` as an attribute in the strict
# sense of the base object class.
# Essentially equivalent to `name in dir(obj)`, but it does it
# much faster by calling object.__getattribute__(obj, name) and
# catching AttributeError and absorbing any other exceptions.
def object_hasattr(obj, name):
    try:
        object.__getattribute__(obj, name)
    except AttributeError:
        return False
    except Exception:
        # Absorb any other exceptions because (in theory) the only
        # way object.__getattribute__() can throw any other
        # exception is if some property of `obj` threw the exception
        # as part of being accessed, which of course means the
        # property exists and so we should return True.
        pass
    return True
