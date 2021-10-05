'''
Classes and functions having to do with color.
'''

import morpholib as morpho
from morpholib import numTween
from morpholib.tools.basics import listfloor, listceil

import math, cairo
import numpy as np

# Normalizes an RGB triplet in the range [0...255] into
# the range [0.0, 1.0].
# RGB can be specified as three separate inputs, or as a
# tuple supplied as one input.
# Optional upperbound argument can be supplied to change
# what the max possible value for the input RGB values is.
# Default: 255.
def rgbNormalize(R, G=None, B=None, upperbound=255):
    # If one of the components is missing,
    # assume user supplied RGB as a tuple in the first input.
    if G is None or B is None:
        R,G,B = R
    return (R/upperbound, G/upperbound, B/upperbound)

# Checks that a string codes to a valid hex color
# That is, consists only of the characters "0" thru "f"
# Returns boolean indicating validity.
def validHexColor(string):
    string = string.lower()
    for char in string:
        if char not in "0123456789abcdef":
            return False
    return True

# Parses a hex color string into an RGB triple (0-1, 0-1, 0-1)
# If optional argument normalize is set to False, the RGB triple returned
# is the raw hex data in the range [0...255]: (0-255, 0-255, 0-255).
# By default: normalize = True.
def parseHexColor(string, normalize=True):
    if not validHexColor(string):
        raise ValueError("Not a valid hex string!")
    N = int(string, 16)
    B = N % 256

    N = N // 256
    G = N % 256

    N = N // 256
    R = N % 256

    if normalize:
        return tuple(X/255 for X in (R,G,B))
    else:
        return (R,G,B)

# Takes a color string (whether named or hex) and returns
# the normalized RGB triple (0-1, 0-1, 0-1)
def colorStr2Tuple(string):
    string = string.strip().lower()
    if string in colormap:
        return colormap[string]
    else:
        return rgbNormalize(parseHexColor(string))

# Same as colorStr2Tuple but returns a list instead of a tuple.
def colorStr2List(string):
    return list(colorStr2Tuple(string))

# Dict of named colors
colormap = {
    "black": (0,0,0),
    "white": (1,1,1),
    "red": (1,0,0),
    "green": rgbNormalize(0x23, 0xb5, 0x83),
    "blue": (0,0,1),
    "yellow": (1,1,0),
    "magenta": (1,0,1),
    "cyan": (0,1,1),
    "orange": rgbNormalize(0xff, 0xa5, 0),
    "violet": parseHexColor("800080"),
    "brown": rgbNormalize(0x80, 0x40, 0)
}

# List of the colors in proper order.
# For use in constructing the combobox ONLY!
# colormap should be used for programming purposes.
colors = ["red", "green", "blue", "yellow", "cyan", "magenta",
    "orange", "violet", "brown", "white", "black"]

# Transparently overlays the color A over the color B
# using transparency alpha (default=0.5)
def alphaOverlay(A, B, alpha=0.5):
    if type(A) is list or type(A) is tuple:
        result = [0,0,0]
        for i in range(len(A)):
            result[i] = alphaOverlay(A[i], B[i], alpha)
        return tuple(result)
    else:
        return A*alpha + B*(1-alpha)

# Tweens two RGB colors represented by triples and returns
# a new list with the tweened value.
def colorTween(rgb1, rgb2, t, start=0, end=1):
    if rgb1 == rgb2: return rgb1

    R1, G1, B1 = rgb1
    R2, G2, B2 = rgb2

    dR = R2 - R1
    dG = G2 - G1
    dB = B2 - B1

    R = R1 + t*dR
    G = G1 + t*dG
    B = B1 + t*dB

    R = numTween(R1, R2, t, start, end)
    G = numTween(G1, G2, t, start, end)
    B = numTween(B1, B2, t, start, end)

    return [R,G,B]



