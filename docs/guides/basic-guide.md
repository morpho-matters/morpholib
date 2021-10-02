---
layout: default
title: Morpho Guide: Basics
---

# Morpho Guide: Basics

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

## Figures

The fundamental object in morpho is the *Figure*. A figure is basically anything that supports being drawn and interpolated (meaning in an animation that a figure can be smoothly transformed into another figure of the same type). Anything that appears on screen during an animation is a figure. This includes curves, polygons, text, etc.

Each figure comes with its own particular set of *attributes* which determine its state and what the figure looks like when drawn. For example: position, color, size, rotation, etc. These attributes are common to a given figure type, but figures of different types can have different attributes (for example, a *Point* figure will have some attributes that a *Path* figure does not possess and vice-versa).

### Points

To get a sense of how to make and manipulate a figure, let's make a *Point* figure. The *Point* figure is located within the ``morpho.grid`` submodule. To make one, use the following syntax:

```python
mypoint = morpho.grid.Point()
```

This will create a point in its default state. Let's see what it looks like. To actually view a figure, we need to package it into an *Animation*. To do that, type the following:

```python
movie = morpho.Animation(mypoint)
movie.play()
```

You should see a red dot in the middle of a black background.

Let's change what it looks like. Let's make it bigger, color it green, and give it a thick white border:

```python
mypoint = morpho.grid.Point()
mypoint.size = 50         # Diameter given in units of pixels
mypoint.fill = [0,1,0]    # Color in RGB, where 0 is min and 1 is max
mypoint.color = [1,1,1]   # Border is colored white
mypoint.strokeWeight = 5  # Thickness in pixels

movie = morpho.Animation(mypoint)
movie.play()
```

Let's also change where it's located. To do that, we modify the point's ``pos`` attribute. One thing to note: in Morpho, you should always think of the animation canvas as viewing a particular rectangular region of the complex plane. By default, the region is the square whose real and imaginary extents are ``[-5,5]`` and ``[-5i, 5i]`` respectively, but this can be changed. Thus, all positions in Morpho are expressed as complex numbers (``x + y*1j`` in Python lingo).

Let's move our point to the position ``4 + 3i``. We can do it like so:

