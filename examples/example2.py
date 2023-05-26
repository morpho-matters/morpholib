import morpholib as morpho
morpho.importAll()

from morpholib.tools.basics import *
from morpholib.video import *

import math, cmath

# morpho.transitions.default = morpho.transitions.quadease


def textEx():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    mytext = mainlayer.Actor(morpho.text.Text("Hello World").set(
        size=84,
        color=[1,0,0]
        ))

    mation.play()

def textMorph():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    message = mainlayer.Actor(morpho.text.MultiText("Hello World!"))
    # Over the course of a second, morph the text to say "Bye!"
    message.newendkey(30).set(text="Bye!")

    mation.play()

def imageMorph():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    mypic = mainlayer.Actor(morpho.graphics.MultiImage("./ball.png").set(
        width=3
        ))
    # Rescale height while leaving width unchanged
    mypic.newendkey(30).newSource("./oo.png").scaleByWidth()

    mation.play()

def arrowTest():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    pt = mainlayer.Actor(morpho.grid.Point(0))

    label = mainlayer.Actor(morpho.text.Text("Watch me carefully!").set(
        pos=pt.first().pos-3j,
        size=48,
        color=[1,0,0]
        ))

    arrow = mainlayer.Actor(morpho.grid.Arrow().set(
        headSize=0,    # Override default headSize of 25
        width=5,
        color=[1,1,1]  # Color it white
        ))
    arrow.first().tail = arrow.first().head = label.first().pos + 0.5j

    arrow.newendkey(30).set(
        head=pt.first().pos-0.5j,
        headSize=25
        )
    arrow.last().head = pt.first().pos - 0.5j
    arrow.last().headSize = 25

    mation.play()


def rectTest():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    myrect = mainlayer.Actor(morpho.grid.rect([-3,3, -1,2]).set(
        width=5,
        color=[1,0,0],
        fill=[1,1,0]
        ))

    mation.play()

def ellipseTest():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Ellipse centered at (2,1) with semi-width 3, and semi-height 1.
    myoval = mainlayer.Actor(morpho.grid.ellipse(2+1j, 3, 1))

    mation.play()

def arcTest():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Connect the point -2-1j to the point 3+2j with
    # an arc of angle pi/2 radians traveling counter-
    # clockwise from the first to the second point.
    myarc = mainlayer.Actor(morpho.grid.arc(-2-1j, 3+2j, pi/2))

    mation.play()

def gridTest():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Make a grid with thick, green horizontal lines
    # and 4 minor grid lines between every two major
    # lines. Also disable background grid and axes.
    mygrid = mainlayer.Actor(morpho.grid.mathgrid(
        view=[-3,3, -3,3],
        hcolor=[0,1,0], hwidth=5,
        hmidlines=4, vmidlines=4,
        BGgrid=False, axes=False
        ))

    mation.play()

def graphTest():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    f = lambda x: x**2
    fgraph = mainlayer.Actor(morpho.graph.realgraph(f, -2, 2))

    mation.play()

def graphTest2():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # This looks awful
    f1 = lambda x: 4*(1+math.sin(5*x))/2
    fgraph1 = mainlayer.Actor(morpho.graph.realgraph(f1, -4, 4))

    # This looks way better
    f2 = lambda x: 4*(-1+math.sin(5*x))/2
    fgraph2 = mainlayer.Actor(morpho.graph.realgraph(f2, -4, 4, steps=200))

    mation.play()

def graphTest3():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    f = lambda x: x**2
    # Make graph thick, red, and semi-transparent
    fgraph = mainlayer.Actor(morpho.graph.realgraph(f, -2, 2).set(
        width=10,
        color=[1,0,0],
        alpha=0.5
        ))

    mation.play()

def ellipseRotation():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    myoval = mainlayer.Actor(morpho.grid.ellipse(2+1j, 3, 1).set(
    rotation=2*pi/3
    ))

    mation.play()

def ellipseOrigin():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    myoval = mainlayer.Actor(morpho.grid.ellipse(0, 3, 1).set(
        origin=2+1j,
        rotation=2*pi/3
        ))

    mation.play()

def parallelogram():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Initialize the shape to be the unit square
    # and apply the linear transformation corresponding to the matrix
    # [[  1  1]
    #  [0.5  2]]
    shape = mainlayer.Actor(morpho.grid.rect([0,1,0,1]).set(
        transform=np.array([[1,1],[0.5,2]])
        ))
    shape.transform = np.array([[1,1],[0.5,2]])

    mation.play()

def commitExample():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Ellipse centered at (0,0) with semi-width 3,
    # and semi-height 1.
    myoval = mainlayer.Actor(morpho.grid.ellipse(0, 3, 1).set(
        origin=2+1j,
        rotation=2*pi/3
        ))
    print(myoval.first().origin, myoval.first().rotation)
    myoval.first().commitTransforms()
    print(myoval.first().origin, myoval.first().rotation)

    mation.play()

