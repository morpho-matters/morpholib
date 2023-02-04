
import morpholib as morpho
import morpholib.tools.latex2svg as latex2svg

template = latex2svg.default_template
preamble = latex2svg.default_preamble
params = latex2svg.default_params.copy()

# Aliases allow them to be accessed from an inner scope
_preamble = preamble
_params = params

def sanitizeTex(tex):
    tex = tex.strip()
    if r"\(" not in tex:
        tex = r"\(" + tex + r"\)"
    return tex

def tosvg(tex, *args, preamble=None, **kwargs):
    tex = sanitizeTex(tex)
    if preamble is None:
        preamble = _preamble
    params = _params.copy()
    params["preamble"] = preamble

    out = latex2svg.latex2svg(tex, params)
    return morpho.shapes.MultiSpline.fromsvg(out["svg"], *args, **kwargs)
