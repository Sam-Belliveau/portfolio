from __future__ import annotations

import numpy as np

CURVE_SAMPLES = 1536
CHUNK = 4096


def _unit_corner(samples=CURVE_SAMPLES):
    s = np.linspace(0.0, np.pi, samples)
    angle = s / 2.0 - np.sin(2.0 * s) / 4.0
    dx = np.cos(angle)
    dy = -np.sin(angle)
    x = np.concatenate([[0.0], np.cumsum((dx[1:] + dx[:-1]) * 0.5 * np.diff(s))])
    y = np.concatenate([[0.0], np.cumsum((dy[1:] + dy[:-1]) * 0.5 * np.diff(s))])
    return x, y


UNIT_X, UNIT_Y = _unit_corner()
UNIT_EXTENT = float(UNIT_X[-1])


def corner_curvature_profile(samples=CURVE_SAMPLES):
    s = np.linspace(0.0, np.pi, samples)
    return s / np.pi, np.sin(s) ** 2


class CircularCorner:
    style = "circular"

    def __init__(self, half_x, half_y, extent):
        self.half_x = float(half_x)
        self.half_y = float(half_y)
        self.extent = float(extent)

    def distance(self, x, y):
        qx = np.abs(x) - (self.half_x - self.extent)
        qy = np.abs(y) - (self.half_y - self.extent)
        outside = np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0))
        inside = np.minimum(np.maximum(qx, qy), 0.0)
        return outside + inside - self.extent

    def curvature(self, x, y):
        qx = np.abs(x) - (self.half_x - self.extent)
        qy = np.abs(y) - (self.half_y - self.extent)
        return np.where((qx > 0.0) & (qy > 0.0), 1.0 / self.extent, 0.0)

    def direction(self, x, y):
        qx = np.abs(x) - (self.half_x - self.extent)
        qy = np.abs(y) - (self.half_y - self.extent)
        gx = np.sign(x) * np.maximum(qx, 0.0)
        gy = np.sign(y) * np.maximum(qy, 0.0)
        length = np.hypot(gx, gy)
        on_face = length < 1e-9
        fallback_x = np.where(qx >= qy, np.sign(x), 0.0)
        fallback_y = np.where(qx >= qy, 0.0, np.sign(y))
        safe = np.where(on_face, 1.0, length)
        return (
            np.where(on_face, fallback_x, gx / safe),
            np.where(on_face, fallback_y, gy / safe),
        )


class ContinuousCorner:
    style = "g3"

    def __init__(self, half_x, half_y, extent):
        self.half_x = float(half_x)
        self.half_y = float(half_y)
        self.extent = float(extent)
        scale = self.extent / UNIT_EXTENT
        self.curve = np.stack(
            [
                self.half_x - self.extent + UNIT_X * scale,
                self.half_y + UNIT_Y * scale,
            ],
            axis=1,
        )
        edges = np.diff(self.curve, axis=0)
        lengths = np.hypot(edges[:, 0], edges[:, 1])
        self.starts = self.curve[:-1]
        self.edges = edges
        self.lengths_squared = lengths**2
        self.normals = np.stack([-edges[:, 1], edges[:, 0]], axis=1) / lengths[:, None]
        arc = np.linspace(0.0, np.pi, self.curve.shape[0])
        self.segment_curvature = (np.sin(arc) ** 2 / scale)[:-1]
        self.peak_curvature = np.pi / (2.0 * self.extent / UNIT_EXTENT) / np.pi

    def _corner_solve(self, px, py):
        distance = np.empty(px.shape)
        dir_x = np.empty(px.shape)
        dir_y = np.empty(px.shape)
        bend = np.empty(px.shape)
        for begin in range(0, px.size, CHUNK):
            stop = min(begin + CHUNK, px.size)
            qx = px[begin:stop, None]
            qy = py[begin:stop, None]
            wx = qx - self.starts[None, :, 0]
            wy = qy - self.starts[None, :, 1]
            t = np.clip(
                (wx * self.edges[None, :, 0] + wy * self.edges[None, :, 1])
                / self.lengths_squared[None, :],
                0.0,
                1.0,
            )
            cx = self.starts[None, :, 0] + self.edges[None, :, 0] * t
            cy = self.starts[None, :, 1] + self.edges[None, :, 1] * t
            dx = qx - cx
            dy = qy - cy
            squared = dx * dx + dy * dy
            nearest = np.argmin(squared, axis=1)
            rows = np.arange(stop - begin)
            offset_x = dx[rows, nearest]
            offset_y = dy[rows, nearest]
            magnitude = np.hypot(offset_x, offset_y)
            normal_x = self.normals[nearest, 0]
            normal_y = self.normals[nearest, 1]
            side = np.sign(offset_x * normal_x + offset_y * normal_y)
            side = np.where(side == 0.0, 1.0, side)
            degenerate = magnitude < 1e-9
            bend[begin:stop] = self.segment_curvature[nearest]
            distance[begin:stop] = side * magnitude
            dir_x[begin:stop] = np.where(
                degenerate, normal_x, side * offset_x / np.where(degenerate, 1.0, magnitude)
            )
            dir_y[begin:stop] = np.where(
                degenerate, normal_y, side * offset_y / np.where(degenerate, 1.0, magnitude)
            )
        return distance, dir_x, dir_y, bend

    def _solve(self, x, y):
        ax = np.abs(x)
        ay = np.abs(y)
        inner_x = self.half_x - self.extent
        inner_y = self.half_y - self.extent
        in_corner = (ax > inner_x) & (ay > inner_y)

        distance = np.maximum(ax - self.half_x, ay - self.half_y)
        dir_x = np.where(ax - self.half_x >= ay - self.half_y, 1.0, 0.0)
        dir_y = 1.0 - dir_x
        bend = np.zeros(ax.shape)

        if np.any(in_corner):
            flat = np.flatnonzero(in_corner.ravel())
            solved, sdx, sdy, sbend = self._corner_solve(
                ax.ravel()[flat], ay.ravel()[flat]
            )
            distance = distance.ravel()
            dir_x = np.broadcast_to(dir_x, ax.shape).astype(np.float64).ravel()
            dir_y = np.broadcast_to(dir_y, ax.shape).astype(np.float64).ravel()
            bend = bend.ravel()
            distance[flat] = solved
            dir_x[flat] = sdx
            dir_y[flat] = sdy
            bend[flat] = sbend
            distance = distance.reshape(ax.shape)
            dir_x = dir_x.reshape(ax.shape)
            dir_y = dir_y.reshape(ax.shape)
            bend = bend.reshape(ax.shape)

        return distance, dir_x * np.sign(x), dir_y * np.sign(y), bend

    def distance(self, x, y):
        return self._solve(x, y)[0]

    def direction(self, x, y):
        _, dx, dy, _ = self._solve(x, y)
        return dx, dy

    def curvature(self, x, y):
        return self._solve(x, y)[3]


def make_corner(style, half_x, half_y, extent):
    if style == "circular":
        return CircularCorner(half_x, half_y, extent)
    return ContinuousCorner(half_x, half_y, extent)