def rotationComparison():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    myoval = mainlayer.Actor(morpho.grid.ellipse(0, 3, 1))

    # Set rotation to pi radians after 1 second passes
    myoval.newendkey(30).set(rotation=pi)
    myoval.last().commitTransforms()

    mation.play()

def shearedBall():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    ball = mainlayer.Actor(morpho.graphics.Image("./ball.png").set(
        width=2,
        transform=np.array([[1,1],[0,1]])  # Shear the ball
        ))

    label = mainlayer.Actor(morpho.text.Text("sheared ball", pos=3j).set(
        transform=ball.first().transform  # Shear the label
        ))

    mation.play()

def ellipticalArcExample():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Initialize the arc centered at the point 1-2j,
    # with the semi-width and semi-height of the
    # containing arc being 2 and 3 respectively,
    # and having the portion of the elliptical curve
    # shown being the angle range from pi/2 to 7*pi/2.
    earc = mainlayer.Actor(morpho.shapes.EllipticalArc(
        pos=1-2j, xradius=2, yradius=3,
        theta0=pi/2, theta1=7*pi/6
        ))

    mation.play()

def pieExample():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    pie = mainlayer.Actor(morpho.shapes.Pie(
        pos=0, xradius=4, yradius=2, innerFactor=0.2,
        theta0=pi/2, theta1=11*pi/6,
        strokeWeight=5, color=[1,1,1], fill=[0,0.8,0.6]
        ))

    mation.play()

def pie2poly():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    pie = morpho.shapes.Pie(
        pos=0, xradius=4, yradius=2, innerFactor=0.2,
        theta0=pi/2, theta1=11*pi/6,
        strokeWeight=5, color=[1,1,1], fill=[0.8,0.3,0]
        )
    # By default, dTheta=5*deg, so this is twice as coarse
    poly = mainlayer.Actor(pie.toPolygon(dTheta=10*deg))

    mation.play()

def splineTest():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    spline = morpho.shapes.Spline()
    spline.newNode(-1-1j)

    # Set the last node's outhandle control point to be
    # located 1 unit above the latest node's position.
    spline.outhandle(-1, -1)          # These two actually
    spline.outhandleRel(-1, 1j)  # do the same thing

    spline.newNode(3+1j)
    spline.inhandleRel(-1, -1+1j)

    spline.newNode(-4j)
    spline.inhandleRel(-1, 1)

    # Make the handle control points visible by drawing
    # tangent line segments
    spline.showTangents = True

    # Turn into an actor so it can be viewed
    spline = mainlayer.Actor(spline)

    mation.play()

def crossoutTest():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Some text that's just begging to be crossed out
    mistake = mainlayer.Actor(morpho.text.Text("2 + 2 = 5"))

    # Generate an actor that does a crossout within
    # the specified box
    cross = mainlayer.Actor(morpho.gadgets.crossout(mistake.first().box(),
        pad=0.5, time=60, width=6, color=[1,1,0],
        transition=morpho.transitions.quadease
        ))

    mation.play()

def enboxTest():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Some sample text to enbox
    greeting = mainlayer.Actor(morpho.text.Text("Hello World!"))

    boxer = mainlayer.Actor(morpho.gadgets.enbox(greeting.first().box(),
        pad=0.5, time=20, width=4, color=[0,1,0],
        corner="NE",  # Start drawing from northeast corner
        CCW=False,  # Draw it in a clockwise direction
        transition=morpho.transitions.quadease
        ))

    mation.play()

def encircleTest():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    # Something worth encircling
    message = mainlayer.Actor(morpho.text.Text("Success!", color=[0.5,0.5,1]))

    encirc = mainlayer.Actor(morpho.gadgets.encircle(message.first().box(),
        pad=0.5, time=45, width=8, color=[0,1,0],
        phase=-pi/2, CCW=False,
        transition=morpho.transitions.quadease
        ))

    mation.play()

def imageBoxTest():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    ball = mainlayer.Actor(morpho.graphics.Image("./ball.png"))
    # Draw bounding box with 0.25 units of padding on all sides
    boxer = morpho.gadgets.enbox(ball.first().box(pad=0.25))

    mation.play()

def textBoxTest():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    mytext = mainlayer.Actor(morpho.text.Text("Hello World!"))

    # The default view and window dimensions of an
    # animation are [-5,5]x[-5j,5j] and 600x600 pixels.
    # Supply both of these to the box() method.
    boxer = mainlayer.Actor(morpho.gadgets.enbox(mytext.first().box(), pad=0.25))

    mation.play()


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
