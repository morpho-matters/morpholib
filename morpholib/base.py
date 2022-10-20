'''
This is the base module of the morpho library.
All the classes, functions, constants, etc. in this file
are imported into the "morpholib" namespace when the command
import morpholib
is called.

To avoid name conflicts, please avoid using names in the
outermost scope that could be names of subpackages.
This can be done by avoiding names that are nothing but
lowercase letters since convention has it that package
names are all lowercase letters.
'''

from morpholib.tools.basics import tau, argShift, argShiftArray, arcCenter, arcCenterArray
import math
import numpy as np
import cairo
cr = cairo
# from warnings import filterwarnings

# Ignore warnings by default.
# This is mainly for the sake of the Spline class, which
# uses some non-standard arithmetic intentionally.
# filterwarnings("ignore")


version = "0.6.0"  # Current public morpho version
internalVersion = "2.3.2ip"  # Current internal morpho version
subversion = ""
DEBUG_MODE = False


### CLASSES ###


# This class serves the purpose of a "tweenable" attribute.
# Its objects tell a figure subclass that this object's value
# is supposed to respond to tween methods.
# A collection of tweenables with particular values forms a "state"
# which is meant to represent the configuration of a figure
# at any given moment.
# Examples of tweenables include position, size, color, angle,
# x, y, z, etc.
# Although these are typical, you can make them however you want.
#
# Tweenables have four attributes: name, value, tags, and metadata.
# name is just the name you give to the tweenable. It should be something
#     descriptive like "position" or "width". By default, a figure will
#     create attrs whose names are the tweenables' names and whose attr
#     values are the tweenables themselves. This is done for user
#     convenience. More on this in the Figure class comments.
#     Because of this, a tweenable's name should not contain spaces or
#     special characters. Basically, treat a tweenable's name like you
#     would a Python variable's name.
#
# tags is a set of strings that records the KIND of parameter the
#     tweenable is supposed to be. For example: "size", "vector",
#     "magitude", "position", etc.
#     This is optional. If you leave it blank, it will default to the
#     empty set, but the idea is listing certain tags will tell
#     generic tween methods (such as tweenLinear) what to do with this
#     tweenable regardless of its name. Tags are basically a way to group
#     tweenables together so that general-purpose tween methods can act on
#     them without the user having to individually recreate a tailored
#     version of the tween method for each tweenable or figure they make.
#     More info on the values you may want to assign to tags can be
#     found in the comments on the generic tween methods
#     (such as tweenLinear).
#
# value is the actual data value of the tweenable which gets tweened
#     by a tween method. It is typically a float or an int, but could
#     conceivably be any data type you want as long as you have a tween
#     method that can deal with it.
#
# metadata is an optional attribute where you can put a string.
#     It has no strict usage in mind, but the idea is if you needed
#     to keep track of a tweenable without using its name, the metadata
#     is a more hidden attribute whereby you could do so (hidden in the
#     sense that figures won't name attributes after it!)
class Tweenable(object):
    def __init__(self, name, value=0.0, tags=None, metadata=""):
        # # Default parameters
        # if "name" not in kwargs: kwargs["name"] = "tweenable"
        # if "category" not in kwargs: kwargs["category"] = "none"
        # if "value" not in kwargs: kwargs["value"] = 0.0
        # if "tag" not in kwargs: kwargs["tag"] = ""

        # self.name = kwargs["name"]
        # self.category = kwargs["category"]
        # self.value = kwargs["value"]
        # self.tag = kwargs["tag"]

        # Convert tags to proper format.
        if tags is None:
            tags = set()
        # elif type(tags) is set:
        elif isinstance(tags, set):
            # tags = tags.copy()
            pass
        # elif type(tags) is str:
        elif isinstance(tags, str):
            tags = {tags,}
        # elif type(tags) in (list, tuple):
        elif isinstance(tags, list) or isinstance(tags, tuple):
            tags = set(tags)
        else:
            raise TypeError("Given tags attribute is not a valid type of set, None, str, list, or tuple.")

        self.name = name
        self.tags = tags
        self.value = value
        self.metadata = metadata

        # FUTURE: Tweenables can be linked to another figure within
        # the same frame as the figure the tweenable is a part of.
        # The basic idea is the tweenable mimics whatever its master
        # figure does when tweened, but "mimic" can be defined as
        # whatever you want via some kind of "link method" maybe.
        # self.master = None

    # Return a deep-ish copy of the tweenable.
    # To ensure depth, copy() tries to make a copy
    # of the given tweenable's value attribute by calling the method
    # self.value.copy() if such a method exists. If for some reason
    # this can't be done, the copied tweenable's value attribute
    # will just assign to the original's value.
    # i.e. twCopy.value = self.value
    # copy() will also make a copy of the tags set, but
    # it doesn't attempt to copy any of the other
    # attributes of the tweenable such as name, or metadata
    # as it assumes these are strings and hence immutable.
    def copy(self):
        twCopy = Tweenable(
            name=self.name,
            tags=self.tags.copy(),
            value=self.value,
            metadata=self.metadata)

        try:
            twCopy.value = self.value.copy()
        except Exception:  # Upon failure, just reassign and hope for the best.
            # Actually, I think I DO want this line. It looks redundant,
            # but if the try clause somehow messed up the assignment
            # process itself, I'd like to reassign the initial value.
            twCopy.value = self.value

        return twCopy

    def __repr__(self):
        return "<"+self.name+": " + repr(self.value) + ">"

    def __str__(self):
        return repr(self)


