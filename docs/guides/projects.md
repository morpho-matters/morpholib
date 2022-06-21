---
layout: default
title: Morpho Guide -- Making Longer-Form Videos
---

# Morpho Guide: Making Longer-Form Videos

In this guide, we'll go over how to use Morpho to create longer animations and entire videos.

Now, since I really only have my own use case to go on for now, I'll mostly just be explaining my own personal process for video creation here. However, I think Morpho is a flexible enough tool to support multiple video-making schemes, and so I hope that by presenting my scheme, you'll get enough inspiration to come up with your own. You should absolutely modify, or even totally replace, my scheme to suit whatever your particular needs are.

## Organizing a Project

When working on a longer-form video, I divide up all the animation tasks into individual scenes, where the code for each scene is contained in its own separate, independent Python file. By "scene" I generally mean a single continuous stretch of animated video, each of which will eventually be separated from the others by a jump cut or other video transition in the final product. I like to keep these individual scene files all together in one folder, together with a subfolder called "resources" where I keep other files (mostly images) that need to be imported by some scenes.

After the animations of each scene are finished and sync'd up with the narration, all of the individual scenes are rendered as individual MP4 files and then assembled together with the audio using an external video editing program.

## Creating a Scene

### Header

At the top of every scene file is some header code that is almost always the same that handles importing all the necessary components from the Morpho library and defining useful constants, etc. There's endless room for customization here, and as you progress further in your own projects, you'll probably create your own custom header that you prefer.

For my own case, I generally use a header that looks like this:

```python
import morpholib as morpho
morpho.importAll()
mo = morpho  # Allows the shorthand "mo" to be optionally used instead of "morpho"

# Import particular transition functions into the main namespace
from morpholib.transitions import uniform, quadease, drop, toss, sineease, step
# Import useful functions and constants into the main namespace
from morpholib.tools.basics import *

# Import various other libraries
import math, cmath, random
import numpy as np

# Set default transition to quadease
morpho.transition.default = quadease
# Set default font to be the LaTeX font.
# Note you may have to install this font separately onto your system
# if you want to use it.
morpho.text.defaultFont = "CMU serif"

# Basic unit vectors for 3D animations
ihat = mo.array([1,0,0])
jhat = mo.array([0,1,0])
khat = mo.array([0,0,1])

# Particular colors are named here.
# Feel free to customize to your heart's content.
violet = tuple(mo.color.parseHexColor("800080"))
orange = tuple(mo.color.parseHexColor("ff6300"))
lighttan = tuple(mo.color.parseHexColor("f4f1c1"))

# Give a name unique to this scene file.
# It's used to allow this scene file to export a video file
# in parallel with other scene files.
morpho.anim.exportSignature = ""
```

### Body

Below the header is the body---the place for the animation code itself. I generally structure the body according to a specific scaffolding and construct the animations within that scaffolding according to a particular workflow pattern that I have found most helpful in navigating the messy process of creation, revision, etc. that goes into making complex animations.

I think it will be easiest to explain if we have a specific example scene to aim for. So let's construct a scene where we have a grid on which we draw a line and label it with the word "Linear" and then morph the line into a parabola while simultaneously morphing the label's text to the word "Quadratic".

### The `main()` function

To begin, we define a `main()` function beneath the header that will contain all the animation-specific code.
```python
def main():
    # Animation code will go here...

main()
```

The purpose of encapsulating the code within the `main()` function is to prevent accidentally overwriting any of the constants/functions/etc. defined in the header.

### Setup clause

At the top of `main()` we setup the layers and initialize the animation with basic display settings:
```python
def main():
    mainlayer = morpho.Layer(view=mo.video.view169())
    mation = morpho.Animation([mainlayer])
    # Display settings
    mation.windowShape = (1920, 1080)
    mation.fullscreen = True
    mation.background = lighttan
```

Here, we define one layer, `mainlayer`, and set its viewbox to be the 16:9 view of the complex plane where its lower and upper extents are `-10j` to `10j`. This viewbox can be conveniently accessed by calling `mo.video.view169()`. This layer is used as part of the Animation object named `mation`.