# Provides a datatype in which you can specify gradients like color
# gradients or variable width paths. It inherits off of Figure, but
# it's not really supposed to function like a figure. There's no draw()
# method, for example. But making it a figure allows it to possess
# tween methods, which will be helpful for any classes that want to use
# gradients so that they don't have to worry about how to do the tweening
# themselves.
#
# Usage: Gradient(data) where "data" is a dict mapping numbers in the
# unit interval [0,1] to color values.
class Gradient(morpho.Figure):
    def __init__(self, data=None):
        if data is None:
            data = {}
        elif isinstance(data, list) or isinstance(data, tuple):
            data = {0: data}
        elif isinstance(data, float) or isinstance(data, int):
            data = {0: data}
        elif not isinstance(data, dict):
            raise TypeError("Unsupported type for data supplied to Gradient()")


        super().__init__()

        # Define tweenables

        # data is a dict that maps floats in the range [0,1]
        # to gradient waypoint values (e.g. RGB, floats, etc.)
        data = morpho.Tweenable("data", data, tags=["gradient", "nolinear", "nospiral"])
        self.update([data])

        # Set to true to identify 0 with 1 and make the gradient looped.
        # For now this is not implemented and does nothing.
        self.cycle = False


    def copy(self):
        # Copy according to superclass first
        new = super().copy()

        # Go thru the data dict and make copies of each individual value (if needed)
        for key in new.data:
            value = new.data[key]
            if "copy" in dir(value):
                new.data[key] = value.copy()

        # Copy the non-tweenable attributes manually
        new.cycle = self.cycle

        return new


    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def __len__(self):
        return len(self.data)

    # Returns the interpolated gradient value at the specified x in [0,1]
    def value(self, x):
        if len(self.data) == 0:
            raise KeyError("This gradient has no keys. Cannot interpolate an empty gradient.")

        keylist = sorted(list(self.data.keys()))

        x = float(x)  # Convert to python float

        # If the given parameter is a key in the dict, just return the value
        if x in keylist:
            return self[x]

        # Compute the latest key
        k = listfloor(keylist, x)
        if k == -1: return self[keylist[0]]
        key = keylist[k]

        # Grab latest value
        keyval = self.data[key]

        if key == keylist[-1]:
            return keyval
        else:
            key2 = keylist[k+1]
            keyval2 = self[key2]
            if isinstance(keyval, list) or isinstance(keyval, tuple):
                return type(keyval)(map(morpho.numTween, keyval, keyval2, ((x-key)/(key2-key),)*len(keyval)))
            else:
                return morpho.numTween(keyval, keyval2, x, start=key, end=key2)

    # Generates a new Gradient which is a segment between the values [a,b] of the
    # current gradient.
    def segment(self, a, b=None):
        if len(self.data) == 0:
            return Gradient()

        keylist = sorted(list(self.data.keys()))
        if b is None:
            b = keylist[-1]

        segdata = {}
        segdata[a] = self.value(a)
        start = listceil(keylist, a)
        end = listfloor(keylist, b)
        for x in keylist[start:end+1]:
            segdata[x] = self.data[x]
        segdata[b] = self.value(b)

        return Gradient(segdata).copy()  # To handle needing to make copies of lists, etc.

    # Normalizes the gradient parameter space so that the lowest parameter is 0
    # and the highest parameter is 1. Does nothing if the gradient has fewer than 2
    # nodes. This function also affects the gradient IN PLACE!
    def normalize(self):
        if len(self.data) < 2:
            return
        newdata = {}
        start = min(self.data)
        end = max(self.data)
        for x in self.data.keys():
            newdata[morpho.numTween(0, 1, x, start, end)] = self.data[x]
        self.data = newdata

    def verify(self):
        for key in self.data:
            if not(0 <= key <= 1):
                raise ValueError("Gradient error contains key values not in the range [0,1]")

    def __repr__(self):
        if len(self.data) == 0:
            return "Gradient()"

        keys = list(self.data.keys())
        lines = []
        for key in keys:
            lines.append(repr(key) + ": " + repr(self.data[key]))

        return "Gradient({\n    " + ",\n    ".join(lines) + "\n})"


    @morpho.TweenMethod
    def tweenLinear(self, other, t):
        # # Defaults to the empty tuple.
        # if ignore is None:
        #     ignore = ()
        # # Convert string to tuple containing string
        # elif isinstance(ignore, str):
        #     ignore = (ignore,)

        # if "data" in ignore:
        #     return self.copy()

        self.verify()
        other.verify()

        if len(self.data) > len(other.data):
            # Tweened figure inherits basic attributes of self,
            # but gets its state determined by the following code.
            tw = self.copy()
            tw.update(other.tweenLinear(self, 1-t)._state)
            return tw
        elif len(self.data) < len(other.data):
            numNewNodes = len(other.data) - len(self.data)
            M = numNewNodes + 1

            # If self is empty, just return copy of other.
            if len(self.data) == 0:
                return other.copy()

            # Make a copy of self and populate it with more nodes
            newself = self.copy()

            # How many new nodes need to be added?

            # First get a list of nodes (and include 0 and 1 if not)
            nodes = sorted(list(self.data.keys()))
            if nodes[0] != 0:
                nodes.insert(0, 0)
            if nodes[-1] != 1:
                nodes.append(1)

            # Iterate over the gaps, indexed by left endpoint
            for n in range(len(nodes)-1):
                # Identify endpoints and number N of new nodes
                # to sprinkle in this gap.
                a = nodes[n]
                b = nodes[n+1]
                N = math.ceil(M*b) - math.ceil(max(M*a, 1))

                # Sprinkle new nodes in uniformly local to the gap
                gapSize = b - a
                for k in range(1, N+1):
                    newNode = a + k/(N+1)*gapSize
                    newself.data[newNode] = self.value(newNode)

            # Temporary for testing! Remove this at some point!
            assert len(newself.data) == len(other.data)

            return newself.tweenLinear(other, t)

        # From this point, we assume the dict lengths are the same.

        # Get keys in sorted order
        selfkeys = sorted(list(self.data.keys()))
        otherkeys = sorted(list(other.data.keys()))
        newkeys = list(map(morpho.numTween, selfkeys, otherkeys, (t,)*len(selfkeys)))

        selfvals = [self.data[selfkeys[n]] for n in range(len(selfkeys))]
        othervals = [other.data[otherkeys[n]] for n in range(len(otherkeys))]

        if isinstance(selfvals[0], list) or isinstance(selfvals[0], tuple):
            newvals = []
            for n in range(len(selfvals)):
                selfval = selfvals[n]
                otherval = othervals[n]
                newvals.append(type(selfval)(map(morpho.numTween, selfval, otherval, (t,)*len(selfval))))
        else:
            newvals = list(map(morpho.numTween, selfvals, othervals, (t,)*len(selfvals)))

        # Construct updated data dict
        data = {}
        for n in range(len(newkeys)):
            data[newkeys[n]] = newvals[n]

        # Construct tweened Gradient figure
        tw = type(self)(data)  # Using type(self) instead of explicit Gradient() for sake of possible inheritance
        tw.cycle = self.cycle

        return tw

    # For this figure, spiral tween and linear tween are identical
    tweenSpiral = tweenLinear

    # Pivot tween is not supported for gradients
    def tweenPivot(self, other, t):
        raise NotImplementedError


