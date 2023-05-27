
import morpholib as morpho
import morpholib.anim
from morpholib.tools.basics import *
import morpholib.transitions

import pyglet as pg
pyglet = pg
from cmath import exp

import numpy as np

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
# Any additional keyword arguments are set as attributes of the
# returned path.
def flowStreamer(p0, vfield, tstart=0, tend=1, *,
    rtol=1e-5, atol=1e-6, steps=50,
    _3dmode=False, **kwargs):

    try:
        from scipy.integrate import solve_ivp
    except ModuleNotFoundError:
        raise ModuleNotFoundError("scipy library required to use this function. Install via `pip3 install scipy`.")

    dtype = float if _3dmode else complex
    sol = solve_ivp(
        vfield, [tstart, tend], np.array(p0, dtype=dtype).reshape(-1),
        t_eval=np.linspace(tstart, tend, steps+1),
        rtol=rtol, atol=atol
        )

    PathType = morpho.grid.SpacePath if _3dmode else morpho.grid.Path
    path = PathType(sol.y.T.squeeze().tolist())
    path.set(**kwargs)
    return path

def flowStreamer3d(*args, **kwargs):
    return flowStreamer(*args, _3dmode=True, **kwargs)


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
# stagger = Cycle offset between consecutive streamers.
#           For example, stagger=0.25 means each consecutive streamer
#           will be a quarter cycle offset from the previous one.
#           Default: 0 (no stagger)
# offset = Cycle position the first streamer should start in.
#          Essentially, this advances all the initial streamers
#          by the given amount. Default: 0 (no offset)
#          Can also be a list of N values which will generate N-many
#          copies of each streamer offset by each amount in the list.
# sectorSize = Portion of the cycle that will be visible at any given
#              moment. Default: 0.5 (display half a cycle)
# transition = Transition function to use for each streamer.
#              Default: Uniform transition
# Any additional inputs will be passed to flowStreamer() for the
# construction of each individual streamer.
class FlowField(morpho.Layer):
    def __init__(self, *args, **kwargs):
        super().__init__()

        self.actors = self.generateStreamers(*args, **kwargs)

    @property
    def streamers(self):
        return self.actors

    @streamers.setter
    def streamers(self, value):
        self.actors = value

    @staticmethod
    def generateStreamers(points, *args, stagger=0, offset=0, sectorSize=0.5,
        transition=morpho.transitions.uniform, _3dmode=False, **kwargs):

        if isinstance(offset, np.ndarray):
            offset = offset.tolist()
        elif not isinstance(offset, (list, tuple)):
            offset = [offset]

        makeStreamer = flowStreamer3d if _3dmode else flowStreamer
        streamers = []

        for shift in offset:
            for n,z in enumerate(points):
                streamer = makeStreamer(z, *args, **kwargs)
                streamer.start = n*stagger + shift
                streamer.end = streamer.start + sectorSize
                streamer.transition = transition

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

    def lastID(self):
        return max(streamer.lastID() for streamer in self.streamers)

    def firstID(self):
        return min(streamer.firstID() for streamer in self.streamers)

    def keyID(self, n):
        indices = set()
        for streamer in self.streamers:
            indices.update(streamer.keyIDs)
        indices = sorted(indices)
        return indices[n]

    # Calls newkey() on all component streamers and returns
    # a selection of all the newly created keyfigures so
    # attributes can be modified en masse by calling .set()
    #   myflow.newkey(time).set(width=5, color=(1,0,0), ...)
    def newkey(self, f):
        frame = _FlowFrame()
        for streamer in self.streamers:
            keyfig = streamer.newkey(f)
            frame.figures.append(keyfig)
        return frame

    # Calls newendkey() on all component streamers and returns
    # a selection of all the newly created keyfigures so
    # attributes can be modified en masse by calling .set()
    #   myflow.newendkey(time).set(width=5, color=(1,0,0), ...)
    def newendkey(self, df=None, *, glob=False):
        frame = _FlowFrame()
        if df is None:
            df = 0
            glob = True
        if glob:
            f = self.glastID() + df
        else:
            f = max(streamer.lastID() for streamer in self.streamers) + df

        for streamer in self.streamers:
            keyfig = streamer.newkey(f)
            frame.figures.append(keyfig)
        return frame

    ### GADGET ACTIONS ###

    # Retroactively makes the FlowField fade in from invisibility.
    # The main difference with regular fadeIn() for Actors is
    # this method should only be used RETROACTIVELY after the
    # FlowField has some keyframes.
    def prefadeIn(self, duration=30, *, jump=0):
        initial = self.newkey(self.keyID(-2))
        self.newkey(self.keyID(-2)+duration).all.set(visible=True)

        initial.all.set(alpha=0, visible=True)
        if jump != 0:
            for keyfig in self.first().figures:
                # Avoiding using `-=` so it works with mutable np.arrays
                keyfig.origin = keyfig.origin - jump

    # Retroactively makes the FlowField fade out to invisibility.
    # The main difference with regular fadeOut() for Actors is
    # this method should only be used RETROACTIVELY after the
    # FlowField has some keyframes.
    def prefadeOut(self, duration=30, *, jump=0):
        self.newkey(self.lastID()-duration)

        self.last().all.set(alpha=0, visible=False)
        if jump != 0:
            for keyfig in self.last().figures:
                # Avoiding using `+=` so it works with mutable np.arrays
                keyfig.origin = keyfig.origin + jump

# 3D version of FlowField class. See FlowField for more info.
class FlowField3D(FlowField):
    @staticmethod
    def generateStreamers(*args, **kwargs):
        return FlowField.generateStreamers(*args, _3dmode=True, **kwargs)

FlowField3d = FlowField3D
