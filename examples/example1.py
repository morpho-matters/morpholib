import morpholib as morpho
morpho.importAll()

from morpholib.tools.basics import *
from morpholib.video import *

import math, cmath

# morpho.transitions.default = morpho.transitions.quadease

def pointEx():
    mypoint = morpho.grid.Point()
    mypoint.size = 50         # Diameter given in units of pixels
    mypoint.fill = [0,1,0]    # Color in RGB, where 0 is min and 1 is max
    mypoint.color = [1,1,1]
    mypoint.strokeWeight = 5  # Thickness in pixels
    mypoint.pos = 4 + 3*1j
    mypoint.alpha = 0.5       # Takes values in [0,1] where 1 = opaque, 0 = invisible

    movie = morpho.Animation(mypoint)
    movie.play()

def pathEx():
    mypath = morpho.grid.Path([3, 3*1j, -3, -3*1j])
    mypath.close()
    mypath.color = [0,0,1]  # Make the path blue
    mypath.width = 5        # Make the path 5 pixels thick

    movie = morpho.Animation(mypath)
    movie.play()

def lineEx():
    # Make a linear path connecting -2-3i to 1+4i
    myline = morpho.grid.line(-2-3*1j, 1+4*1j)

    movie = morpho.Animation(myline)
    movie.play()

def ellipseEx():
    # Make an elliptical path centered at 1+1j with
    # semi-width 3 and semi-height 1
    myoval = morpho.grid.ellipse(1+1j, 3, 1)

    movie = morpho.Animation(myoval)
    movie.play()

def gridEx():
    mygrid = morpho.grid.mathgrid(
        view=[-5,5, -4,4],  # read this as [xmin, xmax, ymin, ymax]
        dx=1, dy=1  # Distance between major x and y tick marks
        )

    movie = morpho.Animation(mygrid)
    movie.play()

def polyEx():
    mypoly = morpho.grid.Polygon([3, 3*1j, -3, -3*1j])
    mypoly.color = [1,1,1]  # Make the border white
    mypoly.width = 5        # Thicken the border
    mypoly.fill = [1,0,0]   # Fill the interior with red

    movie = morpho.Animation(mypoly)
    movie.play()

def pointActor():
    mypoint = morpho.grid.Point()
    mypoint.size = 50         # Diameter given in units of pixels
    mypoint.fill = [0,1,0]    # Color in RGB, where 0 is min and 1 is max
    mypoint.color = [1,1,1]
    mypoint.strokeWeight = 5  # Thickness in pixels
    mypoint.pos = 4 + 3*1j
    mypoint.transition = morpho.transitions.quadease  # New transition

    mypoint = morpho.Actor(mypoint)
    mypoint.newkey(60)  # Create a copy of the point at frame 60
    mypoint.time(60).fill = [1,0,0]  # Change fill color to red
    mypoint.time(60).size = 25  # Cut the size in half
    mypoint.time(60).pos = 0  # Move the point to the origin

    mypoint.newkey(120)
    mypoint.time(120).size = 75        # Inflate size of point
    mypoint.time(120).pos = -3 + 3*1j  # Move point to (-3+3i)
    mypoint.time(120).alpha = 0        # Fade point to invisibility

    mypoint.newkey(90)
    mypoint.time(90).pos = -3  # Point takes a detour to -3.

    mypoint.newkey(180, mypoint.time(0).copy())

    movie = morpho.Animation(mypoint)
    movie.play()


def relativePoint():
    mypoint = morpho.grid.Point()
    mypoint.size = 50         # Diameter given in units of pixels
    mypoint.fill = [0,1,0]    # Color in RGB, where 0 is min and 1 is max
    mypoint.color = [1,1,1]
    mypoint.strokeWeight = 5  # Thickness in pixels
    mypoint.pos = 4 + 3*1j
    mypoint.transition = morpho.transitions.quadease  # New transition

    mypoint = morpho.Actor(mypoint)
    mypoint.newendkey(60)  # Create a copy of the point at frame 60
    mypoint.last().fill = [1,0,0]  # Change fill color to red
    mypoint.last().size = 25  # Cut the size in half
    mypoint.last().pos = 0  # Move the point to the origin

    mypoint.newendkey(60)
    mypoint.last().size = 75        # Inflate size of point
    mypoint.last().pos = -3 + 3*1j  # Move point to (-3+3i)
    mypoint.last().alpha = 0        # Fade point to invisibility

    mypoint.newendkey(-30)  # New key 30 frames before last key
    mypoint.key(-2).pos = -3  # key(-2) means second-to-last key

    mypoint.newendkey(60, mypoint.first().copy())

    movie = morpho.Animation(mypoint)
    movie.play()

