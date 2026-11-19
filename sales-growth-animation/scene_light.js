import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

/* ------------------------------------------------------------------ */
/* constants & helpers                                                 */
/* ------------------------------------------------------------------ */
const W = 1920, H = 1080;
const DUR = 8;                 // output length (s)
// scenes 1-2 keep their original timing; scene 3 (zoom-out -> target) is slowed so the final state is reached at ~7.1 s, then holds
const warp = (tv) => tv < 4 ? tv : Math.min(6, 4 + (tv - 4) * 0.65);
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const prog = (t, a, b) => clamp((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const E = {
  outCubic: x => 1 - Math.pow(1 - x, 3),
  outQuart: x => 1 - Math.pow(1 - x, 4),
  inOutCubic: x => (x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
  inOutSine: x => -(Math.cos(Math.PI * x) - 1) / 2,
  outBack: (x, s = 1.7) => 1 + (s + 1) * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2),
};
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/* ------------------------------------------------------------------ */
/* timeline (seconds)                                                  */
/* ------------------------------------------------------------------ */
const T = {
  logo: [0.0, 0.6],
  title: [0.2, 0.85],
  bar1: [0.3, 1.4],
  txt1: [1.1, 1.7],
  bar2: [2.1, 3.2],
  arrowA: [2.4, 3.4],
  txt2: [2.9, 3.5],
  badge: [3.25, 3.95],
  count: [3.3, 4.0],
  arrowB: [4.0, 4.95],
  bar3: [4.25, 5.25],
  flag: [5.0, 5.5],
  txt3: [4.95, 5.5],
  sumL: [4.5, 5.1],
  sumR: [4.85, 5.45],
};

/* ------------------------------------------------------------------ */
/* renderer                                                            */
/* ------------------------------------------------------------------ */
const dpr = window.devicePixelRatio || 1;
const canvas = document.getElementById('gl');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(dpr);
renderer.setSize(W, H, false);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.45;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

const camera = new THREE.PerspectiveCamera(30, W / H, 0.1, 200);

/* ------------------------------------------------------------------ */
/* background (2D canvas used as scene background)                     */
/* ------------------------------------------------------------------ */
const bgc = document.createElement('canvas');
bgc.width = W * dpr; bgc.height = H * dpr;
const bg = bgc.getContext('2d');
const bgTex = new THREE.CanvasTexture(bgc);
bgTex.colorSpace = THREE.SRGBColorSpace;
bgTex.minFilter = THREE.LinearFilter; bgTex.generateMipmaps = false;
scene.background = bgTex;

// static pre-rendered grid (masked with a radial fade)
const gridc = document.createElement('canvas');
const GW = Math.round(W * 1.5 * dpr), GH = Math.round(H * 1.5 * dpr);
gridc.width = GW; gridc.height = GH;
(function buildGrid() {
  const g = gridc.getContext('2d');
  const step = 80 * dpr;
  g.lineWidth = Math.max(1, dpr);
  for (let x = 0; x <= GW; x += step) {
    const major = Math.round(x / step) % 5 === 0;
    g.strokeStyle = major ? 'rgba(184,134,42,0.22)' : 'rgba(184,134,42,0.10)';
    g.beginPath(); g.moveTo(x, 0); g.lineTo(x, GH); g.stroke();
  }
  for (let y = 0; y <= GH; y += step) {
    const major = Math.round(y / step) % 5 === 0;
    g.strokeStyle = major ? 'rgba(184,134,42,0.22)' : 'rgba(184,134,42,0.10)';
    g.beginPath(); g.moveTo(0, y); g.lineTo(GW, y); g.stroke();
  }
  // glowing intersections
  for (let x = 0; x <= GW; x += step * 5) for (let y = 0; y <= GH; y += step * 5) {
    const r = 3.2 * dpr;
    const gr = g.createRadialGradient(x, y, 0, x, y, r * 4);
    gr.addColorStop(0, 'rgba(200,150,50,0.55)'); gr.addColorStop(1, 'rgba(200,150,50,0)');
    g.fillStyle = gr; g.beginPath(); g.arc(x, y, r * 4, 0, 7); g.fill();
  }
  g.globalCompositeOperation = 'destination-in';
  const m = g.createRadialGradient(GW * .5, GH * .46, GH * .12, GW * .5, GH * .46, GH * .62);
  m.addColorStop(0, 'rgba(0,0,0,1)'); m.addColorStop(1, 'rgba(0,0,0,0.05)');
  g.fillStyle = m; g.fillRect(0, 0, GW, GH);
})();

// floating data elements (seeded => deterministic)
const rng = mulberry32(20260);
const sparks = [];
for (let i = 0; i < 9; i++) {
  const n = 9 + Math.floor(rng() * 6);
  const pts = []; let y = rng() * .4;
  for (let k = 0; k < n; k++) { y += (rng() - .38) * .35; pts.push(y); }
  sparks.push({
    x: rng() * 1.15 - .08, y: rng() * .9 + .03, w: .13 + rng() * .12, h: .05 + rng() * .05,
    pts, par: .3 + rng() * .9, gold: rng() > .62, ph: rng() * 6.28,
  });
}
const candles = [];
for (let i = 0; i < 4; i++) {
  const n = 7 + Math.floor(rng() * 4); const arr = []; let v = .5;
  for (let k = 0; k < n; k++) { const o = v; v = clamp(v + (rng() - .42) * .28, .1, .95); arr.push([o, v, Math.max(o, v) + rng() * .1, Math.min(o, v) - rng() * .1]); }
  candles.push({ x: rng() * 1.0, y: rng() * .8 + .05, w: .1 + rng() * .07, h: .08 + rng() * .05, arr, par: .4 + rng() * .6 });
}
const motes = [];
for (let i = 0; i < 70; i++) motes.push({ x: rng(), y: rng(), r: .6 + rng() * 1.8, s: .01 + rng() * .03, ph: rng() * 6.28, par: .3 + rng() * 1.2, gold: rng() > .6 });

function drawBG(t, camX, camY) {
  const w = bgc.width, h = bgc.height, S = dpr;
  bg.setTransform(1, 0, 0, 1, 0, 0);
  // base gradient
  let g = bg.createRadialGradient(w * .6, h * .34, 0, w * .6, h * .34, w * .95);
  g.addColorStop(0, '#fffaf0'); g.addColorStop(.4, '#fbf2e0'); g.addColorStop(.75, '#f0e5cc'); g.addColorStop(1, '#e2d3b0');
  bg.fillStyle = g; bg.fillRect(0, 0, w, h);
  // warm gold glow upper-right (towards the target)
  g = bg.createRadialGradient(w * .84, h * .2, 0, w * .84, h * .2, w * .38);
  g.addColorStop(0, 'rgba(255,196,92,0.30)'); g.addColorStop(1, 'rgba(255,196,92,0)');
  bg.fillStyle = g; bg.fillRect(0, 0, w, h);
  // grid with parallax
  const ox = -(GW - w) / 2 - camX * 14 * S, oy = -(GH - h) / 2 + camY * 10 * S + (t * 4) * S;
  bg.drawImage(gridc, ox, oy);

  // sparklines
  bg.lineJoin = 'round'; bg.lineCap = 'round';
  for (const s of sparks) {
    const px = (s.x * w - camX * 22 * s.par * S), py = s.y * h + camY * 8 * s.par * S + Math.sin(t * .6 + s.ph) * 5 * S;
    const ww = s.w * w, hh = s.h * h;
    const col = s.gold ? '196,146,48' : '40,80,160';
    bg.shadowColor = `rgba(${col},0.8)`; bg.shadowBlur = 12 * S;
    bg.strokeStyle = `rgba(${col},0.30)`; bg.lineWidth = 2 * S;
    bg.beginPath();
    s.pts.forEach((v, k) => { const x = px + (k / (s.pts.length - 1)) * ww, y = py - v * hh * 2.2; k ? bg.lineTo(x, y) : bg.moveTo(x, y); });
    bg.stroke();
    const k2 = s.pts.length - 1; const ex = px + ww, ey = py - s.pts[k2] * hh * 2.2;
    bg.fillStyle = `rgba(${col},0.7)`; bg.beginPath(); bg.arc(ex, ey, 4 * S, 0, 7); bg.fill();
    bg.shadowBlur = 0;
  }
  // candle clusters
  for (const c of candles) {
    const px = c.x * w - camX * 26 * c.par * S, py = c.y * h + camY * 8 * c.par * S;
    const cw = c.w * w, ch = c.h * h, n = c.arr.length, bw = cw / n * .55;
    bg.lineWidth = 1.5 * S;
    c.arr.forEach((a, k) => {
      const x = px + (k + .5) * cw / n; const up = a[1] >= a[0];
      const col = up ? '196,146,48' : '40,80,160';
      bg.strokeStyle = `rgba(${col},0.22)`; bg.fillStyle = `rgba(${col},0.14)`;
      const yo = py - a[0] * ch, yc = py - a[1] * ch;
      bg.beginPath(); bg.moveTo(x, py - a[2] * ch); bg.lineTo(x, py - a[3] * ch); bg.stroke();
      bg.fillRect(x - bw / 2, Math.min(yo, yc), bw, Math.max(2 * S, Math.abs(yo - yc)));
      bg.strokeRect(x - bw / 2, Math.min(yo, yc), bw, Math.max(2 * S, Math.abs(yo - yc)));
    });
  }
  // faint rising bar-charts at both edges
  for (const side of [0, 1]) {
    const n = 9, bw = w * 0.012, gap = w * 0.019;
    const x0 = side ? w * 0.905 - camX * 8 * S : w * 0.01 - camX * 8 * S;
    const pts = [];
    for (let k = 0; k < n; k++) {
      const kk = side ? k : n - 1 - k;                         // taller towards the centre-right / left edge
      const hh = (0.10 + 0.045 * (side ? k : n - 1 - k)) * h * (side ? 1.0 : 0.85);
      const x = x0 + k * gap, y = h * 0.78 - hh;
      const gr = bg.createLinearGradient(0, y, 0, h * 0.78);
      gr.addColorStop(0, 'rgba(30,70,150,0.16)'); gr.addColorStop(1, 'rgba(30,70,150,0.01)');
      bg.fillStyle = gr; bg.fillRect(x, y, bw, hh);
      pts.push([x + bw / 2, y - h * 0.045]);
    }
    bg.strokeStyle = 'rgba(30,70,150,0.35)'; bg.lineWidth = 2 * S; bg.beginPath();
    pts.forEach(([x, y], k) => k ? bg.lineTo(x, y) : bg.moveTo(x, y)); bg.stroke();
    bg.fillStyle = 'rgba(30,70,150,0.7)';
    pts.forEach(([x, y]) => { bg.beginPath(); bg.arc(x, y, 4.5 * S, 0, 7); bg.fill(); });
  }
  // floating motes
  for (const m of motes) {
    const x = ((m.x * w - camX * 30 * m.par * S) % w + w) % w;
    const y = (((m.y - t * m.s) % 1 + 1) % 1) * h;
    const a = .25 + .25 * Math.sin(t * 1.6 + m.ph);
    const col = m.gold ? '214,170,70' : '110,140,200';
    const gr = bg.createRadialGradient(x, y, 0, x, y, m.r * 5 * S);
    gr.addColorStop(0, `rgba(${col},${a})`); gr.addColorStop(1, `rgba(${col},0)`);
    bg.fillStyle = gr; bg.beginPath(); bg.arc(x, y, m.r * 5 * S, 0, 7); bg.fill();
  }
  bgTex.needsUpdate = true;
}

/* ------------------------------------------------------------------ */
/* lights                                                              */
/* ------------------------------------------------------------------ */
scene.add(new THREE.HemisphereLight(0xffffff, 0xd9cdb4, 0.9));
const key = new THREE.DirectionalLight(0xfff0dc, 3.0);
key.position.set(-7, 13, 10);
key.target.position.set(2, 0, 0);
key.castShadow = true;
key.shadow.mapSize.set(4096, 4096);
key.shadow.camera.left = -16; key.shadow.camera.right = 16;
key.shadow.camera.top = 14; key.shadow.camera.bottom = -8;
key.shadow.camera.near = 1; key.shadow.camera.far = 50;
key.shadow.bias = -0.0004; key.shadow.normalBias = 0.03; key.shadow.radius = 5;
scene.add(key, key.target);
const rim = new THREE.DirectionalLight(0xfff0d0, 1.2); rim.position.set(11, 6, -7); scene.add(rim);
const fill = new THREE.DirectionalLight(0xffc782, 0.9); fill.position.set(7, 3, 12); scene.add(fill);

/* ------------------------------------------------------------------ */
/* floor                                                               */
/* ------------------------------------------------------------------ */
function makeGridTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 512;
  const g = c.getContext('2d');
  g.fillStyle = '#f7f2e7'; g.fillRect(0, 0, 512, 512);
  g.strokeStyle = 'rgba(190,145,60,0.60)'; g.lineWidth = 3;
  g.strokeRect(0, 0, 512, 512);
  g.strokeStyle = 'rgba(190,145,60,0.22)'; g.lineWidth = 2;
  g.beginPath(); g.moveTo(256, 0); g.lineTo(256, 512); g.moveTo(0, 256); g.lineTo(512, 256); g.stroke();
  const tx = new THREE.CanvasTexture(c);
  tx.colorSpace = THREE.SRGBColorSpace;
  tx.wrapS = tx.wrapT = THREE.RepeatWrapping; tx.repeat.set(60, 33);
  tx.anisotropy = 16;
  return tx;
}
function makeRadialAlpha() {
  const c = document.createElement('canvas'); c.width = c.height = 512;
  const g = c.getContext('2d');
  const r = g.createRadialGradient(256, 256, 20, 256, 256, 256);
  r.addColorStop(0, '#fff'); r.addColorStop(.6, '#e8e8e8'); r.addColorStop(1, '#000');
  g.fillStyle = r; g.fillRect(0, 0, 512, 512);
  return new THREE.CanvasTexture(c);
}
const floorMat = new THREE.MeshStandardMaterial({
  map: makeGridTexture(), alphaMap: makeRadialAlpha(), transparent: true, opacity: 0.8,
  metalness: 0.05, roughness: 0.12, envMapIntensity: 0.6, depthWrite: false,
});
const floor = new THREE.Mesh(new THREE.PlaneGeometry(90, 50), floorMat);
floor.rotation.x = -Math.PI / 2; floor.position.set(5, 0, -4);
floor.renderOrder = 2;
scene.add(floor);
const shadowPlane = new THREE.Mesh(new THREE.PlaneGeometry(90, 50), new THREE.ShadowMaterial({ opacity: 0.2, depthWrite: false }));
shadowPlane.rotation.x = -Math.PI / 2; shadowPlane.position.set(5, 0.004, -4); shadowPlane.receiveShadow = true; shadowPlane.renderOrder = 3;
scene.add(shadowPlane);

/* ------------------------------------------------------------------ */
/* shared materials / textures                                         */
/* ------------------------------------------------------------------ */
function radialSprite(stops) {
  const c = document.createElement('canvas'); c.width = c.height = 256;
  const g = c.getContext('2d');
  const r = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  stops.forEach(([o, col]) => r.addColorStop(o, col));
  g.fillStyle = r; g.fillRect(0, 0, 256, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const glowTexGold = radialSprite([[0, 'rgba(255,214,120,0.95)'], [.25, 'rgba(255,190,80,0.4)'], [1, 'rgba(255,170,50,0)']]);
const glowTexBlue = radialSprite([[0, 'rgba(140,200,255,0.9)'], [.3, 'rgba(70,140,255,0.35)'], [1, 'rgba(40,100,255,0)']]);

const M = {
  bar: new THREE.MeshPhysicalMaterial({ vertexColors: true, metalness: 0.25, roughness: 0.2, clearcoat: 1, clearcoatRoughness: 0.12, envMapIntensity: 1.25 }),
  gold: new THREE.MeshPhysicalMaterial({ color: 0xe8b84a, metalness: 1, roughness: 0.22, envMapIntensity: 1.8, emissive: 0x6a4a10, emissiveIntensity: 0.8 }),
  plinth: new THREE.MeshPhysicalMaterial({ color: 0xf3eee2, metalness: 0.2, roughness: 0.2, clearcoat: 1, envMapIntensity: 0.9 }),
  arrow: new THREE.MeshBasicMaterial({ color: new THREE.Color(0.5, 0.27, 0.015) }),
  arrowGlow: new THREE.MeshBasicMaterial({ color: new THREE.Color(1.0, 0.75, 0.2), transparent: true, opacity: 0.12, depthWrite: false }),
  arrowGlowHead: new THREE.MeshBasicMaterial({ color: new THREE.Color(1.0, 0.75, 0.2), transparent: true, opacity: 0.1, depthWrite: false }),
  arrowGlow2: new THREE.MeshBasicMaterial({ color: new THREE.Color(1.0, 0.6, 0.15), transparent: true, opacity: 0.045, blending: THREE.AdditiveBlending, depthWrite: false }),
  ribbon: new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, side: THREE.DoubleSide, depthWrite: false }),
  node: new THREE.MeshBasicMaterial({ color: new THREE.Color(0.8, 0.5, 0.06) }),
  dropLine: new THREE.LineBasicMaterial({ color: 0xf2c460, transparent: true, opacity: 0.35 }),
  tNavy: new THREE.MeshPhysicalMaterial({ color: 0x0b2a69, metalness: 0.5, roughness: 0.18, clearcoat: 1, envMapIntensity: 1.2 }),
  tBlue: new THREE.MeshPhysicalMaterial({ color: 0x2f7be6, metalness: 0.35, roughness: 0.2, clearcoat: 1, envMapIntensity: 1.2 }),
  tWhite: new THREE.MeshPhysicalMaterial({ color: 0xaec4ea, metalness: 0.2, roughness: 0.25, clearcoat: 1, envMapIntensity: 1.2 }),
  ripple: new THREE.MeshBasicMaterial({ color: 0xd4a02a, transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide }),
};

/* ------------------------------------------------------------------ */
/* data / geometry layout.  1 world unit = RM0.5 million:              */
/* RM1.2M -> 2.4, RM1.8M -> 3.6, RM3M -> 6.0  (strictly proportional)  */
/* ------------------------------------------------------------------ */
M.goldBar = new THREE.MeshPhysicalMaterial({ vertexColors: true, metalness: 0.55, roughness: 0.28, clearcoat: 1, clearcoatRoughness: 0.1, envMapIntensity: 1.4, emissive: 0x9a6200, emissiveIntensity: 0.75 });
M.goldLight = new THREE.MeshPhysicalMaterial({ color: 0xffe28a, metalness: 1, roughness: 0.18, envMapIntensity: 1.6, emissive: 0x6a4a10, emissiveIntensity: 0.7 });
M.arrowW = new THREE.MeshBasicMaterial({ color: 0x0b2a69 });
M.arrowWGlow = new THREE.MeshBasicMaterial({ color: 0x1a3f94, transparent: true, opacity: 0.10, depthWrite: false });
M.flag = new THREE.MeshStandardMaterial({ color: 0x6a0408, roughness: 0.6, metalness: 0.0, side: THREE.DoubleSide, emissive: 0x8a0410, emissiveIntensity: 0.8 });
M.pole = new THREE.MeshPhysicalMaterial({ color: 0xf0e6c8, metalness: 1, roughness: 0.25, envMapIntensity: 1.4 });

const BASE = 0.09;
const BARS = [
  { x: -5.2, w: 3.2, d: 2.2, h: 1.2 * 2, c0: '#05194a', c1: '#2358c4', grow: T.bar1, mat: M.bar, gold: false },
  { x: 0.0,  w: 3.2, d: 2.2, h: 1.8 * 2, c0: '#07266b', c1: '#3f86ec', grow: T.bar2, mat: M.bar, gold: false },
  { x: 5.4,  w: 3.6, d: 2.2, h: 3.0 * 2, c0: '#d98e10', c1: '#ffe266', grow: T.bar3, mat: M.goldBar, gold: true },
];
const Z = 1.45;
const CURVE_PTS = [[-5.2, 3.0], [-2.6, 3.85], [0.2, 4.45], [1.95, 5.15], [3.2, 6.15]].map(([x, y]) => new THREE.Vector3(x, y, Z));
const curve = new THREE.CatmullRomCurve3(CURVE_PTS, false, 'centripetal');
const DENSE = curve.getPoints(480);
const idxNear = (v) => { let bi = 0, bd = 1e9; DENSE.forEach((p, i) => { const d = p.distanceTo(v); if (d < bd) { bd = d; bi = i; } }); return bi; };
const IDX_C = idxNear(CURVE_PTS[2]);
const IDX_END = DENSE.length - 1;

function barGeo(w, h, d, hFinal, c0, c1) {
  const r = Math.min(0.1, h * 0.45);
  const g = new RoundedBoxGeometry(w, h, d, 4, r);
  g.translate(0, h / 2, 0);
  const pos = g.attributes.position;
  const col = new Float32Array(pos.count * 3);
  const a = new THREE.Color(c0), b = new THREE.Color(c1), c = new THREE.Color();
  for (let i = 0; i < pos.count; i++) {
    const k = clamp(pos.getY(i) / hFinal);
    c.lerpColors(a, b, Math.pow(k, 0.85));
    col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
  }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  return g;
}
function orient(mesh, dir, pos) {
  mesh.position.copy(pos);
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
}

/* ------------------------------------------------------------------ */
class Chart {
  constructor(mirror) {
    this.mirror = mirror;
    this.root = new THREE.Group();
    const shadow = !mirror;
    const gr = mirror ? new THREE.Group() : this.root;     // only bars reflect in the floor

    this.bars = BARS.map(b => {
      const grp = new THREE.Group(); grp.position.set(b.x, 0, 0);
      const plGrp = new THREE.Group();
      const plinth = new THREE.Mesh(new RoundedBoxGeometry(b.w + 0.55, BASE, b.d + 0.55, 3, 0.04), M.plinth);
      plinth.position.y = BASE / 2;
      const rim = new THREE.Mesh(new RoundedBoxGeometry(b.w + 0.62, 0.035, b.d + 0.62, 3, 0.02), M.gold);
      rim.position.y = 0.018;
      plGrp.add(plinth, rim);
      const body = new THREE.Mesh(new THREE.BufferGeometry(), b.mat);
      body.position.y = BASE; body.castShadow = shadow;
      const cap = new THREE.Mesh(new RoundedBoxGeometry(b.w + 0.06, 0.14, b.d + 0.06, 3, 0.05), b.gold ? M.goldLight : M.gold);
      cap.castShadow = shadow;
      const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: b.gold ? glowTexGold : glowTexBlue, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, opacity: 0 }));
      if (mirror) grp.add(body, cap); else grp.add(plGrp, body, cap, glow);
      this.root.add(grp);
      return { cfg: b, grp, plGrp, body, cap, glow, lastH: -1 };
    });

    // leg 1: solid gold arrow, bar 1 -> bar 2
    this.tube = new THREE.Mesh(new THREE.BufferGeometry(), M.arrow);
    this.tubeGlow = new THREE.Mesh(new THREE.BufferGeometry(), M.arrowGlow);
    this.head = new THREE.Mesh(new THREE.ConeGeometry(0.26, 0.68, 28), M.arrow);
    this.headGlow = new THREE.Mesh(new THREE.ConeGeometry(0.38, 0.9, 28), M.arrowGlowHead);
    this.startNode = new THREE.Mesh(new THREE.SphereGeometry(0.12, 24, 24), M.node);
    this.startNode.position.copy(CURVE_PTS[0]);
    // leg 2: white dashed arrow, bar 2 -> gold target bar
    this.dashes = new THREE.Mesh(new THREE.BufferGeometry(), M.arrowW);
    this.dashGlow = new THREE.Mesh(new THREE.BufferGeometry(), M.arrowWGlow);
    this.head2 = new THREE.Mesh(new THREE.ConeGeometry(0.26, 0.68, 28), M.arrowW);
    gr.add(this.tube, this.tubeGlow, this.head, this.headGlow, this.startNode, this.dashes, this.dashGlow, this.head2);

    // flag on the gold bar
    this.flagGrp = new THREE.Group();
    const top = BASE + BARS[2].h + 0.14;
    this.flagGrp.position.set(BARS[2].x + 0.5, top, 0);
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 1.25, 12), M.pole);
    pole.position.y = 0.625;
    const ball = new THREE.Mesh(new THREE.SphereGeometry(0.1, 16, 16), M.goldLight); ball.position.y = 1.28;
    this.flagGeo = new THREE.PlaneGeometry(1.15, 0.72, 16, 1); this.flagGeo.translate(0.575, 0, 0);
    this.flag = new THREE.Mesh(this.flagGeo, M.flag); this.flag.position.set(0.05, 0.9, 0);
    this.flagBase = this.flagGeo.attributes.position.array.slice();
    this.flagGrp.add(pole, ball, this.flag);
    gr.add(this.flagGrp);

    this.ripples = mirror ? [] : BARS.map((b, i) => {
      const m = new THREE.Mesh(new THREE.RingGeometry(0.97, 1.0, 96), M.ripple.clone());
      m.rotation.x = -Math.PI / 2; m.position.set(b.x, 0.03, 0);
      this.root.add(m);
      return { m, t0: b.grow[1] - 0.15, i };
    });
  }

  setTube(mesh, glow, pts, r, rg) {
    const c = new THREE.CatmullRomCurve3(pts); const seg = Math.max(12, pts.length);
    mesh.geometry.dispose(); mesh.geometry = new THREE.TubeGeometry(c, seg, r, 12, false);
    if (glow) { glow.geometry.dispose(); glow.geometry = new THREE.TubeGeometry(c, seg, rg, 12, false); }
  }

  update(t) {
    for (const b of this.bars) {
      const c = b.cfg;
      const p = E.outQuart(prog(t, c.grow[0], c.grow[1]));
      const h = c.h * p;
      const vis = h > 0.02;
      b.body.visible = b.cap.visible = vis;
      if (vis && Math.abs(h - b.lastH) > 1e-5) {
        b.body.geometry.dispose();
        b.body.geometry = barGeo(c.w, h, c.d, c.h, c.c0, c.c1);
        b.lastH = h;
      }
      b.cap.position.y = BASE + h + 0.07;
      // plinths: first two are there from the start, the target bar's appears just before it grows
      const pp = c.gold ? E.outCubic(prog(t, c.grow[0] - 0.45, c.grow[0] - 0.05)) : 1;
      b.plGrp.visible = pp > 0.01; b.plGrp.scale.set(0.6 + 0.4 * pp, 1, 0.6 + 0.4 * pp);
      b.glow.material.opacity = 0 * p * (0.8 + 0.2 * Math.sin(t * 3 + c.x));
      b.glow.position.y = BASE + h + 0.25;
      const gs = 3.6 * p + 0.2; b.glow.scale.set(gs, gs, 1);
    }

    // ---- leg 1 (gold) ----
    const pA = E.inOutCubic(prog(t, T.arrowA[0], T.arrowA[1]));
    const n1 = Math.round(lerp(0, IDX_C, pA));
    this.startNode.visible = pA > 0.01;
    this.startNode.scale.setScalar(Math.max(0.001, E.outBack(prog(t, T.arrowA[0], T.arrowA[0] + .35))));
    const vis1 = n1 >= 6;
    this.tube.visible = this.tubeGlow.visible = this.head.visible = this.headGlow.visible = vis1;
    if (vis1) {
      const pts = DENSE.slice(0, n1 + 1);
      this.setTube(this.tube, this.tubeGlow, pts, 0.064, 0.15);
      const tip = pts[pts.length - 1], prev = pts[Math.max(0, pts.length - 4)];
      const dir = tip.clone().sub(prev).normalize();
      const hp = tip.clone().addScaledVector(dir, -0.22);
      orient(this.head, dir, hp); orient(this.headGlow, dir, hp);
    }

    // ---- leg 2 (white dashes) ----
    const pB = E.inOutCubic(prog(t, T.arrowB[0], T.arrowB[1]));
    const n2 = Math.round(lerp(IDX_C, IDX_END, pB));
    const vis2 = t >= T.arrowB[0] && n2 - IDX_C >= 8;
    this.dashes.visible = this.dashGlow.visible = this.head2.visible = vis2;
    if (vis2) {
      const geos = [], geosG = [];
      const D = 15, G = 11;
      for (let i = IDX_C + 6; i < n2 - 8; i += D + G) {
        const sl = DENSE.slice(i, Math.min(i + D, n2 - 8));
        if (sl.length < 4) continue;
        const c = new THREE.CatmullRomCurve3(sl);
        geos.push(new THREE.TubeGeometry(c, 6, 0.07, 8, false));
        geosG.push(new THREE.TubeGeometry(c, 6, 0.16, 8, false));
      }
      this.dashes.geometry.dispose(); this.dashGlow.geometry.dispose();
      if (geos.length) { this.dashes.geometry = mergeGeometries(geos); this.dashGlow.geometry = mergeGeometries(geosG); geos.concat(geosG).forEach(g => g.dispose()); }
      else { this.dashes.geometry = new THREE.BufferGeometry(); this.dashGlow.geometry = new THREE.BufferGeometry(); }
      const tip = DENSE[n2], prev = DENSE[Math.max(0, n2 - 6)];
      const dir = tip.clone().sub(prev).normalize();
      orient(this.head2, dir, tip.clone().addScaledVector(dir, -0.22));
    }

    // ---- flag ----
    const fp = E.outBack(prog(t, T.flag[0], T.flag[1]), 1.2);
    this.flagGrp.visible = fp > 0.01;
    this.flagGrp.scale.set(Math.max(0.001, fp), Math.max(0.001, fp), Math.max(0.001, fp));
    const pa = this.flagGeo.attributes.position.array;
    for (let i = 0; i < pa.length; i += 3) {
      const x = this.flagBase[i];
      pa[i + 2] = Math.sin(x * 5.0 - t * 6.0) * 0.07 * (x / 1.15);
      pa[i + 1] = this.flagBase[i + 1] + Math.sin(x * 3.0 - t * 4.0) * 0.03 * (x / 1.15);
    }
    this.flagGeo.attributes.position.needsUpdate = true; this.flagGeo.computeVertexNormals();

    for (const r of this.ripples) {
      const k = prog(t, r.t0, r.t0 + 1.0);
      const s = lerp(0.9, 2.8, E.outCubic(k)) * (r.i === 2 ? 1.15 : 1);
      r.m.scale.set(s * BARS[r.i].w / 3.2, s, 1);
      r.m.material.opacity = k > 0 && k < 1 ? 0.8 * (1 - k) : 0;
    }
  }
}