# Decorator modifies tween methods to support
# gradients for the specified tweenables.
#
# Example usage:
# @morpho.TweenMethod
# @handleGradients(["color", "fill", "alpha"])
# def tweenLinear(self, other, t):
#     etc.
def handleGradients(gradTweenableNames):
    def decorator(twMethod):
        def wrapper(self, other, t, *args, **kwargs):
            # Use the original tween method as normal.
            # The given tween method should be designed to ignore
            # the tweenables that may contain gradients.
            tw = twMethod(self, other, t, *args, **kwargs)

            for name in gradTweenableNames:
                # If both are gradients...
                if isinstance(self._state[name].value, Gradient) and isinstance(other._state[name].value, Gradient):
                    # tw.color = self.color.tweenLinear(other.color, t)
                    tw._state[name].value = self._state[name].value.tweenLinear(other._state[name].value, t)
                # self is gradient but not other
                elif isinstance(self._state[name].value, Gradient):
                    othercopy_state_name = self._state[name].value.copy()
                    for key in othercopy_state_name.data:
                        value = other._state[name].value
                        othercopy_state_name[key] = value.copy() if "copy" in dir(value) else value
                    tw._state[name].value = self._state[name].value.tweenLinear(othercopy_state_name, t)
                # other is gradient but not self
                elif isinstance(other._state[name].value, Gradient):
                    selfcopy_state_name = other._state[name].value.copy()
                    for key in selfcopy_state_name.data:
                        value = self._state[name].value
                        selfcopy_state_name[key] = value.copy() if "copy" in dir(value) else value
                    tw._state[name].value = selfcopy_state_name.tweenLinear(other._state[name].value, t)
                # neither are gradients
                else:
                    value = self._state[name].value
                    if isinstance(value, list) or isinstance(value, tuple):
                        tw._state[name].value = type(value)(map(morpho.numTween, self._state[name].value, other._state[name].value, (t,)*len(value)))
                    elif isinstance(value, np.ndarray):
                        tw._state[name].value = morpho.numTween1(self._state[name].value, other._state[name].value, t)
                    else:
                        tw._state[name].value = morpho.numTween(self._state[name].value, other._state[name].value, t)

            return tw
        return wrapper
    return decorator


