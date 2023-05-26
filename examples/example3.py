import morpholib as morpho
morpho.importAll()

from morpholib.tools.basics import *
from morpholib.video import *

import math, cmath

# morpho.transitions.default = morpho.transitions.quadease

def spiralPoint():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Place a default grid in the background just to
    # make the motion clearer
    gridBG = mainlayer.Actor(morpho.grid.basicgrid(axes=True))

    # Setup point at the coordinates (3,2) and
    # set the tween method to be the Point class's
    # spiral tween method.
    mypoint = mainlayer.Actor(morpho.grid.Point(3+2j).set(
        tweenMethod=morpho.grid.Point.tweenSpiral
        ))

    # Change the position to (-1,0) over the course of 1 second (30 frames).
    mypoint.newendkey(30).pos = -1

    mation.play()

def spiralPath():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Setup a standard grid, but with the spiral
    # tween method for a path.
    mygrid = mainlayer.Actor(morpho.grid.mathgrid(
        tweenMethod=morpho.grid.Path.tweenSpiral
        ))

    # Have it tween into a morphed version of itself
    fgrid = mygrid.last().fimage(lambda z: z**2/10)
    mygrid.newendkey(60, fgrid)

    mation.play()

def pivotPoint():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Place a default grid in the background just to
    # make the motion clearer
    gridBG = mainlayer.Actor(morpho.grid.basicgrid(axes=True))

    # Setup point at the coordinates (3,2) and
    # set the tween method to be the Point class's
    # pivot tween method with an angle of pi radians.
    mypoint = mainlayer.Actor(morpho.grid.Point(3+2j).set(
        tweenMethod=morpho.grid.Point.tweenPivot(pi)
        ))

    # Change the position to (-1,0) over the course of 1 second (30 frames).
    mypoint.newendkey(30).pos = -1

    mation.play()

def spiralThenLinear():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Place a default grid in the background just to
    # make the motion clearer
    gridBG = mainlayer.Actor(morpho.grid.basicgrid(axes=True))

    # Setup point at the coordinates (3,2) and
    # set the tween method to be the Point class's spiral tween method.
    # Also set the transition to be quadease.
    mypoint = mainlayer.Actor(morpho.grid.Point(3+2j).set(
        tweenMethod=morpho.grid.Point.tweenSpiral,
        transition=morpho.transitions.quadease
        ))

    # Change the position to (-1,0) over the course of 1 second (30 frames)
    # and also reassign the tween method at this point to be linear tween.
    # Also set the transition from this point to be uniform
    mypoint.newendkey(30).set(
        pos=-1,
        tweenMethod=mypoint.figureType.tweenLinear,
        transition=morpho.transitions.uniform
        )

    # Create a new keyfigure returning the point to its
    # starting location. The tween method is governed by
    # the previous keyfigure's tween method: tweenLinear
    mypoint.newendkey(30, mypoint.first().copy())

    mation.play()

def invisibility():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Initialize point at the origin, but make it big.
    mypoint = mainlayer.Actor(morpho.grid.Point(0).set(size=50))

    # Move point off the left side of the screen
    mypoint.newendkey(30).set(
        pos=-6,
        visible=False
        )

    # While invisible, move to being off the
    # right side of the screen
    mypoint.newendkey(15).set(
        pos=6,
        visible=True
        )

    # After being made visible again, move
    # back to the origin.
    mypoint.newendkey(30).pos = 0

    mation.play()

def locatorTest():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Setup a default grid
    mygrid = mainlayer.Actor(morpho.grid.mathgrid())

    # Morph it into a distorted version
    mygrid.newendkey(30, mygrid.first().fimage(lambda z: z**2/10))

    # Set the first layer (the layer #0) as the locator layer
    mation.locatorLayer = 0
    # Set the initial frame of the animation to be its final frame
    mation.start = mation.lastID()
    mation.play()

def locatorAlt():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Setup a default grid
    mygrid = mainlayer.Actor(morpho.grid.mathgrid())

    # Morph it into a distorted version
    mygrid.newendkey(30, mygrid.first().fimage(lambda z: z**2/10))

    # Set `mainlayer` as the locator layer
    mation.locatorLayer = mainlayer
    # Set the initial frame of the animation to be its final frame
    mation.start = mation.lastID()
    mation.play()


# spiralPoint()
# spiralPath()
# pivotPoint()
# spiralThenLinear()
# invisibility()
# locatorTest()
# locatorAlt()
