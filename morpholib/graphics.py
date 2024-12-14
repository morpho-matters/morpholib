
import morpholib as morpho
import morpholib.anim
import morpholib.color
import morpholib.grid
from morpholib.actions import wiggle
from morpholib.combo import TransformableFrame
from morpholib.tools.basics import *
from morpholib.tools.dev import BoundingBoxFigure, \
    BackgroundBoxFigure, PreAlignableFigure, Transformable2D

import cairo
cr = cairo

import numpy as np

I2 = np.identity(2)

### CLASSES ###

# Draws an image on the screen.
# Syntax: Image(source)
# where "source" can be a string defining a filepath or can be another
# Image figure (or a derivative figure) to use its internal image data.
# Source can be changed after construction by using the newSource()
# method.
#
# TWEENABLES
# pos = position (complex). Default: 0
# align = alignment (pair of numbers: [align_x, align_y]).
#         -1 = left or bottom aligned, 0 = center aligned, 1 = right or top aligned
#         Default: [0,0] (center alignment)
# width = Image width in physical units (unless physical = False). Default: 1
# height = Image height in physical units (unless physical = False).
# scale_x = Horizontal scale factor. Applies after rotation. Default: 1
# scale_y = Vertical scale factor. Applies after rotation. Default: 1
# rotation = Rotation in radians. Default: 0
# transform = Transformation matrix (applied relative to imageOrigin after
#             all else). Default: np.eye(2)
# alpha = Opacity. Default: 1 (opaque)
# background = Background box color. Default: [1,1,1] (white)
# backAlpha = Background box opacity. Default: 0 (transparent)
# backPad = Background box padding (physical units). Default: 0
#
# OTHER ATTRIBUTES
# linked = Boolean specifying whether width and height are linked via aspectRatioWH.
#          Default: True
# aspectRatioWH = Image aspect ratio. Mainly used only if linked = True.
#                 Equals self.width / self.height at any given moment.
#                 Generally only used under the hood.
# physical = Boolean on whether width and height are in physical units or pixels.
#            Default: True (physical units)
@Transformable2D(exclude="origin")
class Image(PreAlignableFigure):
    def __init__(self, source=None):

        # morpho.Figure.__init__(self)
        super().__init__()

        self.NonTweenable("imageSurface", None)

        self.newSource(source)

        # Position in the complex plane
        pos = morpho.Tweenable("pos", complex(0), tags=["complex"])
        # align specifies where the centerpoint of the image is.
        # [0,0] means center, [-1,-1] is bottom-left, [1,1] is top-right.
        align = morpho.Tweenable(
            name="align",
            value=[0,0],
            tags=["scalar", "list"]
            )

        # Width and height the image should take in physical units of
        # the complex plane.
        _width = morpho.Tweenable("_width", 1, tags=["scalar"])
        _height = morpho.Tweenable("_height", self.imageHeight/self.imageWidth, tags=["scalar"])

        # Scale factor in the horizontal and vertical directions.
        # Note these are NOT affected by the linked attribute.
        # Also note that these factors are applied AFTER rotation is;
        # scaling due to modifying width or height applies BEFORE rotation.
        scale_x = morpho.Tweenable("scale_x", 1, tags=["scalar"])
        scale_y = morpho.Tweenable("scale_y", 1, tags=["scalar"])

        alpha = morpho.Tweenable("alpha", 1, tags=["scalar"])

        # Background box parameters
        background = morpho.Tweenable("background", [1,1,1], tags=["color"])
        backAlpha = morpho.Tweenable("backAlpha", 0, tags=["scalar"])
        backPad = morpho.Tweenable("backPad", 0, tags=["scalar"])

        # Initialize tweenables
        self.update([pos, align, _width, _height, scale_x, scale_y,
            alpha, background, backAlpha, backPad])

        # If set to True, changing the width or height will
        # automatically change the other to maintain the proportion.
        self.NonTweenable("linked", True)
        self.NonTweenable("aspectRatioWH", self.width/self.height)
        self.NonTweenable("physical", True)  # Are width and height in physical units, or pixel?

    @property
    def origin(self):
        return self.pos

    @origin.setter
    def origin(self, value):
        self.pos = value

    # The "width" and "height" attrs are set up as properties,
    # because we may need to dynamically modify one in response
    # to a change in the other based on the "linked" attr.
    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        if self.linked:
            # self._height = value*self._height/self._width
            self._height = value/self.aspectRatioWH
        self._width = value

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        if self.linked:
            # self._width = value*self._width/self._height
            self._width = value*self.aspectRatioWH
        self._height = value

    @property
    def anchor_x(self):
        return self.align[0]

    @anchor_x.setter
    def anchor_x(self, value):
        align = list(self.align)
        align[0] = value
        self.align = align

    @property
    def anchor_y(self):
        return self.align[1]

    @anchor_y.setter
    def anchor_y(self, value):
        align = list(self.align)
        align[1] = value
        self.align = align



    # Restores the aspect ratio to normal. That is, recomputes it as
    # imageWidth/imageHeight for the current image.
    # Optionally specify view and windowShape that are disproportional,
    # and it will rescale the aspect ratio so that the image will look
    # undistorted despite that the viewbox and windowShape may not be
    # proportional.
    def rescaleAspectRatioWH(self, view=None, windowShape=None):
        self.aspectRatioWH = self.imageWidth / self.imageHeight
        if view is not None and windowShape is not None:
            self.aspectRatioWH /= morpho.pixelAspectRatioWH(view, windowShape)
        return self


    # Restores the aspect ratio to normal, keeping width fixed
    # and adjusting height. Optionally specify viewbox and windowShape
    # to rescale the aspect ratio so that the image looks normal even
    # if the viewbox and windowShape are not proportional to each other.
    def scaleByWidth(self, view=None, windowShape=None):
        # self.aspectRatioWH = self.imageWidth / self.imageHeight
        self.rescaleAspectRatioWH(view, windowShape)
        self._height = self.width/self.aspectRatioWH
        return self

    # Restores the aspect ratio to normal, keeping height fixed
    # and adjusting width. Optionally specify viewbox and windowShape
    # to rescale the aspect ratio so that the image looks normal even
    # if the viewbox and windowShape are not proportional to each other.
    def scaleByHeight(self, view=None, windowShape=None):
        # self.aspectRatioWH = self.imageWidth / self.imageHeight
        self.rescaleAspectRatioWH(view, windowShape)
        self._width = self.height*self.aspectRatioWH
        return self

    # Restores the aspect ratio to normal, keeping height fixed
    # and rescaling width. Optionally specify viewbox and windowShape
    # to rescale the aspect ratio so that the image looks normal even
    # if the viewbox and windowShape are not proportional to each other.
    def rescaleWidth(self, view=None, windowShape=None):
        self.scaleByHeight(view, windowShape)
        return self

    # Restores the aspect ratio to normal, keeping width fixed
    # and rescaling height. Optionally specify viewbox and windowShape
    # to rescale the aspect ratio so that the image looks normal even
    # if the viewbox and windowShape are not proportional to each other.
    def rescaleHeight(self, view=None, windowShape=None):
        self.scaleByWidth(view, windowShape)
        return self

    # Supply a new source to the image figure.
    # Aspect ratio and width and height will NOT be changed!
    # You need to call either scaleByWidth() or scaleByHeight()
    # after supplying a new source if you want to re-adjust them
    # so there is no distortion.
    def newSource(self, source):
        if source is None:
            self.imageSurface = None
        elif isinstance(source, str):
            source = source.strip()
            if source.lower().endswith("png"):
                self.imageSurface = cr.ImageSurface.create_from_png(source)
            else:
                # This is based on user Marwan Alsabbagh's code on StackOverflow.
                # https://stackoverflow.com/a/13457584
                from PIL import Image as PIL_Image
                from io import BytesIO
                with PIL_Image.open(source) as img, BytesIO() as buffer:
                    img.save(buffer, format="PNG")
                    buffer.seek(0)
                    self.imageSurface = cr.ImageSurface.create_from_png(buffer)
        elif isinstance(source, Image) or isinstance(source, MultiImageBase):
            self.imageSurface = source.imageSurface
        elif isinstance(source, cairo.ImageSurface):
            self.imageSurface = source
        else:
            raise TypeError("Unrecognized source for image!")

        # Save pixel width and height of the input image.
        if source is None:  # Dummy values if source is None
            self.imageWidth = 1
            self.imageHeight = 1
        else:
            self.imageWidth = self.imageSurface.get_width()
            self.imageHeight = self.imageSurface.get_height()

        return self

    # Returns both imageWidth and imageHeight as a tuple.
    @property
    def imageDimensions(self):
        return (self.imageWidth, self.imageHeight)


    def copy(self):

        # This is necessary because self needs to be passed
        # into the constructor in order for the pixel dimensions
        # to be correctly copied over!
        img = super().copy(self)

        return img

    # Sets the "linked" attr to True and updates the aspect ratio.
    def link(self):
        # Do nothing if already linked.
        if self.linked:
            return self

        self.linked = True
        if self.width == 0 or self.height == 0:
            raise ValueError("Can't link image with a zero width or height!")
        self.aspectRatioWH = self.width/self.height

        return self

    # Sets the "linked" attr to False
    def unlink(self):
        self.linked = False
        return self

    @property
    def imageOrigin(self):
        x,y = self.align
        return [self.imageWidth*(x+1)/2, self.imageHeight*(y+1)/2]

    @imageOrigin.setter
    def imageOrigin(self, value):
        X,Y = value
        self.align = [2*X/self.imageWidth-1, 2*Y/self.imageHeight-1]

    # Returns the bounding box (with possible padding) of the image.
    # If keyword `raw` is set to True, it will ignore `origin`,
    # `rotation`, `transform`, and `scale` attributes.
    # Also assumes the image has `physical` set to True.
    def box(self, *args, **kwargs):
        return self._boxFromRelbox(*args, **kwargs)

    # Same as box(), but the coordinates are relative to the image's
    # physical position.
    def relbox(self, pad=0, *, raw=False):
        align_x, align_y = self.align
        a = -self.width/2*(align_x + 1)
        b = a + self.width
        c = -self.height/2*(align_y + 1)
        d = c + self.height

        if not raw and not(self.rotation == 0 and self.scale_x == 1 and self.scale_y == 1 and np.array_equal(self._transform, I2)):
            transform = self._transform @ morpho.matrix.scale2d(self.scale_x, self.scale_y)
            return BoundingBoxFigure._transformedBox([a,b,c,d], 0, self.rotation, transform, pad)
        else:
            return [a-pad, b+pad, c-pad, d+pad]

    # Returns the four corners of the image's bounding box
    # plus any optional padding. The sequence of the corners is
    # NW, SW, SE, NE.
    def corners(self, *args, **kwargs):
        # NOTE: This method should actually be removable
        # since its behavior should be identical to the corners()
        # method inherited from BoundingBoxFigure.
        a,b,c,d = self.box(*args, **kwargs)

        NW = a + d*1j
        SW = a + c*1j
        SE = b + c*1j
        NE = b + d*1j

        return [NW,SW,SE,NE]


    # Same as corners(), but the coordinates are relative to wherever
    # the image's physical position is.
    def relcorners(self, *args, **kwargs):
        a,b,c,d = self.relbox(*args, **kwargs)

        NW = a + d*1j
        SW = a + c*1j
        SE = b + c*1j
        NE = b + d*1j

        return [NW,SW,SE,NE]

    # # Returns the visual centerpoint of the image, ignoring
    # # the transformation attributes.
    # @property
    # def center(self):
    #     return mean(self.corners())

    # @center.setter
    # def center(self, value):
    #     center_x, center_y = value.real, value.imag
    #     align_x, align_y = self.align

    #     # Compute new position
    #     x = center_x + self.width*align_x/2
    #     y = center_y + self.height*align_y/2

    #     self.pos = complex(x,y)


    def draw(self, camera, ctx):
        if self.imageSurface is None: return

        view = camera.view

        # # Don't try to render images whose dimensions
        # # are smaller than a pixel.
        # pxlWidth = abs(morpho.pixelWidth(self.width*self.scale_x, view, ctx))
        # pxlHeight = abs(morpho.pixelHeight(self.height*self.scale_y, view, ctx))
        # if pxlWidth < 1 or pxlHeight < 1: return

        # # If transform matrix results in an image whose pixel area is less
        # # than one pixel, don't draw.
        # if abs(np.linalg.det(self.transform))*pxlWidth*pxlHeight < 1: return

        # Pixel coordinates of position
        X,Y = morpho.anim.screenCoords(self.pos, view, ctx)

        # Compute proper scale factor for sprite draw command
        # so that we obtain the desired number of units per pixel.
        view_width = view[1] - view[0]
        view_height = view[3] - view[2]
        # self.sprite.scale_x = self.width/self.imageWidth * (window.width/view_width)
        # self.sprite.scale_y = self.height/self.imageHeight * (window.height/view_height)
        # self.sprite.scale_x *= self.scale_x
        # self.sprite.scale_y *= self.scale_y
        # self.sprite.opacity = int(255*self.alpha)

        # Aspect ratio scale factors.
        # A1 matrix converts the raw image box in its native
        # pixel space into physical box, and
        # A2 matrix converts the physical box the image takes up
        # into the actual pixel box the image will take up
        # on screen where it's rendered.
        # Thus when combined, they convert an image box in its
        # native pixel space, to a pixel box on the particular
        # viewing window.
        #
        # A1 should be applied BEFORE any transformations to
        # the physical image (e.g. rotations, scales, transforms)
        # and then A2 is applied AFTERWARD to handle final
        # physical-to-screenpixel rendering.
        if self.physical:
            # aspectScale_x = self.width/self.imageWidth * ctx.get_target().get_width() / view_width  #* self.scale_x
            # aspectScale_y = self.height/self.imageHeight * ctx.get_target().get_height() / view_height  #* self.scale_y
            a1_x = self.width/self.imageWidth
            a1_y = self.height/self.imageHeight
            a2_x = ctx.get_target().get_width() / view_width
            a2_y = ctx.get_target().get_height() / view_height

            A1 = np.array([[a1_x, 0], [0, a1_y]], dtype=float)
            A2 = np.array([[a2_x, 0], [0, a2_y]], dtype=float)
        else:
            aspectScale_x = self.width/self.imageWidth
            aspectScale_y = self.height/self.imageHeight
            A1 = np.array([[aspectScale_x, 0], [0, aspectScale_y]], dtype=float)
            A2 = I2

        # Calculate total transformation matrix
        # Rotation matrix
        s = math.sin(self.rotation)
        c = math.cos(self.rotation)
        R = np.array([[c, -s], [s, c]], dtype=float)
        # Scale matrix
        scale_xy = np.array([[self.scale_x, 0], [0, self.scale_y]], dtype=float)
        # Transform matrix
        T = self._transform
        premat = T @ scale_xy @ R
        # Aspect Ratio matrix
        # aspectScale = np.array([[aspectScale_x, 0], [0, aspectScale_y]], dtype=float)
        # Total transformation matrix
        # mat = aspectScale @ premat
        mat = A2 @ premat @ A1

        # # Calculate total transformation matrix
        # rot = cmath.exp(self.rotation*1j)  # Rotation factor
        # xcol = rot*aspectScale_x
        # ycol = rot*aspectScale_y*1j
        # mat = self.transform @ np.array(
        #     [[self.scale_x*xcol.real, self.scale_x*ycol.real],
        #      [self.scale_y*xcol.imag, self.scale_y*ycol.imag]],
        #     dtype=float
        #     )

        # Check if the image has been distorted too thin.
        # Specifically, is the thinnest height of the parallelogram
        # it spans less then a pixel? If so, don't draw!
        areaMat = mat.copy()
        areaMat[:,0] *= self.imageWidth
        areaMat[:,1] *= self.imageHeight
        if morpho.matrix.thinHeight2x2(areaMat) < 1:
            return

        if self.backAlpha > 0:
            # Construct background rectangle and draw it
            rectTransform = premat
            box = self.relbox(pad=self.backPad, raw=True)
            if not self.physical:
                w1 = morpho.physicalWidth(1, view, ctx)
                h1 = morpho.physicalHeight(1, view, ctx)
                a,b,c,d = box
                box = [a*w1, b*w1, c*h1, d*h1]

                # If in a non-square view, conjugate the premat
                par = morpho.pixelAspectRatioWH(view, ctx)
                if abs(par-1) > 1e-9:
                    rectTransform = morpho.parconj(par, transform=premat)

            rect = morpho.grid.rect(box)
            rect.origin = self.pos
            rect.width = 0
            rect.fill = self.background
            rect.alpha = self.backAlpha*self.alpha
            # rect.rotation = self.rotation

            # # Calculate scaling matrices if non-identity
            # transform = self.transform
            # if self.scale_x != 1 or self.scale_y != 1:
            #     scaleMat = morpho.array([[self.scale_x,0], [0,self.scale_y]])
            #     transform = transform @ scaleMat

            rect._transform = rectTransform
            rect.draw(camera, ctx)

        ctx.save()
        ctx.translate(X,Y)

        # # Apply transformation matrix if necessary
        # if not np.array_equal(self.transform, np.identity(2)):
        #     # Define cairo matrix
        #     xx, xy, yx, yy = self.transform.flatten().tolist()
        #     # Order is MATLAB-style: top-down, then left-right. So the matrix
        #     # specified below is:
        #     # [[xx  xy]
        #     #  [yx  yy]]
        #     mat = cairo.Matrix(xx, yx, xy, yy)

        #     # Apply to context
        #     ctx.transform(mat)

        # # Scale by the scale factor tweenables
        # ctx.scale(self.scale_x, self.scale_y)

        # # Perform rotation
        # ctx.rotate(self.rotation)

        # # Scale by aspect ratio scale factors
        # ctx.scale(aspectScale_x, aspectScale_y)

        # Define cairo matrix
        xx, xy, yx, yy = mat.flatten().tolist()
        # Order is MATLAB-style: top-down, then left-right. So the matrix
        # specified below is:
        # [[xx  xy]
        #  [yx  yy]]
        cairoMat = cairo.Matrix(xx, yx, xy, yy)
        # Apply to context
        ctx.transform(cairoMat)

        # if shouldRotate and not self.rotateBeforeScale:
        #     ctx.rotate(self.rotation)
        # ctx.scale(scale_x, scale_y)
        # if shouldRotate and self.rotateBeforeScale:
        #     ctx.rotate(self.rotation)
        # origin = self.origin
        ctx.translate(-self.imageOrigin[0], -self.imageOrigin[1])
        ctx.translate(0, self.imageHeight)
        ctx.scale(1,-1)
        # ctx.scale(scale_x, scale_y)
        # ctx.translate(x-self.origin[0]*scale_x, y-self.origin[1]*scale_y)
        # ctx.translate(x,y)
        ctx.set_source_surface(self.imageSurface)
        ctx.paint_with_alpha(self.alpha)
        ctx.restore()


        # # Set position in pixel space, adjusted by origin location.
        # self.sprite.position = \
        #     (x-self.origin[0]*self.sprite.scale_x,
        #         y-self.origin[1]*self.sprite.scale_y)

        # self.sprite.draw()


