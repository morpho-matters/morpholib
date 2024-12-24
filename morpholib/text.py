import io

import morpholib as morpho
import morpholib.anim, morpholib.grid, morpholib.shapes
from morpholib.combo import TransformableFrame
from morpholib.tools.basics import *
from morpholib.tools.dev import typecastViewCtx, typecastView, \
    typecastWindowShape, BoundingBoxFigure, BackgroundBoxFigure, \
    PreAlignableFigure, AlignableFigure, Transformable2D

import cairo
cr = cairo

import numpy as np

# Setup a dummy context for use in computing certain text values
# outside of draw time (e.g. width and height)
mation = morpho.Animation()
mation.setupContext()
ctx0 = mation.context
del mation

DUMMY = object()

# Default font. If set to a font's name, this font
# will be used as the default font for the Text class
# and its derivatives.
defaultFont = "Times New Roman"

# Default alphabet to use in calculating line heights
# for paragraphs
LINE_HEIGHT_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

### CLASSES ###

'''
anchor_x and anchor_y should be interpreted as defining where the
origin for the text is. (0,0) corresponds to centered,
(1,1) corresponds to the upper-right corner,
(-1, -1) corresponds to the lower-left corner.
'''

I2 = np.identity(2)

# Basic text figure. Displays uniformly formatted text on screen.
#
# TWEENABLES
# pos = Position of text (complex number). Default: 0
# size = Text size (in pixels? Not totally sure). Default: 64
# anchor_x = Horizontal alignment parameter.
#            -1 = left-aligned, 0 = center-aligned, 1 = right-aligned.
#            Default: 0 (center-aligned)
# anchor_y = Vertical alignment parameter.
#            -1 = bottom-aligned, 0 = center-aligned, 1 = top-aligned.
#            Default: 0 (center-aligned)
# color = Text color (RGB list). Default: (1,1,1) (white)
# alpha = Opacity. Default: 1 (opaque)
# background = Background box color. Default: [1,1,1] (white)
# backAlpha = Background box opacity. Default: 0 (transparent)
# backPad = Background box padding (physical units). Default: 0
# rotation = Rotation in radians. Default: 0
# prescale_x, prescale_y = Scale factors applied to the text
#             BEFORE the rotation tweenable is applied.
#             Mainly for internal use.
#
# OTHER ATTRIBUTES
# text = Text to display (string). Default: "" (empty string)
# font = Font to use. Default: "Times New Roman"
# bold = Boolean indicating whether to bold. Default: False
# italic = Boolean indicating whether to use italics. Default: False
@Transformable2D(exclude="origin")
class Text(PreAlignableFigure, BackgroundBoxFigure):
    def __init__(self, text="", pos=0,
        size=64, font=None,
        bold=False, italic=False,
        anchor_x=0, anchor_y=0,
        color=(1,1,1), alpha=1,
        background=(1,1,1), backAlpha=0, backPad=0,
        *, align=None):

        # Handle Text figure derivative inputs for text.
        if isinstance(text, PText):
            raise TypeError(f"Cannot convert PText to {type(self).__name__}")
        elif isinstance(text, MultiTextBase):
            raise TypeError(f"Cannot convert MultiText to {type(self).__name__}")
        elif isinstance(text, Text):
            # text = text.text
            Text.__init__(self)
            self._updateFrom(text, common=True)
            if isinstance(text, SpaceText):
                self.pos = complex(*text._pos[:2])
            return
        elif not isinstance(text, str):
            raise TypeError(f"Cannot convert {type(text).__name__} to {type(self).__name__}")


        if type(color) is tuple:
            color = list(color)
        elif type(color) is not list:
            raise TypeError("Unsupported color input")

        super().__init__()

        # Take last three coords of color.
        color = list(color[:3])

        # Tack on zeros if len(color) < 4
        if len(color) < 3:
            color.extend([0]*(4-len(color)))

        # Turn position into complex
        if type(pos) in (list, tuple):
            pos = pos[0] + 1j*pos[1]

        # Update anchor_x, anchor_y based on align parameter if given
        if align is not None:
            anchor_x, anchor_y = align

        # Create tweenables
        self.Tweenable("pos", pos, tags=["complex"])
        self.Tweenable("size", size, tags=["size", "pixel"])
        self.Tweenable("anchor_x", anchor_x, tags=["scalar"])
        self.Tweenable("anchor_y", anchor_y, tags=["scalar"])
        self.Tweenable("color", color, tags=["color"])
        self.Tweenable("alpha", alpha, tags=["scalar"])
        # CCW rotation in radians

        # These are the pre-transformation scale factors. These get
        # applied to the text BEFORE rotation and transform do.
        # This is mainly for use in the Multi decorator, so that
        # tweening between two texts with differing rotation parameters
        # works correctly.
        self.Tweenable("prescale_x", 1, tags=["scalar"])
        self.Tweenable("prescale_y", 1, tags=["scalar"])

        # Other attributes
        self.NonTweenable("text", text)
        self.NonTweenable("font", font if font is not None else defaultFont)
        self.NonTweenable("bold", bold)
        self.NonTweenable("italic", italic)
        # Indicates whether the text figure is meant to be invisible
        # whitespace. Mainly used to make space() function work.
        self.NonTweenable("_isWhitespace", False)
        # self.text = text
        # self.font = font if font is not None else defaultFont
        # self.bold = bold
        # self.italic = italic

    @property
    def origin(self):
        return self.pos

    @origin.setter
    def origin(self, value):
        self.pos = value

    @property
    def align(self):
        return (self.anchor_x, self.anchor_y)

    @align.setter
    def align(self, value):
        self.anchor_x, self.anchor_y = value

    # NOT IMPLEMENTED!
    # Only for internal use by the Text class for now.
    # Currently not meant to work for PText or other classes.
    # Aligns origin taking into account possible non-square
    # views.
    def _alignOrigin(self, align, view, windowShape, *args, **kwargs):
        # NOTE: I believe this method is fully working, but I no longer
        # need it for its original purpose. Nevertheless, I'm keeping
        # the code here in case we ever want to implement it (or a
        # variant of it) in the future.
        raise NotImplementedError

        view = typecastView(view)
        windowShape = typecastWindowShape(windowShape)

        # Compute anchor point
        anchor = self.anchorPoint(align, view, windowShape, *args, raw=True, **kwargs)

        # Update align
        self.align = align

        # Move position to physical position of anchor point
        par = morpho.pixelAspectRatioWH(view, windowShape)
        if abs(par-1) > 1e-9:
            # Do something special if the viewbox and window shape
            # are not proportional to each other.
            rotation = 0
            transform = self._specialBoxTransform(par)
        else:
            rotation = self.rotation
            transform = self.transform

        rotator = cmath.exp(rotation*1j)
        transformer = morpho.matrix.Mat(transform)

        self.pos = self.pos + transformer*(rotator*anchor)

        return self

    # def copy(self):
    #     # Do a standard figure copy first
    #     # new = morpho.Figure.copy(self)
    #     new = super().copy()

    #     # Copy the non-tweenable attributes
    #     new.text = self.text
    #     new.font = self.font
    #     new.bold = self.bold
    #     new.italic = self.italic

    #     return new

    # Returns the dimensions (in pixels) of the text as a pair
    # (textwidth, textheight).
    # Note: This ignores the transform attribute.
    def pixelDimensions(self):
        ctx0.select_font_face(
            self.font,
            cr.FONT_SLANT_ITALIC if self.italic else cr.FONT_SLANT_NORMAL,
            cr.FONT_WEIGHT_BOLD if self.bold else cr.FONT_WEIGHT_NORMAL
            )
        ctx0.set_font_size(self.size)
        ctx0.set_source_rgba(*self.color, self.alpha)

        # Compute alignment parameters
        anchor_x = (self.anchor_x + 1)/2
        anchor_y = (self.anchor_y + 1)/2
        xDummy, yDummy, textWidth, textHeight, dx, dy = ctx0.text_extents(self.text)

        return (textWidth, textHeight)

    # Given viewbox and cairo context (or windowShape tuple),
    # returns tuple (width, height) representing the text's physical
    # width and height.
    # Note this ignores the "transform" and prescale tweenables.
    @typecastViewCtx
    def dimensions(self, view, ctx):
        if isinstance(view, morpho.anim.Camera):
            view = view.view

        WIDTH, HEIGHT = self.pixelDimensions()
        width = morpho.physicalWidth(WIDTH, view, ctx)
        height = morpho.physicalHeight(HEIGHT, view, ctx)

        return (width, height)

    # Returns bounding box of the text in physical units.
    # Mainly of use internally to draw the background box.
    def box(self, *args, **kwargs):
        return self._boxFromRelbox(*args, **kwargs)

    # Same as box(), but the coordinates are relative to
    # the text's position.
    @typecastViewCtx
    def relbox(self, view, ctx, pad=0, *, raw=False):
        width, height = self.dimensions(view, ctx)
        # Modify by prescale factors
        width *= self.prescale_x
        height *= self.prescale_y
        align_x, align_y = self.anchor_x, self.anchor_y
        a = -width/2*(align_x + 1)
        b = a + width
        c = -height/2*(align_y + 1)
        d = c + height

        if not raw and not(self.rotation == 0 and np.array_equal(self._transform, I2)):
            return BoundingBoxFigure._transformedBox([a,b,c,d], 0, self.rotation, self._transform, pad)
        else:
            return [a-pad, b+pad, c-pad, d+pad]

    # Same as corners(), but the coordinates are relative to wherever
    # the text's physical position is.
    def relcorners(self, *args, **kwargs):
        a,b,c,d = self.relbox(*args, **kwargs)

        NW = a + d*1j
        SW = a + c*1j
        SE = b + c*1j
        NE = b + d*1j

        return [NW,SW,SE,NE]

    # Returns the visual centerpoint of the text.
    @typecastViewCtx
    def center(self, view, ctx):
        return mean(self.corners(view, ctx))

    # Returns the width of the text in pixels.
    def pixelWidth(self):
        return self.pixelDimensions()[0]

    # Returns the height of the text in pixels.
    def pixelHeight(self):
        return self.pixelDimensions()[1]

    # Returns the physical width of the text.
    # Same as mytext.dimensions(view, ctx)[0]
    @typecastViewCtx
    def width(self, view, ctx):
        return self.dimensions(view, ctx)[0]

    # Returns the physical height of the text.
    # Same as mytext.dimensions(view, ctx)[1]
    @typecastViewCtx
    def height(self, view, ctx):
        return self.dimensions(view, ctx)[1]

    # Returns a special transform matrix to attach to the
    # bounding box figure, which handles rendering Text
    # bounding boxes in a non-square coordinate system.
    # par = pixel aspect ratio. Can be computed from
    #       morpho.pixelAspectRatioWH(view, ctx)
    def _specialBoxTransform(self, par):
        return morpho.parconj(par, self.rotation, self._transform)

    # Returns the "M" pixel width of the text.
    # That is, returns the pixel width of the current text
    # if it only consisted of the single capital letter "M".
    # Mainly used to help define horizontal spacing relative
    # to the style and size of the text.
    #
    # Optionally, a different glyph may be supplied to use it
    # instead of "M":
    #   mytext.em("A")
    def em(self, glyph="M"):
        textOrig = self.text
        self.text = glyph
        M_width = self.pixelWidth()
        self.text = textOrig
        return M_width

    # Returns the "x" pixel height of the text.
    # That is, returns the pixel height of the current text
    # if it only consisted of the single lowercase letter "x".
    # Mainly used to help define vertical spacing relative
    # to the style and size of the text.
    #
    # Optionally, a different glyph may be supplied to use it
    # instead of "x":
    #   mytext.ex("a")
    def ex(self, glyph="x"):
        textOrig = self.text
        self.text = glyph
        x_height = self.pixelHeight()
        self.text = textOrig
        return x_height

    # Special version of _drawBackgroundBox() to deal with
    # drawing Text background boxes in non-square views.
    def _drawBackgroundBox(self, camera, ctx,
            origin=None, rotation=None, transform=None,
            *args, **kwargs):

        if self.backAlpha <= 0:
            # No need to attempt to draw invisible background box
            return

        # Infer transformation attributes if not specified.
        if origin is None:
            origin = self.origin
        if rotation is None:
            rotation = getattr(self, "rotation", 0)
        if transform is None:
            transform = getattr(self, "transform", I2)

        view = camera.view
        # Do something special if the viewbox and window shape
        # are not proportional to each other.
        par = morpho.pixelAspectRatioWH(view, ctx)
        if abs(par-1) > 1e-9:
            rotation = 0
            transform = self._specialBoxTransform(par)
        else:
            transform = self.transform
        BackgroundBoxFigure._drawBackgroundBox(self,
            camera, ctx, origin, rotation, transform,
            *args, **kwargs
            )

    def draw(self, camera, ctx):
        # Do nothing if whitespace or if size is less than 1.
        if self._isWhitespace or self.size < 1:
            return

        view = camera.view

        x,y = morpho.anim.screenCoords(self.pos, view, ctx)

        ctx.select_font_face(
            self.font,
            cr.FONT_SLANT_ITALIC if self.italic else cr.FONT_SLANT_NORMAL,
            cr.FONT_WEIGHT_BOLD if self.bold else cr.FONT_WEIGHT_NORMAL
            )
        ctx.set_font_size(self.size)
        ctx.set_source_rgba(*self.color, self.alpha)

        # Compute alignment parameters
        anchor_x = (self.anchor_x + 1)/2
        anchor_y = (self.anchor_y + 1)/2
        xDummy, yDummy, textWidth, textHeight, dx, dy = ctx.text_extents(self.text)

        # # Check if transformation matrix is too close to singular.
        # # Specifically, is the area covered by the transformed text
        # # smaller than a single pixel?
        # if abs(np.linalg.det(self.transform)*textWidth*textHeight) < 1:
        #     return

        # Check if the text has been distorted too thin.
        # Specifically, is the thinnest height of the parallelogram
        # it spans less then a pixel? If so, don't draw!
        mat = self.transform.copy()
        mat[:,0] *= textWidth*self.prescale_x
        mat[:,1] *= textHeight*self.prescale_y
        if morpho.matrix.thinHeight2x2(mat) < 1:
            return

        self._drawBackgroundBox(
            camera, ctx, self.pos, self.rotation, self.transform,
            camera, ctx
            )

        ctx.save()

        # ctx.translate(x,-y)
        # ctx.translate(0, 2*y)
        ctx.translate(x,y)

        # Apply transformation matrix if necessary
        if not np.array_equal(self.transform, I2):
            # Define cairo matrix
            xx, xy, yx, yy = self.transform.flatten()
            mat = cairo.Matrix(xx, yx, xy, yy)

            # Apply to context
            ctx.transform(mat)

        if (self.rotation % tau) != 0:
            ctx.rotate(self.rotation)

        # Apply pre-transformation scales
        ctx.scale(self.prescale_x, self.prescale_y)

        # Handle alignment
        ctx.translate(-anchor_x*textWidth, -anchor_y*textHeight)

        ctx.scale(1,-1)

        # ctx.move_to(x-anchor_x*textWidth, y+anchor_y*textHeight)
        ctx.move_to(0,0)

        try:
            ctx.show_text(self.text)
        except cairo.Error:
            pass

        ctx.restore()
        ctx.new_path()


