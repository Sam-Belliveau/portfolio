#!/usr/bin/env python
"""Bake the bevel tiles.

    uv run tools/bevel/bake.py                 # every radius
    uv run tools/bevel/bake.py --radii 32      # one, for iterating
    uv run tools/bevel/bake.py --preview       # quarter scale, few samples

Builds a mesh per radius from the erf curves, hands them to Cycles through
`blender_scene.py`, then cuts nine-slice tiles out of the renders and writes the
PNGs and custom properties the stylesheet imports.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from bevelkit.assemble import invariance_error, nine_slice  # noqa: E402
from bevelkit.colour import hex_to_linear  # noqa: E402
from bevelkit.config import (  # noqa: E402
    CSS_PATH,
    SCENE_SCRIPT,
    TILE_DIR,
    load_config,
)
from bevelkit.emit import (  # noqa: E402
    current_paper,
    split_layers,
    write_stylesheet,
    write_tiles,
)
from bevelkit.layout import tile_layout  # noqa: E402
from bevelkit.mesh import card_mesh, ground_mesh  # noqa: E402

BLENDER_CANDIDATES = (
    "/Applications/Blender.app/Contents/MacOS/Blender",
    "/Applications/Blender/Blender.app/Contents/MacOS/Blender",
    "blender",
)


def find_blender(override=None):
    for candidate in filter(None, (override, *BLENDER_CANDIDATES)):
        resolved = shutil.which(candidate) or (
            candidate if Path(candidate).exists() else None
        )
        if resolved:
            return resolved
    raise SystemExit("Blender not found; pass --blender /path/to/Blender")


def build_meshes(config, layouts, work, models):
    """One curvature-adaptive mesh per radius, used to render and to view."""
    render = config["render"]
    chord = float(render["max_chord"])
    turn = np.radians(float(render["max_turn_degrees"]))
    models.mkdir(parents=True, exist_ok=True)
    paths = {}

    for radius, layout in layouts.items():
        payload = card_mesh(layout, chord, turn)
        path = work / f"card-{radius:g}.npz"
        np.savez(path, **payload)
        paths[radius] = {
            "render": path,
            "model": path,
            "glb": models / f"panel-{radius:g}.glb",
        }
        print(
            f"  panel-{radius:g}: corner r {radius:g}  height r"
            f" {layout['profile_radius']:.2f}"
            f"  curvature ratio {radius / layout['profile_radius']:.3f}"
            f"   {payload['quads'].shape[0]:,} quads"
        )

    reach = max(layout["frame_css"] for layout in layouts.values()) * 40.0
    ground = work / "ground.npz"
    np.savez(ground, **ground_mesh(reach))
    return paths, ground


def build_job(config, layouts, meshes, ground, work, models_only=False):
    render = config["render"]
    paper = dict(config["paper"])
    paper["base_color"] = list(hex_to_linear(paper["base_color"]))

    frames = []

    def add(name, kind, size, resolution, samples, mesh=None):
        frames.append(
            {
                "name": name,
                "kind": kind,
                "size": size,
                "resolution": int(resolution),
                "samples": int(samples),
                "mesh": str(mesh) if mesh else None,
                "exr": str(work / f"{name}.exr"),
                "output": str(work / f"{name}.npy"),
            }
        )

    for radius, layout in [] if models_only else layouts.items():
        name = f"panel-{radius:g}"
        size = layout["frame_css"]
        pixels = layout["frame_pixels"]
        add(
            f"{name}-beauty",
            "beauty",
            size,
            pixels,
            render["samples"],
            meshes[radius]["render"],
        )
        add(
            f"{name}-diffuse",
            "diffuse",
            size,
            pixels,
            render["samples"],
            meshes[radius]["render"],
        )
        add(
            f"{name}-mask",
            "mask",
            size,
            pixels,
            render["mask_samples"],
            meshes[radius]["render"],
        )

    job = {
        "models": [
            {"mesh": str(entry["render"]), "glb": str(entry["glb"])}
            for entry in meshes.values()
        ],
        "sky": config["sky"],
        "paper": paper,
        "bounces": int(render["bounces"]),
        "filter_width": float(render["filter_width"]),
        "adaptive_threshold": float(render["adaptive_threshold"]),
        "ground": str(ground),
        "probe": str(work / "probe.exr"),
        "frames": frames,
    }
    path = work / "job.json"
    path.write_text(json.dumps(job, indent=2))
    return path, frames


SAMPLE = re.compile(r"Sample (\d+)/(\d+)")
REMAINING = re.compile(r"Remaining:(\S+)")


def run_blender(blender, job_path, verbose):
    command = [blender, "-b", "-noaudio", "-P", str(SCENE_SCRIPT), "--", str(job_path)]
    print(f"\n  {Path(blender).name} rendering ...", flush=True)
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    tail = []
    finished = False
    label = ""
    live = False
    for line in process.stdout:
        tail.append(line)
        finished |= line.startswith("scene done")

        if verbose:
            print(f"    {line.rstrip()}", flush=True)
            continue

        progress = SAMPLE.search(line)
        if progress:
            done, total = (int(value) for value in progress.groups())
            left = REMAINING.search(line)
            filled = int(28 * done / max(total, 1))
            print(
                f"\r    {label:<22s} [{'#' * filled}{'.' * (28 - filled)}]"
                f" {done:>5d}/{total}"
                f"  {left.group(1) if left else '':>9s}",
                end="",
                flush=True,
            )
            live = True
        elif line.startswith(("  render", "  model", "  sun ", "cycles backend", "scene done")):
            if live:
                print(flush=True)
                live = False
            print(f"    {line.rstrip()}", flush=True)
            if line.startswith("  render"):
                label = line.split()[1]
    if live:
        print(flush=True)

    # Blender exits 0 even when a -P script raises, so trust the sentinel instead.
    if process.wait() != 0 or not finished:
        sys.stdout.write("".join(tail[-40:]))
        raise SystemExit("Blender did not finish the job")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--radii", type=float, nargs="*", default=None)
    parser.add_argument("--blender", default=None)
    parser.add_argument("--work", type=Path, default=None)
    parser.add_argument("--models", type=Path, default=None)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--models-only", action="store_true")
    parser.add_argument("--css-only", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--keep", action="store_true")
    arguments = parser.parse_args()

    config = load_config(arguments.config)
    if arguments.preview:
        config["render"].update(
            scale=1, samples=64, mask_samples=32
        )
    radii = arguments.radii if arguments.radii else config["radii"]

    work = arguments.work or Path(__file__).resolve().parent / ".bake"
    work.mkdir(parents=True, exist_ok=True)

    started = time.time()
    layouts = {radius: tile_layout(config, radius) for radius in radii}

    # The stylesheet is pure layout, so rewriting it never needs a render.
    if arguments.css_only:
        paper = write_stylesheet(layouts, current_paper(CSS_PATH), CSS_PATH)
        print(f"wrote {CSS_PATH} (--paper {paper}) without rendering")
        return

    models = arguments.models or Path(__file__).resolve().parent / "models"
    meshes, ground = build_meshes(config, layouts, work, models)
    job_path, frames = build_job(
        config, layouts, meshes, ground, work, arguments.models_only
    )
    run_blender(find_blender(arguments.blender), job_path, arguments.verbose)

    if arguments.models_only:
        for path in sorted(models.glob("*.glb")):
            print(f"  {path}  {path.stat().st_size / 1e6:.2f} MB")
        return

    def load(name):
        return np.load(work / f"{name}.npy").astype(np.float64)

    scale = int(config["render"]["scale"])
    crossfade = float(config["render"]["crossfade"])

    assembled = {}
    for radius, layout in layouts.items():
        name = f"panel-{radius:g}"
        beauty, flat_beauty = nine_slice(
            load(f"{name}-beauty")[..., :3], layout, crossfade, scale
        )
        diffuse, flat_diffuse = nine_slice(
            load(f"{name}-diffuse")[..., :3], layout, crossfade, scale
        )
        coverage, _ = nine_slice(load(f"{name}-mask")[..., 3:4], layout, crossfade, scale)
        assembled[radius] = (beauty, diffuse, coverage, flat_diffuse, flat_beauty)

    # The tile's own centre is the flat top face, so it is the reference: no
    # separate render of bare ground, and the anchor is guaranteed to be the same
    # surface under the same sky as the tile it normalises.
    flat_diffuse = np.mean([entry[3] for entry in assembled.values()], axis=0)
    flat_beauty = np.mean([entry[4] for entry in assembled.values()], axis=0)

    # A physical sky is in absolute radiometric units, so the render has no
    # inherent exposure. White balancing per channel is what a camera does: the
    # sunlit surface lands on exactly the configured paper colour, and shadows
    # keep the blue cast of being lit by sky alone.
    gain = hex_to_linear(config["paper"]["base_color"]) / flat_diffuse
    print(
        f"\n  flat centre: diffuse {flat_diffuse.round(4).tolist()}"
        f"  beauty {flat_beauty.round(4).tolist()}"
        f"\n  sun/sky tint {(flat_diffuse / flat_diffuse[1]).round(4).tolist()}"
        f"  white balance gain {gain.round(6).tolist()}"
    )
    flat_diffuse = flat_diffuse * gain
    flat_beauty = flat_beauty * gain

    tiles = {}
    for radius, layout in layouts.items():
        beauty, diffuse, coverage, centre, _ = assembled[radius]
        darken, lighten = split_layers(
            beauty * gain, diffuse * gain, flat_diffuse, flat_beauty
        )
        tiles[radius] = {
            "layout": layout,
            "darken": darken,
            "lighten": lighten,
            "coverage": coverage[..., 0],
        }
        drift = max(invariance_error(darken, layout), invariance_error(lighten, layout))
        border = np.concatenate([beauty[0], beauty[-1], beauty[:, 0], beauty[:, -1]])
        outside = border.mean(axis=0) / (flat_beauty / gain)
        print(
            f"  panel-{radius:g}: strip drift {drift:.2e}"
            f"  page / face {outside.round(4).tolist()}"
            f"  darken [{darken.min():.3f}, {darken.max():.3f}]"
            f"  lighten [{lighten.min():.4f}, {lighten.max():.4f}]"
        )

    paper = write_tiles(tiles, flat_beauty, config, TILE_DIR, CSS_PATH)
    if not arguments.keep:
        shutil.rmtree(work, ignore_errors=True)
    print(f"\nwrote {CSS_PATH} (--paper {paper}) in {time.time() - started:.1f}s")


if __name__ == "__main__":
    main()
