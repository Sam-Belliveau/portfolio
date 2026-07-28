from __future__ import annotations

from copy import deepcopy

import ipywidgets as widgets
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import display

from .config import default_config, load_config, save_config
from .emit import write_tiles
from .preview import (
    plot_curvature,
    plot_normals,
    plot_profile,
    render_once,
    show_mockup,
    show_tile,
)
from .profile import EdgeProfile
from .render import resolve_level

SLIDER = {"continuous_update": False, "style": {"description_width": "110px"}}
WIDE = widgets.Layout(width="330px")


def _points_to_text(points):
    return "\n".join(f"{x:.5f}, {y:.5f}" for x, y in points)


def _text_to_points(text):
    rows = []
    for line in text.strip().splitlines():
        if not line.strip():
            continue
        x, y = line.split(",")
        rows.append([float(x), float(y)])
    return rows


class BevelStudio:
    def __init__(self, config=None):
        self.saved = deepcopy(config or load_config())
        self.working = deepcopy(self.saved)
        self.level = list(self.working["levels"].keys())[0]
        self.curves = widgets.Output()
        self.tiles = widgets.Output()
        self.status = widgets.HTML()
        self._build()

    def _build(self):
        levels = list(self.working["levels"].keys())
        self.level_picker = widgets.ToggleButtons(
            options=levels, value=self.level, description="Level"
        )
        self.level_picker.observe(self._switch_level, names="value")

        self.profile_picker = widgets.Dropdown(
            options=list(self.working["profiles"].keys()), description="Profile", layout=WIDE
        )
        self.material_picker = widgets.Dropdown(
            options=list(self.working["materials"].keys()), description="Material", layout=WIDE
        )
        self.ground_picker = widgets.Dropdown(
            options=list(self.working["materials"].keys()), description="Rests on", layout=WIDE
        )
        self.corner_picker = widgets.Dropdown(
            options=["g3", "circular"], description="Corner", layout=WIDE
        )
        self.radius = widgets.FloatSlider(
            min=0.0, max=48.0, step=0.5, description="Corner radius", layout=WIDE, **SLIDER
        )
        self.height = widgets.FloatSlider(
            min=0.5, max=28.0, step=0.5, description="Height", layout=WIDE, **SLIDER
        )
        self.skirt = widgets.FloatSlider(
            min=0.5, max=32.0, step=0.5, description="Skirt width", layout=WIDE, **SLIDER
        )
        self.margin = widgets.FloatSlider(
            min=4.0, max=64.0, step=1.0, description="Tile margin", layout=WIDE, **SLIDER
        )

        self.points = widgets.Textarea(
            description="Control pts", layout=widgets.Layout(width="330px", height="150px")
        )
        self.start_slope = widgets.FloatSlider(
            min=-8.0, max=0.0, step=0.05, description="Rim slope", layout=WIDE, **SLIDER
        )
        self.end_slope = widgets.FloatSlider(
            min=-4.0, max=0.0, step=0.05, description="Base slope", layout=WIDE, **SLIDER
        )
        self.continuity = widgets.Dropdown(
            options=["G3", "G2", "G1"], description="Continuity", layout=WIDE
        )

        self.albedo = widgets.ColorPicker(description="Albedo", layout=WIDE)
        self.specular = widgets.FloatSlider(
            min=0.0, max=0.6, step=0.01, description="Specular", layout=WIDE, **SLIDER
        )
        self.gloss = widgets.FloatSlider(
            min=2.0, max=80.0, step=1.0, description="Gloss", layout=WIDE, **SLIDER
        )

        self.sun_azimuth = widgets.FloatSlider(
            min=0.0, max=360.0, step=5.0, description="Sun azimuth", layout=WIDE, **SLIDER
        )
        self.sun_elevation = widgets.FloatSlider(
            min=5.0, max=89.0, step=1.0, description="Sun elevation", layout=WIDE, **SLIDER
        )
        self.sun_falloff = widgets.Dropdown(
            options=["gaussian", "disk"], description="Sun falloff", layout=WIDE
        )
        self.sun_size = widgets.FloatSlider(
            min=0.1, max=30.0, step=0.1, description="Disk radius°", layout=WIDE, **SLIDER
        )
        self.sun_sigma = widgets.FloatSlider(
            min=0.1, max=40.0, step=0.1, description="Gaussian σ°", layout=WIDE, **SLIDER
        )
        self.sun_color = widgets.ColorPicker(description="Sun color", layout=WIDE)
        self.sky_color = widgets.ColorPicker(description="Sky color", layout=WIDE)
        self.sky_strength = widgets.FloatSlider(
            min=0.0, max=0.8, step=0.01, description="Sky strength", layout=WIDE, **SLIDER
        )

        self.save_button = widgets.Button(description="Save config", button_style="primary")
        self.reset_button = widgets.Button(description="Reset to saved")
        self.factory_button = widgets.Button(description="Restore defaults")
        self.preview_button = widgets.Button(description="Preview tile")
        self.auto_preview = widgets.Checkbox(
            value=False, description="Auto preview", indent=False,
            layout=widgets.Layout(width="140px"),
        )
        self.render_button = widgets.Button(description="Render tiles", button_style="success")
        self.preview_button.on_click(lambda _: self._draw_tile())
        self.save_button.on_click(self._save)
        self.reset_button.on_click(self._reset)
        self.factory_button.on_click(self._factory)
        self.render_button.on_click(self._render_tiles)

        self.editors = [
            self.profile_picker, self.material_picker, self.ground_picker,
            self.corner_picker, self.radius, self.height, self.skirt, self.margin,
            self.points, self.start_slope, self.end_slope, self.continuity,
            self.albedo, self.specular, self.gloss,
            self.sun_azimuth, self.sun_elevation, self.sun_falloff, self.sun_size,
            self.sun_sigma, self.sun_color, self.sky_color, self.sky_strength,
        ]
        self._load_level()
        for widget in self.editors:
            widget.observe(self._apply, names="value")

        geometry = widgets.VBox(
            [widgets.HTML("<b>Level geometry</b>"), self.corner_picker, self.radius,
             self.height, self.skirt, self.margin, self.profile_picker]
        )
        edge = widgets.VBox(
            [widgets.HTML("<b>Edge profile</b>"), self.continuity, self.start_slope,
             self.end_slope, self.points]
        )
        surface = widgets.VBox(
            [widgets.HTML("<b>Material</b>"), self.material_picker, self.ground_picker,
             self.albedo, self.specular, self.gloss]
        )
        light = widgets.VBox(
            [widgets.HTML("<b>Lighting</b>"), self.sun_azimuth, self.sun_elevation,
             self.sun_falloff, self.sun_size, self.sun_sigma, self.sun_color,
             self.sky_color, self.sky_strength]
        )
        self.panel = widgets.VBox([
            self.level_picker,
            widgets.HBox([geometry, edge, surface, light]),
            self.status,
            self.curves,
            widgets.HBox([self.preview_button, self.auto_preview, self.save_button,
                          self.reset_button, self.factory_button, self.render_button]),
            self.tiles,
        ])

    def _level(self):
        return self.working["levels"][self.level]

    def _profile_spec(self):
        return self.working["profiles"][self._level()["profile"]]

    def _material(self):
        return self.working["materials"][self._level()["material"]]

    def _load_level(self):
        self._loading = True
        level = self._level()
        self.profile_picker.value = level["profile"]
        self.material_picker.value = level["material"]
        self.ground_picker.value = level.get("ground", "page")
        self.corner_picker.value = level.get("corner", "g3")
        self.radius.value = level["radius"]
        self.height.value = level["height"]
        self.skirt.value = level["skirt"]
        self.margin.value = level["margin"]

        spec = self._profile_spec()
        self.points.value = _points_to_text(spec["points"])
        self.start_slope.value = spec.get("start_slope", -2.0)
        self.end_slope.value = spec.get("end_slope", 0.0)
        self.continuity.value = spec.get("continuity", "G3")

        material = self._material()
        self.albedo.value = material["albedo"]
        self.specular.value = material["specular_strength"]
        self.gloss.value = material["gloss"]

        sun = self.working["lighting"]["sun"]
        sky = self.working["lighting"]["sky"]
        self.sun_azimuth.value = sun["azimuth"]
        self.sun_elevation.value = sun["elevation"]
        self.sun_falloff.value = sun.get("falloff", "gaussian")
        self.sun_size.value = sun["angular_radius"]
        self.sun_sigma.value = sun.get("angular_sigma", 6.0)
        self.sun_color.value = sun["color"]
        self.sky_color.value = sky["color"]
        self.sky_strength.value = sky["strength"]
        self._loading = False

    def _switch_level(self, change):
        self.level = change["new"]
        self._load_level()
        self._draw_curves()

    def _apply(self, change=None):
        if getattr(self, "_loading", False):
            return
        level = self._level()
        level["profile"] = self.profile_picker.value
        level["material"] = self.material_picker.value
        level["ground"] = self.ground_picker.value
        level["corner"] = self.corner_picker.value
        level["radius"] = self.radius.value
        level["height"] = self.height.value
        level["skirt"] = self.skirt.value
        level["margin"] = self.margin.value

        spec = self._profile_spec()
        try:
            spec["points"] = _text_to_points(self.points.value)
        except ValueError:
            self.status.value = "<b style='color:#9c1c1c'>control points must be 'x, y' per line</b>"
            return
        spec["start_slope"] = self.start_slope.value
        spec["end_slope"] = self.end_slope.value
        spec["continuity"] = self.continuity.value

        material = self._material()
        material["albedo"] = self.albedo.value
        material["specular_strength"] = self.specular.value
        material["gloss"] = self.gloss.value

        self.working["lighting"]["sun"].update(
            azimuth=self.sun_azimuth.value,
            elevation=self.sun_elevation.value,
            falloff=self.sun_falloff.value,
            angular_radius=self.sun_size.value,
            angular_sigma=self.sun_sigma.value,
            color=self.sun_color.value,
        )
        self.working["lighting"]["sky"].update(
            color=self.sky_color.value, strength=self.sky_strength.value
        )
        self._draw_curves()
        if self.auto_preview.value:
            self._draw_tile()

    def _draw_curves(self):
        with self.curves:
            self.curves.clear_output(wait=True)
            try:
                level, profile, _, _ = resolve_level(self.working, self.level)
            except Exception as error:
                print(f"profile error: {error}")
                return
            figure, panes = plt.subplots(1, 3, figsize=(13.5, 3.6))
            plot_profile(profile, panes[0], label=level["profile"])
            panes[0].set_title(f"{self.level} edge profile")
            plot_curvature(
                profile, panes[1], skirt=level["skirt"], height=level["height"]
            )
            panes[1].set_title("curvature")
            plot_normals(self.working, self.level, panes[2])
            figure.tight_layout()
            plt.show()
            self._report(profile)

    def _draw_tile(self):
        with self.tiles:
            self.tiles.clear_output(wait=True)
            try:
                image, metrics = render_once(self.working, self.level)
            except Exception as error:
                print(f"render error: {error}")
                return
            figure, panes = plt.subplots(1, 2, figsize=(9, 4.4))
            show_tile(image, metrics, panes[0], title=f"{self.level} tile")
            show_mockup(image, metrics, panes[1])
            figure.tight_layout()
            plt.show()

    def _report(self, profile):
        level = self._level()
        _, curvature = profile.surface_curvature(level["skirt"], level["height"])
        jump = float(np.abs(np.diff(curvature)).max())
        flags = []
        if not profile.is_monotone():
            flags.append("non-monotone height")
        if profile.overshoot() > 1e-6:
            flags.append(f"overshoot {profile.overshoot():.3f}")
        note = "; ".join(flags) if flags else "monotone, no overshoot"
        self.status.value = (
            f"continuity {profile.continuity} &middot; max curvature step "
            f"{jump:.4f} &middot; {note}"
        )

    def _save(self, _):
        save_config(self.working)
        self.saved = deepcopy(self.working)
        self.status.value = "<b>saved to config.json</b>"

    def _reset(self, _):
        self.working = deepcopy(self.saved)
        self._load_level()
        self._draw_curves()
        self.status.value = "reverted to last saved config"

    def _factory(self, _):
        self.working = default_config()
        self._load_level()
        self._draw_curves()
        self.status.value = "restored built-in defaults (not yet saved)"

    def _render_tiles(self, _):
        self.status.value = "rendering tiles…"
        path = write_tiles(self.working)
        self.status.value = f"<b>wrote tiles and {path.name}</b>"

    def show(self):
        display(self.panel)
        self._draw_curves()
        self._draw_tile()
        return self


def launch(config=None):
    return BevelStudio(config).show()
