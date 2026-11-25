/* Animated sales-growth chart (2D canvas), 10 s.  Data: 2025 = RM1.2 juta, 2026 = RM1.8 juta.
   Derived (not invented): difference RM0.6 juta, growth +50%. */
(async function () {
const W = 1920, H = 1080, DUR = 10;
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

/* ------------------------------ layout ------------------------------ */
const A = { x0: 270, x1: 1650, base: 900, k: 285 };            // value 0 -> y=900, 2.0 -> y=330
const BW = 220;
const BARS = [
  { x: 600,  v: 1.2, yr: '2025', grow: [1.3, 2.4], c0: '#06215e', c1: '#2e6fdc', plate: 1.15 },
  { x: 1080, v: 1.8, yr: '2026', grow: [3.6, 5.0], c0: '#08307f', c1: '#58aaff', plate: 3.5 },
];
const topY = (b) => A.base - b.v * A.k;
const P1 = { x: BARS[0].x, y: topY(BARS[0]) - 12 }, P2 = { x: BARS[1].x, y: topY(BARS[1]) - 12 };
const TL = { header: [0.0, 0.9], panel: [0.3, 1.1], grid: [0.5, 1.4], line: [5.0, 6.6], guide: [6.5, 7.4], diff: [7.1, 7.8], badge: [6.9, 7.7], count: [6.95, 7.9] };

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

/* ------------------------------- chart ------------------------------- */
function drawPanel(t) {
  const p = E.outCubic(prog(t, ...TL.panel));
  c.globalAlpha = p; c.save(); c.translate(0, (1 - p) * 30);
  rr(150, 205, 1620, 815, 34);
  const g = c.createLinearGradient(0, 205, 0, 1020); g.addColorStop(0, 'rgba(18,48,120,0.55)'); g.addColorStop(1, 'rgba(6,22,66,0.62)');
  c.shadowColor = 'rgba(0,0,0,0.5)'; c.shadowBlur = 50; c.shadowOffsetY = 18; c.fillStyle = g; c.fill();
  c.shadowColor = 'transparent'; c.shadowBlur = 0; c.shadowOffsetY = 0;
  c.lineWidth = 2; c.strokeStyle = 'rgba(238,190,84,0.55)'; c.stroke();
  c.restore(); c.globalAlpha = 1;
}
function drawAxes(t) {
  const p = prog(t, ...TL.grid);
  const vals = [0, 0.5, 1.0, 1.5, 2.0];
  vals.forEach((v, i) => {
    const q = E.outCubic(prog(t, TL.grid[0] + i * 0.08, TL.grid[0] + 0.5 + i * 0.08));
    const y = A.base - v * A.k;
    c.globalAlpha = q;
    c.strokeStyle = v === 0 ? 'rgba(240,200,110,0.75)' : 'rgba(150,190,255,0.22)'; c.lineWidth = v === 0 ? 3 : 1.5;
    c.setLineDash(v === 0 ? [] : [10, 10]); c.beginPath(); c.moveTo(A.x0, y); c.lineTo(lerp(A.x0, A.x1, q), y); c.stroke(); c.setLineDash([]);
    text(v === 0 ? '0' : v.toFixed(1), A.x0 - 26, y, font(700, 30), 'rgba(220,232,255,0.9)', 'right');
  });
  c.globalAlpha = E.outCubic(prog(t, TL.grid[0] + .3, TL.grid[1]));
  text('JUALAN (RM JUTA)', A.x0 - 80, 275, font(700, 26), '#f3c75a', 'left');
  c.globalAlpha = 1;
}
function barPath(b, h) { rr(b.x - BW / 2, A.base - h, BW, h, [10, 10, 2, 2]); }
function drawBar(t, b, idx) {
  const p = E.outQuart(prog(t, ...b.grow)); const h = b.v * A.k * p;
  if (h < 2) return 0;
  // glow
  c.save(); c.shadowColor = idx ? 'rgba(90,170,255,0.55)' : 'rgba(60,120,240,0.5)'; c.shadowBlur = 40;
  barPath(b, h); const g = c.createLinearGradient(0, A.base - b.v * A.k, 0, A.base); g.addColorStop(0, b.c1); g.addColorStop(1, b.c0); c.fillStyle = g; c.fill(); c.restore();
  // glossy highlight
  c.save(); barPath(b, h); c.clip();
  let hg = c.createLinearGradient(b.x - BW / 2, 0, b.x + BW / 2, 0); hg.addColorStop(0, 'rgba(255,255,255,0.28)'); hg.addColorStop(.22, 'rgba(255,255,255,0.06)'); hg.addColorStop(.7, 'rgba(255,255,255,0)'); hg.addColorStop(1, 'rgba(0,10,60,0.30)');
  c.fillStyle = hg; c.fillRect(b.x - BW / 2, A.base - h, BW, h);
  const sg = c.createLinearGradient(0, A.base - h, 0, A.base - h + 90); sg.addColorStop(0, 'rgba(255,255,255,0.35)'); sg.addColorStop(1, 'rgba(255,255,255,0)'); c.fillStyle = sg; c.fillRect(b.x - BW / 2, A.base - h, BW, 90);
  c.restore();
  // gold cap
  c.save(); c.shadowColor = 'rgba(255,200,90,0.8)'; c.shadowBlur = 16;
  rr(b.x - BW / 2 - 6, A.base - h - 10, BW + 12, 14, 6); c.fillStyle = goldGrad(A.base - h - 10, A.base - h + 4); c.fill(); c.restore();
  // value text counting with the bar
  const val = b.v * p;
  const ty = A.base - h * 0.5;
  const f = clamp((p - 0.12) / 0.2);
  c.globalAlpha = f;
  text('RM' + val.toFixed(1), b.x, ty - 20, font(800, 62), '#fff', 'center', ['rgba(0,20,90,0.65)', 14, 4]);
  text('JUTA', b.x, ty + 36, font(800, 42), '#fff', 'center', ['rgba(0,20,90,0.65)', 14, 4]);
  c.globalAlpha = 1;
  return p;
}
function drawPlate(t, b) {
  const q = E.outBack(prog(t, b.plate, b.plate + .5)); if (q <= 0.01) return;
  c.save(); c.translate(b.x, 948); c.scale(q, q); c.globalAlpha = clamp(q);
  rr(-120, -30, 240, 60, 12); c.shadowColor = 'rgba(0,10,50,0.55)'; c.shadowBlur = 22; c.shadowOffsetY = 8;
  const g = c.createLinearGradient(0, -30, 0, 30); g.addColorStop(0, '#fff'); g.addColorStop(1, '#dde5f3'); c.fillStyle = g; c.fill();
  c.shadowColor = 'transparent'; c.shadowBlur = 0; c.shadowOffsetY = 0;
  text(b.yr, 0, 2, font(800, 42), '#0b1f52'); c.restore();
}
function marker(x, y, t, appear) {
  const q = E.outBack(prog(t, appear, appear + .45)); if (q <= 0.01) return;
  c.save(); c.translate(x, y);
  const pulse = (t * 0.9) % 1; c.globalAlpha = clamp(q) * (1 - pulse) * 0.6; c.strokeStyle = '#ffd36b'; c.lineWidth = 3; c.beginPath(); c.arc(0, 0, 16 + pulse * 30, 0, 7); c.stroke();
  c.globalAlpha = clamp(q); c.shadowColor = 'rgba(255,200,80,0.95)'; c.shadowBlur = 28;
  c.fillStyle = '#fff6d2'; c.beginPath(); c.arc(0, 0, 13 * q, 0, 7); c.fill();
  c.shadowBlur = 0; c.fillStyle = '#e2a93a'; c.beginPath(); c.arc(0, 0, 6 * q, 0, 7); c.fill(); c.restore();
}
const REACH = 0.9;   // arrow tip ends just before the 2026 marker
function lineTip(t) { const p = E.inOutCubic(prog(t, ...TL.line)); const r = p * REACH; return { p, x: lerp(P1.x, P2.x, r), y: lerp(P1.y, P2.y, r) }; }
function drawArea(t) {
  const { p, x, y } = lineTip(t); if (p <= 0.001) return;
  const g = c.createLinearGradient(0, P2.y, 0, A.base); g.addColorStop(0, 'rgba(247,200,90,0.34)'); g.addColorStop(1, 'rgba(247,200,90,0)');
  c.beginPath(); c.moveTo(P1.x, P1.y); c.lineTo(x, y); c.lineTo(x, A.base); c.lineTo(P1.x, A.base); c.closePath(); c.fillStyle = g; c.fill();
}
function drawLine(t) {
  const { p, x, y } = lineTip(t); if (p <= 0.001) return;
  c.lineCap = 'round';
  c.save(); c.shadowColor = 'rgba(255,190,70,0.95)'; c.shadowBlur = 30;
  c.strokeStyle = '#ffd36b'; c.lineWidth = 9; c.beginPath(); c.moveTo(P1.x, P1.y); c.lineTo(x, y); c.stroke(); c.restore();
  c.strokeStyle = '#fff6d8'; c.lineWidth = 3.5; c.beginPath(); c.moveTo(P1.x, P1.y); c.lineTo(x, y); c.stroke();
  // arrow head
  const ang = Math.atan2(P2.y - P1.y, P2.x - P1.x);
  c.save(); c.translate(x, y); c.rotate(ang); c.shadowColor = 'rgba(255,190,70,0.95)'; c.shadowBlur = 24;
  c.fillStyle = '#fff1bf'; c.beginPath(); c.moveTo(22, 0); c.lineTo(-14, -17); c.lineTo(-6, 0); c.lineTo(-14, 17); c.closePath(); c.fill(); c.restore();
  // travelling sparkle once the line is complete
  if (t > 7.8) {
    const k = ((t - 7.8) % 2.2) / 2.2, sx = lerp(P1.x, P2.x, k), sy = lerp(P1.y, P2.y, k);
    const gr = c.createRadialGradient(sx, sy, 0, sx, sy, 34); gr.addColorStop(0, 'rgba(255,255,255,0.95)'); gr.addColorStop(1, 'rgba(255,230,150,0)');
    c.globalAlpha = Math.sin(k * Math.PI); c.fillStyle = gr; c.beginPath(); c.arc(sx, sy, 34, 0, 7); c.fill(); c.globalAlpha = 1;
  }
}
function arrowV(x, y, dir) { // small arrowhead pointing up (dir=-1) or down (dir=1)
  c.beginPath(); c.moveTo(x, y); c.lineTo(x - 11, y - dir * 20); c.lineTo(x + 11, y - dir * 20); c.closePath(); c.fill();
}
function drawDiff(t) {
  const g = E.outCubic(prog(t, ...TL.guide)); const BX = 1290;
  if (g > 0) {
    c.save(); c.strokeStyle = 'rgba(255,214,120,0.8)'; c.lineWidth = 2.5; c.setLineDash([12, 10]);
    c.beginPath(); c.moveTo(P1.x + 20, P1.y + 12); c.lineTo(lerp(P1.x + 20, BX + 20, g), P1.y + 12); c.stroke();
    c.beginPath(); c.moveTo(P2.x + 20, P2.y + 12); c.lineTo(lerp(P2.x + 20, BX + 20, g), P2.y + 12); c.stroke();
    c.setLineDash([]);
    // bracket (vertical double arrow)
    const y1 = P1.y + 12, y2 = P2.y + 12, mid = (y1 + y2) / 2, half = (y1 - y2) / 2 * g;
    c.strokeStyle = '#ffd36b'; c.fillStyle = '#ffd36b'; c.lineWidth = 4; c.shadowColor = 'rgba(255,190,70,0.8)'; c.shadowBlur = 14;
    c.beginPath(); c.moveTo(BX, mid + half - 18); c.lineTo(BX, mid - half + 18); c.stroke();
    arrowV(BX, mid - half, -1); arrowV(BX, mid + half, 1);
    c.restore();
  }
  // difference card
  const q = E.outCubic(prog(t, ...TL.diff)); if (q <= 0.01) return;
  c.save(); c.globalAlpha = q; c.translate(1500, (P1.y + P2.y) / 2 + 12 + (1 - q) * 20);
  rr(-150, -42, 300, 84, 20); const gg = c.createLinearGradient(0, -42, 0, 42); gg.addColorStop(0, 'rgba(24,56,128,0.95)'); gg.addColorStop(1, 'rgba(8,24,70,0.96)');
  c.shadowColor = 'rgba(0,0,0,0.5)'; c.shadowBlur = 30; c.shadowOffsetY = 10; c.fillStyle = gg; c.fill(); c.shadowColor = 'transparent'; c.shadowBlur = 0; c.shadowOffsetY = 0;
  c.lineWidth = 2.5; c.strokeStyle = 'rgba(238,190,84,0.85)'; c.stroke();
  text('+RM0.6 JUTA', 0, 3, font(800, 40), '#ffe08a');
  c.restore();
}
function drawBadge(t) {
  const q = clamp(E.outBack(prog(t, ...TL.badge), 1.4)); if (q <= 0.01) return;
  const cnt = Math.round(50 * E.outCubic(prog(t, ...TL.count)));
  c.save(); c.translate(1500, 322); c.scale(q * 0.92, q * 0.92); c.globalAlpha = clamp(q);
  rr(-190, -92, 380, 184, 34);
  c.shadowColor = 'rgba(230,60,40,0.55)'; c.shadowBlur = 44; c.shadowOffsetY = 12;
  const g = c.createLinearGradient(0, -92, 0, 92); g.addColorStop(0, '#e32a2a'); g.addColorStop(1, '#8f0b0b'); c.fillStyle = g; c.fill();
  c.shadowColor = 'transparent'; c.shadowBlur = 0; c.shadowOffsetY = 0;
  const bg = c.createLinearGradient(0, -92, 0, 92); bg.addColorStop(0, '#fff0b0'); bg.addColorStop(.6, '#e2a93a'); bg.addColorStop(1, '#b9852a');
  c.lineWidth = 6; c.strokeStyle = bg; c.stroke();
  text('PENINGKATAN', 0, -52, font(800, 40), '#fff', 'center', ['rgba(80,0,0,0.6)', 8, 3]);
  text('+' + cnt + '%', 0, 20, font(800, 118), '#fff', 'center', ['rgba(80,0,0,0.55)', 12, 5]);
  c.restore();
}

/* ------------------------------- DOM header ------------------------------- */
const $ = id => document.getElementById(id);
const head = { logo: $('logo'), div: $('divider'), title: $('title') };
function fixed(node, p, dx) { node.style.opacity = p.toFixed(3); node.style.transform = `translate(${(dx * (1 - p)).toFixed(1)}px,0)`; node.style.filter = p < 1 ? `blur(${((1 - p) * 7).toFixed(1)}px)` : 'none'; }

await document.fonts.load('800 40px Inter'); await document.fonts.load('700 40px Inter'); await document.fonts.ready;
await new Promise(r => { const im = new Image(); im.onload = r; im.onerror = r; im.src = 'kamaar-logo-white.png'; });

window.renderAt = (t) => {
  c.setTransform(dpr, 0, 0, dpr, 0, 0); c.clearRect(0, 0, W, H);
  drawBG(t);
  // slow cinematic push-in on the chart
  const z = 1 + 0.035 * E.inOutCubic(t / DUR), dx = -14 * (t / DUR);
  c.save(); c.translate(W / 2 + dx, 600); c.scale(z, z); c.translate(-W / 2, -600);
  drawPanel(t); drawAxes(t); drawArea(t);
  BARS.forEach((b, i) => drawBar(t, b, i));
  drawLine(t);
  BARS.forEach((b, i) => { marker(b.x, topY(b) - 12, t, b.grow[1] - 0.15); drawPlate(t, b); });
  drawDiff(t); drawBadge(t);
  c.restore();
  const hp = E.outCubic(prog(t, ...TL.header)); fixed(head.logo, E.outCubic(prog(t, 0, .6)), -40);
  head.div.style.opacity = prog(t, .2, .8).toFixed(3); fixed(head.title, E.outCubic(prog(t, .2, .85)), 50);
  return true;
};
window.DUR = DUR; window.__ready = true; window.renderAt(0);
})();