def pathMorph():
    grid = morpho.grid.mathgrid(
        view=[-5,5, -5,5],  # read this as [xmin, xmax, ymin, ymax]
        dx=1, dy=1  # Distance between major x and y tick marks
        )
    fgrid = grid.fimage(lambda z: z**2/10)

    grid = morpho.Actor(grid)
    grid.newendkey(60, fgrid)

    movie = morpho.Animation(grid)
    movie.play()

def layerEx():
    ### DEFINING POINT ACTOR ###

    mypoint = morpho.grid.Point()
    mypoint.size = 50         # Diameter given in units of pixels
    mypoint.fill = [0,1,0]    # Color in RGB, where 0 is min and 1 is max
    mypoint.color = [1,1,1]
    mypoint.strokeWeight = 5  # Thickness in pixels
    mypoint.pos = 4 + 3*1j
    mypoint.transition = morpho.transitions.quadease  # New transition

    mypoint.zdepth = -10  # Initial zdepth is now -10

    mypoint = morpho.Actor(mypoint)
    mypoint.newendkey(60)  # Create a copy of the point at frame 60
    mypoint.last().fill = [1,0,0]  # Change fill color to red
    mypoint.last().size = 25  # Cut the size in half
    mypoint.last().pos = 0  # Move the point to the origin
    mypoint.last().zdepth = 10  # Second key has zdepth = +10

    mypoint.newendkey(60)
    mypoint.last().size = 75        # Inflate size of point
    mypoint.last().pos = -3 + 3*1j  # Move point to (-3+3i)
    mypoint.last().alpha = 0        # Fade point to invisibility

    mypoint.newendkey(-30)  # New key 30 frames before last key
    mypoint.key(-2).pos = -3  # key(-2) means second-to-last key

    mypoint.newendkey(60, mypoint.first().copy())

    ### DEFINING GRID ACTOR ###

    grid = morpho.grid.mathgrid(
        view=[-5,5, -5,5],  # read this as [xmin, xmax, ymin, ymax]
        dx=1, dy=1  # Distance between major x and y tick marks
        )
    fgrid = grid.fimage(lambda z: z**2/10)

    grid = morpho.Actor(grid)
    grid.newendkey(60, fgrid)

    ### PACKAGE INTO A LAYER ###

    # View of the complex plane is now [-10, 10] x [-10i, 10i]
    layer = morpho.Layer([mypoint, grid], view=[-10,10, -10,10])

    # Change the view after layer construction
    layer.camera.time(0).view = [-10,10, -10,10]
    layer.camera.newendkey(120)
    layer.camera.last().view = [-5,5, -5,5]

    # Use zoomIn() and zoomOut()
    layer.camera.newendkey(60)
    layer.camera.last().zoomOut(2)
    layer.camera.newendkey(60)
    layer.camera.last().zoomIn(10)
    layer.camera.newendkey(30)
    layer.camera.last().centerAt(1+2*1j)  # Center the camera at 1+2i
    layer.camera.newendkey(30)
    layer.camera.last().moveBy(-2-3j)  # Move the camera 2 units left, 3 down

    # Package further into animation
    movie = morpho.Animation(layer)
    # movie.frameRate = 60  # Up the framerate to 60 fps
    # movie.newFrameRate(12)
    movie.background = [0.5, 0.5, 0.5]  # Make a gray background
    movie.windowShape = (400, 400)

    movie.play()

# pointEx()
# pathEx()
# lineEx()
# ellipseEx()
# gridEx()
# polyEx()
# pointActor()
# relativePoint()
# pathMorph()
# layerEx()
