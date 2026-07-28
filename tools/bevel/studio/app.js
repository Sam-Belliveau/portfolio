import { BevelRenderer, EdgeProfile, hexToLinear } from './renderer.js';

const view = document.getElementById('view');
const status = document.getElementById('status');
const renderer = new BevelRenderer(view);

let config = null;
let saved = null;
let level = 'panel';
let activeProfile = null;
let activeMaterial = null;
let profile = null;
let tileView = false;
let loading = false;
let frames = 0;
let lastReport = performance.now();
let frameCost = 0;

const el = (id) => document.getElementById(id);
const pairs = [
  'radius', 'height', 'skirt', 'margin', 'startSlope', 'endSlope', 'specular', 'gloss',
  'sunAz', 'sunEl', 'sunSigma', 'sunRadius', 'skyStrength', 'cardW', 'cardH', 'azimuths',
];

const levelData = () => config.levels[level];
const profileSpec = () => config.profiles[activeProfile];
const materialData = () => config.materials[activeMaterial];
const groundData = () => config.materials[levelData().ground ?? 'page'];

function fillSelect(node, options, value) {
  node.innerHTML = '';
  for (const option of options) {
    const item = document.createElement('option');
    item.value = option;
    item.textContent = option;
    node.appendChild(item);
  }
  node.value = value;
}

const setPair = (name, value) => { el(name).value = value; el(`${name}N`).value = value; };

function loadLevel() {
  loading = true;
  const data = levelData();
  activeProfile = data.profile;
  activeMaterial = data.material;
  const spec = profileSpec();
  const material = materialData();
  const sun = config.lighting.sun;
  const sky = config.lighting.sky;

  fillSelect(el('profileName'), Object.keys(config.profiles), data.profile);
  fillSelect(el('material'), Object.keys(config.materials), data.material);
  fillSelect(el('ground'), Object.keys(config.materials), data.ground ?? 'page');
  el('corner').value = data.corner ?? 'g3';
  el('continuity').value = spec.continuity ?? 'G3';
  el('falloff').value = sun.falloff ?? 'gaussian';

  setPair('radius', data.radius);
  setPair('height', data.height);
  setPair('skirt', data.skirt);
  setPair('margin', data.margin);
  setPair('startSlope', spec.start_slope);
  setPair('endSlope', spec.end_slope ?? 0);
  setPair('specular', material.specular_strength);
  setPair('gloss', material.gloss);
  setPair('sunAz', sun.azimuth);
  setPair('sunEl', sun.elevation);
  setPair('sunSigma', sun.angular_sigma ?? 6);
  setPair('sunRadius', sun.angular_radius);
  setPair('skyStrength', sky.strength);
  el('albedo').value = material.albedo;
  el('sunColour').value = sun.color;
  el('skyHorizonColour').value = sky.horizon_color ?? sky.color;
  el('skyZenithColour').value = sky.zenith_color ?? sky.color;
  writePointsField(spec.points);
  loading = false;
}

function commit() {
  if (loading || !config) return;
  const data = levelData();
  data.corner = el('corner').value;
  data.radius = +el('radius').value;
  data.height = +el('height').value;
  data.skirt = +el('skirt').value;
  data.margin = +el('margin').value;
  data.ground = el('ground').value;

  const spec = profileSpec();
  spec.continuity = el('continuity').value;
  spec.start_slope = +el('startSlope').value;
  spec.end_slope = +el('endSlope').value;

  const material = materialData();
  material.albedo = el('albedo').value;
  material.specular_strength = +el('specular').value;
  material.gloss = +el('gloss').value;

  Object.assign(config.lighting.sun, {
    azimuth: +el('sunAz').value,
    elevation: +el('sunEl').value,
    falloff: el('falloff').value,
    angular_sigma: +el('sunSigma').value,
    angular_radius: +el('sunRadius').value,
    color: el('sunColour').value,
  });
  Object.assign(config.lighting.sky, {
    horizon_color: el('skyHorizonColour').value,
    zenith_color: el('skyZenithColour').value,
    strength: +el('skyStrength').value,
  });
}

function writePointsField(points) {
  el('points').value = points
    .map(([x, y]) => `${(+x).toFixed(4)}, ${(+y).toFixed(4)}`)
    .join('\n');
}

function setPoints(points) {
  profileSpec().points = points.map(([x, y]) => [+x, +y]);
  writePointsField(profileSpec().points);
  apply();
}

