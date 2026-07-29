# Bevel

Path-traced nine-slice tiles for the site's raised surfaces. One card is built
from erf curves, rendered in Cycles under a physical sky, and cut into
`border-image` tiles the page retints at runtime.

```sh
uv sync
uv run tools/bevel/bake.py               # the tile
uv run tools/bevel/bake.py --preview     # quarter scale, few samples
uv run tools/bevel/bake.py --models-only # meshes only, no Cycles
uv run tools/bevel/bake.py --css-only    # stylesheet only, no Cycles
```

Blender is found automatically on macOS; override with `--blender`.

## Why it is not a box-shadow

Paired light and dark blurs cannot produce a bevel: they have no surface, so the
shading never responds to the geometry and the shadow is only an offset
silhouette. Here the card is real geometry under a real sky, and every pixel is
the answer to an actual light transport problem.

## One shape, one knob

Everything is a tangent angle turning through offset erf steps, integrated as a
point travelling around the unit circle.

```text
theta(s) = sum_k  sweep_k * Phi((s - centre_k) / width)
curve(s) = integral (cos theta, sin theta) ds
```

Curvature is therefore a sum of Gaussians: smooth to every order, with nothing
to tune but the width of a turn.

- **Outline** — one periodic staircase of four 90 degree turns, summed over its
  images and integrated once around the loop. Four *isolated* turns leave the
  straight runs off by about 0.12 degrees where the tails are cut.
- **Cross-section** — a closed pill, sliced by the ground through its equator.

`surface.curvature` is the whole shape. It is how much tighter the edge turns
than the corner:

| value | meaning |
| ----- | ------- |
| 1 | equal curvature: one sphere sits tangent to both, the corner is a spherical fillet. The thickest a card can sensibly be — past it the edge is flatter than the corner it turns through. |
| 2 | edge twice as tight, card half that thickness |
| 3 | a third: a pressed sheet rather than a moulded card |

Thickness is never chosen. It follows the radius, so the card is one shape
scaled by one number, and `surface.reach` sets what that costs: at 2.0 the bevel
is 1.86x the radius and the profile meets the top face within 4 degrees.

**Nesting is a constant offset of the same curve, not a ladder of radii.** A
smaller radius starts turning earlier than an offset does, so nesting by
shrinking radii pinches the band at the corners by about 12%.

## Nine-slice, and why the frame is bigger than the tile

```text
slice = margin + extent + guard
```

`margin` carries the cast shadow, its penumbra and the ambient falloff, so CSS
never has to leave room for one. `extent` is the corner box. `guard` is the run
of straight edge the corner still perturbs — measured in standard deviations of
the corner's own Gaussian (`surface.guard_sigma`), because that is what its
influence actually decays like.

`border-image` *stretches* the four edge strips, so whatever is in them has to be
constant along the direction it gets stretched. A path trace is not — it carries
per-pixel noise, and stretching noise smears it into streaks. So the frame is
rendered wider than the tile by `strip`, a run of straight edge where the field
genuinely is translation-invariant. Averaging along that run is not a blur: it is
a better estimator of a single number, and it drops strip noise by the square
root of the run length. The corner blocks keep their own noise and are crossfaded
into the averaged strips across the guard band.

`bake.py` prints the residual drift along each stretched strip. It is zero to
floating point.

**This is why the material is spatially uniform.** Any grain would be averaged
out of the strips and survive only in the corners.

## Tile size

The finished tile is cropped to `render.tile_pixels` from the outside, where the
shadow has already faded to nothing. Cropping moves the slice and the outset in
by the same amount, so the card still lands exactly on the element's edge — the
tile just stops carrying shadow that was doing nothing. Raising `render.scale`
against a fixed `tile_pixels` therefore buys effective resolution, until the crop
reaches the card and the outset would go negative.

## Retintable output

Two renders per tile: `beauty` with the full material, `diffuse` with specular
and sheen switched off. The diffuse render is albedo times shading, so dividing
by its own flat value cancels the albedo exactly:

```text
darken(x)  = diffuse(x) / diffuse_flat                 -> multiply
lighten(x) = 1 - (1 - render) / (1 - base*darken)      -> screen
```

`darken` is a pure shading ratio, so multiplying any colour by it carries the
shadow, contact darkening and shaded bevel face along. It can only darken, and
the sunlit bevel face is *brighter* than flat, so that surplus goes into
`lighten` with the specular. The page composites

```text
screen(multiply(face, darken), lighten)
```

`--paper` is the mid grey the tiles were baked against, not a page colour: the
reference is mid grey because `lighten`'s denominator collapses near white and
bands. The page picks its own colours and the tiles retint them.

The third layer is `mask`, the card's exact silhouette as alpha. CSS can only
round a corner with a circular arc and this corner is not one, so any surface
carrying its own colour is clipped with the mask rather than `border-radius`.

## Dither

Eight bits over a bevel this shallow bands visibly, so quantisation error is
pushed into the frequencies the eye is worst at, via a void-and-cluster blue
noise matrix. The middle band of the tile is exactly one matrix, since the edge
strips are a single averaged profile broadcast along their run and everything
past that is repetition.

## Layout

```text
bake.py           host driver: meshes -> Blender -> tiles
blender_scene.py  runs inside Blender: sky, paper, orthographic bake
bevelkit/
  shape.py     erf turns: outline, corner and cross-section
  mesh.py      loft the card from those curves
  layout.py    thickness from radius, margins, guards, slice and frame sizes
  assemble.py  frame -> exactly edge-invariant nine-slice tile
  emit.py      darken/lighten/mask split, PNG and custom properties
  dither.py    blue noise
  colour.py    sRGB transfer
  config.py    defaults and JSON overlay
```

`config.json` overlays `config.py`'s defaults and is the only thing to edit.
