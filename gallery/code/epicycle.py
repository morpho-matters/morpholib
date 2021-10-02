import morpholib as morpho
morpho.importAll()

from morpholib.tools.basics import *

import math, cmath


def epicycle():

    r0 = 2
    r1 = 1.5
    v0 = r0*1j  # *cmath.exp(30*deg*1j)
    w0 = tau/2
    v1 = r1*1j  # *cmath.exp(120*deg*1j)
    w1 = 5/3*w0
    class Epicycle(morpho.Skit):
        def makeFrame(self):
            t = self.t

            arrow0 = morpho.grid.Arrow(0, v0)
            arrow0.color = [0,1,0]
            arrow0.rotation = w0*t
            arrow0.commitTransforms()

            circ0 = morpho.shapes.Ellipse(
                pos=arrow0.tail, xradius=r0, yradius=r0,
                strokeWeight=1.5, color=arrow0.color,
                fillAlpha=0, alpha=0.5
                )

            arrow1 = morpho.grid.Arrow(0, v1)
            arrow1.color = [0,1,1]
            arrow1.rotation = w1*t
            arrow1.origin = arrow0.head
            arrow1.commitTransforms()

            circ1 = morpho.shapes.Ellipse(
                pos=arrow1.tail, xradius=r1, yradius=r1,
                strokeWeight=1.5, color=arrow1.color,
                fillAlpha=0, alpha=0.5
                )

            path = morpho.grid.line(0, t, steps=60*t)
            path = path.fimage(lambda t: v0*cmath.exp(w0*t*1j) + v1*cmath.exp(w1*t*1j))

            return morpho.Frame([circ0, circ1, path, arrow0, arrow1])

    ecycle = Epicycle()
    ecycle = morpho.Actor(ecycle)
    ecycle.newendkey(6*30).t = 6

    mation = morpho.Animation(ecycle)
    mation.play()

epicycle()
