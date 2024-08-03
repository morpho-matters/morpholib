'''
A collection of figure classes that can be useful for animating
Calculus concepts.
'''

import morpholib as morpho
mo = morpho
import morpholib.anim, morpholib.graph, morpholib.grid, morpholib.matrix
from morpholib.tools.basics import *

import numpy as np
from cmath import exp

deg90 = tau/4
deg270 = 3*tau/4
rot90x = morpho.matrix.rotation([1,0,0], tau/4); rot90x.flags.writeable = False
rot270y = morpho.matrix.rotation([0,1,0], -tau/4); rot270y.flags.writeable = False
swapxy = morpho.array([[0,1,0],[1,0,0],[0,0,1]]); swapxy.flags.writeable = False

# Simple numerical derivative. Calculated according to the
# double-sided formula (f(x+dx) - f(x-dx))/(2*dx) but falls back on
# a single-sided method if one of x+dx or x-dx results in an
# illegal value (e.g. nan, inf, throws error, etc.).
#
# func = Callable function to take derivative of
# x = Input value to take derivative at
# dx = Change in x value. Default: 1.0e-6
#
# Returns approximation of derivative of func at x.
def derivative(func, x, dx=1.0e-6):
    x_left = x - dx
    x_right = x + dx

    # Attempt to compute function values at x_left and x_right.
    # If it fails for any reason, just use func(x) instead
    # for a one-sided derivative.
    try:
        f_left = func(x_left)
    except Exception:
        f_left = nan
    if isbadnum(f_left):
        x_left = x
        f_left = func(x)

    try:
        f_right = func(x_right)
    except Exception:
        f_right = nan
    if isbadnum(f_right):
        x_right = x
        f_right = func(x)

    if x_left == x_right:
        raise ValueError("Cannot evaluate function on left or right of target point.")

    return (f_right - f_left)/(x_right - x_left)

diff = derivative  # Alias


class IntegralArea(morpho.Figure):

    def __init__(self, func=lambda x: x, start=0, end=1,
        strokeWeight=3, color=(0,0,0), fill=(1,0,0), alpha=1,
        steps=50, *, alphaEdge=1, alphaFill=1):

        # Construct default figure
        super().__init__()

        func = morpho.Tweenable("func", func, tags=["function"])
        start = morpho.Tweenable("start", start, tags=["scalar"])
        end = morpho.Tweenable("end", end, tags=["scalar"])
        color = morpho.Tweenable("color", list(color), tags=["color"])
        fill = morpho.Tweenable("fill", list(fill), tags=["color"])
        alphaEdge = morpho.Tweenable("alphaEdge", alphaEdge, tags=["scalar"])
        alphaFill = morpho.Tweenable("alphaFill", alphaFill, tags=["scalar"])
        alpha = morpho.Tweenable("alpha", alpha, tags=["scalar"])
        strokeWeight = morpho.Tweenable("strokeWeight", strokeWeight, tags=["scalar", "pixel"])
        steps = morpho.Tweenable("steps", steps, tags=["integer"])

        self.update([func, start, end, color, fill,
            alphaEdge, alphaFill, alpha, strokeWeight, steps])

        # # Integrand function
        # self.func = func

        # Internal polygon
        self.polygon = morpho.grid.Polygon()
        self.polygon.alphaFill = 1
        self.updatePolygon()

    def updatePolygon(self):
        path = morpho.graph.realgraph(
            self.func, self.start, self.end, self.steps,
            self.strokeWeight, self.color[:]
            )

        self.polygon.vertices = path.seq + [path.seq[-1].real, path.seq[0].real]
        self.polygon.width = self.strokeWeight
        self.polygon.color = self.color[:]
        self.polygon.fill = self.fill[:]
        self.polygon.alphaEdge = self.alphaEdge
        self.polygon.alphaFill = self.alphaFill
        self.polygon.alpha = self.alpha

    def copy(self, *args, **kwargs):
        # Copy according to superclass first
        copy = super().copy(*args, **kwargs)

        # # Now copy the function and internal polygon
        # copy.func = self.func
        # Actually, not sure we need to copy the internal
        # polygon, because I think a new one will be made
        # when the generic copy() calls the constructor.
        copy.polygon = self.polygon.copy()

        return copy

    def draw(self, camera, ctx):
        self.updatePolygon()
        self.polygon.draw(camera, ctx)

