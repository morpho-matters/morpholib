import morpholib as morpho
morpho.importAll()


def main():
    mainlayer = morpho.Layer()
    mation = morpho.Animation(mainlayer)

    grid0 = morpho.grid.mathgrid(
        tweenMethod=morpho.grid.Path.tweenSpiral,
        transition=morpho.transition.quadease
        )

    grid = mainlayer.Actor(grid0)

    grid.newendkey(60, grid0.fimage(lambda s: s**2/10))
    mation.wait(30)

    grid.newendkey(60, grid0.fimage(lambda s: s**3/64))
    mation.wait(30)

    grid.newendkey(60, grid0.fimage(lambda s: s**4/8**3))
    mation.wait(30)

    grid.newendkey(60, grid0.fimage(lambda s: s**5/8**4))
    mation.wait(30)

    grid.newendkey(60, grid0.copy())

    mation.play()

main()