```python
mypoint.pos = 4 + 3*1j
```
(This can also be specified as ``4 + 3j``, but using ``*1j`` is safer if you're new to the syntax since it works even when the imaginary component is a variable instead of a literal.)

> ***CAUTION!*** In Python, the imaginary unit is represented with ``j``, not ``i``. To avoid confusion, this guide will use *j* instead of *i* from now on.

We can also make the point semi-transparent. To do so, modify the ``alpha`` attribute:

```python
mypoint.alpha = 0.5    # Takes values in [0,1] where 1 = opaque, 0 = invisible
```

The ``alpha`` attribute is shared by many figures and is useful to make figures fade in and fade out.

### Paths

*Points* are good example figures since they're very simple, but they aren't actually used that often in my experience. *Paths*, on the other hand, are used much more often, but are also still pretty basic figures, and so are a good figure to practice with.

A path is basically a sequence of line segments. However, by increasing the number of vertices, they can approximate curves. The standard syntax for creating a *Path* figure is as follows:

```python
mypath = morpho.grid.Path(seq)
```

where ``seq`` is a list of complex numbers. For example, let's make a path in the shape of a diamond whose corners are located on the coordinate axes 3 units away from the origin and see what it looks like:

```python
mypath = morpho.grid.Path([3, 3*1j, -3, -3*1j])

movie = morpho.Animation(mypath)
movie.play()
```

As we requested, the path ends at the point *-3j*. We can close the loop by appending the starting vertex to the input sequence, but the *Path* class already supplies a way to do this automatically:

```python
mypath = morpho.grid.Path([3, 3*1j, -3, -3*1j])
mypath.close()

movie = morpho.Animation(mypath)
movie.play()
```

The vertex sequence can be extracted and modified at any time by accessing the ``seq`` attribute (``mypath.seq``), although this is seldom done in practice.

Like points, paths also support a variety of attributes modifying their visual appearance. These include ``color``, ``alpha``, and ``width``. For example, let's color the path blue and make it thicker:

```python
mypath = morpho.grid.Path([3, 3*1j, -3, -3*1j])
mypath.close()
mypath.color = [0,0,1]  # Make the path blue
mypath.width = 5        # Make the path 5 pixels thick

movie = morpho.Animation(mypath)
movie.play()
```

### Built-in Paths

Although you can define a path explicitly by enumerating its vertex sequence, this is seldom done in practice unless you want to make a very short polygonal path. To make a curved path appear, we need many more vertices, and Morpho provides several tools to construct them.

#### Lines

The first tool is the ``line()`` function. Here's an example of how to use it:

```python
# Make a linear path connecting -2-3i to 1+4i
myline = morpho.grid.line(-2-3*1j, 1+4*1j)

movie = morpho.Animation(myline)
movie.play()
```

Admittedly, this is visually the same as simply doing ``morpho.grid.Path([-2-3*1j, 1+4*1j])``, but the difference is the line actually consists of about 50 vertices. This is useful if you want to later transform the line into a curve (more on that later). The number of steps to take between the starting and ending vertices can be specified using the optional argument ``steps``:

```python
myline = morpho.grid.line(-2-3*1j, 1+4*1j, steps=100)
```

#### Ellipses

You can also make elliptical paths in a similar way:

```python
# Make an elliptical path centered at 1+1j with
# semi-width 3 and semi-height 1
myoval = morpho.grid.ellipse(1+1j, 3, 1).edge()

movie = morpho.Animation(myoval)
movie.play()
```
> **Note:** The method ``edge()`` is called because ``ellipse()`` actually returns a *Polygon* figure (more on them later). Calling ``edge()`` returns the *Path* figure representing the ellipse's outer edge.

By default, the angular separation between adjacent vertices is 5 degrees, but this can also be changed:

```python
myoval = morpho.grid.ellipse(1+1j, 3, 1, dTheta=10)
```

#### Grids

A very common use of paths is to construct grids. Morpho provides a built-in function to generate one. Let's make a grid that spans the rectangle ``[-5,5] x [-4j, 4j]``. Here's how:

```python
mygrid = morpho.grid.mathgrid(
    view=[-5,5, -4,4],  # read this as [xmin, xmax, ymin, ymax]
    dx=1, dy=1          # Distance between major x and y tick marks
    )

movie = morpho.Animation(mygrid)
movie.play()
```

The colors of the horizontal and vertical lines can be altered by supplying the optional arguments ``hcolor=[R,G,B]`` and ``vcolor=[R,G,B]`` to the ``mathgrid()`` function.

By default it also includes minor grid lines exactly halfway between every two major grid lines, but these can be disabled by including the arguments ``hmidlines=0`` and ``vmidlines=0``.

The colors of the minor grid lines can also be changed with the arguments ``hmidColor`` and ``vmidColor``.

> **Note:** Technically the figure ``mathgrid()`` returns is not a path, but a collection of paths packaged together into a type of figure called a *Frame*. But don't worry about that now.

### Polygons

There is also a *Polygon* figure. This is a lot like the *Path* figure, except that the boundary is always closed and you can fill the interior with color.

```python
mypoly = morpho.grid.Polygon([3, 3*1j, -3, -3*1j])
mypoly.color = [1,1,1]  # Make the border white
mypoly.width = 5        # Thicken the border
mypoly.fill = [1,0,0]   # Fill the interior with red

movie = morpho.Animation(mypoly)
movie.play()
```

> **Note:** In a *Path* figure, the vertex sequence attribute is called ``seq`` but in a Polygon figure, the vertex sequence attribute is called ``vertices``.

## Actors

So far we've just been dealing with static figures. How do we animate them?

Animation in Morpho primarily takes the form of smooth interpolation between a starting figure and an ending figure over a certain duration. This process is called *tweening*. To set this up, we need to add a timeline to a figure. Once this is done, the figure is called an *actor* (based on a loose analogy with a stage play). To see how this is done, let's take our old *Point* figure from before and turn it into an actor:

```python
mypoint = morpho.grid.Point()
mypoint.size = 50         # Diameter given in units of pixels
mypoint.fill = [0,1,0]    # Color in RGB, where 0 is min and 1 is max
mypoint.color = [1,1,1]
mypoint.strokeWeight = 5  # Thickness in pixels
mypoint.pos = 4 + 3*1j

mypoint = morpho.Actor(mypoint)
```

The point now has a timeline, and the original point figure that we started with is assigned to frame 0.

> **Note:** All references to time and duration in Morpho are always in units of frames of animation. This is translated into actual units of time like seconds in the *Animation* class where you can specify the framerate (more on that later). By default, the framerate is 30 frames per second.

To make this actor come alive, we now specify a modified version of the point at a later point in the timeline, say at frame 60. We can start this by using the ``newkey()`` method.

```python
mypoint.newkey(60)  # Create a copy of the point at frame 60
```

This generates a copy of the frame 0 point at frame 60. We can now modify the attributes of the frame 60 point. Let's change the fill color, size, and position of the point. Since the point is now an actor, before we can access or change its attributes, we first have to specify the frame. This can be done using the ``time()`` method of an actor.

```python
mypoint.time(60).fill = [1,0,0]  # Change fill color to red
mypoint.time(60).size = 25  # Cut the size in half
mypoint.time(60).pos = 0  # Move the point to the origin
```

> ***CAUTION!*** Please be careful not to forget to call the ``time()`` method before modifying a figure's attributes! Morpho does not always throw an error if you forget to do this, and it will instead basically ignore any changes you make. This can lead to considerable confusion debugging your code if you're not careful!

Let's now package the actor into an animation and play it!

```python
mypoint = morpho.grid.Point()
mypoint.size = 50         # Diameter given in units of pixels
mypoint.fill = [0,1,0]    # Color in RGB, where 0 is min and 1 is max
mypoint.color = [1,1,1]
mypoint.strokeWeight = 5  # Thickness in pixels
mypoint.pos = 4 + 3*1j

mypoint = morpho.Actor(mypoint)
mypoint.newkey(60)  # Create a copy of the point at frame 60
mypoint.time(60).fill = [1,0,0]  # Change fill color to red
mypoint.time(60).size = 25  # Cut the size in half
mypoint.time(60).pos = 0  # Move the point to the origin

movie = morpho.Animation(mypoint)
movie.play()
```

The point is now animated! And it is gradually transformed ("*tweened*") into the final point over time.

It's perhaps a good time to introduce some more terminology: The starting and ending points that we specified are called *keyfigures* or just simply *keys*, and their positions on the timeline are referred to as *key indices* or *keyframes*. Morpho does the job of tweening between keyfigures but does not store the tweened figures by default.

We can add more keyfigures along the timeline, as many as we please! Let's add another key point to the timeline at frame 120 with some other changes:

```python
mypoint.newkey(120)
mypoint.time(120).size = 75        # Inflate size of point
mypoint.time(120).pos = -3 + 3*1j  # Move point to (-3+3j)
mypoint.time(120).alpha = 0        # Fade point to invisibility

movie = morpho.Animation(mypoint)
movie.play()
```

We can even insert a key between two previous keys. For instance, instead of having the red point at frame 60 fade away by moving to ``-3+3j`` directly, let's have it take a detour to the point ``-3`` on the real axis:

```python
mypoint.newkey(120)
mypoint.time(120).size = 75        # Inflate size of point
mypoint.time(120).pos = -3 + 3*1j  # Move point to (-3+3j)
mypoint.time(120).alpha = 0        # Fade point to invisibility

mypoint.newkey(90)
mypoint.time(90).pos = -3  # Point takes a detour to -3.
```

> ***CAUTION!*** Don't forget to declare ``newkey(90)`` in the above code! If you omit it, the animation will appear unchanged because ``mypoint.time(90)`` will not be considered a keyfigure, and thus changes made to it will not be registered.

Observe that the point already begins fading and growing on its way to the position ``-3``. This is because we already specified the fading and growing behavior at frame 120 BEFORE creating a new keyfigure at frame 90. If we swap the order and create the new key at 90 first and THEN make the new key at 120, the point will merely move to the position ``-3`` without changing either its size or transparency until after it reaches ``-3``. The reason this behavior occurs is because when creating a new keyfigure that is BETWEEN two existing keyfigures, the new keyfigure's state will be that of the *tweened* figure. So inserting a keyfigure at frame 90 between the two keyfigures at frame 60 and 120 results in a partially tweened figure whose position we modify to be ``-3``.

The general rule for keyfigure creation is if the new keyfigure is *ahead* of all existent keyfigures, the new keyfigure will be a copy of the latest already existent keyfigure. If a new keyfigure is created *between* two existent keyfigures, the new keyfigure will be defined by tweening the two surrounding keyfigures. Finally, if a new keyfigure is created *before* all existent keyfigures (or is the first keyfigure to be created in an empty timeline), the new keyfigure will be the default figure (like calling ``Point()`` with no optional arguments).

However, there is a way to bypass this behavior for new key creation and instead force the new key to be whatever figure you specify. To see how this works, let's say we want to take our point actor and return it to its original starting state. Instead of making a new key and then modifying the attributes, we can instead force the new key to be a copy of the frame 0 figure by passing an additional argument to the ``newkey()`` method:

```python
mypoint.newkey(180, mypoint.time(0).copy())
```

> ***CAUTION!*** Be sure to remember to include the ``copy()`` method! Forgetting to do so will mean the frame 180 keyfigure and the frame 0 keyfigure will be linked, so changing the attributes of one will influence the other. This can lead to considerable confusion in debugging your code.

### Transitions

Our animation looks fine as far as it goes, but it looks a bit mechanical. It would be nice if we could make the transitions between keyframes a little more organic, such as by having it accelerate and decelerate as it leaves and arrives at keyframes. This can be accomplished by setting a so-called *transition* or *transition function*.

Since we want to change the transition of all the movements, we can change the transition function of our initial starting figure before we made it an actor. This will then cause the transition function to propagate to all the other keyfigures as they are created. Built-in transition functions can be found in the ``morpho.transitions`` submodule, and a good one for this purpose is ``quadease`` (short for "quadratic easing"):

```python
mypoint = morpho.grid.Point()
mypoint.size = 50         # Diameter given in units of pixels
mypoint.fill = [0,1,0]    # Color in RGB, where 0 is min and 1 is max
mypoint.color = [1,1,1]
mypoint.strokeWeight = 5  # Thickness in pixels
mypoint.pos = 4 + 3*1j
mypoint.transition = morpho.transitions.quadease  # New transition
```

> ***Tip:*** If you expect to use a certain transition function for almost all tweens, you can change the default transition function Morpho uses on all actors by including the line
```python
morpho.transition.default = my_transition
```
at the top of your code. The normal default transition is ``morpho.transitions.uniform``.

### Working with relative time coordinates

When in the middle of making an animation, it can be cumbersome to always work in absolute units of time, where you specify the exact time coordinates for each keyframe. This can be especially difficult if you want to change the duration between just two keyframes in the middle but you don't want to modify the duration of any others.

For example, say we change our mind and want to make the transition from the frame 0 point to the frame 60 point happen faster. We could rewrite our code so that instead of making a new key at 60, we make it at 30:

```python
mypoint = morpho.Actor(mypoint)
mypoint.newkey(30)  # Create a copy of the point at frame 30
mypoint.time(30).fill = [1,0,0]  # Change fill color to red
mypoint.time(30).size = 25  # Cut the size in half
mypoint.time(30).pos = 0  # Move the point to the origin
```

But since we didn't change the time coordinates of the frame 90 keyfigure, it will now take 60 frames to get there instead of 30 which was the original duration. To fix this would mean having to change all the time values for all keyfigures that came after the modified keyfigure, which would be a pain.

Instead, let's rewrite our code using methods that make use of *relative* time coordinates. The main methods for this job are going to be ``newendkey()`` and ``last()``.

``newendkey()`` is like ``newkey()`` except instead of specifying the absolute time coordinates of where to create a new keyfigure, we specify it in terms of how many frames it should be *after* the latest keyframe (i.e. number of frames after the keyfigure with the highest index). You can even specify negative values to make a new keyfigure some number of frames *before* the latest keyframe.

``last()`` is a helpful method that always returns whatever the latest keyfigure currently is. There is also a complementary method called ``first()`` which returns the earliest keyfigure (the one with the lowest index).

```python
mypoint = morpho.grid.Point()
mypoint.size = 50         # Diameter given in units of pixels
mypoint.fill = [0,1,0]    # Color in RGB, where 0 is min and 1 is max
mypoint.color = [1,1,1]
mypoint.strokeWeight = 5  # Thickness in pixels
mypoint.pos = 4 + 3*1j
mypoint.transition = morpho.transitions.quadease  # New transition

mypoint = morpho.Actor(mypoint)
mypoint.newendkey(60)  # Create a copy of the point at frame 60
mypoint.last().fill = [1,0,0]  # Change fill color to red
mypoint.last().size = 25  # Cut the size in half
mypoint.last().pos = 0  # Move the point to the origin

mypoint.newendkey(60)
mypoint.last().size = 75        # Inflate size of point
mypoint.last().pos = -3 + 3*1j  # Move point to (-3+3i)
mypoint.last().alpha = 0        # Fade point to invisibility

mypoint.newendkey(-30)  # New key 30 frames before last key
mypoint.key(-2).pos = -3  # key(-2) means second-to-last key

mypoint.newendkey(60, mypoint.first().copy())

movie = morpho.Animation(mypoint)
movie.play()
```

Now if we want to modify the second keyfigure's timing, we just need to change the first instance of ``mypoint.newendkey(60)`` to ``mypoint.newendkey(30)`` and all future keyfigure times will adjust accordingly.

One last thing to note about the above code. In it, we made use of the ``key()`` method. Typing ``mypoint.key(n)`` returns the ``n``th keyfigure in the actor where ``n = 0`` is the first keyfigure. Negative ``n`` values are interpreted cyclically, so ``mypoint.key(-1)`` is equivalent to ``mypoint.last()`` and so ``mypoint.key(-2)`` returns the second-to-last keyfigure.

### An example with grids

Let's do another example this time using a grid. First we'll make a standard grid spanning the full canvas:

```python
grid = morpho.grid.mathgrid(
    view=[-5,5, -5,5],  # read this as [xmin, xmax, ymin, ymax]
    dx=1, dy=1  # Distance between major x and y tick marks
    )
```

We'll now transform this grid using a function. To do this we'll use the ``fimage()`` method:

```python
fgrid = grid.fimage(lambda z: z**2/10)
```

The ``fimage()`` method stands for "function image" and refers to taking the "image" of a path or grid in the mathematical set theory sense: applying a function to every vertex. In the above code, we are applying the function *f*(*z*) = *z*<sup>2</sup>/10 to every vertex in the grid and putting the resulting image grid in a new variable called ``fgrid``.

Let's now make an animation where our starting grid transforms into the image grid. To do that, we'll turn our starting grid into an actor, and then turn our ``fgrid`` image grid into a new keyfigure:

```python
grid = morpho.Actor(grid)
grid.newendkey(60, fgrid)

movie = morpho.Animation(grid)
movie.play()
```

## Layers, Camera, and Animation

So far we've just been animating one actor at a time, but an animation typically consists of many actors. We can package many independent actors together into a structure called a *Layer* which has its own local camera (i.e. coordinate system).

To start, let's package the two example actors we've been playing with into one *Layer*:

```python
### DEFINING POINT ACTOR ###

mypoint = morpho.grid.Point()
mypoint.size = 50         # Diameter given in units of pixels
mypoint.fill = [0,1,0]    # Color in RGB, where 0 is min and 1 is max
mypoint.color = [1,1,1]
mypoint.strokeWeight = 5  # Thickness in pixels
mypoint.pos = 4 + 3*1j
mypoint.transition = morpho.transitions.quadease  # New transition

mypoint = morpho.Actor(mypoint)
mypoint.newendkey(60)  # Create a copy of the point at frame 60
mypoint.last().fill = [1,0,0]  # Change fill color to red
mypoint.last().size = 25  # Cut the size in half
mypoint.last().pos = 0  # Move the point to the origin

mypoint.newendkey(60)
mypoint.last().size = 75        # Inflate size of point
mypoint.last().pos = -3 + 3*1j  # Move point to (-3+3i)
mypoint.last().alpha = 0        # Fade point to invisibility

mypoint.newendkey(-30)  # New key 30 frames before last key
mypoint.key(-2).pos = -3  # key(-2) means second-to-last key

mypoint.newendkey(60, mypoint.first().copy())

### DEFINING GRID ACTOR ###

grid = morpho.grid.mathgrid(
    view=[-5,5, -5,5],  # read this as [xmin, xmax, ymin, ymax]
    dx=1, dy=1  # Distance between major x and y tick marks
    )
fgrid = grid.fimage(lambda z: z**2/10)

grid = morpho.Actor(grid)
grid.newendkey(60, fgrid)

### PACKAGE INTO A LAYER ###

layer = morpho.Layer([mypoint, grid])

# Package further into animation
movie = morpho.Animation(layer)
movie.play()
```

Both actors now appear simultaneously. However, you'll notice the point actor appears behind the grid actor. This is due to the order in which the actors were supplied to the layer: ``grid`` came last, so it is drawn in front. To change this, you can change the order of the actors when constructing the layer, but there is a more dynamic way to do this as well.

### zdepth

Every Morpho figure has an attribute called ``zdepth`` which indicates how close the figure is to the "camera" so to speak. Figures with higher zdepths are drawn in front of figures with lower zdepths (as long as they are within the same layer). The default zdepth for a figure is 0. However, zdepth can be tweened just like many other figure attributes, so a figure can start out in the back and then transition to the front at a later point (or vice-versa).

Let's change the initial zdepth of our point actor to be ``-10``, and let's make the zdepth of the next keyframe positive ``10``. Let's make these changes early in the code so that the changes will propagate to later keyframes:

```python
mypoint = morpho.grid.Point()
mypoint.size = 50         # Diameter given in units of pixels
mypoint.fill = [0,1,0]    # Color in RGB, where 0 is min and 1 is max
mypoint.color = [1,1,1]
mypoint.strokeWeight = 5  # Thickness in pixels
mypoint.pos = 4 + 3*1j
mypoint.transition = morpho.transitions.quadease  # New transition

mypoint.zdepth = -10  # Initial zdepth is now -10

mypoint = morpho.Actor(mypoint)
mypoint.newendkey(60)  # Create a copy of the point at frame 60
mypoint.last().fill = [1,0,0]  # Change fill color to red
mypoint.last().size = 25  # Cut the size in half
mypoint.last().pos = 0  # Move the point to the origin
mypoint.last().zdepth = 10  # Second key has zdepth = +10
```

You'll notice the point starts out behind the grid, but then by the time it reaches the origin, it is then in front. Later on it actually switches back to being behind because the final keyfigure was a copy of the first keyfigure whose zdepth was ``-10``.

> **Note:** If the zdepths of two figures are exactly equal, the draw order is inferred from the order of actors in the layer. Actors late in the list are drawn in front of actors early in the list.

### Camera

So far our animations have always taken place within the 10 by 10 square region of the complex plane centered at the origin, but we can change this at the Layer level. The simplest way to do this is during layer construction by passing in the optional argument ``view``:

```python
# View of the complex plane is now [-10, 10] x [-10j, 10j]
layer = morpho.Layer([mypoint, grid], view=[-10,10, -10,10])
```

But this can also be changed after layer construction by modifying the layer's ``camera`` attribute:

```python
# Change the view after layer construction
layer.camera.time(0).view = [-10,10, -10,10]
```

You might notice that we first call the ``time()`` method on the ``camera`` attribute before specifying the new view. This is because (as you might have guessed) the layer's camera is actually an actor, which means the camera can change dynamically during an animation!

```python
# Change the view after layer construction
layer.camera.time(0).view = [-10,10, -10,10]
layer.camera.newendkey(120)
layer.camera.last().view = [-5,5, -5,5]
```

> **Note:** You can also specify a view box which is not proportional to the dimensions of the animation window (in this case, a non-square view box). Although this works, it can sometimes be hard to wrap your brain around how everything scales, as the appearance of some figures will visibly stretch out of proportion (like paths and images) whereas others (like points) will not. Generally I recommend keeping the view box in proportion to the animation window unless you have a very special reason not to.

Besides explicitly specifying the boundaries of the view box, there is another way to modify the camera. You can use the ``zoomIn()`` and ``zoomOut()`` methods:

```python
# Use zoomIn() and zoomOut()
layer.camera.newendkey(60)
layer.camera.last().zoomOut(2)
layer.camera.newendkey(60)
layer.camera.last().zoomIn(10)
```

``zoomIn(factor)`` zooms the camera in by the given factor, whereas ``zoomOut(factor)`` zooms it out by the given factor.

You can also shift the camera left and right, and up and down using the ``moveBy()`` and ``centerAt()`` methods:

```python
layer.camera.newendkey(30)
layer.camera.last().centerAt(1+2*1j)  # Center the camera at 1+2i
layer.camera.newendkey(30)
layer.camera.last().moveBy(-2-3j)  # Move the camera 2 units left, 3 down
```

### Animation

Finally, there are some things you can change at the animation level. We've actually been making use of the *Animation* class for a while, but only just to get our animations to play on the screen. Here we'll actually pay more direct attention to it.

From within the *Animation* class, you can change the animation's framerate, background color, and the shape of the window that plays the animation (the canvas).

#### Framerate

By default, an animation plays at 30 frames per second (fps). You can change this as follows:

```python
movie.frameRate = 60  # Up the framerate to 60 fps
```

However, this changes the playback speed of your animation (making it play twice as fast in this case), which is not necessarily what you want to happen. To change the framerate without affecting the playback speed, use the ``newFrameRate()`` method:

```python
movie.newFrameRate(60)
```

You can also, of course, decrease the framerate the same way. This can be useful while testing a busy animation that your machine is having trouble playing at full speed:

```python
movie.newFrameRate(12)
```

> ***CAUTION!*** Be careful changing framerates down and then up! When decreasing the framerate, it is possible that keyframes (which must always be integers) that are already close to each other may collide and so Morpho will delete some of those colliding keyframes. If you then increase the framerate, you may notice some keyframes have disappeared. Changing the framerate with ``newFrameRate()`` also modifies the time coordinates of the actors, so it's generally not a good idea to change the framerate in the *middle* of constructing an animation. Save it for the end when you're about to play it.

#### Background color

You can change the background color of an animation too:

```python
movie.background = [0.5, 0.5, 0.5]  # Make a gray background
```

#### Window shape

By default, the shape of the Morpho animation window is 600 x 600 pixels. This can be changed to whatever you like:

```python
movie.windowShape = (400, 400)  # Horizontal pixels by Vertical pixels
```

> ***CAUTION!*** If you make the window a non-square shape, remember to double-check that the layer camera's view box is proportional to it!
>
> Generally, I tend to either work with square window shapes, or fullscreen animations whose aspect ratio is 16:9. When working with these fullscreen animations, I often set up the view box centered at the origin such that the the top of the screen corresponds to ``+10j`` and the bottom is ``-10j``, where the left and right extents are determined by the aspect ratio. I then adjust it if necessary using the camera zoom and move methods. Since this is such a common setup for fullscreen animations, you can access this view box from the ``video`` submodule:
> ```python
> layer = morpho.Layer([actor1, actor2, etc], view=morpho.video.view169())
> ```
> If you want to view your animation in fullscreen, do the following:
> ```python
> movie.fullscreen = True
> ```
> Press the Escape key to exit.

### In-animation control

While an animation is playing, you can click anywhere in the window to pause it. Click again to unpause. When an animation finishes, you can click to replay it. Unfortunately, there is no way (yet) to rewind or fast-forward an animation during playback, but there is a partial remedy to this.

If you have a long animation, you can start the animation at a later point of the timeline by changing the animation's ``start`` attribute:

```python
movie.start = 600  # Start the animation at frame 600
```

To undo this, set ``movie.start = None``. You can also change the end of the animation in a similar way:

```python
movie.end = 1000  # End the animation at frame 1000
```

#### Delays

Another useful construct in the Animation class is *delays*. These are basically pauses you can insert at any point in the animation. They can last for a set duration, or be infinitely-long, in which case the animation will only progress once you click on the screen:

```python
movie.delays[60] = 30  # Pause at frame 60 for a duration of 30 frames
movie.delays[150] = float("inf")  # Pause at frame 150 until screen is clicked
```

> ***Tip:*** Infinity comes up from time to time when using Morpho. I find it helpful to assign double lowercase letter *o*'s to infinity: ``oo = float("inf")``. You can automatically import this constant (among others) by including the line ``from morpholib.tools.basics import *`` at the top of your code.

> **Note:** Morpho treats delays like automated pauses during playback, so setting delays will NOT modify the time coordinates of any keyfigures.

### Exporting

Once you have an animation you like, you can export it as a file in three different formats.

To export an animation as an MP4 video file in the same folder as the script you're running, just type

```python
movie.export("./movie.mp4")
```
> ***CAUTION!*** Don't forget to include ``./`` at the beginning of a relative file path! This is required in Morpho.

You can also export an animation as a GIF animation by typing
```python
movie.export("./movie.gif")
```
And you can export an animation as a sequence of PNG images by typing
```python
movie.export("./movie.png")
```
which will result in PNG images with names like ``movie_000.png``, ``movie_001.png``, etc. There will be one PNG image per frame of animation (excluding delays).

> **Note:** You cannot export an animation as MP4 if the animation contains infinitely-long delays. You will have to finitize them. One way to do so is to call the method ``movie.finitizeDelays(numFrames)`` which will convert all infinite delays to the finite number of frames you specify.

> ***Tip:*** If you have a complicated animation that runs slowly when previewing it with ``play()``, I sometimes find it helpful to export a segment of the animation as an MP4 to view it at full speed. If exporting at full quality takes too long, you can also reduce the framerate before exporting and/or reduce the export resolution by typing, for example,
> ```python
> movie.newFrameRate(10)
> movie.export("./movie.mp4", scale=0.5)
> ```

You can also only export a portion of the animation between a starting frame and an ending frame. You can do this with the ``start`` and ``end`` attributes:
```python
movie.start = 30  # Start the animation at frame 30
movie.end = 120   # End the animation at frame 120
```

By default, ``start`` and ``end`` are set to the Python null value ``None``, which means the animation will start and end at the earliest and latest keyframes it contains.

While constructing an animation, I sometimes want to just view its final frame without playing through the entire animation first. You can accomplish this by setting
```python
movie.start = movie.lastID()
```
where ``movie.lastID()`` returns the frame number of the final frame of the animation.

> **Note:** In Morpho, frame number is usually referred to as "index" or "ID" in the code. So methods like ``lastID()``, ``firstID()``, and ``keyID()`` all return the frame numbers of important moments in an actor, layer, or animation.
