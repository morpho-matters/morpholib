---
layout: default
title: Morpho Guide -- Basics
---

# Morpho Guide: Basics

> **Note:** This guide is only for Morpho 0.7.0+. For older versions, see [this guide](https://morpho-matters.github.io/morpholib/guides/old/basic-guide).

## Importing Morpho

Once Morpho is installed, you can import the entire library by including the following code at the top of your script:

```python
import morpholib as morpho
morpho.importAll()
```

You can then test if everything's working properly by playing the sample animation:

```python
import morpholib as morpho
morpho.importAll()

morpho.sample.play()
```

## Hello World

Let's hit the ground running by making a quick, simple animation of a point moving through space. We'll go over how it all works here later on. Here's how the code might look:
```python
import morpholib as morpho
morpho.importAll()

mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)

point = mainlayer.Actor(morpho.grid.Point().set(pos=-3))
point.newendkey(30).set(pos=3)

mation.play()
```
Any animation in Morpho involves at least *three* things: an *Actor* (the thing being animated), a *Layer* that contains the actor, and an *Animation* object to contain the layer(s). The general workflow is to define the layers and animation object at the top of the code, and in the main body create Actors for the layer(s) and then manipulate them over time to define animations. Now let's get a better understanding of how it all works.

## Figures

The fundamental objects in Morpho are called *Figures*. A figure is basically anything that supports being drawn and interpolated (meaning in an animation that it can be smoothly transformed into another figure of the same type). Anything that appears on screen during an animation is a figure. This includes curves, polygons, text, etc.

By themselves, figures are static entities representing the state of an animated entity at a specific point in time. But when multiple figures of the same type are assembled together on a common timeline, the collective object they form is called an *Actor*, and Morpho animates the actor by smoothly interpolating between key figures in the actor's timeline. We'll get more into how this works later on.

Now, every figure comes with its own particular set of *attributes* which determine its state and what the figure looks like when drawn. For example: position, color, size, rotation, etc. These attributes are common to a given figure type, but figures of different types can have different attributes (for example, a *Point* figure will have some attributes that a *Path* figure does not possess and vice-versa).

### Points

To get a sense of how to make and manipulate a figure, let's make a *Point* figure. But first we must setup the layer and animation objects:
```python
import morpholib as morpho
morpho.importAll()

mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)
```
(This header should precede all future example code shown in this guide.)

Then a point can be created within `mainlayer` using this syntax:
```python
mypoint = mainlayer.Actor(morpho.grid.Point())
```

This will create a `Point` figure in its default state. To actually view it now, we have to tell Morpho to play the animation it's part of:
```python
mypoint = mainlayer.Actor(morpho.grid.Point())

mation.play()
```

You should see a red dot in the middle of a black background.

Let's change what it looks like. How about we make the point 50 pixels wide. We can do that by invoking the Point figure's `set()` method immediately after creation and change its `size` attribute:
```python
# Make the point 50 pixels wide
mypoint = mainlayer.Actor(morpho.grid.Point().set(size=50))

mation.play()
```
You can also modify multiple attributes with the `set()` method. For example, we can also color it green, and give it a thick white border:
```python
mypoint = mainlayer.Actor(morpho.grid.Point().set(
    size=50,        # Diameter in pixels
    fill=[0,1,0],   # Color in RGB, where 0 is min and 1 is max
    color=[1,1,1],  # Border color
    strokeWeight=5  # Border thickness in pixels
    ))

mation.play()
```

Let's also change where it's located. Let's move it to the position (3,4). To do that, we modify the point's ``pos`` attribute.

Note that in Morpho, positions in 2D space are almost always specified as complex numbers where the real part corresponds to the x-coordinate and the imaginary part is the y. So to move our point actor to the position (3,4), we'd specify it like this:
```python
mypoint = mainlayer.Actor(morpho.grid.Point().set(
    pos=3+4*1j,     # Position as a complex number
    size=50,        # Diameter in pixels
    fill=[0,1,0],   # Color in RGB, where 0 is min and 1 is max
    color=[1,1,1],  # Border color
    strokeWeight=5  # Border thickness in pixels
    ))

mation.play()
```
Note that in Python, the imaginary unit is represented with `j`, not `i`.

> **Note:** You can also specify a complex number in Python with the notation ``3 + 4j``, but doing ``3 + 4*1j`` is safer if you're new to the syntax since it works even when the imaginary component is a variable instead of a literal. You can also use the syntax ``complex(3,4)`` if you prefer.

We can also make the point semi-transparent. To do so, modify the ``alpha`` attribute:
```python
mypoint = mainlayer.Actor(morpho.grid.Point().set(
    pos=3+4*1j,     # Position as a complex number
    size=50,        # Diameter in pixels
    fill=[0,1,0],   # Fill color in RGB, where 0 is min and 1 is max
    color=[1,1,1],  # Border color
    alpha=0.5,      # Value from 0 to 1 where 0 = invisible, 1 = opaque
    strokeWeight=5  # Border thickness in pixels
    ))

mation.play()
```
The ``alpha`` attribute is shared by many figures and is useful for making figures fade in and fade out.

### Paths

A *Path* is another type of Figure. A *Path* is basically a sequence of line segments connected end to end, but by increasing the number of vertices, they can approximate curves. A *Path* figure can be created like this:
```python
mypath = mainlayer.Actor(morpho.grid.Path(seq))
```

where ``seq`` is a list of complex numbers denoting the vertex sequence for the path. For example, let's make a path in the shape of a diamond whose corners are located on the coordinate axes 3 units away from the origin and see what it looks like:
```python
mypath = mainlayer.Actor(morpho.grid.Path([3, 3*1j, -3, -3*1j]))

mation.play()
```

As we requested, the path ends at the point *-3j*. We can close the loop by appending the starting vertex to the input sequence, but the *Path* class already provides a way to do this automatically. We can call its `close()` method like this:
```python
mypath = mainlayer.Actor(morpho.grid.Path([3, 3*1j, -3, -3*1j]).close())

mation.play()
```

Like points, paths also support a variety of attributes modifying their visual appearance. These include ``color``, ``alpha``, and ``width``. For example, let's color the path blue and make it thicker:
```python
mypath = mainlayer.Actor(morpho.grid.Path([3, 3*1j, -3, -3*1j]).close().set(
    color=[0,0,1],  # Make the path blue
    width=5         # Make the path 5 pixels thick
    ))

mation.play()
```

### Built-in Paths

Although you can define a path explicitly by enumerating its vertex sequence, this is seldom done in practice unless you want to make a very short polygonal path. To make a curved path appear, we need many more vertices, and Morpho provides several tools to construct them.

#### Lines

The first tool is the ``line()`` function. Here's an example of how to use it:

```python
# Make a linear path connecting -2-3j to 1+4j
myline = mainlayer.Actor(morpho.grid.line(-2-3*1j, 1+4*1j))
```

Admittedly, this is visually the same as simply doing ``morpho.grid.Path([-2-3*1j, 1+4*1j])``, but the difference is the line actually consists of about 50 vertices. This is useful if you want to later transform the line into a curve (more on that later). The number of steps to take between the starting and ending vertices can be specified using the optional argument ``steps``:

```python
myline = mainlayer.Actor(morpho.grid.line(-2-3*1j, 1+4*1j, steps=100))
```

#### Ellipses

You can also make elliptical paths in a similar way:

```python
# Make an elliptical path centered at 1+1j with
# x-radius 3 and y-radius 1
myoval = mainlayer.Actor(morpho.grid.ellipse(1+1j, 3, 1).edge())
```
> **Note:** The method ``edge()`` is called because ``ellipse()`` actually returns a *Polygon* figure (more on them later). Calling ``edge()`` returns the *Path* figure representing the ellipse's outer edge.

By default, the angular separation between adjacent vertices is 5 degrees, but this can also be changed:

```python
myoval = mainlayer.Actor(morpho.grid.ellipse(1+1j, 3, 1, dTheta=10*deg))
# (This requires the constant "deg" to be imported from morpholib.tools.basics)
```

#### Grids

A very common use of paths is to construct grids. Morpho provides a built-in function to generate one. Let's make a grid that spans the rectangle ``[-5,5] x [-4j, 4j]``. Here's how:

```python
mygrid = mainlayer.Actor(morpho.grid.mathgrid(
    view=[-5,5, -4,4],  # read this as [xmin, xmax, ymin, ymax]
    dx=1, dy=1          # Distance between major x and y tick marks
    ))
```

The colors of the horizontal and vertical lines can be altered by supplying the optional arguments ``hcolor=[R,G,B]`` and ``vcolor=[R,G,B]`` to the ``mathgrid()`` function.

By default it also includes minor grid lines exactly halfway between every two major grid lines, but these can be disabled by including the arguments ``hmidlines=0`` and ``vmidlines=0``. The colors of the minor grid lines can also be changed with the arguments ``hmidColor`` and ``vmidColor``.

> **Note:** Technically the figure ``mathgrid()`` returns is not a path, but a collection of paths packaged together into a type of figure called a *Frame*. But don't worry about that now.

### Polygons

There is also a *Polygon* figure. This is a lot like the *Path* figure, except that the boundary is always closed and you can fill the interior with color.

```python
mypoly = mainlayer.Actor(morpho.grid.Polygon([3, 3*1j, -3, -3*1j]).set(
    width=5,        # Border is 5 pixels thick
    color=[1,1,0],  # Border color is yellow
    fill=[1,0,0]    # Fill color is red
    ))
```

> **Note:** *Path* figures can also be filled with color, but for it to appear, you must set the Path's `alphaFill` attribute to 1, since by default a Path's fill is invisible.


## Actors

So far we've just been dealing with static figures. Now let's animate them!

Animation in Morpho primarily takes the form of smooth interpolation between a starting figure and an ending figure over a certain duration. This process is called *tweening* and is accomplished thru an object called an *Actor*.

As mentioned briefly before, *Actors* are composite objects made up of multiple figures placed on a timeline. We've actually been creating them all along, every time we invoked `mainlayer.Actor()`, in order to even view our figures, but all those Actors have just consisted of a single figure, and so there was nothing to animate. To bring these actors to life, we need to add additional, different figures of the same type to their timelines. We can do this with the `newendkey()` actor method.

To see how it works, let's go back to our original *Point* actor and add a new figure to its timeline. We can do it like this:
```python
mypoint = mainlayer.Actor(morpho.grid.Point().set(
    pos=3+4*1j,     # Position as a complex number
    size=50,        # Diameter in pixels
    fill=[0,1,0],   # Fill color in RGB, where 0 is min and 1 is max
    color=[1,1,1],  # Border color
    alpha=0.5,      # Value from 0 to 1 where 0 = invisible, 1 = opaque
    strokeWeight=5  # Border thickness in pixels
    ))
mypoint.newendkey(30)
```

This creates a copy of the original initial figure, but located 30 frames later on its timeline.

> **Note:** All references to time and duration in Morpho are always in units of frames of animation. This is translated into actual units of time like seconds in the *Animation* class where you can specify the framerate (more on that later). By default, the framerate is 30 frames per second.

To make this actor come alive, we now modify the newly created future figure by chaining the `set()` method after the `newendkey()` call:
```python
mypoint.newendkey(30).set(pos=0)
```
This works because the `newendkey()` method returns the new figure it creates. We then modify that returned new figure by calling its `set()` method. If we now play the animation, we should now see the point move from the coordinates (3,4) to the origin (0,0):
```python
mypoint = mainlayer.Actor(morpho.grid.Point().set(
    pos=3+4*1j,     # Position as a complex number
    size=50,        # Diameter in pixels
    fill=[0,1,0],   # Fill color in RGB, where 0 is min and 1 is max
    color=[1,1,1],  # Border color
    alpha=0.5,      # Value from 0 to 1 where 0 = invisible, 1 = opaque
    strokeWeight=5  # Border thickness in pixels
    ))
mypoint.newendkey(30).set(pos=0)

mation.play()
```

A note on terminology: the individual figures we specify in an actor's timeline are known as *keyfigures* or *keys* and their locations on the timeline are called *keyframes* (or sometimes *keyindices*), following the terminology from the animation industry. Hence the `newendkey()` method is so-called because it creates a new ending keyfigure. On the other hand, the interpolated figures Morpho generates between keyfigures during an animation are called *tweened figures*.

From here, we can continue adding `newendkey()` calls to add more keyfigures to `mypoint`'s timeline to make it do all kinds of things:
```python
mypoint.newendkey(30).set(pos=0)  # Move to origin
mypoint.newendkey(30).set(size=20, fill=[1,0,0], alpha=1)  # Get smaller, change color, make opaque
mypoint.newendkey(30)  # Do nothing, just wait a second
mypoint.newendkey(20).set(pos=-3)  # Move to (-3,0) in 20 frames (2/3 sec)
```

You can optionally pass in a *Figure* object itself into `newendkey()` in addition to the frame duration. When this is done, instead of creating a new keyfigure that is a copy of the latest keyfigure, the new keyfigure will be taken to be the supplied figure:
```python
mypoint.newendkey(30, morpho.grid.Point())  # Turn into a default Point figure
```

### Accessing Keyfigures

Keyfigures can be accessed and modified after creation with a few handy methods.

#### `first()` and `last()`

The `first()` and `last()` methods can be used to grab the current earliest and latest keyfigures in an actor's timeline.
```python
mypoint = mainlayer.Actor(morpho.grid.Point().set(
    size=50,        # Diameter in pixels
    fill=[0,1,0],   # Fill color in RGB, where 0 is min and 1 is max
    color=[1,1,1],  # Border color
    strokeWeight=5  # Border thickness in pixels
    ))
mypoint.newendkey(30)

# Change initial position (but not final), so the point now moves
# from (3,4) to (0,0) since (0,0) is the default position.
mypoint.first().set(pos=3+4*1j)

# Change final keyfigure's fill color to yellow
mypoint.last().set(fill=[1,1,0])
```

These methods can also be handy to return an actor to a previous state. For example, say we want the animation to finish by having the point return to its original initial state. We can do that easily by passing in a copy of the initial keyfigure into `newendkey()`:
```python
mypoint.newendkey(30, mypoint.first().copy())
```
> ***CAUTION!*** Be sure to remember to include the ``copy()`` method! Forgetting to do so can sometimes cause two keyfigures to become linked, so changing the attributes of one will influence the other. This can lead to considerable confusion in debugging your code.

Alternatively, you can also use the properties `beg` and `fin` to access the first and last keyfigures, but these also allow you to replace those figures by reassigning them:
```python
mypoint = mainlayer.Actor(morpho.grid.Point().set(
    size=50,        # Diameter in pixels
    fill=[0,1,0],   # Fill color in RGB, where 0 is min and 1 is max
    color=[1,1,1],  # Border color
    strokeWeight=5  # Border thickness in pixels
    ))
mypoint.newendkey(30)

# Replace initial keyfigure with a default Point figure
mypoint.beg = morpho.grid.Point()

# Replace final keyfigure with a new Point figure
mypoint.fin = morpho.grid.Point().set(
    pos=3+4*1j,
    size=25,
    fill=[1,1,1]
    )
```

#### The `key[]` property

The `key[]` property can be used to access or replace any keyfigure in the timeline:
```python
mypoint = mainlayer.Actor(morpho.grid.Point().set(
    pos=3+4*1j,     # Position as a complex number
    size=50,        # Diameter in pixels
    fill=[0,1,0],   # Fill color in RGB, where 0 is min and 1 is max
    color=[1,1,1],  # Border color
    alpha=0.5,      # Value from 0 to 1 where 0 = invisible, 1 = opaque
    strokeWeight=5  # Border thickness in pixels
    ))
mypoint.newendkey(30).set(pos=0)  # Move to origin
mypoint.newendkey(30).set(size=20, fill=[1,0,0], alpha=1)  # Get smaller, change color, make opaque
mypoint.newendkey(30)  # Do nothing, just wait a second
mypoint.newendkey(20).set(pos=-3)  # Move to (-3,0) in 20 frames (2/3 sec)


mypoint.key[1].set(fill=[0,0,1])  # Second keyfigure color is now blue
mypoint.key[-2].set(alpha=0)  # Make second-to-last keyfigure fade to invisibility
mypoint.key[2] = morpho.grid.Point()  # Third keyfigure is now a default Point.
```
Note that, just like lists in Python, the initial keyfigure corresponds to `key[0]`, NOT `key[1]`, and negative indices will be interpreted cyclically, allowing you to access keys from last to first.


### Creating Intermediate Keyfigures

You can also specify a *negative* duration into `newendkey()` to create a new keyfigure a certain number of frames *BEFORE* the current final keyfigure. However, when this is done, instead of merely creating a copy of the final keyfigure, the new keyfigure created will be taken to be the intermediate figure obtained by *tweening* the two keyfigures surrounding the new keyfigure. This can change how the animation will behave.

Here's an example: Say we have a point start at the origin and move to (3,4) over the course of 2 seconds while also growing and changing its color:
```python
mypoint = mainlayer.Actor(morpho.grid.Point().set(
    pos=0,  # 0 is default, but it's nice to be explicit
    size=20,
    fill=[1,0,0]
    ))
mypoint.newendkey(60).set(pos=3+4*1j, size=50, fill=[0,1,0])
```
But now let's say that we want the point to first take a detour to (3,0) before moving to (3,4). We can add an intermediate keyfigure 30 frames *before* the current final keyfigure and change its position to `3`:
```python
mypoint = mainlayer.Actor(morpho.grid.Point().set(
    pos=0,  # 0 is default, but it's nice to be explicit
    size=20,
    fill=[1,0,0]
    ))
mypoint.newendkey(60).set(pos=3+4*1j, size=50, fill=[0,1,0])
mypoint.newendkey(-30).set(pos=3)
```
But note how the point already begins growing and changing its color *on its way* to (3,0). This is because the new keyfigure we created was taken to be the the intermediate "*tweened*" figure between the first and last keyfigures whose position attribute we modified to be `3`. If we instead set this up more straightforwardly, the point wouldn't start changing its size or color *UNTIL* it had reached (3,0):
```python
mypoint = mainlayer.Actor(morpho.grid.Point().set(
    pos=0,  # 0 is default, but it's nice to be explicit
    size=20,
    fill=[1,0,0]
    ))
mypoint.newendkey(30).set(pos=3)
mypoint.newendkey(30).set(pos=3+4*1j, size=50, fill=[0,1,0])
```
So it's worth remembering that creating intermediate keyfigures can sometimes help you pull off animations that would be hard to create otherwise.

> ***Tip:*** Here are some more details about how keyfigure creation works, if you want to know: The general rule for keyfigure creation is if the new keyfigure is *ahead* of all existing keyfigures, the new keyfigure will be a copy of the latest already existing keyfigure. If a new keyfigure is created *between* two existing keyfigures, the new keyfigure will be defined by tweening the two surrounding keyfigures. Finally, if a new keyfigure is created *before* all existing keyfigures (or is the first keyfigure to be created in an empty timeline), the new keyfigure will be the default figure (like calling ``Point()`` with no optional arguments). However, all of this behavior is overridden if you instead pass in a figure to the `newendkey()` method, e.g. `mypoint.newendkey(-30, morpho.grid.Point().set(pos=-2))`

### Transitions

I suppose our animations have been looking fine as far as they go, but they feel a little mechanical, don't they? It would be nice if we could make the transitions between keyframes a little more organic, such as by having it accelerate and decelerate as it leaves and arrives at keyframes. This can be accomplished by setting a so-called *transition* or *transition function*.

To change the transition of *all* movements of the actor, we should set the transition function to the *initial* keyfigure *before* creating any of the future keyfigures. This will cause the transition function to propagate to all future keyfigures as they are created. Built-in transition functions can be found in the ``morpho.transitions`` submodule, and a good one for this purpose is ``quadease`` (short for "quadratic easing"):

```python
mypoint = mainlayer.Actor(morpho.grid.Point().set(
    pos=3+4*1j,     # Position as a complex number
    size=50,        # Diameter in pixels
    fill=[0,1,0],   # Fill color in RGB, where 0 is min and 1 is max
    color=[1,1,1],  # Border color
    strokeWeight=5, # Border thickness in pixels
    transition=morpho.transitions.quadease  # Quadease transition
    ))
mypoint.newendkey(30).pos = 0
```
The point should now move to the origin in more fluid manner.

> ***Tip:*** If you expect to use a certain transition function for almost all tweens for all actors, you can change the default transition function Morpho uses on all actors by including the line
```python
morpho.transition.default = my_transition  # e.g. morpho.transitions.quadease
```
at the top of your code. The normal default transition is ``morpho.transitions.uniform``.

### Applying Functions to Figures

Let's do another example this time using a grid. First we'll make a standard grid spanning the full canvas:

```python
grid = mainlayer.Actor(morpho.grid.mathgrid(
    view=[-5,5, -5,5],  # read this as [xmin, xmax, ymin, ymax]
    dx=1, dy=1  # Distance between major x and y tick marks
    ))
```

We'll now transform this grid using a function and assign the resulting figure to a new variable `fgrid`. To do this, use the ``fimage()`` method:
```python
fgrid = grid.last().fimage(lambda z: z**2/10)
```

``fimage()`` stands for "function image" and refers to taking the "image" of a path or grid in the mathematical set theory sense: applying a function to every vertex. In the above code, we are applying the function *f*(*z*) = *z*<sup>2</sup>/10 to every vertex in the grid and putting the resulting image grid in a new variable called ``fgrid``.

Let's now make an animation where our starting grid transforms into the image grid. To do that, we'll turn our ``fgrid`` image grid into a new keyfigure of the `grid` actor:

```python
grid = mainlayer.Actor(morpho.grid.mathgrid(
    view=[-5,5, -5,5],  # read this as [xmin, xmax, ymin, ymax]
    dx=1, dy=1  # Distance between major x and y tick marks
    ))

fgrid = grid.last().fimage(lambda z: z**2/10)
grid.newendkey(60, fgrid)

mation.play()
```

Note this can also be specified without creating the intermediate variable `fgrid`, though at the possible cost of making the code a little harder to read:
```python
grid = mainlayer.Actor(morpho.grid.mathgrid(
    view=[-5,5, -5,5],  # read this as [xmin, xmax, ymin, ymax]
    dx=1, dy=1  # Distance between major x and y tick marks
    ))
grid.newendkey(60, grid.last().fimage(lambda z: z**2/10))

mation.play()
```

## Layers and Cameras

So far we've just been animating one actor at a time, but an animation typically consists of many actors grouped together within a structure called a *Layer* which has its own local camera (i.e. coordinate system). We've actually been using a layer all throughout this guide (it was called `mainlayer`), but now we'll pay more direct attention to what it is and what you can do with it.

### Initialization

Layers are generally the first objects defined when making an animation. In our case, we just have one layer, called `mainlayer` which we initialized at the beginning and assigned to our *Animation* object `mation`:
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)
```
However, you can create and assign as many layers as you want, which can be useful in more complex animations where you might want to have different coordinate systems (cameras) for different actors.
```python
mainlayer = morpho.Layer()
layer2 = mainlayer.copy()
layer3 = mainlayer.copy()
mation = morpho.Animation([mainlayer, layer2, layer3])
```

### Adding Actors to a Layer

The `Actor()` method of a layer is used to add actors to it. For example, whenever `mainlayer.Actor(myfigure)` is called, it creates a new actor out of the given figure `myfigure`, returns it, and affixes it to `mainlayer`. This can be used to add multiple actors to an animation:
```python
# Defining point actor
mypoint = mainlayer.Actor(morpho.grid.Point().set(
    pos=3+4*1j,     # Position as a complex number
    size=50,        # Diameter in pixels
    fill=[0,1,0],   # Fill color in RGB, where 0 is min and 1 is max
    color=[1,1,1],  # Border color
    strokeWeight=5, # Border thickness in pixels
    transition=morpho.transitions.quadease  # Quadease transition
    ))
