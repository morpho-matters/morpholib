---
layout: default
title: Morpho Guide -- Modifiers
---

# Morpho Guide: Modifiers

> **Note:** Modifiers were introduced in Morpho 0.8.1, with other features added thereafter. To make the best use of this guide, make sure you have v0.8.1 or higher.

To run the example code snippets in this guide, make sure to include the following lines at the top of your script:
```python
import morpholib as morpho
morpho.importAll()
from morpholib.tools.basics import *
```

## Intro

Modifiers provide a way to control an actor's state with another actor or actors, essentially allowing you to link actors' behavior together, which allows for some sophisticated effects like having an actor precisely mimic another actor's movement, color, transparency, etc. This applies to the camera actor as well, so you can have effects where the camera reacts dynamically to another actor, e.g. perhaps by keeping the camera centered on it. And by tying multiple actors to a single master actor, you can choreograph some complex animations involving several actors in a fairly straightforward way. So how does this work?

## What Is a Modifier?

At its most basic, a modifier is just a Python function that takes a figure as input and modifies the figure in some way. That's it. When assigned to the `modifier` attribute of a keyfigure in an actor, the modifier will be called before the keyfigure (and its tweened figures) are drawn during animation playback. To see how it works, let's do a really silly basic example where we use a modifier to modify a Point actor's position. We'll start with a simple animation, without using modifiers, where a Point moves left-to-right across the screen while changing its color:
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)

mypoint = mainlayer.Actor(morpho.grid.Point(-3))
# Move point and change its color to green.
mypoint.newendkey(30).set(pos=3, fill=[0,1,0])

mation.play()
```
Now let's define a modifier for this Point actor that modifies its position to `3+3j`
```python
def modifyPoint(self):
    self.pos = 3+3j
```
(The convention is to name the figure-to-be-modified in a modifier function `self` in line with the convention for Python methods.)

We now assign it to the `modifier` attribute of the first keyfigure of the `mypoint` actor so that the modifier will propagate to all future keyfigures, as well as intermediate tweened figures:
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)

def modifyPoint(self):
    self.pos = 3+3j
mypoint = mainlayer.Actor(morpho.grid.Point(-3).set(
    modifier=modifyPoint
    ))
# Move point and change its color to green.
mypoint.newendkey(30).set(pos=3, fill=[0,1,0])

mation.play()
```
Running the code now, you'll see it stays constantly fixed at position `3+3j` while its color still changes. The modifier is modifying the `pos` attribute to `3+3j` for each individual Point figure produced by the `mypoint` actor thruout the animation playback.

An important thing to note about modifiers is they apply *only at playback-time* and even then do not actually modify the underlying keyfigures of an actor. The modification is all done internally at playback-time to the figures produced by the actor before they are actually drawn. This means that if, outside of playback-time, you manually sample the `pos` attribute of `mypoint` at any point in its timeline, you'll find it to be exactly the same as if the modifier were not there:
```python
def modifyPoint(self):
    self.pos = 3+3j
mypoint = mainlayer.Actor(morpho.grid.Point(-3).set(
    modifier=modifyPoint
    ))
# Move point and change its color to green.
mypoint.newendkey(30).set(pos=3, fill=[0,1,0])

print(mypoint.time(15).pos)  # Still outputs 0
```
This is true even if you sample the `pos` attribute *after* playing the animation:
```python
def modifyPoint(self):
    self.pos = 3+3j
mypoint = mainlayer.Actor(morpho.grid.Point(-3).set(
    modifier=modifyPoint
    ))
# Move point and change its color to green.
mypoint.newendkey(30).set(pos=3, fill=[0,1,0])

mation.play()

print(mypoint.time(15).pos)  # STILL outputs 0
```
So keep in mind that modifiers are a *post-processing* effect: in general, you cannot reference a modifier's effects before animation playback. If you REALLY need to reference a modifier's effect as part of constructing an animation before playback, there *is* actually a way to do it, but that's a story for later in this guide.

