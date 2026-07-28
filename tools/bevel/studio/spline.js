const basis = {
  value(t) {
    const t2 = t * t, t3 = t2 * t, t4 = t3 * t, t5 = t4 * t;
    return [
      1 - 10 * t3 + 15 * t4 - 6 * t5,
      t - 6 * t3 + 8 * t4 - 3 * t5,
      0.5 * t2 - 1.5 * t3 + 1.5 * t4 - 0.5 * t5,
      10 * t3 - 15 * t4 + 6 * t5,
      -4 * t3 + 7 * t4 - 3 * t5,
      0.5 * t3 - t4 + 0.5 * t5,
    ];
  },
  slope(t) {
    const t2 = t * t, t3 = t2 * t, t4 = t3 * t;
    return [
      -30 * t2 + 60 * t3 - 30 * t4,
      1 - 18 * t2 + 32 * t3 - 15 * t4,
      t - 4.5 * t2 + 6 * t3 - 2.5 * t4,
      30 * t2 - 60 * t3 + 30 * t4,
      -12 * t2 + 28 * t3 - 15 * t4,
      1.5 * t2 - 4 * t3 + 2.5 * t4,
    ];
  },
  curvature(t) {
    const t2 = t * t, t3 = t2 * t;
    return [
      -60 * t + 180 * t2 - 120 * t3,
      -36 * t + 96 * t2 - 60 * t3,
      1 - 9 * t + 18 * t2 - 10 * t3,
      60 * t - 180 * t2 + 120 * t3,
      -24 * t + 84 * t2 - 60 * t3,
      3 * t - 12 * t2 + 10 * t3,
    ];
  },
  third(t) {
    const t2 = t * t;
    return [
      -60 + 360 * t - 360 * t2,
      -36 + 192 * t - 180 * t2,
      -9 + 36 * t - 30 * t2,
      60 - 360 * t + 360 * t2,
      -24 + 168 * t - 180 * t2,
      3 - 24 * t + 30 * t2,
    ];
  },
  fourth(t) {
    return [360 - 720 * t, 192 - 360 * t, 36 - 60 * t, -360 + 720 * t, 168 - 360 * t, -24 + 60 * t];
  },
};

function solve(matrix, rhs) {
  const n = rhs.length;
  const a = matrix.map((row, i) => [...row, rhs[i]]);
  for (let col = 0; col < n; col += 1) {
    let pivot = col;
    for (let row = col + 1; row < n; row += 1) {
      if (Math.abs(a[row][col]) > Math.abs(a[pivot][col])) pivot = row;
    }
    [a[col], a[pivot]] = [a[pivot], a[col]];
    const lead = a[col][col];
    if (Math.abs(lead) < 1e-14) continue;
    for (let row = 0; row < n; row += 1) {
      if (row === col) continue;
      const factor = a[row][col] / lead;
      if (factor === 0) continue;
      for (let k = col; k <= n; k += 1) a[row][k] -= factor * a[col][k];
    }
  }
  return a.map((row, i) => row[n] / a[i][i]);
}

function fritschCarlson(xs, ys, startSlope, endSlope) {
  const n = xs.length;
  const spans = [];
  const secants = [];
  for (let i = 0; i < n - 1; i += 1) {
    spans.push(xs[i + 1] - xs[i]);
    secants.push((ys[i + 1] - ys[i]) / spans[i]);
  }
  const tangents = new Array(n).fill(0);
  tangents[0] = startSlope;
  tangents[n - 1] = endSlope;
  for (let i = 1; i < n - 1; i += 1) {
    const left = secants[i - 1];
    const right = secants[i];
    if (left * right <= 0) {
      tangents[i] = 0;
    } else {
      const wa = 2 * spans[i] + spans[i - 1];
      const wb = spans[i] + 2 * spans[i - 1];
      tangents[i] = (wa + wb) / (wa / left + wb / right);
    }
  }
  return { tangents, curvatures: new Array(n).fill(null), spans, cubic: true };
}

