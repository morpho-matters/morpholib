
import morpholib as morpho
import morpholib.anim
from morpholib.tools.basics import *

import cairo
cr = cairo

import numpy as np

### CLASSES ###

# Draws a PNG image on the screen.
# Syntax: Image(source)
# where "source" can be a string defining a filepath or can be another
# Image figure (or a derivative figure) to use its internal PNG.
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
class Image(morpho.Figure):
    def __init__(self, source=None):

        morpho.Figure.__init__(self)

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

        # CCW rotation in radians
        rotation = morpho.Tweenable("rotation", 0, tags=["scalar"])
        # self.rotateBeforeScale = False

        # Transformation matrix to be applied last.
        # It is performed by treating the origin pixel as the origin of the
        # linear transformation.
        _transform = morpho.Tweenable("_transform", np.identity(2), tags=["nparray"])

        alpha = morpho.Tweenable("alpha", 1, tags=["scalar"])

        # Background box parameters
        background = morpho.Tweenable("background", [1,1,1], tags=["color"])
        backAlpha = morpho.Tweenable("backAlpha", 0, tags=["scalar"])
        backPad = morpho.Tweenable("backPad", 0, tags=["scalar"])

        # Initialize tweenables
        self.update([pos, align, _width, _height, scale_x, scale_y,
            rotation, _transform, alpha, background, backAlpha, backPad])

        # If set to True, changing the width or height will
        # automatically change the other to maintain the proportion.
        self.linked = True
        self.aspectRatioWH = self.width/self.height
        self.physical = True  # Are width and height in physical units, or pixel?

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
            self.imageSurface = cr.ImageSurface.create_from_png(source)
        elif isinstance(source, Image) or isinstance(source, MultiImage):
            self.imageSurface = source.imageSurface
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


    @property
    def transform(self):
        return self._transform

    @transform.setter
    def transform(self, value):
        self._transform = morpho.matrix.array(value)


    def copy(self):
        # Do standard figure copy first.
        # img = morpho.Figure.copy(self, self)
        img = super().copy(self)

        # Now copy the other parameters
        img.linked = self.linked
        img.aspectRatioWH = self.aspectRatioWH
        img.physical = self.physical

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

    # # Allows you to specify the origin using a scheme
    # # similar to the Text class's anchor scheme
    # def align(self, x=None, y=None):
    #     if x is not None:
    #         self.origin[0] = self.imageWidth*(x + 1)/2
    #     if y is not None:
    #         self.origin[1] = self.imageHeight*(y + 1)/2

    @property
    def imageOrigin(self):
        x,y = self.align
        return [self.imageWidth*(x+1)/2, self.imageHeight*(y+1)/2]

    @imageOrigin.setter
    def imageOrigin(self, value):
        X,Y = value
        self.align = [2*X/self.imageWidth-1, 2*Y/self.imageHeight-1]

    # Returns the bounding box (with possible padding) of the image
    # ignoring any transformations like rotation, transform, or scale
    # Also assumes the image has physical set to True.
    def box(self, pad=0):
        align_x, align_y = self.align
        # a = self.pos.real - self.scale_x*self.width/2*(align_x + 1)
        # b = a + self.scale_x*self.width
        # c = self.pos.imag - self.scale_y*self.height/2*(align_y + 1)
        # d = c + self.scale_y*self.height

        a = self.pos.real - self.width/2*(align_x + 1)
        b = a + self.width
        c = self.pos.imag - self.height/2*(align_y + 1)
        d = c + self.height

        return [a-pad, b+pad, c-pad, d+pad]

    # Same as box(), but the coordinates are relative to the image's
    # physical position.
    def relbox(self, pad=0):
        align_x, align_y = self.align
        a = -self.width/2*(align_x + 1)
        b = a + self.width
        c = -self.height/2*(align_y + 1)
        d = c + self.height

        return [a-pad, b+pad, c-pad, d+pad]

    # Returns the four corners of the image's bounding box
    # plus any optional padding. The sequence of the corners is
    # NW, SW, SE, NE.
    def corners(self, pad=0):
        a,b,c,d = self.box(pad)

        NW = a + d*1j
        SW = a + c*1j
        SE = b + c*1j
        NE = b + d*1j

        return [NW,SW,SE,NE]

    # Same as corners(), but the coordinates are relative to wherever
    # the image's physical position is.
    def relcorners(self, pad=0):
        a,b,c,d = self.relbox(pad)

        NW = a + d*1j
        SW = a + c*1j
        SE = b + c*1j
        NE = b + d*1j

        return [NW,SW,SE,NE]

    # Returns the visual centerpoint of the image, ignoring
    # the transformation attributes.
    @property
    def center(self):
        return mean(self.corners())

    @center.setter
    def center(self, value):
        center_x, center_y = value.real, value.imag
        align_x, align_y = self.align

        # Compute new position
        x = center_x + self.width*align_x/2
        y = center_y + self.height*align_y/2

        self.pos = complex(x,y)


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

        # Aspect ratio scale factors
        if self.physical:
            aspectScale_x = self.width/self.imageWidth * ctx.get_target().get_width() / view_width  #* self.scale_x
            aspectScale_y = self.height/self.imageHeight * ctx.get_target().get_height() / view_height  #* self.scale_y
        else:
            aspectScale_x = self.width/self.imageWidth
            aspectScale_y = self.height/self.imageHeight

        # Calculate total transformation matrix
        rot = cmath.exp(self.rotation*1j)  # Rotation factor
        xcol = rot*aspectScale_x
        ycol = rot*aspectScale_y*1j
        mat = self.transform @ np.array(
            [[self.scale_x*xcol.real, self.scale_x*ycol.real],
             [self.scale_y*xcol.imag, self.scale_y*ycol.imag]],
            dtype=float
            )

        # Check if the image has been distorted too thin.
        # Specifically, is the thinnest height of the parallelogram
        # it spans less then a pixel? If so, don't draw!
        areaMat = mat.copy()
        areaMat[:,0] *= self.imageWidth
        areaMat[:,1] *= self.imageHeight
        if morpho.matrix.thinHeight2x2(areaMat) < 1:
            return

        if self.backAlpha > 0:
            if not self.physical:
                # Temporarily change width and height to physical units
                # so that the bounding box is computed correctly.
                widthOrig = self.width
                heightOrig = self.height
                self._width *= view_width / ctx.get_target().get_width()
                self._height *= view_height / ctx.get_target().get_height()

            # Construct background rectangle and draw it
            box = self.relbox(pad=self.backPad)
            rect = morpho.grid.rect(box)
            rect.origin = self.pos
            rect.width = 0
            rect.fill = self.background
            rect.alpha = self.backAlpha*self.alpha
            rect.rotation = self.rotation

            # Calculate scaling matrices if non-identity
            transform = self.transform
            if self.scale_x != 1 or self.scale_y != 1:
                scaleMat = morpho.array([[self.scale_x,0], [0,self.scale_y]])
                transform = transform @ scaleMat

            rect.transform = transform
            rect.draw(camera, ctx)

            if not self.physical:
                # Restore original width and height
                self._width = widthOrig
                self._height = heightOrig

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
        _pos = morpho.Tweenable("_pos", np.zeros(3), tags=["nparray", "fimage"])
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
        a = self.pos[0] - self.scale_x*self.width/2*(align_x + 1)
        b = a + self.scale_x*self.width
        c = self.pos[1] - self.scale_y*self.height/2*(align_y + 1)
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

        img = Image(self)
        img.pos = (pos3d[0] + 1j*pos3d[1]).tolist()
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
# Optionally specify a method called "reverseMethod" which is used
# instead of the main method when the main method would have been
# called "in reverse" by calling imageMethod(other, self, 1-t).
# This was originally developed to solve the problem of decorating
# tweenPivot() because it is not symmetric in swapping
# self with other.
def Multi(imageMethod, reverseMethod=None):
    if reverseMethod is None:
        reverseMethod = imageMethod

    def wrapper(self, other, t, *args, **kwargs):
        # if len(self.images) != len(other.images):
        #     raise Exception("Tweening between multi-images of differing image counts is currently not supported.")

        diff = len(self.images) - len(other.images)
        if diff > 0:
            # Temporarily extend the image list of other with copies of
            # other's final image
            extension = []
            for i in range(diff):
                extension.append(other.images[-1].copy())
            other.images.extend(extension)
            tw = wrapper(self, other, t)
            # Restore other to its original state
            other.images = other.images[:-diff]
            return tw
        elif diff < 0:
            # Temporarily extend the image list of self with copies of
            # self's final image
            extension = []
            for i in range(-diff):
                extension.append(self.images[-1].copy())
            self.images.extend(extension)
            tw = wrapper(self, other, t)
            self.images = self.images[:diff]
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

        tw = type(self)(images)
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
class MultiImage(morpho.MultiFigure):

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

    def all(self):
        raise NotImplementedError
        if len(self.figures) == 0:
            raise IndexError("MultiImage has no component images.")

        tweenableNames = list(self.figures[0]._state)
        tweenableNames.extend(["width", "height"])
        figures = self.figures

        return super().all(tweenableNames, figures)


    # tween = morpho.Figure.tween

    ### TWEEN METHODS ###

    tweenLinear = Multi(Image.tweenLinear)
    tweenSpiral = Multi(Image.tweenSpiral)

    @classmethod
    def tweenPivot(cls, angle=tau/2, *args, **kwargs):
        return Multi(Image.tweenPivot(angle, *args, **kwargs),
            reverseMethod=Image.tweenPivot(-angle, *args, **kwargs)
            )

# Alternative name
MultImage = MultiImage


# Multi version of the SpaceImage class.
# See "SpaceImage" and "MultiImage" for more info.
class SpaceMultiImage(MultiImage):
    def __init__(self, source=None):
        if source is None:
            images = []
        elif isinstance(source, list) or isinstance(source, tuple):
            images = [(SpaceImage(item) if isinstance(item, str) else item) for item in source]
        else:
            images = [SpaceImage(source)]

        # Create frame figure
        super().__init__(images)

    def primitives(self, camera): # orient=np.identity(3), focus=np.zeros(3)):
        primlist = []
        for img in self.images:
            primlist.extend(img.primitives(camera))

        return primlist

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