class DoubleIntegralVolume(morpho.SpaceFigure):

    def __init__(
        self, func=lambda v: v, mode="dydx",
        inmin=0, inmax=1, outmin=0, outmax=1,
        width=0, color=(0,0,0), alphaEdge=1,
        fill=(1,0,0), alphaFill=1, alpha=1,
        steps=24, origin=morpho.array([0,0,0])
        ):

        # Construct default figure
        super().__init__()

        mode = mode.lower()
        if not(mode == "dxdy" or mode == "dydx"):
            raise ValueError("mode must be 'dydx' or 'dxdy'")

        # Modify constants into constant functions for the
        # inner bounds.
        if not callable(inmin):
            inmin = lambda t, value=inmin: value
        if not callable(inmax):
            inmax = lambda t, value=inmax: value

        # Define tweenables
        # innerBounds = morpho.Tweenable("innerBounds", innerBounds, tags=["function", "list", "loop"])
        # outerBounds = morpho.Tweenable("outerBounds", outerBounds, tags=["scalar", "list"])

        func = morpho.Tweenable("func", func, tags=["function"])
        _inmin = morpho.Tweenable("_inmin", inmin, tags=["function"])
        _inmax = morpho.Tweenable("_inmax", inmax, tags=["function"])
        outmin = morpho.Tweenable("outmin", outmin, tags=["scalar"])
        outmax = morpho.Tweenable("outmax", outmax, tags=["scalar"])
        width = morpho.Tweenable("width", width, tags=["scalar", "pixel"])
        # strokeWeight = morpho.Tweenable("strokeWeight", strokeWeight, tags=["scalar"])
        color = morpho.Tweenable("color", color, tags=["color"])
        alphaEdge = morpho.Tweenable("alphaEdge", alphaEdge, tags=["scalar"])
        alphaFill = morpho.Tweenable("alphaFill", alphaFill, tags=["scalar"])
        fill = morpho.Tweenable("fill", fill, tags=["color"])
        alpha = morpho.Tweenable("alpha", alpha, tags=["scalar"])
        steps = morpho.Tweenable("steps", steps, tags=["integer"])
        _origin = morpho.Tweenable("_origin", morpho.array(origin), tags=["nparray"])

        self.update([func, _inmin, _inmax, outmin, outmax,
            width, color,
            alphaEdge, alphaFill, fill, alpha, steps, _origin])

        # Non-tweenable attributes
        self.mode = mode
        self.shading = True

    @property
    def inmin(self):
        return self._inmin

    @inmin.setter
    def inmin(self, value):
        if not callable(value):
            self._inmin = lambda t, value=value: value
        else:
            self._inmin = value

    @property
    def inmax(self):
        return self._inmax

    @inmax.setter
    def inmax(self, value):
        if not callable(value):
            self._inmax = lambda t, value=value: value
        else:
            self._inmax = value


    def copy(self):
        new = super().copy()
        new.mode = self.mode
        new.shading = self.shading
        return new

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, value):
        self._origin = morpho.array(value)

    # Returns a dict mapping a cardinal direction ("north", "east", etc.)
    # to a quadmesh representing that wall.
    def makeWalls(self):
        a,b = self.outmin, self.outmax
        xLen = b-a
        cfunc, dfunc = self.inmin, self.inmax
        dr = 1/self.steps
        swap = (self.mode.lower()=="dxdy")

        westWall = morpho.grid.quadgrid(
            view=[0,1,0,1],
            dx=1, dy=dr,
            width=self.width, color=self.color, alphaEdge=self.alphaEdge,
            fill=self.fill, alphaFill=self.alphaFill, alpha=self.alpha
            )
        westWall.shading = self.shading
        westWall = westWall.fimage(lambda v: rot270y @ v)
        westc,westd = cfunc(a), dfunc(a)
        westYlen = westd-westc
        def stretchWest(v):
            x,y,z = v
            X = a
            Y = y*westYlen + westc
            Z = z

            return morpho.array([X,Y,Z])

        westWall = westWall.fimage(stretchWest)
        if swap:
            westWall = westWall.fimage(lambda v: swapxy @ v)
        def curveWest(v):
            x,y,z = v
            X,Y = x,y
            Z = z*self.func(v)[2]

            return morpho.array([X,Y,Z])

        westWall = westWall.fimage(curveWest)


        eastWall = morpho.grid.quadgrid(
            view=[0,1,0,1],
            dx=1, dy=dr,
            width=self.width, color=self.color, alphaEdge=self.alphaEdge,
            fill=self.fill, alphaFill=self.alphaFill, alpha=self.alpha
            )
        eastWall.shading = self.shading
        eastWall = eastWall.fimage(lambda v: rot270y @ v)
        eastc,eastd = cfunc(b), dfunc(b)
        eastYlen = eastd-eastc
        def stretchEast(v):
            x,y,z = v
            X = b
            Y = y*eastYlen + eastc
            Z = z

            return morpho.array([X,Y,Z])

        eastWall = eastWall.fimage(stretchEast)
        if swap:
            eastWall = eastWall.fimage(lambda v: swapxy @ v)
        def curveEast(v):
            x,y,z = v
            X,Y = x,y
            Z = z*self.func(v)[2]

            return morpho.array([X,Y,Z])

        eastWall = eastWall.fimage(curveEast)


        southWall = morpho.grid.quadgrid(
            view=[0,1,0,1],
            dx=dr, dy=1,
            width=self.width, color=self.color, alphaEdge=self.alphaEdge,
            fill=self.fill, alphaFill=self.alphaFill, alpha=self.alpha
            )
        southWall.shading = self.shading
        southWall = southWall.fimage(lambda v: rot90x @ v)
        def stretchSouth(v):
            x,y,z = v
            X = xLen*x + a
            Y = cfunc(X)
            Z = z

            return morpho.array([X,Y,Z])

        southWall = southWall.fimage(stretchSouth)
        if swap:
            southWall = southWall.fimage(lambda v: swapxy @ v)
        def southTop(v):
            x,y,z = v
            X,Y = x,y
            Z = z*self.func(v)[2]

            return morpho.array([X,Y,Z])
        southWall = southWall.fimage(southTop)


        northWall = morpho.grid.quadgrid(
            view=[0,1,0,1],
            dx=dr, dy=1,
            width=self.width, color=self.color, alphaEdge=self.alphaEdge,
            fill=self.fill, alphaFill=self.alphaFill, alpha=self.alpha
            )
        northWall.shading = self.shading
        northWall = northWall.fimage(lambda v: rot90x @ v)
        def stretchNorth(v):
            x,y,z = v
            X = xLen*x + a
            Y = dfunc(X)
            Z = z

            return morpho.array([X,Y,Z])

        northWall = northWall.fimage(stretchNorth)
        if swap:
            northWall = northWall.fimage(lambda v: swapxy @ v)
        def northTop(v):
            x,y,z = v
            X,Y = x,y
            Z = z*self.func(v)[2]

            return morpho.array([X,Y,Z])
        northWall = northWall.fimage(northTop)

        # if self.strokeWeight > 0 and self.alphaEdge > 0:
        #     # Construct edges at the four corners
        #     SWedge = morpho.grid.SpacePath([[a,westc,0],[a,westc,self.func(mo.array([a,westc,0]))[2]] ])
        #     SEedge = morpho.grid.SpacePath([[b,eastc,0],[b,eastc,self.func(mo.array([b,eastc,0]))[2]] ])
        #     NEedge = morpho.grid.SpacePath([[b,eastd,0],[b,eastd,self.func(mo.array([b,eastd,0]))[2]] ])
        #     NWedge = morpho.grid.SpacePath([[a,westd,0],[a,westd,self.func(mo.array([a,westd,0]))[2]] ])

        #     # Assign common style parameters
        #     edges = [SWedge, SEedge, NEedge, NWedge]
        #     for fig in edges:
        #         fig.color = self.color
        #         fig.width = self.strokeWeight
        #         fig.alpha = self.alphaEdge*self.alpha
        # else:
        #     edges = []

        return {
            "west": westWall,
            "east": eastWall,
            "south": southWall,
            "north": northWall
        }


    def primitives(self, camera):
        walls = self.makeWalls()
        prims = []
        for fig in walls.values():  # + edges:
            prims.extend(fig.primitives(camera))
        return prims




