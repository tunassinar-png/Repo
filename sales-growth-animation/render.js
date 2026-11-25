// Renders the animation page frame-by-frame with headless Chromium (WebGL via SwiftShader)
// and pipes PNG frames straight into ffmpeg.
//
// usage:
//   node render.js preview <out_dir> <t1,t2,...> [dpr]        -> PNG stills
//   node render.js video   <out.mp4> [fps=30] [dpr=2] [audio.wav]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const http = require('http');

const ROOT = __dirname;
const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.jpg': 'image/jpeg', '.png': 'image/png' };
function serve() {
  return new Promise(res => {
    const s = http.createServer((q, r) => {
      const f = path.join(ROOT, decodeURIComponent(q.url.split('?')[0]).replace(/^\/$/, '/index.html'));
      if (!f.startsWith(ROOT) || !fs.existsSync(f)) { r.writeHead(404); return r.end(); }
      r.writeHead(200, { 'Content-Type': MIME[path.extname(f)] || 'application/octet-stream' });
      fs.createReadStream(f).pipe(r);
    }).listen(0, '127.0.0.1', () => res(s));
  });
}

async function open(dpr) {
  const server = await serve();
  const browser = await chromium.launch({
    args: ['--use-angle=swiftshader', '--use-gl=angle', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl', '--no-sandbox'],
  });
  const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: dpr });
  const page = await ctx.newPage();
  page.on('console', m => { if (m.type() === 'error') console.error('[page]', m.text()); });
  page.on('pageerror', e => console.error('[pageerror]', e.message));
  await page.goto(`http://127.0.0.1:${server.address().port}/${process.env.PAGE || 'index.html'}`);
  await page.waitForFunction('window.__ready === true', null, { timeout: 120000 });
  return { page, close: async () => { await browser.close(); server.close(); } };
}

(async () => {
  const [mode, out, a3, a4, a5] = process.argv.slice(2);
  if (mode === 'preview') {
    const times = a3.split(',').map(Number); const dpr = Number(a4 || 1);
    fs.mkdirSync(out, { recursive: true });
    const { page, close } = await open(dpr);
    for (const t of times) {
      const t0 = Date.now();
      await page.evaluate(t => window.renderAt(t), t);
      await page.screenshot({ path: path.join(out, `t${t.toFixed(2)}.png`), type: 'png' });
      console.log('t=', t, (Date.now() - t0) + 'ms');
    }
    await close();
  } else if (mode === 'video') {
    const fps = Number(a3 || 30), dpr = Number(a4 || 2), audio = a5;
    const { page, close } = await open(dpr);
    const dur = await page.evaluate('window.DUR');
    const frames = Math.round(dur * fps);
    const args = ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-'];
    if (audio) args.push('-i', audio);
    args.push('-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p',
      '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
      '-vf', 'scale=3840:2160:flags=lanczos,format=yuv420p', '-r', String(fps));
    if (audio) args.push('-c:a', 'aac', '-b:a', '256k', '-shortest');
    args.push('-movflags', '+faststart', out);
    const ff = spawn('ffmpeg', args, { stdio: ['pipe', 'inherit', 'inherit'] });
    const done = new Promise(r => ff.on('close', r));
    const t00 = Date.now();
    for (let i = 0; i < frames; i++) {
      const t = i / fps;
      await page.evaluate(t => window.renderAt(t), t);
      const png = await page.screenshot({ type: 'png' });
      if (!ff.stdin.write(png)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 10 === 0) console.log(`frame ${i + 1}/${frames}  ${((Date.now() - t00) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end();
    await done;
    await close();
    console.log('wrote', out);
  }
})().catch(e => { console.error(e); process.exit(1); });