const real = new Chart(false);
const refl = new Chart(true);
scene.add(real.root);
const mirrorRoot = new THREE.Group(); mirrorRoot.scale.y = -1; mirrorRoot.add(refl.root);
scene.add(mirrorRoot);

/* ------------------------------------------------------------------ */
/* camera path                                                         */
/* ------------------------------------------------------------------ */
const KEYS = [
  { t: 0.0,  p: [-6.7, 3.1, 12.6],  l: [-5.0, 1.7, 0.5], f: 30 },
  { t: 2.0,  p: [-4.0, 3.9, 16.0],  l: [-3.1, 2.1, 0.5], f: 30 },
  { t: 3.9,  p: [-2.4, 4.4, 17.8],  l: [-2.2, 2.7, 0.5], f: 30 },
  { t: 4.85, p: [-0.6, 5.2, 21.2],  l: [-0.5, 3.2, 0.5], f: 30 },
  { t: 6.0,  p: [0.3, 6.2, 23.4],   l: [0.1, 3.6, 0.5], f: 30 },
];
function hermite(v0, v1, m0, m1, h, s) {
  const s2 = s * s, s3 = s2 * s;
  return (2 * s3 - 3 * s2 + 1) * v0 + (s3 - 2 * s2 + s) * h * m0 + (-2 * s3 + 3 * s2) * v1 + (s3 - s2) * h * m1;
}
function keyVal(get, t) {
  const n = KEYS.length;
  let i = 0; while (i < n - 2 && t > KEYS[i + 1].t) i++;
  const a = KEYS[i], b = KEYS[i + 1], h = b.t - a.t, s = clamp((t - a.t) / h);
  const tan = (k) => (k === 0 || k === n - 1) ? 0 : (get(KEYS[k + 1]) - get(KEYS[k - 1])) / (KEYS[k + 1].t - KEYS[k - 1].t);
  return hermite(get(a), get(b), tan(i), tan(i + 1), h, s);
}
const lookV = new THREE.Vector3();
function setCamera(t) {
  const px = keyVal(k => k.p[0], t), py = keyVal(k => k.p[1], t), pz = keyVal(k => k.p[2], t);
  const lx = keyVal(k => k.l[0], t), ly = keyVal(k => k.l[1], t), lz = keyVal(k => k.l[2], t);
  camera.position.set(px + Math.sin(t * 1.05) * 0.12, py + Math.sin(t * 0.8 + 1) * 0.06, pz);
  lookV.set(lx, ly, lz);
  camera.fov = keyVal(k => k.f, t);
  camera.updateProjectionMatrix();
  camera.lookAt(lookV);
  camera.updateMatrixWorld(true);
}