_referenceString = "A"

# Physical Text figure.
# It's pretty much the same as Text, but the `size` parameter
# controls the PHYSICAL size of the rendered text instead of the
# pixel size. That means a PText figure will scale correctly as
# the camera zooms.
#
# More precisely, `size` refers to the physical "A-height" of the text;
# that is, the physical height the text would have if the text string
# was the single letter "A".
class PText(Text):

    def __init__(self, text="", pos=0,
        size=1, *args, **kwargs):

        super().__init__(text, pos, size, *args, **kwargs)

        # Size here is physical, so remove the "pixel" tag.
        self._state["size"].tags.remove("pixel")

        # del self._nontweenables["text"]
        self._nontweenables.remove("font")
        # self._nontweenables.update({"_text", "_font", "_fontRatio", "_aspectRatioWH"})
        self._nontweenables.update({"_font", "_fontRatio"})

    # @property
    # def text(self):
    #     return self._text

    # @text.setter
    # def text(self, value):
    #     self._text = value
    #     self._updateAspectRatioWH()

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, value):
        self._font = value
        self._updateFontRatio()

    # Returns a dummy 2D version of the PText figure for use
    # in calculating scale factors, ratios, etc. internally.
    # size=64 is arbitrary and corresponds to dummy Text figure's
    # size attribute. You can override it, but it's best not to make
    # it too small.
    def _makeDummy(self, size=64):
        # Create dummy non-physical Text figure to reference
        txt = Text()
        txt.text = self.text
        txt.font = self._font
        txt.bold = self.bold
        txt.italic = self.italic
        txt.size = size

        return txt

    def aspectRatioWH(self):
        # Create dummy non-physical Text figure to reference
        txt = self._makeDummy()

        width, height = txt.pixelDimensions()
        return width/height

    # def _updateAspectRatioWH(self):
    #     self._aspectRatioWH = self._getAspectRatioWH()

    def _updateFontRatio(self):
        self._fontRatio = self._getFontRatio(self._font)

    # Computes the ratio of size/pixelHeight for a given font.
    # Used to convert between pixelHeight and fontsize when
    # constructing a Text figure from a PText figure.
    #
    # More precisely, it computes size/pixelHeight for a
    # rendering of the capital letter "A" in the given font.
    @staticmethod
    def _getFontRatio(font):
        txt = Text()
        txt.text = _referenceString
        txt.font = font
        # txt.bold = self.bold
        # txt.italic = self.italic
        txt.size = 64  # Arbitrarily chosen dummy size

        # Ratio of text "size" parameter units to pixel height
        return txt.size/txt.pixelHeight()

    # Returns the dimensions (in pixels) of the text as a pair
    # (textWidth, textHeight).
    # Note: This ignores the transform attribute.
    @typecastViewCtx
    def pixelDimensions(self, view, ctx):
        # aspectRatioWH = self.aspectRatioWH()
        # textHeight = morpho.pixelHeight(self.size, view, ctx)
        # textWidth = morpho.pixelWidth(aspectRatioWH*self.size, view, ctx)

        textWidth = self.pixelWidth(view, ctx)
        textHeight = self.pixelHeight(view, ctx)

        return (textWidth, textHeight)

    # Returns the width of the text in pixels.
    @typecastViewCtx
    def pixelWidth(self, view, ctx):
        aspectRatioWH = self.aspectRatioWH()
        return morpho.pixelWidth(aspectRatioWH*self.width(), view, ctx)

    # Returns the height of the text in pixels.
    @typecastViewCtx
    def pixelHeight(self, view, ctx):
        return morpho.pixelHeight(self.height(), view, ctx)

    # Returns tuple (width, height) representing the text's physical
    # width and height.
    #
    # The optional arguments `view` and `ctx` do nothing here,
    # but they exist for internal implementation reasons.
    #
    # Note this ignores the "transform" and prescale tweenables.
    #
    # Also note the physical width is estimated and may not be
    # perfectly accurate.
    def dimensions(self, view=DUMMY, ctx=DUMMY):
        # return (self.aspectRatioWH()*self.size, self.size)
        height = self.height()
        width = self.aspectRatioWH()*height

        return (width, height)

    # Returns (estimated) physical width of the text's bounding box
    #
    # The optional arguments `view` and `ctx` do nothing here,
    # but they exist for internal implementation reasons.
    #
    # Note this ignores the "transform" and prescale tweenables.
    def width(self, view=DUMMY, ctx=DUMMY):
        # return self.aspectRatioWH()*self.height()
        return self.dimensions()[0]

    # Returns the physical height of the text's bounding box.
    def height(self, view=DUMMY, ctx=DUMMY):
        txt = self._makeDummy()
        heightSelf = txt.pixelHeight()
        txt.text = _referenceString
        heightA = txt.pixelHeight()

        return self.size*(heightSelf/heightA)

    # Returns the corresponding fontsize (i.e. the value of the
    # `size` attribute in the 2D Text class) for this PText figure
    # given the viewbox and ctx/windowShape.
    @typecastViewCtx
    def fontsize(self, view, ctx):
        # return self._fontRatio*self.pixelHeight(view, ctx)
        return self._fontRatio*morpho.pixelHeight(self.size, view, ctx)

    # Same as box(), but the coordinates are relative to
    # the text's position.
    def relbox(self, pad=0, *, raw=False):
        return Text.relbox(self, DUMMY, DUMMY, pad=pad, raw=raw)

    # Returns the visual centerpoint of the text.
    def center(self):
        return mean(self.corners())

    # Returns the "M" physical width of the text.
    # That is, returns the physical width of the current text
    # if it only consisted of the single capital letter "M".
    # Mainly used to help define horizontal spacing relative
    # to the style and size of the text.
    #
    # Optionally, a different glyph may be supplied to use it
    # instead of "M":
    #   mytext.ex("A")
    def em(self, glyph="M"):
        textOrig = self.text
        self.text = glyph
        M_width = self.width()
        self.text = textOrig
        return M_width

    # Returns the "x" physical height of the text.
    # That is, returns the physical height of the current text
    # if it only consisted of the single lowercase letter "x".
    # Mainly used to help define vertical spacing relative
    # to the style and size of the text.
    #
    # Optionally, a different glyph may be supplied to use it
    # instead of "x":
    #   mytext.ex("a")
    def ex(self, glyph="x"):
        textOrig = self.text
        self.text = glyph
        x_height = self.height()
        self.text = textOrig
        return x_height

    # Mainly for internal use.
    # Converts the text object into an SVG data stream.
    #
    # This method is best to invoke as part of a `with` statement
    # to ensure it closes properly:
    #   with ptxt.tosvg() as source:
    #       ...
    def tosvg(self):
        stream = io.BytesIO()

        try:
            # Initialize a cairo SVG surface of arbitrary dimensions.
            # It will all get rescaled later.
            # This code is inspired from code found on geeksforgeeks.org
            # https://www.geeksforgeeks.org/pycairo-creating-text-paths/
            with cairo.SVGSurface(stream, 700, 700) as surface:

                # surface.restrict_to_version(cairo.SVGVersion.VERSION_1_1)

                context = cairo.Context(surface)

                context.select_font_face(
                    self.font,
                    cr.FONT_SLANT_ITALIC if self.italic else cr.FONT_SLANT_NORMAL,
                    cr.FONT_WEIGHT_BOLD if self.bold else cr.FONT_WEIGHT_NORMAL
                    )
                context.set_font_size(64)  # Dummy value. Will be rescaled later
                context.set_source_rgba(*self.color, self.alpha)

                # Arbitrary position. Will be rescaled later.
                context.move_to(35, 45)

                # displays the text
                context.text_path(self.text)

                context.fill()

            # Seek to beginning of data stream so it is ready for reading.
            stream.seek(0)
        except Exception:
            stream.close()
            raise

        return stream

    # EXPERIMENTAL! May be changed in a future version!
    # Converts the text figure into an equivalent MultiSpline figure.
    # The `origin` attribute of the resulting MultiSpline will be set
    # as the position of the text figure.
    def toSpline(self):
        with self.tosvg() as source:
            spline = morpho.shapes.MultiSpline.fromsvg(source,
                align=self.align, boxHeight=self.height(),
                tightbox=True
                )
        spline.origin = self.pos
        spline.rotation = self.rotation
        spline._transform = self._transform
        return spline

    # Returns equivalent non-physical Text object
    @typecastViewCtx
    def makeText(self, view, ctx):
        txt = Text()
        txt._updateFrom(self)

        # Remove nontweenables particular to PText
        txt._nontweenables.difference_update({"_font", "_fontRatio"})
        del txt._font
        del txt._fontRatio

        txt.font = self._font
        # txt.size = self._fontRatio*self.pixelHeight(view, ctx)
        txt.size = self.fontsize(view, ctx)

        # If in a non-square view, distort the txt figure accordingly
        par = morpho.pixelAspectRatioWH(view, ctx)
        if abs(par-1) > 1e-9:
            txt._transform = np.array([[par, 0], [0, 1]], dtype=float) @ txt._transform

        return txt

    # PText is physical and so doesn't need the special
    # _drawBackgroundBox() method.
    _drawBackgroundBox = BackgroundBoxFigure._drawBackgroundBox

    def draw(self, camera, ctx):
        self.makeText(camera.view, ctx).draw(camera, ctx)

