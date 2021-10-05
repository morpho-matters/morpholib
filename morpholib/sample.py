import morpholib as morpho
import morpholib.grid, morpholib.transitions


def play():
    grid0 = morpho.grid.mathgrid(
        tweenMethod=morpho.grid.Path.tweenSpiral,
        transition=morpho.transition.quadease
        )

    grid = morpho.Actor(grid0)
    mation = morpho.Animation(grid)

    grid.newendkey(60, grid0.fimage(lambda s: s**2/10))
    mation.endDelay(30)

    grid.newendkey(60, grid0.fimage(lambda s: s**3/64))
    mation.endDelay(30)

    grid.newendkey(60, grid0.fimage(lambda s: s**4/8**3))
    mation.endDelay(30)

    grid.newendkey(60, grid0.fimage(lambda s: s**5/8**4))
    mation.endDelay(30)

    grid.newendkey(60, grid0.copy())


    mation.play()
