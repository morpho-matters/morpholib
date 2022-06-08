
import morpholib as morpho
import morpholib.anim, morpholib.grid
from morpholib.tools.basics import *

import cairo
cr = cairo

import numpy as np

# Setup a dummy context for use in computing certain text values
# outside of draw time (e.g. width and height)
mation = morpho.Animation()
mation.setupContext()
ctx0 = mation.context
del mation

# Default font. If set to a font's name, this font
# will be used as the default font for the Text class
# and its derivatives.
defaultFont = "Times New Roman"

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
class Text(morpho.Figure):
    def __init__(self, text="", pos=complex(0),
        size=64, font=None,
        bold=False, italic=False,
        anchor_x=0, anchor_y=0,
        color=(1,1,1), alpha=1,
        background=(1,1,1), backAlpha=0, backPad=0):

        super().__init__()

        # Handle Text figure derivative inputs for text.
        # Just extract the "text" attribute.
        if isinstance(text, Text) or isinstance(text, MultiText) \
            or isinstance(text, SpaceMultiText):
            text = text.text

        if type(color) is tuple:
            color = list(color)
        elif type(color) is not list:
            raise TypeError("Unsupported color input")

        # Take last three coords of color.
        color = list(color[:3])

        # Tack on zeros if len(color) < 4
        if len(color) < 3:
            color.extend([0]*(4-len(color)))

        # Turn position into complex
        if type(pos) in (list, tuple):
            pos = pos[0] + 1j*pos[1]

        # Create tweenables
        pos = morpho.Tweenable("pos", pos, tags=["complex"])
        size = morpho.Tweenable("size", size, tags=["size"])
        anchor_x = morpho.Tweenable("anchor_x", anchor_x, tags=["scalar"])
        anchor_y = morpho.Tweenable("anchor_y", anchor_y, tags=["scalar"])
        _transform = morpho.Tweenable("_transform", np.identity(2), tags=["nparray"])
        color = morpho.Tweenable("color", color, tags=["color"])
        alpha = morpho.Tweenable("alpha", alpha, tags=["scalar"])
        background = morpho.Tweenable("background", background, tags=["color"])
        backAlpha = morpho.Tweenable("backAlpha", backAlpha, tags=["scalar"])
        backPad = morpho.Tweenable("backPad", backPad, tags=["scalar"])
        # CCW rotation in radians
        rotation = morpho.Tweenable("rotation", 0, tags=["scalar"])

        # These are the pre-transformation scale factors. These get
        # applied to the text BEFORE rotation and transform do.
        # This is mainly for use in the Multi decorator, so that
        # tweening between two texts with differing rotation parameters
        # works correctly.
        prescale_x = morpho.Tweenable("prescale_x", 1, tags=["scalar"])
        prescale_y = morpho.Tweenable("prescale_y", 1, tags=["scalar"])

        self.update([pos, size, anchor_x, anchor_y, _transform,
            color, alpha, background, backAlpha, backPad, rotation,
            prescale_x, prescale_y])

        # Other attributes
        self.text = text
        self.font = font if font is not None else defaultFont
        self.bold = bold
        self.italic = italic

    @property
    def transform(self):
        return self._transform

    @transform.setter
    def transform(self, value):
        self._transform = morpho.matrix.array(value)


    def copy(self):
        # Do a standard figure copy first
        # new = morpho.Figure.copy(self)
        new = super().copy()

        # Copy the non-tweenable attributes
        new.text = self.text
        new.font = self.font
        new.bold = self.bold
        new.italic = self.italic

        return new

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
    # Note this ignores the "transform" tweenable.
    def dimensions(self, view, ctx):
        if isinstance(view, morpho.anim.Camera):
            view = view.view

        WIDTH, HEIGHT = self.pixelDimensions()
        width = morpho.physicalWidth(WIDTH, view, ctx)
        height = morpho.physicalHeight(HEIGHT, view, ctx)

        return (width, height)

    # Returns bounding box of the text in physical units.
    # Mainly of use internally to draw the background box.
    # Note: Ignores rotation and prescale factors.
    def box(self, view, ctx, pad=0):
        width, height = self.dimensions(view, ctx)
        # Modify by prescale factors
        width *= self.prescale_x
        height *= self.prescale_y
        align_x, align_y = self.anchor_x, self.anchor_y
        a = self.pos.real - width/2*(align_x + 1)
        b = a + width
        c = self.pos.imag - height/2*(align_y + 1)
        d = c + height

        return [a-pad, b+pad, c-pad, d+pad]

    # Same as box(), but the coordinates are relative to
    # the text's position.
    def relbox(self, view, ctx, pad=0):
        width, height = self.dimensions(view, ctx)
        # Modify by prescale factors
        width *= self.prescale_x
        height *= self.prescale_y
        align_x, align_y = self.anchor_x, self.anchor_y
        a = -width/2*(align_x + 1)
        b = a + width
        c = -height/2*(align_y + 1)
        d = c + height

        return [a-pad, b+pad, c-pad, d+pad]

    # Returns the four corners of the text's bounding box
    # plus any optional padding. The sequence of the corners is
    # NW, SW, SE, NE.
    def corners(self, view, ctx, pad=0):
        a,b,c,d = self.box(view, ctx, pad)

        NW = a + d*1j
        SW = a + c*1j
        SE = b + c*1j
        NE = b + d*1j

        return [NW,SW,SE,NE]

    # Same as corners(), but the coordinates are relative to wherever
    # the text's physical position is.
    def relcorners(self, view, ctx, pad=0):
        a,b,c,d = self.relbox(view, ctx, pad)

        NW = a + d*1j
        SW = a + c*1j
        SE = b + c*1j
        NE = b + d*1j

        return [NW,SW,SE,NE]

    # Returns the visual centerpoint of the text, ignoring
    # the transformation attributes.
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
    def width(self, view, ctx):
        return self.dimensions(view, ctx)[0]

    # Returns the physical height of the text.
    # Same as mytext.dimensions(view, ctx)[1]
    def height(self, view, ctx):
        return self.dimensions(view, ctx)[1]

    def draw(self, camera, ctx):
        # Do nothing if size less than 1.
        if self.size < 1:
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

        if self.backAlpha > 0:
            # Construct background rectangle and draw it
            box = self.relbox(view, ctx, pad=self.backPad)
            rect = morpho.grid.rect(box)
            rect.origin = self.pos
            rect.width = 0
            rect.fill = self.background
            rect.alpha = self.backAlpha*self.alpha
            rect.rotation = self.rotation
            rect.transform = self.transform
            rect.draw(camera, ctx)

        ctx.save()

        # ctx.translate(x,-y)
        # ctx.translate(0, 2*y)
        ctx.translate(x,y)

        # Apply transformation matrix if necessary
        if not np.array_equal(self.transform, np.identity(2)):
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
def Multi(imageMethod, reverseMethod=None):
    if reverseMethod is None:
        reverseMethod = imageMethod

    def wrapper(self, other, t, *args, **kwargs):

        diff = len(self.figures) - len(other.figures)
        if diff > 0:
            # Temporarily extend the image list of other with copies of
            # other's final image
            extension = []
            for i in range(diff):
                extension.append(other.figures[-1].copy())
            other.figures.extend(extension)
            tw = wrapper(self, other, t)
            # Restore other to its original state
            other.figures = other.figures[:-diff]
            return tw
        elif diff < 0:
            # Temporarily extend the image list of self with copies of
            # self's final image
            extension = []
            for i in range(-diff):
                extension.append(self.figures[-1].copy())
            self.figures.extend(extension)
            tw = wrapper(self, other, t)
            self.figures = self.figures[:diff]
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

        tw = type(self)(figures)
        tw.defaultTween = self.defaultTween
        tw.transition = self.transition
        tw.static = self.static
        tw.delay = self.delay
        tw.visible = self.visible

        # The following handling of zdepth seems a little too
        # hard-coded.
        # It assumes you always want to linearly tween zdepth.
        # If you plan on using the Multi decorator more broadly,
        # you should consider reimplementing this.
        tw.zdepth = morpho.numTween(self.zdepth, other.zdepth, t)

        return tw

    return wrapper


