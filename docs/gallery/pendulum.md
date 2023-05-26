---
layout: default
title: Pendulum
---

<video controls loop style="width:100%; max-width:450px">
<source src="https://raw.githubusercontent.com/morpho-matters/morpholib/master/gallery/pendulum.mp4" type="video/mp4">
</video>

```python
import morpholib as morpho
morpho.importAll()

from morpholib.tools.basics import *

import math, cmath


def pendulum():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    thetamax = pi/6  # Hard code thetamax
    length = 3  # Hard code pendulum string length
    class Pendulum(morpho.Skit):
        def makeFrame(self):
            t = self.t

            theta = thetamax*math.sin(t)

            # Create pendulum string
            string = morpho.grid.Path([0, -length*1j])
            string.rotation = theta
            # Commit the rotation so that the string's
            # final node can be used to position the ball.
            string.commitTransforms()

            # Create the ball hanging on the string.
            # Its position is equal to the position of the
            # final node of the string path
            ball = morpho.grid.Point()
            ball.pos = string.seq[-1]
            ball.strokeWeight = string.width
            ball.color = [1,1,1]  # Ball border is white
            ball.size = 40  # Make it 40 pixels wide

            # Create neutral vertical dashed line
            neutral = morpho.grid.Path([0, -length*1j])
            neutral.dash = [10,10]

            # Create connecting arc
            arc = morpho.shapes.EllipticalArc(
                pos=0, xradius=1, yradius=1,
                theta0=-pi/2, theta1=-pi/2+theta,
                )

            # Create theta label
            thetaLabel = morpho.text.Text("\u03b8",  # Unicode for theta
                pos=1.5*cmath.exp(1j*mean([arc.theta0, arc.theta1])),
                size=min(36, 36*abs(theta/0.36)), italic=True
                )

            thetanum = morpho.text.formatNumber(theta*180/pi, decimal=0)
            tracker = morpho.text.Text(
                "\u03b8 = "+thetanum+"\u00b0",
                pos=1j, size=56
                )

            return morpho.Frame([neutral, arc, thetaLabel, string, ball, tracker])

    pend = mainlayer.Actor(Pendulum())

    # Set internal time parameter t to be 6pi after 5 seconds
    # (150 frames) have passed in the animation's clock.
    pend.newendkey(150).t = 6*pi

    mation.play()

pendulum()
```