# This class does nothing (by itself). It just exists to be the parent of all
# GradientFill subclasses like GradientFillLinear and GradientFillRadial.
# It makes it easier to implement handleGradientFills because I can use
# isinstance(fig, GradientFill) to check for being an object of ANY
# GradientFill subclass.
class GradientFill(morpho.Figure):
    # This method should be tailored to each subclass. It should generate
    # a cairo source object (like gradient or mesh pattern). It is also
    # expected that this method will implicitly call
    # ctx.save() via morpho.pushPhysicalCoords(), so you will always need
    # to call ctx.restore() at some later point after calling this method.
    def makeSource(self, camera, ctx, alpha=1, pushPhysicalCoords=True):
        if pushPhysicalCoords:
            morpho.pushPhysicalCoords(camera.view, ctx)  # Implicit ctx.save()
        return None

    # This method should be tailored to each subclass.
    # It generates the correct gradient source object (after
    # pushing physical coordinates) and then calls
    # fill_preserve() on the given cairo context.
    # It then calls ctx.restore() as a final step, so the
    # transformation stack should be unchanged after this method is
    # finished.
    def draw(self, camera, ctx, alpha=1, pushPhysicalCoords=True):
        source = self.makeSource(camera, ctx, alpha, pushPhysicalCoords)  # Implicitly calls ctx.save()
        ctx.set_source(source)
        ctx.fill_preserve()
        if pushPhysicalCoords:
            ctx.restore()

# Non-drawable figure that describes how to fill a shape with a linear
# gradient.
# "tail" and "head" represent where (in physical space) the gradient should
# begin and end (tail: z=0, and head: z=1). Default to tail=0, head=1.
# "gradient" is the Gradient figure used. Defaults to the blank Gradient.
# "origin" describes where in physical space the origin of gradient space is
# in the event that you want gradient physical coordinates to be offset
# from the standard physical coordinates. Defaults to origin=0 so that
# gradient space and physical space coincide.
# Basically, origin is just a translation parameter that can be added to
# head and tail by classes that use GradientFill.
# Please note that the expression "self.head" and "self.tail" will NOT
# automatically incorporate the origin offset. "origin" is just data,
# and it is the responsibility of classes that use GradientFill to make
# use of the origin attribute if they so choose.
# Correct usage: PHYSICAL tail = self.origin + self.tail
class LinearGradientFill(GradientFill):
    def __init__(self, tail=0, head=1, gradient=None, origin=0):
        if gradient is None:
            gradient = Gradient()

        # Use superclass constructor
        super().__init__()

        # Tweenables
        tail = morpho.Tweenable("tail", tail, tags=["complex", "tail"])
        head = morpho.Tweenable("head", head, tags=["complex", "head"])
        gradient = morpho.Tweenable("gradient", gradient, tags=["gradient", "nolinear", "nospiral"])
        origin = morpho.Tweenable("origin", origin, tags=["complex"])

        self.update([tail, head, gradient, origin])

    # Returns a cairo gradient object which can be set as a cairo source to draw
    # a gradient somewhere
    def makeGradient(self, camera, ctx, alpha=1, pushPhysicalCoords=True):
        if pushPhysicalCoords:
            morpho.pushPhysicalCoords(camera.view, ctx)  # Implicit ctx.save()

        # X0, Y0 = morpho.screenCoords(self.fill.tail+self.fill.origin, view, ctx)
        # X1, Y1 = morpho.screenCoords(self.fill.head+self.fill.origin, view, ctx)
        # cairoGrad = cairo.LinearGradient(X0,Y0, X1,Y1)
        z0 = self.tail + self.origin
        z1 = self.head + self.origin
        cairoGrad = cairo.LinearGradient(z0.real, z0.imag, z1.real, z1.imag)
        # If the color gradient is an RGBA gradient,
        # use the alpha values accordingly.
        if len(list(self.gradient.data.values())[0]) == 4:
            for key in self.gradient.data:
                R,G,B,A = self.gradient[key]
                cairoGrad.add_color_stop_rgba(key, R,G,B, A*alpha)
        else:
            for key in self.gradient.data:
                cairoGrad.add_color_stop_rgba(key, *self.gradient[key], alpha)
        # ctx.set_source(cairoGrad)
        # ctx.fill_preserve()
        return cairoGrad

    makeSource = makeGradient

    # # Fills whatever the current path of the given cairo context is with the
    # # gradient specified by this figure.
    # def fillCurrentPath(self, camera, ctx):
    #     raise NotImplementedError

    #     cairoGrad = self.makeGradient(camera, ctx)
    #     ctx.set_source(cairoGrad)
    #     ctx.fill_preserve()

    @morpho.TweenMethod
    @handleGradients(["gradient"])
    def tweenLinear(self, other, t, *args, **kwargs):
        return super().tweenLinear(other, t, *args, **kwargs)


