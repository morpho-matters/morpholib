import cairo
import PIL.Image as Image
import numpy


# Converts a cairo image surface object into a PIL image.
# Useful for converting between formats.
#
# Credit: https://casualhacker.net/post/2013-06-02-convert-pycairo-argb32-surface-to-pil-rgb-image
def toPil(surface):
    # See also: https://pycairo.readthedocs.io/en/latest/tutorial/pillow.html
    # for another implementation that didn't work as well because of
    # alpha channel issues.
    cairoFormat = surface.get_format()
    if cairoFormat == cairo.FORMAT_ARGB32:
        pilMode = 'RGB'
        # Cairo has ARGB. Convert this to RGB for PIL which supports only RGB or
        # RGBA.
        argbArray = numpy.fromstring( bytes(surface.get_data()), 'c' ).reshape( -1, 4 )
        rgbArray = argbArray[ :, 2::-1 ]
        pilData = rgbArray.reshape( -1 ).tostring()
    else:
        raise ValueError( 'Unsupported cairo format: %d' % cairoFormat )
    with Image.frombuffer( pilMode,
            ( surface.get_width(), surface.get_height() ), pilData, "raw",
            pilMode, 0, 1 ) as pilImage:
        pilImage_converted = pilImage.convert( 'RGB' )
    return pilImage_converted

# Saves a cairo image surface object to a file.
#
# Optional keyword-only input `options` is a dict containing
# keyword options that will be passed to the PIL image writer
# for cases where `filename` is not a PNG image (e.g. JPG).
# Any unrecognized options will be silently ignored.
def surfaceSave(surface, filename, *, options):
    if filename.lower().strip().endswith("png"):
        surface.write_to_png(filename)
    else:
        with toPil(surface) as img:
            img.save(filename, **options)