mypoint.newendkey(60).set(
    pos=0,          # Move the point to the origin
    size=25,        # Cut the size in half
    fill=[1,0,0]    # Change fill color to red
    )
mypoint.newendkey(60).set(
    pos=-3+3*1j,    # Move point to (-3+3i)
    size=75,        # Inflate size of point
    alpha=0         # Fade point to invisibility
    )
mypoint.newendkey(-30).set(pos=-3)  # New key 30 frames before last key
mypoint.newendkey(60, mypoint.first().copy())

# Defining grid actor
grid = mainlayer.Actor(morpho.grid.mathgrid(
    view=[-5,5, -5,5],  # read this as [xmin, xmax, ymin, ymax]
    dx=1, dy=1  # Distance between major x and y tick marks
    ))

fgrid = grid.last().fimage(lambda z: z**2/10)
grid.newendkey(60, fgrid)

mation.play()
```

Note how the grid only appears *AFTER* the Point figure has finished its entire animation. This is because we created the `grid` actor *after* creating all of the keyfigures of `mypoint`. By default, `mainlayer.Actor(myfigure)` places the initial keyfigure at the current end of the global animation timeline. To make the grid appear at the same time as the point, we have to define both their actors before creating any of their keyfigures:
```python
# Create Point actor
mypoint = mainlayer.Actor(morpho.grid.Point().set(
    pos=3+4*1j,     # Position as a complex number
    size=50,        # Diameter in pixels
    fill=[0,1,0],   # Fill color in RGB, where 0 is min and 1 is max
    color=[1,1,1],  # Border color
    strokeWeight=5, # Border thickness in pixels
    transition=morpho.transitions.quadease  # Quadease transition
    ))

