---
layout: default
title: Morpho Guide -- Making Longer-Form Videos
---

# Morpho Guide: Making Longer-Form Videos

> **Note:** This guide is only for Morpho 0.6.1+. For older versions, see [this guide](https://morpho-matters.github.io/morpholib/guides/old/projects-old).

In this guide, we'll go over how to use Morpho to create longer animations and entire videos.

Now, since I really only have my own use case to go on for now, I'll mostly just be explaining my own personal process for video creation here. However, I think Morpho is a flexible enough tool to support multiple video-making schemes, and so I hope that by presenting my scheme, you'll get enough inspiration to come up with your own. You should absolutely modify, or even totally replace, my scheme to suit whatever your particular needs are.

## Organizing a Project

When working on a longer-form video, I divide up all the animation tasks into individual scenes, where the code for each scene is contained in its own separate, independent Python file. By "scene" I generally mean a single continuous stretch of animated video, each of which will eventually be separated from the others by a jump cut or other video transition in the final product. I like to keep these individual scene files all together in one folder, together with a subfolder called "resources" where I keep other files (mostly images) that need to be imported by some scenes. You can find the source code for some of my projects [here.](https://github.com/morpho-matters/video-code)

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
from morpholib.transitions import uniform, quadease, drop, toss, sineease
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

# Particular colors are named here.
# Feel free to customize to your heart's content.
violet = tuple(mo.color.parseHexColor("800080"))
orange = tuple(mo.color.parseHexColor("ff6300"))
lighttan = tuple(mo.color.parseHexColor("f4f1c1"))
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

Here, we define one layer, `mainlayer`, and set its viewbox to be the 16:9 view of the complex plane centered at the origin where its lower and upper extents are `-10j` to `10j`. This viewbox can be conveniently accessed by calling `mo.video.view169()`. This layer is used as part of the Animation object named `mation`.

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
mation.wait(10*30)

mation.finitizeDelays(30)

# mation.start = mation.lastID()
mation.locatorLayer = mainlayer
mation.clickRound = 2
mation.clickCopy = True
# mation.newFrameRate(10)
mation.play()
```

`print("Animation length:", mation.seconds())`

The first line causes the animation's length in seconds to be printed to the console every time the code is run, which is handy.

`mation.wait(10*30)`

The second line appends a 10 second pause to the animation's end that just acts as a little buffer to make splicing all of the scenes together in a video editor easier later on.

`mation.finitizeDelays(30)`

The next line replaces all placeholder pauses in the animation with 1 second pauses. More on that later.

```python
# mation.start = mation.lastID()
mation.locatorLayer = mainlayer
mation.clickRound = 2
mation.clickCopy = True
# mation.newFrameRate(10)
mation.play()
```

This block contains some code that controls animation playback. I treat these lines like dynamic settings, and constantly change, comment, and uncomment these lines while composing the main animation code in order to control the playback while previewing the animations-in-progress.

```python
mation.start = mation.lastID()
```

The first line (currently commented out) makes the animation display only the final frame when played. I usually uncomment this line while in the middle of constructing a piece of animation, and comment it out once I'm ready to preview that piece in motion.

The next three lines configure the locator layer. It's currently set to `mainlayer`, but in a multilayer animation, I will swap it out with other layers as needed.

The `clickRound` setting rounds the locator coordinates to whatever decimal place you specify. I like to set it to 2 so it rounds coordinates to the hundreths place.

Setting `clickCopy` to `True` causes the coordinates of every click to be copied to the clipboard, which I usually prefer to do so I can quickly paste the clicked coordinates into the code wherever I need it.

```python
mation.newFrameRate(10)
```

The next line (currently commented out) is meant to modify the animation framerate for previewing purposes ***only*** (but not for the final render!). I generally keep this commented out unless the animation is so complex that it plays sluggishly when previewed. Uncommenting it lowers the framerate, allowing for quicker previewing playback.

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
    mation.wait(10*30)

    mation.finitizeDelays(30)

    # mation.start = mation.lastID()
    mation.locatorLayer = mainlayer
    mation.clickRound = 2
    mation.clickCopy = True
    # mation.newFrameRate(10)
    mation.play()

main()
```

As my videos are typically narration-driven with animation executed on cue according to the dialogue, I split the animation code for the scene into individual "chunks" with a placeholder pause after each chunk. For our example scene, our first chunk will have a line being drawn and labeled on top of a background grid. Let's start by creating the grid and adding it to `mainlayer`:

```python
# Define background grid
grid = mainlayer.Actor(mo.grid.mathgrid(
    view=[-9,9, -5,5],
    steps=1,
    hcolor=[0,0.6,0], vcolor=[0,0,1],
    axesColor=[0,0,0],
    axisWidth=7
    ))
```
> **Note:** Remember `mo` is a shorthand for `morpho`, as we defined in the header.

Next, we'll create the line and animate it being drawn on the grid. We can define the line itself with `realgraph()`, but then we'll also set the `end` attribute of the resulting path figure to 0 so that we can update it to `end=1` in a new keyframe. This will create the drawing animation we want.

```python
# Define curve to initially be a line
curve = mainlayer.Actor(mo.graph.realgraph(lambda x: 2*x + 1, -3, 3))
curve.first().set(width=5, color=[1,0,0], end=0)
curve.newendkey(30).end = 1  # Draw curve over 1 second (30 frames)
```

> **Note:** The `end` attribute of a Path is a number between 0 and 1 that controls where along the path it ends. So having the path transition from `end=0` to `end=1` causes the path to gradually be drawn out starting from its initial node.

Now we'll add in the text label:

```python
# Create "Linear" label.
# MultiText is used so that we can morph the text later
label = mainlayer.Actor(mo.text.MultiText("Linear",
    pos=1+0.5j, size=64, color=[1,0,0], alpha=0
    ))
```

Note how we set its `alpha` value to 0 so that it starts out invisible. We'll now create a new keyframe for the label where we set `alpha=1` so we get the fade-in effect:

```python
label.newendkey(20).alpha = 1
```

That's it! We're done animating this chunk, so we'll end it off with a line that inserts a placeholder pause at the end of the chunk. It will eventually be replaced once the narration is recorded, but more on that later.

```python
mation.waitUntil()
```

So here's our first chunk in its entirety:

```python
# Define background grid
grid = mainlayer.Actor(mo.grid.mathgrid(
    view=[-9,9, -5,5],
    steps=1,
    hcolor=[0,0.6,0], vcolor=[0,0,1],
    axesColor=[0,0,0],
    axisWidth=7
    ))

# Define curve to initially be a line
curve = mainlayer.Actor(mo.graph.realgraph(lambda x: 2*x + 1, -3, 3))
curve.first().set(width=5, color=[1,0,0], end=0)
curve.newendkey(30).end = 1  # Draw curve over 1 second (30 frames)

# Create "Linear" label.
# MultiText is used so that we can morph the text later
label = mainlayer.Actor(mo.text.MultiText("Linear",
    pos=1+0.5j, size=64, color=[1,0,0], alpha=0
    ))
label.newendkey(20).alpha = 1

mation.waitUntil()
```

### Morphing to a quadratic

After the first chunk, I like to precede each successive chunk with a line that prints the current animation length so far---basically printing to the console the time at which the following chunk will start animating. This will be useful later on when synchronizing the animation to the narration.

In this chunk we'll be morphing the line to a parabola, so begin this chunk with the following line:
```python
print("Morph line to parabola:", mation.seconds())
```

To get the morphing animation to begin at the start of this chunk, we need to create a new key at what is currently the end of the animation. This can be done with an empty call to `newendkey()`:

```python
curve.newendkey()  # Make a new key at the current animation end frame
```

Now we'll create the parabola figure

```python
curve.newendkey()

quadratic = mo.graph.realgraph(lambda x: x**2, -3, 3)
quadratic.set(width=5, color=violet)
```

and then assign this curve to a new keyfigure of `curve` to have it morph into the parabola:

```python
curve.newendkey()

quadratic = mo.graph.realgraph(lambda x: x**2, -3, 3)
quadratic.set(width=5, color=violet)
curve.newendkey(30, quadratic)
```

Note that the empty `curve.newendkey()` is important here, as it defines the starting point for the morphing animation. If we omitted it, our line figure would morph into a parabola too soon: it would start morphing *immediately* after its drawing animation finished during the previous chunk while the "Linear" label is still fading in. But including the line `curve.newendkey()` here causes the line to remain static on screen after its initial animation finishes, until the start of this new chunk.

All right, now let's also have the "Linear" label morph into the word "Quadratic" at the same time while the line is morphing into a parabola. To ensure the label starts morphing exactly when the line starts morphing, we include an empty `newendkey()` call for the label actor at the same place where we called it for the `curve` actor:

```python
curve.newendkey()
label.newendkey()  # label will morph when curve morphs

quadratic = mo.graph.realgraph(lambda x: x**2, -3, 3)
quadratic.set(width=5, color=violet)
curve.newendkey(30, quadratic)
```

Then afterward, make a new key for the label with a new `text` string:

```python
curve.newendkey()
label.newendkey()  # label will morph when curve morphs

quadratic = mo.graph.realgraph(lambda x: x**2, -3, 3)
quadratic.set(width=5, color=violet)
curve.newendkey(30, quadratic)

label.newendkey(30).text = "Quadratic"  # New keyfigure with new text string
```

We can also change its position and color while we're at it by changing the line to this:

```python
label.newendkey(30).set(text="Quadratic", pos=2.5+0.5j, color=violet)
```

Playing the animation, you should see the line and label morph together at the same time. If instead, you wanted the label to start morphing *after* the line finishes morphing into a parabola, just move the `label.newendkey()` line to a point *after* the code defining the curve animation:

```python
curve.newendkey()

quadratic = mo.graph.realgraph(lambda x: x**2, -3, 3)
quadratic.set(width=5, color=violet)
curve.newendkey(30, quadratic)

label.newendkey()  # It's over here now
label.newendkey(30).set(text="Quadratic", pos=2.5+0.5j, color=violet)
```

Now we end off the chunk with another placeholder pause. Here's the code for this chunk in full:

```python
print("Morph line to parabola:", mation.seconds())

curve.newendkey()
label.newendkey()

quadratic = mo.graph.realgraph(lambda x: x**2, -3, 3)
quadratic.set(width=5, color=violet)
curve.newendkey(30, quadratic)

label.newendkey(30).set(text="Quadratic", pos=2.5+0.5j, color=violet)

mation.waitUntil()
```

### Fading out

We can keep adding new chunks in the same way as we added the previous chunk---however many we need. But for this example, let's end it off by putting in one final chunk where we fade the curve and label away. We'll do it with this code:

```python
print("Fade everything out:", mation.seconds())

# Create initial keyfigures
curve.newendkey()
label.newendkey()

# Fade curve
curve.newendkey(30).alpha = 0

# Simultaneously fade the label
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

In the code we have so far, the placeholder pauses are created by the various `mation.waitUntil()` calls that are spread thruout the code. But it only does this because we have called `waitUntil()` with no parameters. The actual use of `waitUntil()` is to cause the animation to pause at its current endpoint *UNTIL* a given point in time.

To see how it works, let's say that you've recorded some narration for this animation, and after carefully reviewing the audio in an audio editor, you conclude that you would like the line to morph into a parabola starting at 3 seconds into the audio, and would like to have the figures fade out at the 6.25 second mark. In that case, simply supply the following inputs into the two `mation.waitUntil()` calls we have in the code:

```python
mation.waitUntil(3*30)
print("Morph line to parabola:", mation.seconds())

...etc...

mation.waitUntil(6.25*30)
print("Fade everything out:", mation.seconds())
```

Note that we have to multiply both numbers by 30 to convert seconds into frames. Remember that virtually all measurements of time in Morpho are in units of frames.

To test it, comment out `mation.play()` in the playback clause, and run the code. If all has gone well, the console should print out the timings of the two checkpoints as 3 seconds and 6.25 seconds respectively (note these may not be exactly 3 and 6.25 because the times will be rounded to the nearest frame).

Sometimes it happens that an animation may transpire slower, or the audio go faster, than you first expected. In such a case, you may have accidentally set the `waitUntil()` value of a chunk to be a time BEFORE the chunk actually ends. In this case, Morpho will throw an error and will report to you how many frames too early your wait-until point occurred, so you know how to adjust your animation and/or audio to correct it (e.g. by speeding up your animation, or inserting a pause in your audio).

```python
mation.waitUntil(3*30)
print("Morph line to parabola:", mation.seconds())

...etc...

# This line will throw an error saying the "until" value occurs
# 15 frames before the animation's (i.e. chunk's) end.
mation.waitUntil(3.5*30)
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

> ***Tip:*** When exporting the animation either to test the audio syncing or do the final render, I recommend commenting out the line in the playback clause that says `mation.finitizeDelays(30)`. Doing so causes Morpho to throw an error when exporting if you happened to forget to replace one of the placeholder pauses with a final finite value. Any leftover placeholder pauses in the animation can cause the audio synchrony to fall out of whack.

## Actor actions

Once you have the core workflow pattern of animating with Morpho down, you can make use of so-called *actor actions* to speed up creating certain very common animations.

Actor actions, or just *actions* for short, are built-in mini routines that automatically implement certain common, simple animations, typically opening animations (making an actor appear on screen) and closing animations (making an actor disappear from the screen).

For example, in our code, we introduced the line actor by having it get "drawn" as if with a pen, and we had the "Linear" label appear by fading it in from invisibility. Both of these are types of opening animations, and they're both very common for paths and text labels. Because they're so common, `Path` actors and `Text` actors come built-in with two *actions* that handle creating these opening animations for you.

The one for the line is called `growIn()`, and causes a path to "grow" into its final state starting from its initial node.

The one for the text label is called `fadeIn()`, and does exactly what you think: it causes the actor to "fade in" to full visibility from invisibility.

In our example code, we implemented both of these opening animations manually. For the line actor, we did it by setting `end=0` and then later updating it to `end=1`. For the text label, we did it by setting `alpha=0` and then later updating it to `alpha=1`.

```python
# Define curve to initially be a line
curve = mainlayer.Actor(mo.graph.realgraph(lambda x: 2*x + 1, -3, 3))
curve.first().set(width=5, color=[1,0,0], end=0)
curve.newendkey(30).end = 1  # Draw curve over 1 second (30 frames)

# Create "Linear" label.
# MultiText is used so that we can morph the text later
label = mainlayer.Actor(mo.text.MultiText("Linear",
    pos=1+0.5j, size=64, color=[1,0,0], alpha=0
    ))
label.newendkey(20).alpha = 1
```

But we can produce this effect automatically by using *actions*, like this:

```python
# Define curve to initially be a line
curve = mainlayer.Actor(mo.graph.realgraph(lambda x: 2*x + 1, -3, 3))
curve.first().set(width=5, color=[1,0,0])  # No longer need to say end=0
curve.growIn(duration=30)

# Create "Linear" label.
# MultiText is used so that we can morph the text later
label = mainlayer.Actor(mo.text.MultiText("Linear",
    pos=1+0.5j, size=64, color=[1,0,0]  # No longer need to say alpha=0
    ))
label.fadeIn(duration=20)
```

Note how we don't have to specify `end=0` and `alpha=0` for the starting keyfigures anymore. All of that is handled by the `growIn()` and `fadeIn()` actions.

At the end of our animation, we had both the curve and the label fade out to invisibility. We implemented it manually, but we could use the `fadeOut()` action instead:

```python
# Create initial keyfigures
curve.newendkey()
label.newendkey()

# Fade curve and label
curve.fadeOut(duration=30)
label.fadeOut(duration=30)
```

> ***CAUTION!*** The empty `newendkey()` calls are important here! By default, actions act starting on the given ***actor's*** current final frame, not the layer or animation's final frame. If you omit the `newendkey()` calls, the fade outs may occur earlier than you wanted.

However, this can be streamlined even further: If you want to apply the same action to *multiple* actors all at once, you can use the following syntax:

```python
# Create initial keyfigures
curve.newendkey()
label.newendkey()

# Fade curve and label
mo.action.fadeOut([curve, label], duration=30)
```

which also enables another neat feature: staggering. By passing in another optional parameter called `stagger` into the `fadeOut()` action, you can cause each actor to fade out slightly out of sync with each other by a time difference you specify. For example, setting `stagger=15` causes each actor to start fading out 15 frames *after* the previous actor in the list starts fading out, leading to a kind of "staggered" fade out animation:

```python
# Create initial keyfigures
curve.newendkey()
label.newendkey()

# Fade curve and label in a staggered fashion
mo.action.fadeOut([curve, label], duration=30, stagger=15)
```

`fadeIn()` and `fadeOut()` also support an optional parameter called `jump` which causes the affected actors to move a certain amount in a certain direction while fading in or out. For example, setting `jump=2j` causes each actor to "jump" 2 units upward while fading in/out:

```python
# Create initial keyfigures
curve.newendkey()
label.newendkey()

# Fade curve and label in a staggered fashion with jumping
mo.action.fadeOut([curve, label], duration=30, stagger=15, jump=2j)
```

You can apply this on `fadeIn()` as well, which is how I accomplish many of the opening animations in my videos:

```python
# Create "Linear" label.
# MultiText is used so that we can morph the text later
label = mainlayer.Actor(mo.text.MultiText("Linear",
    pos=1+0.5j, size=64, color=[1,0,0]  # No longer need to say alpha=0
    ))
label.fadeIn(duration=20, jump=1j)
```

### Limitations

Actions are a relatively recent addition to Morpho, and they are not fully supported for all figure types yet. So it's best not to get overly reliant on them. You should still make sure you master implementing opening and closing animations manually if you need to.

## Bookmarking

Here's one last trick: If you're working on animating a very long scene, you may want to preview only a single chunk of the animation without having to wait for all the previous chunks to play thru first. You can do that by including this line at the appropriate point in your code:

```python
mation.start = mation.lastID()
```

For example, let's say we want to preview the fade out animation without having to wait thru watching all the previous animations. We can do that by inserting the above line at the beginning of the fade out chunk:

```python
print("Fade everything out:", mation.seconds())

mation.start = mation.lastID()  # BOOKMARK

# Create initial keyfigures
curve.newendkey()
label.newendkey()

# Fade curve and label in a staggered fashion with jumping
morpho.action.fadeOut([curve, label], duration=30, stagger=15, jump=2j)
```

To restore the animation playback to normal, you can just comment out `mation.start = mation.lastID()`. You can uncomment it again whenever you need to, and so it acts kind of like a playback "bookmark" in your code allowing you to skip to whatever part of the scene you want when previewing.

## More Example Code

You can find the full code of the example scene we worked on in this guide [here.](https://github.com/morpho-matters/morpholib/blob/master/examples/scene.py)

If you'd like to see more examples of how I use Morpho to create videos, I've posted the source code for some of my projects [here.](https://github.com/morpho-matters/video-code)