So that's the basic way modifiers work, but the above example does nothing to show why they'd be useful. After all, it just sets one attribute of a Point to a constant value. There are much simpler ways to accomplish that! The real utility of modifiers comes in when we set an attribute based on the current state of *another* actor. Let's see how that works now.

## Puppeting

To start, we'll define an Arrow actor and have it move, and spin around a bit:
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)

arrow = mainlayer.Actor(morpho.grid.Arrow(0, 3))
arrow.newendkey(30).origin = -2-2j
arrow.newendkey(60).rotation = 2*pi

mation.play()
```
We'll now define a Point actor and create a modifier for it that positions it at the center of the `arrow` actor at all times. The way this will work is we'll set the point's position to be whatever the centerpoint is of the `arrow` actor *at the current moment*, whatever that is. The way to reference an actor's current state during animation playback is with the `now()` method. By calling `arrow.now()` we get the current state of the `arrow` actor as an `Arrow` figure. We can then access its centerpoint with the `center()` method. Here's what it looks like all put together:
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)

def pointMod(self):
    self.set(pos=arrow.now().center())
point = mainlayer.Actor(morpho.grid.Point().set(
    modifier=pointMod
    ))

arrow = mainlayer.Actor(morpho.grid.Arrow(0, 3))
arrow.newendkey(30).origin = -2-2j
arrow.newendkey(60).rotation = 2*pi

mation.play()
```
> **Note:** Just like with modifiers, the `now()` method only really applies at playback-time. Calling `now()` outside of a modifier (or in any process that can run outside of playback-time) will cause either an error or unexpected behavior.

The `point` actor's position is now completely controlled by the `arrow` actor. When one actor controls part of the behavior of another, I call this *puppeting*: because one actor (the *puppeteer* or *controller*) is "pulling the strings" of another actor (the *puppet*).

However, note that only the `pos` attribute of `point` is currently being overridden by `arrow`: its other attributes are free to be manipulated completely independently---irrespective even of `arrow`'s keyframes:
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)

def pointMod(self):
    self.set(pos=arrow.now().center())
point = mainlayer.Actor(morpho.grid.Point().set(
    modifier=pointMod
    ))

arrow = mainlayer.Actor(morpho.grid.Arrow(0, 3))
arrow.newendkey(30).origin = -2-2j
arrow.newendkey(60).rotation = 2*pi

# Change point's size and fill independently of
# the arrow actor
point.newendkey(60).set(size=30, fill=[0,1,0])
point.newendkey(30).set(size=15, fill=[1,1,0])

mation.play()
```
But even `point`'s `pos` attribute does not have to be *completely* overridden by `arrow`. By slightly changing the modifier, we can have it so `point`'s native `pos` attribute serves to *offset* `point` from the center of `arrow`:
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)

def pointMod(self):
    # Modifier position is now shifted by self.pos
    self.set(pos=self.pos+arrow.now().center())
point = mainlayer.Actor(morpho.grid.Point().set(
    modifier=pointMod
    ))

arrow = mainlayer.Actor(morpho.grid.Arrow(0, 3))
arrow.newendkey(30).origin = -2-2j
arrow.newendkey(60).rotation = 2*pi

# Offset the point's position relative to the
# arrow's center over time.
point.newendkey(45).pos = 2j
point.newendkey(45).pos = 0

mation.play()
```
So modifiers provide a lot of flexibility in how an actor controls another actor.

Lastly, observe that since modifiers usually only modify a figure via its `set()` method, it can be more compact to assign a Python `lambda` expression directly to the `modifier` attribute instead of explicitly naming a modifier function and assigning it later. Here's the same modifier as above implemented using `lambda`:
```python
point = mainlayer.Actor(morpho.grid.Point().set(
    modifier=lambda self: self.set(pos=self.pos+arrow.now().center())
    ))
```
Since this is such a common way for modifiers to be implemented, this guide will use the `lambda` style from now on wherever possible.

