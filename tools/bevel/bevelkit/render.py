from __future__ import annotations

import math

import numpy as np

from .geometry import HeightField
from .profile import EdgeProfile
from .horizon import saddle_correction
from .shading import LightRig, hex_to_linear, linear_to_srgb


def lerp(low, high, blend):
    return low + (high - low) * blend


def mix(low, high, blend):
    return low[None, :] + (high - low)[None, :] * blend[:, None]


def resolve_level(config, name):
    level = config["levels"][name]
    profile = EdgeProfile.from_dict(config["profiles"][level["profile"]])
    material = config["materials"][level["material"]]
    ground = config["materials"][level.get("ground", "page")]
    return level, profile, material, ground


def required_margin(config, level):
    sun = config["lighting"]["sun"]
    elevation = math.radians(float(sun["elevation"]))
    sigma = math.radians(float(sun.get("angular_sigma", 6.0)))
    height = float(level["height"])
    reach = height / math.tan(elevation)
    grazing = max(math.radians(4.0), elevation - 3.0 * sigma)
    penumbra = height / math.tan(grazing) - reach
    return float(level["skirt"]) + reach + penumbra + 2.0


def tile_metrics(config, name):
    level = config["levels"][name]
    radius = float(level["radius"])
    margin = max(float(level["margin"]), required_margin(config, level))
    guard = 2.0 * float(level["height"]) + float(level.get("corner_guard", 2.0))
    slice_css = margin + radius + guard
    span = 2.0 * slice_css + 4.0
    return {
        "radius": radius,
        "margin": margin,
        "guard": guard,
        "slice_css": slice_css,
        "span": span,
        "half_face": span / 2.0 - margin,
        "corner": level.get("corner", "g3"),
    }


def render_level(config, name, scale=None, supersample=None, progress=None, encode=True):
    level, profile, material, ground = resolve_level(config, name)
    metrics = tile_metrics(config, name)
    settings = config["render"]
    scale = int(scale or settings["scale"])
    supersample = int(supersample or settings["supersample"])

    rig = LightRig(config["lighting"])
    field = HeightField(
        metrics["half_face"],
        metrics["half_face"],
        metrics["radius"],
        metrics["corner"],
        profile,
        float(level["skirt"]),
        float(level["height"]),
    )

    pixels = int(round(metrics["span"] * scale * supersample))
    extent = metrics["span"] / 2.0
    axis = (np.arange(pixels) + 0.5) / pixels * metrics["span"] - extent
    grid_x, grid_y = np.meshgrid(axis, axis)

    elevation, nx, ny, nz, on_top, on_skirt, gx, gy, bend = field.surface(
        grid_x, grid_y
    )
    footprint = field.footprint(grid_x, grid_y)

    image = np.empty((pixels, pixels, 3), dtype=np.float64)
    face_color = rig.flat_color(material)
    ground_color = rig.flat_color(ground)
    image[on_top] = face_color
    image[~on_top] = ground_color

    indices = np.flatnonzero((footprint > 0.0).ravel())
    if indices.size:
        snx = nx.ravel()[indices]
        sny = ny.ravel()[indices]
        snz = nz.ravel()[indices]
        outward_x = gx.ravel()[indices]
        outward_y = gy.ravel()[indices]
        ridge, run = field.horizon_slope(footprint.ravel()[indices])
        curl = bend.ravel()[indices]

        slices = int(settings["azimuth_samples"])
        uniform_total = np.zeros_like(ridge)
        graded_total = np.zeros_like(ridge)
        for index in range(slices):
            azimuth = (index + 0.5) / slices * 2.0 * math.pi
            inward = np.maximum(
                -(math.cos(azimuth) * outward_x + math.sin(azimuth) * outward_y), 0.0
            )
            tangent = saddle_correction(ridge, run, curl, inward)
            uniform, graded = rig.sky_moments(snx, sny, snz, tangent, azimuth)
            uniform_total += uniform
            graded_total += graded
            if progress:
                progress(name, "sky", index + 1, slices)

        weight = (2.0 * math.pi / slices) / math.pi
        sky_uniform = uniform_total * weight
        sky_graded = graded_total * weight

        toward_sun = np.maximum(
            -(
                rig.ground_direction[0] * outward_x
                + rig.ground_direction[1] * outward_y
            ),
            0.0,
        )
        coverage = rig.sun_coverage(saddle_correction(ridge, run, curl, toward_sun))
        sun_term = coverage * rig.lambert(snx, sny, snz)

        blend = np.clip(elevation.ravel()[indices] / float(level["height"]), 0.0, 1.0)
        albedo = mix(
            hex_to_linear(ground["albedo"]), hex_to_linear(material["albedo"]), blend
        )
        gloss = lerp(ground["gloss"], material["gloss"], blend)
        strength = lerp(
            ground["specular_strength"], material["specular_strength"], blend
        )
        sheen = coverage * rig.blinn(snx, sny, snz, gloss) * strength
        shaded = rig.compose(sun_term, sky_uniform, sky_graded, sheen, albedo)

        flat_image = image.reshape(-1, 3)
        flat_image[indices] = shaded
        image = flat_image.reshape(pixels, pixels, 3)

    coverage = (footprint <= 0.0).astype(np.float64)
    if supersample > 1:
        reduced = pixels // supersample
        image = image[: reduced * supersample, : reduced * supersample]
        image = image.reshape(reduced, supersample, reduced, supersample, 3).mean(
            axis=(1, 3)
        )
        coverage = coverage[: reduced * supersample, : reduced * supersample]
        coverage = coverage.reshape(reduced, supersample, reduced, supersample).mean(
            axis=(1, 3)
        )

    palette = {"face": face_color, "ground": ground_color, "coverage": coverage}
    if not encode:
        return image, metrics, palette
    encoded = np.clip(np.round(linear_to_srgb(image) * 255.0), 0, 255).astype(np.uint8)
    return encoded, metrics, palette


def render_preview(config, name, scale=1, supersample=1):
    return render_level(config, name, scale, supersample)
