"""Runs inside Blender: `blender -b -P blender_scene.py -- job.json`.

Builds one scene -- physical sky, paper surface, orthographic camera straight
down -- and renders every frame in the job from it. The camera is orthographic
so the render *is* the tile: world units are CSS pixels, and `ortho_scale` set
to the frame size makes pixel centres land exactly where the layout says.

Renders are written as linear OpenEXR and then read back out to .npy, so the
host never needs an EXR reader and nothing passes through a view transform.
"""

import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def enable_gpu():
    preferences = bpy.context.preferences.addons["cycles"].preferences
    for backend in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
        try:
            preferences.compute_device_type = backend
        except TypeError:
            continue
        preferences.get_devices()
        usable = [d for d in preferences.devices if d.type != "CPU"]
        if usable:
            for device in preferences.devices:
                device.use = True
            return backend
    return "CPU"


def socket(node, *names):
    for name in names:
        if name in node.inputs:
            return node.inputs[name]
    return None


def assign(node, value, *names):
    found = socket(node, *names)
    if found is not None:
        found.default_value = value
    return found


def paper_material(spec, name="paper", diffuse_only=False):
    """A matte, slightly translucent paper surface.

    Paper is diffuse-dominant with a weak wide specular lobe, a sheen from
    surface fibres at grazing angles, and enough subsurface transport to glow
    where the bevel thins.

    Deliberately uniform: no grain, no roughness blotching. A nine-slice tile
    stretches its edge strips, so anything varying across the surface would be
    averaged out of the strips and survive only in the corners. Fibre texture
    belongs in a page-wide overlay, not baked into the tile.

    `diffuse_only` keeps everything that scales with base colour -- the diffuse
    lobe and subsurface -- and drops only specular and sheen. Subsurface has to
    stay: Principled *substitutes* it for part of the diffuse lobe rather than
    adding to it, so removing it would make `beauty - diffuse` a redistribution
    instead of the pure specular term the lighten layer needs.
    """
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()

    output = tree.nodes.new("ShaderNodeOutputMaterial")
    principled = tree.nodes.new("ShaderNodeBsdfPrincipled")
    tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    assign(principled, tuple(spec["base_color"]) + (1.0,), "Base Color")
    assign(principled, 0.0, "Metallic")
    assign(principled, float(spec["roughness"]), "Roughness")
    assign(principled, float(spec["ior"]), "IOR")

    strength = 0.0 if diffuse_only else 1.0
    assign(
        principled,
        strength * float(spec["specular"]),
        "Specular IOR Level",
        "Specular",
    )
    assign(principled, strength * float(spec["sheen"]), "Sheen Weight", "Sheen")
    assign(principled, float(spec["sheen_roughness"]), "Sheen Roughness")
    assign(principled, float(spec["subsurface"]), "Subsurface Weight", "Subsurface")
    radius = float(spec["subsurface_radius"])
    assign(principled, (radius, radius * 0.92, radius * 0.82), "Subsurface Radius")
    assign(principled, radius, "Subsurface Scale")

    return material


def configure(target, **values):
    """Set what this Blender build actually exposes, skip what it does not."""
    for name, value in values.items():
        if hasattr(target, name):
            try:
                setattr(target, name, value)
            except (TypeError, AttributeError) as error:
                print(f"  skipped {name}={value!r}: {error}")


def physical_sky(spec):
    """A real atmosphere: sun and sky come from one scattering model.

    The sun stays in the sky texture rather than being a separate lamp, so the
    disc, its limb and the sky it lights are all the same physical solution
    instead of two things tuned to agree.
    """
    world = bpy.data.worlds.new("sky")
    world.use_nodes = True
    tree = world.node_tree
    tree.nodes.clear()

    output = tree.nodes.new("ShaderNodeOutputWorld")
    background = tree.nodes.new("ShaderNodeBackground")
    background.inputs["Strength"].default_value = float(spec["strength"])
    tree.links.new(background.outputs["Background"], output.inputs["Surface"])

    sky = tree.nodes.new("ShaderNodeTexSky")
    sky.sky_type = spec["model"]
    configure(
        sky,
        sun_elevation=math.radians(float(spec["sun_elevation"])),
        sun_rotation=math.radians(float(spec["sun_azimuth"]) + 90.0),
        sun_size=math.radians(float(spec["sun_size"])),
        sun_intensity=float(spec["sun_intensity"]),
        sun_disc=bool(spec["sun_disc"]),
        altitude=float(spec["altitude"]),
        air_density=float(spec["air_density"]),
        aerosol_density=float(spec["aerosol_density"]),
        ozone_density=float(spec["ozone_density"]),
        ground_albedo=float(spec["ground_albedo"]),
    )
    tree.links.new(sky.outputs["Color"], background.inputs["Color"])

    configure(world.cycles, sample_map_resolution=2048)
    return world, sky


