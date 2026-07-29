"""Tile geometry: how big to render, and where to cut.

A nine-slice tile is `span` on a side and cuts at `slice_css` from each edge:

    slice_css = margin + extent + guard

`margin` is how far the shadow reaches past the card, so the tile carries its
own shadow and CSS never has to leave room for one. `extent` is the corner box.
`guard` is the part of the straight edge the corner still perturbs -- slicing
inside it would stretch corner shading down the whole side.

The render frame is wider than the tile by `strip`, a run of straight edge in
the middle of each side. Nothing is cut from there: it is averaged along its
length to recover an exactly translation-invariant edge profile, which is what
`border-image` needs when it stretches those strips.

    frame = 2*slice_css + strip
    span  = 2*slice_css + noise
"""

from __future__ import annotations

import math

from .dither import MATRIX_SIZE
from .shape import CornerCurve, Outline, Profile


def shadow_margin(config, height):
    """How far light still changes past the card's edge.

    The cast shadow ends at `height / tan(elevation)`, its penumbra at the sun's
    lower limb, and the ambient gradient fades over roughly a card height. The
    tile carries all three, so CSS never has to leave room for a shadow.
    """
    sky = config["sky"]
    elevation = math.radians(float(sky["sun_elevation"]))
    radius = math.radians(float(sky["sun_size"]) / 2.0)
    reach = height / math.tan(elevation)
    grazing = max(math.radians(4.0), elevation - radius)
    penumbra = height / math.tan(grazing) - reach
    ambient = float(config["render"]["ambient_margin"]) * height
    return reach + penumbra + ambient + 2.0


def card_thickness(radius, reach, curvature):
    """Half-thickness, set by how much tighter the edge turns than the corner.

    `curvature` is the ratio of the cross-section's tightest curvature to the
    plan corner's. At 1 the two are equal, so a single sphere of that radius
    sits tangent to both and the corner is a spherical fillet -- which is the
    thickest a card can sensibly be, because past it the edge would be flatter
    than the corner it has to turn through. Above 1 the edge is tighter and the
    card thinner, in exact proportion: 2 is half as thick.

    Thickness is therefore never chosen directly. It follows the radius, and the
    card stays one shape scaled by it.
    """
    tangent = float(radius) * float(Profile(1.0, reach).curvature.max())
    return tangent / max(float(curvature), 1e-6)


def tile_layout(config, radius):
    surface = config["surface"]
    render = config["render"]

    reach = float(surface["reach"])
    corner = CornerCurve(reach)

    # "cut" slices the pill through its equator, so the top face sits at one
    # thickness and the wall drops straight into the plane. "rest" stands the
    # whole pill on the plane instead, putting the top face at two and rounding
    # over underneath; it is sunk a hair in so the solid genuinely intersects the
    # ground rather than meeting it coplanar, which would leak light along the
    # seam.
    resting = str(surface.get("seat", "cut")) == "rest"
    thickness = card_thickness(radius, reach, surface["curvature"])
    profile = Profile(thickness, reach)
    height = 2.0 * thickness if resting else thickness
    lift = thickness - 0.02 * height if resting else 0.0

    extent = corner.extent_for_radius(float(radius))
    margin = shadow_margin(config, height)
    # The corner's curvature is a Gaussian, so its influence on the straight run
    # decays like one and the guard is honestly measured in its standard
    # deviations rather than guessed from the thickness. Scaling the corner to a
    # radius scales that sigma with it, so the guard stays proportional and the
    # whole tile keeps one knob.
    guard = float(surface["guard_sigma"]) * float(radius) / corner.tightest_radius
    scale = int(render["scale"])

    slice_pixels = int(round((margin + extent + guard) * scale))
    strip_pixels = max(int(round(float(render["strip"]) * scale)), 2 * scale)
    # The browser round-repeats the middle band, so it holds a whole number of
    # blue-noise tiles or the dither seams where the repeats meet.
    noise_pixels = MATRIX_SIZE * int(render["dither_cell"])
    frame_pixels = 2 * slice_pixels + strip_pixels

    # The finished tile is cropped to `tile_pixels`, taken off the outside where
    # the shadow has already faded to nothing. Cropping there costs no shading
    # and moves both the slice and the outset in by the same amount, so the card
    # still lands exactly on the element's edge.
    trim_pixels = max(0, (2 * slice_pixels + noise_pixels - int(render["tile_pixels"])) // 2)
    cut_pixels = slice_pixels - trim_pixels

    half_face = frame_pixels / scale / 2.0 - margin
    outline = Outline(half_face, float(radius), reach)
    return {
        "corner": corner,
        "outline": outline,
        "profile": profile,
        "padding": float(radius),
        "clip_radius": outline.clip_radius,
        "lift": lift,
        "extent": extent,
        "margin": margin,
        "guard": guard,
        "bevel": profile.bevel,
        "profile_radius": 1.0 / float(profile.curvature.max()),
        "slice_css": slice_pixels / scale,
        "slice_pixels": slice_pixels,
        "trim_pixels": trim_pixels,
        "cut_pixels": cut_pixels,
        "cut_css": cut_pixels / scale,
        "outset_css": margin - trim_pixels / scale,
        "tile_pixels": 2 * cut_pixels + noise_pixels,
        "noise_pixels": noise_pixels,
        "frame_pixels": frame_pixels,
        "frame_css": frame_pixels / scale,
        "span_css": (2 * slice_pixels + noise_pixels) / scale,
        "half_face": half_face,
    }
