<img src="https://github.com/morpho-matters/morpholib/blob/main/logo/logo-white.png" width=600>

**A general-purpose programmatic animation tool**

For a gallery of animations made with Morpho, (click here). Most of the animations found in the YouTube channels (Morphocular) and (Serpentine Integral) were made with Morpho, so you can also look there for a more robust demonstration of Morpho's capabilities.

## Features
- Animate basic figures like Points, Paths, Polygons, Splines, Images, and Text
- Helper functions to build more complex composite figures like grids
- Tools for quickly creating custom figures that animate in precisely specified ways
- Multiple tweening options and the ability to define custom tweens
- Apply custom transformations to figures to create complex patterns
- Support for multiple layers each with its own independent dynamic camera
- Ability to use layers as masks for other layers
- Color gradients, both as fills and as color gradients along paths
- Some primitive 3D animation capability
- Preview animations along with the ability to locate positions on screen with a click
- Export animations as MP4, GIF, and PNG sequences at arbitrary framerates and resolutions
  - (**Note:** [FFmpeg](https://ffmpeg.org/) required to create MP4s, and [Gifsicle](https://www.lcdf.org/gifsicle/) required to make small size GIFs)

## Installation

Morpho should work on Python 3.6 or higher and in its most basic form can be installed via pip:

```sh
pip install morpholib
```

However, [FFmpeg](https://ffmpeg.org/) is required if you want to export animations in MP4 format, and [Gifsicle](https://www.lcdf.org/gifsicle/) is required to create small size GIF animations. But if neither of those matter to you (or if you just want to try out Morpho), you can still preview animations and export them as PNG sequences and large-sized GIFs just using the base installation of Morpho.

To see if it installed correctly, try running the script (sample.py). You should see an animation of a morphing grid appear on your screen.

## License

This project is licensed under the terms of the MIT license.
