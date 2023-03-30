
import morpholib as morpho
import morpholib.anim
from morpholib.tools.basics import *
import morpholib.transitions

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


# Given a point and a velocity field, returns as a Path figure
# the path the point travels "flowing" along the velocity field.
#
# INPUTS
# p0 = Initial point (complex number).
# vfield = Velocity field. A function of the form vfield(t,z)
#          where t is time and z is position (as a complex number)
#          For a static velocity field, the function should not
#          actually depend on t, though the `t` argument must still
#          be present in vfield()'s function signature.
# tstart = Initial time value. Default: 0
# tend = Final time value. Default: 1
#
# KEYWORD ONLY INPUTS
# rtol = Relative error tolerance of IVP solution (solve_ivp).
#        Default: 1e-5
# atol = Absolute error tolerance of IVP solution (solve_ivp).
#        Default: 1e-6
# steps = Number of steps to use in the solution. The outputted
#         Path will have steps+1 nodes.
def flowStreamer(p0, vfield, tstart=0, tend=1, *,
    rtol=1e-5, atol=1e-6, steps=50
    ):
    try:
        from scipy.integrate import solve_ivp
    except ModuleNotFoundError:
        raise ModuleNotFoundError("scipy library required to use this function. Install via `pip3 install scipy`.")

    sol = solve_ivp(
        vfield, [tstart, tend], [complex(p0)],
        t_eval=np.linspace(tstart, tend, steps+1),
        rtol=rtol, atol=atol
        )

    path = morpho.grid.Path(sol.y.squeeze().tolist())
    return path


# Mainly for internal use.
# Variant of Frame class used to make the FlowField gadget
# feel a bit like a regular Actor object.
class _FlowFrame(morpho.Frame):
    # Advances all the streamers by the given cycle amount.
    # For example, myflow.advance(1) advances all the streamers
    # by one cycle.
    def advance(self, dt):
        for fig in self.figures:
            fig.start += dt
            fig.end += dt
        return self

# Generates a Gadget defining a field of flow streamers.
#
# INPUTS
# points = List of initial points for each streamer
#
# KEYWORD ONLY INPUTS
# offset = Sector offset between consecutive streamers.
#          For example, offset=0.25 means each consecutive streamer
#          will be a quarter cycle offset from the previous one.
#          Default: 0 (no offset)
# sectorSize = Portion of the cycle that will be visible at any given
#              moment. Default: 0.5 (display half a cycle)
# style = Dictionary that can be used to specify style attributes
#         of the underlying streamer Paths. Example:
#         dict(width=5, color=(1,0,0), ...)
#         Default: dict() (empty dict)
# Any additional inputs will be passed to flowStreamer() for the
# construction of each individual streamer.
#
# Also note that by default, the transition of the underlying
# streamers will be set to uniform(). This can be overridden by
# passing in a transition value into the style dict.
class FlowField(morpho.Layer):
    def __init__(self, points, *args, offset=0, sectorSize=0.5, style=dict(), **kwargs):
        super().__init__()

        self.actors = self.generateStreamers(points, *args,
            offset=offset, sectorSize=sectorSize, style=style, **kwargs)

    @property
    def streamers(self):
        return self.actors

    @streamers.setter
    def streamers(self, value):
        self.actors = value

    @staticmethod
    def generateStreamers(points, *args, offset=0, sectorSize=0.5, style=None, **kwargs):
        if style is None:
            style = dict()

        streamers = []
        for n,z in enumerate(points):
            streamer = flowStreamer(z, *args, **kwargs)
            streamer.start = n*offset
            streamer.end = streamer.start + sectorSize
            streamer.transition = morpho.transitions.uniform
            streamer.set(**style)

            streamer = morpho.Actor(streamer)
            streamers.append(streamer)
        return streamers

    # Returns a Frame-like object consisting of all the final
    # keyfigures for each streamer.
    # Note that these may not all correspond to exactly the same
    # time coordinate!
    def last(self):
        return _FlowFrame([streamer.last() for streamer in self.streamers])

    # Returns a Frame-like object consisting of all the initial
    # keyfigures for each streamer.
    # Note that these may not all correspond to exactly the same
    # time coordinate!
    def first(self):
        return _FlowFrame([streamer.first() for streamer in self.streamers])

    # Calls newkey() on all component streamers and returns
    # a selection of all the newly created keyfigures so
    # attributes can be modified en masse by calling .set()
    #   myflow.newkey(time).set(width=5, color=(1,0,0), ...)
    def newkey(self, *args, **kwargs):
        frame = _FlowFrame()
        for streamer in self.streamers:
            keyfig = streamer.newkey(*args, **kwargs)
            frame.figures.append(keyfig)
        return frame

    # Calls newendkey() on all component streamers and returns
    # a selection of all the newly created keyfigures so
    # attributes can be modified en masse by calling .set()
    #   myflow.newendkey(time).set(width=5, color=(1,0,0), ...)
    def newendkey(self, *args, **kwargs):
        frame = _FlowFrame()
        for streamer in self.streamers:
            keyfig = streamer.newendkey(*args, **kwargs)
            frame.figures.append(keyfig)
        return frame