/* ------------------------------------------------------------------ */
/* post-processing                                                     */
/* ------------------------------------------------------------------ */
const rt = new THREE.WebGLRenderTarget(W * dpr, H * dpr, { type: THREE.HalfFloatType, samples: 4 });
const composer = new EffectComposer(renderer, rt);
composer.setPixelRatio(dpr); composer.setSize(W, H);
composer.addPass(new RenderPass(scene, camera));
composer.addPass(new UnrealBloomPass(new THREE.Vector2(W, H), 0.12, 0.5, 0.97));
composer.addPass(new OutputPass());

/* ------------------------------------------------------------------ */
/* DOM overlays                                                        */
/* ------------------------------------------------------------------ */
const $ = (id) => document.getElementById(id);
const el = { logo: $('logo'), div: $('divider'), title: $('title'), t1: $('t1'), t2: $('t2'), t3: $('t3'),
  p1: $('p1'), p2: $('p2'), p3: $('p3'), badge: $('badge'), pct: $('pct'), sum: $('sum'), sumL: $('sumL'), sumR: $('sumR') };
const v3 = new THREE.Vector3();
function project(x, y, z) { v3.set(x, y, z).project(camera); return [(v3.x * 0.5 + 0.5) * W, (-v3.y * 0.5 + 0.5) * H]; }
function place(node, p, x, y, s, dy = 24) {
  node.style.opacity = p.toFixed(3);
  node.style.transform = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px) translate(-50%,-50%) translateY(${((1 - p) * dy).toFixed(1)}px) scale(${s.toFixed(4)})`;
  node.style.filter = p < 1 ? `blur(${((1 - p) * 8).toFixed(1)}px)` : 'none';
}
function fixed(node, p, dx, dy) {
  node.style.opacity = p.toFixed(3);
  node.style.transform = `translate(${(dx * (1 - p)).toFixed(1)}px,${(dy * (1 - p)).toFixed(1)}px)`;
  node.style.filter = p < 1 ? `blur(${((1 - p) * 7).toFixed(1)}px)` : 'none';
}
function updateOverlays(t) {
  const dist = camera.position.distanceTo(lookV);
  const ppu = H / (2 * dist * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)));    // pixels per world unit
  const s = ppu / 84.6;                                                                 // 1.0 at the final framing

  // header
  fixed(el.logo, E.outCubic(prog(t, T.logo[0], T.logo[1])), -40, 0);
  el.div.style.opacity = E.outCubic(prog(t, T.title[0], T.title[1])).toFixed(3);
  fixed(el.title, E.outCubic(prog(t, T.title[0], T.title[1])), 50, 0);

  // texts + plates attached to the bars
  const txt = [el.t1, el.t2, el.t3], plt = [el.p1, el.p2, el.p3];
  const times = [T.txt1, T.txt2, T.txt3];
  BARS.forEach((b, i) => {
    const p = E.outCubic(prog(t, times[i][0], times[i][1]));
    const front = b.d / 2 + 0.02;
    const [cx, cy] = project(b.x, BASE + b.h * (i === 2 ? 0.64 : 0.62), front);
    place(txt[i], p, cx, cy, s, 18);
    const [px_, py_] = project(b.x, BASE + 0.34, front + 0.05);
    place(plt[i], E.outCubic(prog(t, times[i][0] - 0.25, times[i][1] - 0.1)), px_, py_, s, 14);
  });

  // red badge
  const bp = clamp(E.outBack(prog(t, T.badge[0], T.badge[1]), 1.3));
  const [bx, by] = project(-3.2, 4.85, Z);
  const bs = Math.pow(s, 0.5) * 0.7;
  place(el.badge, bp, bx, by, bs * (0.88 + 0.12 * bp), 18);
  el.pct.textContent = '+' + Math.round(50 * E.outCubic(prog(t, T.count[0], T.count[1]))) + '%';

  // summary strip
  const pl = E.outCubic(prog(t, T.sumL[0], T.sumL[1])), pr = E.outCubic(prog(t, T.sumR[0], T.sumR[1]));
  el.sum.style.opacity = 1;
  el.sumL.style.opacity = pl; el.sumL.style.transform = `translateY(${(1 - pl) * 50}px)`; el.sumL.style.filter = pl < 1 ? `blur(${(1 - pl) * 7}px)` : 'none';
  el.sumR.style.opacity = pr; el.sumR.style.transform = `translateY(${(1 - pr) * 50}px) scale(${0.94 + 0.06 * pr})`; el.sumR.style.filter = pr < 1 ? `blur(${(1 - pr) * 7}px)` : 'none';
}

await document.fonts.load('800 40px Inter');
await document.fonts.load('italic 800 40px Inter');
await document.fonts.load('700 40px Inter');
await document.fonts.ready;

window.renderAt = (tv) => {
  const t = warp(tv);
  setCamera(t);
  drawBG(t, lookV.x, lookV.y);
  real.update(t); refl.update(t);
  key.position.set(-7 + Math.sin(t * .7) * 0.8, 13, 10);
  composer.render();
  updateOverlays(t);
  return true;
};
window.DUR = DUR;
window.__ready = true;
window.renderAt(0);