# Image class with winding number.
# NOT IMPLEMENTED! I believe this class's purpose has been obsoleted by
# the new "rotation" attribute of the Image class.
# I should probably just delete this class...
class ImagePolar(Image):
    def __init__(self, source):
        raise NotImplementedError
        Image.__init__(self, source)

        wind = morpho.Tweenable("wind", 0, tags=["integer", "winding number", "nolinear", "nospiral"])

        self.update(self.listState()+[wind])


# 3D version of the Image class.
#
# TWEENABLES that are not shared with Image
# orient = Orientation matrix relative to image origin.
#          Default: np.eye(3) meaning image is oriented flat on xy-plane facing
#          in the positive z direction.
#
# OTHER ATTRIBUTES
# orientable = Boolean specifying whether image should be orientable in 3D space,
#              or just behave like a label always facing the camera. Default: False
class SpaceImage(Image):
    def __init__(self, source=None):
        # Use superclass constructor
        super().__init__(source)

        # Redefine pos tweenable to be 3D.
        _pos = morpho.Tweenable("_pos", np.zeros(3), tags=["nparray", "fimage", "3d"])
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

        # self.pos = np.zeros(3)

    def copy(self):
        new = super().copy()
        new.orientable = self.orientable
        return new

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

    def box(self, pad=0):
        align_x, align_y = self.align
        a = self.pos[0].tolist() - self.scale_x*self.width/2*(align_x + 1)
        b = a + self.scale_x*self.width
        c = self.pos[1].tolist() - self.scale_y*self.height/2*(align_y + 1)
        d = c + self.scale_y*self.height

        return [a-pad, b+pad, c-pad, d+pad]

    def corners(self, pad=0):
        corners = super().relcorners(pad)
        # Convert to np.array and apply orientation matrix and translation
        corners = np.array([morpho.array(corner) for corner in corners], dtype=float)
        corners = self.pos + (corners @ self.orient.T)
        corners = list(corners)

        return corners

    def relcorners(self, pad=0):
        corners = super().relcorners(pad)
        # Convert to np.array and apply orientation matrix and translation
        corners = np.array([morpho.array(corner) for corner in corners], dtype=float)
        corners = (corners @ self.orient.T)
        corners = list(corners)

        return corners

    # Property is not supported for SpaceImages.
    @property
    def center(self):
        raise TypeError("`center` attribute not supported for SpaceImage.")

    @center.setter
    def center(self, value):
        # Throw error by attempting to access self.center
        self.center


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

        img = Image(self)
        img.pos = pos3d[0] + 1j*pos3d[1]
        img.zdepth = pos3d[2]
        img.align = self.align[:]
        img._width = self._width
        img._height = self._height
        img.scale_x = self.scale_x
        img.scale_y = self.scale_y
        img.rotation = self.rotation
        img.transform = self.transform
        if self.orientable:
            img.transform = (orient @ self.orient)[:2,:2] @ img.transform
        img.alpha = self.alpha
        img.background = self.background
        img.backAlpha = self.backAlpha
        img.backPad = self.backPad

        # img.rotateBeforeScale = self.rotateBeforeScale
        img.linked = self.linked
        img.aspectRatioWH = self.aspectRatioWH
        img.physical = self.physical

        img._updateSettings(self)

        return [img]


    def draw(self, camera, ctx): #, orient=np.identity(3), focus=np.zeros(3)):
        primlist = self.primitives(camera)
        if len(primlist) == 0:
            return
        img = primlist[0]
        img.draw(camera, ctx)

