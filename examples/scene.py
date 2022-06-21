import morpholib as morpho
morpho.importAll()
mo = morpho  # Allows the shorthand "mo" to be optionally used instead of "morpho"

# Import particular transition functions into the main namespace
from morpholib.transitions import uniform, quadease, drop, toss, sineease, step
# Import useful functions and constants into the main namespace
from morpholib.tools.basics import *

# Import various other libraries
import math, cmath, random
import numpy as np

# Set default transition to quadease
morpho.transition.default = quadease
# Set default font to be the LaTeX font
# Note you may have to install this font separately onto your system
morpho.text.defaultFont = "CMU serif"

# Basic unit vectors for 3D animations
ihat = mo.matrix.array([1,0,0])
jhat = mo.matrix.array([0,1,0])
khat = mo.matrix.array([0,0,1])

# Particular colors are named here.
# Feel free to customize to your heart's content.
violet = tuple(mo.color.parseHexColor("800080"))
orange = tuple(mo.color.parseHexColor("ff6300"))
lighttan = tuple(mo.color.parseHexColor("f4f1c1"))

# Give a name unique to this scene file.
# It's used to allow this scene file to export a video file
# in parallel with other scene files.
morpho.anim.exportSignature = "example-scene"



def main():
    # Define layers here
    mainlayer = morpho.Layer(view=mo.video.view169())
    mation = morpho.Animation([mainlayer])
    # Display settings
    mation.windowShape = (1920, 1080)
    mation.fullscreen = True
    mation.background = lighttan

    mainlayer.camera.first().zoomIn(2)

    # Define background grid
    grid = mo.grid.mathgrid(
        view=[-9,9, -5,5],
        hsteps=1, vsteps=1,
        hcolor=[0,0.6,0], vcolor=[0,0,1],
        axesColor=[0,0,0],
        xaxisWidth=7, yaxisWidth=7
        )
    grid = mo.Actor(grid)
    mainlayer.merge(grid)

    # Define curve to initially be a line
    curve = mo.graph.realgraph(lambda x: 2*x + 1, -3, 3)
    curve.set(width=5, color=[1,0,0], end=0)
    curve = mo.Actor(curve)
    mainlayer.merge(curve)
    curve.newendkey(30).end = 1  # Draw curve over 1 second (30 frames)

    time = mation.lastID()
    # Create "Linear" label.
    # MultiText is used so that we can morph the text later
    label = mo.text.MultiText("Linear",
        pos=1+0.5j, size=64, color=[1,0,0], alpha=0
        )
    label = mo.Actor(label)
    mainlayer.merge(label, atFrame=time)
    label.newendkey(20).alpha = 1

    mation.endDelayUntil(3*30)
    print("Morph to quadratic:", mation.seconds())

    time = mation.lastID()
    curve.newkey(time)
    quadratic = mo.graph.realgraph(lambda x: x**2, -3, 3)
    quadratic.set(width=5, color=violet)
    curve.newendkey(30, quadratic)

    # time = mation.lastID()  # Label morphs after curve finishes morphing
    label.newkey(time)  # Don't start morphing until this chunk starts
    label.newendkey(30).set(text="Quadratic", pos=2.5+0.5j, color=violet)

    mation.endDelayUntil(6.25*30)
    print("Fade everything out:", mation.seconds())

    time = mation.lastID()

    # Fade curve
    curve.newkey(time)
    curve.newendkey(30).alpha = 0

    # Simultaneously fade the label
    label.newkey(time)
    label.newendkey(30).alpha = 0




    print("Animation length:", mation.seconds())
    mation.endDelay(10*30)

    mation.finitizeDelays(30)

    # mation.start = mation.lastID()
    mation.locatorLayer = mainlayer
    mation.clickRound = 2
    mation.clickCopy = True
    # mation.newFrameRate(10)
    mation.play()

    # mation.newFrameRate(60)
    # mation.export("./animation.mp4", scale=1)

def streamlined():
    # Define layers here
    mainlayer = morpho.Layer(view=mo.video.view169())
    mation = morpho.Animation([mainlayer])
    # Display settings
    mation.windowShape = (1920, 1080)
    mation.fullscreen = True
    mation.background = lighttan

    mainlayer.camera.first().zoomIn(2)

    # Define background grid
    grid = mo.grid.mathgrid(
        view=[-9,9, -5,5],
        hsteps=1, vsteps=1,
        hcolor=[0,0.6,0], vcolor=[0,0,1],
        axesColor=[0,0,0],
        xaxisWidth=7, yaxisWidth=7
        )
    grid = mo.Actor(grid)
    mainlayer.merge(grid)

    # Define curve to initially be a line
    curve = mo.graph.realgraph(lambda x: 2*x + 1, -3, 3)
    curve.set(width=5, color=[1,0,0])  # No longer need to say alpha=0
    curve = mo.Actor(curve)
    mainlayer.merge(curve)
    curve.growIn(duration=30)

    # Create "Linear" label.
    # MultiText is used so that we can morph the text later
    label = mo.text.MultiText("Linear",
        pos=1+0.5j, size=64, color=[1,0,0]  # No longer need to say alpha=0
        )
    label = mo.Actor(label)
    mainlayer.append(label)
    label.fadeIn(duration=20, jump=1j)

    mation.endDelayUntil(3*30)
    print("Morph to quadratic:", mation.seconds())

    time = mation.lastID()
    curve.newkey(time)
    quadratic = mo.graph.realgraph(lambda x: x**2, -3, 3)
    quadratic.set(width=5, color=violet)
    curve.newendkey(30, quadratic)

    # time = mation.lastID()  # Label morphs after curve finishes morphing
    label.newkey(time)  # Don't start morphing until this chunk starts
    label.newendkey(30).set(text="Quadratic", pos=2.5+0.5j, color=violet)

    mation.endDelayUntil(6.25*30)
    print("Fade everything out:", mation.seconds())

    time = mation.lastID()
    # Fade curve and label
    morpho.action.fadeOut([curve, label],
        atFrame=time, duration=30, stagger=15, jump=2j)






    print("Animation length:", mation.seconds())
    mation.endDelay(10*30)

    mation.finitizeDelays(30)

    # mation.start = mation.lastID()
    mation.locatorLayer = mainlayer
    mation.clickRound = 2
    mation.clickCopy = True
    # mation.newFrameRate(10)
    mation.play()

    # mation.newFrameRate(60)
    # mation.export("./animation.mp4", scale=1)

main()
# streamlined()
