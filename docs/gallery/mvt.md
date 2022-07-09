---
layout: default
title: Mean Value Theorem
---

<video controls loop style="width:100%; max-width:600px">
<source src="https://raw.githubusercontent.com/morpho-matters/morpholib/master/gallery/mvt.mp4" type="video/mp4">
</video>

```python
import morpholib as morpho
mo = morpho
morpho.importAll()

import math, cmath, random
import numpy as np

from morpholib.tools.basics import *
from morpholib.video import standardAnimation, ratioXY, std_view
from morpholib.tools.color import colormap

morpho.transition.default = morpho.transition.quadease

uniform = morpho.transitions.uniform
quadease = morpho.transitions.quadease
sineease = sinease = morpho.transition.sineease

exportDir = "./"

# Returns a film with some standard axes.
def makeAxes():
    axes = morpho.graph.Axes([-100,100, -100,100],
        xwidth=10, ywidth=10,
        xalpha=1, yalpha=1
        )
    # axes.zdepth = 1000
    axes = morpho.Actor(axes)
    return axes

def mvt():
    axes = makeAxes()

    mation = morpho.video.standardAnimation(axes)
    mainlayer = mation.layers[0]
    mainlayer.camera.first().centerAt(14+7j)

    mation.endDelay()

    a = 6
    b = 25
    tickHeight = 1

    ticka = morpho.grid.Arrow(
        a-tickHeight/2*1j, a+tickHeight/2*1j,
        width=5, headSize=0, color=[0,0,0]
        )
    ticka = morpho.Actor(ticka)
    ticka.newkey(15)
    ticka.first().head = ticka.first().tail
    mainlayer.merge(ticka)

    tickb = morpho.grid.Arrow(
        b-tickHeight/2*1j, b+tickHeight/2*1j,
        width=5, headSize=0, color=[0,0,0]
        )
    tickb = morpho.Actor(tickb)
    tickb.newkey(15)
    tickb.first().head = tickb.first().tail
    mainlayer.append(tickb)

    # Labels
    textHeight = 1.25*tickHeight
    time = mainlayer.lastID()
    labela = morpho.text.Text("a", pos=a, color=[0,0,0], size=64, anchor_x=0, italic=True, alpha=0)
    labela = morpho.Actor(labela)
    labela.newkey(15)
    labela.last().alpha = 1
    labela.last().pos -= textHeight*1j
    mainlayer.merge(labela, atFrame=time)

    labelb = labela.copy()
    for fig in labelb.keys():
        fig.text = "b"
        fig.pos += b-a
    mainlayer.merge(labelb)

    mation.endDelay(15)

    c = 18
    w = 12.5
    h = 12
    f = lambda x: h*math.sqrt(1-(x-c)**2/w**2)
    graph = mo.graph.realgraph(f,a,b, steps=100, width=7, color=[0,0,1])

    graph = morpho.Actor(graph)
    graph.newkey(30)
    graph.first().end = 0
    mainlayer.append(graph)

    # y ticks
    tickfa = morpho.grid.Arrow(
        1j*f(a)-tickHeight/2, 1j*f(a)+tickHeight/2,
        width=5, headSize=0, color=[0,0,0]
        )
    tickfa = morpho.Actor(tickfa)
    tickfa.newkey(15)
    tickfa.first().head = tickfa.first().tail
    mainlayer.append(tickfa)

    time = mation.lastID()
    linea = mo.grid.Arrow(
        f(a)*1j, a+f(a)*1j, color=[0,0,0], width=5,
        headSize=0
        )
    linea.dash = [10]
    linea.zdepth = -1
    linea = mo.Actor(linea)
    linea.newendkey(20)
    linea.first().head = linea.first().tail
    mainlayer.merge(linea, atFrame=time)

    tickfb = morpho.grid.Arrow(
        1j*f(b)-tickHeight/2, 1j*f(b)+tickHeight/2,
        width=5, headSize=0, color=[0,0,0]
        )
    tickfb = morpho.Actor(tickfb)
    tickfb.newkey(15)
    tickfb.first().head = tickfb.first().tail
    mainlayer.merge(tickfb, atFrame=time)

    lineb = mo.grid.Arrow(
        f(b)*1j, b+f(b)*1j, color=[0,0,0], width=5,
        headSize=0
        )
    lineb.dash = [10]
    lineb.zdepth = -1
    lineb = mo.Actor(lineb)
    lineb.newendkey(20)
    lineb.first().head = lineb.first().tail
    mainlayer.append(lineb)

    time = mainlayer.lastID()
    # textHeight *= 1.5
    labelfa = morpho.text.Text("f(a)", pos=f(a)*1j, color=[0,0,0], size=64, anchor_x=0, italic=True, alpha=0)
    labelfa = morpho.Actor(labelfa)
    labelfa.newkey(15)
    labelfa.last().alpha = 1
    labelfa.last().pos -= textHeight*1.5
    mainlayer.merge(labelfa, atFrame=time)

    labelfb = morpho.text.Text("f(b)", pos=f(b)*1j, color=[0,0,0], size=64, anchor_x=0, italic=True, alpha=0)
    labelfb = morpho.Actor(labelfb)
    labelfb.newkey(15)
    labelfb.last().alpha = 1
    labelfb.last().pos -= textHeight*1.5
    mainlayer.merge(labelfb, atFrame=time)

    mation.endDelay()

    time = mation.lastID()
    pta = mo.grid.Point(a+f(a)*1j, strokeWeight=3, size=20, alpha=0)
    pta = mo.Actor(pta)
    pta.newkey(15).alpha = 1
    mainlayer.merge(pta, atFrame=time)

    ptb = pta.copy()
    for fig in ptb.keys():
        fig.pos = b+f(b)*1j
    mainlayer.merge(ptb)

    xmin = -4
    xmax = 32
    m = (f(b)-f(a))/(b-a)
    L = lambda x: m*(x-a) + f(a)
    secline = mo.graph.realgraph(L,xmin,xmax, steps=1, width=7,
        color=mo.color.colormap["green"]
        )
    secline.zdepth = -1
    secline.end = 0
    secline = mo.Actor(secline)
    secline.newkey(30)
    secline.last().end = 1
    mainlayer.append(secline)

    mation.endDelay(15)

    # Secant formula
    secslope = mo.graphics.Image("./resources/secslope.png")
    secslope.pos = 16.5 + 7j
    secslope.align = [0,0]
    secslope.height = 0
    secslope.zdepth = 10
    # secslope.alpha = 0

    secslope = mo.Actor(secslope)
    secslope.newendkey(20)
    secslope.last().pos = a+5 + 2j
    secslope.last().height = 2
    # secslope.last().alpha = 1
    mainlayer.append(secslope)

    mation.endDelay()

    dx = 0.00001
    deriv = lambda f: (lambda x: (f(x+dx) - f(x-dx))/(2*dx))
    df = deriv(f)
    dfcImg = morpho.graphics.Image("./resources/df.png")
    @morpho.SkitParameters({
        "f":f, "df":df, "x":a+dx, "radius":5, "ptalpha":1, "alpha":1,
        "start":0, "end":1
        })
    class Tanline(morpho.Skit):
        def makeFrame(self):
            x = self.x
            radius = self.radius
            ptalpha = self.ptalpha
            alpha = self.alpha
            f = self.f
            df = self.df

            m = df(x)
            y = f(x)
            T = lambda t: m*(t-x)+y
            xrad = radius/math.sqrt(1+m**2)
            tanline = mo.graph.realgraph(T, x-xrad, x+xrad, steps=1,
                color=[0,0,0], width=7, alpha=alpha
                )
            tanline.start = self.start
            tanline.end = self.end

            pt = mo.grid.Point(x+y*1j, strokeWeight=3,
                fill=mo.color.colormap["violet"], alpha=alpha*ptalpha, size=20
                )

            dfc = mo.graphics.Image(dfcImg)
            dfc.pos = pt.pos + 4j
            dfc.height = 1
            dfc.alpha = ptalpha*alpha

            arrow = mo.grid.Arrow(dfc.pos-0.75j, pt.pos+0.75j,
                width=5, color=mo.color.colormap["violet"],
                alpha=ptalpha*alpha
                )

            vert = mo.grid.Arrow(x, pt.pos,
                color=[0,0,0], alpha=ptalpha*alpha, width=5, headSize=0
                )
            vert.dash = [10]
            vert.zdepth = -1

            tickc = morpho.grid.Arrow(
                x-tickHeight/2*1j, x+tickHeight/2*1j,
                width=5, headSize=0, alpha=ptalpha*alpha, color=[0,0,0]
                )

            labelc = morpho.text.Text(
                "c", pos=x-1j*textHeight, color=mo.color.colormap["violet"], size=64,
                anchor_x=0, italic=True, alpha=ptalpha*alpha
                )

            return mo.Frame([tanline, pt, arrow, vert, tickc, labelc, dfc])

    tanline = Tanline()
    tanline.zdepth = 1
    tanline.x = a+2
    tanline.end = 0
    tanline.ptalpha = 0

    tanline = morpho.Actor(tanline)
    mainlayer.append(tanline)

    tanline.newendkey(20)
    tanline.last().end = 1
    tanline.last().ptalpha = 1

    mation.endDelay()

    tanline.newendkey(60).x = b-2
    tanline.newendkey(60).x = a+4
    tanline.newendkey(45).x = 13.757  # First MVT point

    mation.endDelay()

    # Assert parallel
    tline = tanline.last().makeFrame().figures[0]
    tline.zdepth = -0.5
    tline = mo.Actor(tline)
    mainlayer.append(tline)

    tline.newendkey(20)
    for n in range(2):
        z = tline.last().seq[n]
        tline.last().seq[n] = z.real + 1j*(L(z.real)+0.25)

    mation.endDelay()

    tline.newendkey(20, tline.first().copy())
    tline.last().visible = False

    mation.endDelay()

    # Construct equation
    time = mation.lastID()
    dfc = tanline.last().makeFrame().figures[-1]
    dfc.zdepth = 10
    dfc = mo.Actor(dfc)
    dfc.newendkey(30)
    dfc.last().pos = secslope.last().pos + secslope.last().width
    mainlayer.merge(dfc, atFrame=time)

    eq = mo.text.Text(
        "=", pos=16.4+1.7j, color=[0,0,0],
            size=84, anchor_x=0, alpha=0
            )
    eq.zdepth = 10
    eq = mo.Actor(eq)
    eq.newendkey(30).alpha = 1
    mainlayer.merge(eq, atFrame=time)

    mation.endDelay()

    # Enbox formula
    time = mation.lastID()
    box = [6.5,20.5, 0.5,3.5]
    boxer = mo.gadgets.enbox(box, width=5)
    for key in boxer.keys():
        key.zdepth = 10
    mainlayer.append(boxer)

    whitebox = mo.grid.rect(box)
    whitebox.width = 0
    whitebox.fill = [1,1,1]
    whitebox.alpha = 0
    whitebox.zdepth = 9
    whitebox = mo.Actor(whitebox)
    whitebox.newendkey(30).alpha = 1
    mainlayer.merge(whitebox, atFrame=time)

    mation.endDelay()

    boxer.newendkey(20)
    boxer.last().alpha = 0
    boxer.last().visible = False

    whitebox.newendkey(20)
    whitebox.last().alpha = 0
    whitebox.last().visible = False

    # Morph graph
    time = mation.lastID()
    f2 = lambda x: 4*math.sin(-x/2.5)+8
    graph2 = mo.graph.realgraph(f2,a,b, steps=100, width=7, color=[0,0,1])
    graph.newkey(time)
    graph.newendkey(30, graph2)

    # Morph secline
    m2 = (f2(b) - f2(a))/(b-a)
    L2 = lambda x: m2*(x-a) + f2(a)
    secline2 = mo.graph.realgraph(L2,xmin,xmax, steps=1, width=7,
        color=mo.color.colormap["green"]
        )
    secline2.zdepth = -1
    secline.newkey(time)
    secline.newendkey(30, secline2)

    pta.newkey(time)
    pta.newendkey(30).pos = a + 1j*f2(a)

    ptb.newkey(time)
    ptb.newendkey(30).pos = b + 1j*f2(b)

    linea.newkey(time)
    linea.newendkey(30)
    linea.last().tail = f2(a)*1j
    linea.last().head = a + f2(a)*1j

    lineb.newkey(time)
    lineb.newendkey(30)
    lineb.last().tail = f2(b)*1j
    lineb.last().head = b + f2(b)*1j

    tickfa.newkey(time)
    tickfa.newendkey(30)
    tickfa.last().tail += (f2(a)-f(a))*1j
    tickfa.last().head += (f2(a)-f(a))*1j

    tickfb.newkey(time)
    tickfb.newendkey(30)
    tickfb.last().tail += (f2(b)-f(b))*1j
    tickfb.last().head += (f2(b)-f(b))*1j

    labelfa.newkey(time)
    labelfa.newendkey(30)
    labelfa.last().pos += (f2(a)-f(a))*1j

    labelfb.newkey(time)
    labelfb.newendkey(30)
    labelfb.last().pos += (f2(b)-f(b))*1j

    tanline.newkey(time)
    tanline.newendkey(30)
    tanline.last().f = f2
    tanline.last().df = deriv(f2)
    tanline.last().radius = 3.5

    mation.endDelay()

    # Find both new MVT points
    mvt1 = 11.378
    mvt2 = 20.038

    tanline.newendkey(45).x = mvt2

    mation.endDelay(15)

    tan2 = tanline.last().makeFrame().figures[0]
    tan2.zdepth = 10
    mainlayer.append(tan2)
    pt2 = tanline.last().makeFrame().figures[1]
    pt2.zdepth = 10
    mainlayer.append(pt2)

    tanline.newendkey(60).x = mvt1

    tan1 = tanline.last().makeFrame().figures[0]
    tan1.zdepth = 10
    mainlayer.append(tan1)
    pt1 = tanline.last().makeFrame().figures[1]
    pt1.zdepth = 10
    mainlayer.append(pt1)

    mation.endDelay(15)

    tanline.last().transition = mo.transition.uniform
    tanline.newendkey(30).alpha = 0

    mation.endDelay(30*3)

    mation.finitizeDelays(60)

    mation.locatorLayer = 0
    mation.play()

mvt()
```