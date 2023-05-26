import morpholib as morpho
morpho.importAll()

from morpholib.tools.basics import *

import math, cmath


def tanline():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    f = lambda x: 0.2*(x**3 - 12*x)
    path = mainlayer.Actor(morpho.graph.realgraph(f, -4, 4))

    # Define a numerical derivative function
    dx = 0.000001  # A small change in x
    df = lambda x: (f(x+dx)-f(x-dx))/(2*dx)

    @morpho.SkitParameters(t=-4, length=4, alpha=1)
    class TangentLine(morpho.Skit):
        def makeFrame(self):
            # t will represent the input to the function f
            t = self.t
            length = self.length
            alpha = self.alpha

            # Initialize tangent line to be a horizontal
            # line segment of length 4 centered at the
            # origin
            line = morpho.grid.Path([-length/2, length/2])
            line.color = [1,0,0]  # Red color
            line.alpha = alpha

            # Compute derivative
            slope = df(t)
            # Convert into an angle and set it as the rotation
            # of the line segment
            angle = math.atan(slope)
            line.rotation = angle

            # Position the tangent line at the tangent point
            x = t
            y = f(t)
            line.origin = x + 1j*y

            # Create derivative tracker
            slopenum = morpho.text.formatNumber(slope, decimal=3, rightDigits=3)
            dlabel = morpho.text.Text("Slope = "+slopenum,
                pos=line.origin, anchor_y=-1,
                size=36, color=[1,1,0], alpha=alpha
                )
            dlabel.rotation = angle

            return morpho.Frame([line, dlabel])

    # Initialize the tangent line Skit
    tanline = mainlayer.Actor(TangentLine(t=-4, length=0))
    tanline.first().transition = morpho.transitions.quadease

    # Set t to +4 over the course of 5 seconds (150 frames)
    tanline.newendkey(150).set(t=4, length=4)

    # Finally, fade the tangent line to invisibility
    tanline.newendkey(30).alpha = 0

    mation.play()

tanline()