Spaceimage = SpaceImage  # Synonym for SpaceImage for people who hate camel case



# Decorator for tween methods in the MultiImage class below.
# Reworks ordinary Image class tween methods so that they work
# in a multi-image setting.
#
# `mainMethod` is the tween method that will be used to tween
# everything in the multiImage EXCEPT the subimage list.
# It should not act at all on the subimage list.
#
# Optionally specify a method called "reverseMethod" which is used
# instead of the main method when the main method would have been
# called "in reverse" by calling imageMethod(other, self, 1-t).
# This was originally developed to solve the problem of decorating
# tweenPivot() because it is not symmetric in swapping
# self with other.
def Multi(imageMethod, mainMethod=morpho.Figure.tweenLinear, *, reverseMethod=None):
    if reverseMethod is None:
        reverseMethod = imageMethod

    def wrapper(self, other, t, *args, **kwargs):
        # if len(self.images) != len(other.images):
        #     raise Exception("Tweening between multi-images of differing image counts is currently not supported.")

        diff = len(self.images) - len(other.images)
        if diff > 0:
            # Temporarily extend the image list of other with copies of
            # other's subimages
            orig_figures = other.images
            extension = []
            for i in range(diff):
                extension.append(other.images[i%len(other.images)].copy())
            other.images = extension + other.images
            tw = wrapper(self, other, t)
            # Restore other to its original state
            other.images = orig_figures
            return tw
        elif diff < 0:
            # Temporarily extend the image list of self with copies of
            # self's subimages
            orig_figures = self.images
            extension = []
            for i in range(-diff):
                extension.append(self.images[i%len(self.images)].copy())
            self.images = extension + self.images
            tw = wrapper(self, other, t)
            # Restore self to its original state
            self.images = orig_figures
            return tw

        images = []
        for n in range(len(self.images)):
            selfimg = self.images[n]
            otherimg = other.images[n]

            # If both underlying images are the same, don't do anything fancy.
            if selfimg.imageSurface == otherimg.imageSurface:
                new = imageMethod(selfimg, otherimg, t, *args, **kwargs)
                images.append(new)
            # Fade out self and fade in other
            else:
                selfimg1 = otherimg.copy()
                selfimg1.alpha = 0

                otherimg0 = selfimg.copy()
                otherimg0.alpha = 0

                newself = imageMethod(selfimg, selfimg1, t, *args, **kwargs)
                newother = reverseMethod(otherimg, otherimg0, 1-t, *args, **kwargs)

                images.append(newself)
                images.append(newother)

        # Remove temporary extensions
        if diff > 0:
            other.images = other.images[:-len(extensions)]
        elif diff < 0:
            self.images = self.images[:-len(extensions)]

        # Create final tweened multifigure object
        tw = mainMethod(self, other, t)
        tw.figures = images

        return tw

    return wrapper

