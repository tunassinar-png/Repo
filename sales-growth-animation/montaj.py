#!/usr/bin/env python3
"""Cinematic re-grade of a montage clip.  16:9, 2560x1440, 30 fps, 9 s, no text added.

usage:  python3 montaj.py <input.mp4> <output.mp4> [--preview t1,t2,...] [--out_dir dir]

Pipeline: ffmpeg decodes + time-stretches the source (8.3 s -> 9.0 s, frame-blended),
python/numpy applies slow push-in, cut-punch, focus pull, chromatic aberration, teal/orange
grade, bloom + anamorphic streaks, light leaks on cuts, golden bokeh dust, light sweep on the
logo, vignette, film grain and a fade-out; ffmpeg encodes (H.264 + AAC with synthesised
whooshes / sub hit mixed over the original music).
"""
import subprocess, sys, os, json, numpy as np
from PIL import Image, ImageFilter

W, H, SW, SH = 2560, 1440, 1920, 1080
FPS, DUR = 30, 9.0
SRC_DUR = None                       # filled from ffprobe
CUTS_SRC = [2.2667, 3.0667, 4.6333, 5.0, 5.6333, 6.5667, 7.4]     # scene changes in the source (s)
HOLD_AT = 7.95                      # source time where the last shot goes into slow motion

clamp = lambda x, a=0.0, b=1.0: np.minimum(b, np.maximum(a, x))
def ease(x): x = min(1, max(0, x)); return x * x * (3 - 2 * x)

# ------------------------------------------------------------------ static assets
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
RAD = np.sqrt(((XX - W / 2) / (W / 2)) ** 2 + ((YY - H / 2) / (H / 2)) ** 2) / np.sqrt(2)
VIGN = (1.0 - 0.52 * np.clip(RAD * 1.15, 0, 1) ** 2.3).astype(np.float32)[..., None]
del YY, XX
rng = np.random.default_rng(2026)

# bokeh dust (half-res layer)
NP = 110
P = dict(x=rng.random(NP), y=rng.random(NP), r=rng.choice([2, 3, 4, 6, 9, 14], NP, p=[.28, .24, .2, .14, .09, .05]),
         v=0.012 + rng.random(NP) * 0.035, sw=rng.random(NP) * 6.28, sa=0.004 + rng.random(NP) * 0.012,
         ph=rng.random(NP) * 6.28, a=0.25 + rng.random(NP) * 0.6)
KERN = {}
for r in set(P['r'].tolist()):
    k = int(r * 2.6) | 1
    g = np.arange(k) - k // 2
    d = np.sqrt(g[:, None] ** 2 + g[None, :] ** 2) / (r * 1.25)
    KERN[r] = (np.exp(-d ** 3.2) * 0.9).astype(np.float32)       # soft-edged disc (bokeh-like)

