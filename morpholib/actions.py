'''
This module contains some helper functions that automate some common
animation actions.
'''

import morpholib as morpho
from morpholib.tools.basics import aslist
import math

autoJumpNames = {"pos", "origin", "_pos", "_origin"}

# Applies the jump amount `dz` to all supported tweenables
# in the given figure's state
def _applyJump(figure, dz):
    # Add dz in place to all supported tweenables
    for tweenable in figure._state.values():
        if (tweenable.name in autoJumpNames and "nojump" not in tweenable.tags) \
            or ("jump" in tweenable.tags):

            tweenable.value = tweenable.value + dz

        # This clause works, but doesn't handle alpha.
        # I've decided not to use it for now.
        # elif "figures" in tweenable.tags:
        #     figlist = tweenable.value
        #     for fig in figlist:
        #         _applyJump(fig, dz)

# Convenience function fades out a collection of actors and then
# sets the visibility attribute of the final keyfigure of each actor
# to False. Useful for dismissing actors from a scene.
#
# NOTE: Only works for figures that possess an "alpha" tweenable, so
# this function may not work for custom figures like Skits unless you
# implement an alpha tweenable yourself.
#
# PARAMETERS
# actors = List of actors (or a single actor)
# duration = Duration (in frames) of fade out for each actor.
#            Default: 30
# atFrame = Frame index at which to begin fade out.
#           Default: the latest keyindex among all the given actors.
# stagger = Number of frames to wait between starting fade outs of
#           adjacent actors in the list. Leads to a "staggering" effect.
#           Example: stagger=5 means the second actor will start fading
#           5 frames after the first actor STARTS fading. Likewise,
#           the third actor will begin fading 5 frames after the
#           second actor starts fading, and so on.
#           `stagger` can also be a sequence of numbers for variable
#           stagger values. If the sequence exhausts early, the sequence
#           will repeat.
#           Default: 0 (meaning all actors begin fading at the same time)
# KEYWORD ONLY
# jump = Displacement each actor should "jump" during the fade out.
#        Example: jump=2j causes each actor to jump up by 2 units;
#        `jump` can also be a list to specify different jump vectors
#        for each actor in the `actors` list. If the list is too short,
#        it will loop back to the start.
#        Default: () empty tuple (meaning no jumps)
def fadeOut(actors, duration=30, atFrame=None, stagger=0, *, jump=()):
    # if not isinstance(actors, list) and not isinstance(actors, tuple):
    #     actors = [actors]
    # Turn into a list if necessary
    if isinstance(actors, morpho.Actor):
        actors = [actors]

    stagger = aslist(stagger)

    if atFrame is None:
        atFrame = max(actor.lastID() for actor in actors)

    # # If jump isn't a subscriptable type, turn it into a singleton list
    # if not hasattr(jump, "__getitem__"):

    # If jump isn't a list or tuple, turn it into one.
    if not isinstance(jump, list) and not isinstance(jump, tuple):
        jump = [jump]

    offset = 0
    for n in range(len(actors)):
        actor = actors[n]
        actor.newkey(atFrame+offset)
        offset += stagger[n % len(stagger)]
        keyfig = actor.newendkey(duration)
        keyfig.alpha = 0
        keyfig.visible = False
        if len(jump) > 0:
            dz = jump[n%len(jump)]
            _applyJump(keyfig, dz)

            # # Add dz in place to all supported tweenables
            # for tweenable in keyfig._state.values():
            #     if (tweenable.name in autoJumpNames and "nojump" not in tweenable.tags) \
            #         or ("jump" in tweenable.tags):

            #         tweenable.value += dz

            # # Add dz in place to either the "pos" or "origin"
            # # attributes (if they exist).
            # if hasattr(keyfig, "pos"):
            #     keyfig.pos += dz
            # elif hasattr(keyfig, "origin"):
            #     keyfig.origin += dz
            # else:
            #     raise TypeError(f"{type(keyfig)} figure cannot be jumped.")