## Multiple Controllers

A puppet actor can also be controlled by multiple controller actors in pretty much any way you can imagine. For example, we can have the `point` actor positioned at the *midpoint* between the centers of two Arrow actors, while the point's color is controlled solely by one of the arrows:
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)

arrow = mainlayer.Actor(morpho.grid.Arrow(0, 3))
arrow2 = mainlayer.Actor(morpho.grid.Arrow(0, 3j).set(color=[1,0,0]))
point = mainlayer.Actor(morpho.grid.Point().set(
    modifier=lambda self: self.set(
        # Position at the midpoint between the centers of both arrows
        pos=mean([arrow.now().center(), arrow2.now().center()]),
        fill=arrow2.now().color  # Fill color matches arrow2's color
        )
    ))

# Move first arrow around
arrow.newendkey(30).origin = -2-2j
arrow.newendkey(60).rotation = 2*pi

# Move second arrow around and change its color
arrow2.newendkey(45).set(
    rotation=-135*deg,
    color=[0,1,0]
    )
arrow2.newendkey(45).set(
    origin=3j,
    color=[0,0,1]
    )

mation.play()
```

## Puppet Chaining

Puppet actors can also act as controllers for *other* puppet actors, leading to a sort of chain of actors controlling other actors. For example, take the animation above, and we'll add a text label for the `point` actor that follows it around. To do this, we'll define a `Text` actor and create a modifier for it that references `point.now()`.
```python
arrow = mainlayer.Actor(morpho.grid.Arrow(0, 3))
arrow2 = mainlayer.Actor(morpho.grid.Arrow(0, 3j).set(color=[1,0,0]))
point = mainlayer.Actor(morpho.grid.Point().set(
    modifier=lambda self: self.set(
        # Position at the midpoint between the centers of both arrows
        pos=mean([arrow.now().center(), arrow2.now().center()]),
        fill=arrow2.now().color  # Fill color matches arrow2's color
        )
    ))
label = mainlayer.Actor(morpho.text.Text("Midpoint").set(
    align=[0,-2], size=36,
    modifier=lambda self: self.set(pos=point.now().pos)
    ))
```
> ***CAUTION!*** Puppets can be chained together as far as you like, though be careful to avoid forming loops, where an actor's modifier directly or indirectly references its *OWN* state with `now()`. This will cause either a recursion error or Python to outright crash.

## Hidden Controllers

It can sometimes be useful to have an actor controlled by an invisible actor. This can allow you to decouple part of an actor's behavior from the rest of what it's doing.

### A shaking point

For example, let's say we want to have a point shaking back and forth while moving along a predetermined path. We can get the point to shake about the origin by defining several keyfigures evenly spaced over time at alternating positions:
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)
morpho.transition.default = morpho.transition.quadease

point = mainlayer.Actor(morpho.grid.Point(-0.5))
for n in range(18):
    # Point alternates between +0.5 and -0.5 over the course
    # of 90 frames (3 seconds)
    point.newendkey(5).pos *= -1

mation.play()
```
This is relatively straightforward to pull off, but since we've defined its movement using 19 keyframes, it will now be difficult to have it move smoothly along a path, since that will involve adjusting those 19 keyframes one by one in some sort of clever way to enact the desired motion while preserving the local shaking. In other words, it's hard to *decouple* the point's shaking from any other behavior we might want it to do *while* shaking. But modifiers provide a simple way to do this decoupling!

If we simply want the point to move along a simple linear path while shaking, we can define a hidden *second* Point actor whose position will control the visible point's base position via a modifier. Here's how we might implement that:
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)
morpho.transition.default = morpho.transition.quadease

# Create hidden point actor that will move from -4j to +4j
hiddenPoint = mainlayer.Actor(morpho.grid.Point(-4j))
hiddenPoint.visible = False  # Make the entire actor invisible

