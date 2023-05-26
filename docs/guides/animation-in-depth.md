---
layout: default
title: Morpho Guide -- Animation In-depth
---

# Morpho Guide: Animation In-depth

> **Note:** This guide is only for Morpho 0.7.0+. For older versions, see [this guide](https://morpho-matters.github.io/morpholib/guides/old/animation-in-depth).

In [the previous guide](https://morpho-matters.github.io/morpholib/guides/figures-and-gadgets), we mostly dealt with static figures and went over their properties in great detail, but we didn't spend much time thinking about animation. So in this guide, we'll discuss Morpho's animation model in a bit more detail than we did in the first guide.

Since we already covered the basics of Morpho's animation model in the first guide, I won't repeat the basics here. So if you're rusty on how Actors work, I'd encourage you to [re-read](https://morpho-matters.github.io/morpholib/guides/basic-guide#actors) some of that part of the first guide.

> **Note:** To properly run the example code snippets in this guide, you should include the following lines at the top of your code:
> ```python
> import morpholib as morpho
> morpho.importAll()
>
> from morpholib.tools.basics import *
>
> mainlayer = morpho.Layer()
> mation = morpho.Animation(mainlayer)
> ```

## Tween Methods

We discussed "transitions" briefly in the first guide, which were basically variations on how the interpolation timing was performed. For example, setting a transition function to ``quadease`` (my favorite transition) results in a more organic animation where actors move and morph by first accelerating out of the initial keyfigure, and then slowing down when getting close to their ending keyfigure. However, all we've really seen so far has been figures moving in a straight line (just maybe with some variation on its speed of motion). Can you change an actor's *spatial* trajectory when tweening? Yes you can! To do it, you will have to change the so-called "tween method".

A *tween method* is a basically a function that takes three inputs: two figures (starting and ending) and an interpolation parameter *t* in the range 0 &#8804; t &#8804; 1, and outputs the interpolated (or "tweened") figure, where *t* = 0 corresponds to the starting figure, and *t* = 1 corresponds to the ending figure. By defining and setting a tween method, you gain full control on how interpolation behaves for an actor. And it's not too hard to create them yourself, really. However, in my experience, I often find that I rarely want to modify a tween method, and when I do, I usually only need to change it to one of the two alternative built-in tween methods. Let's go over them now and see how to set them.

### Spiral Tween

The *spiral tween* method essentially interpolates a position by linearly interpolating the radius and direction of the position instead of the *x* and *y* coordinates. This results in the figure moving along a spiral trajectory. Let's see how it works for a point:

```python
# Place a default grid in the background just to
# make the motion clearer
gridBG = mainlayer.Actor(morpho.grid.basicgrid(axes=True))

# Setup point at the coordinates (3,2) and
# set the tween method to be the Point class's
# spiral tween method.
mypoint = mainlayer.Actor(morpho.grid.Point(3+2j).set(
    tweenMethod=morpho.grid.Point.tweenSpiral
    ))

# Change the position to (-1,0) over the course of 1 second (30 frames).
mypoint.newendkey(30).pos = -1

mation.play()
```

The code reveals how you set a tween method. You assign it to a figure's ``tweenMethod`` attribute. So in the above code, we're setting the tween method of ``mypoint`` to be the ``tweenSpiral`` method associated with the ``Point`` class.

> ***CAUTION!*** There are two important things to remember about setting tween methods that are easy to get wrong if you're new to how they work. The first is that tween methods are assigned to a *Figure* object, NOT an *Actor* object. This means to assign a tween method after the actor has been defined, you will have to remember to reference a keyfigure using a method like ``first()``, ``last()``, or ``key()``. Something like this: ``mypoint.first().set(tweenMethod=etc)``.
>
> The second thing to remember about tween methods is that each figure type has its own personal set of tween methods that work on it. For example, the ``Point`` class has ``Point`` tween methods, and the ``Path`` class has ``Path`` tween methods. Be sure you assign a tween method that the given figure is designed to take. In the case of using the built-in tween methods, that means accessing the tween method as an attribute of the class's name. So for a point, you assign
> ```python
> mypoint.first().tweenMethod = morpho.grid.Point.tweenSpiral
> ```
> If you don't want to explicitly reference the figure's type when assigning a tween method, you can use Python's ``type()`` function:
> ```python
> mypoint.first().tweenMethod = type(mypoint.first()).tweenSpiral
> ```
> Or using the actor's ``figureType`` attribute:
> ```python
> mypoint.first().tweenMethod = mypoint.figureType.tweenSpiral
> ```

You can change the tween method for a grid as well. The easiest way is to set it via a parameter in ``mathgrid()`` when initially constructing the grid:

```python
# Setup a standard grid, but with the spiral
# tween method for a path.
mygrid = mainlayer.Actor(morpho.grid.mathgrid(
    tweenMethod=morpho.grid.Path.tweenSpiral
    ))

# Have it tween into a morphed version of itself
fgrid = mygrid.last().fimage(lambda z: z**2/10)
mygrid.newendkey(60, fgrid)

mation.play()
```

### Pivot Tween

The second non-trivial alternative tween method to the linear tween method is *Pivot Tween*. This essentially means moving the figure along a circular arc with angular span and direction you specify. The visual effect is often similar to Spiral Tween, but one big difference is that while Spiral Tween rotates figures about the global origin point, Pivot Tween rotates them about a *local* centerpoint determined by the angle of the arc. This can be nice because it means Pivot Tween is *translation symmetric*: the motion of the tween will look the same even if you translate the starting and ending figures by the same amount, i.e. translating the coordinate system; meaning the tween will look the same even if you're working under a coordinate system where the origin is way off screen.

The syntax for setting up a Pivot Tween is a slightly different than all other built-in tween methods because you also have to specify an angle parameter: the angle of the arc trajectory. Here's how it looks:

```python
# Place a default grid in the background just to
# make the motion clearer
gridBG = mainlayer.Actor(morpho.grid.basicgrid(axes=True))

# Setup point at the coordinates (3,2) and
# set the tween method to be the Point class's
# pivot tween method with an angle of pi radians.
mypoint = mainlayer.Actor(morpho.grid.Point(3+2j).set(
    tweenMethod=morpho.grid.Point.tweenPivot(pi)
    ))

# Change the position to (-1,0) over the course of 1 second (30 frames).
mypoint.newendkey(30).pos = -1

mation.play()
```

The important difference to note is that instead of just typing the tween method's *name*, like ``tweenPivot``, you actually have to *call* it with an input value (the angle): ``tweenPivot(pi)``. This tells Morpho that the trajectory of the tween should be along an arc of &pi; radians (180 degrees) traveling counter-clockwise from the starting figure to the ending figure.

> ***CAUTION!*** Please be careful to remember to call the ``tweenPivot()`` function either with a supplied angle value (like ``tweenPivot(pi/2)``), or else with no parameters (like ``tweenPivot()``), but NEVER set it without calling it at all<sup>[</sup>[^1]<sup>]</sup>:
> ```python
> # This is WRONG! Never do this! You need to always call it
> # with parentheses: tweenPivot(myangle) or tweenPivot()
> mypoint.first().tweenMethod = mypoint.figureType.tweenPivot
> ```
> This is one of the major differences in syntax between ``tweenPivot`` and all the other built-in tween methods (like ``tweenLinear`` and ``tweenSpiral``).

[^1]: For the more technically inclined, what this means is that the built-in function ``tweenPivot()`` associated with most figures is not *strictly speaking* a tween method, but rather a tween method *generator*: it takes as input an angle value, and it returns a bona fide tween method that performs the intended pivot tween behavior determined by the angle.

You can reverse the direction of the pivot by making the angle value negative:

```python
mypoint.first().tweenMethod = morpho.grid.Point.tweenPivot(-pi)
```

which results in the point traveling *clockwise* to its final destination.

Try experimenting with other angle values to get a better sense of how it works. The only requirement is that the supplied angle value cannot be a multiple of 2&pi;.

### Using multiple tween methods/transitions

You might be wondering why tween methods are assigned at the *Figure* level as opposed to the *Actor* level. The reason is because a single actor can make use of multiple tween methods at different points in its timeline!

As an example, let's consider our point animation from earlier, and let's say we want to have it spiral tween to the point (-1,0), but then linearly tween back to its starting position. Here's one way to code it up:

```python
# Place a default grid in the background just to
# make the motion clearer
gridBG = mainlayer.Actor(morpho.grid.basicgrid(axes=True))

# Setup point at the coordinates (3,2) and
# set the tween method to be the Point class's
# spiral tween method.
mypoint = mainlayer.Actor(morpho.grid.Point(3+2j).set(
    tweenMethod=morpho.grid.Point.tweenSpiral
    ))

# Change the position to (-1,0) over the course of 1 second (30 frames)
# and also reassign the tween method at this point to be linear tween.
mypoint.newendkey(30).set(
    pos=-1,
    tweenMethod=mypoint.figureType.tweenLinear
    )

# Create a new keyfigure returning the point to its
# starting location. The tween method is governed by
# the previous keyfigure's tween method: tweenLinear
mypoint.newendkey(30, mypoint.first().copy())

mation.play()
```

As you can see, the point first follows a spiral path getting to the point (-1,0) before rebounding back to its starting position along a straight line. So how is the code instructing this exactly?

The key idea is that the tween method used for a tween between two keyfigures is controlled by the *earlier* keyfigure's ``tweenMethod`` setting. If we call the two keyfigures we're tweening *A* and *B*, where *A* is the earlier keyfigure, then *A*'s tween method determines the tween method used for the interpolation between *A* and *B*. Likewise, if keyfigure *B* is followed by keyfigure *C*, then *B*'s tween method controls the interpolation between *B* and *C*.

So in the above code, we initialized ``mypoint`` with the spiral tween method ``tweenSpiral``, but after we set up the second keyfigure (after calling ``newendkey(30)``), we then edited its tween method by stating
```python
tweenMethod = mypoint.figureType.tweenLinear
```
which means that when we set up the third keyfigure with the second ``newendkey()`` declaration, the interpolation between the second and third keyfigures is controlled by ``tweenLinear``.

This actually reflects a general convention about interpolation in Morpho: Whenever a property of a figure is not tweenable, the interpolated figure takes on the property of the *earlier* keyfigure in the interpolation.

For example, all figures possess a visibility attribute called ``visible`` which indicates whether the figure should be drawn at all. It's just a boolean, so it's not tweenable, and so if we have two keyfigures *A* and *B* one after the other in an actor's timeline, where *A* is the earlier keyfigure, if *A*'s visibility is set to ``False``, then all tweened figures interpolated between *A* and *B* will inherit the visibility of *A*, which has the effect of making the actor disappear for the interval of time between the keyfigures *A* and *B*.

This convention also has the nice effect that if you want to set a tween method (or other such property) that applies to the entire actor, this can usually be accomplished by setting the first keyfigure's tween method to the desired value, and then it will propagate to all future keyfigures until you modify it again<sup>[</sup>[^2]<sup>]</sup>.

[^2]: The only exception to this is if you use the second argument of ``newendkey()`` to explicitly set a keyfigure to be an externally constructed figure. e.g. ``mypoint.newendkey(30, myotherpoint)``. In this case, the tween method (or other property) of the new keyfigure will be that of whatever the externally supplied figure is.

You can also use this technique to set up multiple different ``transitions`` for an actor at different points in its timeline:

```python
# Place a default grid in the background just to
# make the motion clearer
gridBG = mainlayer.Actor(morpho.grid.basicgrid(axes=True))

# Setup point at the coordinates (3,2) and
# set the tween method to be the Point class's spiral tween method.
# Also set the transition to be quadease.
mypoint = mainlayer.Actor(morpho.grid.Point(3+2j).set(
    tweenMethod=morpho.grid.Point.tweenSpiral,
    transition=morpho.transitions.quadease
    ))

# Change the position to (-1,0) over the course of 1 second (30 frames)
# and also reassign the tween method at this point to be linear tween.
# Also set the transition from this point to be uniform
mypoint.newendkey(30).set(
    pos=-1,
    tweenMethod=mypoint.figureType.tweenLinear,
    transition=morpho.transitions.uniform
    )

# Create a new keyfigure returning the point to its
# starting location. The tween method is governed by
# the previous keyfigure's tween method: tweenLinear
mypoint.newendkey(30, mypoint.first().copy())

mation.play()
```

Here, the transition is initially set to ``quadease`` which leads to the organic easing in and out along the spiral trajectory, but then it switches back to a ``uniform`` transition when it takes the linear trajectory back to its starting point.

So to summarize, a *tween method* can fully control the behavior of tweening (i.e. figure interpolation). All a tween method really needs to do is take three inputs: two figures of the exact same type, and one interpolation parameter, which outputs another figure of the exact same type as the inputs. A *transition function* essentially modifies the *timing* or *speed* at which the tween method is applied, but actually, strictly speaking, transitions are not a required component of tweening: you can define a tween method independently to implement whatever transition you'd like. So transitions just provide a more convenient way to modify a tween method's behavior without having to go out of your way to define a completely separate new tween method.

## The ``visible`` and ``static`` Attributes

All figures have these two non-tweenable attributes associated with them. The first, ``visible``, I briefly touched on earlier, and basically controls whether or not a figure will be drawn. Within an actor, this can be used to define a time interval on which the actor will be invisible because between two keyfigures, the interpolated figure inherits the visibility of the earlier keyfigure. This can be useful if you want to change some aspect of an actor after you've faded it out or moved it off of the screen. For example, if you move a figure off screen and want it to reappear after a while on the opposite side of the screen, you can make the actor invisible during the duration in which you reposition it.

```python
# Initialize point at the origin, but make it big.
mypoint = mainlayer.Actor(morpho.grid.Point(0).set(size=50))

# Move point off the left side of the screen
mypoint.newendkey(30).set(
    pos=-6,
    visible=False
    )

# While invisible, move to being off the
# right side of the screen
mypoint.newendkey(15).set(
    pos=6,
    visible=True
    )

# After being made visible again, move
# back to the origin.
mypoint.newendkey(30).pos = 0

mation.play()
```

The ``static`` attribute is a less commonly used attribute, but it's occasionally handy. It's ``False`` by default, but if set to ``True``, ``fimage()`` will ignore the figure if it's part of a composite figure like a ``Frame``, and the figure will no longer be tweened with a partner figure if it's part of an actor or ``Frame`` object.

This is the how the static background grid generated by ``mathgrid()`` works: the component ``Path`` figures that make up the background grid (as well as the axes) are set to be static, so they do not respond either to ``fimage()`` calls, nor will they be tweened.

> **Technical Note:** Both the ``visible`` and the ``static`` attributes only apply if the figure is a part of a higher order structure like an actor or a ``Frame``. This means that if you were to manually call the figure's ``draw()`` method in a vacuum, it would still be drawn even if its ``visible`` attribute were set to ``False``. Similarly, tweening two figures in a vacuum by manually calling ``myfig.tween(myotherfig, 0.5)`` will still perform the tween even if ``myfig.static`` is set to ``True``. So ``visible`` and ``static`` are merely requests to higher order constructs containing the figure; it is the responsibility of the higher order constructs to honor those requests. This reflects another general convention of Morpho: any meta-setting that an object possesses is usually merely a request, and it is the responsibility of the programming constructs that make use of these objects to fulfill those requests. The object's native methods will usually ignore these meta-settings.

## Other Tools

### Locator layers

When constructing an animation, you may sometimes want to know the *exact* coordinates of a point on the screen; like to place a label or something over a figure. While sometimes you can get away with just eyeballing it and guessing the coordinates, if you need to know more precisely, there is a way to do just that.

The idea is that you can get the *Animation* class to consider a particular layer a so-called "locator layer". Once this is set up, every time you click on some pixel of an animation during playback, it will print the exact physical coordinates of that pixel (according to the specified locator layer) to the console window. I use these all the time while in the process of creating an animation, and there's really no reason to ever *not* set a locator layer as far as I know.

Let's do an example. First let's take a standard grid and have it morph into some distorted grid:

```python
# Setup a default grid
mygrid = mainlayer.Actor(morpho.grid.mathgrid())

# Morph it into a distorted version
mygrid.newendkey(30, mygrid.first().fimage(lambda z: z**2/10))

# Set the first layer (the layer #0) as the locator layer
mation.locatorLayer = 0
mation.play()
```

Try clicking on the screen! You'll find that every click results in the coordinates being printed to your console window. The way it works is we set the "locator layer" of the animation we called ``mation`` to be the bottommost layer it contains (index ``0``) which, in our simple animation, is actually the only layer it contains.

You could use this feature to, for example, get pretty precise coordinates of any of the lattice points in the distorted grid, if you wanted to label some of them, perhaps. However, at the moment it's a bit annoying to do so, because in addition to printing coordinates to the screen, every click causes the animation to either pause, unpause, or repeat itself from the beginning. And since the distorted grid is the final frame of the animation, every click on one of the distorted lattice points requires you to rewatch the entire animation again before you can click on another one. To get around this, what I often do is set the starting frame of the animation to coincide with the final frame. That way, the animation only ever displays the final frame and you can click as often as you like with no change to the view:

```python
# Set the first layer (the layer #0) as the locator layer
mation.locatorLayer = 0
# Set the initial frame of the animation to be its final frame
mation.start = mation.lastID()
mation.play()
```

There's actually another way to specify a locator layer which I find more useful when I'm creating an animation that contains many layers. Usually in a multi-layer animation, I have given names to the various layers (e.g. ``mainlayer`` or ``toplayer``). In this case, you can set the locator layer to be the actual *Layer* object itself instead of its position within the animation's internal stack:

```python
# Set `mainlayer` as the locator layer
mation.locatorLayer = mainlayer
mation.play()
```

Finally, there are two additional attributes for locator layers called ``clickCopy`` and ``clickRound``.

``clickCopy`` is a boolean which if set to True, causes the coordinates of every click to be copied to your clipboard.

``clickRound`` takes an integer specifying the decimal place to round the coordinates to. By default, it's set to ``None``, meaning it doesn't round.

```python
mation.clickCopy = True  # Coordinates will be copied to clipboard
mation.clickRound = 2    # Coordinates round to the second decimal place
```

### Still other tools

Finally, there are a miscellaneous collection of handy functions you can access via ``morpholib.tools``. The most common set are found in the ``morpholib.tools.basics`` submodule. I usually prefer to just import the entire module into the current namespace:
```python
from morpholib.tools.basics import *
```
This imports a number of useful constants and functions including
- ``pi``, ``tau``: &pi; and its big brother &tau; = 2&pi; are provided free of charge.
- ``oo``, ``nan``: The floats ``inf`` and ``nan`` are provided, though ``inf`` goes by the name ``oo`` (two lowercase letter *o*'s) as I think it resembles an infinity symbol.
- ``sgn()``: Signum function. Returns ``+1`` given positive input, ``-1`` given negative input, and ``0`` given ``0`` input.
- ``mean()``: Computes the mean of a list of numbers or numpy arrays. I find this function particularly useful if I want to place a figure exactly halfway in between two other figures.
  ```python
  label.pos = mean([point1.pos, point2.pos])
  ```
- ``truncate()``: Behaves like Python's built-in ``round(num, ndigits)``, but truncates at the final decimal place instead of rounding.
  ```python
  truncate(pi, 4) -> 3.1415 instead of 3.1416
  ```
- ``compose()``: Returns the composition of an arbitrary number of functions. Usage:
  ```python
  compose(f,g,h) -> Composition lambda x: f(g(h(x)))
  ```
  I find this useful to compose multiple transition functions together, particularly if I have a custom transition function that I would like to be traversed with quadease:
  ```python
  mytransition = compose(custom_transition, morpho.transitions.quadease)
  ```
- ``boxCorners()``: Given a viewbox 4-tuple/list ``[xmin,xmax,ymin,ymax]``, it returns the corner points of the box as a list of complex numbers. By default, it returns them starting with the northwest corner and going counter-clockwise, but this can be modified with some optional arguments. Usage:
  ```python
  corners = boxCorners([-3,2,-1,0])  # outputs list of 4 complex numbers
  altcorners = boxCorners([-3,2,-1,0], initCorner="SE", CCW=False)
  ```

#### Footnotes
