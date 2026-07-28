import { EdgeProfile, cornerCurve, horizonTable, HORIZON_SAMPLES, UNIT_EXTENT } from './spline.js';

const QUAD_VERTEX = `#version 300 es
in vec2 position;
out vec2 uv;
void main() {
  uv = position * 0.5 + 0.5;
  gl_Position = vec4(position, 0.0, 1.0);
}`;

const FIELD_FRAGMENT = `#version 300 es
precision highp float;
precision highp sampler2D;

in vec2 uv;
out vec4 field;

uniform vec2 uViewport;
uniform vec2 uHalfSize;
uniform float uRadius;
uniform float uSkirt;
uniform float uHeight;
uniform int uCornerStyle;
uniform int uCurveSamples;
uniform float uCurveScale;
uniform sampler2D uProfile;
uniform sampler2D uCurve;

vec2 curvePoint(int index) {
  return texelFetch(uCurve, ivec2(index, 0), 0).xy;
}

float circularDistance(vec2 p) {
  vec2 q = abs(p) - (uHalfSize - uRadius);
  return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - uRadius;
}

float gCornerBend = 0.0;

float continuousDistance(vec2 p) {
  gCornerBend = 0.0;
  vec2 a = abs(p);
  vec2 inner = uHalfSize - uRadius;
  float straight = max(a.x - uHalfSize.x, a.y - uHalfSize.y);
  if (a.x <= inner.x || a.y <= inner.y) return straight;

  vec2 shifted = a - vec2(uHalfSize.x - uRadius, uHalfSize.y - uRadius);
  vec2 origin = vec2(0.0, uRadius);
  float best = 1e9;
  int bestIndex = 0;
  vec2 bestOffset = vec2(0.0);
  vec2 bestNormal = vec2(0.0);
  for (int i = 0; i < uCurveSamples - 1; i++) {
    vec2 s = origin + curvePoint(i);
    vec2 e = origin + curvePoint(i + 1);
    vec2 edge = e - s;
    vec2 w = shifted - s;
    float t = clamp(dot(w, edge) / max(dot(edge, edge), 1e-12), 0.0, 1.0);
    vec2 offset = w - edge * t;
    float squared = dot(offset, offset);
    if (squared < best) {
      best = squared;
      bestIndex = i;
      bestOffset = offset;
      bestNormal = normalize(vec2(-edge.y, edge.x));
    }
  }
  float magnitude = sqrt(best);
  float side = dot(bestOffset, bestNormal) >= 0.0 ? 1.0 : -1.0;
  gCornerBend = pow(sin(float(bestIndex) / float(uCurveSamples - 1) * 3.14159265359), 2.0) / uCurveScale;
  return side * magnitude;
}

vec2 gradientAt(vec2 p, float centre) {
  float step = 0.05;
  float dx = (uCornerStyle == 1 ? continuousDistance(p + vec2(step, 0.0)) : circularDistance(p + vec2(step, 0.0))) - centre;
  float dy = (uCornerStyle == 1 ? continuousDistance(p + vec2(0.0, step)) : circularDistance(p + vec2(0.0, step))) - centre;
  vec2 g = vec2(dx, dy);
  float len = length(g);
  return len < 1e-6 ? vec2(0.0, 0.0) : g / len;
}

void main() {
  vec2 p = vec2((uv.x - 0.5) * uViewport.x, (0.5 - uv.y) * uViewport.y);
  float u;
  float boundaryBend;
  if (uCornerStyle == 1) {
    u = continuousDistance(p);
    boundaryBend = gCornerBend;
  } else {
    u = circularDistance(p);
    vec2 q = abs(p) - (uHalfSize - uRadius);
    boundaryBend = (q.x > 0.0 && q.y > 0.0) ? 1.0 / uRadius : 0.0;
  }
  vec2 n2 = gradientAt(p, u);
  float bend = boundaryBend / (1.0 + max(u, 0.0) * boundaryBend);
  field = vec4(u, n2.x, n2.y, bend);
}`;

