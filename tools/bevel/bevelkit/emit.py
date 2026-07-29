"""Encoding tiles for CSS.

A tile is not a picture of a card, it is what the card *does* to whatever is
behind it, split so the page can retint the surface at runtime.

Two renders per tile: `beauty` with the full material, `diffuse` with specular
and sheen switched off. Because the diffuse render is albedo times shading,
dividing it by its own flat value cancels the albedo exactly:

    darken(x)  = diffuse(x) / diffuse_flat                    -> multiply
    lighten(x) = 1 - (1 - render) / (1 - base*darken)         -> screen

`darken` is a pure shading ratio, so it retints exactly: multiply it by any
colour and the shadow, contact darkening and shaded bevel face all follow. It
can only darken though, and the sunlit bevel face is *brighter* than flat, so
that surplus goes into `lighten` along with the specular.
"""

from __future__ import annotations

import re

import numpy as np
from PIL import Image

from .colour import linear_to_hex, linear_to_srgb
from .dither import quantise


def feather(layer, identity, width):
    """Fade to the no-op value at the tile border."""
    rows, columns = layer.shape[:2]
    down = np.minimum(np.arange(rows), rows - 1 - np.arange(rows))
    across = np.minimum(np.arange(columns), columns - 1 - np.arange(columns))
    edge = np.minimum(down[:, None], across[None, :])
    ramp = np.clip(edge / max(width, 1.0), 0.0, 1.0)
    ramp = ramp * ramp * (3.0 - 2.0 * ramp)
    return identity + (layer - identity) * ramp[..., None]


def split_layers(beauty, diffuse, flat_diffuse, flat_beauty):
    """Split a render into a multiply layer and a screen layer.

    The page composites them as

        screen(multiply(surface, darken), lighten)

    Both come back in display space, because that is where the browser blends.

    `darken` is the diffuse shading ratio. The albedo cancels in that ratio, so
    multiplying *any* surface colour by it carries the shadow, contact darkening
    and shaded bevel face along -- that is what makes the tiles retintable.

    `lighten` is then whatever screen has to contribute to land on the render,
    which inverts exactly:

        lighten = 1 - (1 - render) / (1 - base*darken)

    That denominator is the reason the reference colour is mid grey. Near white
    it collapses towards zero and amplifies sampling noise into banding; at 0.5
    it stays within [0.5, 1], and both layers get comparable headroom instead of
    the screen layer being squeezed into the few codes left below white.
    """
    darken = linear_to_srgb(np.clip(diffuse / np.maximum(flat_diffuse, 1e-8), 0.0, 1.0))
    render = linear_to_srgb(beauty)
    headroom = 1.0 - linear_to_srgb(flat_beauty) * darken
    lighten = 1.0 - (1.0 - render) / np.maximum(headroom, 1e-4)
    return darken, np.clip(lighten, 0.0, 1.0)


def encode(config, darken, lighten):
    render = config["render"]
    width = 20.0 * int(render["scale"]) * float(render["feather"])

    darken = feather(darken, 1.0, width)
    lighten = feather(lighten, 0.0, width)

    # Multiply's identity is 255; a pixel one code off would tint the whole page.
    untouched = np.abs(darken - 1.0) < (0.75 / 255.0)
    darken = np.where(untouched, 255.0, darken * 255.0)
    return quantise(darken, render), quantise(lighten * 255.0, render)


def encode_mask(coverage, config):
    alpha = quantise(np.clip(coverage, 0.0, 1.0) * 255.0, config["render"])
    return np.dstack([np.full_like(alpha, 255)] * 3 + [alpha])


def declarations(radius, layout):
    """The custom properties one baked radius contributes.

    Every one of these is a layout number rather than a measurement, so the
    stylesheet can be rewritten from the geometry alone -- see `write_stylesheet`.
    """
    name = f"panel-{radius:g}"
    cut = layout["cut_pixels"]
    border = f"{cut} fill / {layout['cut_css']:g}px / {layout['outset_css']:g}px round"
    lines = [
        f"  --bevel-{radius:g}-{suffix}: url('/bevel/{name}-{suffix}.png') {border};"
        for suffix in ("darken", "lighten", "mask")
    ]
    lines.append(f"  --bevel-{radius:g}-radius: {layout['padding']:g}px;")
    # The same number without units, so the page can divide by it. Dividing the
    # radius it wants by the radius this was baked at gives the factor to redraw
    # the tile at, which makes the effective corner a CSS value rather than
    # whatever the bake happened to use.
    lines.append(f"  --bevel-{radius:g}-unit: {layout['padding']:g};")
    # What to clip a coloured face with. Not the same as the radius above:
    # CSS only has circular corners, and this one is not circular.
    lines.append(f"  --bevel-{radius:g}-clip: {layout['clip_radius']:.4g}px;")
    lines.append(f"  --bevel-{radius:g}-bevel: {layout['bevel']:g}px;")
    # Twice the slice is the smallest surface the tile fits in unscaled, and the
    # two together are the drawn size, so the page can redraw a tile at a
    # fraction of its baked scale without hardcoding either.
    lines.append(f"  --bevel-{radius:g}-slice: {layout['cut_css']:g}px;")
    lines.append(f"  --bevel-{radius:g}-outset: {layout['outset_css']:g}px;")
    return lines


def write_stylesheet(layouts, paper, css_path):
    """The stylesheet on its own.

    Only `--paper` ever came from the render, so with that carried over a layout
    change reaches the page without going back to Cycles.
    """
    body = "\n".join(
        line
        for radius, layout in sorted(layouts.items())
        for line in declarations(radius, layout)
    )
    css_path.parent.mkdir(parents=True, exist_ok=True)
    css_path.write_text(
        "/* generated by tools/bevel/bake.py -- do not edit */\n"
        f":root {{\n  --paper: {paper};\n{body}\n}}\n"
    )
    return paper


def current_paper(css_path, fallback="#7f7f7f"):
    if not css_path.exists():
        return fallback
    found = re.search(r"--paper:\s*(#[0-9a-fA-F]{6})", css_path.read_text())
    return found.group(1) if found else fallback


def write_tiles(tiles, reference, config, tile_dir, css_path):
    tile_dir.mkdir(parents=True, exist_ok=True)

    for radius, payload in sorted(tiles.items()):
        name = f"panel-{radius:g}"
        edge = payload["layout"]["trim_pixels"]
        keep = (slice(edge, -edge), slice(edge, -edge)) if edge else (Ellipsis,)
        darken, lighten = encode(
            config, payload["darken"][keep], payload["lighten"][keep]
        )

        Image.fromarray(darken, mode="RGB").save(
            tile_dir / f"{name}-darken.png", optimize=True
        )
        Image.fromarray(lighten, mode="RGB").save(
            tile_dir / f"{name}-lighten.png", optimize=True
        )
        Image.fromarray(encode_mask(payload["coverage"][keep], config), mode="RGBA").save(
            tile_dir / f"{name}-mask.png", optimize=True
        )

    return write_stylesheet(
        {radius: payload["layout"] for radius, payload in tiles.items()},
        linear_to_hex(reference),
        css_path,
    )