# Method names in the Image class that return self when called.
# These will need to be modified in the MultiImage class to return
# the original calling MultiFigure.
selfmethods = ["rescaleAspectRatioWH", "scaleByWidth", "scaleByHeight",
    "rescaleWidth", "rescaleHeight", "newSource", "link", "unlink"]

@morpho.MultiFigure._modifyMethods(selfmethods, Image, morpho.MultiFigure._returnOrigCaller)
class MultiImageBase(morpho.MultiFigure):

    def __init__(self, source=None):
        if source is None:
            images = []
        elif isinstance(source, list) or isinstance(source, tuple):
            images = [(Image(item) if isinstance(item, str) else item) for item in source]
        else:
            images = [Image(source)]

        # Create frame figure
        super().__init__(images)

    @property
    def images(self):
        return self.figures

    @images.setter
    def images(self, value):
        self.figures = value

        # Convert every figure in the list to an Image figure
        # if possible.
        for n in range(len(self.figures)):
            fig = self.figures[n]
            if not isinstance(fig, Image):
                newfig = fig.images[0].copy()
                self.figures[n] = newfig

    # tween = morpho.Figure.tween

    ### TWEEN METHODS ###

    tweenLinear = Multi(Image.tweenLinear, mainMethod=morpho.Figure.tweenLinear)
    tweenSpiral = Multi(Image.tweenSpiral, mainMethod=morpho.Figure.tweenSpiral)

    @classmethod
    def tweenPivot(cls, angle=tau/2, *args, **kwargs):
        mainPivot = morpho.MultiFigure.tweenPivot(angle, *args, **kwargs)
        pivot = Multi(Image.tweenPivot(angle, *args, **kwargs),
            mainMethod=mainPivot,
            reverseMethod=Image.tweenPivot(-angle, *args, **kwargs)
            )
        # Enable splitting for this tween method
        pivot = morpho.pivotTweenMethod(cls.tweenPivot, angle)(pivot)

        return pivot

