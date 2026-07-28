from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
STUDIO_ROOT = PACKAGE_ROOT.parent
PROJECT_ROOT = STUDIO_ROOT.parent.parent
CONFIG_PATH = STUDIO_ROOT / "config.json"
TILE_DIR = PROJECT_ROOT / "public" / "bevel"
CSS_PATH = PROJECT_ROOT / "src" / "bevel.generated.css"

DEFAULTS = {
    "lighting": {
        "sun": {
            "azimuth": 225.0,
            "elevation": 45.0,
            "falloff": "gaussian",
            "angular_radius": 3.0,
            "angular_sigma": 6.0,
            "color": "#fff6e4",
        },
        "sky": {
            "horizon_color": "#cdd9e6",
            "zenith_color": "#8fb4e2",
            "strength": 0.36,
        },
    },
    "materials": {
        "page": {
            "albedo": "#eae8e2",
            "specular_strength": 0.14,
            "gloss": 20.0,
        },
        "panel_plastic": {
            "albedo": "#eae8e2",
            "specular_strength": 0.14,
            "gloss": 20.0,
        },
        "pill_plastic": {
            "albedo": "#eae8e2",
            "specular_strength": 0.16,
            "gloss": 24.0,
        },
        "photo_mount": {
            "albedo": "#e4e1da",
            "specular_strength": 0.10,
            "gloss": 16.0,
        },
    },
    "profiles": {
        "sharp_top_chamfer": {
            "points": [
                [0.0, 1.0],
                [0.2, 0.52429],
                [0.4, 0.20217],
                [0.6, 0.04710],
                [0.8, 0.00339],
                [1.0, 0.0],
            ],
            "start_slope": -2.6,
            "end_slope": 0.0,
            "continuity": "G3",
        },
        "soft_rim": {
            "points": [
                [0.0, 1.0],
                [0.2, 0.65536],
                [0.4, 0.31104],
                [0.6, 0.09216],
                [0.8, 0.00896],
                [1.0, 0.0],
            ],
            "start_slope": -1.6,
            "end_slope": 0.0,
            "continuity": "G3",
        },
        "knife_rim": {
            "points": [
                [0.0, 1.0],
                [0.2, 0.36864],
                [0.4, 0.10368],
                [0.6, 0.01536],
                [0.8, 0.00064],
                [1.0, 0.0],
            ],
            "start_slope": -4.0,
            "end_slope": 0.0,
            "continuity": "G3",
        },
        "flat_chamfer": {
            "points": [[0.0, 1.0], [1.0, 0.0]],
            "start_slope": -1.0,
            "end_slope": -1.0,
            "continuity": "G1",
        },
        "round_over": {
            "points": [[0.0, 1.0], [0.35, 0.94], [0.70, 0.68], [1.0, 0.0]],
            "start_slope": 0.0,
            "end_slope": -2.4,
            "continuity": "G1",
        },
        "ogee": {
            "points": [[0.0, 1.0], [0.22, 0.62], [0.45, 0.44], [0.72, 0.30], [1.0, 0.0]],
            "start_slope": -2.2,
            "end_slope": 0.0,
            "continuity": "G1",
        },
    },
    "levels": {
        "panel": {
            "radius": 22.0,
            "height": 9.0,
            "skirt": 8.0,
            "profile": "sharp_top_chamfer",
            "material": "panel_plastic",
            "ground": "page",
            "margin": 26.0,
            "corner": "g3",
            "corner_guard": 2.0,
        },
        "pill": {
            "radius": 16.0,
            "height": 5.0,
            "skirt": 5.0,
            "profile": "sharp_top_chamfer",
            "material": "pill_plastic",
            "ground": "panel_plastic",
            "margin": 16.0,
            "corner": "g3",
            "corner_guard": 2.0,
        },
        "image": {
            "radius": 12.0,
            "height": 3.5,
            "skirt": 3.5,
            "profile": "ogee",
            "material": "photo_mount",
            "ground": "pill_plastic",
            "margin": 12.0,
            "corner": "circular",
            "corner_guard": 2.0,
        },
    },
    "render": {
        "scale": 2,
        "supersample": 2,
        "azimuth_samples": 128,
    },
}


def default_config() -> dict:
    return deepcopy(DEFAULTS)


def load_config(path: Path | None = None) -> dict:
    target = Path(path) if path else CONFIG_PATH
    if not target.exists():
        return default_config()
    stored = json.loads(target.read_text())
    return merge(default_config(), stored)


def save_config(config: dict, path: Path | None = None) -> Path:
    target = Path(path) if path else CONFIG_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(config, indent=2) + "\n")
    return target


def merge(base: dict, overlay: dict) -> dict:
    result = deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def level_names(config: dict) -> list[str]:
    return list(config["levels"].keys())