function buildProfile() {
  const spec = profileSpec();
  try {
    profile = new EdgeProfile(
      spec.points, spec.start_slope, spec.end_slope ?? 0, spec.continuity ?? 'G3',
    );
    renderer.uploadProfile(profile, +el('skirt').value, +el('height').value);
    return null;
  } catch (error) {
    return error.message;
  }
}

function apply() {
  commit();
  const error = buildProfile();
  renderer.uploadCorner(+el('radius').value);
  drawEditor();
  drawCurvature();
  report(error);
}

const PAD = 18;

function editorFrame() {
  const canvas = el('profilePlot');
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  const innerW = w - 2 * PAD;
  const innerH = h - 2 * PAD;
  return {
    canvas, w, h,
    toPx: (x, y) => [w - PAD - x * innerW, h - PAD - y * innerH],
    toData: (px, py) => [(w - PAD - px) / innerW, (h - PAD - py) / innerH],
  };
}

function prepare(canvas) {
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvas.width = Math.max(1, canvas.clientWidth * dpr);
  canvas.height = Math.max(1, canvas.clientHeight * dpr);
  const ctx = canvas.getContext('2d');
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight);
  return ctx;
}

let hovered = -1;

function drawEditor() {
  if (!profile) return;
  const frame = editorFrame();
  const ctx = prepare(frame.canvas);
  const ink = getComputedStyle(document.body).color;

  ctx.strokeStyle = 'rgba(128,128,128,0.22)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i += 1) {
    const [, gy] = frame.toPx(0, i / 4);
    const [gx] = frame.toPx(i / 4, 0);
    ctx.beginPath(); ctx.moveTo(PAD, gy); ctx.lineTo(frame.w - PAD, gy); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(gx, PAD); ctx.lineTo(gx, frame.h - PAD); ctx.stroke();
  }

  ctx.fillStyle = 'rgba(128,128,128,0.8)';
  ctx.font = '10px ui-sans-serif, sans-serif';
  ctx.fillText('rim', frame.w - PAD - 16, frame.h - 5);
  ctx.fillText('page', PAD - 4, frame.h - 5);

  ctx.strokeStyle = '#9c1c1c';
  ctx.lineWidth = 2;
  ctx.beginPath();
  for (let i = 0; i < 240; i += 1) {
    const x = i / 239;
    const [px, py] = frame.toPx(x, profile.evaluate(x)[0]);
    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
  }
  ctx.stroke();

  const points = profileSpec().points;
  points.forEach(([x, y], index) => {
    const [px, py] = frame.toPx(x, y);
    const locked = index === 0 || index === points.length - 1;
    ctx.beginPath();
    ctx.arc(px, py, index === hovered ? 7 : 5, 0, Math.PI * 2);
    ctx.fillStyle = locked ? 'rgba(128,128,128,0.55)' : '#9c1c1c';
    ctx.fill();
    ctx.strokeStyle = ink;
    ctx.lineWidth = 1;
    ctx.stroke();
  });
}

function drawCurvature() {
  if (!profile) return;
  const canvas = el('curvaturePlot');
  const ctx = prepare(canvas);
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  const { arc, curvature } = profile.surfaceCurvature(
    +el('skirt').value, +el('height').value,
  );
  const span = arc[arc.length - 1] || 1;
  const low = Math.min(0, ...curvature);
  const high = Math.max(0, ...curvature);
  const range = high - low || 1;
  const toY = (v) => h - PAD - ((v - low) / range) * (h - 2 * PAD);

  ctx.strokeStyle = 'rgba(128,128,128,0.35)';
  ctx.beginPath(); ctx.moveTo(0, toY(0)); ctx.lineTo(w, toY(0)); ctx.stroke();
  ctx.strokeStyle = '#2f6fb0';
  ctx.lineWidth = 2;
  ctx.beginPath();
  for (let i = 0; i < arc.length; i += 1) {
    const px = w - PAD - (arc[i] / span) * (w - 2 * PAD);
    if (i === 0) ctx.moveTo(px, toY(curvature[i])); else ctx.lineTo(px, toY(curvature[i]));
  }
  ctx.stroke();
  ctx.fillStyle = 'rgba(128,128,128,0.8)';
  ctx.font = '10px ui-sans-serif, sans-serif';
  ctx.fillText(`arc length ${span.toFixed(2)}px`, PAD, h - 5);
}

function nearestPoint(px, py) {
  const frame = editorFrame();
  const points = profileSpec().points;
  let best = -1;
  let bestDistance = 11;
  points.forEach(([x, y], index) => {
    const [ax, ay] = frame.toPx(x, y);
    const distance = Math.hypot(ax - px, ay - py);
    if (distance < bestDistance) { bestDistance = distance; best = index; }
  });
  return best;
}

