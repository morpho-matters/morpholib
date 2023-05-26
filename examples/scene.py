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

# Particular colors are named here.
# Feel free to customize to your heart's content.
violet = tuple(mo.color.parseHexColor("800080"))
orange = tuple(mo.color.parseHexColor("ff6300"))
lighttan = tuple(mo.color.parseHexColor("f4f1c1"))


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
    grid = mainlayer.Actor(mo.grid.mathgrid(
        view=[-9,9, -5,5],
        steps=1,
        hcolor=[0,0.6,0], vcolor=[0,0,1],
        axesColor=[0,0,0],
        axisWidth=7
        ))

    # Define curve to initially be a line
    curve = mainlayer.Actor(mo.graph.realgraph(lambda x: 2*x + 1, -3, 3))
    curve.first().set(width=5, color=[1,0,0], end=0)
    curve.newendkey(30).end = 1  # Draw curve over 1 second (30 frames)

    # Create "Linear" label.
    # MultiText is used so that we can morph the text later
    label = mainlayer.Actor(mo.text.MultiText("Linear",
        pos=1+0.5j, size=64, color=[1,0,0], alpha=0
        ))
    label.newendkey(20).alpha = 1

    mation.waitUntil(3*30)
    print("Morph line to parabola:", mation.seconds())

    curve.newendkey()
    label.newendkey()

    quadratic = mo.graph.realgraph(lambda x: x**2, -3, 3)
    quadratic.set(width=5, color=violet)
    curve.newendkey(30, quadratic)

    label.newendkey(30).set(text="Quadratic", pos=2.5+0.5j, color=violet)

    mation.waitUntil(6.25*30)
    print("Fade everything out:", mation.seconds())

    # Create initial keyfigures
    curve.newendkey()
    label.newendkey()

    # Fade curve
    curve.newendkey(30).alpha = 0

    # Simultaneously fade the label
    label.newendkey(30).alpha = 0


    print("Animation length:", mation.seconds())
    mation.wait(10*30)

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
    grid = mainlayer.Actor(mo.grid.mathgrid(
        view=[-9,9, -5,5],
        steps=1,
        hcolor=[0,0.6,0], vcolor=[0,0,1],
        axesColor=[0,0,0],
        axisWidth=7
        ))

    # Define curve to initially be a line
    curve = mainlayer.Actor(mo.graph.realgraph(lambda x: 2*x + 1, -3, 3))
    curve.first().set(width=5, color=[1,0,0])  # No longer need to say end=0
    curve.growIn(duration=30)

    # Create "Linear" label.
    # MultiText is used so that we can morph the text later
    label = mainlayer.Actor(mo.text.MultiText("Linear",
        pos=1+0.5j, size=64, color=[1,0,0]  # No longer need to say alpha=0
        ))
    label.fadeIn(duration=20, jump=1j)

    mation.waitUntil(3*30)
    print("Morph line to parabola:", mation.seconds())

    curve.newendkey()
    label.newendkey()

    quadratic = mo.graph.realgraph(lambda x: x**2, -3, 3)
    quadratic.set(width=5, color=violet)
    curve.newendkey(30, quadratic)

    label.newendkey(30).set(text="Quadratic", pos=2.5+0.5j, color=violet)

    mation.waitUntil(6.25*30)
    print("Fade everything out:", mation.seconds())

    # Create initial keyfigures
    curve.newendkey()
    label.newendkey()

    # Fade curve and label in a staggered fashion with jumping
    mo.action.fadeOut([curve, label], duration=30, stagger=15, jump=2j)


    print("Animation length:", mation.seconds())
    mation.wait(10*30)

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