class Wall(morpho.SpaceFigure):

    def __init__(
        self, func=lambda v: v, start=morpho.array([0,0]), end=morpho.array([1,0]),
        strokeWeight=3, color=(0,0,0), alphaEdge=1, fill=(1,0,0), alphaFill=1, alpha=1,
        steps=50, origin=morpho.array([0,0,0])):

        # Construct default figure
        super().__init__()

        # Define tweenables
        func = morpho.Tweenable("func", func, tags=["function"])
        _start = morpho.Tweenable("_start", morpho.array(start), tags=["nparray"])
        _end = morpho.Tweenable("_end", morpho.array(end), tags=["nparray"])
        strokeWeight = morpho.Tweenable("strokeWeight", strokeWeight, tags=["scalar", "pixel"])
        color = morpho.Tweenable("color", color, tags=["color"])
        alphaEdge = morpho.Tweenable("alphaEdge", alphaEdge, tags=["scalar"])
        alphaFill = morpho.Tweenable("alphaFill", alphaFill, tags=["scalar"])
        fill = morpho.Tweenable("fill", fill, tags=["color"])
        alpha = morpho.Tweenable("alpha", alpha, tags=["scalar"])
        steps = morpho.Tweenable("steps", steps, tags=["integer"])
        _origin = morpho.Tweenable("_origin", morpho.array(origin), tags=["nparray"])

        self.update([func, _start, _end, strokeWeight, color, fill,
            alpha, alphaEdge, alphaFill, steps, _origin])

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, value):
        self._start = morpho.array(value)

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, value):
        self._end = morpho.array(value)

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, value):
        self._origin = morpho.array(value)

    def makePolygon(self):
        # v0 = np.pad(self.start, (0,1))
        # v1 = np.pad(self.end, (0,1))
        v0 = self.start
        v1 = self.end
        top = morpho.grid.spaceline(v0, v1, steps=self.steps)

        # def f(v):
        #     x,y,z = v
        #     X = x
        #     Y = y
        #     Z = self.func([x,y])

        #     return morpho.array([X,Y,Z])

        top = top.fimage(self.func)
        vertices = top.seq + [v1, v0]
        wall = morpho.grid.SpacePolygon(vertices, width=self.strokeWeight,
            color=self.color, alphaEdge=self.alphaEdge, fill=self.fill,
            alphaFill=self.alphaFill, alpha=self.alpha)
        if not np.allclose(self.origin, (0,0,0)):
            wall = wall.fimage(lambda v: v + self.origin)

        return wall

    def primitives(self, camera):
        wall = self.makePolygon()
        return wall.primitives(camera)