point = mainlayer.Actor(morpho.grid.Point(-0.5).set(
    modifier=lambda self: self.set(pos=self.pos+hiddenPoint.now().pos)
    ))
for n in range(18):
    # Point alternates between +0.5 and -0.5 over the course
    # of 90 frames (3 seconds)
    point.newendkey(5).pos *= -1

# Move the hidden point to position 4j
hiddenPoint.newendkey(90).pos = 4j

mation.play()
```
If we instead want the point to move along a more complicated path, we'll need a hidden "clock actor", as I call it.

### Clock actors

A "clock actor" is just an invisible actor whose sole purpose is to hold some kind of varying tweenable quantity which can be referenced by another actor's modifier. I call it a "clock" because often the quantity it holds can be thought of as the current time coordinate of a simulation, but the parameter it holds can represent anything. The simplest way to set one up is to create a generic Skit actor:
```python
clock = mainlayer.Actor(morpho.Skit(t=0))
```
In this case, `clock` is an Actor that only keeps track of one single tweenable attribute, `t`. What's nice about generic Skits is that they are naturally invisible, and so there's no need to manually declare them invisible.

To see how to use the clock, let's first define a path for our shaking point to follow:
```python
path = mainlayer.Actor(morpho.graph.realgraph(lambda x: 0.5*x**2-2, -3, 3))
```
This path will be in the shape of parabola. We can reference any particular position along the path with its `positionAt()` method, which takes a parameter in the range [0,1] where 0 corresponds to the start of the path, and 1 corresponds to its end, with values in between referring to in-between points. This is where our clock actor comes in: We let the `t`-value it holds be this parameter to pass into `positionAt()`. By having the `clock` actor vary its `t`-value from `0` to `1`, we can use a modifier on the `point` actor to have it move along the path over time. I think it'll make more sense if I show you the implementation:
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)
morpho.transition.default = morpho.transition.quadease

# Define clock and path actors
clock = mainlayer.Actor(morpho.Skit(t=0))
path = mainlayer.Actor(morpho.graph.realgraph(lambda x: 0.5*x**2-2, -3, 3))

# Point is positioned along the path at whatever point
# corresponds to the current t-value of the clock.
point = mainlayer.Actor(morpho.grid.Point(-0.5).set(
    modifier=lambda self: self.set(
        pos=self.pos+path.now().positionAt(clock.now().t)
        )
    ))
for n in range(18):
    # Point alternates between +0.5 and -0.5 over the course
    # of 90 frames (3 seconds)
    point.newendkey(5).pos *= -1

# Clock varies from 0 to 1 over the course of 90 frames
clock.newendkey(90).t = 1

mation.play()
```
Even cooler, since we also reference the `path` actor's current state with `now()`, our `point` is actually being controlled by `path`'s shape too, so this animation will work even if we have `path` dynamically change its shape over time:
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)
morpho.transition.default = morpho.transition.quadease

# Define clock and path actors
clock = mainlayer.Actor(morpho.Skit(t=0))
path = mainlayer.Actor(morpho.graph.realgraph(lambda x: 0.5*x**2-2, -3, 3))

# Point is positioned along the path at whatever path point
# corresponds to the current t-value of the clock.
point = mainlayer.Actor(morpho.grid.Point(-0.5).set(
    modifier=lambda self: self.set(
        pos=self.pos+path.now().positionAt(clock.now().t)
        )
    ))
for n in range(18):
    # Point alternates between +0.5 and -0.5 over the course
    # of 90 frames (3 seconds)
    point.newendkey(5).pos *= -1

# Clock varies from 0 to 1 over the course of 90 frames
clock.newendkey(90).t = 1
# Path morphs into a cubic curve over the same duration
path.newendkey(90, morpho.graph.realgraph(lambda x: -(x**3-3*x)/5, -3, 3))

