from __future__ import annotations

import numpy as np

HULL_SAMPLES = 1024
TABLE_SAMPLES = 1024


def reach(skirt, height):
    return float(skirt + 16.0 * height)


def tangent_table(profile, skirt, height, samples=TABLE_SAMPLES, hull=HULL_SAMPLES):
    limit = reach(skirt, height)
    ridge = np.linspace(0.0, skirt, hull)
    ridge_height = profile.height(ridge / skirt) * height

    query = np.linspace(0.0, limit, samples)
    query_height = np.where(
        query <= skirt, profile.height(np.clip(query / skirt, 0.0, 1.0)) * height, 0.0
    )

    run = query[:, None] - ridge[None, :]
    rise = ridge_height[None, :] - query_height[:, None]
    slope = np.where(run > 1e-9, rise / np.where(run > 1e-9, run, 1.0), -np.inf)
    touch = slope.argmax(axis=1)
    table = np.maximum(slope.max(axis=1), 0.0)
    runs = np.where(table > 0.0, query - ridge[touch], 0.0)
    table[0] = 0.0
    runs[0] = 0.0
    return table, runs, limit


def _lookup(table, limit, footprint):
    position = np.clip(footprint / limit, 0.0, 1.0) * (table.size - 1)
    index = position.astype(np.int32)
    blend = position - index
    lower = table[index]
    upper = table[np.minimum(index + 1, table.size - 1)]
    return lower + (upper - lower) * blend


def sample_table(table, runs, limit, footprint, height):
    beyond = footprint > limit
    inside = footprint <= 0.0
    slope = np.where(
        inside, 0.0,
        np.where(beyond, height / np.maximum(footprint, 1e-6), _lookup(table, limit, footprint)),
    )
    run = np.where(
        inside, 0.0, np.where(beyond, footprint, _lookup(runs, limit, footprint))
    )
    return slope, run


def saddle_correction(slope, run, bend, inward):
    squared = np.maximum(inward * inward, 1e-6)
    stretch = 1.0 + 0.5 * run * bend * (1.0 - squared) / squared
    return inward * slope / stretch
