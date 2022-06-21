import morpholib as morpho
morpho.importAll()

from morpholib.tools.basics import *
from morpholib.video import *

import math, cmath

# morpho.transitions.default = morpho.transitions.quadease

def tracker():
    class Tracker(morpho.Skit):
        def makeFrame(self):
            # The t value is stored as a tweenable attribute
            # of the tracker itself. Let's extract it just
            # to simplify the later syntax.
            t = self.t

            # Create a "number" object based on the value t,
            # but auto-rounds it to the third decimal place
            # and always displays three digits to the right
            # of the decimal place, appending zeros if necessary.
            number = morpho.text.formatNumber(t, decimal=3, rightDigits=3)

            # The label's text is the stringified version of
            # the "number" object, which does the job of
            # rounding and appending trailing zeros for us.
            label = morpho.text.Text(number)

            return label

    # Construct an instance of our new Tracker Skit.
    # By default, t is initialized to t = 0.
    mytracker = Tracker()

    # Turn it into an actor, and have its t value progress
    # to the number 1 over the course of 2 seconds (60 frames)
    mytracker = morpho.Actor(mytracker)
    mytracker.newendkey(60)
    mytracker.last().t = 1

    movie = morpho.Animation(mytracker)
    movie.play()

def follower():
    # Create a curved path that begins at x = -4 and ends at x = +4
    path = morpho.graph.realgraph(lambda x: 0.2*(x**3 - 12*x), -4, 4)

    class Follower(morpho.Skit):
        def makeFrame(self):
            t = self.t

            # Create a generic Point figure
            point = morpho.grid.Point()
            # Set the position of the point to be the path's
            # position at parameter t.
            point.pos = path.positionAt(t)

            # Create Number objects out of the coordinates
            # to handle rounding and trailing zeros.
            x,y = point.pos.real, point.pos.imag
            xnum = morpho.text.formatNumber(x, decimal=2, rightDigits=2)
            ynum = morpho.text.formatNumber(y, decimal=2, rightDigits=2)

            # Create coordinate label
            label = morpho.text.Text(
                "("+xnum+", "+ynum+")",
                pos=point.pos, anchor_y=-1,
                size=36, color=[0,1,0]
                )
            # Anchor is +1 when t = 1, but -1 when t = 0
            label.anchor_x = morpho.lerp(-1, 1, t)

            return morpho.Frame([point, label])

    myfollower = Follower()
    # Set the follower to begin at the END of the path,
    # just to change things up a little.
    myfollower.t = 1

    # Turn it into an actor, and set its t value to be 0
    # after 2 seconds (60 frames) have passed.
    myfollower = morpho.Actor(myfollower)
    myfollower.newendkey(60)
    myfollower.last().t = 0

    # Include both the original path and the follower, so
    # we can clearly see that the follower is following the
    # intended path.
    movie = morpho.Animation(morpho.Layer([path, myfollower]))
    movie.play()

def imageFollower():
    # Create a curved path that begins at x = -4 and ends at x = +4
    path = morpho.graph.realgraph(lambda x: 0.2*(x**3 - 12*x), -4, 4)

    ballimage = morpho.graphics.Image("./ball.png")
    class Follower(morpho.Skit):
        def makeFrame(self):
            t = self.t

            # Create an Image figure from "ball.png"
            ball = morpho.graphics.Image(ballimage)
            ball.height = 0.75
            # Set the position of the image to be the path's
            # position at parameter t.
            ball.pos = path.positionAt(t)

            return ball

    myfollower = Follower()
    # Set the follower to begin at the END of the path,
    # just to change things up a little.
    myfollower.t = 1

    # Turn it into an actor, and set its t value to be 0
    # after 2 seconds (60 frames) have passed.
    myfollower = morpho.Actor(myfollower)
    myfollower.newendkey(60)
    myfollower.last().t = 0

    # Include both the original path and the follower, so
    # we can clearly see that the follower is following the
    # intended path.
    movie = morpho.Animation(morpho.Layer([path, myfollower]))
    movie.play()

def tanline():
    f = lambda x: 0.2*(x**3 - 12*x)
    path = morpho.graph.realgraph(f, -4, 4)

    # Define a numerical derivative function
    dx = 0.000001  # A small change in x
    df = lambda x: (f(x+dx)-f(x-dx))/(2*dx)

    @morpho.SkitParameters({"t":-4, "length":4, "alpha":1})
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
    tanline = TangentLine()
    tanline.t = -4  # Set initial t to -4
    tanline.length = 0  # Initial length is zero
    tanline.transition = morpho.transitions.quadease

    # Convert to actor and set t to +4 over
    # the course of 5 seconds (150 frames)
    tanline = morpho.Actor(tanline)
    tanline.newendkey(150)
    tanline.last().t = 4
    tanline.last().length = 4

    # Finally, fade the tangent line to invisibility
    tanline.newendkey(30)
    tanline.last().alpha = 0

    movie = morpho.Animation(morpho.Layer([path, tanline]))
    movie.play()

def pendulum():
    thetamax = pi/6  # Hard code thetamax for now
    length = 3  # Hard code pendulum string length for now
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

    pend = Pendulum()

    # Set internal time parameter t to be 6pi
    # after 5 seconds (150 frames) have passed
    # in the animation's clock.
    pend = morpho.Actor(pend)
    pend.newendkey(150).t = 6*pi

    movie = morpho.Animation(pend)
    movie.play()




# tracker()
# follower()
# tanline()
# imageFollower()
# pendulum()