class RiemannRect(morpho.Figure):

    def __init__(self, width=1, height=1, pos=0,
        color=(0,0,0), fill=(1,0,0), alpha=1, align=0,
        strokeWeight=3, *, alphaFill=1):
        # Construct a default figure
        super().__init__()

        width = morpho.Tweenable("width", width, tags=["scalar"])
        height = morpho.Tweenable("height", height, tags=["scalar"])
        pos = morpho.Tweenable("pos", pos, tags=["complex", "position"])
        color = morpho.Tweenable("color", list(color), tags=["color"])
        fill = morpho.Tweenable("fill", list(fill), tags=["color"])
        alpha = morpho.Tweenable("alpha", alpha, tags=["scalar"])
        align = morpho.Tweenable("align", align, tags=["scalar"])
        strokeWeight = morpho.Tweenable("strokeWeight", strokeWeight, tags=["scalar", "pixel"])

        # Initialize tweenables
        self.update([width, height, pos, color, fill, alpha, align, strokeWeight])

        self.Tweenable("alphaFill", alphaFill, tags=["scalar"])

        # Initialize polygon reference figure
        self.polygon = morpho.grid.Polygon(
            vertices=[0,0,0,0], width=self.strokeWeight, color=self.color,
            fill=self.fill, alphaFill=1, alpha=self.alpha
            )
        self.updatePolygon()

    # Updates polygon reference figure
    def updatePolygon(self):
        # Locate corners of the rectangle
        SW = -self.width/2*(self.align + 1) + self.pos
        NW = SW + self.height*1j
        NE = NW + self.width
        SE = SW + self.width

        self.polygon.vertices = [SW, NW, NE, SE]
        self.polygon.width = self.strokeWeight
        self.polygon.color = self.color[:]
        self.polygon.fill = self.fill[:]
        self.polygon.alpha = self.alpha
        self.polygon.alphaFill = self.alphaFill

    # Again, not sure this is needed because generic copy()
    # will call the constructor thereby initializing a new
    # internal polygon.
    def copy(self):
        C = super().copy()
        C.polygon = self.polygon.copy()
        return C

    def draw(self, camera, ctx):
        self.updatePolygon()
        self.polygon.draw(camera, ctx)