# Non-drawable figure that describes how to draw a radial gradient fill.
# "center" is a position (complex number) in physical space where the
# gradient is centered.
# r0, r1 denote the inner and outer physical radii of the gradient respectively.
# "gradient" is the Gradient figure used. Defaults to the blank Gradient.
# "origin" describes where in physical space the origin of gradient space is
# in the event that you want gradient physical coordinates to be offset
# from the standard physical coordinates. Defaults to origin=0 so that
# gradient space and physical space coincide.
# Basically, origin is just a translation parameter that can be added to
# the "center" tweenable by classes that use GradientFill.
class RadialGradientFill(GradientFill):
    def __init__(self, center=0, r0=0, r1=1, gradient=None, origin=0):
        if gradient is None:
            gradient = Gradient()

        # Use superclass constructor
        super().__init__()

        # Tweenables
        center = morpho.Tweenable("center", center, tags=["complex", "position"])
        r0 = morpho.Tweenable("r0", r0, tags=["scalar"])
        r1 = morpho.Tweenable("r1", r1, tags=["scalar"])
        gradient = morpho.Tweenable("gradient", gradient, tags=["gradient", "nolinear", "nospiral"])
        origin = morpho.Tweenable("origin", origin, tags=["complex"])

        self.update([center, r0, r1, gradient, origin])

    # Returns a cairo gradient object which can be set as a cairo source to draw
    # a gradient somewhere.
    # PLEASE NOTE: This method implicitly calls ctx.save(), so you will
    # need to call ctx.restore() later to reset it.
    def makeGradient(self, camera, ctx, alpha=1, pushPhysicalCoords=True):
        if pushPhysicalCoords:
            morpho.pushPhysicalCoords(camera.view, ctx)  # Implicit ctx.save()

        # X0, Y0 = morpho.screenCoords(self.fill.center+self.fill.origin, view, ctx)
        # R0 = morpho.pixelWidth(self.fill.r0, view, ctx)
        # R1 = morpho.pixelWidth(self.fill.r1, view, ctx)

        z0 = self.center + self.origin
        cairoGrad = cairo.RadialGradient(
            z0.real,z0.imag, self.r0, z0.real,z0.imag, self.r1
            )
        # If the color gradient is an RGBA gradient,
        # use the alpha values accordingly.
        if len(list(self.gradient.data.values())[0]) == 4:
            for key in self.gradient.data:
                R,G,B,A = self.gradient[key]
                cairoGrad.add_color_stop_rgba(key, R,G,B, A*alpha)
        else:
            for key in self.gradient.data:
                cairoGrad.add_color_stop_rgba(key, *self.gradient[key], alpha)

        return cairoGrad
        # ctx.set_source(cairoGrad)
        # ctx.fill_preserve()

    makeSource = makeGradient

    # # Fills whatever the current path of the given cairo context is with the
    # # gradient specified by this figure.
    # def fillCurrentPath(self, camera, ctx):
    #     raise NotImplementedError

    #     cairoGrad = self.makeGradient(camera, ctx)
    #     ctx.set_source(cairoGrad)
    #     ctx.fill_preserve()

    @morpho.TweenMethod
    @handleGradients(["gradient"])
    def tweenLinear(self, other, t, *args, **kwargs):
        return super().tweenLinear(other, t, *args, **kwargs)

