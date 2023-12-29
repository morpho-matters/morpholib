---
layout: default
title: Morpho Guide -- Incorporating LaTeX
---

# Morpho Guide: Incorporating LaTeX

> **Note:** To use Morpho's LaTeX features, you must be using Morpho 0.7.0+ and have a LaTeX distribution installed on your system, as well as [dvisvgm](https://dvisvgm.de/).

To run the example code snippets in this guide, make sure to include the following lines at the top of your script:
```python
import morpholib as morpho
morpho.importAll()
from morpholib.tools.basics import *
```

## Loading LaTeX

LaTeX is treated differently in Morpho than regular `Text` figures. They're loaded in as `MultiSpline` figures that act like `Image` figures more than anything else. The syntax to construct one is fairly straightforward. Use the `latex.parse()` function:
```python
equ = morpho.latex.parse(r"e^{\pi i} = -1", boxHeight=1)
```
By default, `latex.parse()` will interpret the given TeX code in math mode, display style, and load it accordingly. Also note the lowercase `r` preceding the string `"e^{\pi i} = -1"`. This tells Python that the following string literal is a "raw string", meaning you don't have to manually escape the backslash character `\` and can input it "raw". This is important since LaTeX code often makes use of backslashes (e.g. Greek characters like `\pi`).

The parameter `boxHeight` specifies the size of the rendered TeX in terms of the height of its bounding box. You always need to specify a value for `boxHeight` (or `boxWidth`) when parsing LaTeX code since the default size will likely be very wrong. You can also specify other parameters such as position and alignment:
```python
equ = morpho.latex.parse(r"e^{\pi i} = -1", boxHeight=1, pos=1j, align=[1,0])
```

Unlike `Text` figures, though, LaTeX is colored black by default, so to view it, we'll need to display it on a non-black background:
```python
mainlayer = morpho.Layer()
mation = morpho.Animation(mainlayer)
mation.background = (1,1,1)  # White background

equ = mainlayer.Actor(morpho.latex.parse(r"e^{\pi i} = -1", boxHeight=1))

mation.play()
```
There are ways to change the color of the LaTeX both in Morpho and within the LaTeX code itself, but more on that later.

## Modifying LaTeX attributes

Just like any other figure, the attributes of a LaTeX figure can be changed after construction and tweened to create animations:
```python
equ = mainlayer.Actor(morpho.latex.parse(r"e^{\pi i} = -1", boxHeight=1))
equ.newendkey(30).set(pos=-3j, rotation=90*deg, align=[0,-1])
```

The size of a LaTeX figure can be changed after construction too, but the syntax is not as straightforward as simply reassigning a `boxHeight` or `boxWidth` attribute. To do it, use the `resize()` method:
```python
equ = mainlayer.Actor(morpho.latex.parse(r"e^{\pi i} = -1", boxHeight=1))
equ.newendkey(30).resize(boxHeight=2)  # Change the boxHeight to be 2
```

You can also specify `boxWidth` instead to `resize()` to change the box width of the LaTeX. By default, changing only one of these parameters will cause the other to change in tandem to preserve the aspect ratio, but this can be overridden by passing in values to both `boxWidth` ***and*** `boxHeight`
```python
equ = mainlayer.Actor(morpho.latex.parse(r"e^{\pi i} = -1", boxHeight=1))
equ.newendkey(30).resize(boxWidth=2, boxHeight=3)  # Make a very warped equation
```

Similarly there is a `rescale()` method that allows you to change the size of the LaTeX according to a scale factor instead of by setting a specific target box width/height:
```python
equ = mainlayer.Actor(morpho.latex.parse(r"e^{\pi i} = -1", boxHeight=1))
equ.newendkey(30).rescale(2)  # Make it twice as big
equ.newendkey(30).rescale(0.5, 1.5)  # Rescale width and height independently
```

### Modifying attributes glyph-by-glyph

Modifying other attributes like color and alpha are a bit more complicated for LaTeX figures owing to the fact that they are actually `MultiSpline` figures---that is, a collection of individual Spline figures that together form the shape of the LaTeX math. So to change, for example, the color of some LaTeX after construction, you have to change it for all the individual subsplines within the MultiSpline. Luckily, this can be done pretty easily by using the `.all` property:
```python
equ = mainlayer.Actor(morpho.latex.parse(r"e^{\pi i} = -1", boxHeight=1))
equ.newendkey(30).all.set(fill=[1,0,0])
```
> **Note:** Using the `.all` property is largely optional in Morpho v0.7.1+ since it will be done implicitly most of the time.