Ptext = PText  # Alias is maybe easier to type


# Decorator for tween methods in the MultiText class below.
# Reworks ordinary Text class tween methods so that they work
# in a multifigure setting.
#
# Optionally specify a method called "reverseMethod" which is used
# instead of the main method when the main method would have been
# called "in reverse" by calling textMethod(other, self, 1-t).
# This was originally developed to solve the problem of decorating
# tweenPivot() because it is not symmetric in swapping
# self with other.
def Multi(imageMethod, mainMethod=morpho.Figure.tweenLinear, *, reverseMethod=None):
    if reverseMethod is None:
        reverseMethod = imageMethod

    def wrapper(self, other, t, *args, **kwargs):

        diff = len(self.figures) - len(other.figures)
        if diff > 0:
            # Temporarily extend the image list of other with copies of
            # other's subfigures
            orig_figures = other.figures
            extension = []
            for i in range(diff):
                extension.append(other.figures[i%len(other.figures)].copy())
            other.figures = extension + other.figures
            tw = wrapper(self, other, t)
            # Restore other to its original state
            other.figures = orig_figures
            return tw
        elif diff < 0:
            # Temporarily extend the image list of self with copies of
            # self's subfigures
            orig_figures = self.figures
            extension = []
            for i in range(-diff):
                extension.append(self.figures[i%len(self.figures)].copy())
            self.figures = extension + self.figures
            tw = wrapper(self, other, t)
            # Restore self to its original state
            self.figures = orig_figures
            return tw

        figures = []
        for n in range(len(self.figures)):
            selffig = self.figures[n]
            otherfig = other.figures[n]

            # If both underlying figures have the same text and style,
            # don't do anything fancy.
            if selffig.text == otherfig.text and selffig.font == otherfig.font \
                and selffig.bold == otherfig.bold and selffig.italic == otherfig.italic:

                new = imageMethod(selffig, otherfig, t, *args, **kwargs)
                figures.append(new)
            # Fade out self and fade in other
            else:
                # Compute the scale matrices
                if isinstance(selffig, PText):
                    selfWidth, selfHeight = selffig.dimensions()
                    otherWidth, otherHeight = otherfig.dimensions()
                else:
                    selfWidth, selfHeight = selffig.pixelDimensions()
                    otherWidth, otherHeight = otherfig.pixelDimensions()
                self_to_other_size_ratio = selffig.size/otherfig.size
                forward_scale_x = otherWidth / selfWidth * self_to_other_size_ratio
                forward_scale_y = otherHeight / selfHeight * self_to_other_size_ratio
                backward_scale_x = 1/forward_scale_x
                backward_scale_y = 1/forward_scale_y
                # # Scale matrix for self so that it fits other at t=1
                # fwdMatrix = np.array(
                #     [[forward_scale_x, 0],
                #      [0, forward_scale_y]], dtype=float
                #      )
                # # Scale matrix for other so that it fits self at t=0
                # backMatrix = np.array(
                #     [[1/forward_scale_x, 0],
                #      [0, 1/forward_scale_y]], dtype=float
                #      )

                # if (self.rotation % tau) != 0:
                #     c,s = math.cos(self.rotation), math.sin(self.rotation)
                #     selfRot = np.array([[c,-s],[s,c]], dtype=float)
                #     backMatrix = selfRot @ backMatrix @ selfRot.T
                # if (other.rotation % tau) != 0:
                #     c,s = math.cos(other.rotation), math.sin(other.rotation)
                #     otherRot = np.array([[c,-s],[s,c]], dtype=float)
                #     fwdMatrix = otherRot @ fwdMatrix @ otherRot.T

                selffig1 = otherfig.copy()
                # selffig1.transform = selffig1.transform @ fwdMatrix
                selffig1.prescale_x *= forward_scale_x
                selffig1.prescale_y *= forward_scale_y
                selffig1.alpha = 0

                otherfig0 = selffig.copy()
                # otherfig0.transform = otherfig0.transform @ backMatrix
                otherfig0.prescale_x *= backward_scale_x
                otherfig0.prescale_y *= backward_scale_y
                otherfig0.alpha = 0

                newself = imageMethod(selffig, selffig1, t, *args, **kwargs)
                newother = reverseMethod(otherfig, otherfig0, 1-t, *args, **kwargs)

                figures.append(newself)
                figures.append(newother)

        # Remove temporary extensions
        if diff > 0:
            other.figures = other.figures[:-len(extensions)]
        elif diff < 0:
            self.figures = self.figures[:-len(extensions)]

        # Create final tweened multifigure object
        tw = mainMethod(self, other, t)
        tw.figures = figures

        return tw

    return wrapper