def build_object(name, payload, material):
    vertices = payload["vertices"].astype(np.float64)
    faces = [tuple(int(i) for i in face) for face in payload["quads"]]
    faces += [tuple(int(i) for i in face) for face in payload["caps"]]

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(v) for v in vertices], [], faces)
    mesh.update()
    for polygon in mesh.polygons:
        polygon.use_smooth = True

    normals = payload["normals"].astype(np.float64)
    try:
        mesh.normals_split_custom_set_from_vertices(
            [tuple(n) for n in normals[: len(mesh.vertices)]]
        )
    except Exception as error:  # pragma: no cover - Blender version drift
        print(f"  custom normals unavailable ({error}); using smooth shading")

    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(material)
    bpy.context.collection.objects.link(obj)
    return obj


def sun_lamp(spec):
    """A real sun lamp, aimed by the config's azimuth and elevation."""
    data = bpy.data.lights.new("sun", type="SUN")
    data.angle = math.radians(float(spec["sun_size"]))
    lamp = bpy.data.objects.new("sun", data)
    bpy.context.collection.objects.link(lamp)

    azimuth = math.radians(float(spec["sun_azimuth"]))
    elevation = math.radians(float(spec["sun_elevation"]))
    # World +Y is the top of the frame, so the image convention's +y-down
    # azimuth flips sign here. At 225 degrees the light lands top-left.
    toward = Vector(
        (
            math.cos(azimuth) * math.cos(elevation),
            -math.sin(azimuth) * math.cos(elevation),
            math.sin(elevation),
        )
    ).normalized()
    lamp.rotation_euler = (-toward).to_track_quat("-Z", "Y").to_euler()
    return lamp


def calibrate_sun(scene, sky, lamp, probe):
    """Match the lamp to the sun the sky model would have drawn.

    A half-degree disc sitting in the environment map is the worst case for
    importance sampling -- it is a handful of texels carrying five orders of
    magnitude more radiance than its neighbours, and it fireflies badly in
    exactly the shadowed regions this bevel is made of. A sun lamp is sampled
    analytically instead, at zero variance.

    Keeping it physical rather than tuned: light transport is linear in the
    source, so rendering bare ground three ways isolates each term exactly.

        gain = (sky_with_disc - sky_alone) / (unit_lamp - sky_alone)
    """

    def flat(disc, energy):
        sky.sun_disc = disc
        lamp.data.energy = energy
        scene.render.filepath = probe
        bpy.ops.render.render(write_still=True)
        pixels = read_render(probe, scene.render.resolution_x, scene.render.resolution_y)
        return pixels[..., :3].mean(axis=(0, 1)).astype(np.float64)

    full = flat(True, 0.0)
    ambient = flat(False, 0.0)
    unit = flat(False, 1.0)

    gain = (full - ambient) / np.maximum(unit - ambient, 1e-9)
    peak = float(max(gain.max(), 1e-9))
    lamp.data.color = tuple(np.clip(gain / peak, 0.0, 1.0))
    lamp.data.energy = peak
    sky.sun_disc = False

    print(
        f"  sun calibrated: irradiance {peak:.3f}"
        f"  colour {np.round(gain / peak, 4).tolist()}"
        f"  (sky {np.round(ambient, 3).tolist()})",
        flush=True,
    )
    return gain


def export_model(mesh_path, glb_path, material):
    """The card as glTF, with the plane that slices it.

    The card is a whole pill, so half of it sits below the ground. Exporting the
    slicing plane with it is what makes the model legible -- otherwise you are
    looking at a closed lozenge and cannot tell which half is the card.
    """
    payload = dict(np.load(mesh_path))
    card = build_object("card", payload, material)

    reach = float(np.abs(payload["vertices"][:, :2]).max()) * 1.35
    plane = build_object("ground", ground_payload(reach), material)

    try:
        bpy.ops.object.select_all(action="DESELECT")
        card.select_set(True)
        plane.select_set(True)
        bpy.ops.export_scene.gltf(
            filepath=str(glb_path),
            export_format="GLB",
            use_selection=True,
            export_normals=True,
            export_apply=False,
        )
        print(f"  model {Path(glb_path).name}", flush=True)
    except Exception as error:  # pragma: no cover - exporter availability
        print(f"  glTF export unavailable ({error})")
    finally:
        bpy.data.objects.remove(card, do_unlink=True)
        bpy.data.objects.remove(plane, do_unlink=True)