const SHADE_FRAGMENT = `#version 300 es
precision highp float;
precision highp sampler2D;

in vec2 uv;
out vec4 colour;

uniform sampler2D uField;
uniform sampler2D uProfile;
uniform sampler2D uHorizon;
uniform vec2 uViewport;
uniform vec3 uAlbedo;
uniform vec3 uGroundAlbedo;
uniform vec3 uSunColour;
uniform vec3 uSkyHorizon;
uniform vec3 uSkyGradient;
uniform vec3 uSunGain;
uniform float uHeight;
uniform float uHorizonLimit;
uniform float uSkyStrength;
uniform float uSpecular;
uniform float uGroundSpecular;
uniform float uGloss;
uniform float uGroundGloss;
uniform float uSunAzimuth;
uniform float uSunElevation;
uniform float uSunSigma;
uniform float uSunRadius;
uniform int uFalloff;
uniform int uAzimuths;
uniform float uSkirt;

const float PI = 3.14159265359;

float erfApprox(float x) {
  float sign = x < 0.0 ? -1.0 : 1.0;
  x = abs(x);
  float t = 1.0 / (1.0 + 0.3275911 * x);
  float y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * exp(-x * x);
  return sign * y;
}

float normalCdf(float x) {
  return 0.5 * (1.0 + erfApprox(x * 0.70710678));
}

float discFraction(float offset) {
  float c = clamp(offset, -1.0, 1.0);
  return (acos(-c) + c * sqrt(max(0.0, 1.0 - c * c))) / PI;
}

vec2 ridgeTangency(float footprint) {
  if (footprint <= 0.0) return vec2(0.0);
  if (footprint > uHorizonLimit) return vec2(uHeight / max(footprint, 1e-6), footprint);
  return texture(uHorizon, vec2(footprint / uHorizonLimit, 0.5)).xy;
}

float saddleTangent(vec2 tangency, float bend, float inward) {
  float squared = max(inward * inward, 1e-6);
  float stretch = 1.0 + 0.5 * tangency.y * bend * (1.0 - squared) / squared;
  return inward * tangency.x / stretch;
}

void main() {
  vec4 field = texture(uField, uv);
  float u = field.x;
  vec2 outward = field.yz;

  vec2 sampled = texture(uProfile, vec2(clamp(u / uSkirt, 0.0, 1.0), 0.5)).xy;
  float z = u <= 0.0 ? uHeight : (u >= uSkirt ? 0.0 : sampled.x * uHeight);
  float radial = (u > 0.0 && u < uSkirt) ? -sampled.y * (uHeight / uSkirt) : 0.0;
  float scale = inversesqrt(radial * radial + 1.0);
  vec3 normal = vec3(outward * radial * scale, scale);

  float blend = clamp(z / uHeight, 0.0, 1.0);
  vec3 albedo = mix(uGroundAlbedo, uAlbedo, blend);
  float specular = mix(uGroundSpecular, uSpecular, blend);
  float gloss = mix(uGroundGloss, uGloss, blend);
  vec2 tangency = ridgeTangency(u);
  float bend = field.w;

  vec3 sunDirection = vec3(
    cos(uSunAzimuth) * cos(uSunElevation),
    sin(uSunAzimuth) * cos(uSunElevation),
    sin(uSunElevation));
  vec3 halfVector = normalize(sunDirection + vec3(0.0, 0.0, 1.0));

  float skyUniform = 0.0;
  float skyGraded = 0.0;
  for (int i = 0; i < uAzimuths; i++) {
    float azimuth = (float(i) + 0.5) / float(uAzimuths) * 2.0 * PI;
    vec2 direction = vec2(cos(azimuth), sin(azimuth));
    float inward = max(0.0, -dot(direction, outward));
    float along = normal.x * direction.x + normal.y * direction.y;
    float occluded = atan(saddleTangent(tangency, bend, inward));
    float selfShadow = atan(max(0.0, -along), max(normal.z, 1e-9));
    float lower = max(occluded, selfShadow);
    if (lower >= PI * 0.5 - 1e-6) continue;
    float c = cos(lower);
    float sn = sin(lower);
    skyUniform += max(0.0, along * (PI / 4.0 - lower / 2.0 - sin(2.0 * lower) / 4.0)
                          + 0.5 * normal.z * c * c);
    skyGraded += max(0.0, (along * c * c * c + normal.z * (1.0 - sn * sn * sn)) / 3.0);
  }
  float weight = (2.0 * PI / float(uAzimuths)) / PI;
  skyUniform *= weight;
  skyGraded *= weight;

  vec2 sunGround = vec2(cos(uSunAzimuth), sin(uSunAzimuth));
  float towardSun = max(0.0, -dot(sunGround, outward));
  float clearance = uSunElevation - atan(saddleTangent(tangency, bend, towardSun));
  float coverage = uFalloff == 1
    ? discFraction(clearance / uSunRadius)
    : normalCdf(clearance / uSunSigma);

  float lambert = max(0.0, dot(normal, sunDirection));
  float sheen = coverage * pow(max(0.0, dot(normal, halfVector)), gloss) * specular;

  vec3 radiance = albedo * (uSunGain * uSunColour * (coverage * lambert)
                          + uSkyStrength * (uSkyHorizon * skyUniform
                                          + uSkyGradient * skyGraded))
                + sheen * uSunColour;

  colour = vec4(pow(clamp(radiance, 0.0, 1.0), vec3(1.0 / 2.4)) * 1.055 - 0.055, 1.0);
  colour.rgb = mix(clamp(radiance, 0.0, 1.0) * 12.92, colour.rgb, step(0.0031308, radiance));
  colour.a = 1.0;
}`;

