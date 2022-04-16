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
# set to False.
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
def fadeOut(actors, duration=30, atFrame=None, stagger=0):
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
        actor.newendkey(duration).alpha = 0
        actor.last().visible = False

# Similar to fadeOut(), but fades in actors from (presumed) invisibility.
# See fadeOut() for more info.
#
# NOTE: Only works for figures that possess an "alpha" tweenable, so
# this function may not work for custom figures like Skits unless you
# implement an alpha tweenable yourself.
#
# Only intended to work for actors whose final keyfigure has alpha = 0.
def fadeIn(actors, duration=30, atFrame=None, stagger=0):
    # if not isinstance(actors, list) and not isinstance(actors, tuple):
    #     actors = [actors]
    # Turn into a list if necessary
    if isinstance(actors, morpho.Actor):
        actors = [actors]
    if atFrame is None:
        atFrame = max(actor.lastID() for actor in actors)
    for n in range(len(actors)):
        actor = actors[n]
        actor.newkey(atFrame+n*stagger).visible = True
        actor.newendkey(duration).alpha = 1

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
