"""Cutting a nine-slice tile out of a rendered frame.

`border-image` stretches the four edge strips, so whatever is in them has to be
constant along the direction it gets stretched. A path trace is not: it carries
per-pixel noise, and stretching noise smears it into streaks.

The frame is rendered wider than the tile by a run of straight edge, where the
field genuinely is translation-invariant. Averaging along that run is therefore
not a blur -- it is a better estimator of a single number, and it drives the
sampling noise in the strips down by the square root of the run length.

The corner blocks keep their own noise, so they are crossfaded into the averaged
strips across the guard band. That band exists precisely because the corner stops
perturbing the edge there, so the two agree to within noise before they are mixed.
"""

from __future__ import annotations

import numpy as np


def _ramp(size, width):
    width = max(int(width), 1)
    travel = (np.arange(size) - (size - width)) / max(width - 1, 1)
    travel = np.clip(travel, 0.0, 1.0)
    return travel * travel * (3.0 - 2.0 * travel)


def _blend(block, along_rows, along_cols, centre, ramp):
    """Corner block in canonical orientation: index 0 is the tile's outer edge."""
    across = ramp[None, :, None]
    down = ramp[:, None, None]
    return (
        (1.0 - across) * (1.0 - down) * block
        + across * (1.0 - down) * along_rows[:, None, :]
        + (1.0 - across) * down * along_cols[None, :, :]
        + across * down * centre[None, None, :]
    )


def nine_slice(frame, layout, crossfade=0.6, scale=4):
    """Assemble an exactly edge-invariant tile from a rendered frame."""
    cut = layout["slice_pixels"]
    edge = layout["frame_pixels"]
    if frame.shape[0] != edge or frame.shape[1] != edge:
        raise ValueError(f"frame is {frame.shape[:2]}, layout expects {edge}x{edge}")

    top = frame[:cut, cut : edge - cut].mean(axis=1)
    bottom = frame[edge - cut :, cut : edge - cut].mean(axis=1)
    left = frame[cut : edge - cut, :cut].mean(axis=0)
    right = frame[cut : edge - cut, edge - cut :].mean(axis=0)
    centre = frame[cut : edge - cut, cut : edge - cut].mean(axis=(0, 1))

    ramp = _ramp(cut, round(crossfade * layout["guard"] * scale))
    corners = {
        "tl": _blend(frame[:cut, :cut], top, left, centre, ramp),
        "tr": _blend(frame[:cut, edge - cut :][:, ::-1], top, right[::-1], centre, ramp)[
            :, ::-1
        ],
        "bl": _blend(frame[edge - cut :, :cut][::-1], bottom[::-1], left, centre, ramp)[
            ::-1
        ],
        "br": _blend(
            frame[edge - cut :, edge - cut :][::-1, ::-1],
            bottom[::-1],
            right[::-1],
            centre,
            ramp,
        )[::-1, ::-1],
    }

    band = layout["noise_pixels"]
    size = 2 * cut + band
    tile = np.empty((size, size, frame.shape[2]), dtype=np.float64)

    tile[:cut, :cut] = corners["tl"]
    tile[:cut, size - cut :] = corners["tr"]
    tile[size - cut :, :cut] = corners["bl"]
    tile[size - cut :, size - cut :] = corners["br"]

    tile[:cut, cut : size - cut] = top[:, None, :]
    tile[size - cut :, cut : size - cut] = bottom[:, None, :]
    tile[cut : size - cut, :cut] = left[None, :, :]
    tile[cut : size - cut, size - cut :] = right[None, :, :]
    tile[cut : size - cut, cut : size - cut] = centre[None, None, :]

    return tile, centre


def invariance_error(tile, layout):
    """Largest drift along a strip that `border-image` will stretch."""
    cut = layout["slice_pixels"]
    middle = slice(cut, tile.shape[0] - cut)
    rows = tile[:cut, middle]
    columns = tile[middle, :cut]
    return max(
        float(np.abs(rows - rows[:, :1]).max()),
        float(np.abs(columns - columns[:1, :]).max()),
    )