# Similar to fadeOut(), but fades in actors from invisibility.
# See fadeOut() for more info.
#
# UNIQUE PARAMETERS
# alpha = Final alpha value (keyword only).
#         Like `jump`, it can also be a list of alphas to be applied
#         to the actors list.
#
# NOTE: Only works for figures that possess an "alpha" tweenable, so
# this function may not work for custom figures like Skits unless you
# implement an alpha tweenable yourself.
#
# Also note that this function will force alpha=0 and visible=False
# for the current final keyfigure in each actor before applying
# the effect.
def fadeIn(actors, duration=30, atFrame=None, stagger=0, *,
    jump=(), alpha=(1,)):

    # if not isinstance(actors, list) and not isinstance(actors, tuple):
    #     actors = [actors]
    # Turn into a list if necessary

    if isinstance(actors, morpho.Actor):
        actors = [actors]

    if atFrame is None:
        atFrame = max(actor.lastID() for actor in actors)

    stagger = aslist(stagger)

    # # If jump isn't a subscriptable type, turn it into a singleton list
    # if not hasattr(jump, "__getitem__"):

    # If jump isn't a list or tuple, turn it into one.
    if not isinstance(jump, list) and not isinstance(jump, tuple):
        jump = [jump]

    # if not hasattr(alpha, "__getitem__"):
    if not isinstance(alpha, list) and not isinstance(alpha, tuple):
        alpha = [alpha]

    offset = 0
    for n in range(len(actors)):
        actor = actors[n]
        actor.last().set(alpha=0, visible=False)
        keyfigInit = actor.newkey(atFrame+offset)
        offset += stagger[n % len(stagger)]
        keyfigInit.visible = True
        keyfig = actor.newendkey(duration)
        keyfig.alpha = alpha[n%len(alpha)]
        if len(jump) > 0:
            dz = jump[n%len(jump)]
            _applyJump(keyfigInit, -dz)

            # # Subtract dz in place from all supported tweenables
            # for tweenable in keyfigInit._state.values():
            #     if (tweenable.name in autoJumpNames and "nojump" not in tweenable.tags) \
            #         or ("jump" in tweenable.tags):

            #         tweenable.value -= dz

            # # Subtract dz in place from either the "pos" or "origin"
            # # attributes (if they exist).
            # if hasattr(keyfig, "pos"):
            #     keyfigInit.pos -= dz
            # elif hasattr(keyfig, "origin"):
            #     keyfigInit.origin -= dz
            # else:
            #     raise TypeError(f"{type(keyfigInit)} figure cannot be jumped.")

# Convenience function tweens an actor back to its first keyfigure
# and then sets the visibility attribute of the final keyfigure of
# each actor set to False.
#
# Intended to be used when the the first keyfigure of an actor
# is invisible or offscreen. It's a nice way to make an actor
# gracefully leave a scene the same way it entered.
#
# PARAMETERS
# actors = List of actors (or a single actor)
# duration = Duration (in frames) of rollback animation for each actor.
#            Default: 30
# atFrame = Frame index at which to begin rollback animation.
#           Default: the latest keyindex among all the given actors.
# stagger = Number of frames to wait between starting rollbacks of
#           adjacent actors in the list. Leads to a "staggering" effect.
#           Example: stagger=5 means the second actor will start rolling
#           back 5 frames after the first actor STARTS fading. Likewise,
#           the third actor will begin rolling back 5 frames after the
#           second actor starts rolling back, and so on.
#           `stagger` can also be a sequence of numbers for variable
#           stagger values. If the sequence exhausts early, the sequence
#           will repeat.
#           Default: 0 (all actors begin rolling back at the same time)
def rollback(actors, duration=30, atFrame=None, stagger=0):

    stagger = aslist(stagger)

    # Turn into a list if necessary
    if isinstance(actors, morpho.Actor):
        actors = [actors]
    if atFrame is None:
        atFrame = max(actor.lastID() for actor in actors)

    offset = 0
    for n in range(len(actors)):
        actor = actors[n]
        actor.newkey(atFrame+offset)
        offset += stagger[n % len(stagger)]
        actor.newendkey(duration, actor.first().copy())
        actor.last().visible = False

# NOT IMPLEMENTED!
# Transforms one figure into another using a fade effect.
# Requires the underlying figures to have "pos" and "alpha"
# attributes to work.
# Returns an animation in which fig move toward pig while
# fading into pig.
def transform(fig, pig, time=30):
    raise NotImplementedError

