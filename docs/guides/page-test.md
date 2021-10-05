---
layout: default
title: Morpho Guide -- Useful Figures and Gadgets
---

# Morpho Guide: Useful Figures and Gadgets

Last guide, we explored some basic figures like points, paths, and polygons. Now we'll look at some other useful figures like text, images, and arrows along with some handy gadgets which help to generate some of these figures in commonly used configurations.

> **Note:** To properly run the example code snippets in this guide, you should include the following lines at the top of your code:
> ```python
> import morpholib as morpho
> morpho.importAll()
> ```
> You will also need to place the two image files ``ball.png`` and ``oo.png`` into the same directory as your Python scripts. These image files can be downloaded [from here](https://github.com/morpho-matters/morpholib/tree/master/examples).

## Text

The ``Text`` figure allows you to display text in an animation. This figure can be accessed from the ``text`` submodule. The basic syntax to create one is as follows:

```python
mytext = morpho.text.Text("Hello World")
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

> ***Tip:*** All of the above attributes, except ``rotation``, can actually be specified as arguments during construction. So for example, you can do:
> ```python
> mytext = morpho.text.Text("Hello World", pos=3+4j, size=72, color=[0,1,0])
> ```

Most of these attributes are tweenable, meaning they can be interpolated in an actor. Alas, the ``text`` string attribute is not tweenable so you can't morph one text string into another, but there actually is a way to do it using the ``MultiText`` class (more on that later).

For now, let's see an example. Let's make our Hello World text bigger and color it red:

```python
mytext.size = 84
mytext.color = [1,0,0]

movie = morpho.Animation(mytext)
movie.play()
```

You can also change the actual text string of a text figure by modifying its ``text`` attribute:

```python
mytext.text = "Goodbye!"
mytext.size = 84
mytext.color = [1,0,0]

movie = morpho.Animation(mytext)
movie.play()
```

## Images

You can display PNG images using the ``Image`` class (found in the ``graphics`` submodule). The basic syntax is as follows:

```python
mypic = morpho.graphics.Image("path/to/image/file.png")
```

Though you can also initialize an Image figure using a separate already initialized Image:

```python
myotherpic = morpho.graphics.Image(mypic)
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

An important thing to note here is that ``width`` and ``height`` are specified in so-called "physical" units, which means relative to distances and lengths in the current view of the complex plane as opposed to pixels<sup>[[^1]]</sup>.

[^1]: Might be a good time for some more terminology: In Morpho, a "physical" quantity pretty much always means *relative to the local coordinate system of the layer's camera*. e.g. *physical width* or *physical coordinates*. This is in contrast to "pixel" or "screen" coordinates or quantities, which mean *relative to the pixels on the user's actual screen*. Morpho has tools to convert between the two. See the documentation for the methods ``morpho.physicalCoords()``, ``morpho.pixelCoords()``, ``morpho.physicalWidth()``, etc. for more info.

For example, in the standard [-5,5] x [-5*j*, 5*j*] view of the complex plane, setting ``width`` to 5 would mean the image would be about half as wide as the entire canvas when drawn (because 5 is half of the width of the entire view: ``5-(-5) = 10``). This convention makes it easier to set the sizes of images relative to other objects in the scene. It also means zooming the camera in and out will scale the image correctly relative to its surroundings. That is, the image behaves as if it is an actual "physical" object in the scene, as opposed to a sticker or a label floating above it.

Another thing to note is that by default, ``width`` and ``height`` are linked together, so modifying one modifies the other so that the image's aspect ratio is preserved. If you don't want this behavior, you can disable it by calling the method ``unlink()``:

```python
mypic.unlink()
mypic.width = 5   # These are now independent
mypic.height = 2  # of each other
```

Similar to ``Text`` figures, you can't properly tween two image figures with different source files, or at least not using the vanilla ``Image`` class. To do it, you'll have to use the ``MultiImage`` class.

## Multifigures

Both the ``Text`` class and the ``Image`` class have so-called "multifigure" versions called ``MultiText`` and ``MultiImage``. In most use cases, these variants behave exactly like their vanilla counterparts, but support a primitive morphing effect that allows you to more properly tween their normally untweenable contents.

To see what I mean, let's have one Text figure morph into another one with a different content string:

```python
message = morpho.text.MultiText("Hello World!")
message = morpho.Actor(message)
message.newendkey(30)         # Over the course of a second,
message.last().text = "Bye!"  # morph the text to say "Bye!"

movie = morpho.Animation(message)
movie.play()
```

You can achieve a similar effect with images. But to change one image to another requires using the ``newSource()`` method to define a new source PNG file:

```python
mypic = morpho.graphics.MultiImage("./ball.png")
mypic.width = 3
mypic = morpho.Actor(mypic)
mypic.newendkey(30)
mypic.last().newSource("./oo.png")

movie = morpho.Animation(message)
movie.play()
```

This works, but you might notice that the final image is distorted. This is because calling ``newSource()`` on its own leaves the previous aspect ratio unchanged. But it's easy to reset the aspect ratio to the new final image by calling either ``scaleByWidth()`` or ``scaleByHeight()``. For example:

```python
mypic = morpho.graphics.MultiImage("./ball.png")
mypic.width = 3
mypic = morpho.Actor(mypic)
mypic.newendkey(30)
mypic.last().newSource("./oo.png")
mypic.last().scaleByWidth()  # Rescale height while leaving width unchanged

movie = morpho.Animation(message)
movie.play()
```

The final image is now in the correct proportion. This was accomplished by rescaling the height while leaving the width fixed from the original. But you can do it the other way as well:

```python
mypic = morpho.graphics.MultiImage("./ball.png")
mypic.width = 3
mypic = morpho.Actor(mypic)
mypic.newendkey(30)
mypic.last().newSource("./oo.png")
mypic.last().scaleByHeight()  # Rescale width while leaving height unchanged

movie = morpho.Animation(message)
movie.play()
```

The final image is again in proper proportion, but this time it was done by rescaling the width while leaving the height unchanged from the original image.

Depending on how you interpret the phrase "scale by", the naming convention used by these methods might feel backward to you. And maybe you're right. But for what it's worth, here's how I read them: ``scaleByWidth()``, for example, means to scale the image *based on* the width: you're rescaling it while using the width as your reference.

> ***Tip:*** Since it's such a common procedure to immediately call either ``scaleByWidth()`` or ``scaleByHeight()`` after calling ``newSource()`` to specify a new image source, you can streamline it all into one line in the following way:
> ```python
> mypic.last().newSource("./oo.png").scaleByWidth()
> ```
> This is possible because the ``newSource()`` method actually returns the figure which called it (in this case, ``mypic.last()``), and so you can immediately string a second method call after it.
>
> If you want to be *really* concise, you can also make use of the fact that the ``newkey()`` and ``newendkey()`` methods return the newly created keyfigure, so you can condense even that part into a single line:
> ```python
> mypic.newendkey(30).newSource("./oo.png").scaleByWidth()
> ```

## Arrows

An arrow is just a line segment whose ends can be made pointy (mindblowing, I know). This figure can be accessed from the ``grid`` submodule. The basic syntax to create one is as follows:

```python
arrow = morpho.grid.Arrow(tail, head)
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
pt = morpho.grid.Point(0)
```
Next we'll make a Text figure labeling the point. Let's place it a bit below the location of our point. We'll use relative coordinates to define it so that if we want to go back in the code and change where the point's position is, our label will move accordingly:
```python
label = morpho.text.Text("Watch me carefully!", pos=pt.pos - 3j)
```
Now let's format it a little. We'll make it bigger, color it red, and give it center alignment:

```python
label.size = 48
label.color = [1,0,0]
label.anchor_x = 0
```

Now for the fun part. Let's make an arrow that grows from a position slightly above our text label and then points toward our Point figure. To do this, we'll start out by positioning both the head *and* tail of the arrow at a position slightly above the label:

```python
arrow = morpho.grid.Arrow()
arrow.tail = arrow.head = label.pos + 0.5j
```

Next we'll give it some formatting:

```python
arrow.headSize = 0  # Override default headSize of 25
arrow.width = 5
arrow.color = [1,1,1]  # Color it white
```

Now let's turn it into an actor and give it a modified keyframe at the 1 second (30 frame) mark. We'll move the arrow's head position to be slightly below the Point figure and grow the size of its tip:

```python
arrow = morpho.Actor(arrow)
arrow.newkey(30)  # New keyfigure at the 1 second mark
arrow.last().head = pt.pos - 0.5j
arrow.last().headSize = 25
```

And finally, let's package all three figures/actors into a single layer and play the animation!

```python
layer = morpho.Layer([pt, label, arrow])
movie = morpho.Animation(layer)
movie.play()
```

> ***Tip:*** The Path class also supports the ``headSize`` and ``tailSize`` attributes, which are set to 0 by default. So you can turn any path into a curved arrow by changing its ``headSize`` and ``tailSize``. The "head" of a path is considered the last vertex in the vertex sequence while the "tail" of a path is its first vertex.

### Other arrow tools

There are a few other methods/attributes of arrows that come in handy from time to time. First you can compute the length (distance between head and tail) of an arrow using the ``length`` attribute:
```python
print(arrow.length)
```
But you can also change its length too:
```python
arrow.length = 4
```
The way this is done is the tail of the arrow is held fixed and the head is moved along the original direction of the arrow until it is the specified distance away from the tail. So the distinction between the head and the tail of an arrow is more than just conceptual.

The ``angle`` attribute indicates the direction the arrow is pointing (tail-to-head) in terms of an absolute angle (in radians) measured counter-clockwise from the positive real axis. It can also be set similar to the ``length`` attribute.

```python
print(arrow.angle)
arrow.angle = math.pi/2
```

The ``unit()`` method returns a complex number representing the direction unit vector for the arrow (tail-to-head).
```python
print(arrow.unit())
```

## Helpful gadgets

There are a number of helpful functions and gadgets to assist in creating common figure constructions. We already looked at a few in the previous guide, but now we'll explore them in more detail and give a more comprehensive list of the available tools.

### More about ``line()``, ``rect()``, ``ellipse()``, and ``arc()``

The three functions ``line()``, ``rect()``, ``ellipse()``, and ``arc()`` can all be found in the ``grid`` submodule. They are accessible like this: ``morpho.grid.line()``

We actually already covered ``line()`` in the previous guide. So I won't repeat it here.

``rect()`` can be used to create a generic rectangle polygon. It takes exactly one input: a 4-tuple or list describing a box in the complex plane: ``[xmin,xmax,ymin,ymax]``. It will return a *generic* polygon figure with its four vertices set to describe the specified box. However, please remember that ``rect()`` returns a *generic* polygon (that is, all its other attributes beyond ``vertices`` will all be their default values), so you will need to modify its other attributes afterward to make it look a particular way.

Example:
```python
myrect = morpho.grid.rect([-3,3, -1,2])
myrect.width = 5
myrect.color = [1,0,0]
myrect.fill = [1,1,0]

movie = morpho.Animation(myrect)
movie.play()
```

Note you can also create a rectangular ``Path`` figure using ``rect()`` as well. Just call the Polygon method ``edge()`` after construction:
```python
myrect = morpho.grid.rect([-3,3, -1,2])
rectpath = myrect.edge()
```
or just in a single line like this:
```python
rectpath = morpho.grid.rect([-3,3, -1,2]).edge()
```

``ellipse()`` is used to construct a generic Polygon that looks like an ellipse. It takes three required parameters:
- ``z0``: Center of ellipse (complex number)
- ``a``: Horizontal radius (i.e. semi-width) in physical units
- ``b``: Vertical radius (i.e. semi-height) in physical units


Try it out:
```python
# Ellipse centered at (2,1) with semi-width 3,
# and semi-height 1.
myoval = morpho.grid.ellipse(2+1j, 3, 1)

movie = morpho.Animation(myoval)
movie.play()
```
And like before, this polygon is otherwise generic, so you will have to modify its style parameters afterward:
```python
# Ellipse centered at (2,1) with semi-width 3,
# and semi-height 1.
myoval = morpho.grid.ellipse(2+1j, 3, 1)
myoval.width = 5
myoval.color = [0,0,1]
myoval.fill = [0,0.6,0]
```
And if you want the Path describing its boundary, you can call ``edge()``:
```python
ovalpath = myoval.edge()
```

Note that ``ellipse()`` can also take two additional optional inputs:
- ``dTheta``: Angular separation between adjacent vertices of the polygon (in ***degrees***). Default: 5 degrees
- ``phase``: Angle (in ***degrees***) where the initial vertex of the polygon begins. Measured counter-clockwise from the positive real axis. Default: 0 degrees

I generally don't find much occasion to mess with these parameters, but they might be important in certain special cases. For example, ``phase`` might matter if you want to more precisely control how the ellipse morphs into a different polygon.

``arc()`` returns a ``Path`` figure in the shape of a circular arc that connects two complex numbers ``p`` and ``q`` which you specify with an arc of a specified angle.

Here's an example:
```python
# Connect the point -2-1j to the point 3+2j with
# an arc of angle pi/2 radians traveling counter-
# clockwise from the first to the second point.
myarc = morpho.grid.arc(-2-1j, 3+2j, pi/2)

movie = morpho.Animation(myarc)
movie.play()
```
Note that the arc travels *under* the line connecting the two points ``-2-1j`` and ``3+2j``. This is because the angle value we supplied, ``pi/2`` was *positive*. And so the arc will travel counter-clockwise from the first point toward the second. To reverse this behavior, you can either swap the order of the two points, or flip the sign of the angle:
```python
myarc = morpho.grid.arc(3+2j, -2-1j, pi/2)   # Two ways to reverse
myarc = morpho.grid.arc(-2-1j, 3+2j, -pi/2)  # the arc's direction
```
And once again, the output of ``arc()`` is a generic path, so to modify its appearance, you must set its attributes one at a time after construction:
```python
myarc = morpho.grid.arc(-2-1j, 3+2j, pi/2)
# Change style attributes
myarc.width = 8
myarc.color = [0,1,0]
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
mygrid = morpho.grid.mathgrid(
    view=[-3,3, -3,3],
    hcolor=[0,1,0], hwidth=5,
    hmidlines=4, vmidlines=4,
    BGgrid=False, axes=False
    )

movie = morpho.Animation(mygrid)
movie.play()
```

### ``realgraph()``

There is a special gadget that is designed specifically for creating the graph of a function *y* = *f*(*x*). It's called ``realgraph()`` and you can access it from the ``graph`` submodule:

``morpho.graph.realgraph()``

It takes three required inputs:
- ``f``: A real-to-real function whose graph you want.
- ``a``, ``b``: The left- and right-endpoints of the interval on which to graph.

Try it out:
```python
f = lambda x: x**2
fgraph = morpho.graph.realgraph(f, -2, 2)

movie = morpho.Animation(fgraph)
movie.play()
```
> **Note:** I used Python's ``lambda`` syntax to define the function *f*(*x*) = *x*<sup>2</sup>, but this is by no means required. You can input a python function defined in any way into ``realgraph()`` as long as it takes real number inputs in the interval you specify and outputs real numbers.

Depending on the function you're graphing, the path's resolution may need to be higher than the default. So just like with ``line()``, you can change the number of steps within the path by setting the optional argument ``steps``:
```python
# This looks awful
f1 = lambda x: 4*(1+math.sin(5*x))/2
fgraph1 = morpho.graph.realgraph(f1, -4, 4)

# This looks way better
f2 = lambda x: 4*(-1+math.sin(5*x))/2
fgraph2 = morpho.graph.realgraph(f2, -4, 4, steps=200)

movie = morpho.Animation(morpho.Layer([fgraph1, fgraph2]))
movie.play()
```
By default, ``steps`` equals 50.

The output of ``realgraph()`` is a Path figure, so you can modify its other attributes afterward just like with ``line()`` and ``arc()``. However, ``realgraph()`` happens to support three additional style parameters that let you control the basic appearance of the path in advance:
```python
f = lambda x: x**2
# Make graph thick, red, and semi-transparent
fgraph = morpho.graph.realgraph(
    f, -2, 2, width=10, color=[1,0,0], alpha=0.5
    )

movie = morpho.Animation(fgraph)
movie.play()
```

## Transformation Tweenables

Many (though not all) figures support one or more so-called "transformation tweenables". These are tweenable attributes with the names ``origin``, ``rotation``, or ``transform``, and can be used to, well, *transform* the appearance of the figure by translation, rotation, scaling, shearing, or other linear transformation.

To see why these might matter, let's consider the ellipse polygon we created earlier:
```python
# Ellipse centered at (2,1) with semi-width 3,
# and semi-height 1.
myoval = morpho.grid.ellipse(2+1j, 3, 1)

movie = morpho.Animation(myoval)
movie.play()
```
The ``ellipse()`` function is only capable of creating ellipses in one of two basic orientations: either having its long side parallel to the *x*-axis, or having its long side parallel to the *y*-axis. But what if you want to have the major and minor axes of the ellipse oriented at an oblique angle? You can modify the ``rotation`` tweenable that all polygons possess to change it:
```python
myoval = morpho.grid.ellipse(2+1j, 3, 1)
myoval.rotation = 2*pi/3
```
Success! The ellipse has been rotated by ``2*pi/3`` radians<sup>[[^2]]</sup>. However, you'll have noticed that our ellipse has moved to a significantly different position on the screen. This is because the ``rotation`` attribute applies the rotation with respect to the origin point, which is (0,0) here. But we can change that using the ``origin`` tweenable!

[^2]: ***Tip:*** Morpho has some convenience constants that facilitate converting between radians and degrees if you need to. They can be accessed by including the following line at the top of your code: ``from morpholib.tools.basics import *``. You can then convert degrees to radians like this: ``45*deg``, which can make it easier to specify a rotation angle when you have a value in degrees in mind, but the function or object expects radians: ``myoval.rotation = 120*deg``. You can similarly convert a radian value to degrees: ``dTheta=pi/12*rad``, or 120 degrees.

To do it, let's make a new ellipse that starts out centered at the origin of the plane:
```python
# Ellipse centered at (0,0) with semi-width 3,
# and semi-height 1.
myoval = morpho.grid.ellipse(0, 3, 1)

movie = morpho.Animation(myoval)
movie.play()
```
It's exactly the same ellipse as before, but it's now centered at the origin of the plane. But we can move the ellipse to a new location by setting its ``origin`` attribute afterward:
```python
myoval = morpho.grid.ellipse(0, 3, 1)
myoval.origin = 2+1j
```
The ellipse should now display identically to how it originally did. But what if we apply a rotation now?
```python
myoval = morpho.grid.ellipse(0, 3, 1)
myoval.origin = 2+1j
myoval.rotation = 2*pi/3
```
The ellipse rotates about its own local centerpoint! And so we get the rotated ellipse still centered at the point (2,1) that we started at.

An important thing to note about the transformation tweenables is that they are attributes stored *alongside* the other attributes. They do not modify them, and their effects apply after everything else. So if you examine the vertex list of our elliptical polygon, ``myoval.vertices``, they appear unchanged even after setting both the ``origin`` and the ``rotation`` tweenables. One way you can understand how they work is that the ellipse is, in a sense, first drawn at the origin of the plane with no rotation, but AFTER it is drawn, the transformation tweenables take effect to modify the appearance.

In addition to translating and rotating, you can also scale and shear, and in general apply any arbitrary linear transformation. To do that, use the ``transform`` tweenable.

As an example, let's create a square and then deform it into a parallelogram:
```python
# Initialize the shape to be the unit square
shape = morpho.grid.rect([0,1,0,1])
# Apply the linear transformation corresponding to the matrix
# [[  1  1]
#  [0.5  2]]
shape.transform = morpho.array([[1,1],[0.5,2]])

movie = morpho.Animation(shape)
movie.play()
```
> **Note:** The code above invokes the function ``morpho.array()``. It's recommended to use this function whenever you need to define a matrix or a vector. It's basically just a wrapper around ``numpy.array()``, but it has a few different properties, and usually ensures that the result will be compatible with other components of Morpho.

You can also apply the ``origin`` and ``rotation`` tweenables in addition to the ``transform`` tweenable to get other composite effects. However, you will need to be mindful of the order of operations here, which is worth summarizing now.

The transformation tweenables are always applied in the following order: ``rotation``, ``transform``, ``origin``

meaning the transformation effects are performed in the following order:

<p align="center">Rotate, Transform, Translate</p>

Remember how I said that the transformation tweenables are stored separately, or alongside, the other attributes? Meaning that modifying the transformation tweenables has no effect on the actual "raw" data comprising the figure? Well, there is a way to apply the transformation effects *directly* to the data as well. To do it, call the ``commitTransforms()`` method:
```python
# Ellipse centered at (0,0) with semi-width 3,
# and semi-height 1.
myoval = morpho.grid.ellipse(0, 3, 1)
myoval.origin = 2+1j
myoval.rotation = 2*pi/3
print(myoval.origin, myoval.rotation)
myoval.commitTransforms()
print(myoval.origin, myoval.rotation)

movie = morpho.Animation(myoval)
movie.play()
```
Now, admittedly, after calling ``commitTransforms()``, the ellipse looks exactly the same as before, but if you examine its vertex list, you will find they have all been updated to new values based on the transformation tweenables, and meanwhile, the transformation tweenables have been reset to their base values (for ``origin`` and ``rotation``, those would both be ``0``).

Now you might be wondering what the point of that is, if the ellipse looks the same in either case. And indeed, I don't think you will often need to do this. But there are some animation differences between the two worth considering.

Let's say you want to animate an ellipse rotating 180 degrees counter-clockwise. Using the ``rotation`` tweenable, you might write some code that looks like this:
```python
myoval = morpho.grid.ellipse(0, 3, 1)

# Turn into an actor so it can be animated
myoval = morpho.Actor(myoval)

# Set rotation to pi radians after 1 second passes
myoval.newendkey(30)
myoval.last().rotation = pi

movie = morpho.Animation(myoval)
movie.play()
```
The animation plays exactly like we had hoped. But what if we had committed the rotation transformation?
```python
myoval = morpho.grid.ellipse(0, 3, 1)

# Turn into an actor so it can be animated
myoval = morpho.Actor(myoval)

# Set rotation to pi radians after 1 second passes
myoval.newendkey(30)
myoval.last().rotation = pi

# Now commit the rotation
myoval.last().commitTransforms()

movie = morpho.Animation(myoval)
movie.play()
```
That looks off! The ellipse kind of shrinks to a point before rebounding back to how it looked before. What's going on? What's happening is that by committing the rotation, every vertex of the final ellipse was moved to its antipodal point, and Morpho, knowing no better than to tween the two ellipses in the most direct way possible, tweened each starting vertex along a linear path to its final vertex, and the intersection of all these linear paths was at the origin.

Now in this case committing the rotation produced an undesirable effect, but there may be other times where you would like to animate something like a rotation of a figure, but you would like to conceal the rotation and instead have the animation play more like a morphing between the two. In such a case, committing the rotation might do the trick, as it sort of has the effect of "hiding" the rotation from Morpho's default tween methods.

### Transformation tweenables for ``Text`` and ``Image``

I've already mentioned that ``Text`` and ``Image`` figures support a ``rotation`` tweenable, but they also support a ``transform`` tweenable:
```python
ball = morpho.graphics.Image("./ball.png")
ball.width = 2
# Shear the ball
ball.transform = morpho.array([[1,1],[0,1]])

label = morpho.text.Text("sheared ball", pos=3j)
# Shear the label
label.transform = ball.transform.copy()

movie = morpho.Animation(morpho.Layer([ball, label]))
movie.play()
```
However, note that neither ``Text`` nor ``Image`` possess an ``origin`` tweenable. This is because their origin point is already implicitly determined by setting their position attribute ``pos`` together with the alignment attributes ``anchor_x`` and ``anchor_y`` for ``Text``, or ``align`` for ``Image``.

## Miscellaneous Gadgets

Finally, the submodule ``morpho.gadgets`` contains a number of useful miscellaneous gadgets for making a handful of common animation effects.

### Crossouts

The function ``morpho.gadgets.crossout()`` can be used to make a crossout animation: basically where you draw a big red X in front of something incorrect. Its most basic usage is as follows:

```python
# Some text that's just begging to be crossed out
mistake = morpho.text.Text("2 + 2 = 5")

# Generate an actor that does a crossout within
# the specified box
cross = morpho.gadgets.crossout([-2,2, -1,1])

movie = morpho.Animation(morpho.Layer([mistake, cross]))
movie.play()
```

The main required input to ``crossout()`` is a 4-tuple (or list) describing the box region that the crossout animation should occupy. However, there are other inputs you can pass in to further control how the animation looks:

```python
# Some text that's just begging to be crossed out
mistake = morpho.text.Text("2 + 2 = 5")

# Generate an actor that does a crossout within
# the specified box
cross = morpho.gadgets.crossout([-2,2, -1,1],
    time=60, width=6, color=[1,1,0],
    transition=morpho.transitions.quadease
    )

movie = morpho.Animation(morpho.Layer([mistake, cross]))
movie.play()
```

The crossout now takes a full 2 seconds (60 frames) to complete, the line segments are thicker (6 pixels), the color is now yellow, and the transition function has been set to ``quadease`` to make the animation look more organic.

### Enboxings

As opposed to crossing out something incorrect, you can also box in something that you want to highlight. A helpful tool for that is ``morpho.gadgets.enbox()``. Here's how to use it:

```python
# Some sample text to enbox
greeting = morpho.text.Text("Hello World!")

boxer = morpho.gadgets.enbox([-3,3, -1,1])

movie = morpho.Animation(morpho.Layer([greeting, boxer]))
movie.play()
```
And like with ``crossout()``, you can input optional parameters into ``enbox()`` to control the look and timing of the animation:

```python
# Some sample text to enbox
greeting = morpho.text.Text("Hello World!")

boxer = morpho.gadgets.enbox([-3,3, -1,1],
    time=20, width=4, color=[0,1,0],
    transition=morpho.transitions.quadease
    )

movie = morpho.Animation(morpho.Layer([greeting, boxer]))
movie.play()
```

However, you can also change which corner the animation starts drawing from and which direction it travels:

```python
# Some sample text to enbox
greeting = morpho.text.Text("Hello World!")

boxer = morpho.gadgets.enbox([-3,3, -1,1],
    time=20, width=4, color=[0,1,0],
    corner="NE",  # Start drawing from northeast corner
    CCW=False,  # Draw it in a clockwise direction
    transition=morpho.transitions.quadease,
    )

movie = morpho.Animation(morpho.Layer([greeting, boxer]))
movie.play()
```

### Encirclings

And finally, similar to enboxings, you can also encircle a target with an elliptical curve using the ``encircle()`` gadget. It behaves pretty similarly to the others:

```python
# Something worth encircling
message = morpho.text.Text("Success!", color=[0.5,0.5,1])

encirc = morpho.gadgets.encircle([-3,3, -1,1],
    time=45, width=8, color=[0,1,0],
    transition=morpho.transitions.quadease
    )

movie = morpho.Animation(morpho.Layer([message, encirc]))
movie.play()
```

And similar to ``enbox()``, you can control the starting point and draw direction of the encircling using the ``phase`` and ``CCW`` parameters:

```python
# Something worth encircling
message = morpho.text.Text("Success!", color=[0.5,0.5,1])

encirc = morpho.gadgets.encircle([-3,3, -1,1],
    time=45, width=8, color=[0,1,0],
    phase=-pi/2, CCW=False,
    transition=morpho.transitions.quadease
    )

movie = morpho.Animation(morpho.Layer([message, encirc]))
movie.play()
```

The output of ``encircle()`` is actually a ``Path`` actor, which means the elliptical curve drawn is really composed of a lot of straight line steps. By default, an encircling contains 75 steps, but you can modify this if you want:

```python
# Something worth encircling
message = morpho.text.Text("Success!", color=[0.5,0.5,1])

encirc = morpho.gadgets.encircle([-3,3, -1,1],
    time=45, width=8, color=[0,1,0],
    phase=-pi/2, CCW=False,
    steps=20,  # A much coarser path
    transition=morpho.transitions.quadease
    )

movie = morpho.Animation(morpho.Layer([message, encirc]))
movie.play()
```

### Auto generating boxes

All three of the gadgets we just saw require you to input a box region of the complex plane as a standard 4-tuple/list ``(xmin,xmax,ymin,ymax)``, so you might be wondering how you determine the dimensions of this box. Honestly, sometimes it's just a matter of eyeballing it and pure trial and error, though you can also make use of a feature called a "locator layer" to help you identify the coordinates of particular points on screen (more on that in the next guide). However, since needing a bounding box for a ``Text`` or ``Image`` figure is pretty common, there is a function to facilitate finding it. It's called, simply enough, ``box()`` and it's a method of both the ``Text`` and ``Image`` classes, although it's easiest to use for the ``Image`` class.

The ``box()`` method just returns the 4-element list describing the bounding box of the image (before any transformations are applied). Here's an example usage:

```python
ball = morpho.graphics.Image("./ball.png")
boxer = morpho.gadgets.enbox(ball.box())

movie = morpho.Animation(morpho.Layer([ball, boxer]))
movie.play()
```

As you can see, the bounding box is drawn tightly around the ball image. However, if you're using the ``enbox()`` gadget to highlight a figure, you probably don't want the box to be super tight. To give it a little padding, you can supply an optional ``pad`` parameter to the ``box()`` method:

```python
ball = morpho.graphics.Image("./ball.png")
# Draw bounding box with 0.25 units of padding on all sides
boxer = morpho.gadgets.enbox(ball.box(pad=0.25))

movie = morpho.Animation(morpho.Layer([ball, boxer]))
movie.play()
```

Something similar can be done with a ``Text`` figure, but it's a little more complicated owing to the fact that ``Text`` figures are not *physical* in the same way images are. What I mean is that the size of a ``Text`` figure is not in physical units, but a unit system derived from pixel coordinates. That means ``Text`` figures look the same even after a camera zoom. So the physical bounding box of a ``Text`` figure will depend on the current view of the complex plane you're looking at, and so you'll have to pass in the current viewbox of the scene as well as the dimensions of the display window in order to compute its physical bounding box.

Here's one way to do it:

```python
mytext = morpho.text.Text("Hello World!")

# The default view and window dimensions of an
# animation are [-5,5]x[-5j,5j] and 600x600 pixels.
# Supply both of these to the box() method.
box = mytext.box([-5,5, -5,5], (600,600), pad=0.25)
boxer = morpho.gadgets.enbox(box)

movie = morpho.Animation(morpho.Layer([mytext, boxer]))
movie.play()
```

> **Note:** Depending on the actual text string you're using, sometimes the bounding box does does not totally enclose the text (in particular if your text includes a lowercase "y"). This is a known issue which may be addressed at some point, but just be aware that it happens. If it bothers you, you can always increase the padding on the box until it truly encloses it, or just determine the box dimensions manually.

There's actually a slightly cleaner way to do this which doesn't require hard-coding the actual viewbox and window dimensions or knowing them in advance, but that's best discussed after we've talked about layer merging and the typical workflow I use to create more complex animations. But that's a story for another guide.
