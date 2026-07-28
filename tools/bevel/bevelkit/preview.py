from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from .profile import EdgeProfile
from .render import render_preview, resolve_level, tile_metrics


def plot_profile(profile, axes=None, label=None):
    axes = axes or plt.gca()
    xs, ys = profile.sample(400)
    axes.plot(xs, ys, linewidth=2.0, label=label)
    axes.plot(profile.x, profile.y, "o", markersize=6, color="#9c1c1c")
    axes.set_xlabel("outward distance  u / skirt")
    axes.set_ylabel("height  z / level height")
    axes.set_xlim(-0.02, 1.02)
    axes.set_ylim(-0.05, 1.05)
    axes.grid(alpha=0.25)
    axes.invert_xaxis()
    return axes


def plot_curvature(profile, axes=None, label=None, skirt=1.0, height=1.0):
    axes = axes or plt.gca()
    arc, curvature = profile.surface_curvature(skirt, height)
    axes.plot(arc, curvature, linewidth=2.0, label=label)
    axes.axhline(0.0, color="#8a867d", linewidth=0.8)
    axes.set_xlabel("arc length from rim (px)")
    axes.set_ylabel("signed curvature (1/px)")
    axes.grid(alpha=0.25)
    return axes


def plot_cross_section(config, name, axes=None):
    level, profile, _, _ = resolve_level(config, name)
    axes = axes or plt.gca()
    skirt = float(level["skirt"])
    height = float(level["height"])
    xs, ys = profile.sample(400)
    axes.fill_between(
        np.concatenate([[-skirt], xs * skirt]),
        np.concatenate([[height], ys * height]),
        0.0,
        color="#d9d5cc",
        edgecolor="#2a2823",
        linewidth=1.5,
    )
    axes.axhline(0.0, color="#8a867d", linewidth=1.0)
    axes.set_aspect("equal")
    axes.set_xlabel("u (px)")
    axes.set_ylabel("z (px)")
    axes.set_title(f"{name}: skirt {skirt:g}px, height {height:g}px")
    axes.grid(alpha=0.2)
    return axes


def plot_normals(config, name, axes=None, arrows=18):
    level, profile, _, _ = resolve_level(config, name)
    axes = axes or plt.gca()
    skirt = float(level["skirt"])
    height = float(level["height"])
    t = np.linspace(0.02, 0.98, arrows)
    value, slope = profile.evaluate(t)
    radial = -slope * (height / skirt)
    scale = 1.0 / np.sqrt(radial * radial + 1.0)
    plot_cross_section(config, name, axes)
    axes.quiver(
        t * skirt,
        value * height,
        radial * scale,
        scale,
        color="#9c1c1c",
        scale=14,
        width=0.005,
    )
    return axes


def render_once(config, name, scale=1, supersample=1):
    image, metrics, _ = render_preview(config, name, scale, supersample)
    return image, metrics


def show_tile(image, metrics=None, axes=None, title=None):
    axes = axes or plt.gca()
    axes.imshow(image)
    axes.set_title(title or f"tile — {image.shape[1]}×{image.shape[0]}px")
    axes.axis("off")
    return axes


def show_mockup(image, metrics, axes=None, scale=1):
    inset = int(round(metrics["slice_css"] * scale))
    top = image[:inset]
    bottom = image[-inset:]
    stretched = np.repeat(image[inset : inset + 1], inset, axis=0)
    stacked = np.concatenate([top, stretched, bottom], axis=0)

    left = stacked[:, :inset]
    right = stacked[:, -inset:]
    widened = np.repeat(stacked[:, inset : inset + 1], inset * 3, axis=1)
    composed = np.concatenate([left, widened, right], axis=1)

    axes = axes or plt.gca()
    axes.imshow(composed)
    axes.set_title("stretched via 9-slice")
    axes.axis("off")
    return axes


def compare_profiles(config, names=None, axes=None):
    axes = axes or plt.gca()
    for key in names or list(config["profiles"].keys()):
        plot_profile(EdgeProfile.from_dict(config["profiles"][key]), axes, label=key)
    axes.legend(fontsize=8)
    return axes


def studio_figure(config, name, scale=1, supersample=1):
    figure, panes = plt.subplots(1, 4, figsize=(17, 3.8))
    level, profile, _, _ = resolve_level(config, name)
    plot_profile(profile, panes[0], label=level["profile"])
    panes[0].set_title(f"{name} edge profile")
    plot_curvature(profile, panes[1], skirt=level["skirt"], height=level["height"])
    plot_normals(config, name, panes[2])
    image, metrics = render_once(config, name, scale, supersample)
    show_tile(image, metrics, panes[3])
    figure.tight_layout()
    return figure