def ground_payload(reach):
    corners = np.array(
        [[-reach, -reach, 0.0], [reach, -reach, 0.0], [reach, reach, 0.0], [-reach, reach, 0.0]]
    )
    return {
        "vertices": corners.astype(np.float32),
        "normals": np.tile([0.0, 0.0, 1.0], (4, 1)).astype(np.float32),
        "quads": np.array([[0, 1, 2, 3]], dtype=np.int32),
        "caps": np.zeros((0, 4), dtype=np.int32),
    }


def read_render(path, width, height):
    image = bpy.data.images.load(str(path))
    image.colorspace_settings.name = "Non-Color"
    buffer = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(buffer)
    bpy.data.images.remove(image)
    return buffer.reshape(height, width, 4)[::-1]


def main():
    arguments = sys.argv[sys.argv.index("--") + 1 :]
    job = json.loads(open(arguments[0]).read())

    clear()
    backend = enable_gpu()
    print(f"cycles backend: {backend}")

    bounces = int(job["bounces"])
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    configure(
        scene.cycles,
        device="GPU",
        use_adaptive_sampling=True,
        adaptive_threshold=float(job["adaptive_threshold"]),
        use_denoising=True,
        denoiser="OPENIMAGEDENOISE",
        denoising_input_passes="RGB_ALBEDO_NORMAL",
        max_bounces=bounces,
        diffuse_bounces=bounces,
        glossy_bounces=bounces,
        transmission_bounces=bounces,
        caustics_reflective=False,
        caustics_refractive=False,
        blur_glossy=0.0,
        sample_clamp_indirect=0.0,
        # Cycles reads its own filter width; render.filter_size is inert here.
        filter_width=float(job["filter_width"]),
    )

    configure(scene.view_settings, view_transform="Standard", look="None")
    configure(
        scene.render.image_settings,
        file_format="OPEN_EXR",
        color_mode="RGBA",
        color_depth="32",
        exr_codec="ZIP",
    )
    configure(
        scene.render,
        resolution_percentage=100,
        filter_size=float(job["filter_width"]),
        dither_intensity=0.0,
    )

    scene.world, sky = physical_sky(job["sky"])
    materials = {
        "beauty": paper_material(job["paper"], "paper"),
        "diffuse": paper_material(job["paper"], "paper-diffuse", diffuse_only=True),
    }

    camera_data = bpy.data.cameras.new("camera")
    camera_data.type = "ORTHO"
    camera_data.clip_start = 1.0
    camera_data.clip_end = 1.0e6
    camera = bpy.data.objects.new("camera", camera_data)
    camera.location = (0.0, 0.0, 1.0e4)
    camera.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera

    for entry in job["models"]:
        export_model(entry["mesh"], entry["glb"], materials["beauty"])

    if not job["frames"]:
        print("scene done", flush=True)
        return

    ground = build_object("ground", dict(np.load(job["ground"])), materials["beauty"])

    lamp = sun_lamp(job["sky"])
    camera_data.ortho_scale = 8.0
    scene.render.resolution_x = scene.render.resolution_y = 16
    scene.cycles.samples = 512
    calibrate_sun(scene, sky, lamp, job["probe"])

    for frame in job["frames"]:
        size = float(frame["size"])
        resolution = int(frame["resolution"])
        camera_data.ortho_scale = size
        scene.render.resolution_x = resolution
        scene.render.resolution_y = resolution
        scene.cycles.samples = int(frame["samples"])

        mask = frame["kind"] == "mask"
        scene.render.film_transparent = mask
        scene.cycles.use_denoising = not mask
        ground.hide_render = mask

        material = materials["diffuse" if frame["kind"] == "diffuse" else "beauty"]
        ground.data.materials[0] = material

        card = None
        if frame.get("mesh"):
            card = build_object(frame["name"], dict(np.load(frame["mesh"])), material)

        scene.render.filepath = frame["exr"]
        print(f"  render {frame['name']} ({frame['kind']}) {resolution}px", flush=True)
        bpy.ops.render.render(write_still=True)

        pixels = read_render(frame["exr"], resolution, resolution)
        np.save(frame["output"], pixels)

        if card is not None:
            bpy.data.objects.remove(card, do_unlink=True)

    print("scene done", flush=True)


if __name__ == "__main__":
    main()