### INTERPOLATION HELPER FUNCTIONS ###

# Helper function: Numeric tween function.
# Takes two numbers and tweens them
# linearly by the parameter t in [start, end]
# start and end default to 0 and 1.
def numTween(a, b, t, start=0, end=1):
    # Special case for speed because it's common.
    if a == b: return a

    # This is the usual case. I'm putting it in explicitly
    # because the formula is simpler and thus may make the main
    # use case of numTween() run faster.
    if start == 0 and end == 1:
        # return (b-a)*t + a

        # This is more numerically stable than the other version, I think.
        # In any case, it handles interpolating infinite values better.
        return b*t + (1-t)*a
    else:
        t = (t-start)/(end-start)
        # return (b-a)/(end-start) * (t-start) + a
        return b*t + (1-t)*a

lerp = numTween

# Functionally identical to numTween() except it doesn't check
# if a == b at the beginning. This enables this version of the
# function to handle types like numpy arrays.
def numTween1(a, b, t, start=0, end=1):
    # This is the usual case. I'm putting it in explicitly
    # because the formula is simpler and thus may make the main
    # use case of numTween() run faster.
    if start == 0 and end == 1:
        # return (b-a)*t + a
        return b*t + (1-t)*a
    else:
        t = (t-start)/(end-start)
        # return (b-a)/(end-start) * (t-start) + a
        return b*t + (1-t)*a

lerp1 = numTween1

# Functionally identical to numTween(), but does no conditional
# checks to improve performance. It's just an alias for the raw
# linear interpolation formula.
def numTween0(a, b, t, start=0, end=1):
    t = (t-start)/(end-start)
    return b*t + (1-t)*a
    # return (b-a)/(end-start) * (t-start) + a

lerp0 = numTween0

# Does a numerical tween, but always returns integer values.
def intTween(a, b, t, start=0, end=1):
    return round(numTween(a, b, t, start, end))

def spiralInterp(p,q,t, start=0, end=1):
    t = (t-start)/(end-start)  # Normalize

    r1 = abs(p)
    r2 = abs(q)

    th1 = cmath.phase(p) % tau
    th2 = cmath.phase(q) % tau
    dth = argShift(th1, th2)

    dr = r2 - r1

    r = numTween(r1, r2, t)
    th = th1 + t*dth

    tw = r*cmath.exp(th*1j)

    return tw

def spiralInterpArray(p,q,t, start=0, end=1):

    r1 = np.abs(p)
    r2 = np.abs(q)

    th1 = np.angle(p) % tau
    th2 = np.angle(q) % tau
    dth = argShiftArray(th1, th2)

    dr = r2 - r1

    r = numTween1(r1, r2, t)
    th = th1 + t*dth

    tw = r*np.exp(th*1j)

    return tw

def pivotInterpArray(p,q,t, angle=tau/2, start=0, end=1):
    if not(start == 0 and end == 1):
        t = (t-start)/(end-start)  # Normalize

    c = arcCenterArray(p,q, angle)
    tw = (p-c)*np.exp(t*angle*1j) + c

    return tw


