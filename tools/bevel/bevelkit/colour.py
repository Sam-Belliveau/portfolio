from __future__ import annotations

import numpy as np


def srgb_to_linear(colour):
    c = np.asarray(colour, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(colour):
    c = np.clip(np.asarray(colour, dtype=np.float64), 0.0, 1.0)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def hex_to_linear(value):
    text = value.lstrip("#")
    channels = np.array([int(text[i : i + 2], 16) / 255.0 for i in (0, 2, 4)])
    return srgb_to_linear(channels)


def linear_to_hex(colour):
    encoded = np.clip(np.round(linear_to_srgb(colour) * 255.0), 0, 255).astype(int)
    return "#{:02x}{:02x}{:02x}".format(*encoded)