class RiemannDisk(morpho.Figure):

    def __init__(self, thickness=1, radius=1, tilt=0.1, pos=0,
        outlineColor=(0,0,0), faceFill=(0.25,0.25,0.5), edgeFill=(0.5, 0.5, 1),
        alpha=1, align=0, strokeWeight=3):
        # Construct a default figure
        super().__init__()

        thickness = morpho.Tweenable("thickness", thickness, tags=["scalar"])
        radius = morpho.Tweenable("radius", radius, tags=["scalar"])
        tilt = morpho.Tweenable("tilt", tilt, tags=["scalar"])
        pos = morpho.Tweenable("pos", pos, tags=["complex", "position"])
        outlineColor = morpho.Tweenable("outlineColor", list(outlineColor), tags=["color"])
        faceFill = morpho.Tweenable("faceFill", list(faceFill), tags=["color"])
        edgeFill = morpho.Tweenable("edgeFill", list(edgeFill), tags=["color"])
        alpha = morpho.Tweenable("alpha", alpha, tags=["scalar"])
        align = morpho.Tweenable("align", align, tags=["scalar"])
        strokeWeight = morpho.Tweenable("strokeWeight", strokeWeight, tags=["scalar", "pixel"])

        # Initialize tweenables
        self.update([thickness, radius, tilt, pos, outlineColor,
            faceFill, edgeFill, alpha, align, strokeWeight])

        # Initialize ellipse reference figure
        self.face = morpho.shapes.Ellipse(alphaFill=1)
        self.updateFace()

    # Update ellipse figure representing the disk's face.
    def updateFace(self):
        self.face.pos = self.pos - (self.align-1)/2*self.thickness
        self.face.xradius = self.tilt*self.radius
        self.face.yradius = self.radius
        self.face.strokeWeight = self.strokeWeight
        self.face.color = self.outlineColor[:]
        self.face.fill = self.faceFill[:]
        self.face.alpha = self.alpha

    def draw(self, camera, ctx):
        view = camera.view

        self.updateFace()
        # if self.face.xradius == 0 or self.face.yradius == 0:
        #     return

        # Draw the disk edge first.
        # Find peak of the ellipse and move the pen to it.
        z = self.face.pos + self.face.yradius*1j
        X,Y = morpho.screenCoords(z, view, ctx)
        ctx.move_to(X,Y)

        # Draw upper edge of disk
        WIDTH = morpho.pixelWidth(self.thickness, view, ctx)
        ctx.rel_line_to(-WIDTH, 0)

        # Draw leftmost edge of disk
        ctx.save()
        X,Y = morpho.screenCoords(self.face.pos, view, ctx)
        ctx.translate(X-WIDTH, Y)
        ctx.scale(
            max(morpho.pixelWidth(self.face.xradius, view, ctx), 0.1),
            max(morpho.pixelHeight(self.face.yradius, view, ctx), 0.1)
            )
        ctx.arc(0,0, 1, deg90, deg270)
        ctx.restore()

        # Draw lower edge of disk
        ctx.rel_line_to(WIDTH, 0)

        # Close the path and fill the remainder with the edge fill
        ctx.close_path()
        ctx.set_source_rgba(*self.edgeFill, self.alpha)
        ctx.fill_preserve()

        # Stroke path
        if self.strokeWeight < 0.5:  # Don't stroke if strokeWeight is too small
            ctx.new_path()
        else:
            ctx.set_source_rgba(*self.outlineColor, self.alpha)
            ctx.set_line_width(self.strokeWeight)
            ctx.stroke()

        # Now draw the face
        self.face.draw(camera, ctx)