class MultiTextBase(morpho.MultiFigure):
    _baseFigure = Text

    def __init__(self, text="", *args, **kwargs):
        if isinstance(text, str):
            textlist = [self._baseFigure(text, *args, **kwargs)]
        elif isinstance(text, list) or isinstance(text, tuple):
            textlist = [(self._baseFigure(item, *args, **kwargs) if isinstance(item, str) else item) for item in text]
        elif isinstance(text, self._baseFigure):
            textlist = [text]
        else:
            textlist = [self._baseFigure(text, *args, **kwargs)]

        # Create frame figure
        # Splitting the init like this prevents superclass init
        # from doing fancy stuff with a list to __init__()
        super().__init__()
        self.figures = textlist

        # If supplied a figure input, copy its meta-settings
        if isinstance(text, morpho.Figure):
            self._updateSettings(text)

    @property
    def textlist(self):
        return self.figures

    @textlist.setter
    def textlist(self, value):
        self.figures = value

        # # Convert every figure in the list to a Text figure
        # # if possible.
        # for n in range(len(self.figures)):
        #     fig = self.figures[n]
        #     if not isinstance(fig, Text):
        #         newfig = fig.images[0].copy()
        #         self.figures[n] = newfig

    relcorners = Text.relcorners

    ### TWEEN METHODS ###

    tweenLinear = Multi(Text.tweenLinear, morpho.Figure.tweenLinear)
    tweenSpiral = Multi(Text.tweenSpiral, morpho.Figure.tweenSpiral)

    @classmethod
    def tweenPivot(cls, angle=tau/2, *args, **kwargs):
        mainPivot = morpho.MultiFigure.tweenPivot(angle, *args, **kwargs)
        pivot = Multi(Text.tweenPivot(angle, *args, **kwargs),
            mainMethod=mainPivot,
            reverseMethod=Text.tweenPivot(-angle, *args, **kwargs)
            )
        # Enable splitting
        pivot = morpho.pivotTweenMethod(cls.tweenPivot, angle)(pivot)

        return pivot