function quinticC4(xs, ys, startSlope, endSlope, continuity) {
  const n = xs.length;
  const spans = [];
  for (let i = 0; i < n - 1; i += 1) spans.push(xs[i + 1] - xs[i]);

  const size = 2 * n;
  const matrix = Array.from({ length: size }, () => new Array(size).fill(0));
  const rhs = new Array(size).fill(0);
  const D = (i) => i;
  const S = (i) => n + i;

  const addInterval = (row, interval, coefficients, order, sign) => {
    const h = spans[interval];
    const scale = sign / Math.pow(h, order);
    matrix[row][D(interval)] += scale * h * coefficients[1];
    matrix[row][S(interval)] += scale * h * h * coefficients[2];
    matrix[row][D(interval + 1)] += scale * h * coefficients[4];
    matrix[row][S(interval + 1)] += scale * h * h * coefficients[5];
    rhs[row] -= scale * (ys[interval] * coefficients[0] + ys[interval + 1] * coefficients[3]);
  };

  let row = 0;
  for (let knot = 1; knot < n - 1; knot += 1) {
    addInterval(row, knot - 1, basis.third(1), 3, 1);
    addInterval(row, knot, basis.third(0), 3, -1);
    row += 1;
    addInterval(row, knot - 1, basis.fourth(1), 4, 1);
    addInterval(row, knot, basis.fourth(0), 4, -1);
    row += 1;
  }

  matrix[row][D(0)] = 1;
  rhs[row] = startSlope;
  row += 1;
  matrix[row][D(n - 1)] = 1;
  rhs[row] = endSlope;
  row += 1;

  if (continuity === 'G3') {
    matrix[row][S(n - 1)] = 1;
    rhs[row] = 0;
    row += 1;
    addInterval(row, n - 2, basis.third(1), 3, 1);
    row += 1;
  } else {
    matrix[row][S(0)] = 1;
    rhs[row] = 0;
    row += 1;
    matrix[row][S(n - 1)] = 1;
    rhs[row] = 0;
    row += 1;
  }

  const solution = solve(matrix, rhs);
  return {
    tangents: solution.slice(0, n),
    curvatures: solution.slice(n),
    spans,
    cubic: false,
  };
}

export class EdgeProfile {
  constructor(points, startSlope, endSlope, continuity = 'G3') {
    const ordered = [...points].sort((a, b) => a[0] - b[0]);
    this.x = ordered.map((p) => p[0]);
    this.y = ordered.map((p) => p[1]);
    this.continuity = continuity;
    this.startSlope = startSlope;
    this.endSlope = endSlope;
    const fitted =
      continuity === 'G1'
        ? fritschCarlson(this.x, this.y, startSlope, endSlope)
        : quinticC4(this.x, this.y, startSlope, endSlope, continuity);
    Object.assign(this, fitted);
  }

  segment(x) {
    let i = this.spans.length - 1;
    while (i > 0 && x < this.x[i]) i -= 1;
    return i;
  }

  evaluate(x) {
    const clamped = Math.min(Math.max(x, this.x[0]), this.x[this.x.length - 1]);
    const i = this.segment(clamped);
    const h = this.spans[i];
    const t = (clamped - this.x[i]) / h;
    if (this.cubic) {
      const t2 = t * t, t3 = t2 * t;
      const value =
        (2 * t3 - 3 * t2 + 1) * this.y[i] +
        (t3 - 2 * t2 + t) * h * this.tangents[i] +
        (-2 * t3 + 3 * t2) * this.y[i + 1] +
        (t3 - t2) * h * this.tangents[i + 1];
      const slope =
        ((6 * t2 - 6 * t) * (this.y[i] - this.y[i + 1])) / h +
        (3 * t2 - 4 * t + 1) * this.tangents[i] +
        (3 * t2 - 2 * t) * this.tangents[i + 1];
      return [value, slope];
    }
    const weights = [
      this.y[i], h * this.tangents[i], h * h * this.curvatures[i],
      this.y[i + 1], h * this.tangents[i + 1], h * h * this.curvatures[i + 1],
    ];
    const dot = (b) => b.reduce((sum, coefficient, k) => sum + coefficient * weights[k], 0);
    return [dot(basis.value(t)), dot(basis.slope(t)) / h];
  }

