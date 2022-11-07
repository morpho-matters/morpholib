import morpholib as morpho
import math, sys

# Module has alternative name "transition" (singular)
self = sys.modules[__name__]
morpho.transition = self

# # Returns a transition which is the composition of f and g (f o g)
# def compose(f, g):
#     return lambda t: f(g(t))

# BUILT-IN TRANSITIONS

# Easing transition based on the arctangent function.
# Eases in and out of keyframes.
# This was the very first easing transition I implemented,
# but I now almost always use quadease instead, as I think
# it looks better and is probably faster to compute.
# Qualitatively, the main difference between atanease and
# quadease is that atanease is slower at the start and end,
# and faster in the middle compared to quadease.
def atanease(t):
    return (math.atan(14*t-7) + 1.4289)/2.8578
# atanease = lambda t: (math.atan(14*t-7) + 1.4289)/2.8578
slow_fast_slow = atanease  # Alternate name

# Interpolates like how a ball is dropped.
# Slow at first, fast at end.
def drop(t):
    return t**2
# drop = lambda t: t**2

# Interpolates like how a ball is tossed upward.
# Fast at first, slow at end.
def toss(t):
    return 1 - (t-1)**2
# toss = lambda t: 1 - (t-1)**2

# Quadratic Easing transition.
# Slow at the start and end, and faster in the middle,
# according to a quadratic curve.
# This is the primary transition function I use to make
# interpolations that ease in and out of keyframes.
# It is a piecewise combination of the drop and toss
# transitions.
def quadease(t):
    return drop(2*t)/2 if t < 0.5 else (1+toss(2*t-1))/2
droptoss = quadease  # Alternate name. Drop then a toss.
# quadease = lambda t: drop(2*t)/2 if t < 0.5 else (1+toss(2*t-1))/2


# Glide transition maker.
# Returns a glide transition based on the inflection points
# provided.
# A glide transition is where an animation accelerates in,
# moves at a constant speed for a while, then decelerates out.
# The points at which one behavior switches to the next are
# called inflection points.
# The acceleration and deceleration follow a quadratic
# trajectory.
#
# INPUTS (positional only)
# a = First inflection: a number in the range [0,1].
#     For example: a = 0.25 means acceleration phase will
#     last until 25% of the transition is completed.
# b = Second inflection. If unspecified, defaults to 1-a
#     to make a symmetric glide. Must satisfy a <= b.
#
# Example usage:
#   myfig.transition = morpho.transition.glide(0.2)
#   myfig2.transition = morpho.transition.glide(0.1, 0.75)
#
# If a = b = 0, the transition will be identical to toss.
# If a = b = 0.5, the transition will be identical to quadease.
# If a = b = 1, the transition will be identical to drop.
def glide(a, b=None, /):
    if b is None:
        b = 1-a
    if not(0 <= a <= b <= 1):
        raise ValueError("Invalid inflection value. Must have 0 <= a <= b <= 1")

    m = 2/(b-a+1)
    def glideTransition(t):
        if t < a:
            return m*t**2/(2*a)
        elif t <= b:
            return m*(t-a/2)
        else:
            return 0.5*m*(b-a+1 - (t-1)**2/(1-b))
    return glideTransition


halfpi = math.pi/2
# sinetoss = lambda t: math.sin(halfpi*t)
# sinedrop = lambda t: 1 - math.cos(halfpi*t)
# sineease = sinease = lambda t: (1-math.cos(math.pi*t))/2

# Trig versions of toss/drop and ease.
# The movement is sinusoidal instead of quadratic.

# Trig version of toss() where the curve is sinusoidal
# instead of quadratic.
def sinetoss(t):
    return math.sin(halfpi*t)

# Trig version of drop() where the curve is sinusoidal
# instead of quadratic.
def sinedrop(t):
    return 1 - math.cos(halfpi*t)

# Trig version of quadease() where the curve is sinusoidal
# instead of quadratic.
def sineease(t):
    return (1-math.cos(math.pi*t))/2
sinease = sineease

# No special transition. Just transition uniformly at a constant
# speed to the next keyframe.
def uniform(t):
    return t
# uniform = lambda t: t

# DEPRECATED! Set `static=True` instead!
# Instant transition. Makes the figure jump instantly from
# initial to final keyfigure where t = 1 maps to the final
# keyfigure, and all 0 <= t < 1 map to the initial keyfigure.
def instant(t):
    raise NotImplementedError("instant() transition is deprecated. Use `static=True` or `tweenInstant()` instead.")
    return int(t)
step = jump = instant  # Alternate name
# instant = lambda t: int(t)

# Set default transition to uniform. This can be modified anywhere
# in the code by calling
# morpho.transitions.default = newtransition
default = uniform

# Splits a strictly increasing transition function that maps
# [0,1] onto [0,1] into two transition functions that are
# normalized to work as regular transition functions.
def split(func, t):
    if not(0 < t < 1):
        raise ValueError("t must be strictly between 0 and 1.")

    y = func(t)

    def func1(s):
        return func(morpho.lerp0(0,t, s))/y

    def func2(s):
        return (func(morpho.lerp0(t,1, s))-y)/(1-y)

    return func1, func2