# Image class that can support drawing multiple images at once. Useful for having
# one image morph into another image.
#
# It can be used very similarly to the vanilla Image class. But in reality, it
# is internally more like a subclass of Frame. Contains at attribute called
# "images" which is a list of vanilla Image instances that should be drawn.
# However, attempting to access or modify an attribute that is NOT a part of
# MultiImage will cause it to attempt to access/modify the attribute as part of
# the first figure inside the "images" list. This allows you to syntactically treat
# MultiImage as if it is a single Image, because you will mostly just be modifying
# the first image in the "images" list.
#
# Bottom line: It's just like Image except you can tween between different
# underlying image files.
@TransformableFrame.modifyFadeActions
class MultiImage(MultiImageBase, TransformableFrame, PreAlignableFigure):
    @property
    def pos(self):
        return self.origin

    @pos.setter
    def pos(self, value):
        self.origin = value

# Alternative name
MultImage = MultiImage

MultiImage.action(wiggle)


# Multi version of the SpaceImage class.
# See "SpaceImage" and "MultiImage" for more info.
class SpaceMultiImage(MultiImageBase, morpho.SpaceFrame):
    def __init__(self, source=None):
        if source is None:
            images = []
        elif isinstance(source, list) or isinstance(source, tuple):
            images = [(SpaceImage(item) if isinstance(item, str) else item) for item in source]
        else:
            images = [SpaceImage(source)]

        # Create frame figure
        super().__init__(images)


    def draw(self, camera, ctx): #, orient=np.identity(3), focus=np.zeros(3)):
        for img in self.primitives(camera):
            img.draw(camera, ctx)


    # @property
    # def orient(self):
    #     return self.images[0].orient

    # @orient.setter
    # def orient(self, value):
    #     self.images[0].orient = value

    # @property
    # def orientable(self):
    #     return self.images[0].orientable

    # @orientable.setter
    # def orientable(self, value):
    #     self.images[0].orientable = value