function compile(gl, type, source) {
  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    throw new Error(gl.getShaderInfoLog(shader) || 'shader compile failed');
  }
  return shader;
}

function link(gl, vertexSource, fragmentSource) {
  const program = gl.createProgram();
  gl.attachShader(program, compile(gl, gl.VERTEX_SHADER, vertexSource));
  gl.attachShader(program, compile(gl, gl.FRAGMENT_SHADER, fragmentSource));
  gl.bindAttribLocation(program, 0, 'position');
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
    throw new Error(gl.getProgramInfoLog(program) || 'program link failed');
  }
  return program;
}

function srgbToLinear(value) {
  return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
}

export function hexToLinear(hex) {
  const text = hex.replace('#', '');
  return [0, 2, 4].map((i) => srgbToLinear(parseInt(text.slice(i, i + 2), 16) / 255));
}

export class BevelRenderer {
  constructor(canvas) {
    const gl = canvas.getContext('webgl2', { antialias: false, preserveDrawingBuffer: true });
    if (!gl) throw new Error('WebGL2 is required');
    this.gl = gl;
    this.canvas = canvas;
    this.float = gl.getExtension('EXT_color_buffer_float');
    gl.getExtension('OES_texture_float_linear');

    this.fieldProgram = link(gl, QUAD_VERTEX, FIELD_FRAGMENT);
    this.shadeProgram = link(gl, QUAD_VERTEX, SHADE_FRAGMENT);

    const buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    this.vao = gl.createVertexArray();
    gl.bindVertexArray(this.vao);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    gl.bindVertexArray(null);

    this.profileTexture = this.makeTexture(gl.RG32F, gl.RG, 512, 1, gl.LINEAR);
    this.horizonTexture = this.makeTexture(gl.RG32F, gl.RG, HORIZON_SAMPLES, 1, gl.LINEAR);
    this.horizonLimit = 1;
    this.curveTexture = this.makeTexture(gl.RG32F, gl.RG, 256, 1, gl.NEAREST);
    this.fieldTexture = null;
    this.framebuffer = gl.createFramebuffer();
    this.size = [0, 0];
  }

