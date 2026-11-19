import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

/* ------------------------------------------------------------------ */
/* constants & helpers                                                 */
/* ------------------------------------------------------------------ */
const W = 1920, H = 1080;
const DUR = 6;
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
  bar1: [0.25, 1.35],
  card1: [1.05, 1.7],
  bar2: [2.1, 3.2],
  arrowA: [2.5, 3.55],      // arrow drawn from bar 1 to bar 2
  card2: [2.95, 3.55],
  badge: [3.3, 3.95],
  count: [3.35, 4.0],
  arrowB: [4.2, 5.5],     // arrow continues to the target
  target: [4.55, 5.3],
  headline1: [4.45, 5.1],
  headline2: [4.8, 5.4],
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
renderer.toneMappingExposure = 1.05;
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
    g.strokeStyle = major ? 'rgba(110,170,255,0.20)' : 'rgba(90,150,240,0.10)';
    g.beginPath(); g.moveTo(x, 0); g.lineTo(x, GH); g.stroke();
  }
  for (let y = 0; y <= GH; y += step) {
    const major = Math.round(y / step) % 5 === 0;
    g.strokeStyle = major ? 'rgba(110,170,255,0.20)' : 'rgba(90,150,240,0.10)';
    g.beginPath(); g.moveTo(0, y); g.lineTo(GW, y); g.stroke();
  }
  // glowing intersections
  for (let x = 0; x <= GW; x += step * 5) for (let y = 0; y <= GH; y += step * 5) {
    const r = 3.2 * dpr;
    const gr = g.createRadialGradient(x, y, 0, x, y, r * 4);
    gr.addColorStop(0, 'rgba(150,200,255,0.55)'); gr.addColorStop(1, 'rgba(150,200,255,0)');
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
  g.addColorStop(0, '#16418a'); g.addColorStop(.38, '#0b2763'); g.addColorStop(.75, '#061640'); g.addColorStop(1, '#030c26');
  bg.fillStyle = g; bg.fillRect(0, 0, w, h);
  // warm gold glow upper-right (towards the target)
  g = bg.createRadialGradient(w * .84, h * .2, 0, w * .84, h * .2, w * .38);
  g.addColorStop(0, 'rgba(255,196,92,0.16)'); g.addColorStop(1, 'rgba(255,196,92,0)');
  bg.fillStyle = g; bg.fillRect(0, 0, w, h);
  // grid with parallax
  const ox = -(GW - w) / 2 - camX * 14 * S, oy = -(GH - h) / 2 + camY * 10 * S + (t * 4) * S;
  bg.drawImage(gridc, ox, oy);

  // sparklines
  bg.lineJoin = 'round'; bg.lineCap = 'round';
  for (const s of sparks) {
    const px = (s.x * w - camX * 22 * s.par * S), py = s.y * h + camY * 8 * s.par * S + Math.sin(t * .6 + s.ph) * 5 * S;
    const ww = s.w * w, hh = s.h * h;
    const col = s.gold ? '255,205,110' : '120,185,255';
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
      const col = up ? '255,205,110' : '120,185,255';
      bg.strokeStyle = `rgba(${col},0.22)`; bg.fillStyle = `rgba(${col},0.14)`;
      const yo = py - a[0] * ch, yc = py - a[1] * ch;
      bg.beginPath(); bg.moveTo(x, py - a[2] * ch); bg.lineTo(x, py - a[3] * ch); bg.stroke();
      bg.fillRect(x - bw / 2, Math.min(yo, yc), bw, Math.max(2 * S, Math.abs(yo - yc)));
      bg.strokeRect(x - bw / 2, Math.min(yo, yc), bw, Math.max(2 * S, Math.abs(yo - yc)));
    });
  }
  // floating motes
  for (const m of motes) {
    const x = ((m.x * w - camX * 30 * m.par * S) % w + w) % w;
    const y = (((m.y - t * m.s) % 1 + 1) % 1) * h;
    const a = .25 + .25 * Math.sin(t * 1.6 + m.ph);
    const col = m.gold ? '255,215,130' : '170,210,255';
    const gr = bg.createRadialGradient(x, y, 0, x, y, m.r * 5 * S);
    gr.addColorStop(0, `rgba(${col},${a})`); gr.addColorStop(1, `rgba(${col},0)`);
    bg.fillStyle = gr; bg.beginPath(); bg.arc(x, y, m.r * 5 * S, 0, 7); bg.fill();
  }
  bgTex.needsUpdate = true;
}

