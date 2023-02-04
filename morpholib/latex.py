'''
Contains code to facilitate parsing and rendering LaTeX.
Note that to use the functions in this module, you will
need to have LaTeX installed on your system.
'''

import morpholib as morpho
import morpholib.tools.latex2svg as latex2svg

template = latex2svg.default_template
preamble = latex2svg.default_preamble
params = latex2svg.default_params.copy()

# Aliases allow them to be accessed from an inner scope
_preamble = preamble
_params = params

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
def tosvg(tex, *args, preamble=None, **kwargs):
    tex = _sanitizeTex(tex)
    if preamble is None:
        preamble = _preamble
    params = _params.copy()
    params["preamble"] = preamble

    out = latex2svg.latex2svg(tex, params)
    return morpho.shapes.MultiSpline.fromsvg(out["svg"], *args, **kwargs)
