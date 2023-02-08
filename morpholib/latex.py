'''
Contains code to facilitate parsing and rendering LaTeX.
Note that to use the functions in this module, you will
need to have LaTeX installed on your system.
'''

import morpholib as morpho
import morpholib.tools.latex2svg as latex2svg

# Import itself so that global names can be accessed
# from a local scope that uses the same names.
import morpholib.latex

template = latex2svg.default_template
preamble = latex2svg.default_preamble
params = latex2svg.default_params.copy()

# Default fill color to use for MultiSplines produced
# by parse(). None means use whatever natively pops
# out of the LaTeX to SVG converter (probably black).
fill = None

# Mainly for internal use.
# Takes LaTeX code and surrounds it with \( \) if it
# doesn't already. These are needed for the LaTeX
# parser to work.
def _sanitizeTex(tex):
    tex = tex.strip()
    if r"\(" not in tex:
        tex = r"\(" + tex + r"\)"
    return tex

# Parses a string containing LaTeX code and returns a
# MultiSpline figure representing it.
# Optionally a `preamble` keyword argument can be specified.
# This is mainly to change which packages are imported when
# the LaTeX is parsed. If unspecified, the preamble will be
# taken from morpho.latex.preamble.
#
# Any other args/kwargs will be passed into the MultiSpline
# constructor (e.g. boxWidth)
def parse(tex, *args, preamble=None, **kwargs):
    tex = _sanitizeTex(tex)
    if preamble is None:
        # Referencing the global scope `preamble` variable via
        # the module itself is required here since the local
        # variable and global variable have the same name.
        preamble = morpho.latex.preamble
    params = morpho.latex.params.copy()
    params["preamble"] = preamble

    out = latex2svg.latex2svg(tex, params)
    spline = morpho.shapes.MultiSpline.fromsvg(out["svg"], *args, **kwargs)
    if fill is not None:
        spline.all.fill = fill[:]
    return spline