mation.play()
```

## Puppeting the Camera

A layer's camera actor can also be subject to modifiers, allowing it to continuously and dynamically react to other actors' behavior. For example, we can have the camera continuously centered on a moving point. We can do this by having the camera's modifier center the camera at the point's current position:
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)
morpho.transition.default = morpho.transition.quadease

# Start camera zoomed in for a nicer effect
mainlayer.camera.last().zoomIn(2)

grid = mainlayer.Actor(morpho.grid.basicgrid(axes=True))
point = mainlayer.Actor(morpho.grid.Point(0))
mainlayer.camera.last().set(
    # Camera is continuously centered at point's current position
    modifier=lambda self: self.centerAt(point.now().pos)
    )

# Move the point around
point.newendkey(30)
point.newendkey(30).pos = -3+3j
point.newendkey(30)
point.newendkey(30).pos = 2+1j
point.newendkey(30)
point.newendkey(30).pos = -3j

mation.play()
```
This can apply to other attributes too, such as an actor's `rotation`, so the camera rotates along with an actor:
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)
morpho.transition.default = morpho.transition.quadease

# Start camera zoomed in for a nicer effect
mainlayer.camera.last().zoomIn(2)

grid = mainlayer.Actor(morpho.grid.basicgrid(axes=True))
square = mainlayer.Actor(morpho.grid.Polygon([1+1j, -1+1j, -1-1j, 1-1j]))
mainlayer.camera.last().set(
    # Camera rotates the view oppositely to how the square
    # is rotating
    modifier=lambda self: self.rotate(-square.now().rotation)
    )

# Rotate the square one revolution counter-clockwise
square.newendkey(60).rotation = 2*pi

mation.play()
```
A fancier effect is to get the camera to smoothly switch its focus from one actor to another. For example, shifting from following a rotating square to following a moving point. This can be accomplished by incorporating a clock actor into the modifier whose parameter determines whether to focus on one actor or the other, or a blend between the two. To see how this can be done, let's start by having a square spinning and a point moving around simultaneously. We'll have the camera stay in a fixed position for now.
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)
morpho.transition.default = morpho.transition.quadease

# Start camera zoomed in for a nicer effect
mainlayer.camera.last().zoomIn(2)

grid = mainlayer.Actor(morpho.grid.basicgrid(axes=True))
point = mainlayer.Actor(morpho.grid.Point(-1.5+1.5j).set(
    tweenMethod=morpho.grid.Point.tweenSpiral
    ))
square = mainlayer.Actor(morpho.grid.Polygon([1+1j, -1+1j, -1-1j, 1-1j]).set(
    # Makes square rotate at a uniform speed
    transition=morpho.transition.uniform
    ))

# Point revolves counter-clockwise by 90 degrees twice
point.newendkey(30).pos *= -1j
point.newendkey(30).pos *= -1j

# Rotate the square one revolution counter-clockwise
square.newendkey().rotation = 2*pi

mation.play()
```
We'll now define a clock actor with its parameter value `t` initially set to 0. The idea will be `t=0` will correspond to focusing exclusively on the rotation square, and `t=1` will correspond to focusing exclusively on the moving point, and middle values interpolating between the two focuses.
```python
# Create invisible clock actor initialized to parameter t=0
clock = mainlayer.Actor(morpho.Skit(t=0))
```
Now to define the modifier. This one will be a bit more complex than the others, so we'll factor it out into its own separate named function instead of using `lambda`. Let's first deal with interpolating the camera's position of focus and ignore rotation. We want to center the camera at `square`'s position if the `clock`'s parameter is `t=0` and center it at the `point`'s position if the parameter is `t=1`. Both position values are recorded as complex numbers and we can interpolate between them according to a parameter value using the built-in `lerp()` function (short for *"linear interpolation"*).