# Cubic Bezier interpolation.
# p0, p3 are starting and ending positions,
# p1, p2 are control point handles for p0 and p3 respectively.
# t is the parameter value.
# "start" and "end" specify what t-value corresponds to p0 and p1.
# Default: start=0, end=1
def bezierInterp(p0, p1, p2, p3, t, start=0, end=1):
    t = (t-start)/(end-start)  # Normalize

    # Compute polynomial values
    t2 = t*t
    t3 = t2*t
    s = 1-t
    s2 = s*s
    s3 = s2*s

    return s3*p0 + (3*s2*t)*p1 + (3*s*t2)*p2 + t3*p3



### BASIC TWEEN METHODS ###

'''
A tween method is, literally, a tween method: it is a function intended to be
a method of a figure which gives a way for that figure to tween its state.
Structurally, a tween method is a function that takes 3 required inputs:
self    = the current figure object
other   = the figure to tween to
t       = Tween time. A parameter between 0 and 1.

and is meant to be called as a method:
my_figure.tween(my_other_figure, 0.5)
'''

# Tween method decorator.
# Prepended before any tween method's definition as so:
# @tweenMethod
# def my_tween_method(self, other, t)
#
# The decorator performs some sanity checks to make sure tweening
# is possible. e.g. checks the start and end figures are of the same class.
# It also automatically enforces the rule
# that t=0 returns self.copy() and t=1 returns other.copy()
def tweenMethod(tween):
    def wrapper(self, other, t, *args, **kwargs):
        if type(self) is not type(other):
            raise TypeError("Tried to tween figures of different class!")

        # Enforce self and other if t==0 or 1.
        if t == 0:
            return self.copy()
        elif t == 1:
            return other.copy()
        else:
            # t = self.transition(t)  # Compute new time based on transition.
            twfig = tween(self, other, t, *args, **kwargs)
            twfig.visible = self.visible  # Inherits visibility of self
            return twfig
    return wrapper

TweenMethod = tweenMethod  # Initial letter can optionally be uppercase.

# Converts complex coordinates into screen pixel coordinates
# according to the screen dimensions and the shape of the cairo
# context target surface.
# Instead of supplying a cairo context, ctx can optionally be a list/tuple
# indicating the window dimensions in pixels (width, height)
def screenCoords(z, view, ctx):
    a,b,c,d = view

    if isinstance(ctx, tuple) or isinstance(ctx, list):
        width, height = ctx
    else:
        surface = ctx.get_target()
        width = surface.get_width()
        height = surface.get_height()

    x = width/(b-a) * (z.real - a)
    y = height/(d-c) * (z.imag - c)

    return x,y

# Alternate name for screenCoords()
pixelCoords = screenCoords


# Calls ctx.save() and then creates a context manager object for the
# given ctx object that can be used in a `with` statement like this:
#   with SavePoint(ctx):
#       ...
# and ctx.restore() will be called at the end of the block
class SavePoint(object):
    def __init__(self, ctx):
        self.ctx = ctx
        # print("ctx saved!")
        self.ctx.save()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.ctx.restore()
        # print("ctx restored!")

# pushPhysicalCoords(view, ctx)
#
# Starting from a cairo coordinate system in screen coordinates
# (which is default after calling setupContext()), changes the cairo
# coordinate system temporarily into physical coordinates based
# on the viewbox you provide.
#
# Please note that this function implicitly calls ctx.save() so that
# you can later revert back to the original pixel coordinate system that
# Morpho normally expects, by calling ctx.restore(). Please remember to actually
# call ctx.restore() YOURSELF at some point after you're done using the
# effects of pushPhysicalCoords()! Forgetting to will undoubtedly lead to all
# kinds of trouble!
#
# To automatically handle calling ctx.restore(), you can call this
# function as part of a `with` statement:
#   with morpho.pushPhysicalCoords(view, ctx):
#       ...
# At the end of the block, ctx.restore() will be called automatically.
#
# To use it correctly, you should call this function BEFORE any
# calls that modify the context's CTM as part of drawing your given figure.
# The idea is that you apply all of your CTM modifications pretending the
# context is actually working under physical coords (even though it's not),
# but then including pushPhysicalCoords() at the top (meaning it's applied last)
# to perform a final transformation that converts your finished coordinates
# into actual pixel coordinates. In a nutshell, pushPhysicalCoords() applies
# a transformation which has the effect of converting physical coords to pixel
# coords. Therefore it should be the last transformation applied in your chain.
def pushPhysicalCoords(view, ctx):
    a,b,c,d = view

    surface = ctx.get_target()
    WIDTH = surface.get_width()
    HEIGHT = surface.get_height()

    savept = SavePoint(ctx)
    ctx.scale(WIDTH/(b-a), HEIGHT/(d-c))
    ctx.translate(-a, -c)

    return savept