# Text class that can support drawing multiple Text figures at once.
# Useful for having one text morph into another text.
#
# See "morpho.graphics.MultiImage" for more info on the basic idea here.
#
# Bottom line: It's just like Text except you can tween between different
# underlying text strings.
class MultiText(morpho.MultiFigure):
    def __init__(self, text="", *args, **kwargs):
        if isinstance(text, str):
            textlist = [Text(text, *args, **kwargs)]
        elif isinstance(text, list) or isinstance(text, tuple):
            textlist = [(Text(item, *args, **kwargs) if isinstance(item, str) else item) for item in text]
        elif isinstance(text, Text):
            textlist = [text]
        else:
            textlist = [Text(text, *args, **kwargs)]

        # Create frame figure
        super().__init__(textlist)

    @property
    def textlist(self):
        return self.figures

    @textlist.setter
    def textlist(self, value):
        self.figures = value

        # Convert every figure in the list to a Text figure
        # if possible.
        for n in range(len(self.figures)):
            fig = self.figures[n]
            if not isinstance(fig, Text):
                newfig = fig.images[0].copy()
                self.figures[n] = newfig

    def all(self):
        raise NotImplementedError
        if len(self.figures) == 0:
            raise IndexError("MultiText figure has no component Text figures.")

        tweenableNames = list(self.figures[0]._state)
        tweenableNames.extend(["text", "font", "bold", "italic"])
        figures = self.figures

        return super().all(tweenableNames, figures)


    ### TWEEN METHODS ###

    tweenLinear = Multi(Text.tweenLinear)
    tweenSpiral = Multi(Text.tweenSpiral)

    @classmethod
    def tweenPivot(cls, angle=tau/2, *args, **kwargs):
        return Multi(Text.tweenPivot(angle, *args, **kwargs),
            reverseMethod=Text.tweenPivot(-angle, *args, **kwargs)
            )