`lerp()` takes three inputs: a starting value `a`, an ending value `b`, and an interpolation parameter `t` in the range `[0,1]`. For example, `lerp(100, 200, 0.3)` will output `130`. In this case, our `a` will be the `square`'s position, our `b` will be the `point`'s position, and `t` will be the `clock`'s current `t`-value:
```python
# Define modifier function
def mod(self):
    self.centerAt(morpho.lerp(
        square.now().origin,
        point.now().pos,
        clock.now().t
        ))
mainlayer.camera.last().modifier = mod
```
To handle rotation, we do something similar. In this case, we want to interpolate between the (negative of the) rotation of the square at `t=0` to 0 rotation for the point at `t=1`:
```python
# Define modifier function
def mod(self):
    self.centerAt(morpho.lerp(
        square.now().origin,
        point.now().pos,
        clock.now().t
        ))
    self.rotate(morpho.lerp(
        -square.now().rotation,
        0,
        clock.now().t
        ))
mainlayer.camera.last().modifier = mod
```
With this in place, we'll set the clock to shift its value from `t=0` to `t=1` after the point has undergone two 90-degree moves and then have the point complete four more after that so we can get a clear look at how the shift in focus happens dynamically. Here's the full code:
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)
morpho.transition.default = morpho.transition.quadease

# Start camera zoomed in for a nicer effect
mainlayer.camera.last().zoomIn(2)

grid = mainlayer.Actor(morpho.grid.basicgrid(axes=True))
point = mainlayer.Actor(morpho.grid.Point(-1.5+1.5j).set(
    tweenMethod=morpho.grid.Point.tweenSpiral
    ))
square = mainlayer.Actor(morpho.grid.Polygon([1+1j, -1+1j, -1-1j, 1-1j]).set(
    # Makes square rotate at a uniform speed
    transition=morpho.transition.uniform
    ))

# Create invisible clock actor initialized to parameter t=0
clock = mainlayer.Actor(morpho.Skit(t=0))

# Define modifier function
def mod(self):
    self.centerAt(morpho.lerp(
        square.now().origin,
        point.now().pos,
        clock.now().t
        ))
    self.rotate(morpho.lerp(
        -square.now().rotation,
        0,
        clock.now().t
        ))
mainlayer.camera.last().modifier = mod

# Point revolves counter-clockwise by 90 degrees twice
point.newendkey(30).pos *= -1j
point.newendkey(30).pos *= -1j

# Clock shifts from t=0 to 1 over 1.5 sec
clock.newendkey()
clock.newendkey(45).t = 1

# Point revolves 4 additional times
for n in range(4):
    point.newendkey(30).pos *= -1j

# Rotate the square one revolution counter-clockwise
square.newendkey().rotation = 2*pi

mation.play()
```

<!-- ## Puppeting Within Skits -->

## Referencing Modifier Effects Outside of Playback

As stated earlier, modifiers only affect figures *at playback time* and even then only in a temporary way. Accessing a figure's state directly, outside of animation playback time, just gives you its state as if the modifier weren't there. However, there may be rare instances in which you *want* to access a figure's would-be modified state during an animation to help you construct the current animation. An example might be placing a text label at the location a puppet Point actor will eventually be at. Another use case is stopping an actor from being controlled by another actor at a certain point in the animation and resuming normal control over it.

There are two closely related figure methods that will let you access a figure's modified state *in advance* during animation construction time: `actualize()` and `actualized()`.

`actualize()` applies a figure's modifier to itself and then resets its `modifier` attribute back to `None`. Basically it causes the figure's modified state to become actualized *now* instead of at playback time. `actualized()` is similar except it doesn't actually change the original calling figure's state itself, and instead actualizes a *copy* of the figure and returns it. `actualize()` is more useful when wanting to *terminate* modified behavior in an Actor midway thru its lifetime, and `actualized()` is more useful in *referencing* a modified figure's state before playback time. Let's do an example of both:

Let's take our shaking point example from earlier and put a little circle at the position where our shaking point will eventually end up. To do it, we'll need to reference the state of the actualized final keyfigure of the point actor:

```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)
morpho.transition.default = morpho.transition.quadease

