from __future__ import annotations

import math

import numpy as np
from scipy.special import ndtr

VIEW = np.array([0.0, 0.0, 1.0])


def srgb_to_linear(color):
    c = np.asarray(color, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(color):
    c = np.clip(np.asarray(color, dtype=np.float64), 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def hex_to_linear(value):
    text = value.lstrip("#")
    channels = np.array([int(text[i : i + 2], 16) / 255.0 for i in (0, 2, 4)])
    return srgb_to_linear(channels)


def linear_to_hex(color):
    encoded = np.clip(np.round(linear_to_srgb(color) * 255.0), 0, 255).astype(int)
    return "#{:02x}{:02x}{:02x}".format(*encoded)


def disk_fraction(offset):
    clamped = np.clip(offset, -1.0, 1.0)
    return (
        np.arccos(-clamped) + clamped * np.sqrt(np.maximum(0.0, 1.0 - clamped**2))
    ) / math.pi


def gaussian_fraction(offset):
    return ndtr(offset)


class LightRig:
    def __init__(self, lighting):
        sun = lighting["sun"]
        sky = lighting["sky"]
        self.azimuth = math.radians(sun["azimuth"])
        self.elevation = math.radians(sun["elevation"])
        self.angular_radius = max(1e-4, math.radians(sun["angular_radius"]))
        self.angular_sigma = max(1e-4, math.radians(sun.get("angular_sigma", 6.0)))
        self.falloff = sun.get("falloff", "gaussian")
        self.ground_direction = (math.cos(self.azimuth), math.sin(self.azimuth))
        self.direction = np.array(
            [
                self.ground_direction[0] * math.cos(self.elevation),
                self.ground_direction[1] * math.cos(self.elevation),
                math.sin(self.elevation),
            ]
        )
        self.half_vector = (self.direction + VIEW) / np.linalg.norm(
            self.direction + VIEW
        )
        self.sun_color = hex_to_linear(sun["color"])
        fallback = sky.get("color", "#a9c8ea")
        self.sky_horizon = hex_to_linear(sky.get("horizon_color", fallback))
        self.sky_zenith = hex_to_linear(sky.get("zenith_color", fallback))
        self.sky_gradient = self.sky_zenith - self.sky_horizon
        self.sky_strength = float(sky["strength"])
        self.flat_sun = math.sin(self.elevation)
        self.flat_sky = self.sky_horizon + (2.0 / 3.0) * self.sky_gradient
        self.sun_gain = (1.0 - self.sky_strength * self.flat_sky) / (
            self.flat_sun * self.sun_color
        )

    def sky_moments(self, nx, ny, nz, horizon_tangent, azimuth):
        along = nx * math.cos(azimuth) + ny * math.sin(azimuth)
        occluded = np.arctan(np.maximum(horizon_tangent, 0.0))
        self_shadow = np.arctan2(np.maximum(0.0, -along), np.maximum(nz, 1e-9))
        lower = np.maximum(occluded, self_shadow)
        cosine = np.cos(lower)
        sine = np.sin(lower)
        uniform = along * (
            math.pi / 4.0 - lower / 2.0 - np.sin(2.0 * lower) / 4.0
        ) + 0.5 * nz * cosine**2
        graded = (along * cosine**3 + nz * (1.0 - sine**3)) / 3.0
        blocked = lower >= math.pi / 2.0 - 1e-6
        return (
            np.where(blocked, 0.0, np.maximum(uniform, 0.0)),
            np.where(blocked, 0.0, np.maximum(graded, 0.0)),
        )

    def sun_coverage(self, horizon_tangent):
        clearance = self.elevation - np.arctan(np.maximum(horizon_tangent, 0.0))
        if self.falloff == "disk":
            return disk_fraction(clearance / self.angular_radius)
        return gaussian_fraction(clearance / self.angular_sigma)

    def lambert(self, nx, ny, nz):
        return np.maximum(
            0.0,
            nx * self.direction[0] + ny * self.direction[1] + nz * self.direction[2],
        )

    def blinn(self, nx, ny, nz, gloss):
        aligned = np.maximum(
            0.0,
            nx * self.half_vector[0]
            + ny * self.half_vector[1]
            + nz * self.half_vector[2],
        )
        return aligned**gloss

    def flat_color(self, material):
        albedo = hex_to_linear(material["albedo"])
        sheen = material["specular_strength"] * (
            float(VIEW @ self.half_vector) ** material["gloss"]
        )
        return albedo + sheen * self.sun_color

    def compose(self, sun_term, sky_uniform, sky_graded, sheen, albedo):
        albedo = np.asarray(albedo, dtype=np.float64)
        if albedo.ndim == 1:
            albedo = np.broadcast_to(albedo, sun_term.shape + (3,))
        radiance = np.empty(sun_term.shape + (3,), dtype=np.float64)
        for channel in range(3):
            direct = self.sun_gain[channel] * self.sun_color[channel] * sun_term
            ambient = self.sky_strength * (
                self.sky_horizon[channel] * sky_uniform
                + self.sky_gradient[channel] * sky_graded
            )
            radiance[..., channel] = (
                albedo[..., channel] * (direct + ambient)
                + sheen * self.sun_color[channel]
            )
        return radiance
