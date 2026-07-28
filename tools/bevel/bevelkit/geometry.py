from __future__ import annotations

import numpy as np

from .corner import make_corner
from .horizon import sample_table, tangent_table


class HeightField:
    def __init__(
        self,
        half_x,
        half_y,
        extent,
        corner_style,
        profile,
        skirt,
        height,
        table_size=4096,
    ):
        self.corner = make_corner(corner_style, half_x, half_y, extent)
        self.profile = profile
        self.skirt = float(skirt)
        self.height = float(height)
        self.table = profile.height(np.linspace(0.0, 1.0, table_size)) * self.height
        self.last_index = table_size - 1
        self.table_scale = self.last_index / self.skirt
        self.horizon, self.horizon_runs, self.horizon_limit = tangent_table(
            profile, skirt, height
        )

    def footprint(self, x, y):
        return self.corner.distance(x, y)

    def elevation_at(self, footprint):
        position = np.clip(footprint * self.table_scale, 0.0, self.last_index)
        index = position.astype(np.int32)
        blend = position - index
        lower = self.table[index]
        upper = self.table[np.minimum(index + 1, self.last_index)]
        return lower + (upper - lower) * blend

    def elevation(self, x, y):
        return self.elevation_at(self.footprint(x, y))

    def horizon_slope(self, footprint):
        return sample_table(
            self.horizon, self.horizon_runs, self.horizon_limit, footprint, self.height
        )

    def surface(self, x, y):
        footprint = self.footprint(x, y)
        nx, ny = self.corner.direction(x, y)
        boundary_bend = self.corner.curvature(x, y)
        on_top = footprint <= 0.0
        on_skirt = (footprint > 0.0) & (footprint < self.skirt)
        parameter = np.clip(footprint / self.skirt, 0.0, 1.0)
        value, slope = self.profile.evaluate(parameter)
        radial = -slope * (self.height / self.skirt)
        scale = 1.0 / np.sqrt(radial * radial + 1.0)
        elevation = np.where(
            on_top, self.height, np.where(on_skirt, value * self.height, 0.0)
        )
        return (
            elevation,
            np.where(on_skirt, nx * radial * scale, 0.0),
            np.where(on_skirt, ny * radial * scale, 0.0),
            np.where(on_skirt, scale, 1.0),
            on_top,
            on_skirt,
            nx,
            ny,
            boundary_bend / (1.0 + np.maximum(footprint, 0.0) * boundary_bend),
        )
