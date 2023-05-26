---
layout: default
title: Morpho Guide -- Useful Figures and Gadgets
---

# Morpho Guide: Useful Figures and Gadgets

> **Note:** This guide is only for Morpho 0.7.0+. For older versions, see [this guide](https://morpho-matters.github.io/morpholib/guides/old/figures-and-gadgets).

Last guide, we explored some basic figures like points, paths, and polygons. Now we'll look at some other useful figures like *Text*, *Image*, and *Arrow* along with some handy gadgets which help to generate some of these figures in commonly used configurations.

> **Note:** To properly run the example code snippets in this guide, you should include the following lines at the top of your code:
> ```python
> import morpholib as morpho
> morpho.importAll()
>
> import math
> from math import pi
> import numpy as np
>
> mainlayer = morpho.Layer()
> mation = morpho.Animation(mainlayer)
> ```
> You will also need to place the two image files ``ball.png`` and ``oo.png`` into the same directory as your Python scripts. These image files can be downloaded [from here](https://github.com/morpho-matters/morpholib/tree/master/examples).

## Text

The ``Text`` figure allows you to display text in an animation. This figure can be accessed from the ``text`` submodule. The basic syntax to create one is as follows:

```python
morpho.text.Text("Hello World")
```

which defines some text saying "Hello World" centered at the origin. After initialization, you can modify the following attributes:

- ``text``: String of text to display (e.g. "Hello World").
- ``pos``: Text position (as a complex number). Defaults to ``0`` (the origin).
- ``size``: Text size. Defaults to 64.
- ``font``: Font to use. Defaults to ``"Times New Roman"``.
- ``bold``: Boolean denoting whether the text should be bold or not. Defaults to ``False``.
- ``italic``: Boolean denoting whether the text should be italicized or not. Defaults to ``False``.
- ``anchor_x``: Real number in [-1,1] indicating horizontal alignment. -1 is left, +1 is right, 0 is center. Default: ``0``
- ``anchor_y``: Real number in [-1,1] indicating vertical alignment. -1 is bottom, +1 is top, 0 is center. Default: ``0``
- ``color``: Text color. Default: ``[1,1,1]`` (white)
- ``alpha``: Text opacity. Default: ``1`` (opaque)
- ``rotation``: Rotation of text about its anchor point in counter-clockwise radians. Defaults to ``0``.

Most of these attributes are tweenable, meaning they can be interpolated in an actor. Alas, the ``text`` string attribute is not tweenable so you can't morph one text string into another, but there actually is a way to do it using the ``MultiText`` class (more on that later).

For now, let's see an example. Let's make our Hello World text bigger and color it red:

```python
mytext = mainlayer.Actor(morpho.text.Text("Hello World").set(
    size=84,
    color=[1,0,0]
    ))

mation.play()
```

You can also change the actual text string of a text figure by modifying its ``text`` attribute:

```python
mytext = mainlayer.Actor(morpho.text.Text("Hello World").set(
    size=84,
    color=[1,0,0]
    ))
mytext.first().set(text="Hi Y'all!")

mation.play()
```

## Images

You can display PNG images using the ``Image`` class (found in the ``graphics`` submodule). The basic syntax is as follows:

```python
morpho.graphics.Image("path/to/image/file.png")
```

Though you can also initialize an Image figure using a separate already initialized Image figure:

```python
morpho.graphics.Image(mypic)
```

You can then modify the following attributes (all of which are tweenable):
- ``pos``: Image position (complex number). Default: ``0``
- ``align``: Image alignment. A pair of real numbers ``[alignX, alignY]`` in the range [-1,1] indicating alignment similar to ``anchor_x`` and ``anchor_y`` for the ``Text`` class. Default: ``[0,0]`` (center alignment)
- ``width``: Image width in physical units.
- ``height``: Image height in physical units.
- ``scale_x``: Horizontal scale factor. Applied AFTER rotation. Default: ``1``
- ``scale_y``: Vertical scale factor. Applied AFTER rotation. Default: ``1``
- ``rotation``: Rotation in radians. Default: ``0``
- ``alpha``: Opacity. Default: ``1`` (opaque)

An important thing to note here is that ``width`` and ``height`` are specified in so-called "physical" units, which means relative to distances and lengths in the current view of the complex plane as opposed to pixels<sup>[</sup>[^1]<sup>]</sup>.

[^1]: Might be a good time for some more terminology: In Morpho, a "physical" quantity pretty much always means *relative to the local coordinate system of the layer's camera*. e.g. *physical width* or *physical coordinates*. This is in contrast to "pixel" or "screen" coordinates or quantities, which mean *relative to the pixels on the user's actual screen*. Morpho has tools to convert between the two. See the documentation for the methods ``morpho.physicalCoords()``, ``morpho.pixelCoords()``, ``morpho.physicalWidth()``, etc. for more info.

For example, in the standard [-5,5] x [-5*j*, 5*j*] view of the complex plane, setting ``width`` to 5 would mean the image would be about half as wide as the entire canvas when drawn (because 5 is half of the width of the entire view: ``5-(-5) = 10``). This convention makes it easier to set the sizes of images relative to other objects in the scene. It also means zooming the camera in and out will scale the image correctly relative to its surroundings. That is, the image behaves as if it is an actual "physical" object in the scene, as opposed to a sticker or a label floating above it.

Another thing to note is that by default, ``width`` and ``height`` are linked together, so modifying one modifies the other so that the image's aspect ratio is preserved. If you don't want this behavior, you can disable it by calling the method ``unlink()``:

```python
mypic = mainlayer.Actor(morpho.graphics.Image("path/to/image/file.png"))

mypic.first().unlink()
mypic.first().set(
    width=5,   # These are now independent
    height=2   # of each other
    )
```

Similar to ``Text`` figures, you can't properly tween two image figures with different source files, or at least not using the vanilla ``Image`` class. To do it, you'll have to use the ``MultiImage`` class.

## Multifigures

Both the ``Text`` class and the ``Image`` class have so-called "multifigure" versions called ``MultiText`` and ``MultiImage``. In most use cases, these variants behave exactly like their vanilla counterparts, but support a primitive morphing effect that allows you to more properly tween their normally untweenable contents.

To see what I mean, let's have one Text figure morph into another one with a different content string:

```python
message = mainlayer.Actor(morpho.text.MultiText("Hello World!"))
# Over the course of a second, morph the text to say "Bye!"
message.newendkey(30).set(text="Bye!")

mation.play()
```

You can achieve a similar effect with images. But to change one image to another requires using the ``newSource()`` method to define a new source PNG file:

```python
mypic = mainlayer.Actor(morpho.graphics.MultiImage("./ball.png").set(
    width=3
    ))
mypic.newendkey(30).newSource("./oo.png")

mation.play()
```

This works, but you might notice that the final image is distorted. This is because calling ``newSource()`` on its own leaves the previous aspect ratio unchanged. But it's easy to reset the aspect ratio to the new final image by calling either ``scaleByWidth()`` or ``scaleByHeight()``. For example:

```python
mypic = mainlayer.Actor(morpho.graphics.MultiImage("./ball.png").set(
    width=3
    ))
# Rescale height while leaving width unchanged
mypic.newendkey(30).newSource("./oo.png").scaleByWidth()

mation.play()
```

The final image is now in the correct proportion. This was accomplished by rescaling the height while leaving the width fixed from the original. But you can do it the other way as well:

```python
mypic.newendkey(30).newSource("./oo.png").scaleByHeight()
```

The final image is again in proper proportion, but this time it was done by rescaling the width while leaving the height unchanged from the original image.

Depending on how you interpret the phrase "scale by", the naming convention used by these methods might feel backward to you. And maybe you're right. But for what it's worth, here's how I read them: ``scaleByWidth()``, for example, means to scale the image *based on* the width: you're rescaling it while using the width as your reference.

## Arrows

An arrow is just a line segment whose ends can be made pointy (who would have thought?). This figure can be accessed from the ``grid`` submodule. The basic syntax to create one is as follows:

```python
morpho.grid.Arrow(tail, head)
```

where ``tail`` and ``head`` are meant to be complex numbers denoting where the tail and head of the arrow are supposed to be located. If unspecified, they default to ``0`` and ``1`` respectively.

Besides the location of the tail and head, you can also specify the following attributes:
- ``color``: Arrow color
- ``alpha``: Arrow opacity
- ``width``: Arrow thickness (in pixels)
- ``headSize``: Size of the arrow's head tip (in pixels)
- ``tailSize``: Size of the arrow's tail tip (in pixels)

All of these attributes are tweenable, meaning they can be smoothly interpolated in an actor. Let's do an example based off a common animation I make with arrows.

### Example

Let's place a point on the screen and then label it with some text and have an arrow grow out and point at it. We won't do anything fancy with the point, so let's just give it default settings and position it at the origin:
```python
pt = mainlayer.Actor(morpho.grid.Point(0))
```
Next we'll make a Text figure labeling the point. Let's place it a bit below the location of our point. We'll use relative coordinates to define it so that if we want to go back in the code and change where the point's position is, our label will move accordingly:
```python
label = mainlayer.Actor(morpho.text.Text("Watch me carefully!").set(
    pos=pt.first().pos-3j
    ))
```
Now let's format it a little. We'll make it bigger and color it red:

```python
label = mainlayer.Actor(morpho.text.Text("Watch me carefully!").set(
    pos=pt.first().pos-3j,
    size=48,
    color=[1,0,0]
    ))
```

Now for the fun part. Let's make an arrow that grows from a position slightly above our text label and then points toward our Point figure. To do this, we'll start out by positioning both the head *and* tail of the arrow at a position slightly above the label:

```python
arrow = mainlayer.Actor(morpho.grid.Arrow())
arrow.first().tail = arrow.first().head = label.first().pos + 0.5j
```

Next we'll give it some formatting:

```python
arrow = mainlayer.Actor(morpho.grid.Arrow().set(
    headSize=0,    # Override default headSize of 25
    width=5,
    color=[1,1,1]  # Color it white
    ))
arrow.first().tail = arrow.first().head = label.first().pos + 0.5j
```

Now let's give it a modified keyframe at the 1 second (30 frame) mark. We'll move the arrow's head position to be slightly below the Point figure and grow the size of its tip:

```python
arrow.newendkey(30).set(
    head=pt.first().pos-0.5j,
    headSize=25
    )
arrow.last().head = pt.first().pos - 0.5j
arrow.last().headSize = 25

mation.play()
```

> ***Tip:*** The Path class also supports the ``headSize`` and ``tailSize`` attributes, which are set to 0 by default. So you can turn any path into a curved arrow by changing its ``headSize`` and ``tailSize``. The "head" of a path is considered the last vertex in the vertex sequence while the "tail" of a path is its first vertex.

### Other arrow tools

There are a few other methods/attributes of arrows that come in handy from time to time. First you can compute the length (distance between head and tail) of an arrow using the ``length`` attribute:
```python
print(arrow.last().length)
```
But you can also change its length too:
```python
arrow.last().length = 4
```
The way this is done is the tail of the arrow is held fixed and the head is moved along the original direction of the arrow until it is the specified distance away from the tail. So the distinction between the head and the tail of an arrow is more than just conceptual.

The ``angle`` attribute indicates the direction the arrow is pointing (tail-to-head) in terms of an absolute angle (in radians) measured counter-clockwise from the positive real axis. It can also be set similar to the ``length`` attribute.

```python
print(arrow.last().angle)
arrow.last().angle = math.pi
```

The ``unit()`` method returns a complex number representing the direction unit vector for the arrow (tail-to-head).
```python
print(arrow.last().unit())
```

The ``midpoint()`` method returns the midpoint between the arrow's head and tail:
```python
print(arrow.last().midpoint())
```

And finally, the `vector` attribute returns the tail-to-head vector as a complex number. It can also be set to place the arrow head at a position relative to its tail:
```python
print(arrow.last().vector)
arrow.last().vector = 1+1j
```

## Helpful gadgets

There are a number of helpful functions and gadgets to assist in creating common figure constructions. We already looked at a few in the previous guide, but now we'll explore them in more detail and give a more comprehensive list of the available tools.

### More about ``line()``, ``rect()``, ``ellipse()``, and ``arc()``

The three functions ``line()``, ``rect()``, ``ellipse()``, and ``arc()`` can all be found in the ``grid`` submodule. They are accessible like this: ``morpho.grid.line()``

We actually already covered ``line()`` in the previous guide. So I won't repeat it here.

``rect()`` can be used to create a generic rectangle polygon. It takes one required input: a 4-tuple or list describing a box in the complex plane: ``[xmin,xmax,ymin,ymax]``. It will return a *generic* polygon figure with its four vertices set to describe the specified box. However, please remember that ``rect()`` returns a *generic* polygon (that is, all its other attributes beyond ``vertices`` will all be their default values), so you will need to modify its other attributes afterward to make it look a particular way.

Example:
```python
myrect = mainlayer.Actor(morpho.grid.rect([-3,3, -1,2]).set(
    width=5,
    color=[1,0,0],
    fill=[1,1,0]
    ))

mation.play()
```

Note you can also create a rectangular ``Path`` figure using ``rect()`` as well. Just call the Polygon method ``edge()`` after construction:
```python
myrectpath = mainlayer.Actor(morpho.grid.rect([-3,3, -1,2]).edge())
```

``ellipse()`` is used to construct a generic Polygon that looks like an ellipse. It takes three parameters:
- ``z0``: Center of ellipse (complex number)
- ``a``: Horizontal radius (i.e. semi-width) in physical units
- ``b``: Vertical radius (i.e. semi-height) in physical units (optional; if unspecified, it copies `a`)

Try it out:
```python
# Ellipse centered at (2,1) with semi-width 3, and semi-height 1.
myoval = mainlayer.Actor(morpho.grid.ellipse(2+1j, 3, 1))

mation.play()
```
And like before, this polygon is otherwise generic, so you will have to modify its style parameters afterward:
```python
# Ellipse centered at (2,1) with semi-width 3, and semi-height 1.
myoval = mainlayer.Actor(morpho.grid.ellipse(2+1j, 3, 1).set(
    width = 5,
    color=[0,0,1],
    fill=[0,0.6,0]
    ))

mation.play()
```
And if you want the Path describing its boundary, you can call ``edge()``:
```python
myovalpath = mainlayer.Actor(morpho.grid.ellipse(2+1j, 3, 1).edge())
```

Note that ``ellipse()`` can also take two additional optional inputs:
- ``dTheta``: Angular separation between adjacent vertices of the polygon (in ***radians***). Default: 2&pi;/72 (5 degrees)
- ``phase``: Angle (in ***radians***) where the initial vertex of the polygon begins. Measured counter-clockwise from the positive real axis. Default: 0

I generally don't find much occasion to mess with these parameters, but they might be important in certain special cases. For example, ``phase`` might matter if you want to more precisely control how the ellipse morphs into a different polygon.

``arc()`` returns a ``Path`` figure in the shape of a circular arc that connects two positions ``p`` and ``q`` which you specify with an arc of a specified angle.

Here's an example:
```python
# Connect the point -2-1j to the point 3+2j with
# an arc of angle pi/2 radians traveling counter-
# clockwise from the first to the second point.
myarc = mainlayer.Actor(morpho.grid.arc(-2-1j, 3+2j, pi/2))

mation.play()
```
Note that the arc travels *under* the line connecting the two points ``-2-1j`` and ``3+2j``. This is because the angle value we supplied, ``pi/2`` was *positive*. And so the arc will travel counter-clockwise from the first point toward the second. To reverse this behavior, you can either swap the order of the two points, or flip the sign of the angle:
```python
morpho.grid.arc(3+2j, -2-1j, pi/2)   # Two ways to reverse
morpho.grid.arc(-2-1j, 3+2j, -pi/2)  # the arc's direction
```
And once again, the output of ``arc()`` is a generic path, so to modify its appearance, you must set its attributes one at a time after construction:
```python
myarc = morpho.grid.arc(-2-1j, 3+2j, pi/2).set(
    width=8,
    color=[0,1,0]
    )
```
To get a better intuition of exactly what ``arc()`` does, experiment around with a few other points and angle values and see what happens.

### More about ``mathgrid()``

We've already encountered the ``mathgrid()`` function in the previous guide, but now we'll explore it in more detail. As a reminder, the ``mathgrid()`` function can be found in the ``grid`` submodule and is the main tool to use to construct morphable grids. The function can actually take a large number of input parameters, giving you fine control over the look and behavior of the grid. Here are most of them:
- ``view``: Bounding box of the grid (``[xmin,xmax,ymin,ymax]``). Default: ``[-5,5, -5,5]``
- ``dx,dy``: Horizontal or vertical spacing in physical units. Default: ``1``
- ``hsteps``, ``vsteps``: Number of internal steps to take in a single grid line. This is analogous to the ``steps`` parameter in the ``morpho.grid.line()`` function. Higher values mean a higher resolution grid, but possibly slower render time. Default: 50 steps
- ``hcolor``, ``vcolor``: Color of the major horizontal and vertical grid lines. Default: ``[0,0,1]`` (blue)
- ``hmidColor``, ``vmidColor``: Color of minor grid lines. Default: ``None`` (meaning it will brighten the major color by 50%.
- ``hwidth``, ``vwidth``: Thickness of major grid lines in pixels. Default: ``3``
- ``hmidlines``, ``vmidlines``: Number of minor grid lines between each pair of major grid lines. Default: ``1``
- ``hmidWidth``, ``vmidWidth``: Thickness of minor grid lines in pixels. Default: ``1``
- ``BGgrid``: Boolean indicating whether to draw a dimmer static background grid. Useful when doing morphing animations that alter the grid. Default: ``True``
- ``axes``: Boolean indicating whether or not to draw axes. Default: ``True``
- ``axesColor``: Color of axes if they are drawn. Default: ``[1,1,1]`` (white)
- ``xaxisWidth``, ``yaxisWidth``: Thickness of axes in pixels. Default: ``5``
- ``axesStatic``: Boolean indicating whether or not axis paths should be static, meaning they will not be affected by ``fimage()`` calls, nor will they be tweened. Default: ``True``

> **Note:** These parameters can *only* be specified by keyword, not as positional arguments. That is, the format must be ``mathgrid(view=[-5,5,-5,5], dx=1, ...)``, not ``mathgrid([-5,5,-5,5], 1, ...)``

Try it out:
```python
# Make a grid with thick, green horizontal lines
# and 4 minor grid lines between every two major
# lines. Also disable background grid and axes.
mygrid = mainlayer.Actor(morpho.grid.mathgrid(
    view=[-3,3, -3,3],
    hcolor=[0,1,0], hwidth=5,
    hmidlines=4, vmidlines=4,
    BGgrid=False, axes=False
    ))

mation.play()
```

There's also a similar function called `basicgrid()` which is exactly like `mathgrid()` but by default the number of steps per grid line is 1, the axes are off, and there is no background grid. This function is better to use if you just need a simple background grid and don't intend to morph it in any complex way since it can be drawn more efficiently since each grid line doesn't consist of \~50 subsegments!

### ``realgraph()``

There is a special gadget that is designed specifically for creating the graph of a function *y* = *f*(*x*). It's called ``realgraph()`` and you can access it from the ``graph`` submodule:

``morpho.graph.realgraph()``

It takes three required inputs:
- ``f``: A real-to-real function whose graph you want.
- ``a``, ``b``: The left- and right-endpoints of the interval on which to graph.

Try it out:
```python
f = lambda x: x**2
fgraph = mainlayer.Actor(morpho.graph.realgraph(f, -2, 2))

mation.play()
```
> **Note:** I used Python's ``lambda`` syntax to define the function *f*(*x*) = *x*<sup>2</sup>, but this is by no means required. You can input a python function defined in any way into ``realgraph()`` as long as it takes real number inputs in the interval you specify and outputs real numbers.

Depending on the function you're graphing, the path's resolution may need to be higher than the default. So just like with ``line()``, you can change the number of steps within the path by setting the optional argument ``steps``:
```python
# This looks awful
f1 = lambda x: 4*(1+math.sin(5*x))/2
fgraph1 = mainlayer.Actor(morpho.graph.realgraph(f1, -4, 4))

# This looks way better
f2 = lambda x: 4*(-1+math.sin(5*x))/2
fgraph2 = mainlayer.Actor(morpho.graph.realgraph(f2, -4, 4, steps=200))

mation.play()
```
By default, ``steps`` equals 50.

The output of ``realgraph()`` is a Path figure, so you can modify its other attributes afterward just like with ``line()`` and ``arc()``.
```python
f = lambda x: x**2
# Make graph thick, red, and semi-transparent
fgraph = mainlayer.Actor(morpho.graph.realgraph(f, -2, 2).set(
    width=10,
    color=[1,0,0],
    alpha=0.5
    ))

mation.play()
```

## Transformation Tweenables

Many (though not all) figures support one or more so-called "transformation tweenables". These are tweenable attributes with the names ``origin``, ``rotation``, or ``transform``, and can be used to, well, *transform* the appearance of the figure by translation, rotation, scaling, shearing, or other linear transformation.

To see why these might matter, let's consider the ellipse polygon we created earlier:
```python
# Ellipse centered at (2,1) with semi-width 3,
# and semi-height 1.
myoval = mainlayer.Actor(morpho.grid.ellipse(2+1j, 3, 1))
```
The ``ellipse()`` function is only capable of creating ellipses in one of two basic orientations: either having its long side parallel to the *x*-axis, or having its long side parallel to the *y*-axis. But what if you want to have the major and minor axes of the ellipse oriented at an oblique angle? You can modify the ``rotation`` tweenable that all polygons possess to change it:
```python
myoval = mainlayer.Actor(morpho.grid.ellipse(2+1j, 3, 1).set(
    rotation=2*pi/3
    ))
```
Success! The ellipse has been rotated by ``2*pi/3`` radians<sup>[</sup>[^2]<sup>]</sup>. However, you'll have noticed that our ellipse has moved to a significantly different position on the screen. This is because the ``rotation`` attribute applies the rotation with respect to the origin point, which is (0,0) here. But we can change that using the ``origin`` tweenable!

[^2]: ***Tip:*** Morpho has some convenience constants that facilitate converting between radians and degrees if you need to. They can be accessed by including the following line at the top of your code: ``from morpholib.tools.basics import *``. You can then convert degrees to radians like this: ``45*deg``, which can make it easier to specify a rotation angle when you have a value in degrees in mind, but the function or object expects radians: ``rotation = 120*deg``. You can similarly convert a radian value to degrees: ``pi/12*rad``, which is 15 degrees.

To do it, let's make a new ellipse that starts out centered at the origin of the plane:
```python
# Ellipse centered at (0,0) with semi-width 3,
# and semi-height 1.
myoval = mainlayer.Actor(morpho.grid.ellipse(0, 3, 1))
```
It's exactly the same ellipse as before, but it's now centered at the origin of the plane. But we can move the ellipse to a new location by setting its ``origin`` attribute afterward:
```python
myoval = mainlayer.Actor(morpho.grid.ellipse(0, 3, 1).set(origin=2+1j))
```
The ellipse should now display identically to how it originally did. But what if we apply a rotation now?
```python
myoval = mainlayer.Actor(morpho.grid.ellipse(0, 3, 1).set(
    origin=2+1j,
    rotation=2*pi/3
    ))

mation.play()
```
The ellipse rotates about its own local centerpoint! And so we get the rotated ellipse still centered at the point (2,1) that we started at.

An important thing to note about the transformation tweenables is that they are attributes stored *alongside* the other attributes. They do not modify them, and their effects apply after everything else. So if you examine the vertex list of our elliptical polygon, ``myoval.vertices``, they appear unchanged even after setting both the ``origin`` and the ``rotation`` tweenables. One way you can understand how they work is that the ellipse is, in a sense, first drawn at the origin of the plane with no rotation, but AFTER it is drawn, the transformation tweenables take effect to modify the appearance.

In addition to translating and rotating, you can also scale and shear, and in general apply any arbitrary linear transformation. To do that, use the ``transform`` tweenable.

As an example, let's create a square and then deform it into a parallelogram:
```python
# Initialize the shape to be the unit square
# and apply the linear transformation corresponding to the matrix
# [[  1  1]
#  [0.5  2]]
shape = mainlayer.Actor(morpho.grid.rect([0,1,0,1]).set(
    transform=np.array([[1,1],[0.5,2]])
    ))
shape.transform = np.array([[1,1],[0.5,2]])

mation.play()
```

You can also apply the ``origin`` and ``rotation`` tweenables in addition to the ``transform`` tweenable to get other composite effects. However, you will need to be mindful of the order of operations. The transformation tweenables are always applied in the order ``rotation``, ``transform``, ``origin``. This means the figure will be rotated first, then transformed according to the matrix given, and finally translated to its new origin point.

Remember how I said that the transformation tweenables are stored separately, or alongside, the other attributes? Meaning that modifying the transformation tweenables has no effect on the actual "raw" data comprising the figure? Well, there is a way to apply the transformation effects *directly* to the data as well. To do it, call the ``commitTransforms()`` method:
```python
# Ellipse centered at (0,0) with semi-width 3,
# and semi-height 1.
myoval = mainlayer.Actor(morpho.grid.ellipse(0, 3, 1).set(
    origin=2+1j,
    rotation=2*pi/3
    ))
print(myoval.first().origin, myoval.first().rotation)
myoval.first().commitTransforms()
print(myoval.first().origin, myoval.first().rotation)

mation.play()
```
Now, admittedly, after calling ``commitTransforms()``, the ellipse looks exactly the same as before, but if you examine its vertex list, you will find they have all been updated to new values based on the transformation tweenables, and meanwhile, the transformation tweenables have been reset to their base values (for ``origin`` and ``rotation``, those would both be ``0``).

Now you might be wondering what the point of that is, if the ellipse looks the same in either case. And indeed, I don't think you will often need to do this. But there are some animation differences between the two worth considering.

Let's say you want to animate an ellipse rotating 180 degrees counter-clockwise. Using the ``rotation`` tweenable, you might write some code that looks like this:
```python
myoval = mainlayer.Actor(morpho.grid.ellipse(0, 3, 1))

# Set rotation to pi radians after 1 second passes
myoval.newendkey(30).set(rotation=pi)

mation.play()
```
The animation plays exactly like we had hoped. But what if we had committed the rotation transformation?
```python
myoval = mainlayer.Actor(morpho.grid.ellipse(0, 3, 1))

# Set rotation to pi radians after 1 second passes
myoval.newendkey(30).set(rotation=pi)
myoval.last().commitTransforms()

mation.play()
```
That looks off! The ellipse kind of shrinks to a point before rebounding back to how it looked before. What's going on? What's happening is that by committing the rotation, every vertex of the final ellipse was moved to its antipodal point, and Morpho, knowing no better than to tween the two ellipses in the most direct way possible, tweened each starting vertex along a linear path to its final vertex, and the intersection of all these linear paths was at the origin.

Now in this case committing the rotation produced an undesirable effect, but there may be other times where you would like to animate something like a rotation of a figure, but perhaps you would like to conceal the rotation and instead have the animation play more like a morphing between the two. In such a case, committing the rotation might do the trick, as it sort of has the effect of "hiding" the rotation from Morpho's default tween methods.

### Transformation tweenables for ``Text`` and ``Image``

I've already mentioned that ``Text`` and ``Image`` figures support a ``rotation`` tweenable, but they also support a ``transform`` tweenable:
```python
ball = mainlayer.Actor(morpho.graphics.Image("./ball.png").set(
    width=2,
    transform=np.array([[1,1],[0,1]])  # Shear the ball
    ))

label = mainlayer.Actor(morpho.text.Text("sheared ball", pos=3j).set(
    transform=ball.first().transform  # Shear the label
    ))

mation.play()
```
However, note that neither ``Text`` nor ``Image`` possess an ``origin`` tweenable. This is because their origin point is already implicitly determined by setting their position attribute ``pos`` together with the alignment attributes ``anchor_x`` and ``anchor_y`` for ``Text``, or ``align`` for ``Image``.

## Color Tools

The submodule ``morpho.color`` contains a number of useful tools for specifying colors. It also contains tools for creating color gradients, but we won't cover that in this guide.

One useful tool is ``parseHexColor()`` which converts a standard HTML hexadecimal representation of a color into an RGB tuple:
```python
# The following are equivalent ways to define a pink color
pink = morpho.color.parseHexColor("ffc0cb")
pink = morpho.color.parseHexColor("0xffc0cb")
pink = morpho.color.parseHexColor(0xffc0cb)
```

## Miscellaneous Gadgets

Finally, the submodule ``morpho.gadgets`` contains a number of useful miscellaneous gadgets for making a handful of common animation effects.

### Crossouts

The function ``morpho.gadgets.crossout()`` can be used to make a crossout animation: basically where you draw a big red X in front of something incorrect. Its most basic usage is as follows:

```python
# Some text that's just begging to be crossed out
mistake = mainlayer.Actor(morpho.text.Text("2 + 2 = 5"))

# Generate an actor that does a crossout within
# the specified box
cross = mainlayer.Actor(morpho.gadgets.crossout([-2,2, -1,1]))

mation.play()
```

The main required input to ``crossout()`` is a 4-tuple (or list) describing the box region that the crossout animation should occupy. However, many figures possess a box() method that makes it easier to specify those boxes:
```python
# Some text that's just begging to be crossed out
mistake = mainlayer.Actor(morpho.text.Text("2 + 2 = 5"))

# Generate an actor that does a crossout within
# the specified box
cross = mainlayer.Actor(morpho.gadgets.crossout(mistake.first().box()))

mation.play()
```
> ***Tip:*** In version 0.7.1+, you can simply pass in a figure or actor into `crossout()` and it will automatically call its `box()` method to infer the correct box for you. The same holds true for `enbox()` and `encircle()`.

You can even add some padding to the box with the optional `pad` keyword:
```python
cross = mainlayer.Actor(morpho.gadgets.crossout(mistake.first().box(), pad=0.5))
```

In addition, there are other inputs you can pass in to further control how the animation looks:

```python
# Some text that's just begging to be crossed out
mistake = mainlayer.Actor(morpho.text.Text("2 + 2 = 5"))

# Generate an actor that does a crossout within
# the specified box
cross = mainlayer.Actor(morpho.gadgets.crossout(mistake.first().box(),
    pad=0.5, time=60, width=6, color=[1,1,0],
    transition=morpho.transitions.quadease
    ))

mation.play()
```

The crossout now takes a full 2 seconds (60 frames) to complete, the line segments are thicker (6 pixels), the color is now yellow, and the transition function has been set to ``quadease`` to make the animation look more organic.

### Enboxings

As opposed to crossing out something incorrect, you can also box in something that you want to highlight. A helpful tool for that is ``morpho.gadgets.enbox()``. Here's how to use it:

```python
# Some sample text to enbox
greeting = mainlayer.Actor(morpho.text.Text("Hello World!"))

boxer = mainlayer.Actor(morpho.gadgets.enbox(greeting.first().box(), pad=0.5))

mation.play()
```
And like with ``crossout()``, you can input optional parameters into ``enbox()`` to control the look and timing of the animation:

```python
# Some sample text to enbox
greeting = mainlayer.Actor(morpho.text.Text("Hello World!"))

boxer = mainlayer.Actor(morpho.gadgets.enbox(greeting.first().box(),
    pad=0.5, time=20, width=4, color=[0,1,0],
    transition=morpho.transitions.quadease
    ))

mation.play()
```

However, you can also change which corner the animation starts drawing from and which direction it travels:

```python
# Some sample text to enbox
greeting = mainlayer.Actor(morpho.text.Text("Hello World!"))

boxer = mainlayer.Actor(morpho.gadgets.enbox(greeting.first().box(),
    pad=0.5, time=20, width=4, color=[0,1,0],
    corner="NE",  # Start drawing from northeast corner
    CCW=False,  # Draw it in a clockwise direction
    transition=morpho.transitions.quadease
    ))

mation.play()
```

### Encirclings

And finally, similar to enboxings, you can also encircle a target with an elliptical curve using the ``encircle()`` gadget. It behaves pretty similarly to the others:

```python
# Something worth encircling
message = mainlayer.Actor(morpho.text.Text("Success!", color=[0.5,0.5,1]))

encirc = mainlayer.Actor(morpho.gadgets.encircle(message.first().box(),
    pad=0.5, time=45, width=8, color=[0,1,0],
    transition=morpho.transitions.quadease
    ))

mation.play()
```

And similar to ``enbox()``, you can control the starting point and draw direction of the encircling using the ``phase`` and ``CCW`` parameters:

```python
# Something worth encircling
message = mainlayer.Actor(morpho.text.Text("Success!", color=[0.5,0.5,1]))

encirc = mainlayer.Actor(morpho.gadgets.encircle(message.first().box(),
    pad=0.5, time=45, width=8, color=[0,1,0],
    phase=-pi/2, CCW=False,
    transition=morpho.transitions.quadease
    ))

mation.play()
```

The output of ``encircle()`` is actually a ``Path`` actor, which means the elliptical curve drawn is really composed of a lot of straight line steps. By default, an encircling contains 75 steps, but you can modify this if you want:

```python
# Something worth encircling
message = mainlayer.Actor(morpho.text.Text("Success!", color=[0.5,0.5,1]))

encirc = mainlayer.Actor(morpho.gadgets.encircle(message.first().box(),
    pad=0.5, time=45, width=8, color=[0,1,0],
    phase=-pi/2, CCW=False,
    steps=20,  # A much coarser path
    transition=morpho.transitions.quadease
    ))

mation.play()
```

> **Note:** Depending on the actual text string you're using, sometimes the bounding box does does not totally enclose the text (in particular if your text includes a lowercase "y"). This is a known issue which may be addressed at some point, but just be aware that it happens. If it bothers you, you can always increase the padding on the box until it truly encloses it, or just determine the box dimensions manually.