# Define clock and path actors
clock = mainlayer.Actor(morpho.Skit(t=0))
path = mainlayer.Actor(morpho.graph.realgraph(lambda x: 0.5*x**2-2, -3, 3))

# Point is positioned along the path at whatever path point
# corresponds to the current t-value of the clock.
point = mainlayer.Actor(morpho.grid.Point(-0.5).set(
    modifier=lambda self: self.set(
        pos=self.pos+path.now().positionAt(clock.now().t)
        )
    ))
for n in range(18):
    # Point alternates between +0.5 and -0.5 over the course
    # of 90 frames (3 seconds)
    point.newendkey(5).pos *= -1

# Clock varies from 0 to 1 over the course of 90 frames
clock.newendkey(90).t = 1
# Path morphs into a cubic curve over the same duration
path.newendkey(90, morpho.graph.realgraph(lambda x: -(x**3-3*x)/5, -3, 3))

target = mainlayer.Actor(morpho.shapes.Ellipse().set(
    pos=point.last().actualized().pos,
    radius=0.25,
    color=[1,1,0],
    alphaFill=0
    ), atFrame=0)  # Make target appear at animation start

mation.play()
```

Now let's say we want to start doing something brand new with our point now that it's finished shaking its way to the target following the dynamic curved path. To do this, we need to free the point from the path's control. One way to do that is to simply reset the point's `modifier` attribute back to `None`, but if we do that, the point will simply jump back to the final position it would have had if it had never had a modifier in the first place:

```python
point.last().modifier = None
```

Instead we need to `actualize()` the final keyfigure of the point *in place*, which will free it from the modifier's control while preserving the final modified state it would have reached. However, this needs to done carefully, because if we call `actualize()` on the final keyfigure directly using `point.last().actualize()`, it will actually cause the point to move during its final "wiggle" because its final `pos` has been changed and will be tweened against the previous keyfigure's `pos` value.

This happens because the modifier, in addition to *modifying* the point's position, also, in this case, happens to modify it *based on its current value* (the modifier references `self.pos`). A simple way to get around this issue is to create a new keyframe just 1 frame after the wiggling animation completes and then actualize *that* keyfigure instead:

```python
point.newendkey(1).actualize()
```

Now we can freely animate the point however we want and it will no longer be subject to path's control:

```python
# Free the point actor from the modifier's control
# after the animation completes
point.newendkey(1).actualize()

# We can now move its position freely again
point.newendkey(30).pos = 0
point.newendkey(30).pos = -3-3j

mation.play()
```

One final important note about the `actualize()` and `actualized()` methods: they only work on *keyfigures* of an actor. You cannot use them either on intermediate tweened figures, or standalone figures that are not keyfigures in an actor.

```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)
morpho.transition.default = morpho.transition.quadease

point = mainlayer.Actor(morpho.grid.Point(-3).set(
    modifier=lambda self: self.set(pos=3j)
    ))
point.newendkey(30).set(pos=3, fill=[0,1,0])

# Access point's modified position in the middle
# of a tween. THIS WILL NOT WORK!
print(point.time(15).actualized().pos)

mation.play()
```

If you need to access the actualized position of an actor in the middle of a tween, you will need to create an intermediate keyfigure at that point in time:

```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)
morpho.transition.default = morpho.transition.quadease

point = mainlayer.Actor(morpho.grid.Point(-3).set(
    modifier=lambda self: self.set(pos=3j)
    ))
point.newendkey(30).set(pos=3, fill=[0,1,0])

# Reference point's modified position in the middle
# of a tween by first creating an intermediate
# keyfigure. THIS WILL WORK NOW!
print(point.newkey(15).actualized().pos)

mation.play()
```
