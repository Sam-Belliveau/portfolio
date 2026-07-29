"""Curve construction.

Every curve on the card is the same idea: a tangent angle that turns through
offset erf steps, integrated as a point travelling around the unit circle.

    theta(s) = sum_k  sweep_k * Phi((s - centre_k) / width)
    curve(s) = integral (cos theta, sin theta) ds

Two shapes, one rule:

    outline        four 90 degree turns   -> a closed rounded rectangle
    cross-section  two 180 degree turns   -> a closed pill

Both close at 360 degrees. Because theta is a sum of Gaussian integrals,
curvature is a sum of Gaussians: smooth everywhere, with no knots to place and
nothing to tune but the width of a turn.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import ndtr

QUARTER = np.pi / 2.0
GAUSSIAN_PEAK = 1.0 / np.sqrt(2.0 * np.pi)

CORNER_SAMPLES = 2048
PROFILE_SAMPLES = 4096


def adaptive_arc(arc, curvature, max_chord, max_turn):
    """Arc positions that spend vertices only where the curve actually bends.

    Two budgets, whichever is tighter: a segment may not turn by more than
    `max_turn` radians, and may not be longer than `max_chord`. Placing samples
    at equal cumulative `max(1/max_chord, curvature/max_turn)` satisfies both at
    once, so a straight run costs two vertices no matter how long it is, while a
    tight corner gets exactly the density its radius demands.

    A segment turning by dt has sagitta ~ dt^2/(8*curvature), so `max_turn` is a
    direct handle on deviation: 2 degrees holds a 64px corner to 0.01px, well
    under a device pixel.
    """
    density = np.maximum(1.0 / max_chord, np.abs(curvature) / max_turn)
    cost = np.concatenate(
        [[0.0], np.cumsum(0.5 * (density[1:] + density[:-1]) * np.diff(arc))]
    )
    count = max(2, int(np.ceil(cost[-1])))
    return np.interp(np.linspace(0.0, cost[-1], count + 1), cost, arc)


def integrate(angle, step):
    forward = np.cos(angle)
    upward = np.sin(angle)
    run = np.concatenate([[0.0], np.cumsum(0.5 * (forward[1:] + forward[:-1]) * step)])
    rise = np.concatenate([[0.0], np.cumsum(0.5 * (upward[1:] + upward[:-1]) * step)])
    return run, rise


class CornerCurve:
    """A single 90 degree turn, sampled at unit speed.

    The tangent angle is -(pi/2)*Phi(s), so curvature is a Gaussian bump that
    decays to nothing at both ends: the straight sections leaving the corner are
    exactly straight, which is what keeps the outline valid to nine-slice.
    """

    def __init__(self, reach=5.0, samples=CORNER_SAMPLES):
        self.reach = float(reach)
        arc = np.linspace(-self.reach, self.reach, samples)
        self.arc = arc - arc[0]
        self.angle = -QUARTER * ndtr(arc)
        self.x, self.y = integrate(self.angle, arc[1] - arc[0])
        self.curvature = QUARTER * GAUSSIAN_PEAK * np.exp(-0.5 * arc * arc)
        self.unit_extent = float(self.x[-1])
        self.tightest_radius = 1.0 / float(self.curvature.max())

    def sample(self, scale, max_chord, max_turn):
        """Corner points and outward normals, spaced by curvature."""
        arc = self.arc * scale
        picks = adaptive_arc(arc, self.curvature / scale, max_chord, max_turn)
        angle = np.interp(picks, arc, self.angle)
        return (
            np.interp(picks, arc, self.x) * scale,
            np.interp(picks, arc, self.y) * scale,
            -np.sin(angle),
            np.cos(angle),
        )

    @property
    def outward(self):
        """Outward unit normal at each sample, the tangent turned a quarter."""
        return -np.sin(self.angle), np.cos(self.angle)

    def extent_for_radius(self, radius):
        """Corner box width whose tightest point matches a circle of `radius`."""
        return float(radius) * self.unit_extent / self.tightest_radius


class Outline:
    """The closed silhouette, as one periodic erf staircase.

    A closed loop's tangent angle has to satisfy theta(s + L) = theta(s) + 2*pi.
    Four isolated 90 degree turns only approximate that: each turn's tails get
    cut off where the straight runs begin, so the runs are not quite straight and
    the joins carry a small kink. Summing every turn over its periodic images
    makes theta exactly periodic instead -- neighbouring corners' tails add where
    they overlap, and the loop closes because the sweep is exactly 2*pi.

    Shape depends only on the ratio of turn width to period. Widen the turns
    relative to the period and the steps merge, tightening the loop towards a
    circle; narrow them and the straight runs reappear. So the ratio is solved
    for the requested corner radius, and the period then sets the size.
    """

    TURNS = 4

    def __init__(self, half, radius, reach=3.0, samples=4096, images=2):
        self.half = float(half)
        self.radius = float(radius)
        self.reach = float(reach)
        self.samples = int(samples)
        self.images = int(images)

        low, high = 1e-4, 1.0
        for _ in range(80):
            width = 0.5 * (low + high)
            self._trace(width)
            if self.unit_radius / self.unit_half < self.radius / self.half:
                low = width
            else:
                high = width
        self._trace(high)

        self.period = self.half / self.unit_half
        self.x = self.unit_x * self.period
        self.y = self.unit_y * self.period
        self.arc = self.unit_arc * self.period
        self.curvature = self.unit_curvature / self.period

    def _trace(self, width):
        travel = np.linspace(0.0, 1.0, self.samples)
        angle = np.zeros_like(travel)
        rate = np.zeros_like(travel)
        for turn in range(self.TURNS):
            centre = (turn + 0.5) / self.TURNS
            for image in range(-self.images, self.images + 1):
                offset = (travel - centre - image) / width
                angle += QUARTER * ndtr(offset)
                rate += QUARTER * GAUSSIAN_PEAK * np.exp(-0.5 * offset * offset) / width

        angle -= angle[0]
        x, y = integrate(angle, travel[1] - travel[0])
        self.unit_x = x - 0.5 * (x.max() + x.min())
        self.unit_y = y - 0.5 * (y.max() + y.min())
        self.unit_angle = angle
        self.unit_arc = travel
        self.unit_curvature = rate
        self.unit_half = 0.25 * (
            x.max() - x.min() + y.max() - y.min()
        )
        self.unit_radius = 1.0 / float(rate.max())

    @property
    def clip_radius(self):
        """The circular `border-radius` that best matches this silhouette.

        CSS rounds a corner with a circular arc, and this corner is not one --
        its curvature rises and falls, so it starts turning earlier and more
        gently than a circle of the same tightest radius. Clipping with that
        tightest radius therefore leaves the arc several pixels outside the real
        outline. Fitting on shape instead of on curvature cuts the worst error
        by roughly five.

        Only worth the fit once a surface carries a colour of its own: that is
        when the clip stops being invisible and becomes the edge between two
        papers.
        """
        x, y = np.abs(self.x), np.abs(self.y)
        half = 0.5 * (x.max() + y.max())

        def worst(corner):
            centre = half - corner
            arc = np.hypot(np.maximum(x - centre, 0.0), np.maximum(y - centre, 0.0))
            turning = (x > centre) & (y > centre)
            return np.abs(
                np.where(turning, arc - corner, np.maximum(x, y) - half)
            ).max()

        return float(minimize_scalar(worst, bounds=(0.0, half), method="bounded").x)

    def sample(self, max_chord, max_turn):
        """Loop points and outward normals, spaced by curvature."""
        picks = adaptive_arc(self.arc, self.curvature, max_chord, max_turn)[:-1]
        angle = np.interp(picks, self.arc, self.unit_angle)
        return (
            np.stack(
                [
                    np.interp(picks, self.arc, self.x),
                    np.interp(picks, self.arc, self.y),
                ],
                axis=1,
            ),
            np.stack([np.sin(angle), -np.cos(angle)], axis=1),
        )


class Profile:
    """One end of the card's cross-section: a 180 degree turn.

    The full cross-section is a closed pill -- two flat faces joined by two 180
    degree turns -- exactly as the outline is a closed rounded rectangle made of
    four 90 degree ones. A nine-slice tile only ever needs one of those two
    ends, so this is a single turn, scaled so the card is `2*height` thick.

    The solid therefore closes instead of stopping at the floor, and the ground
    plane slices through it. That is what makes contact occlusion behave: the
    card meets the ground as a real solid rather than as an infinitely thin
    sheet ending at the plane.

    `reach` is the only shape knob, in standard deviations. It trades how
    tightly the turn is concentrated against how flat it has arrived by the time
    it meets the top face: small reach gives a compact bevel with a visible kink
    at the join, large reach a wide one that arrives perfectly flat. `bevel` is
    the result, not an input -- how far the turn travels horizontally.
    """

    def __init__(self, height, reach=5.0, samples=PROFILE_SAMPLES):
        self.height = float(height)
        self.reach = max(0.5, float(reach))

        arc = np.linspace(-self.reach, self.reach, samples)
        self.angle = -np.pi * ndtr(arc)
        run, rise = integrate(self.angle, arc[1] - arc[0])

        scale = 2.0 * self.height / max(float(rise[0] - rise[-1]), 1e-12)
        self.arc = (arc - arc[0]) * scale
        self.run = run * scale
        self.rise = self.height + rise * scale
        self.curvature = np.pi * GAUSSIAN_PEAK * np.exp(-0.5 * arc * arc) / scale
        self.bevel = float(self.run.max())
        self.join = float(abs(np.degrees(self.angle[0])))

    def rings(self, max_chord, max_turn):
        """Cross-section rings, spaced by curvature, top face first.

        Each ring is an inward offset of the base outline by `inset`, lifted to
        `rise`, carrying the tangent angle so the surface normal is analytic
        rather than inferred from the tessellation. The straight wall costs two
        rings however tall it is; the round-overs get the density they need.
        """
        picks = adaptive_arc(self.arc, self.curvature, max_chord, max_turn)
        return (
            self.bevel - np.interp(picks, self.arc, self.run),
            np.interp(picks, self.arc, self.rise),
            np.interp(picks, self.arc, self.angle),
        )
