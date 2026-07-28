# Bevel Studio

Offline renderer for the site's raised surfaces. It ray-traces a beveled slab under a
disk sun and a sky dome, then writes 9-slice tiles that CSS stretches with
`border-image`.

## Setup

From the repo root:

```sh
uv sync
```

That is the whole setup. The root `pyproject.toml` installs `bevelkit` from
`tools/bevel/` in editable mode, so it imports from anywhere in the venv and source
edits take effect immediately.

```sh
uv run tools/bevel/serve_studio.py                        # live WebGL studio
uv run tools/bevel/render_tiles.py                        # bake tiles + generated CSS
uv run jupyter lab tools/bevel/notebooks/edge_studio.ipynb  # analysis notebook
```

## Live studio

`serve_studio.py` opens a WebGL2 studio that runs the *same* model as a fragment
shader, so edits are immediate instead of ~700 ms per preview. It reads and writes the
same `config.json`, and **Bake tiles with Python** POSTs to `/render` so you can go
from a live edit to final tiles without leaving the page.

The GPU port is a two-pass shader. Pass one writes the height field and analytic normal
into an `RGBA32F` target; pass two shades it, sampling that target for the horizon
march. That is the same decomposition as the CPU renderer — the height field exists
precisely so the march is a texture fetch rather than an SDF trace.

Parity is not assumed, it is checked. The JS quintic/Hermite splines reproduce scipy to
~1e-14, and flat-surface colours and sun gains match Python exactly. Two things that
must stay in sync if you touch the shader: world space uses **+y down** to match the
image convention (GL's default is +y up, which silently mirrors the lighting), and the
top face takes the level's material while only the surrounding page takes `ground`.

Two approximations are preview-only: the sun's Gaussian CDF uses the Abramowitz–Stegun
`erf` (max error 1.5e-7), and the corner distance is a 256-segment polyline rather than
1536. Neither affects baked output — always bake with Python.

## Why it is not a box-shadow

Paired light/dark blurs cannot produce a bevel: they have no surface, so the shading
does not respond to the geometry and the shadow is just an offset silhouette. Here the
card is a real height field and every pixel is shaded from its own normal.

## Model

The card is a height field `h(x, y)`, which is what makes this cheap. Given the 2D
distance `u` from the top-face outline:

| region | height | normal |
| --- | --- | --- |
| `u ≤ 0` | `height` | `(0, 0, 1)` |
| `0 < u < skirt` | `profile(u / skirt) · height` | analytic from `profile'` |
| `u ≥ skirt` | `0` | `(0, 0, 1)` |

Because it is a height field there is no need to sphere-trace an SDF. For each azimuth
we walk outward in 2D and track `max (h(sample) − z) / t`, which is the **horizon
angle** in that direction. From it:

- **Sun** — the fraction of the solar disc still above the horizon. With
  `falloff: "gaussian"` the disc is a 2D Gaussian of width `angular_sigma`; because a
  radially symmetric Gaussian has the same σ along every axis, the fraction above a
  horizon line is exactly `Φ((θ_sun − θ_horizon) / σ)` — one normal CDF, no sampling.
  `falloff: "disk"` uses a hard disc of `angular_radius` via the circular-segment area.
  Either way the shadow length falls out of the geometry rather than being tuned.
- **Sky** — the dome above the horizon, integrated in closed form per azimuth slice:
  `∫ (N·ω) cosθ dθ` from the horizon to the zenith. Occlusion, ambient light and
  ambient occlusion are the same integral, so contact darkening is not a separate
  effect.

Shading is Lambert plus Blinn-Phong in linear sRGB. Gains are normalised so a flat,
unoccluded surface renders to exactly its albedo, which is why panel tops are
indistinguishable from the page behind them — `--paper` is emitted from that same
computation rather than authored.

## Edge profiles

A profile maps `u / skirt ∈ [0, 1]` to `z / height ∈ [1, 0]`.

`continuity: "G3"` builds a **C4 quintic spline** with `f'(1) = f''(1) = f'''(1) = 0`,
so the skirt meets the page with matching slope, curvature *and* curvature rate — no
Mach band where it lands. Only `f'(0)` is constrained at the rim, leaving the
deliberate crease. `continuity: "G1"` falls back to a monotone cubic (Fritsch–Carlson),
which guarantees no overshoot but leaves curvature steps at every knot.

Watch the slope, not just the height. A profile whose *slope* is non-monotonic reads as
two separate highlight bands even though the curve looks fine.

## Corners

`corner: "circular"` is the CSS `border-radius` arc: curvature jumps `0 → 1/R` at the
tangent point, so it is only G1. `corner: "g3"` ramps curvature as `κ(s) ∝ sin²(πs/L)`,
making `κ` and `dκ/ds` continuous at both ends while keeping the straight sections
exactly straight — a G3 corner that is still valid to 9-slice.

Use `circular` for anything CSS also clips (images clipped by `border-radius`), so the
tile and the browser agree on the outline.

## Nine-slice

`slice = margin + radius + guard`, `guard = 2·height + corner_guard`. The guard matters:
the corner perturbs sky occlusion for roughly a card height past its tangent point, and
slicing inside that would stretch corner shading down the whole edge. The notebook
asserts the middle row and column are bit-identical across their width.

## Layout

```text
bevelkit/
  config.py     defaults, JSON load/save/merge, output paths
  profile.py    quintic G3 / monotone cubic edge profiles
  corner.py     circular and G3 corner outlines, distance + gradient
  geometry.py   height field, analytic normals, horizon marching
  shading.py    sun disk, sky dome integral, materials, colour space
  render.py     tile metrics and the render loop
  emit.py       PNG + CSS custom property output
  preview.py    matplotlib figures (analytic panes vs rendered tile)
  studio.py     ipywidgets editor
```

Levels (`panel`, `pill`, `image`) each set `radius`, `height`, `skirt`, `profile`,
`material`, `ground`, `corner` and `margin`. `ground` is the material the level rests
on, so a pill on a panel renders its shadow against the panel's colour.

Edits made in the notebook land in `config.json`, which overlays these defaults.

The studio separates the two costs deliberately: profile, curvature and normals are
spline evaluations and redraw live on every edit, while the tile is a raytrace and only
runs on demand. Keep that split if you add panes — anything calling `render_once`
belongs behind the preview button.
