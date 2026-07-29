"""The card as a mesh, lofted from the curves that define it.

One ring per step of the cross-section integral. Each ring is the silhouette
*tightened* -- its corner radius is parameterised directly and the spacing
between the erf turns is searched for, rather than the loop being pushed inward
by a distance. That distinction is the whole point: offsetting by a distance
runs the corner radius to zero and then through it, folding the curve, while
choosing the radius cannot cross zero however deep the ring goes.

Holding the radius proportional to the ring's size makes the rings similar, so
the search collapses to a single scale and the same family closes the flat faces
as well -- one construction from the silhouette all the way to the centre.
"""

from __future__ import annotations

import numpy as np


def card_mesh(layout, max_chord=6.0, max_turn=0.035, cap_rings=10):
    """Vertices, faces and split normals for one card.

    A closed solid: the pill's own bottom caps it, well below the ground plane
    that slices the wall, so nothing leaks along the contact seam.
    """
    profile = layout["profile"]
    loop, _ = layout["outline"].sample(max_chord, max_turn)
    count = loop.shape[0]
    half = layout["half_face"]

    inset, rise, _ = profile.rings(max_chord, max_turn)

    # Every ring is the base loop tightened, not offset: the corner radius is
    # held proportional to the ring's size, so the search for the erf spacing
    # always converges and the radius approaches zero without ever crossing it.
    # Proportional tightening makes the rings similar, so the whole solve
    # collapses to a scale.
    shrink = (half - inset) / half
    cap = np.linspace(shrink[0], 0.0, cap_rings + 2)[1:-1]

    scale = np.concatenate([cap[::-1], shrink, cap * shrink[-1] / max(shrink[0], 1e-9)])
    height = np.concatenate(
        [np.full(cap.size, rise[0]), rise, np.full(cap.size, rise[-1])]
    )

    positions = np.empty((scale.size, count, 3))
    positions[:, :, :2] = loop[None, :, :] * scale[:, None, None]
    positions[:, :, 2] = height[:, None] + layout["lift"]

    # The rings are no longer a constant offset apart, so the profile's tangent
    # angle is not the surface normal any more. Take it from the surface: the
    # ring tangent crossed with the across-ring tangent.
    along = np.roll(positions, -1, axis=1) - np.roll(positions, 1, axis=1)
    across = np.gradient(positions, axis=0)
    normals = np.cross(along, across)
    lengths = np.linalg.norm(normals, axis=2, keepdims=True)
    normals = normals / np.maximum(lengths, 1e-12)
    if normals[len(cap), :, 2].mean() < 0.0:
        normals = -normals

    vertices = positions.reshape(-1, 3)
    split = normals.reshape(-1, 3)

    here = np.arange(count)
    nxt = (here + 1) % count
    rows = vertices.shape[0] // count
    band = np.arange(rows - 1) * count
    quads = np.stack(
        [
            (band[:, None] + here[None, :]),
            (band[:, None] + count + here[None, :]),
            (band[:, None] + count + nxt[None, :]),
            (band[:, None] + nxt[None, :]),
        ],
        axis=2,
    ).reshape(-1, 4)

    # Whatever is left in the middle is small enough that its triangulation
    # cannot matter: one n-gon per face, at the innermost ring.
    last = (rows - 1) * count
    caps = np.stack([here, (last + here)[::-1]])

    return {
        "vertices": vertices.astype(np.float32),
        "normals": split.astype(np.float32),
        "quads": quads.astype(np.int32),
        "caps": caps.astype(np.int32),
    }


def ground_mesh(reach):
    span = float(reach)
    vertices = np.array(
        [[-span, -span, 0.0], [span, -span, 0.0], [span, span, 0.0], [-span, span, 0.0]]
    )
    return {
        "vertices": vertices.astype(np.float32),
        "normals": np.tile([0.0, 0.0, 1.0], (4, 1)).astype(np.float32),
        "quads": np.array([[0, 1, 2, 3]], dtype=np.int32),
        "caps": np.zeros((0, 4), dtype=np.int32),
    }