Note that we need to modify the `fill` attribute, not the `color` attribute. This is because the individual LaTeX glyphs are rendered as strokeless Splines, so modifying the `color` attribute will change the color of the (invisible) strokes around each glyph. However, by changing the stroke width to a non-zero value, you can create outlined LaTeX text which can be useful for highlighting purposes:
```python
equ = mainlayer.Actor(morpho.latex.parse(r"e^{\pi i} = -1", boxHeight=1))
equ.newendkey(30).all.set(fill=[1,1,0], width=-3, color=[0,0,0])
```

You might notice the `width` in the above example is specified with a negative value. This causes the stroke to be drawn *behind* the fill, which I recommend for stroking LaTeX glyphs so that the stroke doesn't stand out too much and overwhelm the overall shape of the glyphs.

It's also possible to modify only a *subset* of the LaTeX glyphs. This is done using the `.select[]` feature. In general (though not always) each individual glyph appearing in a LaTeX expression corresponds to a single subspline in the MultiSpline in order from left-to-right. So for example, if we wanted to highlight the _πi_ in the formula, we can do it like this by noting that _π_ is the second (index 1) glyph in the formula and _i_ is the third (index 2):
```python
equ = mainlayer.Actor(morpho.latex.parse(r"e^{\pi i} = -1", boxHeight=1))
# We go from 1:3 since the final index is not included.
# So 1:3 covers indices 1 and 2
equ.newendkey(30).select[1:3].set(fill=[1,1,0], width=-3, color=[0,0,0])
```

Negative index values work as well and are interpreted cyclically. So to highlight -1 instead, we would want to highlight the last and second-to-last glyphs:
```python
equ.newendkey(30).select[-2:].set(fill=[1,1,0], width=-3, color=[0,0,0])
```

All of this also applies to any other attributes that Splines have (e.g. `alpha`, `dash`, etc.)

### Changing the LaTeX dynamically

One LaTeX expression can be morphed into another by simply tweening between the starting and ending LaTeX figures. Within an actor, this is most easily done by using the `replaceTex()` method which, well, *replaces* the LaTeX expression for a given figure with another one:
```python
equ = mainlayer.Actor(morpho.latex.parse(r"e^{\pi i} = -1", boxHeight=1))
equ.newendkey(30).replaceTex(r"a^2 + b^2 = c^2")
```

Optionally, other parameters like position, alignment, and box height can be specified within the `replaceTex()` method:
```python
equ.newendkey(30).replaceTex(r"a^2 + b^2 = c^2",
    pos=3j, boxWidth=5, align=[-1,0])
```
and can even be chained with `set()`, `all.set()`, or `select[].set()` to modify other attributes:
```python
equ.newendkey(30).replaceTex(r"a^2 + b^2 = c^2",
    pos=3j, boxWidth=5, align=[-1,0]).all.set(
    fill=[1,1,0], width=-3, color=[0,0,0]
    )
```

If using Morpho 0.9.0+, you can also pass in a string to the keyword `gauge` to automatically scale the new LaTeX figure so that the glyph sizes do not change. The idea is to pass in a string of LaTeX code that codes for exactly one LaTeX glyph that will be used as a reference to rescale the new LaTeX figure so that the gauge glyph's size remains unchanged. For example, suppose we want to morph the LaTeX `2x + y` into `\frac{1}{x}` while ensuring the size of the `x` glyphs remains unchanged after the transformation. Since `x` is a common glyph between the two LaTeX figures, we can set it as a gauge to tell Morpho to rescale the entire LaTeX figure so that the `x` glyph's size remains unchanged after replacement:
```python
expr = mainlayer.Actor(morpho.latex.parse(r"2x + y", boxHeight=1))
expr.newendkey(30).replaceTex(r"\frac{1}{x}", gauge=r"x")
```

Some important caveats for this to work:
- The gauge glyph must exist in both the starting *and* ending LaTeX figures. The above example works because `x` is a shared glyph between the two figures, but using `y` as the gauge would result in an error because the ending figure does not possess a `y` glyph. If the starting and ending LaTeX figures contain no common glyphs, the gauge feature cannot be used directly<sup>[</sup>[^1]<sup>]</sup>.
- The LaTeX code used for the gauge must code for ***exactly*** one glyph. Usually a single LaTeX character/command corresponds to one glyph, but not always. For example, `\iff` actually codes for two glyphs and therefore cannot be used as a gauge.
- Subscripted and superscripted glyphs are treated differently than their normal forms. For example, to use the `2` in the LaTeX expression `x^2` as a gauge, you must specify it as `^2`.
- If a LaTeX figure has multiple glyphs that match the given gauge, the first instance will always be used for the reference. This is true of both the starting *and* ending figures.