# Wiggles the actor by rotating it about its origin point
# a set number of times by a certain angle.
# Note that this is only possible if the actor's figure type
# supports the `rotation` transformation attribute.
#
# INPUTS
# duration = Total duration in frames for action. Default: 30 frames
# atFrame = Initial frame to use. Default: None (latest keyframe)
# KEYWORD-ONLY INPUTS
# rotation = Rotation angle in radians. Can be negative to start with a
#       clockwise rotation. Default: pi/6 (30 degs)
# times = Number of times to rotate by a full swing. Default: 1
def wiggle(actor, duration=30, atFrame=None, *,
        rotation=math.pi/6, times=1):

    if atFrame is None:
        atFrame = actor.lastID()

    path0 = actor.last()
    final = path0.copy()

    tstep = duration / (2*times + 2)
    actor.newkey(atFrame)
    # Not using newendkey() because intermediate rounding
    # may throw off the time coordinates.
    actor.newkey(atFrame + tstep).rotation += rotation
    sign = -1
    for n in range(1, times+1):
        actor.newkey(atFrame + (2*n + 1)*tstep).rotation += sign*2*rotation
        sign *= -1
    actor.newkey(atFrame+duration, final)


# Multi-action summoner
# Mainly for internal use. Used to automatically implement
# morpho.actions.action that automatically implements multi-action
# versions of registered actor actions.
# See "morpho.actions.action" for more info.
class MultiActionSummoner(object):
    @staticmethod
    def getActionFromName(actor, actionName):
        return getattr(actor, actionName)

    # Prepares a given action for use with a particular actor.
    @staticmethod
    def actionDecorator(action, actor):
        def decoratedAction(*args, **kwargs):
            return action(actor, *args, **kwargs)
        return decoratedAction

    def makeMultiAction(self, action):
        def multiaction(actors, *args, stagger=0, **kwargs):
            if isinstance(actors, morpho.Actor):
                actors = [actors]
            elif isinstance(actors, morpho.Layer):
                actors = actors.actors

            stagger = aslist(stagger)

            now = max(actor.lastID() for actor in actors)
            for n,actor in enumerate(actors):
                if isinstance(action, str):
                    try:
                        action_n = self.getActionFromName(actor, action)
                    except AttributeError:
                        raise AttributeError(f"'{actor.figureType.__name__}' does not implement action '{action}'")
                else:
                    action_n = self.actionDecorator(action, actor)

                if now not in actor.timeline:
                    actor.newkey(now)
                action_n(*args, **kwargs)
            if stagger != [0]:
                # Go thru the actors and shift them by the stagger
                # amount starting at the present. Also preserve the
                # keyfigure at the original present time.
                offset = 0
                for n,actor in enumerate(actors[1:], start=1):
                    # Post-action present-state of the actor
                    present = actor.time(now).copy()
                    offset += stagger[n % len(stagger)]
                    actor.shiftAfter(now-1, offset)
                    actor.newkey(now, present, seamless=False)

        return multiaction

    def __getattr__(self, actionName):
        return self.makeMultiAction(actionName)

    def __call__(self, action, *args, **kwargs):
        multiaction = self.makeMultiAction(action)
        return multiaction(*args, **kwargs)

class MultiSubactionSummoner(MultiActionSummoner):
    @staticmethod
    def getActionFromName(actor, actionName):
        return getattr(actor.subaction, actionName)

    @staticmethod
    def actionDecorator(action, actor):
        return actor.subaction.makeSubaction(action)


# Used to automatically implement multi-actions
# for custom actions similar to how fadeIn/Out() and rollback() work.
# For example, if you have implemented an action called "myaction"
# for a certain figure type, and you have a list of actors of that
# figure type, you can apply `myaction` to the whole list, with optional
# `stagger`, using the syntax
#   morpho.action.myaction(myactorlist, *args, [atFrame=etc, stagger=0], **kwargs)
# Please note that a user-specified `atFrame` value must be specified
# by keyword in an auto-generated multi-action. Same with `stagger`.
action = MultiActionSummoner()

# Used to automatically implement multi-subactions used to
# apply a subaction to multiple Frame-like actors.
# See also: `action`
#
# Usage example:
# subaction.fadeIn(actorlist, 20, substagger=3, stagger=10)
subaction = MultiSubactionSummoner()