  makeTexture(internal, format, width, height, filter) {
    const gl = this.gl;
    const texture = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.texStorage2D(gl.TEXTURE_2D, 1, internal, width, height);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filter);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filter);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    return texture;
  }

  resize(width, height) {
    if (this.size[0] === width && this.size[1] === height) return;
    const gl = this.gl;
    if (this.fieldTexture) gl.deleteTexture(this.fieldTexture);
    this.fieldTexture = this.makeTexture(gl.RGBA32F, gl.RGBA, width, height, gl.LINEAR);
    this.size = [width, height];
  }

  uploadProfile(profile, skirt, height) {
    const gl = this.gl;
    gl.bindTexture(gl.TEXTURE_2D, this.profileTexture);
    gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 512, 1, gl.RG, gl.FLOAT, profile.table(512));
    const { table, limit } = horizonTable(profile, skirt, height);
    this.horizonLimit = limit;
    gl.bindTexture(gl.TEXTURE_2D, this.horizonTexture);
    gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, HORIZON_SAMPLES, 1, gl.RG, gl.FLOAT, table);
  }

  uploadCorner(extent) {
    const gl = this.gl;
    gl.bindTexture(gl.TEXTURE_2D, this.curveTexture);
    gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 256, 1, gl.RG, gl.FLOAT, cornerCurve(extent, 256));
  }

  draw(scene) {
    const gl = this.gl;
    const [width, height] = this.size;
    const set = (program, name) => gl.getUniformLocation(program, name);

    gl.bindVertexArray(this.vao);
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.framebuffer);
    gl.framebufferTexture2D(
      gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, this.fieldTexture, 0,
    );
    gl.viewport(0, 0, width, height);
    gl.useProgram(this.fieldProgram);
    gl.uniform2f(set(this.fieldProgram, 'uViewport'), scene.viewport[0], scene.viewport[1]);
    gl.uniform2f(set(this.fieldProgram, 'uHalfSize'), scene.halfSize[0], scene.halfSize[1]);
    gl.uniform1f(set(this.fieldProgram, 'uRadius'), scene.radius);
    gl.uniform1f(set(this.fieldProgram, 'uSkirt'), scene.skirt);
    gl.uniform1f(set(this.fieldProgram, 'uHeight'), scene.height);
    gl.uniform1i(set(this.fieldProgram, 'uCornerStyle'), scene.corner === 'g3' ? 1 : 0);
    gl.uniform1i(set(this.fieldProgram, 'uCurveSamples'), 256);
    gl.uniform1f(set(this.fieldProgram, 'uCurveScale'), scene.radius / (UNIT_EXTENT || 1));
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, this.profileTexture);
    gl.uniform1i(set(this.fieldProgram, 'uProfile'), 0);
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, this.curveTexture);
    gl.uniform1i(set(this.fieldProgram, 'uCurve'), 1);
    gl.drawArrays(gl.TRIANGLES, 0, 3);

    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, width, height);
    gl.useProgram(this.shadeProgram);
    const p = this.shadeProgram;
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, this.fieldTexture);
    gl.uniform1i(set(p, 'uField'), 0);
    gl.activeTexture(gl.TEXTURE1);
    gl.bindTexture(gl.TEXTURE_2D, this.profileTexture);
    gl.uniform1i(set(p, 'uProfile'), 1);
    gl.activeTexture(gl.TEXTURE2);
    gl.bindTexture(gl.TEXTURE_2D, this.horizonTexture);
    gl.uniform1i(set(p, 'uHorizon'), 2);
    gl.uniform1f(set(p, 'uHorizonLimit'), this.horizonLimit);
    gl.uniform1f(set(p, 'uHeight'), scene.height);
    gl.uniform2f(set(p, 'uViewport'), scene.viewport[0], scene.viewport[1]);
    gl.uniform3fv(set(p, 'uAlbedo'), scene.albedo);
    gl.uniform3fv(set(p, 'uGroundAlbedo'), scene.groundAlbedo);
    gl.uniform3fv(set(p, 'uSunColour'), scene.sunColour);
    gl.uniform3fv(set(p, 'uSkyHorizon'), scene.skyHorizon);
    gl.uniform3fv(set(p, 'uSkyGradient'), scene.skyGradient);
    gl.uniform3fv(set(p, 'uSunGain'), scene.sunGain);
    gl.uniform1f(set(p, 'uSkyStrength'), scene.skyStrength);
    gl.uniform1f(set(p, 'uSpecular'), scene.specular);
    gl.uniform1f(set(p, 'uGroundSpecular'), scene.groundSpecular);
    gl.uniform1f(set(p, 'uGloss'), scene.gloss);
    gl.uniform1f(set(p, 'uGroundGloss'), scene.groundGloss);
    gl.uniform1f(set(p, 'uSunAzimuth'), scene.sunAzimuth);
    gl.uniform1f(set(p, 'uSunElevation'), scene.sunElevation);
    gl.uniform1f(set(p, 'uSunSigma'), scene.sunSigma);
    gl.uniform1f(set(p, 'uSunRadius'), scene.sunRadius);
    gl.uniform1i(set(p, 'uFalloff'), scene.falloff === 'disk' ? 1 : 0);
    gl.uniform1i(set(p, 'uAzimuths'), scene.azimuths);
    gl.uniform1f(set(p, 'uSkirt'), scene.skirt);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    gl.bindVertexArray(null);
  }
}

export { EdgeProfile };