For our example scene we really only need one layer, but if you needed more, you would define any additional layers here at the top as well:
```python
mainlayer = morpho.Layer(view=mo.video.view169())
layer2 = mainlayer.copy()
layer3 = mainlayer.copy()
toplayer = mainlayer.copy()
lowlayer = mainlayer.copy()
mation = morpho.Animation([lowlayer, mainlayer, layer2, layer3, toplayer])
```
> **Note:** the order in which the layers are supplied to the `Animation()` constructor is important! Layers early in the list are drawn behind layers later in the list.

After defining the layers comes the display settings. Modify them as you see fit. In this case, the background color is set to a light tan color, where this color was defined in the header.

After this, I include the code to modify the layers' cameras if needed. For our example scene, I think the default view of the complex plane is a little too wide, so let's zoom in by a factor of 2:
```python
mainlayer.camera.first().zoomIn(2)
```

So here's our initial setup code in full:

```python
mainlayer = morpho.Layer(view=mo.video.view169())
mation = morpho.Animation([mainlayer])
# Display settings
mation.windowShape = (1920, 1080)
mation.fullscreen = True
mation.background = lighttan

mainlayer.camera.first().zoomIn(2)
```

### Playback clause

Before we start writing the actual code for animating the elements of our scene, the following code is used to define the playback behavior of the animation and should be placed after the setup clause:

```python
print("Animation length:", mation.seconds())
mation.endDelay(10*30)

mation.finitizeDelays(30)

# mation.start = mation.lastID()
mation.locatorLayer = mainlayer
mation.clickRound = 2
mation.clickCopy = True
# mation.newFrameRate(10)
mation.play()
```

The first line causes the animation's length in seconds to be printed to the console every time the code is run, which is handy.

`print("Animation length:", mation.seconds())`

The second line appends a 10 second pause to the animation's end that just acts as a little buffer to make splicing all of the scenes together in a video editor easier later on.

`mation.endDelay(10*30)`

The next line replaces all placeholder pauses in the animation with 1 second pauses. More on that later.

`mation.finitizeDelays(30)`

The next block contains some code that controls animation playback. I treat these lines like dynamic settings, and constantly change, comment, and uncomment these lines while composing the main animation code in order to control the playback while previewing the animations-in-progress.
```python
# mation.start = mation.lastID()
mation.locatorLayer = mainlayer
mation.clickRound = 2
mation.clickCopy = True
# mation.newFrameRate(10)
mation.play()
```

The first line (currently commented out) makes the animation display only the final frame when played. I usually uncomment this line while in the middle of constructing a piece of animation, and comment it out once I'm ready to preview that piece in motion.
```python
mation.start = mation.lastID()
```

The next three lines configure the locator layer. It's currently set to `mainlayer`, but in a multilayer animation, I will swap it out with other layers as needed.

The `clickRound` setting rounds the locator coordinates to whatever decimal place you specify. I like to set it to 2 so it rounds coordinates to the hundreths place.

Setting `clickCopy` to `True` causes every coordinate pair to also be copied to the clipboard, which I usually prefer to do so I can quickly paste the clicked coordinates into the code wherever I need it.
```python
mation.locatorLayer = mainlayer
mation.clickRound = 2
mation.clickCopy = True
```

The next line (currently commented out) is meant to modify the animation framerate for previewing purposes ***only*** (but not the final render!). I generally keep this commented out unless the animation is so complex that it plays sluggishly when previewed. Uncommenting it lowers the framerate, allowing for quicker previewing playback.
```python
mation.newFrameRate(10)
```


### The first chunk

Now let's tackle the actual meat of the animation code. This code should be sandwiched between the setup clause and the playback clause.

```python
def main():
    # Define layers here
    mainlayer = morpho.Layer(view=mo.video.view169())
    mation = morpho.Animation([mainlayer])
    # Display settings
    mation.windowShape = (1920, 1080)
    mation.fullscreen = True
    mation.background = lighttan

    mainlayer.camera.first().zoomIn(2)



    ### Main animation code goes here...



    print("Animation length:", mation.seconds())
    mation.endDelay(10*30)

    mation.finitizeDelays(30)

    # mation.start = mation.lastID()
    mation.locatorLayer = mainlayer
    mation.clickRound = 2
    mation.clickCopy = True
    # mation.newFrameRate(10)
    mation.play()

main()
```

