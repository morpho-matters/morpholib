import morpholib as morpho
morpho.importAll()

from morpholib.tools.basics import *
from morpholib.video import *

import math, cmath

# morpho.transitions.default = morpho.transitions.quadease


def textEx():
    mytext = morpho.text.Text("Hello World")

    # mytext.text = "Goodbye!"
    mytext.size = 84
    mytext.color = [1,0,0]

    movie = morpho.Animation(mytext)
    movie.play()

def textMorph():
    message = morpho.text.MultiText("Hello World!")
    message = morpho.Actor(message)
    message.newendkey(30)         # Over the course of a second,
    message.last().text = "Bye!"  # morph the text to say "Bye!"

    movie = morpho.Animation(message)
    movie.play()

def imageMorph():
    mypic = morpho.graphics.MultiImage("./ball.png")
    mypic.width = 3
    mypic = morpho.Actor(mypic)
    mypic.newendkey(30)
    mypic.last().newSource("./oo.png")
    mypic.last().scaleByWidth()  # Rescale height while leaving width unchanged
    # mypic.last().scaleByHeight()  # Rescale width while leaving height unchanged

    movie = morpho.Animation(mypic)
    movie.play()


def arrowTest():
    pt = morpho.grid.Point(0)

    label = morpho.text.Text("Watch me carefully!", pos=pt.pos - 3j)
    label.size = 48
    label.color = [1,0,0]
    label.anchor_x = 0

    arrow = morpho.grid.Arrow()
    arrow.tail = arrow.head = label.pos + 0.5j
    arrow.headSize = 0  # Override default headSize of 25
    arrow.width = 5
    arrow.color = [1,1,1]  # Color it white

    arrow = morpho.Actor(arrow)
    arrow.newkey(30)  # New keyfigure at the 1 second mark
    arrow.last().head = pt.pos - 0.5j
    arrow.last().headSize = 25

    layer = morpho.Layer([pt, label, arrow])
    movie = morpho.Animation(layer)
    movie.play()

def rectTest():
    myrect = morpho.grid.rect([-3,3, -1,2])
    myrect.width = 5
    myrect.color = [1,0,0]
    myrect.fill = [1,1,0]

    movie = morpho.Animation(myrect)
    movie.play()

def ellipseTest():
    # Ellipse centered at (2,1) with semi-width 3,
    # and semi-height 1.
    myoval = morpho.grid.ellipse(2+1j, 3, 1)
    myoval.width = 5
    myoval.color = [0,0,1]
    myoval.fill = [0,0.6,0]

    movie = morpho.Animation(myoval)
    movie.play()

def arcTest():
    # Connect the point -2-1j to the point 3+2j with
    # an arc of angle pi/2 radians traveling counter-
    # clockwise from the first to the second point.
    myarc = morpho.grid.arc(-2-1j, 3+2j, pi/2)
    # myarc = morpho.grid.arc(3+2j, -2-1j, pi/2)   # Two ways to reverse
    # myarc = morpho.grid.arc(-2-1j, 3+2j, -pi/2)  # the arc's direction

    # Change style attributes
    myarc.width = 8
    myarc.color = [0,1,0]

    movie = morpho.Animation(myarc)
    movie.play()

def gridTest():
    # Make a grid with thick, green horizontal lines
    # and 4 minor grid lines between every two major
    # lines. Also disable background grid and axes.
    mygrid = morpho.grid.mathgrid(
        view=[-3,3, -3,3],
        hcolor=[0,1,0], hwidth=5,
        hmidlines=4, vmidlines=4,
        BGgrid=False, axes=False
        )

    movie = morpho.Animation(mygrid)
    movie.play()

def graphTest():
    f = lambda x: x**2
    fgraph = morpho.graph.realgraph(f, -2, 2)

    movie = morpho.Animation(fgraph)
    movie.play()

def graphTest2():
    # This looks awful
    f1 = lambda x: 4*(1+math.sin(5*x))/2
    fgraph1 = morpho.graph.realgraph(f1, -4, 4)

    # This looks way better
    f2 = lambda x: 4*(-1+math.sin(5*x))/2
    fgraph2 = morpho.graph.realgraph(f2, -4, 4, steps=200)

    movie = morpho.Animation(morpho.Layer([fgraph1, fgraph2]))
    movie.play()

def graphTest3():
    f = lambda x: x**2
    # Make graph thick, red, and semi-transparent
    fgraph = morpho.graph.realgraph(
        f, -2, 2, width=10, color=[1,0,0], alpha=0.5
        )

    movie = morpho.Animation(fgraph)
    movie.play()

def ellipseRotation():
    # Ellipse centered at (2,1) with semi-width 3,
    # and semi-height 1.
    myoval = morpho.grid.ellipse(2+1j, 3, 1)
    myoval.rotation = 2*pi/3

    movie = morpho.Animation(myoval)
    movie.play()

def ellipseOrigin():
    # Ellipse centered at (0,0) with semi-width 3,
    # and semi-height 1.
    myoval = morpho.grid.ellipse(0, 3, 1)
    myoval.origin = 2+1j
    myoval.rotation = 2*pi/3

    movie = morpho.Animation(myoval)
    movie.play()

def parallelogram():
    # Initialize the shape to be the unit square
    shape = morpho.grid.rect([0,1,0,1])
    # Apply the linear transformation corresponding to the matrix
    # [[  1  1]
    #  [0.5  2]]
    shape.transform = morpho.array([[1,1],[0.5,2]])

    movie = morpho.Animation(shape)
    movie.play()