# DEPRECATED. Use "Text" instead.
class Text_old(morpho.Figure):
    def __init__(self, text=None, pos=complex(0),
        size=18, font="Times New Roman",
        bold=False, italic=False,
        anchor_x=-1, anchor_y=0,
        color=(1,1,1), alpha=1,
        physical=True):

        morpho.Figure.__init__(self)

        if text is None:
            text = []
        elif type(text) is str or isinstance(text, Number):
            text = [text]
        elif type(text) is tuple:
            text = list(text)
        elif type(text) is not list:
            raise TypeError("Unsupported text input")

        if type(color) is tuple:
            color = list(color)
        elif type(color) is not list:
            raise TypeError("Unsupported color input")

        # Take last three coords of color.
        color = list(color[:3])

        # Tack on zeros if len(color) < 4
        if len(color) < 3:
            color.extend([0]*(4-len(color)))

        # Turn position into complex
        if type(pos) in (list, tuple):
            pos = pos[0] + 1j*pos[1]

        # Create tweenables
        textlist = morpho.Tweenable("textlist", text, tags=["textlist", "nolinear", "nospiral"])
        pos = morpho.Tweenable("pos", pos, tags=["complex"])
        size = morpho.Tweenable("size", size, tags=["size"])
        _transform = morpho.Tweenable("_transform", np.identity(2), tags=["nparray"])
        color = morpho.Tweenable("color", color, tags=["color"])
        alpha = morpho.Tweenable("alpha", alpha, tags=["scalar"])
        self.update([textlist, pos, size, _transform, color, alpha])

        # Other attributes
        self.anchor_x = anchor_x
        self.anchor_y = anchor_y
        self.font = font
        self.bold = bold
        self.italic = italic
        self.physical = physical

        # self.defaultTween = Text.tweenLinear

    # Allows accessing the zeroth item of the textlist via
    # mytext.text
    @property
    def text(self):
        return self.textlist[0]

    # Allows modifying the zeroth item of the textlist via
    # mytext.text = "haha lolz"
    @text.setter
    def text(self, value):
        self.textlist[0] = value

    @property
    def transform(self):
        return self._transform

    @transform.setter
    def transform(self, value):
        self._transform = morpho.matrix.array(value)


    def copy(self):
        # Do a standard figure copy first
        new = morpho.Figure.copy(self)

        # Do a deep copy of the textlist
        for i in range(len(new.textlist)):
            item = new.textlist[i]
            if type(item) is Number:
                new.textlist[i] = item.copy()

        # Copy the non-tweenable attributes
        new.anchor_x = self.anchor_x
        new.anchor_y = self.anchor_y
        new.font = self.font
        new.bold = self.bold
        new.italic = self.italic
        new.physical = self.physical
        return new

    def draw(self, camera, ctx):
        # Do nothing if size less than 1.
        if self.size < 1:
            return

        view = camera.view

        # Compute literal text to draw
        textlist = []
        for item in self.textlist:
            textlist.append(str(item))

        text = "".join(textlist)

        # If the text is physical, position it in the complex plane,
        # else treat position as window pixel coordinates.
        if self.physical:
            x,y = morpho.anim.screenCoords(self.pos, view, ctx)
        else:
            x,y = self.pos.real, self.pos.imag

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
        xDummy, yDummy, textWidth, textHeight, dx, dy = ctx.text_extents(text)

        # Check if transformation matrix is too close to singular.
        # Specifically, is the area covered by the transformed text
        # smaller than a single pixel?
        if abs(np.linalg.det(self.transform)*textWidth*textHeight) < 1:
            return

        ctx.save()

        # ctx.translate(x,-y)
        # ctx.translate(0, 2*y)
        ctx.translate(x,y)

        # Apply transformation matrix if necessary
        if not np.array_equal(self.transform, np.identity(2)):
            # Define cairo matrix
            xx, xy, yx, yy = self.transform.flatten()
            mat = cairo.Matrix(xx, yx, xy, yy)

            # Apply to context
            ctx.transform(mat)

        # Handle alignment
        ctx.translate(-anchor_x*textWidth, -anchor_y*textHeight)

        ctx.scale(1,-1)

        # ctx.move_to(x-anchor_x*textWidth, y+anchor_y*textHeight)
        ctx.move_to(0,0)

        ctx.show_text(text)
        ctx.restore()
        ctx.new_path()

    ### TWEEN METHODS ###

    @morpho.TweenMethod
    def tweenLinear(self, other, t):
        # Tween all tweenables except the textlist
        txt = morpho.Figure.tweenLinear(self, other, t)
        # Don't tween the position if it is not physical
        if not self.physical:
            txt.pos = self.pos

        # Now handle the textlist
        for i in range(len(txt.textlist)):
            item = txt.textlist[i]
            if type(item) is not Number: continue

            self_Number = self.textlist[i]
            other_Number = other.textlist[i]

            txt.textlist[i] = self_Number.defaultTween(
                self_Number, other_Number, t)

        return txt

    @morpho.TweenMethod
    def tweenSpiral(self, other, t):
        # Tween all tweenables except the textlist
        txt = morpho.Figure.tweenSpiral(self, other, t)
        # Don't tween the position if it is not physical
        if not self.physical:
            txt.pos = self.pos

        # Now handle the textlist
        for i in range(len(txt.textlist)):
            item = txt.textlist[i]
            if type(item) is not Number: continue

            self_Number = self.textlist[i]
            other_Number = other.textlist[i]

            txt.textlist[i] = self_Number.defaultTween(
                self_Number, other_Number, t)

        return txt

    # @morpho.TweenMethod
    # def tweenLinearZoom(self, other, t):
    #     # Tween all tweenables except the textlist
    #     txt = morpho.Figure.tweenLinear(self, other, t)
    #     # Don't tween the position if it is not physical
    #     if not self.physical:
    #         txt.pos = self.pos

    #     # Now handle the textlist
    #     for i in range(len(txt.textlist)):
    #         item = txt.textlist[i]
    #         if type(item) is not Number: continue

    #         a = self.textlist[i].number
    #         b = other.textlist[i].number
    #         item.number = a*(b/a)**t

    #     return txt


