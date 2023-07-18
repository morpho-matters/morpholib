'''
Contains classes useful for making composite figures.
'''

import morpholib as morpho
import morpholib.anim
from morpholib.anim import Frame, SpaceFrame, MultiFigure, SpaceMultiFigure, \
    SpaceMultifigure, Spacemultifigure
from morpholib import object_hasattr
from morpholib.tools.dev import listselect
from morpholib.tools.basics import *

import math, cmath
import numpy as np


# A Frame of figures that can be accessed with array index syntax.
# Normally this class is instantiated by calling figureGrid()
class FigureArray(Frame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.NonTweenable("_shape", (1, len(self.figures)))

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, value):
        try:
            array = np.array(self.figures, dtype=object)
            array.shape = value
        except ValueError:
            raise ValueError(f"Cannot arrange {len(self.figures)} subfigures into shape {value}.")
        self._shape = array.shape

    @property
    def figureArray(self):
        array = np.array(self.figures, dtype=object)
        array.shape = self.shape
        return array

    @figureArray.setter
    def figureArray(self, value):
        if not isinstance(value, np.ndarray):
            value = np.array(value, dtype=object)
        self.figures = value.reshape(-1).tolist()
        self.shape = value.shape

    # Update the positions of subfigures IN-PLACE to arrange them
    # in a grid. See figureGrid() for more info.
    def updatePositions(self, *, pos=0, align=(0,0), width=None, height=None):
        nrows, ncols = self.shape  # Don't use `shape` directly cuz it could have negatives
        anchor_x, anchor_y = align

        if width is None and height is None:
            raise ValueError("At least one of width or height must be specified.")
        elif width is None:
            width = ncols/nrows * height
        elif height is None:
            height = nrows/ncols * width

        xmin = pos.real - (anchor_x+1)/2*width if ncols > 1 else pos.real
        ymax = pos.imag - (anchor_y-1)/2*height if nrows > 1 else pos.imag

        dx = width/(ncols-1) if ncols > 1 else width
        dy = height/(nrows-1) if nrows > 1 else height

        figarray = self.figureArray
        posnames = ["pos", "_pos", "origin", "_origin"]
        for i in range(nrows):
            for j in range(ncols):
                subfig = figarray[i,j]
                # Find usable toplevel positional tweenable
                for posname in posnames:
                    if posname in subfig._state:
                        break
                    # Set posname to None so that if we escape the loop without
                    # finding a suitable positional tweenable, we can throw
                    # an error!
                    posname = None
                if posname is None:
                    raise AttributeError("Some subfigures do not possess toplevel positional tweenables.")
                setattr(subfig, posname, complex(xmin + j*dx, ymax - i*dy))
        return self

    def _select(self, index, *, _asFrame=False, _iall=False):
        if not(isinstance(index, tuple) and len(index) == 2):
            raise IndexError("Given index must be a pair (row, col).")

        rowSlice, colSlice = index
        figarray = self.figureArray
        # Extract the selected individual row and column indices
        rowIndices = list(listselect(figarray, rowSlice).keys())
        colIndices = list(listselect(figarray.T, colSlice).keys())
        # Convert into indices in the 1D figure list
        nrows, ncols = self.shape
        selection = tuple(i*ncols + j for i in rowIndices for j in colIndices)
        if _asFrame:
            frm = Frame._select(self, selection, _asFrame=True)
            frm.shape = (len(rowIndices), len(colIndices))
            return frm
        else:
            return Frame._select(self, selection, _iall=_iall)


# Returns a FigureArray of the given figures.
#
# INPUTS
# figures = List of figures to combine into a FigureArray.
#           If given a figure object (not as part of a list),
#           it will make copies of the figure to create an
#           array of the given shape.
# KEYWORD-ONLY INPUTS
# shape = Tuple specifying the shape of the grid (rows, cols)
#         Like in numpy, negative values can be supplied to
#         infer a missing dimension. Default: (1,-1) a single row.
# pos = Position of the grid as a complex number. Default: 0 (origin)
# align = Alignment of the grid with respect to the `pos` value.
#         Default: (0,0) (center alignment)
# width, height = Width and height of the grid. If one is unspecified,
#   it will be inferred from the other and the grid shape. However,
#   at least one of width or height must be specified.
def figureGrid(figures, *,
        shape=(1,-1),
        pos=0, align=(0,0),
        width=None, height=None):

    if len(shape) != 2:
        raise TypeError("Given shape must be a pair (nrows, ncols).")

    if isinstance(figures, morpho.Figure):
        figure = figures
        figures = [figure.copy() for n in range(abs(shape[0]*shape[1]))]
        figgrid = FigureArray(figures)
    elif isinstance(figures, dict):
        figgrid = FigureArray(**figures)
    else:
        figgrid = FigureArray(figures)

    figgrid.shape = shape

    figgrid.updatePositions(pos=pos, align=align, width=width, height=height)
    return figgrid
