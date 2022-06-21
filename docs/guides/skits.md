---
layout: default
title: Morpho Guide -- Skits
---

# Morpho Guide: Skits

> **Note:** To properly run the example code snippets in this guide, you should include the following lines at the top of your code:
> ```python
> import morpholib as morpho
> morpho.importAll()
>
> from morpholib.tools.basics import *
>
> import math, cmath
> ```

Skits are perhaps the most powerful of Morpho's animation tools. In short, they give you a relatively quick way to construct a custom-tailored composite figure that behaves in ways that you can precisely control. I like to think of them as little animated machines. For example, with Skits, you can animate a pendulum swinging, a tangent line moving along a curve, a morphing shape with a label that dynamically keeps track of its area, etc.

The basic idea behind a Skit is you are given a parameter value called ``t`` (which can be any real number and you can interpret it to represent any quantity, e.g. time, angle, size, etc.) and you define a function that takes this ``t`` value as input and then returns a figure (or a group of figures) based on that ``t`` value. It's basically like parametric equations, except instead of outputting a set of numbers (like ``x`` or ``y``) given ``t``, you output a figure, or group of figures, corresponding to that ``t`` value.

That's where the name "Skit" comes from: You're basically choreographing the state of a collection of figures at any given "time" ``t`` in order to define what is essentially a little animated "skit". But although the idea is simple, Skits are powerful. They may be short animations, but they can be *extremely* precisely controlled and fine-tuned.

## Trackers

Let's start by creating a simple Skit I call a "tracker" (also sometimes called a "counter"). A tracker is basically a numeric label that dynamically updates itself every frame, and is usually used to "track" some quantity in the animation that you'd like the viewer to see, like maybe a scale factor, or an area quantity. For now we won't have our tracker actually track anything, but we'll learn how to use Skits to make a dynamically changing label.

Skits are not initialized like any other figure, because you're basically defining a brand new figure type. Here's the basic starting setup:

```python
class Tracker(morpho.Skit):
    def makeFrame(self):
        # Code to generate a figure based on
        # t value will go here eventually
        pass
```

What we're basically doing here is defining a new figure type that we decided to name ``Tracker`` which subclasses from the base class called ``morpho.Skit``. We now have to tell the class what to do with any given parameter ``t`` value. This is where the ``makeFrame()`` method comes in: It contains the instructions for how to build the figure that should be drawn at any given ``t`` value. For our simple tracker, let's have it construct a ``Text`` figure that displays the current value of ``t``:

```python
class Tracker(morpho.Skit):
    def makeFrame(self):
        # The t value is stored as a tweenable attribute
        # of the tracker itself. Let's extract it just
        # to simplify the later syntax.
        t = self.t

        # The label's text is just the t-value converted
        # into a string.
        label = morpho.text.Text(str(t))

        return label
```
<!-- > **Note:** The name ``makeFrame`` is important here! A Skit expects to have a method with this name defined, and calls it in order to construct the figures it needs to draw to the screen. -->
> **Note:** Remember not to convert figures into actors within the ``makeFrame()`` method of a Skit definition; they should remain plain figures.

And that's it! The ``Tracker`` Skit is now fully defined! Now we just need to instantiate an instance of it so we can animate it and watch it in action. This can be done like any other figure:

```python
class Tracker(morpho.Skit):
    def makeFrame(self):
        # The t value is stored as a tweenable attribute
        # of the tracker itself. Let's extract it just
        # to simplify the later syntax.
        t = self.t

        # The label's text is just the t-value converted
        # into a string.
        label = morpho.text.Text(str(t))

        return label

# Construct an instance of our new Tracker Skit.
# By default, t is initialized to t = 0.
mytracker = Tracker()

# Turn it into an actor, and have its t value progress
# to the number 1 over the course of 2 seconds (60 frames)
mytracker = morpho.Actor(mytracker)
mytracker.newendkey(60)
mytracker.last().t = 1

movie = morpho.Animation(mytracker)
movie.play()
```