def commitExample():
    # Ellipse centered at (0,0) with semi-width 3,
    # and semi-height 1.
    myoval = morpho.grid.ellipse(0, 3, 1)
    myoval.origin = 2+1j
    myoval.rotation = 2*pi/3
    print(myoval.origin, myoval.rotation)
    myoval.commitTransforms()
    print(myoval.origin, myoval.rotation)

    movie = morpho.Animation(myoval)
    movie.play()

def rotationComparison():
    myoval = morpho.grid.ellipse(0, 3, 1)

    # Turn into an actor so it can be animated
    myoval = morpho.Actor(myoval)

    # Set rotation to pi radians after 1 second passes
    myoval.newendkey(30)
    myoval.last().rotation = pi

    # Now commit the rotation
    myoval.last().commitTransforms()

    movie = morpho.Animation(myoval)
    movie.play()

def shearedBall():
    ball = morpho.graphics.Image("./ball.png")
    ball.width = 2
    # Shear the ball
    ball.transform = morpho.array([[1,1],[0,1]])

    label = morpho.text.Text("sheared ball", pos=3j)
    # Shear the label
    label.transform = ball.transform.copy()

    movie = morpho.Animation(morpho.Layer([ball, label]))
    movie.play()

def ellipticalArcExample():
    # Initialize the arc centered at the point 1-2j,
    # with the semi-width and semi-height of the
    # containing arc being 2 and 3 respectively,
    # and having the portion of the elliptical curve
    # shown being the angle range from pi/2 to 7*pi/2.
    earc = morpho.shapes.EllipticalArc(
        pos=1-2j, xradius=2, yradius=3,
        theta0=pi/2, theta1=7*pi/6
        )

    movie = morpho.Animation(earc)
    movie.play()

def pieExample():
    pie = morpho.shapes.Pie(
        pos=0, xradius=4, yradius=2, innerFactor=0.2,
        theta0=pi/2, theta1=11*pi/6,
        strokeWeight=5, color=[1,1,1], fill=[0,0.8,0.6]
        )

    movie = morpho.Animation(pie)
    movie.play()

def pie2poly():
    pie = morpho.shapes.Pie(
        pos=0, xradius=4, yradius=2, innerFactor=0.2,
        theta0=pi/2, theta1=11*pi/6,
        strokeWeight=5, color=[1,1,1], fill=[0.8,0.3,0]
        )
    # By default, dTheta=5, so this is twice as coarse
    poly = pie.toPolygon(dTheta=10)

    movie = morpho.Animation(poly)
    movie.play()

def splineTest():
    spline = morpho.shapes.Spline()
    spline.newNode(-1-1j)

    # Set the last node's outhandle control point to be
    # located 1 unit above the latest node's position.
    spline.outhandle(-1, -1)          # These two actually
    spline.outhandleRelative(-1, 1j)  # do the same thing

    spline.newNode(3+1j)
    spline.inhandleRelative(-1, -1+1j)

    spline.newNode(-4j)
    spline.inhandleRel(-1, 1)

    # Make the handle control points visible by drawing
    # tangent line segments
    spline.showTangents = True

    movie = morpho.Animation(spline)
    movie.play()

def crossoutTest():
    # Some text that's just begging to be crossed out
    mistake = morpho.text.Text("2 + 2 = 5")

    # Generate an actor that does a crossout within
    # the specified box
    cross = morpho.gadgets.crossout([-2,2, -1,1],
        time=60, width=6, color=[1,1,0],
        transition=morpho.transitions.quadease
        )

    movie = morpho.Animation(morpho.Layer([mistake, cross]))
    movie.play()

def enboxTest():
    # Some sample text to enbox
    greeting = morpho.text.Text("Hello World!")

    boxer = morpho.gadgets.enbox([-3,3, -1,1],
        time=20, width=4, color=[0,1,0],
        corner="NE",  # Start drawing from northeast corner
        CCW=False,  # Draw it in a clockwise direction
        transition=morpho.transitions.quadease,
        )

    movie = morpho.Animation(morpho.Layer([greeting, boxer]))
    movie.play()

def encircleTest():
    # Something worth encircling
    message = morpho.text.Text("Success!", color=[0.5,0.5,1])

    encirc = morpho.gadgets.encircle([-3,3, -1,1],
        time=45, width=8, color=[0,1,0],
        phase=-pi/2, CCW=False,
        # steps=20,  # A much coarser path
        transition=morpho.transitions.quadease
        )

    movie = morpho.Animation(morpho.Layer([message, encirc]))
    movie.play()

def imageBoxTest():
    ball = morpho.graphics.Image("./ball.png")
    # Draw bounding box with 0.25 units of padding on all sides
    boxer = morpho.gadgets.enbox(ball.box(pad=0.25))

    movie = morpho.Animation(morpho.Layer([ball, boxer]))
    movie.play()

def textBoxTest():
    mytext = morpho.text.Text("Hello World!")

    # The default view and window dimensions of an
    # animation are [-5,5]x[-5j,5j] and 600x600 pixels.
    # Supply both of these to the box() method.
    box = mytext.box([-5,5, -5,5], (600,600), pad=0.25)
    boxer = morpho.gadgets.enbox(box)

    movie = morpho.Animation(morpho.Layer([mytext, boxer]))
    movie.play()


# textEx()
# textMorph()
# imageMorph()
# arrowTest()
# rectTest()
# ellipseTest()
# arcTest()
# gridTest()
# graphTest()
# graphTest2()
# graphTest3()
# ellipseRotation()
# ellipseOrigin()
# parallelogram()
# commitExample()
# rotationComparison()
# shearedBall()
# ellipticalArcExample()
# pieExample()
# pie2poly()
# splineTest()
# crossoutTest()
# enboxTest()
# encircleTest()
# textBoxTest()
