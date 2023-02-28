'''
Contains code to facilitate parsing and rendering LaTeX.
Note that to use the functions in this module, you will
need to have LaTeX installed on your system.
'''

import os, io, hashlib

import morpholib as morpho
import morpholib.tools.latex2svg as latex2svg

# Import itself so that global names can be accessed
# from a local scope that uses the same names.
import morpholib.latex

template = latex2svg.default_template
preamble = latex2svg.default_preamble
params = latex2svg.default_params.copy()

# Directory in which to cache LaTeX code converted to SVG
# By default, it's None, meaning caching is disabled.
cacheDir = None

# Number of hex digits to use as part of the hash
cacheHashLength = 32

# Takes a string as input and returns a string
# which is the input string's SHA-256 hash expressed
# in hexadecimal notation.
# To convert to a standard integer, run the following:
#
# int(sha256(strng), 16)
#
# This function currently only accepts UTF-8 strings
# for input. Someday (probably when need arises) I'll
# generalize it for other kinds of input.
def sha256(strng):
    sha = hashlib.sha256()
    sha.update(bytes(strng, "utf-8"))
    return sha.hexdigest()

# Mainly for internal use.
# Takes LaTeX code and surrounds it with $$ if it
# doesn't already. These are needed for the LaTeX
# parser to work.
def _sanitizeTex(tex):
    tex = tex.strip()
    if not(tex.startswith("$$") and tex.endswith("$$")):
        tex = r"$$" + tex + r"$$"
    return tex

# Returns a filename for the given TeX code that can be
# used to cache the SVG the TeX code was converted into.
def hashTex(tex):
    texhash = sha256(tex)[:cacheHashLength]
    return f"tex-{texhash}.svg"

# Returns boolean on whether the given filename is
# in the current cache directory.
def iscached(tex):
    filename = hashTex(tex)
    return filename in os.listdir(cacheDir)

# Parses a string containing LaTeX code and returns a
# MultiSpline figure representing it.
#
# By default, the MultiSpline is positioned at 0, but this
# can be changed by passing in a complex number to the
# optional keyword argument `pos`.
#
# Optionally a `preamble` keyword argument can be specified.
# This is mainly to change which packages are imported when
# the LaTeX is parsed. If unspecified, the preamble will be
# taken from morpho.latex.preamble.
#
# If keyword argument `useCache` is set to False, the
# TeX cache will be skipped if one was defined.
#
# Any other args/kwargs will be passed into the MultiSpline
# fromsvg() constructor (e.g. boxWidth)
def parse(tex, *args,
    preamble=None, pos=0, useCache=True,
    **kwargs):

    tex = _sanitizeTex(tex)

    # Check if the SVG for this TeX code is cached
    if useCache and cacheDir is not None and iscached(tex):
        filepath = cacheDir + os.sep + hashTex(tex)
        spline = morpho.shapes.MultiSpline.fromsvg(filepath, *args, **kwargs)
        spline.origin = pos
        return spline

    if preamble is None:
        # Referencing the global scope `preamble` variable via
        # the module itself is required here since the local
        # variable and global variable have the same name.
        preamble = morpho.latex.preamble
    params = morpho.latex.params.copy()
    params["preamble"] = preamble

    out = latex2svg.latex2svg(tex, params)
    svgcode = out["svg"]

    # If caching is enabled, save the output svg code
    # as a file in the specified cache directory.
    if useCache and cacheDir is not None:
        filepath = cacheDir + os.sep + hashTex(tex)
        with open(filepath, "w") as file:
            file.write(svgcode)

    with io.StringIO() as stream:
        stream.write(svgcode)
        stream.seek(0)
        spline = morpho.shapes.MultiSpline.fromsvg(stream, *args, **kwargs)
    spline.origin = pos
    spline.all.backstroke = True
    return spline
