'''
This module contains some helper functions that automate some common
animation actions.
'''

import morpholib as morpho
# import morpho, morpho.anim
# import morpho.grid
# from morpho.tools.basics import *
# import math, cmath

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
#           Default: 0 (meaning all actors begin fading at the same time)
# jump = Displacement each actor should "jump" during the fade out.
#        Example: jump=2j causes each actor to jump up by 2 units;
#        `jump` can also be a list to specify different jump vectors
#        for each actor in the `actors` list. If the list is too short,
#        it will loop back to the start.
#        Default: () empty tuple (meaning no jumps)
def fadeOut(actors, duration=30, atFrame=None, stagger=0, jump=()):
    # if not isinstance(actors, list) and not isinstance(actors, tuple):
    #     actors = [actors]
    # Turn into a list if necessary
    if isinstance(actors, morpho.Actor):
        actors = [actors]

    if atFrame is None:
        atFrame = max(actor.lastID() for actor in actors)

    # If jump isn't a subscriptable type, turn it into a singleton list
    if not hasattr(jump, "__getitem__"):
        jump = [jump]

    for n in range(len(actors)):
        actor = actors[n]
        actor.newkey(atFrame+n*stagger)
        keyfig = actor.newendkey(duration)
        keyfig.alpha = 0
        keyfig.visible = False
        if len(jump) > 0:
            dz = jump[n%len(jump)]

            # Add dz in place to either the "pos" or "origin"
            # attributes (if they exist).
            if "pos" in keyfig._state:
                keyfig.pos += dz
            elif "origin" in keyfig._state:
                keyfig.origin += dz
            else:
                raise TypeError(f"{type(keyfig)} figure cannot be jumped.")

# Similar to fadeOut(), but fades in actors from invisibility.
# See fadeOut() for more info.
#
# NOTE: Only works for figures that possess an "alpha" tweenable, so
# this function may not work for custom figures like Skits unless you
# implement an alpha tweenable yourself.
#
# Also note that this function will force alpha=0 for the current
# final keyfigure in each actor before applying the effect.
def fadeIn(actors, duration=30, atFrame=None, stagger=0, jump=()):
    # if not isinstance(actors, list) and not isinstance(actors, tuple):
    #     actors = [actors]
    # Turn into a list if necessary

    if isinstance(actors, morpho.Actor):
        actors = [actors]

    if atFrame is None:
        atFrame = max(actor.lastID() for actor in actors)

    # If jump isn't a subscriptable type, turn it into a singleton list
    if not hasattr(jump, "__getitem__"):
        jump = [jump]

    for n in range(len(actors)):
        actor = actors[n]
        actor.last().alpha = 0
        keyfigInit = actor.newkey(atFrame+n*stagger)
        keyfigInit.visible = True
        keyfig = actor.newendkey(duration)
        keyfig.alpha = 1
        if len(jump) > 0:
            dz = jump[n%len(jump)]

            # Add dz in place to either the "pos" or "origin"
            # attributes (if they exist).
            if "pos" in keyfig._state:
                keyfigInit.pos -= dz
            elif "origin" in keyfig._state:
                keyfigInit.origin -= dz
            else:
                raise TypeError(f"{type(keyfigInit)} figure cannot be jumped.")

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
#           Default: 0 (all actors begin rolling back at the same time)
def rollback(actors, duration=30, atFrame=None, stagger=0):
    # if not isinstance(actors, list) and not isinstance(actors, tuple):
    #     actors = [actors]
    # Turn into a list if necessary
    if isinstance(actors, morpho.Actor):
        actors = [actors]
    if atFrame is None:
        atFrame = max(actor.lastID() for actor in actors)
    for n in range(len(actors)):
        actor = actors[n]
        actor.newkey(atFrame+n*stagger)
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