[^1]: There is a trick to workaround this limitation, but it requires creating a hidden intermediate LaTeX figure. For example, to morph `x` to `y` while preserving general font size, you can replace `x` with `xy` using `x` as the gauge, and then morph `xy` to `y` with `y` as the gauge. A compact implementation might look something like this:
```python
expr = mainlayer.Actor(morpho.latex.parse(r"x", boxHeight=1))
expr.newendkey(30).replaceTex(r"xy", gauge="x").replaceTex(r"y", gauge="y")
```

## Aligning multiple LaTeX expressions

LaTeX figures (and MultiSplines more generally) possess the bounding box corner/side methods `left()`, `right()`, `bottom()`, `top()`, `northwest()`, `southwest()`, `southeast()`, `northeast()` which each return the position (as a complex number) of the corresponding point on the LaTeX figure's bounding box. These are handy when trying to line up two separate LaTeX figures relative to each other.

For example, let's say we have written the equation "_a_ + _b_ = 9 + 16", and we want to place a simplified version of it directly beneath it. The corner/side methods make this easy. We'll just position the simplified equation a little lower than the original equation's southwest corner while having the simplified equation's position aligned with its northwest corner:
```python
equ = mainlayer.Actor(morpho.latex.parse(r"a + b = 9 + 16", boxHeight=1))

simp = mainlayer.Actor(morpho.latex.parse(r"a + b = 25", boxHeight=1,
    pos=equ.last().southwest()-0.75j, align=[-1,1]))
```

## The `box()` method

Like Images and Text figures, LaTeX figures (that is, MultiSplines) possess a `box()` method that returns the bounding box of the figure in the form `[xmin, xmax, ymin, ymax]`. This data is handy to pass into gadgets like the `enbox()` function in order to box in an equation or formula you want highlighted:
```python
equ = mainlayer.Actor(morpho.latex.parse(r"e^{\pi i} = -1", boxHeight=1))

boxer = mainlayer.Actor(morpho.gadgets.enbox(equ.last().box(), pad=0.25,
    width=5, color=[1,0,0]))
```

> **Note:** In Morpho v0.7.1+, a figure/actor can be passed directly into methods like `enbox()` or `crossout()` without having to call the `box()` method.

## Subsetting

A subset of glyphs can also be extracted from a LaTeX figure as its own separate figure using the `sub[]` feature. The syntax is the same as for `select[]`, except the return value is a new MultiSpline with copies of the selected subsplines:
```python
equ = mainlayer.Actor(morpho.latex.parse(r"e^{\pi i} = -1", boxHeight=1))

equ2 = mainlayer.Actor(equ.last().sub[1:3])
equ2.newendkey(30).pos -= 3j
```

This feature can be useful in combination with `enbox()` to box in only a portion of an expression.
```python
equ = mainlayer.Actor(morpho.latex.parse(r"e^{\pi i} = -1", boxHeight=1))

boxer = mainlayer.Actor(morpho.gadgets.enbox(equ.last().sub[1:3].box(),
    pad=0.15, width=5, color=[1,0,0]))
```

## Using `morphFrom()`

`morphFrom()` is an actor action that facilitates animating a new figure "morphing" out of a copy of an old figure of the same type. This works especially well for animating a math equation morphing out of another.
```python
equ = mainlayer.Actor(morpho.latex.parse(r"e^{\pi i} = -1", boxHeight=1))

equ2 = mainlayer.Actor(morpho.latex.parse(r"a^2 + b^2 = c^2", boxHeight=1, pos=-2j))
equ2.morphFrom(equ, duration=20)
```

## Changing the preamble

Morpho's LaTeX parser does not have access to all possible LaTeX commands from all possible packages. By default, the parser only knows about commands from the LaTeX packages `amsmath`, `amsfonts`, `amssymb`, and `xcolor`, which cover a reasonably wide range of common commands. To allow it to use commands from other packages, as well as any custom commands of your own, modify the LaTeX *preamble*.