# Create grid actor
grid = mainlayer.Actor(morpho.grid.mathgrid(
    view=[-5,5, -5,5],  # read this as [xmin, xmax, ymin, ymax]
    dx=1, dy=1  # Distance between major x and y tick marks
    ))


# Define mypoint's keyfigures
mypoint.newendkey(60).set(
    pos=0,          # Move the point to the origin
    size=25,        # Cut the size in half
    fill=[1,0,0]    # Change fill color to red
    )
mypoint.newendkey(60).set(
    pos=-3+3*1j,    # Move point to (-3+3i)
    size=75,        # Inflate size of point
    alpha=0         # Fade point to invisibility
    )
mypoint.newendkey(-30).set(pos=-3)  # New key 30 frames before last key
mypoint.newendkey(60, mypoint.first().copy())

# Define grid's keyfigures
fgrid = grid.last().fimage(lambda z: z**2/10)
grid.newendkey(60, fgrid)

mation.play()
```

Both actors now appear simultaneously. However, you'll notice the point actor appears behind the grid actor. This is due to the order in which the actors were affixed to the layer: ``grid`` came last, so it is drawn in front. To change this, you can change the order in which actors were assigned to layers, or make use of the `beforeActor` option in the `Actor()` method:
```python
grid = mainlayer.Actor(morpho.grid.mathgrid(
    view=[-5,5, -5,5],  # read this as [xmin, xmax, ymin, ymax]
    dx=1, dy=1  # Distance between major x and y tick marks
    ), beforeActor=mypoint)
