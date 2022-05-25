'''
Contains some functions useful for making 1080p videos.
'''

import morpholib as morpho
from morpholib.tools.basics import *

import math

ratio = 1920/1080
ratioXY = ratio
ratioYX = 1/ratio
std_view = (-10*ratio, 10*ratio, -10, 10)

def view169():
    return list(std_view)

# Returns a standard video Animation object.
# Meaning an animation with window shape 1920 x 1080, fullscreen.
# A layer list can optionally be supplied. So can background color and opacity.
# Default background and opacity are [1,1,1] (white) and 1 (opaque)
def standardAnimation(layers=None, background=(1,1,1), alpha=1):
    # if layers is None:
    #     layers = morpho.Actor(morpho.Figure)
    if type(layers) not in (tuple, list) and isinstance(layers, morpho.Actor):
        layers = morpho.anim.Layer(layers, view=std_view)
    elif isinstance(layers, morpho.Figure):
        layers = morpho.anim.Layer(morpho.Actor(layers), view=std_view)
    elif layers is None:
        layers = morpho.Layer(view=std_view)

    mation = morpho.Animation(layers)
    mation.windowShape = (1920, 1080)
    mation.fullscreen = True
    mation.resizable = False
    # mation.firstIndex = 0
    mation.background = background[:3]
    mation.alpha = alpha

    # if BGgrid:
    #     nhorz = math.ceil(std_view[3])-math.floor(std_view[2])+1
    #     nvert = math.ceil(std_view[1])-math.floor(std_view[0])+1
    #     hcolor = morpho.tools.color.rgbNormalize(0x23, 0xb5, 0x83)
    #     vcolor = (0,0,1)
    #     grid = morpho.grid.standardGrid(
    #         view=std_view,
    #         nhorz=nhorz, nvert=nvert,
    #         hres=0.05, vres=0.05,
    #         hcolor=hcolor, vcolor=vcolor, alpha=0.5,
    #         hmidColor=morpho.tools.color.alphaOverlay(mation.background[:3], hcolor, 0.5),
    #         vmidColor=morpho.tools.color.alphaOverlay(mation.background[:3], vcolor, 0.5),
    #         BGgrid=False, axesColor=(0,0,0)
    #         )
    #     grid = grid.fimage(lambda s: ((nvert-1)/2)/std_view[1]*s.real + 1j*s.imag)
    #     grid.static = True
    #     grid.delay = oo
    #     grid = morpho.Actor(grid)

    #     layer = morpho.Layer(grid, std_view)
    #     mation.layers.insert(0, layer)
    #     mation.locaterLayer = 0

    return mation


# Essentially same as standardAnimation(), but intended for SpaceLayers.
def standardSpaceAnimation(layers=None, background=(1,1,1), alpha=1):
    # if layers is None:
    #     layers = morpho.Actor(morpho.Figure)
    if type(layers) not in (tuple, list) and isinstance(layers, morpho.Actor):
        layers = morpho.anim.SpaceLayer(layers, view=std_view)
    elif isinstance(layers, morpho.Figure):
        layers = morpho.anim.SpaceLayer(morpho.Actor(layers), view=std_view)
    elif layers is None:
        layers = morpho.SpaceLayer(view=std_view)

    mation = morpho.Animation(layers)
    mation.windowShape = (1920, 1080)
    mation.fullscreen = True
    mation.resizable = False
    # mation.firstIndex = 0
    mation.background = background[:3]
    mation.alpha = alpha

    return mation


# Sets up a standard 3D animation viewing the first octant.
#
# ARGUMENTS
# t_rot = Camera rotation duration (in frames). Default: 300
# initOrient = Initial camera orientation before tilting and spinning.
#              Default: np.eye(3)
# spin = Angular distance the camera will revolve (in rad).
#        Default: -80*pi/180 (80 degs clockwise)
# tilt = Amount camera is tilted down from viewing the xy-plane from above.
#        Default: 70*pi/180 (70 degs)
def setupSpace(
    t_rot=300, initOrient=np.identity(3), spin=-80*tau/360,
    tilt=70*tau/360, *,
    xColor=(0, 0.5, 0), yColor=(0,0,0.7), zColor=(0.7,0,0)
    ):

    xAxis = morpho.grid.SpaceArrow(0, 7.5)
    xAxis.color = xColor
    xAxis.width = 7
    xAxis.headSize = 20

    yAxis = xAxis.copy()
    yAxis.head = 7.5j
    yAxis.color = yColor

    zAxis = xAxis.copy()
    zAxis.head = [0,0,4.5]
    zAxis.color = zColor

    xLabel = morpho.text.SpaceText(
        text="x", font="Times New Roman",
        pos=xAxis.head + [0, -0.25, 0.25],
        size=55, italic=True,
        anchor_x=0, anchor_y=0,
        color=[0,0,0]
        )
    yLabel = morpho.text.SpaceText(
        text="y", font="Times New Roman",
        pos=yAxis.head + [-0.25, 0, 0.25],
        size=55, italic=True,
        anchor_x=0, anchor_y=0,
        color=[0,0,0]
        )
    zLabel = morpho.text.SpaceText(
        text="z", font="Times New Roman",
        pos=zAxis.head + [0,0,0.25],
        size=55, italic=True,
        anchor_x=0, anchor_y=0,
        color=[0,0,0]
        )

    orient = initOrient
    theta0 = -pi/2 - 5*pi/180
    orient = morpho.matrix.rotation([0,0,1], theta0) @ orient
    orient = morpho.matrix.rotation([1,0,0], -tilt) @ orient
    focus = [3.5, 3.5, 2.5]
    # focus = 0
    layer = morpho.SpaceLayer(orient=orient, focus=focus)
    layer.camera.time(0).view = list(std_view)

    # orient = morpho.matrix.rotation([0,0,1], -pi + 5*pi/180)
    orient = initOrient
    orient = morpho.matrix.rotation([0,0,1], theta0+spin) @ orient
    orient = morpho.matrix.rotation([1,0,0], -tilt) @ orient
    layer.camera.first().transition = morpho.transition.uniform
    layer.camera.first().centerAt(3.5 + 3.5j)
    layer.camera.first().zoomIn(2.5)
    layer.camera.newkey(t_rot)
    layer.camera.last().orient = orient

    # Grid
    grid = morpho.grid.wireframe(
        view=[0,7, 0,7],
        dx=1, dy=1,
        hnodes=2, vnodes=2,
        hcolor=xColor[:], vcolor=yColor[:],
        axes=False, optimize=True
        )
    # grid.figures.pop(14)
    # grid.figures.pop(21)
    # grid.figures = morpho.grid.optimizePathList(grid.figures)
    grid = morpho.Frame(grid.figures)
    layer.merge(grid)

    # Merge axes and labels
    layer.merge(xAxis)
    layer.merge(yAxis)
    layer.merge(zAxis)
    layer.merge(xLabel)
    layer.merge(yLabel)
    layer.merge(zLabel)

    # mation = standardAnimation(background=(1,1,1,1))
    # mation.layers[0] = layer

    mation = standardSpaceAnimation(layer)

    return mation