The *preamble* is the LaTeX code that is executed before the main document code is parsed. It's where all package inclusion statements go as well as any custom commands you might have written. For example, say we want the parser to have access to the `relsize` package. We can extend the built-in preamble by including this line at the top of your code:
```python
morpho.latex.preamble += r"\usepackage{relsize}"
```
> ***CAUTION!*** Remember to use the in-place addition operator `+=` instead of merely an assignment `=`. Using `+=` *extends* the preamble with the code you provide, but using `=` will *replace* the default preamble, causing the parser to lose access to the four packages listed above that are included by default.

If you have multiple lines of LaTeX code you want added to the preamble, you can extend it using a Python docstring:
```python
morpho.latex.preamble += r"""
\usepackage{relsize}
\newcommand{\degs}{^\circ}
\newcommand{\half}{\tfrac 12}
"""
```

## Modifying color at the LaTeX level

The color of LaTeX can also be controlled from the LaTeX code itself. By default, Morpho's LaTeX parser has access to the `xcolor` package, so you can change the color of elements in the LaTeX with the `\textcolor{}` LaTeX command:
```python
morpho.latex.parse(r"\textcolor{red}{e^{\pi i}} = -1", boxHeight=1)
```

You can also change the default color of all LaTeX by adding the following LaTeX code to the preamble:
```python
# All LaTeX will be rendered red by default now
morpho.latex.preamble += r"\everydisplay{\color{red}}"
```

You can also specify your own custom colors using normalized RGB values or HTML notation and use them anywhere in your LaTeX code:
```python
morpho.latex.preamble += r"""
\definecolor{darkgreen}{rgb}{0, 0.5, 0}
\definecolor{softblue}{HTML}{248bad}
\everydisplay{\color{softblue}}
"""

equ = morpho.latex.parse(r"e^{\textcolor{darkgreen}{\pi i}} = -1", boxHeight=1)
```

## Caching

Unfortunately, parsing LaTeX code is a fairly slow operation, and so if you're busy animating a scene that contains lots of LaTeX code, the slowdown can become an issue. This is where caching can help a lot.

When caching is enabled, the LaTeX parser will save out the SVG data for any new LaTeX code it parses to a special cache directory. If the parser encounters that same LaTeX code again, instead of re-parsing it from scratch, it will load in the cached SVG data from the cache directory, which is substantially faster. In practice, this means when running a given script, the LaTeX code only needs to be parsed once and all subsequent runs of the script will use the cache.

To enable caching, create an empty directory anywhere on your system. The easiest place is just in the same directory as the Python script you're working with. Then assign the path to that directory to `morpho.latex.cacheDir`:
```python
morpho.latex.cacheDir = path_to_cache_directory  # e.g. "./tex"
```

### Warnings

A couple of things to look out for when using caching:

- Morpho does not automatically clean up the cache directory over time. This is generally not an issue since each cached SVG file is usually quite small (a handful of kilobytes), but for a large project involving a lot of LaTeX code that has been modified often, the cache directory can start to become quite large. If this happens, simply manually delete all the SVG files in the cache to reset it.
- Before Morpho v0.7.1, changing the preamble would not invalidate the cache, meaning the changes would not be reflected if the parser loads from the cache. So if you're using v0.7.0 and you modify the preamble, you should empty the cache. This has been fixed in v0.7.1 onward.

## Using LaTeX in Skits

Since LaTeX is time/storage consuming to render, you should avoid rendering them within a Skit's `makeFrame()` method. If you need a *non-dynamic* LaTeX figure to appear as part of a Skit, treat it like an `Image` figure, where you pre-load the LaTeX figure *outside* the Skit class and create copies of it within `makeFrame()`.
```python
equbase = morpho.latex.parse(r"e^{\pi i} = -1", boxHeight=1)
class MySkit(morpho.Skit):
    def makeFrame(self):
        equ = equbase.copy()
        ...
```

> ***CAUTION!*** You should **NEVER** include ***dynamic*** LaTeX within the `makeFrame()` method of a Skit when caching is enabled! That is, you should **not** have LaTeX code that changes depending on the parameters of the Skit, e.g. a Tracker Skit with a dynamically updating LaTeX label. This will cause an SVG file to be written to the cache ***for every single frame of animation*** which will quickly fill up the LaTeX cache.
>
> Even without caching, rendering dynamic LaTeX will likely be *extremely* slow, so for all intents and purposes, dynamically updating LaTeX should not be considered a supported feature.