```
However, there's also a more dynamic way to do it.

### zdepth

Every figure has an attribute called ``zdepth`` which indicates how close the figure is to the "camera" so to speak. Figures with higher zdepths are drawn in front of figures with lower zdepths (as long as they're within the same layer). The default zdepth for a figure is 0. However, zdepth can be tweened just like most other figure attributes, so a figure can start out in the back and then transition to the front at a later time (or vice-versa).

Let's change the initial zdepth of our point actor to be ``-10``, and let's make the zdepth of the next keyframe positive ``10``. Let's make these changes early in the code so that the changes will propagate to later keyframes:

```python
# Create Point actor
mypoint = mainlayer.Actor(morpho.grid.Point().set(
    pos=3+4*1j,     # Position as a complex number
    size=50,        # Diameter in pixels
    fill=[0,1,0],   # Fill color in RGB, where 0 is min and 1 is max
    color=[1,1,1],  # Border color
    strokeWeight=5, # Border thickness in pixels
    transition=morpho.transitions.quadease,  # Quadease transition
    zdepth=-10      # Initial zdepth is now -10
    ))

# Create grid actor
grid = mainlayer.Actor(morpho.grid.mathgrid(
    view=[-5,5, -5,5],  # read this as [xmin, xmax, ymin, ymax]
    dx=1, dy=1  # Distance between major x and y tick marks
    ))

