from morpholib.base import *
from morpholib.figure import *
from morpholib.anim import Layer, Animation, Frame, SpaceFrame, Skit, SpaceSkit, SkitParameters, SpaceLayer, MultiFigure, SpaceMultiFigure
import morpholib.color as color
from morpholib.matrix import array
from morpholib.actions import action

from morpholib.tools.subimporter import import_submodules

def importAll():
    import_submodules(morpholib)
