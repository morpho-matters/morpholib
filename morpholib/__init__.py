from morpholib.base import *
from morpholib.figure import *
from morpholib.anim import Layer, Animation, Frame, SpaceFrame, Skit, SpaceSkit, SkitParameters, SpaceLayer, MultiFigure, SpaceMultiFigure
import morpholib.tools.color as color
from morpholib.matrix import array

from morpholib.tools.subimporter import import_submodules

def importAll():
    import_submodules(morpholib)