# Define mypoint's keyfigures
mypoint.newendkey(60).set(
    pos=0,          # Move the point to the origin
    size=25,        # Cut the size in half
    fill=[1,0,0],   # Change fill color to red
    zdepth=10       # Second keyfigure zdepth is now +10
    )
mypoint.newendkey(60).set(
    pos=-3+3*1j,    # Move point to (-3+3i)
    size=75,        # Inflate size of point
    alpha=0         # Fade point to invisibility
    )
mypoint.newendkey(-30).set(pos=-3)  # New key 30 frames before last key
mypoint.newendkey(60, mypoint.first().copy())

# Define grid's keyfigures
fgrid = grid.last().fimage(lambda z: z**2/10)
grid.newendkey(60, fgrid)

mation.play()
```

You'll notice the point starts out behind the grid, but then by the time it reaches the origin, it's in front. Later on, it actually switches back to being behind because the final keyfigure was a copy of the first keyfigure whose zdepth was ``-10``.

> **Note:** If the zdepths of two figures are exactly equal, the draw order is inferred from the order of actors in the layer. Actors late in the list are drawn in front of actors early in the list.

### Syncing Actors

So far we've been treating our two actors independently, just adding keyfigures to each without regard for the other, but often times we want an actor to perform an action at a particular point in another actor's timeline.

For example, let's say we have two separate point actors, a red and a green one, and let's have the red one move to the left while the green one stays put, and then have both points move together to a common location. The key idea is the green point should only move after the red point has finished its first move.

One way to do this is to simply keep track of how long the red point's first move takes, and just call `newendkey()` with the same duration for the green point without modifying any attributes so it stays put:
```python
redpt = mainlayer.Actor(morpho.grid.Point().set(pos=-1, fill=[1,0,0]))
greenpt = mainlayer.Actor(morpho.grid.Point().set(pos=1, fill=[0,1,0]))