# 3D version of the Text class.
#
# TWEENABLES that are not shared with Image
# orient = Orientation of text relative to text position (3x3 np.array).
#          Only used if "orientable" attribute is set to True.
#          Default: np.eye(3) meaning text is oriented flat on xy-plane facing
#          in the positive z direction.
#
# OTHER ATTRIBUTES
# orientable = Boolean specifying whether text should be orientable in 3D space,
#              or just behave like a label always facing the camera. Default: False
class SpaceText(Text):
    def __init__(self, text=None, pos=None,
        size=64, font=None,
        bold=False, italic=False,
        anchor_x=0, anchor_y=0,
        color=(1,1,1), alpha=1,
        background=(1,1,1), backAlpha=0, backPad=0):

        super().__init__(text, 0,
            size, font,
            bold, italic,
            anchor_x, anchor_y,
            color[:], alpha,
            background, backAlpha, backPad
            )

        if pos is None:
            pos = np.zeros(3)

        # Redefine pos tweenable to be 3D.
        _pos = morpho.Tweenable("_pos", morpho.matrix.array(pos), tags=["nparray", "fimage"])
        self._state.pop("pos")
        self._state["_pos"] = _pos
        _orient = morpho.Tweenable("_orient", np.identity(3), tags=["nparray", "orient"])
        self._state["_orient"] = _orient

        self.orientable = False

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

    def copy(self):
        new = super().copy()
        new.orientable = self.orientable
        return new


    def primitives(self, camera): # orient=np.identity(3), focus=np.zeros(3)):
        if self.alpha == 0:
            return []

        orient = camera.orient
        focus = camera.focus

        if np.allclose(focus, 0):
            pos3d = orient @ self.pos
        else:
            pos3d = orient @ (self.pos - focus) + focus

        txt = Text()
        txt.text = self.text
        txt.pos = (pos3d[0] + 1j*pos3d[1]).tolist()
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

        return [txt]


    def draw(self, camera, ctx): #, orient=np.identity(3), focus=np.zeros(3)):
        primlist = self.primitives(camera)
        if len(primlist) == 0:
            return
        txt = primlist[0]
        txt.draw(camera, ctx)