# Constructs the Riemann rectangles for a given function
# over a given interval.
# align = -1 => left-hand rects
# align = 1 => right-hand rects
# align = 0 => midpoints
def RiemannSum(func, interval, rectCount, align=-1,
    color=(0,0,0), fill=(1, 0.3, 0.3), strokeWeight=3,
    transition=morpho.transitions.slow_fast_slow,
    *, alphaFill=1):

    a,b = interval
    dx = (b-a)/rectCount

    frame = morpho.anim.Frame()
    for i in range(rectCount):
        x = a + (i + (align+1)/2)*dx
        rect = RiemannRect(
            width=dx, height=func(x), pos=x,
            color=list(color), fill=list(fill),
            align=align, strokeWeight=strokeWeight,
            alphaFill=alphaFill
            )
        rect.transition = transition
        frame.figures.append(rect)

    return frame

def RiemannSumApproach(
    func, interval, initRectCount=2,
    align=-1, doublings=1,
    tweenDuration=30, pauseDuration=30,
    color=(0,0,0), fill=(1, 0.3, 0.3), strokeWeight=3,
    view=(-5,5, -5,5), transition=morpho.transitions.slow_fast_slow):

    frame0 = RiemannSum(
        func, interval, initRectCount, align, color, fill, strokeWeight, transition
        )
    frames = [frame0]

    # Construct other Riemann sums
    rectCount = initRectCount
    for n in range(doublings):
        rectCount *= 2
        frame = RiemannSum(
            func, interval, rectCount, align, color, fill, strokeWeight, transition
            )
        frames.append(frame)

    # # Test animate
    # mation = morpho.Animation()
    # for n in range(len(frames)):
    #     frame = frames[n]
    #     frame.delay = tweenDuration + pauseDuration - 1
    #     frame = morpho.Actor(frame)
    #     mation.merge(frame, atFrame=(n)*(tweenDuration+pauseDuration))
    # return mation

    # Animate!
    mation = morpho.Animation()
    for n in range(len(frames)-1):
        frame = frames[n]
        # frame.delay = pauseDuration
        # layer = morpho.anim.Layer(frame, view=view)
        # mation.merge(layer, atFrame=n*(tweenDuration))

        # Create doubled-in-place version
        copy1 = frame.copy()
        copy2 = frame.copy()
        doubledFrame = morpho.anim.Frame()
        for j in range(len(frame.figures)):
            doubledFrame.figures.append(copy1.figures[j])
            doubledFrame.figures.append(copy2.figures[j])

        # Create a film where the doubled frame turns into
        # the next frame
        film = morpho.Actor(doubledFrame)
        film.newkey(tweenDuration, frames[n+1])

        layer = morpho.Layer(film, view=view)
        mation.merge(layer, atFrame=n*tweenDuration)

    for n in range(len(frames)):
        mation.delays[n*tweenDuration] = pauseDuration

    return mation