redpt.newendkey(30).set(pos=-4)
redpt.newendkey(45).set(pos=3j)

greenpt.newendkey(30)  # Green point stays motionless for 30 frames
greenpt.newendkey(45).set(pos=3j)

mation.play()
```
But the drawback is if we later want to change how long `redpt` takes to travel, we also have to modify `greenpt`'s `newendkey()` duration to match, which can quickly become a hassle if instead of just one actor, we had many actors that we wanted to start doing something after `redpt` completed its first move.

A cleaner way to do it is to make use of an *EMPTY* `newendkey()` call. That is, calling `newendkey()` without any frame duration specified. Doing this causes the actor to create a new keyframe at the current end of the global animation timeline. So if we insert one of these empty `newendkey()` calls after moving the `redpt` actor the first time but *before* moving it the second time, we can get `greenpt` sync'd up with `redpt` the way we want:
```python
redpt = mainlayer.Actor(morpho.grid.Point().set(pos=-1, fill=[1,0,0]))
greenpt = mainlayer.Actor(morpho.grid.Point().set(pos=1, fill=[0,1,0]))

redpt.newendkey(30).set(pos=-4)
greenpt.newendkey()  # Create new keyfigure at current end of timeline

redpt.newendkey(45).set(pos=3j)
greenpt.newendkey(45).set(pos=3j)