def pushPhysicalCoords_old(view, ctx):
    a,b,c,d = view

    surface = ctx.get_target()
    WIDTH = surface.get_width()
    HEIGHT = surface.get_height()

    ctx.save()
    ctx.scale(WIDTH/(b-a), HEIGHT/(d-c))
    ctx.translate(-a, -c)


# Inverse of screenCoords(). Given screen coordinates,
# returns the corresponding physical coordinates.
# Instead of supplying a cairo context, ctx can optionally be a list/tuple
# indicating the window dimensions in pixels (width x height)
def physicalCoords(X, Y, view, ctx):
    a,b,c,d = view

    if isinstance(ctx, tuple) or isinstance(ctx, list):
        width, height = ctx
    else:
        surface = ctx.get_target()
        width = surface.get_width()
        height = surface.get_height()

    x = numTween(a, b, X, 0, width)
    y = numTween(c, d, Y, 0, height)

    return x + y*1j

# Given physical width, returns number of pixels it would take on screen
# NOTE: output can be non-integer.
# Instead of supplying a cairo context, ctx can optionally be a list/tuple
# indicating the window dimensions in pixels (width x height)
def pixelWidth(w, view, ctx):
    if isinstance(ctx, tuple) or isinstance(ctx, list):
        width = ctx[0]
    else:
        width = ctx.get_target().get_width()
    return w/(view[1]-view[0])*width

# Given pixel width, returns physical width (i.e. width in the complex plane).
# Instead of supplying a cairo context, ctx can optionally be a list/tuple
# indicating the window dimensions in pixels (width x height)
def physicalWidth(W, view, ctx):
    if isinstance(ctx, tuple) or isinstance(ctx, list):
        width = ctx[0]
    else:
        width = ctx.get_target().get_width()
    return W/width * (view[1] - view[0])

# Similar to pixelWidth()
# Instead of supplying a cairo context, ctx can optionally be a list/tuple
# indicating the window dimensions in pixels (width x height)
def pixelHeight(h, view, ctx):
    if isinstance(ctx, tuple) or isinstance(ctx, list):
        height = ctx[1]
    else:
        height = ctx.get_target().get_height()
    return h/(view[3]-view[2])*height

# Similar to physicalWidth()
# Instead of supplying a cairo context, ctx can optionally be a list/tuple
# indicating the window dimensions in pixels (width x height)
def physicalHeight(H, view, ctx):
    if isinstance(ctx, tuple) or isinstance(ctx, list):
        height = ctx[1]
    else:
        height = ctx.get_target().get_height()
    return H/height * (view[3] - view[2])

# Computes a factor indicating how horizontally stretched the screen is
# compared to the viewbox. This ratio is 1 if screen shape and viewbox have
# proportional dimensions.
# Example: Given a square viewbox, but a 400x200 screen, this ratio will be 2.
def pixelAspectRatioWH(view, ctx):
    # # Extract viewbox from camera figure if given camera figure.
    # if isinstance(view, morpho.anim.Camera):
    #     view = view.view

    # Calculate width and height of the viewbox
    a,b,c,d = view
    width = b-a
    height = d-c

    # Extract screen width and height
    if isinstance(ctx, tuple) or isinstance(ctx, list):
        WIDTH, HEIGHT = ctx
    else:
        surface = ctx.get_target()
        WIDTH = surface.get_width()
        HEIGHT = surface.get_height()

    return (WIDTH*height) / (width*HEIGHT)

I2 = np.eye(2)

# Returns the special transformation matrix that compensates
# for rotations and transformations in a non-square view.
#
# INPUTS
# par = Pixel aspect ratio as computed by
#       morpho.pixelAspectRatioWH()
# rotation = Rotation in radians. Default: 0.
# transform = Local transformation matrix. Default: I2
# inverse (keyword-only) = Boolean indicating whether the
#           inverse transformation should be returned.
#           Default: False
#
# More precisely, if S represents the matrix that locally
# transforms pixel coords to physical coords
# according to the par, this function returns
# S @ T @ R @ S.inv
# where R and T are the rotation and transform matrices.
def parconj(par, rotation=0, transform=I2, *, inverse=False):
    # Construct 2D rotation matrix
    if rotation == 0:
        R = I2
    else:
        c = math.cos(rotation)
        s = math.sin(rotation)
        R = np.array([[c, -s],[s, c]], dtype=float)

    # S represents the linear transformation that converts
    # pixel coordinates to physical coordinates.
    # Since S is diagonal, conjugating with it is easy, just
    # multiply element-wise by parmat:
    # S.M.S^-1 = parmat*M
    parmat = np.array([[1, 1/par],[par, 1]], dtype=float)
    if inverse:
        if np.array_equal(transform, I2):
            return parmat*R.T
        else:
            return parmat*np.linalg.inv(transform @ R)
    else:
        return parmat*(transform @ R)

