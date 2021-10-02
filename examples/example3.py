import morpholib as morpho
morpho.importAll()

from morpholib.tools.basics import *
from morpholib.video import *

import math, cmath

# morpho.transitions.default = morpho.transitions.quadease

def spiralPoint():
    # Place a default grid in the background just to
    # make the motion clearer
    gridBG = morpho.grid.mathgrid()

    # Setup point at the coordinates (3,2)
    mypoint = morpho.grid.Point(3+2j)
    # Set the tween method to be the Point class's
    # spiral tween method.
    mypoint.tweenMethod = morpho.grid.Point.tweenSpiral

    # Convert to an actor, and change the position to (-1,0)
    # over the course of 1 second (30 frames).
    mypoint = morpho.Actor(mypoint)
    mypoint.newendkey(30)
    mypoint.last().pos = -1

    movie = morpho.Animation(morpho.Layer([gridBG, mypoint]))
    movie.play()

def spiralPath():
    # Setup a standard grid, but with the spiral
    # tween method for a path.
    mygrid = morpho.grid.mathgrid(tweenMethod=morpho.grid.Path.tweenSpiral)

    # Convert to actor and have it tween into a
    # morphed version of itself
    mygrid = morpho.Actor(mygrid)
    fgrid = mygrid.last().fimage(lambda z: z**2/10)
    mygrid.newendkey(60, fgrid)

    movie = morpho.Animation(mygrid)
    movie.play()

def pivotPoint():
    # Place a default grid in the background just to
    # make the motion clearer
    gridBG = morpho.grid.mathgrid()

    # Setup point at the coordinates (3,2)
    mypoint = morpho.grid.Point(3+2j)
    # Set the tween method to be the Point class's
    # pivot tween method, with an angle value of +pi.
    mypoint.tweenMethod = morpho.grid.Point.tweenPivot(-pi)

    # Convert to an actor, and change the position to (-1,0)
    # over the course of 1 second (30 frames).
    mypoint = morpho.Actor(mypoint)
    mypoint.newendkey(30)
    mypoint.last().pos = -1

    movie = morpho.Animation(morpho.Layer([gridBG, mypoint]))
    movie.play()

def spiralThenLinear():
    # Place a default grid in the background just to
    # make the motion clearer
    gridBG = morpho.grid.mathgrid()

    # Setup point at the coordinates (3,2)
    mypoint = morpho.grid.Point(3+2j)
    # Set the tween method to be the Point class's
    # spiral tween method.
    mypoint.tweenMethod = morpho.grid.Point.tweenSpiral
    # Set the initial transition to quadease
    mypoint.transition = morpho.transitions.quadease

    # Convert to an actor, and change the position to the
    # point (-1,0) over the course of 1 second (30 frames).
    mypoint = morpho.Actor(mypoint)
    mypoint.newendkey(30)
    mypoint.last().pos = -1

    # Reassign the tween method at this point to the linear
    # tween method.
    mypoint.last().tweenMethod = mypoint.figureType.tweenLinear
    # Reassign the transition to be the uniform transition
    mypoint.last().transition = morpho.transitions.uniform

    # Create a new keyfigure returning the point to its
    # starting location. The tween method is governed by
    # the previous keyfigure's tween method: tweenLinear()
    mypoint.newendkey(30, mypoint.first().copy())

    movie = morpho.Animation(morpho.Layer([gridBG, mypoint]))
    movie.play()

def invisibility():
    # Initialize point at the origin, but make it big.
    mypoint = morpho.grid.Point(0)
    mypoint.size = 50

    mypoint = morpho.Actor(mypoint)

    # Move point off the left side of the screen
    mypoint.newendkey(30)
    mypoint.last().pos = -6
    mypoint.last().visible = False

    # While invisible, move to being off the
    # right side of the screen
    mypoint.newendkey(15)
    mypoint.last().pos = 6
    mypoint.last().visible = True

    # After being made visible again, move
    # back to the origin.
    mypoint.newendkey(30)
    mypoint.last().pos = 0

    movie = morpho.Animation(mypoint)
    movie.play()

def locatorTest():
    # Setup a default grid
    mygrid = morpho.grid.mathgrid()

    # Turn it into an actor, and morph it into
    # a distorted version
    mygrid = morpho.Actor(mygrid)
    mygrid.newendkey(30, mygrid.first().fimage(lambda z: z**2/10))

    # Setup animation
    movie = morpho.Animation(mygrid)
    # Set the first layer (the zeroth layer)
    # as the locator layer
    movie.locatorLayer = 0
    # Set the initial frame of the animation
    # to be its final frame
    movie.start = movie.lastID()
    movie.play()

def locatorAlt():
    # Setup layer and animation in advance
    mainlayer = morpho.Layer()
    movie = morpho.Animation([mainlayer])

    # Setup a default grid
    mygrid = morpho.grid.mathgrid()

    # Turn it into an actor, and morph it into
    # a distorted version
    mygrid = morpho.Actor(mygrid)
    mygrid.newendkey(30, mygrid.first().fimage(lambda z: z**2/10))

    # Append grid actor to the mainlayer
    mainlayer.append(mygrid)

    # Set the initial frame of the animation
    # to be its final frame
    movie.start = movie.lastID()
    # Set mainlayer to be the locator layer
    movie.locatorLayer = mainlayer
    movie.play()


# spiralPoint()
# spiralPath()
# pivotPoint()
# spiralThenLinear()
# invisibility()
# locatorTest()
# locatorAlt()
