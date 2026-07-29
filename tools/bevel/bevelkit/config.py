from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
TOOL_ROOT = PACKAGE_ROOT.parent
PROJECT_ROOT = TOOL_ROOT.parent.parent
CONFIG_PATH = TOOL_ROOT / "config.json"
SCENE_SCRIPT = TOOL_ROOT / "blender_scene.py"
TILE_DIR = PROJECT_ROOT / "public" / "bevel"
CSS_PATH = PROJECT_ROOT / "src" / "bevel.generated.css"

DEFAULTS = {
    "surface": {
        # One knob for the whole shape. It trades how tightly the round-over is
        # concentrated against how flat it has arrived by the time it meets the
        # top face: at 2.0 the join is within 4 degrees of flat and the bevel
        # costs 1.86x the radius. Larger is smoother and much wider.
        "reach": 2.0,
        # How far past the corner the tile keeps rendering before it starts
        # slicing, in standard deviations of the corner's Gaussian. Below about
        # 1.5 the corner's shading starts getting stretched down the straight
        # edge; above it the tile is just bigger than it needs to be.
        "guard_sigma": 1.5,
        # How much tighter the edge turns than the corner. 1 makes the two
        # curvatures equal, so one sphere is tangent to both and the corner is a
        # spherical fillet -- the thickest a card can sensibly be, since past it
        # the edge would be flatter than the corner it turns through. 2 is half
        # that thickness. This is the shape knob; thickness follows the radius.
        "curvature": 3.0,
        # How the card meets the ground. "cut": a whole pill sliced through its
        # equator, so the widest ring is the contact and the wall drops straight
        # into the plane. "rest": the whole pill sits on the plane instead, so it
        # rounds over underneath, the silhouette floats a little above the
        # ground, and light reaches in under the rim -- stacked plates rather
        # than shapes pressed into a sheet.
        "seat": "cut",
    },
    "paper": {
        "base_color": "#7f7f7f",
        "roughness": 0.38,
        "ior": 1.5,
        "specular": 0.5,
        # Sheen is a fibre effect -- it is what made this read as paper. Plastic
        # has no grazing-angle bloom, so the gloss has to come from the specular
        # lobe alone.
        "sheen": 0.0,
        "sheen_roughness": 0.85,
        "subsurface": 0.05,
        "subsurface_radius": 0.3,
    },
    "sky": {
        "model": "MULTIPLE_SCATTERING",
        "sun_elevation": 45.0,
        "sun_azimuth": 225.0,
        # Deliberately far wider than the real 0.545 degree disc: a true sun is
        # a point source at this scale and casts a razor edge. Widening it is
        # the only handle on penumbra, and the sky model and the lamp stay
        # consistent because the calibration measures whatever disc it is given.
        "sun_size": 10.0,
        # Below 1: the sun disc carries less of the total, so the sky fills the
        # shadows instead. Together with the haze this is the ambient/direct
        # ratio, and it is what sets how deep a shadow gets.
        "sun_intensity": 0.45,
        "sun_disc": True,
        "altitude": 300.0,
        "air_density": 1.0,
        "aerosol_density": 3.0,
        "ozone_density": 1.0,
        "ground_albedo": 0.3,
        "strength": 1.0,
    },
    # One curvature for the whole page. Nesting is a constant offset of the
    # same corner rather than a ladder of shrinking radii, which is what keeps
    # the band between two surfaces the same width the whole way around -- a
    # smaller radius turns earlier than an offset does, and pinches at the
    # corner. One curve also means one tile.
    "radii": [8.0],
    "render": {
        "scale": 5,
        "samples": 768,
        "mask_samples": 128,
        "adaptive_threshold": 0.003,
        "strip": 64.0,
        "crossfade": 0.6,
        "ambient_margin": 1.0,
        "feather": 0.1,
        "dither_cell": 1,
        # What the finished tile should measure. The shadow's outermost tail is
        # within a code or two of doing nothing, so the tile is cropped back to
        # this and the slice and outset follow -- the file stays a fixed size and
        # spends its pixels on the part that reads.
        "tile_pixels": 256,
        "bounces": 8,
        "filter_width": 1.5,
        "max_chord": 6.0,
        "max_turn_degrees": 2.0,
    },
}


def default_config() -> dict:
    return deepcopy(DEFAULTS)


def load_config(path: Path | None = None) -> dict:
    target = Path(path) if path else CONFIG_PATH
    if not target.exists():
        return default_config()
    return merge(default_config(), json.loads(target.read_text()))


def merge(base: dict, overlay: dict) -> dict:
    result = deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result
