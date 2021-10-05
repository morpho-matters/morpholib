'''
This module contains some helper functions that automate some common
animation actions.
'''

import morpholib as morpho
# import morpho, morpho.anim
# import morpho.grid
# from morpho.tools.basics import *
# import math, cmath

# TODO: Add "stagger" argument to both fadeOut() and rollback()

def fadeOut(actors, duration=30, atFrame=None):
    # if not isinstance(actors, list) and not isinstance(actors, tuple):
    #     actors = [actors]
    # Turn into a list if necessary
    if isinstance(actors, morpho.Actor):
        actors = [actors]
    if atFrame is None:
        atFrame = max(actor.lastID() for actor in actors)
    for actor in actors:
        actor.newkey(atFrame)
        actor.newendkey(duration).alpha = 0
        actor.last().visible = False

def rollback(actors, duration=30, atFrame=None):
    # if not isinstance(actors, list) and not isinstance(actors, tuple):
    #     actors = [actors]
    # Turn into a list if necessary
    if isinstance(actors, morpho.Actor):
        actors = [actors]
    if atFrame is None:
        atFrame = max(actor.lastID() for actor in actors)
    for actor in actors:
        actor.newkey(atFrame)
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