As my videos are typically narration-driven with animation executed on cue according to the dialogue, I split the animation code for the scene into individual "chunks" with a placeholder pause after each chunk. For our example scene, our first chunk will have a line being drawn and labeled on top of a background grid. Let's start by creating the grid:

```python
# Define background grid
grid = mo.grid.mathgrid(
    view=[-9,9, -5,5],
    hsteps=1, vsteps=1,
    hcolor=[0,0.6,0], vcolor=[0,0,1],
    axesColor=[0,0,0],
    xaxisWidth=7, yaxisWidth=7
    )
```
> **Note:** Remember `mo` is a shorthand for `morpho`, as we defined in the header.

Now we'll turn it into an actor and add it to `mainlayer` using the `merge()` method:
```python
grid = mo.Actor(grid)
mainlayer.merge(grid)
```

The `merge()` method is handy to use in longer-form animations because it allows you to add actors to the layer one at a time instead of having to input the complete list of actors all at once when defining the layer. The `merge()` method also allows you to place actors at different points in the timeline, but more on that later.

Next, we'll create the line and animate it being drawn on the grid. We can define the line itself with `realgraph()`, but then we'll also set the `end` attribute of the resulting path figure to 0 so that we can update it to `end=1` in a new keyframe. This will create the drawing animation we want.

```python
# Define curve to initially be a line
curve = mo.graph.realgraph(lambda x: 2*x + 1, -3, 3)
curve.set(width=5, color=[1,0,0], end=0)
curve = mo.Actor(curve)
mainlayer.merge(curve)
curve.newendkey(30).end = 1  # Draw curve over 1 second (30 frames)
```

Now we'll add the text label. However, since we want this text label to appear AFTER the line has finished being drawn, we need to first store the frame number where the line finished animating. Since this corresponds to what is currently the end of the animation, we can grab this frame number by grabbing the current final frame (a.k.a. "index" or "ID") of the animation as a whole. Let's store this frame index value in a variable called `time`:

```python
time = mation.lastID()
```

Now we define the text label itself:

```python
time = mation.lastID()
# Create "Linear" label.
# MultiText is used so that we can morph the text later
label = mo.text.MultiText("Linear",
    pos=1+0.5j, size=64, color=[1,0,0], alpha=0
    )
```

Note how we set its `alpha` value to 0 so that it starts out invisible. We'll later update `alpha` to be 1 in a future keyframe so we get a *fade-in* animation. But first, we need to convert `label` into an Actor and add it to `mainlayer` at frame index `time`:

```python
label = mo.Actor(label)
mainlayer.merge(label, atFrame=time)
```

And now we'll create a new keyframe for the label where we set `alpha=1` so we get the fade-in effect:

```python
label.newendkey(20).alpha = 1
```

That's it! We're done animating this chunk, so we'll end it off with a line that inserts a placeholder pause at the end of the chunk. It will eventually be replaced once the narration is recorded, but more on that later.

```python
mation.endDelayUntil()
```

So here's our first chunk in its entirety:

```python
# Define background grid
grid = mo.grid.mathgrid(
    view=[-9,9, -5,5],
    hsteps=1, vsteps=1,
    hcolor=[0,0.6,0], vcolor=[0,0,1],
    axesColor=[0,0,0],
    xaxisWidth=7, yaxisWidth=7
    )
grid = mo.Actor(grid)
mainlayer.merge(grid)

# Define curve to initially be a line
curve = mo.graph.realgraph(lambda x: 2*x + 1, -3, 3)
curve.set(width=5, color=[1,0,0], end=0)
curve = mo.Actor(curve)
mainlayer.merge(curve)
curve.newendkey(30).end = 1  # Draw curve over 1 second

time = mation.lastID()
# Create "Linear" label.
# MultiText is used so that we can morph the text later
label = mo.text.MultiText("Linear",
    pos=1+0.5j, size=64, color=[1,0,0], alpha=0
    )
label = mo.Actor(label)
mainlayer.merge(label, atFrame=time)
label.newendkey(20).alpha = 1

mation.endDelayUntil()
```

### Morphing to a quadratic