def RiemannDiskSum(func, interval, diskCount, align=-1, tilt=0.3,
    outlineColor=(0,0,0), faceFill=(0.25,0.25,0.5), edgeFill=(0.5, 0.5, 1),
    strokeWeight=3,
    transition=morpho.transitions.slow_fast_slow):

    a,b = interval
    dx = (b-a)/diskCount

    frame = morpho.anim.Frame()
    for i in range(diskCount):
        x = a + (i + (align+1)/2)*dx
        disk = RiemannDisk(
            thickness=dx, radius=func(x), tilt=tilt, pos=x,
            outlineColor=outlineColor, faceFill=faceFill, edgeFill=edgeFill,
            align=align, strokeWeight=3
            )
        disk.transition = transition
        frame.figures.append(disk)

    return frame

def RiemannDiskSumApproach(
    func, interval, initDiskCount=2,
    align=-1, tilt=0.3, doublings=1,
    tweenDuration=30, pauseDuration=30,
    outlineColor=(0,0,0), faceFill=(0.25,0.25,0.5), edgeFill=(0.5, 0.5, 1),
    strokeWeight=3,
    view=(-5,5, -5,5), transition=morpho.transitions.slow_fast_slow):

    frame0 = RiemannDiskSum(
        func, interval, initDiskCount, align, tilt,
        outlineColor, faceFill, edgeFill, strokeWeight,
        transition
        )
    frames = [frame0]

    # Construct other Riemann sums
    diskCount = initDiskCount
    for n in range(doublings):
        diskCount *= 2
        frame = RiemannDiskSum(
            func, interval, diskCount, align, tilt,
            outlineColor, faceFill, edgeFill, strokeWeight,
            transition
            )
        frames.append(frame)

    # Animate!
    mation = morpho.Animation()
    for n in range(len(frames)-1):
        frame = frames[n]
        # frame.delay = pauseDuration
        # layer = morpho.anim.Layer(frame, view=view)
        # mation.merge(layer, atFrame=n*(tweenDuration))

        # Create doubled-in-place version
        copy1 = frame.copy()
        copy2 = frame.copy()
        doubledFrame = morpho.anim.Frame()
        for j in range(len(frame.figures)):
            doubledFrame.figures.append(copy1.figures[j])
            doubledFrame.figures.append(copy2.figures[j])

        # Create a film where the doubled frame turns into
        # the next frame
        film = morpho.Actor(doubledFrame)
        film.newkey(tweenDuration, frames[n+1])

        layer = morpho.Layer(film, view=view)
        mation.merge(layer, atFrame=n*tweenDuration)

    for n in range(len(frames)):
        mation.delays[n*tweenDuration] = pauseDuration

    return mation

# Revolves a copy of the given point by the specified angle.
def revolvePoint(point, theta, axis="x", axisOffset=0, stretch=0.2):
    point = point.copy()
    if axis.lower() == "x":
        C0 = point.pos.real + axisOffset*1j  # Center of rotation
        point.pos = (point.pos - C0)*exp(theta*1j)
        point.pos = stretch*point.pos.real + point.pos.imag*1j
        point.pos += C0
    elif axis.lower() == "y":
        pass
    else:
        raise ValueError('axis must be "x" or "y"')
    return point