SpaceMultimage = SpaceMultImage = SpaceMultiImage  # Synonyms


# A rectangular box of color specified with a numpy array.
# Note that this class should rarely be invoked directly.
# Use colorPattern() or morpho.graphics.heatmap() instead.
#
# TWEENABLES
# array = 3D array of shape (width x height x (3 or 4)) which
#         encodes RGB[A] data. Default: [[[1,1,1]]]
#         The color data can be either normalized RGB or RGBA,
#         but when tweening between multiple raster maps, the
#         scheme must be consistent!
# view = Box of the complex plane in which to draw the raster map.
#        Specified as [xmin,xmax,ymin,ymax]. Default: (0,1,0,1)
# alpha = Opacity. Default: 1 (opaque)
# origin = Translation value (complex number). Default: 0.
@Transformable2D
class RasterMap(BackgroundBoxFigure):
    def __init__(self, array=None, view=(0,1,0,1), alpha=1):
        if array is None:
            array = np.array([1,1,1]).reshape(1,1,3)
        # if view is None:
        #     view = [0,1,0,1]

        super().__init__()

        self.Tweenable("_array", morpho.array(array), tags=["nparray"])
        self.Tweenable("view", view, tags=["scalar", "list"])
        self.Tweenable("alpha", alpha, tags=["scalar"])


    @property
    def array(self):
        return self._array

    @array.setter
    def array(self, value):
        self._array = morpho.array(value)
        # self._updateSurface()

    def _createSurface(self):
        colorLength = self._array.shape[2]
        data = morpho.color.ARGB32(self._array.reshape(-1, colorLength))
        data.shape = self._array.shape[:2] + (-1,)

        return cairo.ImageSurface.create_for_data(
            data, cairo.FORMAT_ARGB32, data.shape[1], data.shape[0]
            )

    # Mainly for internal use by draw().
    # Creates a corresponding Image figure for the RasterMap
    # ready for drawing.
    #
    # If optional kwarg _forceZeroing=True, the corresponding
    # Image figure will be made to have its `pos` at 0.
    # This is mainly for use in making the Image more usable
    # outside of merely immediately drawing it, and is used
    # mainly by the toImage() method.
    def _createImage(self, *, _forceZeroing=False):
        surface = self._createSurface()
        img = Image(surface)
        img.unlink()
        img.align = [-1,-1]
        # center = mean([self.view[0]+self.view[2]*1j, self.view[1]+self.view[3]*1j])
        # img.pos = center + self.origin
        img.pos = self.view[0] + self.view[2]*1j + self.origin
        img.width = self.view[1] - self.view[0]
        img.height = self.view[3] - self.view[2]
        img.alpha = self.alpha

        # If non-trivial transformations are at play,
        # ensure the image is positioned at 0 so that transformations
        # are applied correctly.
        if _forceZeroing or not(self.rotation == 0 and np.array_equal(self._transform, I2)):
            img.placeOrigin(self.origin)
            img.set(
                rotation=self.rotation,
                _transform=self._transform,
                )
        img.set(
            background=self.background,
            backAlpha=self.backAlpha,
            backPad=self.backPad
            )

        return img

    # Returns an Image figure representation of the RasterMap.
    # The Image figure will be aligned such that its position
    # is at 0.
    def toImage(self):
        img = self._createImage(_forceZeroing=True)
        img._updateFrom(self, common=True)
        return img

    def box(self, *, raw=False):
        if raw:
            return self.view
        return morpho.grid.rect(self.view).box(raw=False)

    def draw(self, camera, ctx):
        img = self._createImage()
        img.draw(camera, ctx)

    # ### TWEEN METHODS ###

    # def tweenLinear(self, other, t, *args, **kwargs):
    #     tw = super().tweenLinear(other, t, *args, **kwargs)
    #     tw._updateSurface()
    #     return tw

    # def tweenSpiral(self, other, t, *args, **kwargs):
    #     tw = super().tweenSpiral(other, t, *args, **kwargs)
    #     tw._updateSurface()
    #     return tw

    # @classmethod
    # def tweenPivot(cls, angle=tau/2, *args, **kwargs):
    #     superpivot = super().tweenPivot(angle, *args, **kwargs)
    #     def pivot(self, other, t):
    #         tw = superpivot(self, other, t)
    #         tw._updateSurface()
    #         return tw
    #     return pivot