# Text class that can support drawing multiple Text figures at once.
# Useful for having one text morph into another text.
#
# See "morpho.graphics.MultiImage" for more info on the basic idea here.
#
# Bottom line: It's just like Text except you can tween between different
# underlying text strings.
@TransformableFrame.modifyFadeActions
class MultiText(MultiTextBase, TransformableFrame, PreAlignableFigure):
    def __init__(self, text="", pos=0, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.origin = pos

    @property
    def pos(self):
        return self.origin

    @pos.setter
    def pos(self, value):
        self.origin = value

    @typecastViewCtx
    def relbox(self, *args, raw=False, **kwargs):
        return shiftBox(self.box(*args, raw=raw, **kwargs), -self.origin if not raw else 0)

    @typecastViewCtx
    def box(self, view, ctx, *args, **kwargs):
        return super().box(view, ctx, *args, **kwargs)


class MultiPTextBase(MultiTextBase):
    _baseFigure = PText

    def relbox(self, pad=0, *, raw=False):
        return padbox(totalBox(subfig.box() for subfig in self.figures), pad)

    # EXPERIMENTAL! May be changed in a future version!
    # Converts the MultiPText figure into an equivalent MultiSpline.
    # The resulting MultiSpline will have its global origin set to the
    # position of the MultiPText's first component text figure's
    # position. All subsplines will have origin = 0.
    def toSpline(self):
        multisplines = [ptxt.toSpline().commitTransforms() for ptxt in self.figures]
        finalspline = morpho.shapes.MultiSpline(morpho.flattenList([multispline.figures for multispline in multisplines]))
        for spline in finalspline.figures:
            spline.origin -= self.figures[0].pos
            spline.commitTransforms()
        finalspline.origin = self.figures[0].pos
        return finalspline

# Physical version of the MultiText class.
# See MultiText and PText for more info.
@TransformableFrame.modifyFadeActions
class MultiPText(MultiPTextBase, TransformableFrame):
    def __init__(self, text="", pos=0, *args, **kwargs):
        super().__init__(text, *args, **kwargs)
        self.origin = pos

    @property
    def pos(self):
        return self.origin

    @pos.setter
    def pos(self, value):
        self.origin = value

MultiPtext = MultiPText


# 3D version of the Text class.
#
# TWEENABLES that are not shared with Text
# orient = Orientation of text relative to text position (3x3 np.array).
#          Only used if "orientable" attribute is set to True.
#          Default: np.eye(3) meaning text is oriented flat on xy-plane facing
#          in the positive z direction.
#
# OTHER ATTRIBUTES
# orientable = Boolean specifying whether text should be orientable in 3D space,
#              or just behave like a label always facing the camera. Default: False
class SpaceText(Text):

    _baseFigure = Text

    def __init__(self, text="", pos=None,
        size=64, font=None,
        bold=False, italic=False,
        anchor_x=0, anchor_y=0,
        color=(1,1,1), alpha=1,
        background=(1,1,1), backAlpha=0, backPad=0,
        *, align=None):

        if isinstance(text, self._baseFigure):
            # Copy over the state of the text figure
            super().__init__()
            self._state = text.copy()._state
            # Copy non-tweenable attributes
            self.text = text.text
            self.font = text.font
            self.bold = text.bold
            self.italic = text.italic
            self._updateSettings(text)

            pos = text.pos
        else:
            super().__init__(text, 0,
                size, font,
                bold, italic,
                anchor_x, anchor_y,
                color[:], alpha,
                background, backAlpha, backPad,
                align=align
                )

            if pos is None:
                pos = np.zeros(3)

        # Redefine pos tweenable to be 3D.
        _pos = morpho.Tweenable("_pos", morpho.matrix.array(pos), tags=["nparray", "fimage", "3d"])
        self._state.pop("pos")
        self._state["_pos"] = _pos
        _orient = morpho.Tweenable("_orient", np.identity(3), tags=["nparray", "orient"])
        self._state["_orient"] = _orient

        # self.orientable = False
        self.NonTweenable("orientable", False)

        # # Redefine pos tweenable to be 3D.
        # # Change the "pos" tweenable's "complex" tag to "nparray"
        # tags = self._state["pos"].tags
        # tags.remove("complex")
        # tags.add("nparray")
        # tags.add("fimage")

        # self.pos = pos

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = morpho.matrix.array(value)

    @property
    def orient(self):
        return self._orient

    @orient.setter
    def orient(self, value):
        self._orient = morpho.matrix.array(value)

    # def copy(self):
    #     new = super().copy()
    #     new.orientable = self.orientable
    #     return new

    # box() method for SpaceText is currently unimplemented.
    def box(self, *args, **kwargs):
        raise NotImplementedError("box() method is currently unimplemented for SpaceText.")

    def toText(self):
        txt = self._baseFigure()
        txt._state.update(self.copy()._state)
        del txt._state["_pos"]
        del txt._state["_orient"]
        txt.pos = complex(*self._pos[:2].tolist())

        txt.text = self.text
        txt.font = self.font
        txt.bold = self.bold
        txt.italic = self.italic
        txt._updateSettings(self)

        return txt


    def primitives(self, camera): # orient=np.identity(3), focus=np.zeros(3)):
        if self.alpha == 0:
            return []

        orient = camera.orient
        focus = camera.focus

        if np.allclose(focus, 0):
            pos3d = orient @ self.pos
        else:
            pos3d = orient @ (self.pos - focus) + focus
        pos3d = pos3d.tolist()

        txt = self._baseFigure()
        txt.text = self.text
        txt.pos = pos3d[0] + 1j*pos3d[1]
        txt.zdepth = pos3d[2]
        txt.size = self.size
        txt.transform = self.transform
        if self.orientable:
            txt.transform = (orient @ self.orient)[:2,:2] @ txt.transform
        txt.color = self.color
        txt.alpha = self.alpha
        txt.background = self.background
        txt.backAlpha = self.backAlpha
        txt.backPad = self.backPad
        txt.rotation = self.rotation
        txt.anchor_x = self.anchor_x
        txt.anchor_y = self.anchor_y

        txt.prescale_x = self.prescale_x
        txt.prescale_y = self.prescale_y

        txt.font = self.font
        txt.bold = self.bold
        txt.italic = self.italic

        txt._updateSettings(self)

        return [txt]


    def draw(self, camera, ctx): #, orient=np.identity(3), focus=np.zeros(3)):
        primlist = self.primitives(camera)
        if len(primlist) == 0:
            return
        txt = primlist[0]
        txt.draw(camera, ctx)

Spacetext = SpaceText  # Synonym

# 3D version of PText.
# See PText and SpaceText for more info.
class SpacePText(PText, SpaceText):
    _baseFigure = PText

    # NOT IMPLEMENTED!
    # Converts the text figure into an equivalent SpaceSpline figure.
    # The `origin` attribute of the resulting Spline will be set
    # as the position of the text figure.
    def toSpline(self):
        raise NotImplementedError

        # Create equivalent 2D PText figure
        ptext = PText()
        ptext._updateFrom(self, common=True, ignore=morpho.METASETTINGS)

        # Convert to SpaceSpline and apply transforms
        spline = morpho.shapes.SpaceSpline(ptext.toSpline())
        spline = spline.fimage(lambda v: self.orient @ v)
        spline.origin = self.pos.copy()

        return spline

    def draw(self, camera, ctx):
        SpaceText.draw(self, camera, ctx)

SpacePtext = SpacePText


# Multi version of the SpaceText class.
# See "SpaceText" and "MultiText" for more info.
class SpaceMultiText(MultiTextBase, morpho.SpaceFrame):
    _baseFigure = SpaceText

    def __init__(self, text="", *args, **kwargs):
        if isinstance(text, str):
            textlist = [self._baseFigure(text, *args, **kwargs)]
        elif isinstance(text, list) or isinstance(text, tuple):
            textlist = [(self._baseFigure(item, *args, **kwargs) if isinstance(item, str) else item) for item in text]
        elif isinstance(text, MultiTextBase):
            textlist = [self._baseFigure(item, *args, **kwargs) for item in text.figures]
        else:
            textlist = [self._baseFigure(text, *args, **kwargs)]

        # Create frame figure
        # Splitting the init like this prevents superclass init
        # from doing fancy stuff with a list to __init__()
        super().__init__()
        self.figures = textlist

        # If supplied a figure input, copy its meta-settings
        if isinstance(text, morpho.Figure):
            self._updateSettings(text)

    # box() method for SpaceMultiText is currently unimplemented.
    def box(self, *args, **kwargs):
        raise NotImplementedError("box() method is currently unimplemented for SpaceMultiText.")

    def primitives(self, camera):
        primlist = []
        for fig in self.figures:
            primlist.extend(fig.primitives(camera))

        return primlist

    def draw(self, camera, ctx):
        for fig in self.primitives(camera):
            fig.draw(camera, ctx)

SpaceMultitext = Spacemultitext = SpaceMultiText  # Synonyms


# 3D version of MultiPText class.
# See MultiPText and SpaceMultiText for more info.
class SpaceMultiPText(SpaceMultiText):
    _baseFigure = SpacePText

# Synonyms
SpaceMultiPtext = SpacemultiPText = SpacemultiPtext = SpaceMultiPText


# Non-drawable figure that contains numerical data and tools for
# displaying it.
#
# TWEENABLES
# number = Internal number (real number). Default: 0.0
#
# OTHER ATTRIBUTES
# decimal = When displaying, to what decimal point should it round?
#           Default: 0 (round to nearest integer)
# leftDigits = Minimum number of digits to display left of the
#              decimal point. Prefixes zeros if necessary.
#              Default: 0 (no extra zeros are prefixed)
# rightDigits = Maximum number of digits to display right of the
#               decimal point. Appends zeros if necessary.
#               Default: 0 (no extra zeros are appended)
# truncate = Boolean indicating whether to truncate at the decimal value
#            instead of rounding. Default: False (round, don't truncate)
class Number(morpho.Figure):
    def __init__(self, number=0.0, decimal=0, leftDigits=0, rightDigits=0, truncate=False):
        # morpho.Figure.__init__(self)
        super().__init__()

        number = morpho.Tweenable("number", number, tags=["scalar"])
        self.update([number])

        self.decimal = decimal
        self.leftDigits = leftDigits
        self.rightDigits = rightDigits
        self.truncate = truncate

    def copy(self):
        new = morpho.Figure.copy(self)

        new.decimal = self.decimal
        new.leftDigits = self.leftDigits
        new.rightDigits = self.rightDigits
        return new

    def __str__(self):
        if self.truncate:
            num = truncate(self.number, self.decimal)
        else:
            num = round(self.number, self.decimal)
        # Special case num is an integer AND we're not to display
        # any trailing zeros.
        if num == int(num) and self.rightDigits == 0:
            string = str(int(num))
            string = "0"*(self.leftDigits - len(string)) + string
            return string
        num = float(num)
        string = str(abs(num))
        numLeftDigits = string.find(".")
        numRightDigits = len(string) - numLeftDigits - 1
        string = "0"*(self.leftDigits - numLeftDigits) + string \
               + "0"*(self.rightDigits - numRightDigits)

        if num < 0: string = "-" + string

        return string

    ### TWEEN METHODS ###

    # @morpho.TweenMethod
    # def tweenLinear(self, other, t):
    #     Num = self.copy()
    #     Num.number = morpho.numTween(self.number, other.number, t)
    #     return Num

    @morpho.TweenMethod
    def tweenZoom(self, other, t):
        # This tween method requires both numbers to be positive.
        # If not, default to the Instant tween method.
        if not(self.number > 0 and other.number > 0):
            return self.copy()

        Num = self.copy()
        a = self.number
        b = other.number
        Num.number = a*(b/a)**t

        return Num

# Formats a number according to the parameters described in
# the Number class. See Number for more info.
# This function essentially creates a Number object then
# returns its string form.
def formatNumber(*args, **kwargs):
    num = Number(*args, **kwargs)
    return str(num)

# Converts a number into a string by rounding it to the
# given number of decimal places, appending zeros if necessary
# to ensure there are always the same number of digits trailing
# the decimal point.
def fixedLengthDecimal(number, decimal):
    num = Number(number, decimal, rightDigits=decimal)
    return str(num)


### GROUPS AND PARAGRAPHS ###

@Transformable2D(exclude="origin")
class FancyMultiTextBase(MultiTextBase, PreAlignableFigure):

    def __init__(self, text="", *args, **kwargs):

        # if isinstance(text, type(self)):
        #     super().__init__()
        #     textcopy = text.copy()
        #     self._state = textcopy._state
        #     self._nontweenables = textcopy._nontweenables
        #     self._updateSettings(textcopy)
        #     return
        if isinstance(text, MultiTextBase):
            # text = text.figures
            super().__init__()
            self._updateFrom(text)
        else:
            super().__init__(text, *args, **kwargs)

        self.Tweenable("anchor_x", 0, tags=["scalar"])
        self.Tweenable("anchor_y", 0, tags=["scalar"])
        self.Tweenable("background", (1,1,1), tags=["color"])
        self.Tweenable("backAlpha", 0, tags=["scalar"])
        self.Tweenable("backPad", 0, tags=["scalar"])
        # Dummy value for _refbox is assigned because view and windowShape
        # are needed to compute it.
        self.Tweenable("_refbox", [-1,1,-1,1], tags=["scalar", "list"])

    @property
    def pos(self):
        return self.origin

    @pos.setter
    def pos(self, value):
        self.origin = value

    @property
    def align(self):
        return (self.anchor_x, self.anchor_y)

    @align.setter
    def align(self, value):
        self.anchor_x, self.anchor_y = value

    def partition(self, *args, **kwargs):
        raise NotImplementedError("partition() is not supported for FancyMultiText figures.")

    def combine(self, *args, **kwargs):
        raise NotImplementedError("combine() is not supported for FancyMultiText figures.")

    # Mainly for internal use.
    # Updates the internal reference box of the paragraph.
    def updateReferenceBox(self, *args, **kwargs):
        # Do I really need _dz=0 here? Weirdly, it seems to make
        # no difference, but I feel like it should.
        # Upon closer inspection, I think it doesn't matter because
        # the only thing part of the refbox that's used is its
        # width and height. However, I think it's safer to set
        # _dz=0 here, so that's what I'll do.
        self._refbox = self.box(*args, raw=True, _dz=0, **kwargs)
        return self

    # For internal use.
    # Calculates the translation vector needed to handle positioning
    # the paragraph according to its align parameter.
    def _refboxTranslation(self):
        # Reference box for use in calculating alignment parameters
        left, right, bottom, top = self._refbox

        width = right - left
        height = top - bottom

        # Calculate translation
        dx = -morpho.lerp(-width/2, width/2, self.anchor_x, start=-1, end=1)
        dy = -morpho.lerp(-height/2, height/2, self.anchor_y, start=-1, end=1)
        return complex(dx, dy)

    # General version of totalBox() that can be used to implement totalBox()
    # for both FancyMultiText and FancyMultiPText.
    def _totalBoxGeneral(self, viewctx=(), pad=0, *, raw=False, _dz=None, _verbose=False):
        boxes = [fig.box(*viewctx, pad=0, raw=False) for fig in self.figures]
        left = min(box[0] for box in boxes)
        right = max(box[1] for box in boxes)
        bottom = min(box[2] for box in boxes)
        top = max(box[3] for box in boxes)

        dz = self._refboxTranslation() if _dz is None else _dz
        rawbox = shiftBox([left, right, bottom, top], dz)

        if raw:
            bigbox = padbox(rawbox, pad)
        else:
            if self.rotation == 0 and np.array_equal(self._transform, I2):
                # No fancy calculations, just shift
                bigbox = shiftBox(padbox(rawbox, pad), self.origin)
            else:
                # Do fancy transformation calculations
                bigbox = BoundingBoxFigure._transformedBox(rawbox, self.origin, self.rotation, self._transform, pad)

        if _verbose:
            return dict(rawbox=rawbox, bigbox=bigbox)
        return bigbox

    # Returns the physical bounding box of the entire text group as
    # [xmin, xmax, ymin, ymax]
    # Note that this is with respect to the group's LOCAL origin,
    # meaning this method does not take the `pos` attribute into
    # account.
    @typecastViewCtx
    def totalBox(self, view, ctx, *args, **kwargs):
        return self._totalBoxGeneral((view, ctx), *args, **kwargs)

    # Returns the center of the text group's bounding box.
    def totalCenter(self, *args, **kwargs):
        box = self.totalBox(*args, **kwargs)
        return mean(box[:2]) + 1j*mean(box[2:])

    # Returns the physical bounding box of the whole text group as
    # [xmin, xmax, ymin, ymax].
    def box(self, *args, raw=False, **kwargs):
        boxdata = self.totalBox(*args, _verbose=True, **kwargs)
        rawbox = boxdata["rawbox"]
        if raw:
            return rawbox
        return boxdata["bigbox"]

    corners = Text.corners

    @typecastViewCtx
    def width(self, view, ctx):
        a,b,c,d = self.box(view, ctx, raw=True)
        return b - a

    @typecastViewCtx
    def height(self, view, ctx):
        a,b,c,d = self.box(view, ctx, raw=True)
        return d - c

    # Moves the text group so that its total center is at the origin.
    # This makes it so the alignment respects the `pos` attribute.
    def recenter(self, *args, **kwargs):
        center = self.totalCenter(*args, **kwargs)
        for fig in self.figures:
            fig.pos -= center

    def makeFrame(self, *args, ignoreBackground=False, **kwargs):
        dz = self._refboxTranslation()

        # Apply translations/transformations
        figs = []
        rot = cmath.exp(1j*self.rotation) if self.rotation != 0 else 1
        mat = 1 if np.array_equal(self._transform, I2) else morpho.matrix.Mat(self._transform)
        maxSubalpha = 0  # Will eventually hold the max subfigure alpha value for use later
        for fig in self.figures:
            maxSubalpha = max(maxSubalpha, fig.alpha)
            fig = fig.copy()
            fig.pos += dz
            fig.pos = mat*(rot*(fig.pos))
            fig.pos += self.origin
            fig.rotation += self.rotation
            fig._transform = self._transform @ fig._transform
            figs.append(fig)

        if self.backAlpha > 0 and not ignoreBackground:
            rect = morpho.grid.rect(padbox(self.box(*args, raw=True, _dz=dz, **kwargs), self.backPad))
            rect.origin = self.origin
            rect.width = 0
            rect.fill = self.background
            rect.alpha = self.backAlpha*maxSubalpha
            rect.rotation = self.rotation
            rect._transform = self._transform

            frm = morpho.Frame([rect, MultiText(figs)])
            return frm

        return MultiText(figs)

    def draw(self, camera, ctx):
        self.makeFrame(camera, ctx).draw(camera, ctx)

    ### TWEEN METHODS ###

    @morpho.TweenMethod
    def tweenLinear(self, other, t):
        tw = MultiTextBase.tweenLinear(self, other, t)
        return tw

    @morpho.TweenMethod
    def tweenSpiral(self, other, t):
        tw = MultiTextBase.tweenSpiral(self, other, t)
        return tw

    @classmethod
    def tweenPivot(cls, angle=tau/2):
        mainPivot = morpho.MultiFigure.tweenPivot(angle)
        twMethod1 = Multi(Text.tweenPivot(angle),
            mainMethod=mainPivot,
            reverseMethod=Text.tweenPivot(-angle)
            )

        @morpho.pivotTweenMethod(cls.tweenPivot, angle)  # Enable splitting
        def pivot(self, other, t):
            tw = twMethod1(self, other, t)
            return tw

        return pivot

@FancyMultiTextBase.action
def morphFrom(actor, source, *args, **kwargs):
    if isinstance(source, (list, tuple)):
        raise NotImplementedError("Multi-source morphFrom() cannot be used with Paragraph types.")
    return morpho.Figure.actions["morphFrom"](actor, source, *args, **kwargs)

# Fancier MultiText figure that has some global attributes
# that affect the entire group. These attributes include
# pos, anchor_x/y, alpha, rotation, transform, background,
# backAlpha, backPad.
#
# This class is mainly for internal use by the paragraph()
# function, and you probably don't want to use it directly.
# If you just want something like a morphable single Text
# figure, use vanilla MultiText instead.
@TransformableFrame.modifyFadeActions
class FancyMultiText(FancyMultiTextBase):
    pass
    # NOTE: This originally also inherited from TransformableFrame,
    # but commitTransforms() didn't work correctly (I think because
    # of how toplevel `align` interacts with it). Correct this in the
    # future.


# Fancy version of MultiPText.
# See FancyMultiText and MultiPText for more info.
class FancyMultiPText(FancyMultiText):
    _baseFigure = PText

    # Returns the physical bounding box of the entire text group as
    # [xmin, xmax, ymin, ymax]
    def totalBox(self, *args, **kwargs):
        return self._totalBoxGeneral((), *args, **kwargs)

    def width(self):
        a,b,c,d = self.box(raw=True)
        return b - a

    def height(self):
        a,b,c,d = self.box(raw=True)
        return d - c

    corners = PText.corners

    # EXPERIMENTAL! May be changed in a future version!
    # Converts the text figure into an equivalent MultiSpline figure.
    # The origin attribute of the MultiSpline will match the pos
    # attribute of the text figure.
    def toSpline(self):
        multispline = MultiPText(self.makeFrame(raw=True, ignoreBackground=True).figures).toSpline()
        for spline in multispline.figures:
            spline.origin += multispline.origin - self.origin
            spline.commitTransforms()
        multispline.origin = self.origin
        return multispline

    def draw(self, camera, ctx):
        self.makeFrame().draw(camera, ctx)

FancyMultiPtext = FancyMultiPText


# Special class used to render 3D paragraphs.
# Mainly for internal use by the paragraph3d() function.
class SpaceParagraph(FancyMultiTextBase, morpho.SpaceFrame):
    _baseMultiFigure = FancyMultiText

    def __init__(self, text="", *args, **kwargs):

        if isinstance(text, FancyMultiTextBase):
            super().__init__()
            self._updateFrom(text)
        else:
            super().__init__(text, *args, **kwargs)

        # Redefine pos tweenable to be 3D.
        self.Tweenable("_pos", morpho.matrix.array(self.origin), tags=["nparray", "fimage", "3d"])
        self.Tweenable("_orient", np.identity(3), tags=["nparray", "orient"])

        # Reset origin attribute because it has already been accounted for
        # in setting the `_pos` tweenable and in SpaceParagraphs, `pos` and
        # `origin` play different roles.
        self.origin = 0

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = morpho.matrix.array(value)

    @property
    def orient(self):
        return self._orient

    @orient.setter
    def orient(self, value):
        self._orient = morpho.matrix.array(value)

    # box() method for SpaceParagraph is currently unimplemented.
    def box(self, *args, **kwargs):
        raise NotImplementedError("box() method is currently unimplemented for SpaceParagraph.")

    def makeFrame(self, camera, ctx):
        raise NotImplementedError

    def primitives(self, camera):
        orient = camera.orient
        focus = camera.focus

        if np.allclose(focus, 0):
            pos3d = orient @ self.pos
        else:
            pos3d = orient @ (self.pos - focus) + focus

        # Create equivalent 2D FancyMultiText object
        txt = self._baseMultiFigure()
        txt._updateFrom(self, common=True)
        txt.origin = txt.origin + (pos3d[0] + 1j*pos3d[1]).tolist()
        txt.zdepth = pos3d[2]
        txt._transform = (orient @ self.orient)[:2,:2] @ self._transform

        return [txt]

    def draw(self, camera, ctx):
        # Use default SpaceFigure draw()
        morpho.SpaceFigure.draw(self, camera, ctx)

@SpaceParagraph.action
def fadeIn(*args, **kwargs):
    return morpho.Figure.actions["fadeIn"](*args, **kwargs)

@SpaceParagraph.action
def fadeOut(*args, **kwargs):
    return morpho.Figure.actions["fadeOut"](*args, **kwargs)

# @SpaceParagraph.action
# def rollback(*args, **kwargs):
#     return morpho.Figure.actions["rollback"](*args, **kwargs)

# Physical version of SpaceParagraph.
# Mainly for internal use by paragraph3dPhys().
# See SpaceParagraph and PText for more info.
class SpaceParagraphPhys(SpaceParagraph):
    _baseMultiFigure = FancyMultiPText


# Returns an invisible Text figure of a pair of periods.
# A rough way to provide a one-off space between two clauses
# in a paragraph figure.
def space(**kwargs):
    return Text("..", alpha=0).set(**kwargs, _isWhitespace=True)

# Adds the special underline character "\u0332" after every
# character in a string. Can be used as part of defining a
# Text object to add underlining to it:
#   Text(underline("Hello world!"))
# Note that underlines may break partially across spaces
# and may otherwise incorrectly render as this is a somewhat
# hack of an implementation. Use at your own risk and don't
# rely on it!
def underline(string):
    return string.replace("", "\u0332")[1:]

# Takes a collection of Text figures and returns a FancyMultiText
# figure that concatenates all the individual Text figures.
#
# This function has been mostly obsoleted by the paragraph()
# function. You should probably use that one instead.
#
# NOTE: This function makes copies of the individual Text figures
# to construct the MultiText figure. The originals are not affected.
#
# INPUTS
# textfigs = List/tuple of Text figures
# view = viewbox of the layer this group will be in
# windowShape = Tuple denoting pixel dimensions of the animation window
#               (pixel width, pixel height)
# pos = Position of the text group (complex number). Default: 0
# anchor_x = Overall horizontal alignment parameter.
#            -1 = left-aligned, 0 = center-aligned, 1 = right-aligned.
#            Default: 0 (center-aligned)
# anchor_y = Overall vertical alignment parameter.
#            -1 = bottom-aligned, 0 = center-aligned, 1 = top-aligned.
#            Default: 0 (center-aligned)
# alpha = Overall opacity of group. Default: 1 (opaque)
# gap = Pixel separation between adjacent text figures.
#       Default: 0 pixels
# KEYWORD ONLY INPUTS
# xbuf = Relative spacing between adjacent text figures, specified in
#        units of "em's", i.e. number of "M" widths of the text.
#        For variable-sized text, the spacing between two
#        adjacent text figures is done with "em" relative to the
#        previous text figure.
def group(textfigs, view, windowShape,
    pos=0, anchor_x=0, anchor_y=0, alpha=1, gap=0,
    *, align=None, xbuf=None, physical=False, physicalGap=False):

    widths = []
    heights = []

    # `physical` boolean says whether the underlying
    # figures in textfigs are PText or regular Text.
    if physical:
        camctx = ()
    else:
        camctx = (view, windowShape)

    # `physicalGap` indicates whether the gap parameter
    # is already in physical units or not.
    if not physicalGap:
        # Convert gap to physical units
        gap = morpho.physicalWidth(gap, *camctx)

    # Handle case that Frame figure is given
    if isinstance(textfigs, morpho.Frame):
        textfigs = textfigs.figures

    if align is not None:
        anchor_x, anchor_y = align

    if xbuf is not None:
        # Calculate individual physical em sizes
        ems = []
        for fig in textfigs:
            em = fig.em()
            if not physical:
                em = morpho.physicalWidth(em, *camctx)
            ems.append(em)

    # Record the widths and heights of all text figures
    totalWidth = 0
    for fig in textfigs:

        # Check if the figure is NOT a Text figure
        if not isinstance(fig, Text):
            raise TypeError("At least one figure in the list is NOT an instance of the Text class.")
        # Check for non-identity transformations. For now,
        # group() only works on text figures that have not been
        # transformed using a transformation attribute such as
        # rotation, prescale_x, prescale_y, or transform.
        if fig.rotation != 0 or fig.prescale_x != 1 \
            or fig.prescale_y != 1 or not np.array_equal(fig._transform, I2):

            raise ValueError("At least one text figure has a non-identity transformation attribute.")

        width, height = fig.dimensions(*camctx)
        widths.append(width)
        heights.append(height)
        totalWidth += width

    if xbuf is None:
        totalWidth += gap*(len(textfigs)-1)
    else:
        totalWidth += xbuf*sum(ems)
    totalHeight = max(heights)
    totalxRadius = totalWidth/2
    totalyRadius = totalHeight/2
    curpos = pos-totalxRadius*(anchor_x+1) - 1j*totalyRadius*(anchor_y+1)

    if xbuf is None:
        gaps = [gap]*len(textfigs)
    else:
        gaps = [xbuf*em for em in ems]
    for n, fig in enumerate(textfigs):
        # Make a copy of fig so to not affect the original
        fig = fig.copy()
        textfigs[n] = fig

        width = widths[n]
        height = heights[n]
        fig.pos = curpos + (fig.anchor_x+1)*width/2 + 1j*(fig.anchor_y+1)*height/2
        fig.alpha *= alpha
        curpos += width + gaps[n]

    return FancyMultiText(textfigs)

# Creates a conformed version of the given textarray so it's a list
# of lists of Text figures, where each sublist represents a row in
# a paragraph. Throws error if unable to conform the given textarray.
def conformText(textarray):
    # Handle nonstandard values for textarray
    if not isinstance(textarray, (list, tuple)):
        return [[textarray]]

    # Handle empty textarray
    if len(textarray) == 0:
        raise IndexError("Empty `textarray` was given.")

    # Handle list of non-lists
    if not any(isinstance(row, (list, tuple)) for row in textarray):
        textarray = [textarray]

    # Go row by row and conform the types found
    for i, row in enumerate(textarray):
        # Turn strings into singleton lists of Text figures
        if isinstance(row, str):
            textarray[i] = [Text(row)]
            continue
        # Turn Text figures into singleton lists of themselves.
        elif isinstance(row, Text):
            textarray[i] = [row]
            continue
        elif not isinstance(row, (list, tuple)):
            raise TypeError(f"Invalid type {type(row).__name__} for `textarray` row.")
        elif len(row) == 0:
            raise IndexError("Empty sublist in `textarray`.")
        # Turn any individual string items into Text figures
        for j, item in enumerate(row):
            if isinstance(item, str):
                row[j] = Text(item)

    return textarray

# Creates a group of Text figures that look like a paragraph.
# It's basically a multi-line version of group(), and can
# probably replace it.
#
# INPUTS
# textarray = List of lists of Text figures where each sublist
#             represents a single row of the paragraph.
#             Alternatively can be a string containing newlines
#             which will be split into individual default Text figures.
# view = viewbox of the layer this group will be in.
#        Can also be a Camera actor or Layer object, in which case
#        the latest viewbox is used.
# windowShape = Tuple denoting pixel dimensions of the animation window
#               (pixel width, pixel height)
#               Can also be specified as an Animation object, in which
#               case the `windowShape` attribute is extracted and used.
#               If unspecified, it will be inferred from `view`.
# pos = Position of the text group (complex number). Default: 0
# anchor_x = Overall horizontal position alignment parameter.
#            -1 = left-aligned, 0 = center-aligned, 1 = right-aligned.
#            Default: 0 (center-aligned)
# anchor_y = Overall vertical position alignment parameter.
#            -1 = bottom-aligned, 0 = center-aligned, 1 = top-aligned.
#            Default: 0 (center-aligned)
# alpha = Overall opacity of group. Default: 1 (opaque)
# xgap = Pixel separation between adjacent text figures in a row.
#        Default: 0 pixels
# ygap = Pixel separation between adjacent rows in the paragraph.
#        Default: 0 pixels
# KEYWORD ONLY INPUTS
# flush = Inter-row alignment.
#         -1 = left-flush, 0 = center-flush, 1 = right-flush.
#         Default: 0 (center-flush)
# align = Specify both anchors at once as a tuple: (anchor_x, anchor_y)
#         Overrides anchor_x and anchor_y if also specified.
#         Default: None (use given anchor_x, anchor_y)
# xbuf = Relative spacing between adjacent text figures, specified in
#        units of "em's", i.e. number of "M" widths of the text.
#        For variable-sized text in a row, the spacing between two
#        adjacent text figures is done with "em" relative to the
#        previous text figure.
# ybuf = Relative spacing between adjacent rows of text figures,
#        specified in units of "ex's", i.e. number of "x" heights of
#        the text in the row. For variable height text in a row,
#        the max is used.
# gap = Alias for xgap. Exists to match the `gap` arg in group()
#       Overrides xgap if specified.
#       Default: None (ignore and just use given xgap value)
# rotation = Rotation angle of entire paragraph about anchor point
#            Default: 0 radians
# transform = Transformation matrix of entire paragraph about
#             anchor point. Default: identity
# alphabet = String of characters to use to determine line height.
#            Default: morpho.text.LINE_HEIGHT_ALPHABET constant,
#            which by default is all 52 upper and lowercase glyphs
#            in the English alphabet.
# **kwargs = Any other keyword arguments will be applied to
#            every component Text figure:
#            txt.set(**kwargs) for each txt in the textarray
def paragraph(textarray, view, windowShape=None,
    pos=0, anchor_x=0, anchor_y=0, alpha=1, xgap=0, ygap=0,
    *, flush=0, align=None, gap=None, xbuf=None, ybuf=None,
    rotation=0, transform=None,
    background=(1,1,1), backAlpha=0, backPad=0,
    alphabet=None,
    **kwargs):

    if transform is None: transform = np.eye(2)

    # If windowShape unspecified, try to infer it
    # from the given `view` value.
    if windowShape is None:
        try:
            if isinstance(view, morpho.Layer):
                windowShape = view.owner.windowShape
            elif isinstance(view, morpho.Actor):
                windowShape = view.owner.owner.windowShape
            elif isinstance(view, morpho.anim.Camera):
                windowShape = view.owner.owner.owner.windowShape
            else:
                raise AttributeError
        except AttributeError:
            raise TypeError("Cannot infer windowShape.")

    if alphabet is None:
        alphabet = LINE_HEIGHT_ALPHABET

    # Handle case that Frame figure is given
    if isinstance(textarray, morpho.Frame):
        textarray = textarray.figures

    if textarray is None:
        textarray = [[Text("")]]
    elif isinstance(textarray, str):
        stringlist = textarray.split("\n")
        textarray = [[Text(string)] for string in stringlist]
    else:
        textarray = conformText(textarray)

    # Apply any kwargs to the component figures
    if len(kwargs) > 0:
        for row in textarray:
            for fig in row:
                fig.set(**kwargs)

    # Handle Layer/Camera/Animation type inputs to
    # view and windowShape.
    if isinstance(view, morpho.Layer):
        view = view.camera.last().view
    elif isinstance(view, morpho.Actor):
        view = view.last().view
    elif isinstance(view, morpho.anim.Camera):
        view = view.view
    if isinstance(windowShape, morpho.Animation):
        windowShape = windowShape.windowShape

    physical = isinstance(textarray[0][0], PText)
    if physical:
        camctx = ()
    else:
        camctx = (view, windowShape)

    # gap overrides xgap if specified. It exists for backward
    # compatibility with the input scheme of the group() function.
    if gap is not None:
        xgap = gap

    # Convert gap units to physical units if not in physical mode
    if not physical:
        # Convert gaps to physical units
        xgap = morpho.physicalWidth(xgap, *camctx)
        ygap = morpho.physicalHeight(ygap, *camctx)

    # Calculate combined gaps between all elements in each row
    if xbuf is None:
        rowgaps = [(len(row)-1)*xgap for row in textarray]
    else:
        rowgaps = []
        for row in textarray:
            rowgaps.append(xbuf*sum([fig.em() if isinstance(fig, PText) else morpho.physicalWidth(fig.em(), *camctx) for fig in row[:-1]]))

    # Calculate line heights (informally)
    lineHeights = []
    for row in textarray:
        lineHeights.append(max(fig.ex(alphabet) if isinstance(fig, PText) else morpho.physicalHeight(fig.ex(alphabet), *camctx) for fig in row))
    # The mean of the line heights between adjacent lines. Useful later on.
    lineHeightMeans = [mean([h1, h2]) for h1, h2 in zip(lineHeights[:-1], lineHeights[1:])]

    # Calculate ygaps between each row based on whether ybuf
    # is specified or not.
    if ybuf is None:
        ygaps = [ygap]*(len(textarray)-1)
    else:
        ygaps = [ybuf*lineMean for lineMean in lineHeightMeans]

    # Apply align parameter if given
    if align is not None:
        anchor_x, anchor_y = align

    # Calculate y-positions of all rows
    yPositions = [0]
    rowBoxes = []
    for row, row_next, lineMean, ygap in zip(textarray[:-1], textarray[1:], lineHeightMeans, ygaps):
        boxes = [shiftBox(fig.box(*camctx, raw=True), fig.pos) for fig in row]
        boxes_next = [fig.box(*camctx, raw=True) for fig in row_next]
        rowBoxes.append(boxes)
        yPositions.append(yPositions[-1]-ygap-lineMean)
    adjust = -mean([yPositions[0], yPositions[-1]])
    yPositions = [y+adjust for y in yPositions]

    # Append final row of boxes
    rowBoxes.append([shiftBox(fig.box(*camctx, raw=True), fig.pos) for fig in textarray[-1]])

    # Create rows
    rows = []
    for i, row in enumerate(textarray):
        rowWidth = sum(box[1]-box[0] for box in rowBoxes[i]) + rowgaps[i]
        rowPosition = -morpho.lerp(-rowWidth/2, rowWidth/2, flush, start=-1, end=1) + 1j*yPositions[i]
        if physical:
            row = group(row, DUMMY, DUMMY, pos=rowPosition, gap=xgap, xbuf=xbuf, physical=physical, physicalGap=True)
        else:
            row = group(row, *camctx, pos=rowPosition, gap=xgap, xbuf=xbuf, physical=physical, physicalGap=True)
        rows.append(row)

    # Pool all the rows into a single FancyMultiText figure
    figs = []
    for row in rows:
        figs.extend(row.figures)
    if physical:
        parag = FancyMultiPText(figs)
    else:
        parag = FancyMultiText(figs)
    parag.updateReferenceBox(*camctx)
    parag.pos = pos
    parag.anchor_x = anchor_x
    parag.anchor_y = anchor_y
    parag.alpha = alpha
    parag.rotation = rotation
    parag._transform = transform
    parag.background = background
    parag.backAlpha = backAlpha
    parag.backPad = backPad
    # _dz is set to 0 here because we don't want to
    # center based on the current alignment settings.
    # That is, we want to recenter AS IF the paragraph
    # is center-aligned.
    parag.recenter(*camctx, raw=True, _dz=0)

    return parag


# Physical version of paragraph().
# See paragraph() for more info.
# Note that this function will auto-convert any non-physical
# Text figures into PText figures on the fly.
def paragraphPhys(textarray, *args, **kwargs):
    # Handle case that Frame figure is given
    if isinstance(textarray, morpho.Frame):
        textarray = textarray.figures

    if textarray is None:
        textarray = [[PText("")]]
    elif isinstance(textarray, str):
        stringlist = textarray.split("\n")
        textarray = [[PText(string)] for string in stringlist]
    else:
        textarray = conformText(textarray)

    # Convert all items in the textarray into PText
    # if they aren't already.
    for row in textarray:
        for n, item in enumerate(row):
            if not isinstance(item, PText):
                row[n] = PText(item)

    # Convert everything to PText if needed
    for row in textarray:
        for n,fig in enumerate(row):
            if not isinstance(fig, PText):
                row[n] = PText(fig)

    return paragraph(textarray, DUMMY, DUMMY, *args, **kwargs)

# 3D version of paragraph(). See paragraph() for more info.
#
# Note that despite returning a space figure, the `textarray` input
# should be composed of 2D Text figures, NOT 3D SpaceText figures!
# They will be converted within the function.
#
# You also have to specify an `orient` rotation matrix, as space
# paragraphs cannot be non-orientable. It defaults to the identity.
def paragraph3d(textarray, view, windowShape=None,
    pos=0, orient=None, *args, _use_paragraphPhys=False, **kwargs):

    # Create 2d paragraph
    if _use_paragraphPhys:
        parag = paragraphPhys(textarray, 0, *args, **kwargs)
    else:
        parag = paragraph(textarray, view, windowShape, 0, *args, **kwargs)

    # Handle default orient
    if orient is None:
        orient = np.eye(3)

    # Turn it into a SpaceParagraph
    if _use_paragraphPhys:
        spaceParag = SpaceParagraphPhys(parag)
    else:
        spaceParag = SpaceParagraph(parag)
    spaceParag.set(pos=pos, orient=orient)

    return spaceParag

def paragraph3dPhys(textarray, *args, **kwargs):
    return paragraph3d(
        textarray, DUMMY, DUMMY, *args, _use_paragraphPhys=True, **kwargs
        )

# Physical version of paragraph3d().
# See paragraph3d() and paragraphPhys() for more info.
paragraph3dphys = paragraph3dPhys