After the first chunk, I like to precede each successive chunk with a line that prints the current animation length so far---basically printing to the console the time at which the following chunk will start animating. This will be useful later on when synchronizing the animation to the narration.

In this chunk we'll be morphing the line to a parabola, so begin this chunk with the following line:
```python
print("Morph line to parabola:", mation.seconds())
```

Next, store the new current final frame number of the animation into the variable `time`, again.
```python
time = mation.lastID()
```
We will need to do this at the beginning of each successive chunk from now on because we are no longer at the beginning of the animation and we need to tell `mainlayer` where to begin animating the new actors we define here.

To get the morphing animation to begin at the start of this chunk, we need to create a new key for the line at frame `time`:

```python
time = mation.lastID()
curve.newkey(time)
```

Now we'll create the parabola figure

```python
time = mation.lastID()
curve.newkey(time)
quadratic = mo.graph.realgraph(lambda x: x**2, -3, 3)
quadratic.set(width=5, color=violet)
```

and then assign this curve to a new keyfigure of `curve` to have it morph into the parabola:

```python
time = mation.lastID()
curve.newkey(time)
quadratic = mo.graph.realgraph(lambda x: x**2, -3, 3)
quadratic.set(width=5, color=violet)
curve.newendkey(30, quadratic)
```

Note that the line `curve.newkey(time)` is important here, as it defines the starting point for the morphing animation. If we omitted it, our line figure would morph into a parabola too soon: it would start morphing *immediately* after its drawing animation finished during the previous chunk while the "Linear" label is still fading in. But including the line `curve.newkey(time)` here causes the line to remain static on screen after its initial animation finishes, until the start of this new chunk.

All right, now let's also have the "Linear" label morph into the word "Quadratic" at the same time while the line is morphing into a parabola. Let's also change its position and color while we're at it. To do it, add the following two lines:

```python
label.newkey(time)  # Don't start morphing until this chunk starts
label.newendkey(30).set(text="Quadratic", pos=2.5+0.5j, color=violet)
```

Playing the animation, you should see the line and label morph together at the same time. If instead you wanted the label to morph after the line finishes morphing into a parabola, this can be accomplished by adding a new `time = mation.lastID()` line immediately before the new label code:

```python
time = mation.lastID()  # Label morphs after curve finishes morphing
label.newkey(time)
label.newendkey(30).set(text="Quadratic", pos=2.5+0.5j, color=violet)
```

Now we end off the chunk with another placeholder pause. Here's the code for this chunk in full:

```python
print("Morph to quadratic:", mation.seconds())

time = mation.lastID()
curve.newkey(time)
quadratic = mo.graph.realgraph(lambda x: x**2, -3, 3)
quadratic.set(width=5, color=violet)
curve.newendkey(30, quadratic)

label.newkey(time)  # Don't start morphing until this chunk starts
label.newendkey(30).set(text="Quadratic", pos=2.5+0.5j, color=violet)

mation.endDelayUntil()
```

### Fading out

We can keep adding new chunks in the same way as we added the previous chunk; however many we need. But for this example, let's end it off by putting in one final chunk where we fade the curve and label away. We'll do it with this code:

```python
print("Fade everything out:", mation.seconds())

time = mation.lastID()

# Fade curve
curve.newkey(time)
curve.newendkey(30).alpha = 0

# Simultaneously fade the label
label.newkey(time)
label.newendkey(30).alpha = 0
```

Since this is the final chunk, we don't have to end it with a placeholder pause, as the playback clause already inserts a 10 second delay buffer at the end anyway.


### Export clause

Now that we're done constructing the scene, we can export it as a video file. Note that this requires you to have [FFmpeg](https://ffmpeg.org/) installed on your system and included in your PATH environment variable.

Before exporting, be sure the playback clause has the the following lines commented out:
```python
mation.start = mation.lastID()
mation.newFrameRate(10)
mation.play()
```

This disables the animation being played when the code is run, and also ensures the entire animation gets exported and at the correct framerate.

Below the playback clause, insert this line to export the animation as an MP4 file:

```python
mation.export("./animation.mp4")
```

which exports the animation to a video file called "animation.mp4" in the same folder as your Python file resides.