And.... well, it works, but it's honestly pretty ugly. This is because it's trying to display all 15 decimal places after the decimal point every single frame, but some values of ``t`` are nice and round (like ``t = 0.5`` or ``t = 0.25``) and so it's constantly shifting from showing 15 decimals to showing only a few, and so you can't really make anything out.

One way to improve this would be to truncate the string in advance:

```python
# The label's text is just the t-value converted
# into a (truncated) string.
# In this case, take only the first 5 characters.
label = morpho.text.Text(str(t)[:5])
```

This is admittedly better, though you can still see a bit of jumping as it passes very round numbers like ``0.5``. Another thing we can do is make the text left-aligned, so the presence or absence of trailing digits won't affect the position of the text:

```python
label = morpho.text.Text(str(t)[:5], anchor_x=-1)
```

That's a lot better! However, it required us to left-align the text. It would be nice if we could somehow preserve center alignment, but perhaps have it append trailing zeros in the cases where there are round numbers, but not otherwise. Luckily, there is a tool to facilitate doing just that. Use the ``Number`` class:

```python
class Tracker(morpho.Skit):
    def makeFrame(self):
        # The t value is stored as a tweenable attribute
        # of the tracker itself. Let's extract it just
        # to simplify the later syntax.
        t = self.t

        # Create a "number" object based on the value t,
        # but auto-rounds it to the third decimal place
        # and always displays three digits to the right
        # of the decimal place, appending zeros if necessary.
        number = morpho.text.Number(t, decimal=3, rightDigits=3)

        # The label's text is the stringified version of
        # the "number" object, which does the job of
        # rounding and appending trailing zeros for us.
        label = morpho.text.Text(str(number))

        return label
```

Now that looks pretty good! So congratulations! You've just built your first Skit, and a useful one, too: I use trackers quite frequently in my animations.

## Followers

Another good use of Skits is to make what I call a "follower". This is a way to make a figure move along a path (it "follows" the path).

Let's do an example. Let's say I want to have a ``Point`` figure move along a ``Path`` figure over the course of 2 seconds. Let's first define the path:

```python
# Create a curved path that begins at x = -4 and ends at x = +4
path = morpho.graph.realgraph(lambda x: 0.2*(x**3 - 12*x), -4, 4)
```

Now we'll define our *Follower* Skit:

```python
# Create a curved path that begins at x = -4 and ends at x = +4
path = morpho.graph.realgraph(lambda x: 0.2*(x**3 - 12*x), -4, 4)

class Follower(morpho.Skit):
    def makeFrame(self):
        t = self.t

        # Create a generic Point figure
        point = morpho.grid.Point()
        # Set the position of the point to be the path's
        # position at parameter t.
        point.pos = path.positionAt(t)

        return point
```

I've actually used a new method we haven't encountered before. ``Path`` figures possess a ``positionAt()`` method which will return the position of the point that is a given proportion ``t`` along the path (``t = 0`` means the path's beginning, ``t = 1`` means the path's end). This is a perfect function to plug our follower's ``t`` value in to!

With that, the Skit is fully defined, so let's see it in action! To do it, we instantiate an instance of our new ``Follower`` class, and this time, just to change things up from before, let's have the point move along the path backwards: so right-to-left this time:

```python
# Create a curved path that begins at x = -4 and ends at x = +4
path = morpho.graph.realgraph(lambda x: 0.2*(x**3 - 12*x), -4, 4)

class Follower(morpho.Skit):
    def makeFrame(self):
        t = self.t

        # Create a generic Point figure
        point = morpho.grid.Point()
        # Set the position of the point to be the path's
        # position at parameter t.
        point.pos = path.positionAt(t)

        return point

# Set the follower to begin at the END of the path,
# just to change things up a little.
myfollower = Follower(t=1)

# Turn it into an actor, and set its t value to be 0
# after 2 seconds (60 frames) have passed.
myfollower = morpho.Actor(myfollower)
myfollower.newendkey(60)
myfollower.last().t = 0

# Include both the original path and the follower, so
# we can clearly see that the follower is following the
# intended path.
movie = morpho.Animation(morpho.Layer([path, myfollower]))
movie.play()
```
> **Note:** By default, the ``t`` value of a Skit is set to 0 when initialized. You can supply a different initial value by passing it to the constructor like in the above code with ``Follower(t=1)``, but note that this can only be done by *keyword*. So ``Follower(t=1)`` works, but ``Follower(1)`` will not.