Spacetext = SpaceText  # Synonym

# Multi version of the SpaceText class.
# See "SpaceText" and "MultiText" for more info.
class SpaceMultiText(MultiText):
    def __init__(self, text="", *args, **kwargs):
        if isinstance(text, str):
            textlist = [SpaceText(text, *args, **kwargs)]
        elif isinstance(text, list) or isinstance(text, tuple):
            textlist = [(SpaceText(item, *args, **kwargs) if isinstance(item, str) else item) for item in text]
        else:
            textlist = [SpaceText(text, *args, **kwargs)]

        # Create frame figure
        super().__init__(textlist)

    def primitives(self, camera):
        primlist = []
        for fig in self.figures:
            primlist.extend(fig.primitives(camera))

        return primlist

    def draw(self, camera, ctx):
        for fig in self.primitives(camera):
            fig.draw(camera, ctx)


SpaceMultitext = Spacemultitext = SpaceMultiText  # Synonyms


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
        morpho.Figure.__init__(self)

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

# Takes a collection of Text figures and returns a MultiText figure
# that concatenates all the individual Text figures.
# This is basically a cheap and dirty way to implement something like
# a variable-style Text figure.
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
def group(textfigs, view, windowShape,
    pos=0, anchor_x=0, anchor_y=0, alpha=1, gap=0):
    # FUTURE: Perhaps allow for multi-line concatenations so something
    # like a Paragraph figure can be implemented.

    widths = []
    heights = []

    # Convert gap to physical units
    gap = morpho.physicalWidth(gap, view, windowShape)

    # Handle case that Frame figure is given
    if isinstance(textfigs, morpho.Frame):
        textfigs = textfigs.figures

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

        width, height = fig.dimensions(view, windowShape)
        widths.append(width)
        heights.append(height)
        totalWidth += width

    totalWidth += gap*(len(textfigs)-1)
    totalHeight = max(heights)
    totalxRadius = totalWidth/2
    totalyRadius = totalHeight/2
    curpos = pos-totalxRadius*(anchor_x+1) - 1j*totalyRadius*(anchor_y+1)

    for n, fig in enumerate(textfigs):
        # Make a copy of fig so to not affect the original
        fig = fig.copy()
        textfigs[n] = fig

        width = widths[n]
        height = heights[n]
        fig.pos = curpos + (fig.anchor_x+1)*width/2 + 1j*(fig.anchor_y+1)*height/2
        fig.alpha *= alpha
        curpos += width + gap

    return MultiText(textfigs)