# Creates a RasterMap figure (i.e. box of color) via a
# color function that maps positions in the complex plane
# to RGB[A] colors.
#
# INPUTS
# colorfunc = Function that maps complex number positions
#             to normalized RGB[A] tuples. Although both RGB and
#             RGBA are supported, you must stick to a consistent
#             scheme if tweening between multiple color patterns.
# domain = Box of the complex plane on which to evaluate the
#          color function. Specified as [xmin,xmax,ymin,ymax].
#          Can also be a figure/actor in which case its bounding
#          box will be inferred if possible and used.
# res = Pixel resolution of the pattern (xres, yres).
#       Default: (100,100)
# alpha = Opacity. Default: 1 (opaque)
# KEYWORD-ONLY INPUTS
# view = Box of the complex plane on which to DRAW the color pattern.
#        By default, it's the same as the `domain` box.
# vectorized = Boolean indicating whether `colorfunc` should be
#       treated as vectorized. By default it's False, but if set to
#       True, it will input all of the complex number positions into
#       the color function all at once as one big complex-valued numpy
#       vector and will expect an output array of shape (N x (3 or 4))
#       where N is the element count of the massive input vector.
#       Using this option can potentially speed up creating the
#       color pattern.
def colorPattern(colorfunc, domain, res=(100,100), alpha=1,
    *, view=None, vectorized=False):

    domain = inferBox(domain)

    if view is None:
        view = domain[:]

    # Create position array
    zarray = morpho.matrix.positionArray(domain, res)
    # print(zarray.shape)
    # assert zarray.shape == res

    # Reorient the array because otherwise x- and y-directions
    # will be swapped and the top and bottom will be swapped.
    zarray = np.flip(zarray.T, axis=0)

    if vectorized:
        colorArray = colorfunc(zarray.reshape(-1))
        colorArray.shape = zarray.shape + (-1,)
    else:
        zlist = zarray.reshape(-1).tolist()
        colorDim = len(colorfunc(zlist[0]))
        # Initialize colorArray
        colorArray = np.zeros((len(zlist), colorDim))
        for n,z in enumerate(zlist):
            colorArray[n] = colorfunc(z)
        colorArray.shape = zarray.shape + (colorDim,)

    # Create RasterMap
    raster = RasterMap(colorArray, view, alpha)
    return raster