And there you have it! Our point figure *follows* the specified path! You've just constructed your first basic Follower Skit! But why stop here? Let's be a little adventurous and add some cool stuff to our follower. How about a label that tracks the coordinates of the point as it moves along the path? So let's edit our ``Follower`` class like this:

```python
class Follower(morpho.Skit):
    def makeFrame(self):
        t = self.t

        # Create a generic Point figure
        point = morpho.grid.Point()
        # Set the position of the point to be the path's
        # position at parameter t.
        point.pos = path.positionAt(t)

        # Create Number objects out of the coordinates
        # to handle rounding and trailing zeros.
        x,y = point.pos.real, point.pos.imag
        xnum = morpho.text.Number(x, decimal=2, rightDigits=2)
        ynum = morpho.text.Number(y, decimal=2, rightDigits=2)

        # Create coordinate label
        label = morpho.text.Text(
            "("+str(xnum)+", "+str(ynum)+")",
            pos=point.pos, anchor_y=-1,
            size=36, color=[0,1,0]
            )

        return morpho.Frame([point, label])
```
> **Note:** Our Skit now contains two figures that need to be drawn on any given frame. So we now need to group them into a single composite figure. That's what the ``Frame`` figure is for. The ``Frame`` figure allows the grouping together of an arbitrary list of figures into a single composite figure.

Awesome! But why not get fancier still? I notice that the coordinate label gets clipped off screen near the ends of the path. How about we make it so that the horizontal alignment of the label gradually shifts from right alignment at the far right, to left alignment at the far left:

```python
# Create coordinate label
label = morpho.text.Text(
    "("+str(xnum)+", "+str(ynum)+")",
    pos=point.pos, anchor_y=-1,
    size=36, color=[0,1,0]
    )
# Anchor is +1 when t = 1, but -1 when t = 0
label.anchor_x = morpho.lerp(-1, 1, t)
```
> **Note:** The function ``morpho.lerp()`` stands for "linear interpolation", and it basically linearly interpolates between -1 and 1 (in this case) according to the interpolation parameter ``t`` (``t = 0`` is the left endpoint, ``t = 1`` is the right endpoint).

That's looking pretty clean! And if you've understood what's been going on in the code so far, I think you've got a pretty robust understanding of how Skits work and all the various things you can do with them. So at this point, let's allow our imaginations to run wild and try some even fancier stuff.

## Tangent Line Skit

Let's build a Skit that has a tangent line slide along the curve. As for the curve, we'll recycle the one we used for the Follower.
```python
f = lambda x: 0.2*(x**3 - 12*x)
path = morpho.graph.realgraph(f, -4, 4)
```
To find the tangent line at a point, we'll need the derivative of this function. This function is simple enough that we can do it by hand if we really want to, but we can also just use a rough approximation:

```python
f = lambda x: 0.2*(x**3 - 12*x)
path = morpho.graph.realgraph(f, -4, 4)

# Define a numerical derivative function
dx = 0.000001  # A small change in x
df = lambda x: (f(x+dx)-f(x-dx))/(2*dx)
```

Now let's set up our Skit:

```python
class TangentLine(morpho.Skit):
    def makeFrame(self):
        # t will represent the input to the function f
        t = self.t

        # Initialize tangent line to be a horizontal
        # line segment of length 4 centered at the
        # origin
        line = morpho.grid.Path([-2,2])
        line.color = [1,0,0]  # Red color

        # Compute derivative
        slope = df(t)
        # Convert into an angle and set it as the rotation
        # of the line segment
        angle = math.atan(slope)
        line.rotation = angle

        # Position the tangent line at the tangent point
        x = t
        y = f(t)
        line.origin = x + 1j*y

        return line
```

And now let's initialize the Skit and have it slide from ``t = -4`` to ``t = +4``:

```python
# Initialize the tangent line Skit
tanline = TangentLine()
tanline.t = -4  # Set initial t to -4
tanline.transition = morpho.transitions.quadease

# Convert to actor and set t to +4 over
# the course of 5 seconds (150 frames)
tanline = morpho.Actor(tanline)
tanline.newendkey(150)
tanline.last().t = 4

movie = morpho.Animation(morpho.Layer([path, tanline]))
movie.play()
```

Cool! And just like before, we can easily add more frills to the Skit if we want: like a derivative tracker:

```python
class TangentLine(morpho.Skit):
    def makeFrame(self):
        # t will represent the input to the function f
        t = self.t

        # Initialize tangent line to be a horizontal
        # line segment of length 4 centered at the
        # origin
        line = morpho.grid.Path([-2,2])
        line.color = [1,0,0]  # Red color

        # Compute derivative
        slope = df(t)
        # Convert into an angle and set it as the rotation
        # of the line segment
        angle = math.atan(slope)
        line.rotation = angle

        # Position the tangent line at the tangent point
        x = t
        y = f(t)
        line.origin = x + 1j*y

        # Create derivative tracker
        slopenum = morpho.text.Number(slope, decimal=3, rightDigits=3)
        dlabel = morpho.text.Text("Slope = "+str(slopenum),
            pos=line.origin, anchor_y=-1,
            size=36, color=[1,1,0]
            )
        dlabel.rotation = angle

        return morpho.Frame([line, dlabel])
```

## A Warning About Images

There is no restriction on what figures you can construct within the ``makeFrame()`` method of a Skit class, so you can even include ``Image`` and ``MultiImage`` figures. However, I recommend treating these a little differently than all other figures within a Skit.

Let's consider our point follower skit again, and let's say we substitute our ``Point`` figure for an ``Image`` figure. Our code might look something like this:

```python
class Follower(morpho.Skit):
    def makeFrame(self):
        t = self.t

        # Create an Image figure from "ball.png"
        ball = morpho.graphics.Image("./ball.png")
        ball.height = 0.75
        # Set the position of the image to be the path's
        # position at parameter t.
        ball.pos = path.positionAt(t)

        return ball
```

However, I don't think this is the best practice for using images within Skits. The reason is the method ``makeFrame()`` is actually called on every single frame draw of an animation. And right now, it calls for the construction of a new ``Image`` figure on every single frame draw, which could result in it having to read the image file in from disk *every single frame draw*, which is not efficient.

To get around this, I usually define a generic base Image figure *outside* of ``makeFrame()``, and use it as the source when constructing an Image figure *within* ``makeFrame()``. Something like this:

```python
ballimage = morpho.graphics.Image("./ball.png")
class Follower(morpho.Skit):
    def makeFrame(self):
        t = self.t

        # Create an Image figure from "ball.png"
        ball = morpho.graphics.Image(ballimage)
        ball.height = 0.75
        # Set the position of the image to be the path's
        # position at parameter t.
        ball.pos = path.positionAt(t)

        return ball
```

Notice that at the top, I define a generic Image figure called ``ballimage`` whose source is the actual ``ball.png`` file on disk. But within ``makeFrame()``, the Image figure ``ball`` is constructed using the figure ``ballimage`` as its source. This causes Morpho to reuse the internal source image from ``ballimage`` for the new Image figure ``ball``. All of this should happen only in memory, so the disk is accessed only once here: when the original ``ballimage`` base figure was constructed, and not every single frame draw within ``makeFrame()``.