/* ------------------------------------------------------------------ */
/* lights                                                              */
/* ------------------------------------------------------------------ */
scene.add(new THREE.HemisphereLight(0x8fbaff, 0x0a1432, 0.55));
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
const rim = new THREE.DirectionalLight(0x4f90ff, 2.4); rim.position.set(11, 6, -7); scene.add(rim);
const fill = new THREE.DirectionalLight(0xffc782, 0.9); fill.position.set(7, 3, 12); scene.add(fill);

/* ------------------------------------------------------------------ */
/* floor                                                               */
/* ------------------------------------------------------------------ */
function makeGridTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 512;
  const g = c.getContext('2d');
  g.fillStyle = '#0a1a3e'; g.fillRect(0, 0, 512, 512);
  g.strokeStyle = 'rgba(120,185,255,0.85)'; g.lineWidth = 3;
  g.strokeRect(0, 0, 512, 512);
  g.strokeStyle = 'rgba(120,185,255,0.30)'; g.lineWidth = 2;
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
  map: makeGridTexture(), alphaMap: makeRadialAlpha(), transparent: true, opacity: 0.9,
  metalness: 0.55, roughness: 0.3, envMapIntensity: 0.35, depthWrite: false,
});
const floor = new THREE.Mesh(new THREE.PlaneGeometry(90, 50), floorMat);
floor.rotation.x = -Math.PI / 2; floor.position.set(5, 0, -4);
floor.renderOrder = 2;
scene.add(floor);
const shadowPlane = new THREE.Mesh(new THREE.PlaneGeometry(90, 50), new THREE.ShadowMaterial({ opacity: 0.3, depthWrite: false }));
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
  gold: new THREE.MeshPhysicalMaterial({ color: 0xe2b04a, metalness: 1, roughness: 0.2, envMapIntensity: 1.5, emissive: 0x4a3008, emissiveIntensity: 0.6 }),
  plinth: new THREE.MeshPhysicalMaterial({ color: 0x0c1f4d, metalness: 0.6, roughness: 0.25, clearcoat: 1, envMapIntensity: 0.9 }),
  arrow: new THREE.MeshBasicMaterial({ color: new THREE.Color(1.7, 1.3, 0.5) }),
  arrowGlow: new THREE.MeshBasicMaterial({ color: new THREE.Color(1.0, 0.65, 0.2), transparent: true, opacity: 0.22, blending: THREE.AdditiveBlending, depthWrite: false }),
  arrowGlowHead: new THREE.MeshBasicMaterial({ color: new THREE.Color(1.0, 0.65, 0.2), transparent: true, opacity: 0.1, blending: THREE.AdditiveBlending, depthWrite: false }),
  arrowGlow2: new THREE.MeshBasicMaterial({ color: new THREE.Color(1.0, 0.6, 0.15), transparent: true, opacity: 0.045, blending: THREE.AdditiveBlending, depthWrite: false }),
  ribbon: new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, side: THREE.DoubleSide, depthWrite: false }),
  node: new THREE.MeshBasicMaterial({ color: new THREE.Color(2.2, 1.8, 0.8) }),
  dropLine: new THREE.LineBasicMaterial({ color: 0xf2c460, transparent: true, opacity: 0.35 }),
  tNavy: new THREE.MeshPhysicalMaterial({ color: 0x0b2a69, metalness: 0.5, roughness: 0.18, clearcoat: 1, envMapIntensity: 1.2 }),
  tBlue: new THREE.MeshPhysicalMaterial({ color: 0x2f7be6, metalness: 0.35, roughness: 0.2, clearcoat: 1, envMapIntensity: 1.2 }),
  tWhite: new THREE.MeshPhysicalMaterial({ color: 0xaec4ea, metalness: 0.2, roughness: 0.25, clearcoat: 1, envMapIntensity: 1.2 }),
  ripple: new THREE.MeshBasicMaterial({ color: new THREE.Color(1.6, 1.2, 0.5), transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }),
};