# Creates a color pattern of a heatmap.
# See also: colorPattern()
#
# INPUTS
# heatfunc = Function mapping complex positions to scalars.
# domain = Box of the complex plane on which to evaluate the
#          heatfunc. Specified as [xmin,xmax,ymin,ymax]
# interval = 2-tuple specifying the range of the heatfunc values
#            to color with the gradient.
# gradient = Color gradient to use for the heatmap.
#       Default: morpho.color.heatmap()
# res = Pixel resolution of the pattern (xres, yres).
#       Default: (100,100)
# alpha = Opacity. Default: 1 (opaque)
# KEYWORD-ONLY INPUTS
# view = Box of the complex plane on which to DRAW the color pattern.
#        By default, it's the same as the `domain` box.
# vectorized = Boolean indicating whether `heatfunc` should be
#       treated as vectorized. By default it's False, but if set to
#       True, it will input all of the complex number positions into
#       the heatmap all at once as one big complex-valued numpy
#       vector and will expect an output vector of the same length.
#       Using this option can potentially speed up creating the
#       heatmap.
def heatmap(heatfunc, domain, interval, gradient=None, res=(100,100), alpha=1,
    *, view=None, vectorized=False):

    if gradient is None:
        gradient = morpho.color.heatmap()

    low, high = interval

    if vectorized:
        def colorfunc(zlist):
            return gradient.value(morpho.lerp0(0, 1, heatfunc(zlist), start=low, end=high))
    else:
        def colorfunc(z):
            return gradient.value(morpho.lerp(0, 1, heatfunc(z), start=low, end=high))
    return colorPattern(colorfunc, domain, res, alpha, view=view, vectorized=vectorized)


