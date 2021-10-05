<img src="https://github.com/morpho-matters/morpholib/blob/master/logo/logo-white.png" width=600>

**A general-purpose programmatic animation tool**

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

Morpho works on Python 3.6 or higher and requires [Pycairo](https://www.cairographics.org/pycairo/) to run. For Windows users, Morpho and all its basic dependencies, including Pycairo, should be installable via a simple pip command:

```sh
pip3 install morpholib
```

Installation on other platforms has not been well-tested, unfortunately, and does not appear to be as straightforward. For now, I think the best method is to first see if you can install Pycairo separately (for instructions on how to do so, [see this](https://pycairo.readthedocs.io/en/latest/getting_started.html)), test that the Pycairo installation is working, and then attempt to install Morpho via the above pip command.

### Softer requirements

If you want to export animations as MP4s or small-sized GIFs, you will need to install [FFmpeg](https://ffmpeg.org/) for MP4 and/or [Gifsicle](https://www.lcdf.org/gifsicle/) for GIF. But if that doesn't matter to you (or if you just want to try out Morpho), you can still preview animations and export them as PNG sequences and large-sized GIFs just using the base installation of Morpho.

Please note that FFmpeg and Gifsicle will need to be added to your PATH environmental variable for Morpho to be able to access them by default.

### Testing the installation

To see if it installed correctly, try running the following Python code:

```python
import morpholib as morpho
morpho.importAll()
morpho.sample.play()
```

If you see an animation of a morphing grid appear on your screen, congratulations! Morpho should be installed and working properly.

## License

This project is licensed under the terms of the MIT license.