/* ------------------------------------------------------------------ */
/* data / geometry layout (1 unit = RM0.6 million -> 3.6 = RM1.8M)     */
/* bar heights are strictly proportional to the figures shown          */
/* ------------------------------------------------------------------ */
const BASE = 0.09;                 // plinth height
const BARS = [
  { x: -2.5, h: 1.2 * 2, c0: '#06215e', c1: '#2e6fdc', grow: T.bar1, name: 'b1' },   // RM1.2M -> 2.4
  { x: 2.5, h: 1.8 * 2, c0: '#08307f', c1: '#58aaff', grow: T.bar2, name: 'b2' },    // RM1.8M -> 3.6
];
const BW = 1.8, BD = 1.8;
const Z = 1.05;                    // plane of arrow / graph (in front of bar faces)
const CURVE_PTS = [
  [-2.5, 2.95], [0.0, 3.6], [2.5, 4.2], [5.4, 4.75], [8.0, 5.35], [10.4, 5.95], [12.4, 6.6],
].map(([x, y]) => new THREE.Vector3(x, y, Z));
const curve = new THREE.CatmullRomCurve3(CURVE_PTS, false, 'centripetal');
const DENSE = curve.getPoints(480);
const idxNear = (v) => { let bi = 0, bd = 1e9; DENSE.forEach((p, i) => { const d = p.distanceTo(v); if (d < bd) { bd = d; bi = i; } }); return bi; };
const IDX_C = idxNear(CURVE_PTS[2]);
const IDX_END = DENSE.length - 1;
const NODE_IDX = [3, 4, 5].map(i => idxNear(CURVE_PTS[i]));
const RIBBON_START = DENSE.findIndex(p => p.x >= 3.7);
const TARGET = new THREE.Vector3(12.4, 6.6, 0.9);