## Multi-Parameter Skits

So far I've explained Skits as being like parametric figures: They take an input ``t`` and output a figure (or a ``Frame`` of figures), but actually, Skits can support multiple parameters---as many as you want, in fact, and with any name and default value. This can be used to make even fancier Skits, or indeed, even allow you to create brand new figure types with custom tweenables.

Let's start by further spicing up our tangent line Skit. Right now the tangent line segment has a constant length, but how about we make it variable? To do that, we'll need a new parameter (let's call it ``length``). To create multiple parameters for a Skit, use the ``SkitParameters`` decorator upon defining the class:

```python
@morpho.SkitParameters(["t", "length"])
class TangentLine(morpho.Skit):
```

``SkitParameters`` is itself a function that takes a list of strings as input. The list of strings become the names of the Skit's parameters. They are all set to an initial value of ``0``, but if you want to specify alternative default values, pass a *dictionary* into the ``SkitParameters()`` decorator instead:

```python
@morpho.SkitParameters({"t":-4, "length":4})
class TangentLine(morpho.Skit):
```

or just pass them in as keyword arguments:

```python
@morpho.SkitParameters(t=-4, length=4)
class TangentLine(morpho.Skit):
```

Now let's modify the contents of ``makeFrame()`` to take advantage of our new parameter ``length``:

```python
@morpho.SkitParameters(t=-4, length=4)
class TangentLine(morpho.Skit):
    def makeFrame(self):
        # t will represent the input to the function f
        t = self.t
        length = self.length

        # Initialize tangent line to be a horizontal
        # line segment of length 4 centered at the
        # origin
        line = morpho.grid.Path([-length/2, length/2])
        line.color = [1,0,0]  # Red color

        # Compute derivative
        slope = df(t)
        # Convert into an angle and set it as the rotation
        # of the line segment
        angle = math.atan(slope)
        line.rotation = angle

        # Position the tangent line at the tangent point
        x = t
        y = f(t)
        line.origin = x + 1j*y

        # Create derivative tracker
        slopenum = morpho.text.Number(slope, decimal=3, rightDigits=3)
        dlabel = morpho.text.Text("Slope = "+str(slopenum),
            pos=line.origin, anchor_y=-1,
            size=36, color=[1,1,0]
            )
        dlabel.rotation = angle

        return morpho.Frame([line, dlabel])
```

Note that we assigned ``length = self.length`` at the beginning just like we do for ``t``. This is actually an optional step, but I usually prefer to "extract" the parameters from the attributes of ``self`` just to make it easier to work with them in the code (it also protects us from accidentally modifying their values). The other change is to the definition of ``line``: we made the ``Path`` extend from ``-length/2`` to ``+length/2`` which will now give our tangent line a variable length depending on the value of the ``length`` parameter.

Now let's try it out. We'll recycle the code from before, but now let's have the tangent line grow out of the tangent point as it moves along the curve:

```python
# Initialize the tangent line Skit
tanline = TangentLine()
tanline.t = -4  # Set initial t to -4
tanline.length = 0  # Initial length is zero
tanline.transition = morpho.transitions.quadease

# Convert to actor and set t to +4 over
# the course of 5 seconds (150 frames)
tanline = morpho.Actor(tanline)
tanline.newendkey(150)
tanline.last().t = 4
tanline.last().length = 4

movie = morpho.Animation(morpho.Layer([path, tanline]))
movie.play()
```

Let's go one step further and we'll call it done with this tangent line Skit: Let's add a transparency parameter (``alpha``) so that we can make the tangent line fade when we're done:

```python
@morpho.SkitParameters(t=-4, length=4, alpha=1)
class TangentLine(morpho.Skit):
    def makeFrame(self):
        # t will represent the input to the function f
        t = self.t
        length = self.length
        alpha = self.alpha

        # Initialize tangent line to be a horizontal
        # line segment of length 4 centered at the
        # origin
        line = morpho.grid.Path([-length/2, length/2])
        line.color = [1,0,0]  # Red color
        line.alpha = alpha

        # Compute derivative
        slope = df(t)
        # Convert into an angle and set it as the rotation
        # of the line segment
        angle = math.atan(slope)
        line.rotation = angle

        # Position the tangent line at the tangent point
        x = t
        y = f(t)
        line.origin = x + 1j*y

        # Create derivative tracker
        slopenum = morpho.text.Number(slope, decimal=3, rightDigits=3)
        dlabel = morpho.text.Text("Slope = "+str(slopenum),
            pos=line.origin, anchor_y=-1,
            size=36, color=[1,1,0], alpha=alpha
            )
        dlabel.rotation = angle

        return morpho.Frame([line, dlabel])

# Initialize the tangent line Skit
tanline = TangentLine()
tanline.t = -4  # Set initial t to -4
tanline.length = 0  # Initial length is zero
tanline.transition = morpho.transitions.quadease

# Convert to actor and set t to +4 over
# the course of 5 seconds (150 frames)
tanline = morpho.Actor(tanline)
tanline.newendkey(150)
tanline.last().t = 4
tanline.last().length = 4

# Finally, fade the tangent line to invisibility
tanline.newendkey(30)
tanline.last().alpha = 0

movie = morpho.Animation(morpho.Layer([path, tanline]))
movie.play()
```

## Making a Pendulum

As our final project for this guide, let's build a Skit that animates a pendulum swinging back and forth. We'll also add some labels and trackers to it at the end.

We'll use the basic sinusoidal approximation for the motion of a pendulum---meaning the angle &theta; the pendulum makes from its neutral position is a sinusoidal function of time *t*. So the equation describing its motion might look something like this:

<p align="center">&theta;(<i>t</i>) = &theta;<sub>max</sub> sin(<i>t</i>)</p>

Let's start out simple with just a single parameter Skit where the default parameter ``t`` represents time. Given time ``t``, we'll compute the angle the pendulum makes from its neutral position according to the above formula. For now, we'll just hard code some semi-arbitrary values for &theta;<sub>max</sub> and the string's length.

```python
thetamax = pi/6  # Hard code thetamax for now
length = 3  # Hard code pendulum string length for now
class Pendulum(morpho.Skit):
    def makeFrame(self):
        t = self.t

        theta = thetamax*math.sin(t)
```

Now let's construct the pendulum's string. We'll use a basic two node path for the string. Let's have the string's anchor point located at the origin, and have it extend downward:

```python
# Create pendulum string
string = morpho.grid.Path([0, -length*1j])
```

But now we want to rotate the string according to the ``theta`` value we computed earlier. This can be easily accomplished by plugging in the ``theta`` angle into the string's ``rotation`` attribute!

```python
# Create pendulum string
string = morpho.grid.Path([0, -length*1j])
string.rotation = theta
```

Now we need to construct the ball hanging at the end of the string. Let's use a ``Point`` figure to do it, but we'll make it extra big and let's also make its border thickness match that of the string:

```python
ball = morpho.grid.Point()
ball.strokeWeight = string.width
ball.color = [1,1,1]  # Ball border is white
ball.size = 40  # Make it 40 pixels wide
```

But where should the ball be located? Well, at the end of the string, right? That would be the final node in the string's sequence of nodes, so let's assign it directly:

```python
ball = morpho.grid.Point()
ball.pos = string.seq[-1]
ball.strokeWeight = string.width
ball.color = [1,1,1]  # Ball border is white
ball.size = 40  # Make it 40 pixels wide
```

But here we hit a subtle problem. The final node of the string path is actually NOT where the end of the string will actually appear. This is because we rotated the string about the origin using its ``rotation`` attribute, and if you remember what I said in a previous guide about transformation tweenables, they do not modify the internal data of the figure, and their effect is computed at draw time. To solve this problem, let's *commit* the rotation transformation:

```python
# Create pendulum string
string = morpho.grid.Path([0, -length*1j])
string.rotation = theta
# Commit the rotation so that the string's
# final node can be used to position the ball.
string.commitTransforms()

# Create the ball hanging on the string.
# Its position is equal to the position of the
# final node of the string path
ball = morpho.grid.Point()
ball.pos = string.seq[-1]
ball.strokeWeight = string.width
ball.color = [1,1,1]  # Ball border is white
ball.size = 40  # Make it 40 pixels wide
```

And with that, I think we've got everything we need. So now let's package these two figures into a ``Frame`` and return them to complete the specification of ``makeFrame()``:

```python
thetamax = pi/6  # Hard code thetamax for now
length = 3  # Hard code pendulum string length for now
class Pendulum(morpho.Skit):
    def makeFrame(self):
        t = self.t

        theta = thetamax*math.sin(t)

        # Create pendulum string
        string = morpho.grid.Path([0, -length*1j])
        string.rotation = theta
        # Commit the rotation so that the string's
        # final node can be used to position the ball.
        string.commitTransforms()

        # Create the ball hanging on the string.
        # Its position is equal to the position of the
        # final node of the string path
        ball = morpho.grid.Point()
        ball.pos = string.seq[-1]
        ball.strokeWeight = string.width
        ball.color = [1,1,1]  # Ball border is white
        ball.size = 40  # Make it 40 pixels wide

        return morpho.Frame([string, ball])
```

Now let's try it out! Let's create an instance of our new Pendulum Skit and have it perform over the course of 5 seconds:

```python
pend = Pendulum()

# Set internal time parameter t to be 6pi
# after 5 seconds (150 frames) have passed
# in the animation's clock.
pend = morpho.Actor(pend)
pend.newendkey(150).t = 6*pi

movie = morpho.Animation(pend)
movie.play()
```

Not bad! Definitely looks like a pendulum swinging! Now let's add some extra stuff. How about we add a dashed vertical line representing the pendulum's neutral position, and also put in an arc that connects the neutral vertical line to the pendulum's string:

```python
class Pendulum(morpho.Skit):
    def makeFrame(self):
        t = self.t

        theta = thetamax*math.sin(t)

        # Create pendulum string
        string = morpho.grid.Path([0, -length*1j])
        string.rotation = theta
        # Commit the rotation so that the string's
        # final node can be used to position the ball.
        string.commitTransforms()

        # Create the ball hanging on the string.
        # Its position is equal to the position of the
        # final node of the string path
        ball = morpho.grid.Point()
        ball.pos = string.seq[-1]
        ball.strokeWeight = string.width
        ball.color = [1,1,1]  # Ball border is white
        ball.size = 40  # Make it 40 pixels wide

        # Create neutral vertical dashed line
        neutral = morpho.grid.Path([0, -length*1j])
        neutral.dash = [10,10]

        # Create connecting arc
        arc = morpho.shapes.EllipticalArc(
            pos=0, xradius=1, yradius=1,
            theta0=-pi/2, theta1=-pi/2+theta,
            )

        return morpho.Frame([neutral, arc, string, ball])
```
> ***CAUTION!*** When compiling the final ``Frame`` object at the end, make sure the figures go in the exact order above! This determines the draw order of the objects. We want the neutral dashed line behind everything else, followed by the arc and string, and finally have the ball drawn on top of everything else. If you change the order, the pendulum may not look quite like you expect (give it a try, if you want).

> **Note:** Actually, since the neutral vertical line does not move or change whatsoever throughout the Skit (and we don't anticipate that we will want it to change), it doesn't actually *have* to be a part of the Skit: We could alternatively have constructed it as a separate figure independent of the Skit and just have it hang around in the background. But what we did works fine, so this is just an FYI.

Looking fine! Actually, I've used a figure type we may not have encountered before: ``EllipticalArc``. This figure produces a segment of an ellipse, where you can specify the radii and angle interval for which to draw. In this case, I set one of the angle endpoints (``theta0``) to be -&pi;/2 so it constantly touches the dashed vertical line. The other angle endpoint (``theta1``) is set to be -&pi;/2 *plus* whatever the current deviation from neutral is.

Let's continue to add more stuff. How about an angle label for the arc?

```python
class Pendulum(morpho.Skit):
    def makeFrame(self):

        ...

        # Create connecting arc
        arc = morpho.shapes.EllipticalArc(
            pos=0, xradius=1, yradius=1,
            theta0=-pi/2, theta1=-pi/2+theta,
            )

        # Create theta label
        thetaLabel = morpho.text.Text("\u03b8",  # Unicode for theta
            pos=1.5*cmath.exp(1j*mean([arc.theta0, arc.theta1])),
            size=36, italic=True
            )

        return morpho.Frame([neutral, arc, thetaLabel, string, ball])
```

> **Note:** The formula ``1.5*cmath.exp(1j*mean([arc.theta0, arc.theta1]))`` computes the point that is 1.5 units away from the origin at an angle that is halfway between the two angle endpoints of the arc we produced. If you know Euler's Formula, hopefully it will be clearer to you how it works.

It looks fine, but it kind of overlaps with the string when the angle is close to zero. Let's have it shrink when it gets below a certain ``theta`` value:

```python
# Create theta label
thetaLabel = morpho.text.Text("\u03b8",  # Unicode for theta
    pos=1.5*cmath.exp(1j*mean([arc.theta0, arc.theta1])),
    size=min(36, 36*abs(theta/0.36)), italic=True
    )
```

The above code makes it so that if ``theta`` is below 0.36 radians, it will scale the label's size down proportional to ``theta``.

And finally, let's add a tracker off to the side that reports the current ``theta`` value, but in ***degrees***:

```python
class Pendulum(morpho.Skit):
    def makeFrame(self):

        ...

        thetanum = morpho.text.Number(theta*180/pi, decimal=0)
        tracker = morpho.text.Text(
            "\u03b8 = "+str(thetanum)+"\u00b0",
            pos=1j, size=56
            )

        return morpho.Frame([neutral, arc, thetaLabel, string, ball, tracker])
```
> ``\u00b0`` is unicode for the *degree* symbol (&#x00b0;)

All right, and with that, let's call it a day!

## Optional Exercises

If you'd like some additional practice working with Skits, you can try using them to animate the following:
  1. Animate some text moving in a circular path, but have the text's orientation rotate likewise so that you're always reading it along a tangent line to the circular path. Bonus points if you make the text a tracker which maybe reports the current angle of rotation.
  2. Animate a square which grows and shrinks, but put a tracker inside the square that constantly reports the current area of the square at any moment.
  3. Use a multi-parameter Skit to animate a rectangle with variable width and height which also displays an area tracker inside its borders.
  4. Animate a point moving along the spiral path described (parametrically with complex numbers) by *s*(*t*) = (*t*/4)e<sup>*tj*</sup> where *j* is the imaginary unit &#x221a;-1. But also attach an arrow to the point that indicates the *velocity* of the point at any given moment. The velocity of the point (as a complex number) at any time *t* is given by *v*(*t*) = (1+*tj*)/4 &#x00b7; e<sup>*tj*</sup>
  > **Note:** To raise e to a complex power in Python, import the ``cmath`` module and use ``cmath.exp()``.
  5. Create an epicycle! Animate two or more arrows connected tip to tail that are rotating about their tails at different frequencies. Bonus points if you can also trace out in real time the curve the final arrow draws as it moves.
  6. Consider an observer observing a plane flying horizontally overhead. Animate the line of sight connecting the observer to the plane as well as the angle the line of sight makes with the ground. For bonus points, include a tracker that reports the current angle of the line of sight.
  7. Animate two traveling waves that collide to form a standing wave.