# Revolves a copy of the given path by the specified angle.
def revolvePath(path, theta, axis="x", axisOffset=0, tilt=0.1):
    path = path.copy()
    if axis.lower() == "x":
        for n in range(len(path.seq)):
            z = path.seq[n]
            C0 = z.real + axisOffset*1j  # Center of rotation
            z = (z - C0)*exp(theta*1j)
            z = tilt*z.real + z.imag*1j
            z += C0

            path.seq[n] = z
    elif axis.lower() == "y":
        pass
    else:
        raise ValueError('axis must be "x" or "y"')
    return path

def revolvePathSolid(path, theta,
    axis="x", axisOffset=0, tilt=0.1, dtheta=0.03,
    angleSpacing=pi/6, Nsubarcs=10,
    fill=(0.35, 0.35, 1), innerfill=(0.35/2, 0.35/2, 1/2)):

    path = path.copy()
    if axis.lower() == "x":
        # Constrain theta between 0 and tau
        theta = min(max(theta, 0), tau)

        pathFinal = revolvePath(path, min(theta, pi), axis, axisOffset, tilt)

        # Make first-pass righthand boundary vertices
        rverts1 = []
        pt = morpho.grid.Point(path.seq[-1])
        for n in range(1, int(min(theta, pi)//dtheta)):
            rverts1.append(revolvePoint(pt, n*dtheta, axis, axisOffset, tilt).pos)
        if theta >= pi:
            rverts1.append(revolvePoint(pt, pi, axis, axisOffset, tilt).pos)

        # Make second-pass righthand boundary vertices
        rverts2 = []
        for n in range(1, int((theta-pi)//dtheta)):
            rverts2.append(revolvePoint(pt, pi+n*dtheta, axis, axisOffset, tilt).pos)
        if theta == tau:
            rverts2.append(pt.pos)

        # Make lefthand boundary vertices
        lverts = []
        pt = morpho.grid.Point(path.seq[0])
        for n in range(1, int(min(theta, pi)//dtheta)):
            lverts.append(revolvePoint(pt, n*dtheta, axis, axisOffset, tilt).pos)
        if theta >= pi:
            lverts.append(revolvePoint(pt, pi, axis, axisOffset, tilt).pos)

        # Define main polygon
        mainpoly = morpho.grid.Polygon(
            vertices=path.seq[:] + rverts1[:] + pathFinal.seq[::-1] + lverts[::-1],
            width=path.width, color=path.color[:], fill=fill,
            alphaFill=1
            )

        frame = morpho.Frame([mainpoly])

        # Define inner polygon
        if theta > pi:
            pathFinalTrue = revolvePath(
                path, theta, axis, axisOffset, tilt
                )
            innerpoly = morpho.grid.Polygon(
                vertices=rverts2[:] + [path.seq[0].real + 1j*rverts2[-1].imag, lverts[-1]],
                width=path.width, color=path.color[:],
                fill=innerfill, alphaFill=1
                )
            frame.figures.insert(0, innerpoly)

        # Define subpaths
        subpaths = []
        for n in range(1, int(min(theta, pi)//angleSpacing + 1)):
            angle = n*angleSpacing
            # Don't render a subpath at pi.
            if abs(angle-pi) < 1e-9:
                continue
            subpath = revolvePath(
                path, angle, axis, axisOffset, tilt
                )
            subpath.width /= 2
            subpaths.append(subpath)
        frame.figures.extend(subpaths)

        # Define subarcs
        subarcs = []
        len_seq = len(path.seq)
        for n in range(1, Nsubarcs+1):
            index = len_seq*n//(Nsubarcs+1)
            pos = path.seq[index].real + axisOffset*1j
            yradius = path.seq[index].imag - axisOffset
            xradius = tilt*yradius
            arc = morpho.shapes.EllipticalArc(
                pos, xradius, yradius,
                theta0=tau/4, theta1=tau/4+min(theta, pi),
                strokeWeight=path.width/2, color=path.color
                )
            subarcs.append(arc)
        frame.figures.extend(subarcs)

        return frame

    elif axis.lower() == "y":
        pass
    else:
        raise ValueError('axis must be "x" or "y"')
