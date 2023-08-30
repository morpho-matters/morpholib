from morpholib.base import *
from morpholib.figure import *
from morpholib.anim import Layer, Animation, Frame, SpaceFrame, \
    Skit, SpaceSkit, SkitParameters, SpaceLayer, MultiFigure, SpaceMultiFigure, \
    Camera, SpaceCamera
import morpholib.color as color
from morpholib.matrix import array
from morpholib.actions import action, subaction

from morpholib.tools.subimporter import import_submodules

def importAll():
    import_submodules(morpholib)