Currently, the animation is set to a framerate of 30 fps, but in my videos, I prefer them to run at 60 fps. So I usually include an additional line of code immediately before the export command to change the framerate to its final render value:

```python
mation.newFrameRate(60)
mation.export("./animation.mp4")
```


### Syncing to audio

At this point, the animation is finished as far as the essentials are concerned, but currently the animation has placeholder pauses of 1 second between each of the chunks. In the final video, these should be replaced with precise pauses of just the right lengths to sync up properly with the narration. We'll go over how to do that now.

> **Note:** On its own, Morpho cannot insert any audio into a video. That's a job for an external video editing program. However, what we **can** do here is tweak the animation pauses so that the silent video file Morpho outputs is in sync with the audio, and can be combined easily in video editing software.

In the code we have so far, the placeholder pauses are created by the various `mation.endDelayUntil()` calls that are spread thruout the code. But it only does this because we have called `endDelayUntil()` with no inputs. The actual use of `endDelayUntil()` is to cause the animation to pause at its current endpoint *UNTIL* a given point in time.

To see how it works, let's say that you've recorded some narration for this animation, and after carefully reviewing the audio in an audio editor, you conclude that you would like the line to morph into a parabola starting at 3 seconds into the audio, and would like to have the figures fade out at the 6.25 second mark. In that case, simply supply the following inputs into the two `mation.endDelayUntil()` calls we have in the code:

```python
mation.endDelayUntil(3*30)
print("Morph to quadratic:", mation.seconds())

...etc...

mation.endDelayUntil(6.25*30)
print("Fade everything out:", mation.seconds())
```

Note that we have to multiply both numbers by 30 to convert seconds into frames. Remember that virtually all measurements of time in Morpho are in units of frames.

To test it, comment out `mation.play()` in the playback clause, and run the code. If all has gone well, the console should print out the timings of the two checkpoints as 3 seconds and 6.25 seconds respectively (note these may not be exactly 3 and 6.25 because the times will be rounded to the nearest frame).

Sometimes it happens that an animation may transpire slower, or the audio go faster, than you first expected. In such a case, you may have accidentally set the `endDelayUntil()` value of a chunk to be a time BEFORE the chunk actually ends. In this case, Morpho will throw an error and will report to you how many frames too early your delay-until point occurred, so you know how to adjust your animation and/or audio to correct it (e.g. by speeding up your animation, or inserting a pause in your audio).

```python
mation.endDelayUntil(3*30)
print("Morph to quadratic:", mation.seconds())

...etc...

# This line will throw an error saying the "until" value occurs
# 15 frames before the animation's (i.e. chunk's) end.
mation.endDelayUntil(3.5*30)
print("Fade everything out:", mation.seconds())
```

To more thoroughly test the audio is syncing up correctly, I usually export the animation as a very low quality video file and then play it while simultaneously playing the audio in a separate program. To do that, I modify the export clause like this:

```python
mation.newFrameRate(8)  # Make the framerate very low
mation.export("./animation.mp4", scale=1/4)  # Very low res
```

The low quality settings make the export finish much faster, but the video will still play well enough that I can tell if the audio is sync'd up. If it looks good, then I revert the quality settings back to full, and the animation code is ready for final rendering at any time.

```python
mation.newFrameRate(60)
mation.export("./animation.mp4", scale=1)
```

> **Note:** The `scale` value should always be less than or equal to 1. Setting `scale` greater than 1 will not actually improve the resolution.



## Streamlining the Code

So that's the basics of my process for creating a single scene in a video. However, after having used Morpho to create so many scenes for so many videos, I've developed a number of shortcuts that speed up certain animation tasks that occur very frequently. I'll show you them now.

> ***CAUTION!*** Please note that what I've shown in this guide so far really is the core pattern to follow, and you shouldn't come to rely on the shortcuts without a solid understanding of the core patterns. This is because the shortcuts really only work in specific (albeit common) situations, and so you need to know when they won't work and you'll need to fall back on the core patterns.

### The `append()` method

We've been using `merge()` to add actors to a layer, but there is a method called `append()` which does the same thing, except it merges the given actor to the layer at that layer's current final frame index:

```python
# The following lines are equivalent
mylayer.append(myactor)
mylayer.merge(myactor, atFrame=mylayer.lastID())
```