# Sets up an alternative 3D animation object centered around the z-axis.
#
# ARGUMENTS
# t_rot = Camera rotation duration (in frames). Default: 300
# initOrient = Initial camera orientation before tilting and spinning.
#              Default: np.eye(3)
# spin = Angular distance the camera will revolve (in rad).
#        Default: -80*pi/180 (80 degs clockwise)
# tilt = Amount camera is tilted down from viewing the xy-plane from above.
#        Default: 70*pi/180 (70 degs)
def setupSpaceAlt(
    t_rot=300, initOrient=np.identity(3), spin=-80*tau/360,
    tilt=70*tau/360, *,
    xColor=(0, 0.5, 0), yColor=(0,0,0.7), zColor=(0.7,0,0)
    ):

    xAxis = morpho.grid.SpaceArrow(0, 4.5)
    xAxis.color = xColor
    xAxis.width = 7
    xAxis.headSize = 20

    yAxis = xAxis.copy()
    yAxis.head = 4.5j
    yAxis.color = yColor

    # zAxis = xAxis.copy()
    # zAxis.head = [0,0,4.5]
    # zAxis.color = [0.7,0,0]

    xLabel = morpho.text.SpaceText(
        text="x", font="Times New Roman",
        pos=xAxis.head + [0.4,0-0.25,0],
        size=55, italic=True,
        anchor_x=0, anchor_y=0,
        color=[0,0,0]
        )
    yLabel = morpho.text.SpaceText(
        text="y", font="Times New Roman",
        pos=yAxis.head + [-0.25,0.4,0.1],
        size=55, italic=True,
        anchor_x=0, anchor_y=0,
        color=[0,0,0]
        )
    # zLabel = morpho.text.SpaceText(
    #     text="z", pos=zAxis.head + [0,0,0.25],
    #     size=55, italic=True,
    #     anchor_x=0, anchor_y=0,
    #     color=[0,0,0]
    #     )

    orient = initOrient
    theta0 = -pi/2 - 5*pi/180
    orient = morpho.matrix.rotation([0,0,1], theta0) @ orient
    orient = morpho.matrix.rotation([1,0,0], -tilt) @ orient
    focus = [0, 0, 2]
    # focus = 0
    layer = morpho.SpaceLayer(orient=orient, focus=focus)
    layer.camera.time(0).view = list(std_view)

    orient = initOrient
    theta1 = theta0 + spin
    orient = morpho.matrix.rotation([0,0,1], theta1) @ orient
    orient = morpho.matrix.rotation([1,0,0], -tilt) @ orient
    layer.camera.first().transition = morpho.transition.uniform
    # layer.camera.first().centerAt(3.5 + 3.5j)
    layer.camera.first().zoomIn(2.5)
    layer.camera.newkey(t_rot)
    layer.camera.last().orient = orient

    # Grid
    grid = morpho.grid.wireframe(
        view=[-4,4, -4,4],
        dx=1, dy=1,
        hnodes=2, vnodes=2,
        hcolor=xColor[:], vcolor=yColor[:],
        axes=False
        )
    grid = morpho.Frame(grid.figures)
    layer.merge(grid)

    layer.merge(xAxis)
    layer.merge(yAxis)
    # layer.merge(zAxis)
    layer.merge(xLabel)
    layer.merge(yLabel)
    # layer.merge(zLabel)

    # mation = standardAnimation(background=(1,1,1,1))
    # mation.layers[0] = layer

    mation = standardSpaceAnimation(layer)

    return mation
