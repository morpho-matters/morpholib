---
layout: default
title: Morphing Grids
---

<video controls loop style="width:100%; max-width:450px">
<source src="https://raw.githubusercontent.com/morpho-matters/morpholib/master/gallery/sample.mp4" type="video/mp4">
</video>

```python
import morpholib as morpho
morpho.importAll()


def main():
    grid0 = morpho.grid.mathgrid(
        hsteps=50, vsteps=50, BGgrid=True,
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

main()
```