function setupEditor() {
  const canvas = el('profilePlot');
  let dragging = -1;

  const local = (event) => {
    const rect = canvas.getBoundingClientRect();
    return [event.clientX - rect.left, event.clientY - rect.top];
  };

  canvas.addEventListener('contextmenu', (event) => event.preventDefault());

  canvas.addEventListener('pointerdown', (event) => {
    const [px, py] = local(event);
    const index = nearestPoint(px, py);
    const points = profileSpec().points;
    const interior = index > 0 && index < points.length - 1;
    if (index >= 0 && (event.altKey || event.button === 2)) {
      if (interior) setPoints(points.filter((_, i) => i !== index));
      return;
    }
    if (interior) {
      dragging = index;
      canvas.setPointerCapture(event.pointerId);
    }
  });

  canvas.addEventListener('pointermove', (event) => {
    const [px, py] = local(event);
    if (dragging < 0) {
      const index = nearestPoint(px, py);
      if (index !== hovered) { hovered = index; drawEditor(); }
      canvas.style.cursor = index >= 0 ? 'grab' : 'crosshair';
      return;
    }
    const points = profileSpec().points.map((p) => [...p]);
    const [dx, dy] = editorFrame().toData(px, py);
    const lower = points[dragging - 1][0] + 1e-3;
    const upper = points[dragging + 1][0] - 1e-3;
    points[dragging][0] = Math.min(Math.max(dx, lower), upper);
    points[dragging][1] = Math.min(Math.max(dy, 0), 1);
    setPoints(points);
  });

  const release = (event) => {
    if (dragging >= 0) {
      dragging = -1;
      try { canvas.releasePointerCapture(event.pointerId); } catch { /* already released */ }
    }
  };
  canvas.addEventListener('pointerup', release);
  canvas.addEventListener('pointercancel', release);

  canvas.addEventListener('dblclick', (event) => {
    const [px, py] = local(event);
    if (nearestPoint(px, py) >= 0) return;
    const [dx, dy] = editorFrame().toData(px, py);
    if (dx <= 0 || dx >= 1) return;
    const points = profileSpec().points.map((p) => [...p]);
    points.push([Math.min(Math.max(dx, 0.001), 0.999), Math.min(Math.max(dy, 0), 1)]);
    points.sort((a, b) => a[0] - b[0]);
    setPoints(points);
  });
}

function scene() {
  const data = levelData();
  const material = materialData();
  const ground = groundData();
  const sun = config.lighting.sun;
  const sky = config.lighting.sky;

  const horizonLinear = hexToLinear(sky.horizon_color ?? sky.color);
  const zenithLinear = hexToLinear(sky.zenith_color ?? sky.color);
  const gradient = zenithLinear.map((c, i) => c - horizonLinear[i]);
  const flatSky = horizonLinear.map((c, i) => c + (2 / 3) * gradient[i]);
  const sunLinear = hexToLinear(sun.color);
  const flatSun = Math.sin((sun.elevation * Math.PI) / 180);
  const sunGain = sunLinear.map((c, i) => (1 - sky.strength * flatSky[i]) / (flatSun * c));

  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  renderer.resize(
    Math.max(1, Math.round(view.clientWidth * dpr)),
    Math.max(1, Math.round(view.clientHeight * dpr)),
  );
  view.width = Math.max(1, Math.round(view.clientWidth * dpr));
  view.height = Math.max(1, Math.round(view.clientHeight * dpr));

  const span = 2 * (data.margin + data.radius + 2 * data.height + 2) + 4;
  const cardWidth = tileView ? span : +el('cardW').value;
  const cardHeight = tileView ? span : +el('cardH').value;

  return {
    viewport: [view.clientWidth, view.clientHeight],
    halfSize: [cardWidth / 2, cardHeight / 2],
    radius: Math.min(data.radius, cardWidth / 2, cardHeight / 2),
    skirt: data.skirt,
    height: data.height,
    corner: data.corner ?? 'g3',
    albedo: hexToLinear(material.albedo),
    groundAlbedo: hexToLinear(ground.albedo),
    sunColour: sunLinear,
    skyHorizon: horizonLinear,
    skyGradient: gradient,
    sunGain,
    skyStrength: sky.strength,
    specular: material.specular_strength,
    groundSpecular: ground.specular_strength,
    gloss: material.gloss,
    groundGloss: ground.gloss,
    sunAzimuth: (sun.azimuth * Math.PI) / 180,
    sunElevation: (sun.elevation * Math.PI) / 180,
    sunSigma: ((sun.angular_sigma ?? 6) * Math.PI) / 180,
    sunRadius: (sun.angular_radius * Math.PI) / 180,
    falloff: sun.falloff ?? 'gaussian',
    azimuths: +el('azimuths').value,
  };
}

