from __future__ import annotations

import numpy as np
from scipy.interpolate import CubicHermiteSpline, make_interp_spline

CONTINUITY_ORDERS = {"G1": 1, "G2": 2, "G3": 3}


class EdgeProfile:
    def __init__(self, points, start_slope=None, end_slope=0.0, continuity="G3"):
        ordered = sorted((float(x), float(y)) for x, y in points)
        self.x = np.array([p[0] for p in ordered], dtype=np.float64)
        self.y = np.array([p[1] for p in ordered], dtype=np.float64)
        if self.x.size < 2:
            raise ValueError("an edge profile needs at least two control points")
        if np.any(np.diff(self.x) <= 0):
            raise ValueError("control point x values must be strictly increasing")

        self.continuity = continuity if continuity in CONTINUITY_ORDERS else "G1"
        self.start_slope = self._default_start(start_slope)
        self.end_slope = float(end_slope)

        if self.continuity == "G1":
            self._build_monotone_cubic()
        else:
            self._build_quintic()

    @classmethod
    def from_dict(cls, spec):
        return cls(
            spec["points"],
            spec.get("start_slope"),
            spec.get("end_slope", 0.0),
            spec.get("continuity", "G3"),
        )

    def to_dict(self):
        return {
            "points": [[float(x), float(y)] for x, y in zip(self.x, self.y)],
            "start_slope": self.start_slope,
            "end_slope": self.end_slope,
            "continuity": self.continuity,
        }

    def _default_start(self, start_slope):
        if start_slope is not None:
            return float(start_slope)
        return float((self.y[1] - self.y[0]) / (self.x[1] - self.x[0]))

    def _build_quintic(self):
        order = CONTINUITY_ORDERS[self.continuity]
        left = [(1, self.start_slope)]
        right = [(1, self.end_slope)]
        for derivative in range(2, order + 1):
            right.append((derivative, 0.0))
        while len(left) + len(right) < 4:
            left.append((len(left) + 1, 0.0))
        self.spline = make_interp_spline(
            self.x, self.y, k=5, bc_type=(left, right[: 4 - len(left)])
        )
        self.slope_spline = self.spline.derivative()

    def _build_monotone_cubic(self):
        spans = np.diff(self.x)
        secants = np.diff(self.y) / spans
        tangents = np.zeros(self.x.size)
        tangents[0] = self.start_slope
        tangents[-1] = self.end_slope
        for i in range(1, self.x.size - 1):
            left, right = secants[i - 1], secants[i]
            if left * right <= 0:
                tangents[i] = 0.0
            else:
                wa = 2 * spans[i] + spans[i - 1]
                wb = spans[i] + 2 * spans[i - 1]
                tangents[i] = (wa + wb) / (wa / left + wb / right)
        self.spline = CubicHermiteSpline(self.x, self.y, tangents)
        self.slope_spline = self.spline.derivative()

    def evaluate(self, x):
        clamped = np.clip(np.asarray(x, dtype=np.float64), self.x[0], self.x[-1])
        return self.spline(clamped), self.slope_spline(clamped)

    def height(self, x):
        return self.evaluate(x)[0]

    def slope(self, x):
        return self.evaluate(x)[1]

    def curvature(self, x, skirt=1.0, height=1.0):
        clamped = np.clip(np.asarray(x, dtype=np.float64), self.x[0], self.x[-1])
        first = self.slope_spline(clamped) * (height / skirt)
        second = self.spline.derivative(2)(clamped) * (height / (skirt * skirt))
        return second / np.power(1.0 + first * first, 1.5)

    def arclength(self, x, skirt=1.0, height=1.0):
        clamped = np.clip(np.asarray(x, dtype=np.float64), self.x[0], self.x[-1])
        slope = self.slope_spline(clamped) * (height / skirt)
        speed = skirt * np.sqrt(1.0 + slope * slope)
        steps = np.diff(clamped)
        segments = 0.5 * (speed[1:] + speed[:-1]) * steps
        return np.concatenate([[0.0], np.cumsum(segments)])

    def surface_curvature(self, skirt, height, count=400):
        xs = np.linspace(0.0, 1.0, count)
        return self.arclength(xs, skirt, height), self.curvature(xs, skirt, height)

    def sample(self, count=256):
        xs = np.linspace(0.0, 1.0, count)
        return xs, self.height(xs)

    def silhouette(self, skirt, height, segments):
        xs = np.linspace(0.0, 1.0, max(2, segments))
        return np.stack([xs * skirt, self.height(xs) * height], axis=1)

    def is_monotone(self):
        _, ys = self.sample(1024)
        return bool(np.all(np.diff(ys) <= 1e-9))

    def overshoot(self):
        _, ys = self.sample(1024)
        return float(max(0.0, ys.max() - 1.0) + max(0.0, -ys.min()))