mation.play()
```
Now if we want to change the duration of `redpt`'s first move, we can just change it in one spot, and `greenpt` will stay sync'd to match.

### Camera

So far our animations have always taken place within the 10 by 10 square region of the complex plane centered at the origin, but we can change this at the Layer level. The simplest way to do this is during layer construction by passing in the optional argument ``view``:
```python
# View of the complex plane is now [-10, 10] x [-10j, 10j]
mainlayer = morpho.Layer([mypoint, grid], view=[-10,10, -10,10])
```

But this can also be changed after layer construction by modifying the layer's ``camera`` attribute:
```python
# Change the view after layer construction
mainlayer.camera.first().view = [-10,10, -10,10]
```

You might notice that we first call the ``first()`` method on the ``camera`` attribute before specifying the new view. This is because (as you might have guessed) the layer's camera is actually an actor, which means the camera can change dynamically during an animation!
```python
# Change the view after layer construction
mainlayer.camera.first().view = [-10,10, -10,10]
mainlayer.camera.newendkey(120).view = [-5,5, -5,5]
```

> **Note:** You can also specify a view box which is not proportional to the dimensions of the animation window (in this case, a non-square view box). Although this works, it can sometimes be hard to wrap your brain around how everything scales, as the appearance of some figures will visibly stretch out of proportion (like paths and images) whereas others (like points) will not. Generally, I recommend keeping the view box in proportion to the animation window unless you have a very special reason not to.

Besides explicitly specifying the boundaries of the view box, there is another way to modify the camera. You can use the ``zoomIn()`` and ``zoomOut()`` methods:

```python
# Use zoomIn() and zoomOut()
layer.camera.newendkey(60).zoomOut(2)
layer.camera.newendkey(60).zoomIn(10)
```

``zoomIn(factor)`` zooms the camera in by the given factor, whereas ``zoomOut(factor)`` zooms it out by the given factor.

You can also shift the camera left and right, and up and down using the ``moveBy()`` and ``centerAt()`` methods:

```python
layer.camera.newendkey(30).centerAt(1+2*1j)  # Center the camera at 1+2j
layer.camera.newendkey(30).moveBy(-2-3j)  # Move the camera 2 units left, 3 down
```

## Animation

Finally, there are some things you can change at the animation level. We've actually been making use of the *Animation* class for a while, but only just to get our animations to play on the screen. Here we'll actually pay more direct attention to it.

An *Animation* object is created near the beginning of the code and contains all the layers:
```python
mation = morpho.Animation(mainlayer)
```

From within the *Animation* class, you can change the animation's framerate, background color, and the shape of the window that plays the animation.

### Framerate

By default, an animation plays at 30 frames per second (fps). You can change this as follows:
```python
mation.frameRate = 60  # Up the framerate to 60 fps
```

However, this changes the playback speed of your animation (making it play twice as fast in this case), which is not necessarily what you want to happen. To change the framerate without affecting the playback speed, use the ``newFrameRate()`` method:
```python
mation.newFrameRate(60)
```

You can also, of course, decrease the framerate the same way. This can be useful while testing a busy animation that your machine is having trouble playing at full speed:
```python
mation.newFrameRate(12)
```

> ***CAUTION!*** Be careful changing framerates down and then up! When decreasing the framerate, it is possible that keyframes (which must always be integers) that are already close to each other may collide and so Morpho will delete some of those colliding keyframes. If you then increase the framerate, you may notice some keyframes have disappeared. Changing the framerate with ``newFrameRate()`` also modifies the time coordinates of the actors, so it's generally not a good idea to change the framerate in the *middle* of constructing an animation. Save it for the end when you're about to play it.

### Background color

You can change the background color of an animation too:
```python
mation.background = [0.5, 0.5, 0.5]  # Make a gray background
```

### Window shape

By default, the shape of the Morpho animation window is 600 x 600 pixels. This can be changed to whatever you like:
```python
mation.windowShape = (400, 400)  # Horizontal pixels by Vertical pixels
```

> ***CAUTION!*** If you make the window a non-square shape, remember to double-check that the layer camera's view box is proportional to it!
>
> Generally, I tend to either work with square window shapes, or fullscreen animations whose aspect ratio is 16:9. When working with these fullscreen animations, I often set up the view box centered at the origin such that the the top of the screen corresponds to ``+10j`` and the bottom is ``-10j``, where the left and right extents are determined by the aspect ratio. I then adjust it if necessary using the camera zoom and move methods. Since this is such a common setup for fullscreen animations, you can access this view box from the ``video`` submodule:
> ```python
> mainlayer = morpho.Layer(view=morpho.video.view169())
> ```
> If you want to view your animation in fullscreen, do the following:
> ```python
> mation.fullscreen = True
> ```
> Press the Escape key to exit.

### Playback controls

While an animation is playing, you can click anywhere in the window to pause it. Click again to unpause. When an animation finishes, you can click to replay it. Unfortunately, there is no way (yet) to rewind or fast-forward an animation during playback, but there is a partial remedy to this.

If you have a long animation, you can start the animation at a later point of the timeline by changing the animation's ``start`` attribute:
```python
mation.start = 600  # Start the animation at frame 600
```

A very useful way to employ this attribute is with the `lastID()` method of an Animation, which returns the frame number of its current last frame:
```python
mation.start = mation.lastID()
```
Including this line at an intermediate point in your code can kind of act like a "bookmark", enabling you to begin animation playback at that point.

To undo a changed `start` value, set ``mation.start = None``. You can also change the end of the animation in a similar way:
```python
mation.end = mation.lastID()
```

### Delays

Another useful construct in the Animation class is *delays*. These are basically pauses you can insert at any point in the animation. They can last for a set duration, or be infinitely-long, in which case the animation will only progress once you click on the screen. The easiest way to set them up is with the `wait()` method, which inserts a pause at the current end of the global animation timeline.
```python
mation.wait(30)  # Wait for a duration of 30 frames