function report(error) {
  if (!profile) { status.textContent = `profile error: ${error}`; return; }
  const data = levelData();
  const slice = data.margin + data.radius + 2 * data.height + 2;
  const flags = [];
  if (!profile.monotone()) flags.push('NON-MONOTONE');
  const over = profile.overshoot();
  if (over > 1e-6) flags.push(`overshoot ${over.toFixed(3)}`);
  status.innerHTML =
    `${level} · ${activeProfile} · ${data.corner ?? 'g3'} corner · ${profileSpec().continuity} · `
    + `${profileSpec().points.length} pts · slice ${slice.toFixed(1)}px · `
    + `tile ${(2 * slice + 4).toFixed(0)}px · ${frameCost.toFixed(1)} ms/frame`
    + (flags.length ? `  <span class="warn">&lt;${flags.join(', ')}&gt;</span>` : '')
    + (error ? `  ${error}` : '');
}

function frame() {
  if (config) {
    const start = performance.now();
    renderer.draw(scene());
    frames += 1;
    if (start - lastReport > 400) {
      frameCost = (start - lastReport) / frames;
      frames = 0;
      lastReport = start;
      report(null);
    }
  }
  requestAnimationFrame(frame);
}

function buildLevelButtons() {
  const host = el('levels');
  host.innerHTML = '';
  for (const name of Object.keys(config.levels)) {
    const button = document.createElement('button');
    button.textContent = name;
    if (name === level) button.className = 'primary';
    button.onclick = () => { commit(); level = name; buildLevelButtons(); loadLevel(); apply(); };
    host.appendChild(button);
  }
}

function bindControls() {
  for (const name of pairs) {
    const slider = el(name);
    const number = el(`${name}N`);
    number.min = slider.min;
    number.max = slider.max;
    slider.addEventListener('input', () => { number.value = slider.value; apply(); });
    number.addEventListener('input', () => { slider.value = number.value; apply(); });
  }
  for (const id of ['corner', 'continuity', 'falloff', 'ground']) {
    el(id).addEventListener('change', apply);
  }
  el('profileName').addEventListener('change', () => {
    commit();
    levelData().profile = el('profileName').value;
    loadLevel();
    apply();
  });
  el('material').addEventListener('change', () => {
    commit();
    levelData().material = el('material').value;
    loadLevel();
    apply();
  });
  for (const id of ['albedo', 'sunColour', 'skyHorizonColour', 'skyZenithColour']) {
    el(id).addEventListener('input', apply);
  }
  el('points').addEventListener('change', () => {
    const parsed = el('points').value.trim().split('\n')
      .map((line) => line.split(',').map(Number))
      .filter((row) => row.length === 2 && row.every(Number.isFinite))
      .sort((a, b) => a[0] - b[0]);
    if (parsed.length >= 2) setPoints(parsed);
  });
}

async function loadConfig(source) {
  const response = await fetch(source);
  config = await response.json();
  saved = structuredClone(config);
  if (!config.levels[level]) level = Object.keys(config.levels)[0];
  setPair('cardW', 520);
  setPair('cardH', 300);
  setPair('azimuths', 96);
  buildLevelButtons();
  loadLevel();
  apply();
}

el('save').onclick = async () => {
  commit();
  await fetch('/config.json', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config, null, 2),
  });
  saved = structuredClone(config);
  status.textContent = 'saved config.json';
};
el('reload').onclick = () => {
  config = structuredClone(saved);
  buildLevelButtons();
  loadLevel();
  apply();
};
el('defaults').onclick = () => loadConfig('/defaults.json');
el('tileView').onclick = () => {
  tileView = !tileView;
  el('tileView').textContent = tileView ? 'Show card size' : 'Show 9-slice tile size';
};
el('bake').onclick = async () => {
  commit();
  status.textContent = 'saving config…';
  await fetch('/config.json', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config, null, 2),
  });
  saved = structuredClone(config);
  status.textContent = 'baking tiles…';
  const response = await fetch('/render', { method: 'POST' });
  status.textContent = await response.text();
};

bindControls();
setupEditor();
window.addEventListener('resize', () => { drawEditor(); drawCurvature(); });
loadConfig('/config.json').catch((error) => { status.textContent = String(error); });
frame();
