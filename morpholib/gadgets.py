import morpholib as morpho
import morpholib.anim
import morpholib.grid
from morpholib.tools.basics import *

import math, cmath

# DEPRECATED! Use crossout() or crossoutPath() instead.
# Returns a layer which when animated makes a colored X cross
# out the box you specify.
# box = a 4-item list/tuple in the same fashion as the view box
# time = duration for the animation
# width = thickness of the lines
# color = color of the lines
def crossout_old(box, time=30, width=3, color=(1,0,0), view=None):
    x_min, x_max, y_min, y_max = box
    pathSE = morpho.grid.Path([x_min + y_max*1j]*2)
    pathSE.width = width
    pathSE.color = list(color)
    pathSE.transition = morpho.transitions.slow_fast_slow
    pathSW = morpho.grid.Path([x_max + y_max*1j]*2)
    pathSW.width = width
    pathSW.color = list(color)
    pathSW.transition = morpho.transitions.slow_fast_slow

    pathSE = morpho.Actor(pathSE)
    pathSW = morpho.Actor(pathSW)

    pathSE.newkey(time//2).seq[1] = x_max + y_min*1j
    pathSE.key(-1).delay = oo


    pathSW.movekey(0, time//2)
    pathSW.newkey(time).seq[1] = x_min + y_min*1j
    pathSW.key(-1).delay = oo

    if view is None: view = tuple(box)
    layer = morpho.anim.Layer([pathSE, pathSW], view=view)
    return layer

# Returns a path actor which when animated makes a colored X cross
# out the box you specify.
# box = a 4-item list/tuple [xmin,xmax,ymin,ymax]
# time/duration = duration for the animation
# width = thickness of the lines
# color = color of the lines
# transition = Transition function assigned to path.
#              Default: morpho.transition.default
# origin = origin point of path (complex number). Default: 0
# relative = Boolean indicating whether the box values are relative to the origin
#            point, or are in absolute physical coordinates of the layer.
#            Default: False (absolute coordinates)
def crossoutPath(box, time=30, width=3, color=(1,0,0),
    transition=None, origin=0, relative=False, *, duration=None):

    # "duration" is a dominant alias for the "time" parameter
    if duration is not None:
        time = duration

    x_min, x_max, y_min, y_max = box

    path = morpho.grid.Path([x_min+y_max*1j, x_max+y_min*1j, x_max+y_max*1j, x_min+y_min*1j])
    path.deadends.add(1)
    path.width = width
    path.color = list(color)
    path.end = 0
    path.transition = transition if transition is not None else morpho.transition.default
    path.origin = mean(box[:2]) + 1j*mean(box[2:]) if relative else 0
    path.origin += origin

    path = morpho.Actor(path)
    path.newkey(time).end = 1

    return path

crossout = crossoutPath

# Returns a path actor that circles a given box region.
#
# ARGUMENTS
# box = 4-item list/tuple [xmin,xmax,ymin,ymax]
# time/duration = Duration of animation (in frames). Default: 30
# width = Border thickness (in pixels). Default: 3
# color = Border color (RGB list). Default: [1,0,0] (red)
# phase = Starting angle in radians measured CCW from east. Default: pi/2
# CCW = Boolean specifying draw direction being counter-clockwise or not.
#       Default: True
# steps = Number of line segments in path. Default: 75
# transition = Transition function assigned to path.
#              Default: morpho.transition.default
# origin = origin point of path (complex number). Default: 0
# relative = Boolean indicating whether the box values are relative to the origin
#            point, or are in absolute physical coordinates of the layer.
#            Default: False (absolute coordinates)
def encircle(box, time=30, width=3, color=(1,0,0), phase=tau/4,
    CCW=True, steps=75, transition=None, origin=0, relative=False,
    *, duration=None):

    # "duration" is a dominant alias for the "time" parameter
    if duration is not None:
        time = duration

    orbit = 2*int(CCW) - 1
    z0 = (box[0]+box[1])/2 + (box[2]+box[3])/2*1j if not relative else 0
    a = (box[1] - box[0])/2
    b = (box[3] - box[2])/2
    seq = [z0 + a*math.cos(orbit*n/steps*tau + phase) + 1j*b*math.sin(orbit*n/steps*tau + phase) for n in range(steps)]
    seq.append(seq[0])

    path = morpho.grid.Path(seq)
    path.width = width
    path.color = list(color)
    path.end = 0
    path.origin = mean(box[:2]) + 1j*mean(box[2:]) if relative else 0
    path.origin += origin
    if transition is None:
        path.transition = morpho.transition.default
    else:
        path.transition = transition

    path = morpho.Actor(path)
    path.newkey(time)
    path.last().end = 1

    return path

# Draws an enboxing animation. Good for highlighting important things on screen.
#
# ARGUMENTS
# box = 4-item list/tuple [xmin,xmax,ymin,ymax]
# time/duration = Duration of animation (in frames). Default: 30
# width = Border thickness (in pixels). Default: 3
# color = Border color (RGB list). Default: [1,0,0] (red)
# corner = Which corner should the animation start at?
#          Values are given as diagonal compass directions:
#          "NW", "SW", "SE", "NE". Default: "NW"
# CCW = Boolean specifying draw direction being counter-clockwise or not.
#       Default: True
# transition = Transition function assigned to path.
#              Default: morpho.transition.default
# origin = origin point of path (complex number). Default: 0
def enboxPath(box, time=30, width=3, color=(1,0,0), corner="NW", CCW=True,
    transition=None, origin=0, *, duration=None):

    # "duration" is a dominant alias for the "time" parameter
    if duration is not None:
        time = duration

    corner = corner.upper()
    dirs = ["NW", "SW", "SE", "NE"]
    if corner not in dirs:
        raise ValueError('corner must be "NW", "SW", "SE", or "NE".')

    left = box[0]
    right = box[1]
    bottom = box[2]
    top = box[3]

    corners = [left+1j*top, left+1j*bottom, right+1j*bottom, right+1j*top]

    # Reverse order if done clockwise
    if not CCW:
        corners = corners[::-1]
        dirs = dirs[::-1]

    # Find the index of the starting corner
    i = dirs.index(corner)

    # Order the corners according to the starting corner and direction
    corners = corners[i:] + corners[:i]


    path = morpho.grid.Path(corners)
    path.close()
    path.width = width
    path.color = list(color)
    constTrans = path.constantSpeedTransition()
    path.origin = origin
    if transition is None:
        transition = morpho.transition.default
    # if transition is None:
    #     path.transition = lambda t: constTrans(morpho.transition.default(t))
    path.transition = lambda t: constTrans(transition(t))
    path.end = 0

    path = morpho.Actor(path)
    path.newkey(time)
    path.last().end = 1
    path.last().transition = transition

    return path

enbox = enboxPath  # Synonym for emboxPath()

# Scales all the nodes of a path by the given factor about the given
# centerpoint. If the center is unspecified, defaults to the center
# of mass of all the path's nodes.
def expandPath(path, factor, center=None):
    if center is None:
        center = sum(path.seq)/len(path.seq)

    return path.fimage(lambda s: factor*(s-center)+center)

# DEPRECATED! Use enbox() or enboxPath() instead.
def enbox_old(box, time=30, width=3, color=(1,0,0), corner="NW", CCW=True,
    view=None, transition=morpho.transitions.uniform):

    raise NotImplementedError

    corner = corner.upper()
    dirs = ["NW", "SW", "SE", "NE"]
    if corner not in dirs:
        raise ValueError('corner must be "NW", "SW", "SE", or "NE".')

    if view is None:
        view = tuple(box)

    left = box[0]
    right = box[1]
    bottom = box[2]
    top = box[3]

    corners = [left+1j*top, left+1j*bottom, right+1j*bottom, right+1j*top]

    # Reverse order if done clockwise
    if not CCW:
        corners = corners[::-1]
        dirs = dirs[::-1]

    # Find the index of the starting corner
    i = dirs.index(corner)

    # Order the corners according to the starting corner and direction
    corners = corners[i:] + corners[:i]

    # Get drawing!
    layer = morpho.Layer(view=view)
    LEN = 2*(box[1]-box[0] + box[3]-box[2])
    len_sofar = 0
    for i in range(4):
        z0 = corners[i]
        z1 = corners[(i+1) % 4]

        t0 = round((len_sofar)/LEN * time)
        len_sofar += abs(z1-z0)
        t1 = round((len_sofar)/LEN * time)

        path0 = morpho.grid.Path([z0, z0])
        path0.width = width
        path0.color = list(color)
        path0.transition = transition

        path = morpho.Actor(morpho.grid.Path)
        path.newkey(t0, path0)
        path.newkey(t1)
        path.key(-1).seq = [z0, z1]
        path.key(-1).delay = oo

        layer.actors.append(path)

    return layer

