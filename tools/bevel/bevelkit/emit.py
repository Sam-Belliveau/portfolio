from __future__ import annotations

from pathlib import Path

from PIL import Image

import numpy as np

from .config import CSS_PATH, TILE_DIR, level_names
from .render import render_level
from .shading import linear_to_hex, linear_to_srgb


def hard_light_encode(radiance, base):
    result = np.clip(linear_to_srgb(radiance), 0.0, 1.0)
    anchor = np.clip(linear_to_srgb(base), 1e-4, 1.0 - 1e-4)
    darker = result / (2.0 * anchor)
    lighter = 1.0 - (1.0 - result) / (2.0 * (1.0 - anchor))
    return np.clip(np.where(result <= anchor, darker, lighter), 0.0, 1.0)


def write_tiles(config, tile_dir=None, css_path=None, progress=None):
    tiles = Path(tile_dir) if tile_dir else TILE_DIR
    stylesheet = Path(css_path) if css_path else CSS_PATH
    tiles.mkdir(parents=True, exist_ok=True)

    scale = int(config["render"]["scale"])
    declarations = []
    page_color = None

    for name in level_names(config):
        image, metrics, colors = render_level(
            config, name, progress=progress, encode=False
        )
        modulation = hard_light_encode(image, colors["ground"])
        codes = np.round(modulation * 255.0)
        untouched = np.abs(modulation - 0.5) < (0.75 / 255.0)
        codes = np.where(untouched, 128.0, codes)
        encoded = np.clip(codes, 0, 255).astype(np.uint8)
        Image.fromarray(encoded, mode="RGB").save(tiles / f"{name}.png", optimize=True)

        alpha = np.clip(np.round(colors["coverage"] * 255.0), 0, 255).astype(np.uint8)
        mask = np.dstack([np.full_like(alpha, 255)] * 3 + [alpha])
        Image.fromarray(mask, mode="RGBA").save(
            tiles / f"{name}-mask.png", optimize=True
        )
        if page_color is None:
            page_color = linear_to_hex(colors["ground"])
        slice_pixels = int(round(metrics["slice_css"] * scale))
        declarations.append(
            f"  --bevel-{name}: url('/bevel/{name}.png') {slice_pixels} fill"
            f" / {metrics['slice_css']:g}px / {metrics['margin']:g}px stretch;"
        )
        declarations.append(
            f"  --bevel-{name}-mask: url('/bevel/{name}-mask.png') {slice_pixels} fill"
            f" / {metrics['slice_css']:g}px / {metrics['margin']:g}px stretch;"
        )
        declarations.append(f"  --bevel-{name}-radius: {metrics['radius']:g}px;")
        declarations.append(
            f"  --bevel-{name}-face: {linear_to_hex(colors['face'])};"
        )

    body = "\n".join(declarations)
    stylesheet.parent.mkdir(parents=True, exist_ok=True)
    stylesheet.write_text(f":root {{\n  --paper: {page_color};\n{body}\n}}\n")
    return stylesheet