The `append()` method can remove the need to constantly be assigning `time = mation.lastID()` and doing `merge(atFrame=time)`. If you want to add a new actor to a layer *precisely* at the current end of that layer's timeline, you can just use `append()`.

For example, in our code, we merged the text label into `mainlayer` at frame index `time`, where `time` was defined to be the animation's current final frame:

```python
time = mation.lastID()
label = mo.text.MultiText("Linear",
    pos=1+0.5j, size=64, color=[1,0,0], alpha=0
    )
label = mo.Actor(label)
mainlayer.merge(label, atFrame=time)
```

But in this case, since we're only dealing with a single layer thruout (`mainlayer`), the final frame of the animation is the same as the final frame of `mainlayer`, so we can eliminate the `time = mation.lastID()` call and just use `append()` instead to streamline the code:

```python
label = mo.text.MultiText("Linear",
    pos=1+0.5j, size=64, color=[1,0,0], alpha=0
    )
label = mo.Actor(label)
mainlayer.append(label)
```

#### Limitations

This is great and all, but there are some limitations to when you can use `append()`. It's great for adding actors to a single layer one after the other in time,
```python
# These actors will appear one after the other in time
mylayer.append(myfirstactor)
mylayer.append(mysecondactor)
```
but if you want to add two actors to a layer at the exact same frame, `append()` is probably not what you want to use. In this case, using `merge()` with `time` makes more sense:
```python
# These actors will appear at the exact same time
time = mation.lastID()
mylayer.merge(myfirstactor, atFrame=time)
mylayer.merge(mysecondactor, atFrame=time)
```

You also have to be careful using `append()` in a multilayer animation, because `append()` only appends actors to the end of that layer's ***local*** timeline, not the global timeline of the entire animation.

For example, let's say you have two point actors, `pt1` and `pt2`, that you want to appear in the animation one after the other, but they need to belong to two separate layers, `layer1` and `layer2`. If you try to use `append()` like this,

```python
layer1.append(pt1)
layer2.append(pt2)
```

the two point actors will not appear one after the other, because each actor will be appended to the end of its respective layer's *local* timeline. To make them properly appear one after the other in the global animation timeline, there's no escaping using the `time` pattern:

```python
layer1.append(pt1)
time = mation.lastID()
layer2.merge(pt2, atFrame=time)
```

### Actor actions

Actor actions, or just *actions* for short, are built-in mini routines that automatically implement certain common, simple animations, typically opening animations (making an actor appear on screen) and closing animations (making an actor disappear from the screen).

For example, in our code, we introduced the line actor by having it get "drawn" as if with a pen, and we had the "Linear" label appear by fading it in from invisibility. Both of these are types of opening animations, and they're both very common for paths and text labels. Because they're so common, `Path` actors and `Text` actors come built-in with two *actions* that handle creating these opening animations for you.

The one for the line is called `growIn()`, and causes a path to "grow" into its final state starting from its initial node.

The one for the text label is called `fadeIn()`, and does exactly what you think: it causes the actor to "fade in" to full visibility from invisibility.

In our example code, we implemented both of these opening animations manually. For the line actor, we did it by setting `end=0` and then later updating it to `end=1`. For the text label, we did it by setting `alpha=0` and then later updating it to `alpha=1`.

```python
# Define curve to initially be a line
curve = mo.graph.realgraph(lambda x: 2*x + 1, -3, 3)
curve.set(width=5, color=[1,0,0], end=0)
curve = mo.Actor(curve)
mainlayer.merge(curve)
curve.newendkey(30).end = 1  # Draw curve over 1 second (30 frames)

# Create "Linear" label.
# MultiText is used so that we can morph the text later
label = mo.text.MultiText("Linear",
    pos=1+0.5j, size=64, color=[1,0,0], alpha=0
    )
label = mo.Actor(label)
mainlayer.append(label)
label.newendkey(20).alpha = 1
```

But we can produce this effect automatically by using *actions*, like this:

```python
# Define curve to initially be a line
curve = mo.graph.realgraph(lambda x: 2*x + 1, -3, 3)
curve.set(width=5, color=[1,0,0])  # No longer need to say end=0
curve = mo.Actor(curve)
mainlayer.merge(curve)
curve.growIn(duration=30)

# Create "Linear" label.
# MultiText is used so that we can morph the text later
label = mo.text.MultiText("Linear",
    pos=1+0.5j, size=64, color=[1,0,0]  # No longer need to say alpha=0
    )
label = mo.Actor(label)
mainlayer.append(label)
label.fadeIn(duration=20)
```

Note how we don't have to specify `end=0` and `alpha=0` for the starting keyfigures anymore. All of that is handled by the `growIn()` and `fadeIn()` actions.

At the end of our animation, we had both the curve and the label fade out to invisibility. We implemented it manually, but we could use the `fadeOut()` action instead:

```python
time = mation.lastID()
# Fade curve and label
curve.newkey(time)
curve.fadeOut(duration=30)
label.newkey(time)
label.fadeOut(duration=30)
```

> ***CAUTION!*** The `newkey(time)` calls are important here! By default, actions act starting on the given ***actor's*** current final frame, not the layer's final frame. If you omit the `newkey(time)` calls, the fade outs may occur too early.

However, this can be streamlined even further: If you want to apply the same action to *multiple* actors all at once, you can use the following syntax:

```python
time = mation.lastID()
# Fade curve and label
morpho.action.fadeOut([curve, label], atFrame=time, duration=30)
```

which also enables another neat feature: staggering. By passing in another optional parameter called `stagger` into the `fadeOut()` action, you can cause each actor to fade out slightly out of sync with each other by a time difference you specify. For example, setting `stagger=15` causes each actor to start fading out 15 frames *after* the previous actor in the list starts fading out, leading to a kind of "staggered" fade out animation:

```python
time = mation.lastID()
# Fade curve and label
morpho.action.fadeOut([curve, label], atFrame=time, duration=30, stagger=15)
```

`fadeIn()` and `fadeOut()` also support an optional parameter called `jump` which causes the affected actors to move a certain amount in a certain direction while fading in or out. For example, setting `jump=2j` causes each actor to "jump" 2 units upward while fading in/out:

```python
time = mation.lastID()
# Fade curve and label
morpho.action.fadeOut([curve, label],
    atFrame=time, duration=30, stagger=15, jump=2j)
```

You can apply this on `fadeIn()` as well, which is how I accomplish the fade jump animations in my videos:

```python
# Create "Linear" label.
# MultiText is used so that we can morph the text later
label = mo.text.MultiText("Linear",
    pos=1+0.5j, size=64, color=[1,0,0]  # No longer need to say alpha=0
    )
label = mo.Actor(label)
mainlayer.append(label)
label.fadeIn(duration=20, jump=1j)
```

#### Limitations

Actions are a relatively recent addition to Morpho, and they are not fully supported for all figure types yet (probably the most notable deficiency right now is that actions don't really work on mathgrids yet). So it's best not to get overly reliant on them. You should still make sure you master implementing opening and closing animations manually if you need to.



## Bookmarking

Here's one last trick: If you're working on animating a very long scene, you may want to preview only a single chunk of the animation without having to wait for all the previous chunks to play thru first. You can do that by including this line at the appropriate point in your code:

```python
mation.start = mation.lastID()
```

For example, let's say we want to preview the fade out animation without having to wait thru watching all the previous animations. We can do that by inserting the above line at the beginning of the fade out chunk:

```python
print("Fade everything out:", mation.seconds())

mation.start = mation.lastID()  # Bookmark

time = mation.lastID()
# Fade curve and label
morpho.action.fadeOut([curve, label],
    atFrame=time, duration=30, stagger=15, jump=2j)
```

To restore the animation playback to normal, you can just comment out `mation.start = mation.lastID()`. You can uncomment it again whenever you need to, and so it acts kind of like a playback "bookmark" in your code allowing you to skip to whatever part of the scene you want when previewing.

## More Example Code

You can find the full code of the example scene we worked on in this guide [here.](https://github.com/morpho-matters/morpholib/blob/master/examples/example4.py)

If you'd like to see more examples of how I use Morpho to create videos, I've posted the source code for some of my projects [here.](https://github.com/morpho-matters/video-code)
