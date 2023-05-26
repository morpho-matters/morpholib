import morpholib as morpho
morpho.importAll()

from morpholib.tools.basics import *
from morpholib.video import *

import math, cmath

# morpho.transitions.default = morpho.transitions.quadease

def pointEx():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    mypoint = mainlayer.Actor(morpho.grid.Point().set(
        pos=3+4*1j,     # Position as a complex number
        size=50,        # Diameter in pixels
        fill=[0,1,0],   # Color in RGB, where 0 is min and 1 is max
        color=[1,1,1],  # Border color
        strokeWeight=5  # Border thickness in pixels
        ))

    mation.play()

def pathEx():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    mypath = mainlayer.Actor(morpho.grid.Path([3, 3*1j, -3, -3*1j]).close().set(
        color=[0,0,1],  # Make the path blue
        width=5         # Make the path 5 pixels thick
        ))

    mation.play()

def lineEx():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Make a linear path connecting -2-3j to 1+4j
    # containing 100 segments
    myline = mainlayer.Actor(morpho.grid.line(-2-3*1j, 1+4*1j, steps=100))

    mation.play()

def ellipseEx():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Make an elliptical path centered at 1+1j with
    # x-radius 3 and y-radius 1
    myoval = mainlayer.Actor(morpho.grid.ellipse(1+1j, 3, 1).edge())

    mation.play()

def gridEx():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    mygrid = mainlayer.Actor(morpho.grid.mathgrid(
        view=[-5,5, -4,4],  # read this as [xmin, xmax, ymin, ymax]
        dx=1, dy=1          # Distance between major x and y tick marks
        ))

    mation.play()

def polyEx():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    mypoly = mainlayer.Actor(morpho.grid.Polygon([3, 3*1j, -3, -3*1j]).set(
        width=5,        # Border is 5 pixels thick
        color=[1,1,0],  # Border color is yellow
        fill=[1,0,0]    # Fill color is red
        ))

    mation.play()

def pointActor():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    mypoint = mainlayer.Actor(morpho.grid.Point().set(
        pos=3+4*1j,     # Position as a complex number
        size=50,        # Diameter in pixels
        fill=[0,1,0],   # Fill color in RGB, where 0 is min and 1 is max
        color=[1,1,1],  # Border color
        alpha=0.5,      # Value from 0 to 1 where 0 = invisible, 1 = opaque
        strokeWeight=5  # Border thickness in pixels
        ))
    mypoint.newendkey(30).set(pos=0)  # Move to origin
    mypoint.newendkey(30).set(size=20, fill=[1,0,0], alpha=1)  # Get smaller, change color, make opaque
    mypoint.newendkey(30)  # Do nothing, just wait a second
    mypoint.newendkey(20).set(pos=-3)  # Move to (-3,0) in 20 frames (2/3 sec)
    mypoint.newendkey(30, morpho.grid.Point())  # Turn into a default Point figure

    mation.play()


def intermediateKeys():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    mypoint = mainlayer.Actor(morpho.grid.Point().set(
        pos=0,  # 0 is default, but it's nice to be explicit
        size=20,
        fill=[1,0,0]
        ))
    mypoint.newendkey(60).set(pos=3+4*1j, size=50, fill=[0,1,0])
    mypoint.newendkey(-30).set(pos=3)

    mation.play()

def pathMorph():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    grid = mainlayer.Actor(morpho.grid.mathgrid(
        view=[-5,5, -5,5],  # read this as [xmin, xmax, ymin, ymax]
        dx=1, dy=1  # Distance between major x and y tick marks
        ))

    fgrid = grid.last().fimage(lambda z: z**2/10)
    grid.newendkey(60, fgrid)

    mation.play()

def layerEx():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Create Point actor
    mypoint = mainlayer.Actor(morpho.grid.Point().set(
        pos=3+4*1j,     # Position as a complex number
        size=50,        # Diameter in pixels
        fill=[0,1,0],   # Fill color in RGB, where 0 is min and 1 is max
        color=[1,1,1],  # Border color
        strokeWeight=5, # Border thickness in pixels
        transition=morpho.transitions.quadease,  # Quadease transition
        zdepth=-10      # Initial zdepth is now -10
        ))

    # Create grid actor
    grid = mainlayer.Actor(morpho.grid.mathgrid(
        view=[-5,5, -5,5],  # read this as [xmin, xmax, ymin, ymax]
        dx=1, dy=1  # Distance between major x and y tick marks
        ))

    # Define mypoint's keyfigures
    mypoint.newendkey(60).set(
        pos=0,          # Move the point to the origin
        size=25,        # Cut the size in half
        fill=[1,0,0],   # Change fill color to red
        zdepth=10       # Second keyfigure zdepth is now +10
        )
    mypoint.newendkey(60).set(
        pos=-3+3*1j,    # Move point to (-3+3i)
        size=75,        # Inflate size of point
        alpha=0         # Fade point to invisibility
        )
    mypoint.newendkey(-30).set(pos=-3)  # New key 30 frames before last key
    mypoint.newendkey(60, mypoint.first().copy())

    # Define grid's keyfigures
    fgrid = grid.last().fimage(lambda z: z**2/10)
    grid.newendkey(60, fgrid)

    mation.play()


# pointEx()
# pathEx()
# lineEx()
# ellipseEx()
# gridEx()
# polyEx()
# pointActor()
# intermediateKeys()
# pathMorph()
# layerEx()
