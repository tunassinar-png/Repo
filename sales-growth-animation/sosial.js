(async function () {
const W = 1920, H = 1080, DUR = 5;
const dpr = window.devicePixelRatio || 1;
const cv = document.getElementById('cv'); cv.width = W * dpr; cv.height = H * dpr;
const c = cv.getContext('2d');
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const prog = (t, a, b) => clamp((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const E = {
  outCubic: x => 1 - Math.pow(1 - x, 3), outQuart: x => 1 - Math.pow(1 - x, 4),
  inOutCubic: x => (x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
  outBack: (x, s = 1.6) => 1 + (s + 1) * Math.pow(x - 1, 3) + s * Math.pow(x - 1, 2),
};
function mulberry32(a) { return function () { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const rr = (x, y, w, h, r) => { c.beginPath(); c.roundRect(x, y, w, h, r); };
const font = (w, px, it) => `${it ? 'italic ' : ''}${w} ${px}px Inter, Helvetica, Arial, sans-serif`;
function text(s, x, y, f, fill, align = 'center', shadow) {
  c.font = f; c.textAlign = align; c.textBaseline = 'middle';
  if (shadow) { c.shadowColor = shadow[0]; c.shadowBlur = shadow[1]; c.shadowOffsetY = shadow[2] || 0; }
  c.fillStyle = fill; c.fillText(s, x, y);
  c.shadowColor = 'transparent'; c.shadowBlur = 0; c.shadowOffsetY = 0;
}
function goldGrad(y0, y1) { const g = c.createLinearGradient(0, y0, 0, y1); g.addColorStop(0, '#fff7d6'); g.addColorStop(.4, '#f7d56e'); g.addColorStop(.75, '#e2a93a'); g.addColorStop(1, '#b9852a'); return g; }

/* ----------------------------- background ---------------------------- */
const rng = mulberry32(777);
const sparks = Array.from({ length: 8 }, () => { const n = 9 + Math.floor(rng() * 5); let y = rng() * .4; const pts = []; for (let k = 0; k < n; k++) { y += (rng() - .38) * .35; pts.push(y); } return { x: rng() * 1.1 - .05, y: rng() * .9 + .03, w: .12 + rng() * .12, h: .05 + rng() * .05, pts, gold: rng() > .6, ph: rng() * 6.28 }; });
const motes = Array.from({ length: 70 }, () => ({ x: rng(), y: rng(), r: .6 + rng() * 1.8, s: .01 + rng() * .03, ph: rng() * 6.28, gold: rng() > .6 }));
function drawBG(t) {
  let g = c.createRadialGradient(W * .55, H * .38, 0, W * .55, H * .38, W * .95);
  g.addColorStop(0, '#17448f'); g.addColorStop(.4, '#0b2763'); g.addColorStop(.78, '#061640'); g.addColorStop(1, '#030c26');
  c.fillStyle = g; c.fillRect(0, 0, W, H);
  g = c.createRadialGradient(W * .85, H * .22, 0, W * .85, H * .22, W * .35);
  g.addColorStop(0, 'rgba(255,196,92,0.14)'); g.addColorStop(1, 'rgba(255,196,92,0)'); c.fillStyle = g; c.fillRect(0, 0, W, H);
  // fine grid, fades towards the edges
  const step = 80, off = (t * 5) % step;
  c.save(); c.lineWidth = 1;
  for (let x = -step + (off % step); x < W + step; x += step) { const major = Math.round((x - off) / step) % 5 === 0; c.strokeStyle = major ? 'rgba(110,170,255,0.13)' : 'rgba(90,150,240,0.06)'; c.beginPath(); c.moveTo(x, 0); c.lineTo(x, H); c.stroke(); }
  for (let y = 0; y < H + step; y += step) { const major = Math.round(y / step) % 5 === 0; c.strokeStyle = major ? 'rgba(110,170,255,0.13)' : 'rgba(90,150,240,0.06)'; c.beginPath(); c.moveTo(0, y); c.lineTo(W, y); c.stroke(); }
  c.restore();
  // sparklines
  c.lineJoin = 'round'; c.lineCap = 'round';
  for (const s of sparks) {
    const px = s.x * W + Math.sin(t * .3 + s.ph) * 10, py = s.y * H + Math.sin(t * .6 + s.ph) * 5, ww = s.w * W, hh = s.h * H;
    const col = s.gold ? '255,205,110' : '120,185,255';
    c.shadowColor = `rgba(${col},0.8)`; c.shadowBlur = 10; c.strokeStyle = `rgba(${col},0.22)`; c.lineWidth = 2; c.beginPath();
    s.pts.forEach((v, k) => { const x = px + (k / (s.pts.length - 1)) * ww, y = py - v * hh * 2.2; k ? c.lineTo(x, y) : c.moveTo(x, y); }); c.stroke();
    c.shadowBlur = 0;
  }
  for (const m of motes) {
    const x = m.x * W, y = (((m.y - t * m.s) % 1 + 1) % 1) * H, a = .25 + .25 * Math.sin(t * 1.6 + m.ph), col = m.gold ? '255,215,130' : '170,210,255';
    const gr = c.createRadialGradient(x, y, 0, x, y, m.r * 5); gr.addColorStop(0, `rgba(${col},${a})`); gr.addColorStop(1, `rgba(${col},0)`);
    c.fillStyle = gr; c.beginPath(); c.arc(x, y, m.r * 5, 0, 7); c.fill();
  }
}


/* ------------------------------ phones + chips ------------------------------ */
const NFR = 142, T0 = 0.45;                    // footage starts playing at 0.45 s
const stage = document.getElementById('stage');
const PH = [
  { id: 'web', x: 480,  tilt: 7,  chip: 'web', pop: 1.0, src: 'assets/web/f_' },
  { id: 'fb',  x: 960,  tilt: 0,  chip: 'fb',  pop: 2.0, src: 'assets/fb/f_' },
  { id: 'tt',  x: 1440, tilt: -7, chip: 'tt',  pop: 3.0, src: 'assets/tt/f_' },
];
const el = {}; PH.forEach(p => { el[p.id] = { phone: document.getElementById('ph_' + p.id), chip: document.getElementById('chip_' + p.id), ring: document.getElementById('ring_' + p.id), img: document.getElementById('img_' + p.id) }; });
const last = {};
async function setFrame(p, t) {
  if (!p.src) return;
  const n = clamp(Math.floor((t - T0) * 30) + 1, 1, NFR);
  if (last[p.id] === n) return; last[p.id] = n;
  const im = el[p.id].img; im.src = p.src + String(n).padStart(4, '0') + '.jpg';
  try { await im.decode(); } catch (e) {}
}
function fixed(node, p, dx, dy) { node.style.opacity = p.toFixed(3); node.style.transform = `translate(${(dx * (1 - p)).toFixed(1)}px,${(dy * (1 - p)).toFixed(1)}px)`; node.style.filter = p < 1 ? `blur(${((1 - p) * 7).toFixed(1)}px)` : 'none'; }

await document.fonts.load('800 40px Inter'); await document.fonts.load('700 40px Inter'); await document.fonts.ready;
await new Promise(r => { const im = new Image(); im.onload = r; im.onerror = r; im.src = 'kamaar-logo-white.png'; });
// preload first frames so frame 0 is ready
for (const p of PH) await setFrame(p, T0);

window.renderAt = async (t) => {
  c.setTransform(dpr, 0, 0, dpr, 0, 0); c.clearRect(0, 0, W, H);
  drawBG(t);
  // header
  fixed(document.getElementById('logo'), E.outCubic(prog(t, 0, .6)), -40, 0);
  document.getElementById('divider').style.opacity = prog(t, .2, .8).toFixed(3);
  fixed(document.getElementById('title'), E.outCubic(prog(t, .2, .85)), 50, 0);
  for (let i = 0; i < PH.length; i++) {
    const p = PH[i], e = el[p.id];
    // phone entrance (staggered)
    const q = E.outCubic(prog(t, 0.2 + i * 0.12, 0.9 + i * 0.12));
    const glow = Math.max(0, 1 - (t - p.pop) / 0.9) * (t >= p.pop ? 1 : 0);
    e.phone.style.opacity = q.toFixed(3);
    e.phone.style.transform = `translate(${p.x - 170}px, ${300 + (1 - q) * 90}px) perspective(1800px) rotateY(${p.tilt}deg) scale(${0.94 + 0.06 * q})`;
    e.phone.style.boxShadow = `0 40px 80px rgba(0,0,0,.55), 0 0 0 2px rgba(255,255,255,.08), 0 0 ${30 + 60 * glow}px rgba(255,200,90,${0.15 + 0.55 * glow})`;
    // chip pop-up
    const k = prog(t, p.pop, p.pop + 0.5), s = E.outBack(k, 2.1);
    const bob = k >= 1 ? Math.sin((t - p.pop) * 4) * 4 : 0;
    e.chip.style.opacity = clamp(k * 3).toFixed(3);
    e.chip.style.transform = `translate(${p.x}px, ${232 + bob}px) translate(-50%,-50%) scale(${Math.max(0.001, s).toFixed(4)}) rotate(${((1 - clamp(k)) * -6).toFixed(2)}deg)`;
    // expanding ring at the pop moment
    const rk = prog(t, p.pop, p.pop + 0.6);
    e.ring.style.opacity = (rk > 0 && rk < 1 ? 0.8 * (1 - rk) : 0).toFixed(3);
    e.ring.style.transform = `translate(${p.x}px, 232px) translate(-50%,-50%) scale(${(0.8 + rk * 1.1).toFixed(3)})`;
    await setFrame(p, t);
  }
  return true;
};
window.DUR = DUR; window.__ready = true; await window.renderAt(0);
})();