# Base class for QuadGradientFill and QuadGradGroup
class QuadGrad(GradientFill):
    pass

class QuadGradientFill(QuadGrad):
    def __init__(self, vertices=None, colors=None, origin=0):

        super().__init__()

        # Tweenables
        if vertices is None:
            vertices = [0, 1, 1+1j, 1j]
        if colors is None:
            colors = [(1,0,0)]*4
        # Make sure colors is a list of lists, and not other vector type.
        colors = [list(rgb) for rgb in colors]

        vertices = morpho.Tweenable("vertices", vertices, tags=["complex", "list"])
        colors = morpho.Tweenable("colors", colors, tags=["color", "list"])
        origin = morpho.Tweenable("origin", origin, tags=["complex"])

        self.update([vertices, colors, origin])

    def copy(self):
        new = super().copy()

        # Do a deep copy of colors
        new.colors = [list(rgb) for rgb in self.colors]

        return new

    # Generate the cairo MeshPattern this QuadGradientFill describes.
    # Please note this method changes the coordinate system of the
    # inputted cairo context, and you will need to call ctx.restore()
    # at some point to reset it.
    def makeMeshPattern(self, camera, ctx, alpha=1, pushPhysicalCoords=True):
        if pushPhysicalCoords:
            morpho.pushPhysicalCoords(camera.view, ctx)  # Implicit ctx.save()

        pat = cairo.MeshPattern()
        # pat.begin_patch()
        # z0 = self.vertices[0]
        # x0,y0 = z0.real, z0.imag
        # pat.move_to(x0, y0)
        # for n in range(1,4):
        #     z = self.vertices[n] + self.origin
        #     pat.line_to(z.real, z.imag)
        # for n in range(0,4):
        #     color = self.colors[n]
        #     # Append alpha = 1 if color is RGB instead of RGBA
        #     if len(color) < 4:
        #         pat.set_corner_color_rgba(n, *color, alpha)
        #     else:
        #         pat.set_corner_color_rgba(n, *color[:3], alpha*color[3])
        # pat.end_patch()
        self.makePatch(pat, alpha)

        return pat

    # Alias for makeMeshPattern(). Please remember calling this
    # method implicitly calls ctx.save() so you will need to call
    # ctx.restore() later.
    makeSource = makeMeshPattern

    def makePatch(self, meshPattern, alpha=1):
        pat = meshPattern
        pat.begin_patch()
        z0 = self.vertices[0] + self.origin
        x0,y0 = z0.real, z0.imag
        pat.move_to(x0, y0)
        for n in range(1,4):
            z = self.vertices[n] + self.origin
            pat.line_to(z.real, z.imag)
        for n in range(0,4):
            color = self.colors[n]
            # Append alpha = 1 if color is RGB instead of RGBA
            if len(color) < 4:
                pat.set_corner_color_rgba(n, *color, alpha)
            else:
                pat.set_corner_color_rgba(n, *color[:3], alpha*color[3])
        pat.end_patch()


class QuadGradGroup(QuadGrad):
    def __init__(self, quadgrads=None):

        super().__init__()

        if quadgrads is None:
            quadgrads = []

        quadgrads = morpho.Tweenable("quadgrads", quadgrads, tags=["quadgradientfill", "list"])

        self.update([quadgrads])

    def copy(self):
        new = super().copy()

        # Do a deep copy of quadgrads list
        new.quadgrads = [quadgrad.copy() for quadgrad in self.quadgrads]

        return new

    # Generate the cairo MeshPattern this QuadGradientFill describes.
    # Please note this method changes the coordinate system of the
    # inputted cairo context, and you will need to call ctx.restore()
    # at some point to reset it.
    def makeMeshPattern(self, camera, ctx, alpha=1, pushPhysicalCoords=True):
        if pushPhysicalCoords:
            morpho.pushPhysicalCoords(camera.view, ctx)  # Implicit ctx.save()

        pat = cairo.MeshPattern()
        for quadgrad in self.quadgrads:
            quadgrad.makePatch(pat, alpha)

        return pat

    makeSource = makeMeshPattern

    ### TWEEN METHODS ###

    @morpho.TweenMethod
    def tweenLinear(self, other, t):
        # # Defaults to the empty tuple.
        # if ignore is None:
        #     ignore = ()
        # # Convert string to tuple containing string
        # elif isinstance(ignore, str):
        #     ignore = (ignore,)

        # if "quadgrads" in ignore:
        #     return self.copy()

        # Initialize tweened object to a generic QuadGradGroup
        tw = type(self)()

        # Cycle thru all quadgrads in both self and other
        # (assuming they both have the same number)
        # and tween each one in self with the corresponding one in other.
        quadgrads = []
        for n in range(len(self.quadgrads)):
            a = self.quadgrads[n]
            b = other.quadgrads[n]
            quadgrads.append(a.defaultTween(a,b,t))

        tw.quadgrads = quadgrads
        return tw

    # Pivot tween is not supported for this figure
    def tweenPivot(self, other, t):
        raise NotImplementedError

