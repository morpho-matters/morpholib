import morpholib as morpho
mo = morpho
morpho.importAll()

from morpholib.tools.basics import *

import math, cmath

morpho.transitions.default = morpho.transitions.quadease

goodblue = tuple((mo.array([0,0.5,1])).tolist())


def torus():
    mation = morpho.video.setupSpaceAlt()
    mation.windowShape = (600,600)
    mation.fullscreen = False

    mainlayer = mation.layers[0]
    xmin,xmax, ymin,ymax = mainlayer.camera.first().view
    for keyfig in mainlayer.camera.keys():
        keyfig.view = [ymin,ymax,ymin,ymax]
        keyfig.moveBy(-1j)

    meshlayer = morpho.SpaceLayer(view=mainlayer.camera.copy())
    mation.merge(meshlayer)

    mesh = morpho.grid.quadgrid(
        view=[0,tau, 0,tau],
        dx=tau/16, dy=tau/24,
        width=1.5, color=[0,0,0],
        fill=goodblue, fill2=(mo.array(goodblue)/2).tolist()
        )
    mesh.shading = True

    R = 2
    r = 0.75
    def tubify(v):
        theta, phi, dummy = v

        x = r*np.cos(theta+pi/2)
        y = phi-3
        z = r*np.cos(theta) + r

        return morpho.array([x,y,z])

    def torify(v):
        theta, phi, dummy = v

        x = (R+r*np.cos(theta-pi/2))*np.cos(phi)
        y = -(R+r*np.cos(theta-pi/2))*np.sin(phi)
        z = r*np.cos(theta) + r

        return morpho.array([x,y,z])

    torus = morpho.grid.quadgrid(
        view=[-3,3, -3,3],
        dx=6/16, dy=6/24,
        width=1.5, color=[0,0,0],
        fill=goodblue, fill2=(mo.array(goodblue)/2).tolist()
        )
    torus.shading = True
    torus = morpho.Actor(torus)
    torus.newendkey(45)
    torus.newendkey(60, mesh.fimage(tubify))
    torus.newendkey(45)
    torus.newendkey(60, mesh.fimage(torify))
    meshlayer.merge(torus)

    # Change up camera
    mainlayer.camera.movekey(mainlayer.camera.lastID(), torus.lastID() + 90)
    meshlayer.camera = mainlayer.camera.copy()

    mation.newFrameRate(10)
    mation.play()

torus()
