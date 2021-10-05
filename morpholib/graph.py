
import morpholib as morpho
import morpholib.anim
from morpholib.tools.basics import *

import pyglet as pg
pyglet = pg
from cmath import exp

# Returns a Frame figure that defines axes over the given view.
#
# ARGUMENTS
# xwidth = x-axis thickness (in pixels). Default: 5
# ywidth = y-axis thickness (in pixels). Default: 5
# xcolor = x-axis color (RGB list). Default: [0,0,0] (black)
# ycolor = y-axis color (RGB list). Default: [0,0,0] (black)
# xalpha = x-axis opacity. Default: 1 (opaque)
# yalpha = y-axis opacity. Default: 1 (opaque)
def Axes(view, xwidth=5, ywidth=5,
    xcolor=(0,0,0), ycolor=(0,0,0), xalpha=1, yalpha=1):
    xAxis = morpho.grid.Path(view[:2])
    xAxis.static = True
    xAxis.width = xwidth
    xAxis.color = list(xcolor)
    xAxis.alpha = xalpha

    yAxis = morpho.grid.Path([view[2]*1j, view[3]*1j])
    yAxis.static = True
    yAxis.width = ywidth
    yAxis.color = list(ycolor)
    yAxis.alpha = yalpha

    return morpho.anim.Frame([xAxis, yAxis])

# Returns a path which is the graph of a real function.
#
# ARGUMENTS
# f = Real to real python function (e.g. lambda x: x**2)
# a,b = Domain interval [a,b]
# steps = Number of line segments in path. Default: 50
# width = Path thickness (in pixels). Default: 3
# color = Path color (RGB list). Default: [1,1,1] (white)
# alpha = Path opacity. Default: 1 (opaque)
def realgraph(f, a, b, steps=50, width=3, color=(1,1,1), alpha=1):
    line = morpho.grid.line(a, b, steps)
    line.width = width
    line.color = list(color)
    line.alpha = alpha

    transform = lambda s: s.real + f(s.real)*1j
    graph = line.fimage(transform)

    return graph



def revolution():
    pass