function barGeo(w, h, d, hFinal, c0, c1) {
  const r = Math.min(0.09, h * 0.45);
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

/* ------------------------------------------------------------------ */
/* Chart (instantiated twice: real + mirrored reflection)              */
/* ------------------------------------------------------------------ */
class Chart {
  constructor(mirror) {
    this.mirror = mirror;
    this.root = new THREE.Group();
    const shadow = !mirror;

    // bars
    this.bars = BARS.map(b => {
      const grp = new THREE.Group(); grp.position.set(b.x, 0, 0);
      const plinth = new THREE.Mesh(new RoundedBoxGeometry(BW + 0.55, BASE, BD + 0.55, 3, 0.04), M.plinth);
      plinth.position.y = BASE / 2; plinth.receiveShadow = false;
      const rim = new THREE.Mesh(new RoundedBoxGeometry(BW + 0.62, 0.035, BD + 0.62, 3, 0.02), M.gold);
      rim.position.y = 0.018;
      const body = new THREE.Mesh(new THREE.BufferGeometry(), M.bar);
      body.position.y = BASE; body.castShadow = shadow;
      const cap = new THREE.Mesh(new RoundedBoxGeometry(BW + 0.06, 0.14, BD + 0.06, 3, 0.05), M.gold);
      cap.castShadow = shadow;
      const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexBlue, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, opacity: 0.0 }));
      if (mirror) { grp.add(body, cap); } else grp.add(plinth, rim, body, cap, glow);
      this.root.add(grp);
      return { cfg: b, grp, body, cap, glow, lastH: -1 };
    });

    // arrow  (not mirrored: only the bars reflect in the floor)
    const gr = mirror ? new THREE.Group() : this.root;
    this.tube = new THREE.Mesh(new THREE.BufferGeometry(), M.arrow);
    this.tubeGlow = new THREE.Mesh(new THREE.BufferGeometry(), M.arrowGlow);
    this.tubeGlow2 = new THREE.Mesh(new THREE.BufferGeometry(), M.arrowGlow2);
    this.head = new THREE.Mesh(new THREE.ConeGeometry(0.24, 0.62, 28), M.arrow);
    this.headGlow = new THREE.Mesh(new THREE.ConeGeometry(0.36, 0.85, 28), M.arrowGlowHead);
    gr.add(this.tube, this.tubeGlow, this.tubeGlow2, this.head, this.headGlow);
    this.startNode = new THREE.Mesh(new THREE.SphereGeometry(0.11, 24, 24), M.node);
    this.startNode.position.copy(CURVE_PTS[0]);
    gr.add(this.startNode);

    // area ribbon under the growth line
    this.ribbon = new THREE.Mesh(new THREE.BufferGeometry(), M.ribbon);
    this.ribbon.renderOrder = 4;
    gr.add(this.ribbon);

    // nodes + drop lines
    this.nodes = NODE_IDX.map(i => {
      const m = new THREE.Mesh(new THREE.SphereGeometry(0.15, 24, 24), M.node);
      m.position.copy(DENSE[i]);
      const lg = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(DENSE[i].x, 0.02, Z), DENSE[i].clone()]);
      const line = new THREE.Line(lg, M.dropLine);
      const foot = new THREE.Mesh(new THREE.CircleGeometry(0.28, 32), new THREE.MeshBasicMaterial({ map: glowTexGold, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, opacity: 0 }));
      foot.rotation.x = -Math.PI / 2; foot.position.set(DENSE[i].x, 0.015, Z);
      gr.add(m, line, foot);
      return { m, line, foot, i };
    });

    // target
    this.target = new THREE.Group();
    this.target.position.copy(TARGET);
    this.target.rotation.y = -0.22;
    const disc = (r, h, mat) => { const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 72), mat); m.rotation.x = Math.PI / 2; return m; };
    const ring = (r, t, mat) => new THREE.Mesh(new THREE.TorusGeometry(r, t, 28, 120), mat);
    const d1 = disc(1.2, 0.12, M.tNavy); d1.position.z = 0;
    const d2 = disc(0.92, 0.14, M.tWhite); d2.position.z = 0.012;
    const d3 = disc(0.66, 0.16, M.tBlue); d3.position.z = 0.024;
    const d4 = disc(0.4, 0.18, M.tWhite); d4.position.z = 0.036;
    const d5 = disc(0.19, 0.2, M.gold); d5.position.z = 0.048;
    const r1 = ring(1.22, 0.085, M.gold); r1.position.z = 0.02;
    
    this.target.add(d1, d2, d3, d4, d5, r1);
    this.tGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexGold, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, opacity: 0 }));
    this.tGlow.position.set(0, 0, -0.35); this.tGlow.scale.set(6.5, 6.5, 1);
    this.target.add(this.tGlow);
    this.pulse = new THREE.Mesh(new THREE.TorusGeometry(1.25, 0.03, 12, 120), M.ripple.clone());
    this.pulse.position.z = 0.03;
    this.target.add(this.pulse);
    gr.add(this.target);

    // floor ripples
    this.ripples = mirror ? [] : [
      { x: -2.5, t0: 1.25 }, { x: 2.5, t0: 3.1 },
    ].map(r => {
      const m = new THREE.Mesh(new THREE.RingGeometry(0.97, 1.0, 96), M.ripple.clone());
      m.rotation.x = -Math.PI / 2; m.position.set(r.x, 0.03, 0);
      this.root.add(m);
      return { m, t0: r.t0 };
    });
  }

  update(t) {
    // bars
    for (const b of this.bars) {
      const p = E.outQuart(prog(t, b.cfg.grow[0], b.cfg.grow[1]));
      const h = b.cfg.h * p;
      const vis = h > 0.02;
      b.body.visible = b.cap.visible = vis;
      if (vis && Math.abs(h - b.lastH) > 1e-5) {
        b.body.geometry.dispose();
        b.body.geometry = barGeo(BW, h, BD, b.cfg.h, b.cfg.c0, b.cfg.c1);
        b.lastH = h;
      }
      b.cap.position.y = BASE + h + 0.07;
      const done = prog(t, b.cfg.grow[1] - .15, b.cfg.grow[1] + .5);
      b.glow.material.opacity = (this.mirror ? 0 : 1) * (0.32 * p) * (0.8 + 0.2 * Math.sin(t * 3 + b.cfg.x));
      b.glow.position.y = BASE + h + 0.25;
      const gs = 3.2 * p + 0.2; b.glow.scale.set(gs, gs, 1);
      b.cap.material = M.gold;
    }

    // arrow
    const pA = E.inOutCubic(prog(t, T.arrowA[0], T.arrowA[1]));
    const pB = E.inOutCubic(prog(t, T.arrowB[0], T.arrowB[1]));
    let n;
    if (t < T.arrowB[0]) n = Math.round(lerp(0, IDX_C, pA)); else n = Math.round(lerp(IDX_C, IDX_END, pB));
    this.startNode.visible = pA > 0.01;
    const sn = E.outBack(prog(t, T.arrowA[0], T.arrowA[0] + .35));
    this.startNode.scale.setScalar(Math.max(0.001, sn));
    if (n >= 6) {
      const pts = DENSE.slice(0, n + 1);
      const c = new THREE.CatmullRomCurve3(pts);
      const seg = Math.max(12, n);
      this.tube.geometry.dispose(); this.tubeGlow.geometry.dispose(); this.tubeGlow2.geometry.dispose();
      this.tube.geometry = new THREE.TubeGeometry(c, seg, 0.062, 12, false);
      this.tubeGlow.geometry = new THREE.TubeGeometry(c, seg, 0.15, 12, false);
      this.tubeGlow2.geometry = new THREE.BufferGeometry();
      const tip = pts[pts.length - 1], prev = pts[Math.max(0, pts.length - 4)];
      const dir = tip.clone().sub(prev).normalize();
      const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir);
      const hp = tip.clone().addScaledVector(dir, -0.2);
      this.head.position.copy(hp); this.head.quaternion.copy(q);
      this.headGlow.position.copy(hp); this.headGlow.quaternion.copy(q);
      this.tube.visible = this.tubeGlow.visible = this.tubeGlow2.visible = this.head.visible = this.headGlow.visible = true;
    } else {
      this.tube.visible = this.tubeGlow.visible = this.tubeGlow2.visible = this.head.visible = this.headGlow.visible = false;
    }

    // ribbon (area under the line, only beyond bar 2)
    const rEnd = (t < T.arrowB[0]) ? 0 : n;
    if (rEnd - RIBBON_START >= 2) {
      const cnt = rEnd - RIBBON_START + 1;
      const pos = new Float32Array(cnt * 2 * 3), col = new Float32Array(cnt * 2 * 4), idx = [];
      for (let k = 0; k < cnt; k++) {
        const p = DENSE[RIBBON_START + k];
        pos.set([p.x, p.y, Z], k * 6); pos.set([p.x, 0.02, Z], k * 6 + 3);
        const fadeIn = clamp(k / 14) * (1 - prog(k, cnt - 70, cnt - 1));
        col.set([0.2, 0.55, 1.0, 0.22 * fadeIn], k * 8);
        col.set([0.1, 0.3, 0.9, 0.0], k * 8 + 4);
        if (k < cnt - 1) { const a = k * 2; idx.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
      }
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
      g.setAttribute('color', new THREE.BufferAttribute(col, 4));
      g.setIndex(idx);
      this.ribbon.geometry.dispose(); this.ribbon.geometry = g; this.ribbon.visible = true;
    } else this.ribbon.visible = false;

    // nodes
    for (const nd of this.nodes) {
      const k = E.outBack(prog(n - nd.i, 0, 14) * (t >= T.arrowB[0] ? 1 : 0));
      nd.m.scale.setScalar(Math.max(0.001, k)); nd.m.visible = k > 0.01;
      nd.line.visible = k > 0.3; nd.foot.visible = k > 0.01;
      nd.foot.material.opacity = 0.8 * clamp(k);
    }

    // target
    const tp = E.outBack(prog(t, T.target[0], T.target[1]), 1.5);
    this.target.visible = tp > 0.001;
    this.target.scale.setScalar(Math.max(0.001, tp));
    this.target.rotation.y = -0.22 + Math.sin(t * 1.3) * 0.05;
    this.tGlow.material.opacity = (this.mirror ? 0 : 0.5) * clamp(tp) * (0.85 + 0.15 * Math.sin(t * 3));
    // pulse ring
    const pr = prog(t, 5.45, 6.0);
    const ps = 1 + pr * 0.9;
    this.pulse.scale.set(ps, ps, 1);
    this.pulse.material.opacity = this.mirror ? 0 : (pr > 0 ? 0.9 * (1 - pr) : 0) * clamp(tp);

    // ripples
    for (const r of this.ripples) {
      const k = prog(t, r.t0, r.t0 + 1.0);
      const s = lerp(0.9, 2.6, E.outCubic(k));
      r.m.scale.set(s, s, 1);
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
/* camera path (Hermite spline through keyframes)                      */
/* ------------------------------------------------------------------ */
const KEYS = [
  { t: 0.0, p: [-4.8, 3.4, 10.4], l: [-2.3, 1.5, 0.5], f: 30 },
  { t: 2.0, p: [-2.9, 3.7, 12.9], l: [-0.5, 1.85, 0.5], f: 30 },
  { t: 3.9, p: [-1.0, 4.4, 15.9], l: [0.4, 2.2, 0.5], f: 30 },
  { t: 4.85, p: [1.7, 6.0, 23.6], l: [4.3, 2.5, 0.6], f: 30 },
  { t: 6.0, p: [2.6, 6.9, 26.6], l: [5.2, 2.55, 0.6], f: 30 },
];
function hermite(v0, v1, m0, m1, h, s) {
  const s2 = s * s, s3 = s2 * s;
  return (2 * s3 - 3 * s2 + 1) * v0 + (s3 - 2 * s2 + s) * h * m0 + (-2 * s3 + 3 * s2) * v1 + (s3 - s2) * h * m1;
}
function keyVal(get, t) {
  const n = KEYS.length;
  let i = 0; while (i < n - 2 && t > KEYS[i + 1].t) i++;
  const a = KEYS[i], b = KEYS[i + 1], h = b.t - a.t, s = clamp((t - a.t) / h);
  const tan = (k) => {
    if (k === 0 || k === n - 1) return 0;                       // ease in / ease out
    return (get(KEYS[k + 1]) - get(KEYS[k - 1])) / (KEYS[k + 1].t - KEYS[k - 1].t);
  };
  return hermite(get(a), get(b), tan(i), tan(i + 1), h, s);
}
const lookV = new THREE.Vector3();
function setCamera(t) {
  const px = keyVal(k => k.p[0], t), py = keyVal(k => k.p[1], t), pz = keyVal(k => k.p[2], t);
  const lx = keyVal(k => k.l[0], t), ly = keyVal(k => k.l[1], t), lz = keyVal(k => k.l[2], t);
  camera.position.set(px + Math.sin(t * 1.05) * 0.14, py + Math.sin(t * 0.8 + 1) * 0.07, pz);
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
const bloom = new UnrealBloomPass(new THREE.Vector2(W, H), 0.4, 0.6, 0.92);
composer.addPass(bloom);
composer.addPass(new OutputPass());

/* ------------------------------------------------------------------ */
/* DOM overlays                                                        */
/* ------------------------------------------------------------------ */
const el = {
  c1: document.getElementById('card1'), c2: document.getElementById('card2'),
  badge: document.getElementById('badge'), pct: document.getElementById('pct'),
  head: document.getElementById('headline'), scrim: document.getElementById('scrim'),
};
const v3 = new THREE.Vector3();
function project(x, y, z) {
  v3.set(x, y, z).project(camera);
  return [(v3.x * 0.5 + 0.5) * W, (-v3.y * 0.5 + 0.5) * H];
}
function place(node, p, x, y, s, dy = 26) {
  node.style.opacity = p.toFixed(3);
  node.style.transform = `translate(${x.toFixed(1)}px,${y.toFixed(1)}px) translate(-50%,-50%) translateY(${((1 - p) * dy).toFixed(1)}px) scale(${s.toFixed(4)})`;
  node.style.filter = p < 1 ? `blur(${((1 - p) * 8).toFixed(1)}px)` : 'none';
}
function updateOverlays(t) {
  const dist = camera.position.distanceTo(lookV);
  // labels shrink a little as the camera pulls back so they never crowd the graph
  const cs = clamp(Math.pow(11.5 / dist, 0.72), 0.7, 1.1);
  const lab = (bar, node, p) => {
    const [sx, sy] = project(bar.x, 0, 1.25);
    place(node, E.outCubic(p), sx, sy + 62 * cs, cs);
  };
  lab(BARS[0], el.c1, prog(t, T.card1[0], T.card1[1]));
  lab(BARS[1], el.c2, prog(t, T.card2[0], T.card2[1]));

  // badge
  const bp = E.outBack(prog(t, T.badge[0], T.badge[1]), 1.3);
  const [bx, by] = project(0.1, 5.15, Z);
  const bs = clamp(Math.pow(11.5 / dist, 0.62), 0.7, 1.1);
  place(el.badge, clamp(bp), bx, by, bs * (0.88 + 0.12 * clamp(bp)), 18);
  const cnt = Math.round(50 * E.outCubic(prog(t, T.count[0], T.count[1])));
  el.pct.textContent = '+' + cnt + '%';

  // headline (bottom centre)
  const h1 = E.outCubic(prog(t, T.headline1[0], T.headline1[1]));
  const h2 = E.outCubic(prog(t, T.headline2[0], T.headline2[1]));
  const l1 = el.head.querySelector('.l1'), l2 = el.head.querySelector('.l2');
  el.head.style.opacity = 1;
  el.scrim.style.opacity = (0.95 * h1).toFixed(3);
  el.head.style.transform = `translate(-50%, ${H - 135}px) translateY(-50%)`;
  l1.style.opacity = h1; l1.style.transform = `translateY(${(1 - h1) * 34}px)`; l1.style.filter = h1 < 1 ? `blur(${(1 - h1) * 9}px)` : 'none';
  l2.style.opacity = h2; l2.style.transform = `translateY(${(1 - h2) * 26}px)`; l2.style.filter = h2 < 1 ? `blur(${(1 - h2) * 7}px)` : 'none';
}

/* ------------------------------------------------------------------ */
/* frame entry point                                                   */
/* ------------------------------------------------------------------ */
await document.fonts.load('800 40px Inter');
await document.fonts.load('700 40px Inter');
await document.fonts.ready;

window.renderAt = (t) => {
  setCamera(t);
  drawBG(t, lookV.x, lookV.y);
  real.update(t); refl.update(t);
  key.position.set(-7 + Math.sin(t * .7) * 0.8, 13, 10);
  composer.render();
  updateOverlays(t);
  return true;
};
window.DUR = DUR;
window.probe = (t, pts) => { setCamera(t); return pts.map(p => project(p[0], p[1], p[2])); };
window.__ready = true;
window.renderAt(0);