# Apply the values of the given transformation parameters to the
# given cairo context. Generally should be used AFTER
# pushPhysicalCoords() is called.
def applyTransforms(ctx, origin=0, rotation=0, transform=I2):
    # Handle possible other transformations
    if origin != 0:
        ctx.translate(origin.real, origin.imag)
    if not np.array_equal(transform, I2):
        xx, xy, yx, yy = transform.flatten().tolist()
        # Order is MATLAB-style: top-down, then left-right. So the matrix
        # specified below is:
        # [[xx  xy]
        #  [yx  yy]]
        mat = cairo.Matrix(xx, yx, xy, yy)
        # Apply to context
        ctx.transform(mat)
    if (rotation % tau) != 0:
        ctx.rotate(rotation)


### INTERNAL SPARE CAIRO CONTEXT ###

# Dictionary mapping the names of line join styles
# to the corresponding cairo data value.
cairoJointStyle = {
    "miter" : cairo.LINE_JOIN_MITER,
    "bevel" : cairo.LINE_JOIN_BEVEL,
    "round" : cairo.LINE_JOIN_ROUND
}

# Clears the given context and fills it with the background color
def clearContext(context, background, alpha):
    # This extra stuff is to ensure that we can actually paint WITH
    # transparency.
    context.save()
    context.set_source_rgba(*background, alpha)
    context.set_operator(cr.OPERATOR_SOURCE)
    context.paint()
    context.restore()

# Sets up an isolated, basic cairo context and returns it.
def setupContext(width, height, background=(0,0,0), alpha=0,
    flip=True, antialiasText=True, jointStyle="round"):

    surface = cr.ImageSurface(cr.FORMAT_ARGB32, width, height)

    # Setup cairo context
    context = cr.Context(surface)
    # Setup text antialiasing
    if antialiasText:
        fontops = context.get_font_options()
        fontops.set_antialias(cr.Antialias.GOOD)
        context.set_font_options(fontops)
    # Put origin in lower-left
    if flip:
        context.translate(0, height)
        context.scale(1, -1)
    # Setup line join style
    context.set_line_join(cairoJointStyle[jointStyle])
    # Paint background
    clearContext(context, background, alpha)
    return context

spareContext1 = None
spareContext2 = None

# Setup the spare cairo contexts.
# The idea is these cairo contexts can be used by certain draw()
# methods as intermediate drawing
# contexts to aid in creating certain effects.
# THIS FUNCTION HAS NOT BEEN TESTED! I DO NOT CONSIDER
# SPARE CONTEXTS OFFICIALLY IMPLEMENTED YET!!
def setupSpareContexts(ctx):
    raise NotImplementedError

    global spareContext1
    global spareContext2

    # Extract surface's width and height
    surface = ctx.get_target()
    width = surface.get_width()
    height = surface.get_height()

    if spareContext1 is None:
        # Create new context if no current spareContext exists
        spareContext1 = setupContext(width, height, flip=False)
    else:
        # Replace existing spareContext if there is a dimension
        # mismatch
        surf1 = spareContext.get_target()
        width1 = surf1.get_width()
        height1 = surf1.get_height()
        if (width, height) != (width1, height1):
            spareContext1 = setupContext(width, height, flip=False)
    if spareContext2 is None:
        spareContext2 = setupContext(width, height, flip=False)
    else:
        # Setup new contexts if dimensions are mismatched
        surf2 = spareContext2.get_target()
        width2 = surf2.get_width()
        height2 = surf2.get_height()
        if (width, height) != (width2, height2):
            spareContext2 = setupContext(width, height, flip=False)

    # Clear the spareContext
    clearContext(spareContext1, background=(0,0,0), alpha=0)
    clearContext(spareContext2, background=(0,0,0), alpha=0)