  curvatureAt(x, skirt = 1, height = 1) {
    const clamped = Math.min(Math.max(x, this.x[0]), this.x[this.x.length - 1]);
    const i = this.segment(clamped);
    const h = this.spans[i];
    const t = (clamped - this.x[i]) / h;
    let second;
    if (this.cubic) {
      const a = this.y[i], b = h * this.tangents[i];
      const c = this.y[i + 1], d = h * this.tangents[i + 1];
      second = ((12 * t - 6) * (a - c) + (6 * t - 4) * b + (6 * t - 2) * d) / (h * h);
    } else {
      const weights = [
        this.y[i], h * this.tangents[i], h * h * this.curvatures[i],
        this.y[i + 1], h * this.tangents[i + 1], h * h * this.curvatures[i + 1],
      ];
      second =
        basis.curvature(t).reduce((sum, coefficient, k) => sum + coefficient * weights[k], 0) /
        (h * h);
    }
    const dzdu = this.evaluate(clamped)[1] * (height / skirt);
    const d2zdu2 = second * (height / (skirt * skirt));
    return d2zdu2 / Math.pow(1 + dzdu * dzdu, 1.5);
  }

  surfaceCurvature(skirt, height, count = 240) {
    const arc = new Float64Array(count);
    const curvature = new Float64Array(count);
    let travelled = 0;
    let previousSpeed = null;
    for (let i = 0; i < count; i += 1) {
      const x = i / (count - 1);
      const slope = this.evaluate(x)[1] * (height / skirt);
      const speed = skirt * Math.sqrt(1 + slope * slope);
      if (previousSpeed !== null) travelled += ((speed + previousSpeed) / 2) / (count - 1);
      previousSpeed = speed;
      arc[i] = travelled;
      curvature[i] = this.curvatureAt(x, skirt, height);
    }
    return { arc, curvature };
  }

  table(count) {
    const data = new Float32Array(count * 2);
    for (let i = 0; i < count; i += 1) {
      const [value, slope] = this.evaluate(i / (count - 1));
      data[i * 2] = value;
      data[i * 2 + 1] = slope;
    }
    return data;
  }

  monotone() {
    let previous = Infinity;
    for (let i = 0; i < 512; i += 1) {
      const value = this.evaluate(i / 511)[0];
      if (value > previous + 1e-9) return false;
      previous = value;
    }
    return true;
  }

  overshoot() {
    let high = -Infinity;
    let low = Infinity;
    for (let i = 0; i < 512; i += 1) {
      const value = this.evaluate(i / 511)[0];
      high = Math.max(high, value);
      low = Math.min(low, value);
    }
    return Math.max(0, high - 1) + Math.max(0, -low);
  }
}

export let UNIT_EXTENT = 0;

export function cornerCurve(extent, samples = 256) {
  const points = new Float32Array(samples * 2);
  const step = Math.PI / (samples - 1);
  let x = 0;
  let y = 0;
  const angleAt = (s) => s / 2 - Math.sin(2 * s) / 4;
  for (let i = 0; i < samples; i += 1) {
    if (i > 0) {
      const previous = angleAt((i - 1) * step);
      const current = angleAt(i * step);
      x += ((Math.cos(previous) + Math.cos(current)) / 2) * step;
      y -= ((Math.sin(previous) + Math.sin(current)) / 2) * step;
    }
    points[i * 2] = x;
    points[i * 2 + 1] = y;
  }
  const scale = extent / points[(samples - 1) * 2];
  for (let i = 0; i < samples * 2; i += 1) points[i] *= scale;
  return points;
}

export const HORIZON_SAMPLES = 1024;
const HULL_SAMPLES = 1024;

export function horizonReach(skirt, height) {
  return skirt + 16 * height;
}

export function horizonTable(profile, skirt, height, samples = HORIZON_SAMPLES) {
  const limit = horizonReach(skirt, height);
  const ridgeU = new Float64Array(HULL_SAMPLES);
  const ridgeZ = new Float64Array(HULL_SAMPLES);
  for (let i = 0; i < HULL_SAMPLES; i += 1) {
    const t = i / (HULL_SAMPLES - 1);
    ridgeU[i] = t * skirt;
    ridgeZ[i] = profile.evaluate(t)[0] * height;
  }
  const table = new Float32Array(samples * 2);
  for (let i = 1; i < samples; i += 1) {
    const u = (i / (samples - 1)) * limit;
    const z = u >= skirt ? 0 : profile.evaluate(u / skirt)[0] * height;
    let best = 0;
    let bestRun = 0;
    for (let j = 0; j < HULL_SAMPLES; j += 1) {
      const run = u - ridgeU[j];
      if (run <= 1e-9) break;
      const slope = (ridgeZ[j] - z) / run;
      if (slope > best) { best = slope; bestRun = run; }
    }
    table[i * 2] = best;
    table[i * 2 + 1] = bestRun;
  }
  return { table, limit };
}
