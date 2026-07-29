"""Blue-noise dithering, sized to survive the browser rescaling the tile.

Eight bits over a bevel this shallow bands visibly, so the quantisation error is
pushed into the frequencies the eye is worst at. The matrix is built by void-and-
cluster, and `cell` upsamples it so the pattern still reads as noise after a
device pixel ratio that is not a whole number scales the tile down.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter

MATRIX_SIZE = 32
SIGMA = 1.9


def _energy(binary):
    return gaussian_filter(binary.astype(np.float64), SIGMA, mode="wrap").ravel()


def blue_noise_matrix(size=MATRIX_SIZE, seed=17):
    total = size * size
    rng = np.random.default_rng(seed)
    binary = np.zeros(total, dtype=bool)
    binary[rng.choice(total, max(1, total // 10), replace=False)] = True

    while True:
        ones = np.flatnonzero(binary)
        tight = ones[np.argmax(_energy(binary.reshape(size, size))[ones])]
        binary[tight] = False
        zeros = np.flatnonzero(~binary)
        void = zeros[np.argmin(_energy(binary.reshape(size, size))[zeros])]
        if void == tight:
            binary[tight] = True
            break
        binary[void] = True

    prototype = binary.copy()
    rank = np.full(total, -1, dtype=np.int64)

    work = prototype.copy()
    for level in range(int(work.sum()) - 1, -1, -1):
        ones = np.flatnonzero(work)
        tight = ones[np.argmax(_energy(work.reshape(size, size))[ones])]
        work[tight] = False
        rank[tight] = level

    work = prototype.copy()
    for level in range(int(work.sum()), total):
        zeros = np.flatnonzero(~work)
        void = zeros[np.argmin(_energy(work.reshape(size, size))[zeros])]
        work[void] = True
        rank[void] = level

    return ((rank + 0.5) / total).reshape(size, size)


_CACHE = {}


def threshold_field(shape, cell=2, seed=17):
    matrix = _CACHE.setdefault(seed, blue_noise_matrix(seed=seed))
    size = matrix.shape[0]
    rows = (np.arange(shape[0]) // max(1, cell)) % size
    columns = (np.arange(shape[1]) // max(1, cell)) % size
    return matrix[np.ix_(rows, columns)]


def quantise(values, render):
    """Round to eight bits with a blue-noise threshold."""
    cell = int(render["dither_cell"])
    field = threshold_field(values.shape, cell)
    if values.ndim == 3:
        field = field[..., None]
    return np.clip(np.floor(values + field), 0, 255).astype(np.uint8)