# ...do some other stuff...

mation.wait()  # Wait until the user clicks on the screen
```

> **Note:** Delays are treated like automated pauses during playback, so setting delays will NOT modify the time coordinates of any keyfigures.

### Exporting

Once you have an animation you like, you can export it as a file in three different formats.

To export an animation as an MP4 video file in the same folder as the script you're running, just type
```python
mation.export("./animation.mp4")
```
> ***CAUTION!*** Don't forget to include ``./`` at the beginning of a relative file path! This is required!

You can also export an animation as a GIF animation by typing
```python
mation.export("./animation.gif")
```
And you can export an animation as a sequence of PNG images by typing
```python
mation.export("./animation.png")
```
which will result in PNG images with names like ``animation_000.png``, ``animation_001.png``, etc. There will be one PNG image per frame of animation (excluding delays).

> **Note:** You cannot export an animation as MP4 if the animation contains infinitely-long delays. You will have to finitize them. One way to do so is to call the method ``mation.finitizeDelays(numFrames)`` which will convert all infinite delays to the finite number of frames you specify.

> ***Tip:*** If you have a complicated animation that runs slowly when previewing it with ``play()``, I sometimes find it helpful to export a segment of the animation as an MP4 to view it at full speed. If exporting at full quality takes too long, you can also reduce the framerate before exporting and/or reduce the export resolution by typing, for example,
> ```python
> mation.newFrameRate(10)
> mation.export("./animation.mp4", scale=0.5)
> ```

You can also only export a portion of the animation between a starting frame and an ending frame using the `start` and `end` attributes as discussed earlier.

While constructing an animation, I sometimes want to just view its current final frame without playing through the entire animation first. You can accomplish this by including the following line at the end of your code (i.e. after all keyfigures have been created, but before the `play()` method is called).
```python
mation.start = mation.lastID()
```

> **Note:** In Morpho, frame number is often referred to as "index" or "ID" in the code. So methods like ``lastID()``, ``firstID()``, and ``keyID()`` all return the frame numbers of important moments in an actor, layer, or animation.






<!-- ## Bringing Figures to Life

In our "Hello World" example, we started by defining an Actor containing a single *Point* figure initialized to the position `-3` (meaning coordinates (-3,0)).
```python
point = mainlayer.Actor(morpho.grid.Point(-3))
```
To add a new figure to the timeline, we invoke the point actor's `newendkey()` method which creates a copy of the current latest figure in the timeline and places it a given number of frames after the current end of the actor's timeline.
```python
point = mainlayer.Actor(morpho.grid.Point(-3))
point.newendkey(30)
```
> **Note:** All references to time and duration in Morpho are always in units of frames of animation. This is translated into actual units of time like seconds in the *Animation* class where you can specify the framerate (more on that later). By default, the framerate is 30 frames per second.

Note that the `newendkey()` method returns the new figure it creates, allowing us to easily modify the new figure's state by chaining a call to its `set()` method, which we do to change the point's position attribute `pos` to `3`:
```python
point.newendkey(30).set(pos=3)
```
You can also modify more than one attribute at a time using `set()`, such as the point's size or fill color:
```python
# Colors are specified as normalized RGB triples, so
# [1,1,0] refers to yellow
point.newendkey(30).set(pos=3, size=30, fill=[1,1,0])
```
A note on terminology: the individual figures we specify in an actor's timeline are known as *keyfigures* or *keys* and the locations they're at on the timeline are called *keyframes* (or sometimes *keyindices*), following the terminology from the animation industry. Hence the `newendkey()` method is so-called because it creates a new ending keyfigure. On the other hand, the interpolated figures Morpho generates between keyfigures during an animation are called *tweened figures*. -->