# Decorator modifies tween methods to support
# gradient fills for the specified tweenables.
#
# Example usage:
# @morpho.TweenMethod
# @handleGradientFills(["color", "fill", "alpha"])
# def tweenLinear(self, other, t):
#     etc.
def handleGradientFills(gradFillTweenableNames):
    def decorator(twMethod):
        def wrapper(self, other, t, *args, **kwargs):
            # Use the original tween method as normal.
            # The given tween method should be designed to ignore
            # the tweenables that may contain gradients.
            tw = twMethod(self, other, t, *args, **kwargs)

            for name in gradFillTweenableNames:
                # If both are gradient fills...
                if isinstance(self._state[name].value, GradientFill) and isinstance(other._state[name].value, GradientFill):
                    # tw.color = self.color.tweenLinear(other.color, t)
                    tw._state[name].value = self._state[name].value.tweenLinear(other._state[name].value, t)
                # self is gradient fill but not other
                elif isinstance(self._state[name].value, GradientFill):
                    othercopy_state_name = self._state[name].value.copy()  # Copy of self's GradientFill figure
                    # Iterate over each keynode of the GradientFill's internal Gradient
                    # and set them to be the constant value of other.
                    for key in othercopy_state_name.gradient.data:
                        value = other._state[name].value
                        othercopy_state_name.gradient[key] = value.copy() if "copy" in dir(value) else value
                    # Apply tween method of the GradientFill class.
                    tw._state[name].value = self._state[name].value.tweenLinear(othercopy_state_name, t)
                # other is gradient fill but not self
                elif isinstance(other._state[name].value, GradientFill):
                    selfcopy_state_name = other._state[name].value.copy()  # Copy of other's GradientFill figure
                    # Iterate over each keynode of the GradientFill's internal Gradient
                    # and set them to be the constant value of other.
                    for key in selfcopy_state_name.gradient.data:
                        value = self._state[name].value
                        selfcopy_state_name.gradient[key] = value.copy() if "copy" in dir(value) else value
                    tw._state[name].value = selfcopy_state_name.tweenLinear(other._state[name].value, t)
                # neither are gradients
                else:
                    value = self._state[name].value
                    if isinstance(value, list) or isinstance(value, tuple):
                        tw._state[name].value = type(value)(map(morpho.numTween, self._state[name].value, other._state[name].value, (t,)*len(value)))
                    elif isinstance(value, np.ndarray):
                        tw._state[name].value = morpho.numTween1(self._state[name].value, other._state[name].value, t)
                    elif isinstance(value, QuadGradientFill):
                        tw._state[name].value = self._state[name].value.tweenLinear(other._state[name].value, t)
                    else:
                        tw._state[name].value = morpho.numTween(self._state[name].value, other._state[name].value, t)

            return tw
        return wrapper
    return decorator

### SPECIAL PARTICULAR GRADIENTS ###

rainbow = lambda: Gradient({
    0:   [1,0,0],
    1/6: [1,1,0],
    2/6: [0,1,0],
    3/6: [0,1,1],
    4/6: [0,0,1],
    5/6: [1,0,1],
    1:   [1,0,0]
})

heatmap = Gradient({
    0: [0,0,1],
    1/4: [0,1,1],
    1/2: [0,1,0],
    3/4: [1,1,0],
    1: [1,0,0]
    })