def dust_layer(t):
    hw, hh = W // 2, H // 2
    L = np.zeros((hh, hw), np.float32)
    for i in range(NP):
        r = int(P['r'][i])
        x = ((P['x'][i] + P['sa'][i] * np.sin(t * 0.7 + P['sw'][i])) % 1.0) * hw
        y = ((P['y'][i] - P['v'][i] * t) % 1.0) * hh
        a = P['a'][i] * (0.55 + 0.45 * np.sin(t * 2.1 + P['ph'][i]))
        k = KERN[r]; kh = k.shape[0] // 2
        x0, y0 = int(x) - kh, int(y) - kh
        xa, ya = max(0, x0), max(0, y0)
        xb, yb = min(hw, x0 + k.shape[1]), min(hh, y0 + k.shape[0])
        if xb <= xa or yb <= ya: continue
        L[ya:yb, xa:xb] += k[ya - y0:yb - y0, xa - x0:xb - x0] * a
    im = Image.fromarray((np.clip(L, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
    return np.asarray(im, np.float32)[..., None] / 255.0

def blobs(t, cut_pulse):
    """small light-leak texture (180x320x3); warm amber / magenta blobs drifting, pulsing on cuts."""
    h, w = 180, 320
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    out = np.zeros((h, w, 3), np.float32)
    spec = [  # (cx, cy, radius, colour, speed, phase)
        (0.04, 0.35, 0.34, (1.00, 0.45, 0.10), 0.55, 0.0),
        (0.97, 0.62, 0.30, (1.00, 0.22, 0.38), 0.45, 1.9),
        (0.55, -0.05, 0.28, (1.00, 0.62, 0.20), 0.35, 3.3),
        (0.30, 1.05, 0.26, (0.95, 0.30, 0.15), 0.40, 4.6),
    ]
    for cx, cy, rr, col, sp, ph in spec:
        cxp = (cx + 0.10 * np.sin(t * sp + ph)) * w
        cyp = (cy + 0.12 * np.cos(t * sp * 1.3 + ph)) * h
        d = ((xx - cxp) / (rr * w)) ** 2 + ((yy - cyp) / (rr * h * 1.8)) ** 2
        g = np.exp(-d * 2.2)
        out += g[..., None] * np.array(col, np.float32)
    return out * (0.10 + 0.9 * cut_pulse)

def hblur(a, k):          # separable horizontal box blur (cumsum) on small arrays
    pad = np.pad(a, ((0, 0), (k, k), (0, 0)), mode='edge')
    c = np.cumsum(pad, axis=1)
    return (c[:, 2 * k:, :] - c[:, :-2 * k, :]) / (2 * k)

def up(a_small):          # small float array -> full-res via PIL (per channel)
    chans = []
    for c in range(a_small.shape[2]):
        im = Image.fromarray(a_small[..., c].astype(np.float32), mode='F').resize((W, H), Image.BILINEAR)
        chans.append(np.asarray(im, np.float32))
    return np.stack(chans, -1)

# ------------------------------------------------------------------ per-frame look
def look(src_rgb, t, cuts_out, frame_seed):
    # --- camera: slow push-in + gentle sway + punch on every cut ---
    punch = sum(0.045 * np.exp(-(t - tc) / 0.20) for tc in cuts_out if t >= tc)
    pre = sum(0.012 * ease((t - (tc - 0.12)) / 0.12) for tc in cuts_out if tc - 0.12 <= t < tc)
    z = 1.06 + 0.085 * ease(t / DUR) + punch + pre
    vw, vh = SW / z, SH / z
    ax = 0.55 * (SW - vw) / 2 * np.sin(t * 0.55 + 0.6)
    ay = 0.45 * (SH - vh) / 2 * np.sin(t * 0.43 + 2.0)
    cx, cy = SW / 2 + ax, SH / 2 + ay
    box = (cx - vw / 2, cy - vh / 2, cx + vw / 2, cy + vh / 2)

    mr, mg, mb = src_rgb[::8, ::8, 0].mean(), src_rgb[::8, ::8, 1].mean(), src_rgb[::8, ::8, 2].mean()
    gfix = float(np.clip(((mr + mb) / 2 + 1e-3) / (mg + 1e-3), 0.9, 1.0)) ** 0.9
    if gfix < 0.999:
        src_rgb = src_rgb.copy(); src_rgb[..., 1] = np.clip(src_rgb[..., 1] * gfix, 0, 255).astype(np.uint8)
    img = Image.fromarray(src_rgb)
    if t < 1.3:                                                   # focus pull at the start
        img = img.filter(ImageFilter.GaussianBlur(radius=9.0 * (1 - t / 1.3) ** 2))
    img = img.resize((W, H), Image.LANCZOS, box=box)
    img = img.filter(ImageFilter.UnsharpMask(radius=1.6, percent=60, threshold=2))

    # --- chromatic aberration (radial, subtle; grows on cut punches) ---
    ca = 0.0016 + 0.0035 * min(1.0, punch / 0.045 if punch else 0.0)
    r, g, b = img.split()
    def sc(ch, s): return ch.transform((W, H), Image.AFFINE, (s, 0, W / 2 * (1 - s), 0, s, H / 2 * (1 - s)), Image.BILINEAR)
    img = Image.merge('RGB', (r, sc(g, 1 - ca), sc(b, 1 - 2 * ca)))          # scales <= 1 only: no empty edges
    a = np.asarray(img, np.float32) / 255.0

    # --- colour grade: filmic contrast + teal shadows / amber highlights + vibrance ---
    Y = (a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722)[..., None]
    s_curve = a * a * (3 - 2 * a)
    a = clamp(a) ** 0.93                                            # lift mids a little
    s_curve = a * a * (3 - 2 * a)
    a = a + (s_curve - a) * 0.62
    Y = (a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722)[..., None]
    ws = (1 - Y) ** 2.4
    wh = Y ** 2.2
    a = a + ws * np.array([-0.055, 0.000, 0.085], np.float32) + wh * np.array([0.095, 0.035, -0.075], np.float32)
    Y2 = (a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722)[..., None]
    sat = a.max(-1, keepdims=True) - a.min(-1, keepdims=True)
    a = Y2 + (a - Y2) * (1.20 + 0.38 * (1 - clamp(sat * 1.6)))          # vibrance: boost muted colours more
    a = a * 1.06 + 0.008
    a = clamp(a)
    ymean = float(Y2.mean())
    dark = 1.0 - clamp((ymean - 0.25) / 0.55)                       # 1 on dark shots, 0 on the white intro

    # --- bloom + anamorphic streak (computed on a 1/8 res copy) ---
    s8 = a.reshape(H // 8, 8, W // 8, 8, 3).mean((1, 3))
    ys = s8 @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    hl = s8 * (clamp((ys - 0.58) / 0.42) ** 1.4)[..., None]
    soft = np.zeros_like(hl)
    for rad in (3, 8, 18):
        im = [Image.fromarray(np.clip(hl[..., c] * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(rad)) for c in range(3)]
        soft += np.stack([np.asarray(x, np.float32) / 255 for x in im], -1) * (1.0 / 3)
    streak = hblur(hl, 40)
    streak = hblur(streak, 40) * np.array([0.55, 0.80, 1.20], np.float32)
    bloom = up(soft) * (0.55 * (0.35 + 0.65 * dark)) + up(streak) * (0.9 * dark)
    a = 1 - (1 - a) * (1 - clamp(bloom))

    # --- light leaks: base drift + pulse on every cut ---
    pulse = 0.0
    for tc in cuts_out:
        if t >= tc - 0.10:
            pulse = max(pulse, np.exp(-max(0.0, t - tc) / 0.30) * (0.55 if t >= tc else ease((t - (tc - .10)) / 0.10) * 0.55))
    leak = up(blobs(t, pulse)) * (0.30 * (0.25 + 0.75 * dark) + 0.10)
    a = 1 - (1 - a) * (1 - clamp(leak))

    # --- golden light sweep over the logo (dark glyphs only) ---
    if 0.9 <= t <= 2.15:
        k = ease((t - 0.9) / 1.25)
        xs = np.linspace(-0.3, 1.3, W, dtype=np.float32)[None, :]
        ysx = np.linspace(0, 1, H, dtype=np.float32)[:, None]
        d = (xs - (-0.25 + 1.5 * k)) - 0.18 * (ysx - 0.5)
        band = np.exp(-(d / 0.07) ** 2)[..., None].astype(np.float32)
        Yg = (a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722)[..., None]
        a = a + band * (1 - Yg) ** 1.5 * np.array([1.0, 0.72, 0.28], np.float32) * 1.3 * (1 - ease((t - 1.9) / 0.25))
        a = clamp(a)

    # --- golden bokeh dust ---
    d = dust_layer(t) * (0.55 + 0.35 * dark)
    gold = np.array([1.0, 0.78, 0.40], np.float32)
    a = a * (1 - d) + gold * d

    # --- vignette, flicker, grain, fade ---
    a = a * (1 - (1 - VIGN) * (0.55 + 0.45 * dark))
    a = a * (1.0 + 0.008 * np.sin(t * 37.0) + 0.004 * np.sin(t * 91.0))
    r = np.random.default_rng(frame_seed)
    n = r.standard_normal((H // 2, W // 2)).astype(np.float32)
    n = np.repeat(np.repeat(n, 2, 0), 2, 1)[..., None]
    Yf = (a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722)[..., None]
    a = a + n * 0.024 * (0.35 + 1.6 * Yf * (1 - Yf)) * np.array([1.0, 1.0, 1.05], np.float32)
    fade = clamp((DUR - t) / 0.30) ** 1.2
    a = clamp(a) * fade
    return (a * 255 + 0.5).astype(np.uint8)

# ------------------------------------------------------------------ audio fx
def make_fx(path, cuts_out):
    SR = 44100; N = int(SR * DUR); fx = np.zeros((2, N), np.float32)
    r = np.random.default_rng(5)
    def put(sig, t0, g=1.0, pan=0.0):
        i = int(t0 * SR); j = min(N, i + len(sig))
        if j <= i: return
        fx[0, i:j] += sig[:j - i] * g * (1 - max(0, pan)); fx[1, i:j] += sig[:j - i] * g * (1 + min(0, pan))
    def whoosh(dur, up=True):
        n = int(dur * SR); t = np.arange(n) / SR
        x = r.standard_normal(n)
        f = (300 + 5500 * (t / dur) ** 2) if up else (5800 - 5300 * (t / dur))
        ph = np.cumsum(f) / SR
        carrier = np.sin(2 * np.pi * ph * 0.5)
        y = np.diff(x, prepend=0) * (0.55 + 0.45 * carrier)
        env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.6
        return (y / (np.abs(y).max() + 1e-9)) * env
    last = -9
    for k, tc in enumerate(cuts_out):
        if tc - last < 0.5: continue
        last = tc
        w = whoosh(0.55); put(w, tc - 0.30, 0.22, pan=(-0.4 if k % 2 else 0.4))
    # riser into the logo reveal + sub-boom hit on the first cut
    hit = cuts_out[0]
    n = int(1.1 * SR); t = np.arange(n) / SR
    riser = np.diff(r.standard_normal(n), prepend=0) * (t / 1.1) ** 2.2
    put(riser / (np.abs(riser).max() + 1e-9), hit - 1.1, 0.20)
    n = int(1.6 * SR); t = np.arange(n) / SR
    f = 38 + 90 * np.exp(-t * 14); boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.8)
    put(boom, hit, 0.55)
    # soft tail
    n = int(1.4 * SR); t = np.arange(n) / SR
    tail = np.sin(2 * np.pi * 55 * t) * np.exp(-t * 2.2) * (1 - np.exp(-t * 20))
    put(tail, DUR - 1.4, 0.16)
    out = (np.clip(fx.T, -1, 1) * 32767).astype('<i2')
    import wave
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())

# ------------------------------------------------------------------ main
def probe(src):
    o = subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', src])
    return float(json.loads(o)['format']['duration'])

def reader(src, stretch):
    slow = (DUR - HOLD_AT) / (SRC_DUR - HOLD_AT)                  # slow-mo factor for the final shot
    vf = f"setpts='if(lt(T,{HOLD_AT}),PTS,({HOLD_AT}+(T-{HOLD_AT})*{slow:.5f})/TB)',minterpolate=fps={FPS}:mi_mode=blend,tpad=stop_mode=clone:stop=6,scale={SW}:{SH}:flags=lanczos"
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-an', '-vf', vf, '-frames:v', str(int(DUR * FPS)),
                          '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    return p

def main():
    src, out = sys.argv[1], sys.argv[2]
    global SRC_DUR
    SRC_DUR = probe(src)
    stretch = 1.0
    cuts_out = list(CUTS_SRC)                                      # music stays in sync: cuts keep their source times
    preview = None; out_dir = '.'
    if '--preview' in sys.argv: preview = [float(x) for x in sys.argv[sys.argv.index('--preview') + 1].split(',')]
    if '--out_dir' in sys.argv: out_dir = sys.argv[sys.argv.index('--out_dir') + 1]
    nfr = int(DUR * FPS); fsz = SW * SH * 3
    rd = reader(src, stretch)
    if preview is not None:
        os.makedirs(out_dir, exist_ok=True)
        want = {int(round(t * FPS)): t for t in preview}
        for i in range(nfr):
            buf = rd.stdout.read(fsz)
            if len(buf) < fsz: break
            if i in want:
                fr = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
                Image.fromarray(look(fr, i / FPS, cuts_out, 1000 + i)).resize((1920, 1080), Image.LANCZOS).save(os.path.join(out_dir, f'm{want[i]:.2f}.png'))
                print('preview', want[i], flush=True)
            if i >= max(want): break
        rd.kill(); return
    fxp = out + '.fx.wav'; make_fx(fxp, cuts_out)
    af = (f"[1:a]apad=whole_dur={DUR},volume=1.0[m];[2:a]volume=0.9[f];"
          f"[m][f]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-15:TP=-1.5:LRA=7,afade=t=out:st={DUR - 1.1}:d=1.1[a]")
    enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                            '-i', src, '-i', fxp, '-filter_complex', af, '-map', '0:v', '-map', '[a]',
                            '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p',
                            '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                            '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-t', str(DUR), '-movflags', '+faststart', out], stdin=subprocess.PIPE)
    import time; t0 = time.time()
    for i in range(nfr):
        buf = rd.stdout.read(fsz)
        if len(buf) < fsz: print('short read at', i); break
        fr = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
        enc.stdin.write(look(fr, i / FPS, cuts_out, 1000 + i).tobytes())
        if i % 15 == 0: print(f'frame {i + 1}/{nfr}  {time.time() - t0:.0f}s', flush=True)
    enc.stdin.close(); enc.wait(); rd.wait()
    os.remove(fxp)
    print('wrote', out)

if __name__ == '__main__':
    main()
