"""Transparent overlay kit for the 'Gaji Minimum RM2,000' reel (1080x1920, 30 fps, 60 s).
Outputs: overlay_alpha.webm (VP9 alpha), overlay_greenscreen.mp4, preview_overlay.mp4, png/*.png
Usage: build_overlay.py OUTDIR [t0 t1]   (t0/t1 in seconds, for testing a range -> writes test PNGs)"""
import os, sys, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
f32 = np.float32
FB = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
FM = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'
AMBER = (255, 184, 28)
WHITE = (255, 255, 255)
RED = (255, 98, 64)
TEAL = (64, 224, 190)
SS = 3


def premult(img):
    a = np.asarray(img, f32) / 255.0
    a[..., :3] *= a[..., 3:4]
    return a


def down(a, w, h):
    return cv2.resize(a, (w, h), interpolation=cv2.INTER_AREA)


def arrow(d, cx, cy, s, up, color):
    pts = [(cx, cy - s), (cx + .95 * s, cy + .1 * s), (cx + .38 * s, cy + .1 * s), (cx + .38 * s, cy + s), (cx - .38 * s, cy + s), (cx - .38 * s, cy + .1 * s), (cx - .95 * s, cy + .1 * s)]
    if not up:
        pts = [(x, 2 * cy - y) for x, y in pts]
    d.polygon(pts, fill=color)


def plate(lines, icon=None, cta=False, minw=0):
    """lines: list of (text,size,color). Returns premultiplied RGBA float layer."""
    fonts = [ImageFont.truetype(FB, int(sz * SS)) for _, sz, _ in lines]
    tmp = ImageDraw.Draw(Image.new('L', (4, 4)))
    ws = [tmp.textlength(t, font=f) for (t, _, _), f in zip(lines, fonts)]
    lh = [int(sz * 1.22 * SS) for _, sz, _ in lines]
    padx, pady = 52 * SS, 30 * SS
    iconw = (lines[0][1] * 1.0 * SS + 26 * SS) if icon else 0
    w = int(max(ws) + 2 * padx + iconw + 14 * SS)
    w = max(w, minw * SS)
    h = int(sum(lh) + 2 * pady)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = 30 * SS
    if cta:
        d.rounded_rectangle((0, 0, w - 1, h - 1), r, fill=AMBER + (255,))
        tc = (14, 16, 20)
    else:
        d.rounded_rectangle((0, 0, w - 1, h - 1), r, fill=AMBER + (255,))
        d.rounded_rectangle((14 * SS, 0, w - 1, h - 1), r, fill=(8, 10, 14, 178))
        d.rectangle((14 * SS, 0, 14 * SS + r, h - 1), fill=(8, 10, 14, 178))
        tc = None
    y = pady
    for (t, sz, c), f, hh in zip(lines, fonts, lh):
        col = (14, 16, 20) if cta else c
        d.text(((w + (14 * SS if not cta else 0) - iconw) / 2 - ws[lines.index((t, sz, c))] / 2 + (0), y), t, font=f, fill=col + (255,))
        y += hh
    if icon:
        isz = lines[0][1] * 0.42 * SS
        arrow(d, w - padx - isz * 0.4, pady + lh[0] * 0.5, isz, icon == 'up', RED + (255,))
    a = premult(im)
    return down(a, w // SS, h // SS)


def label(text, size, color=WHITE, bold=True, alpha=1.0):
    f = ImageFont.truetype(FB if bold else FM, int(size * SS))
    tmp = ImageDraw.Draw(Image.new('L', (4, 4)))
    w = int(tmp.textlength(text, font=f)) + 8 * SS
    h = int(size * 1.4 * SS)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 * SS, int(size * 0.1 * SS)), text, font=f, fill=color + (int(255 * alpha),))
    return down(premult(im), w // SS, h // SS)


def over(canvas, layer, x, y, op=1.0):
    h, w = layer.shape[:2]
    x0, y0 = int(round(x)), int(round(y))
    X0, Y0, X1, Y1 = max(x0, 0), max(y0, 0), min(x0 + w, canvas.shape[1]), min(y0 + h, canvas.shape[0])
    if X1 <= X0 or Y1 <= Y0:
        return
    src = layer[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] * op
    dst = canvas[Y0:Y1, X0:X1]
    canvas[Y0:Y1, X0:X1] = src + dst * (1 - src[..., 3:4])


def ease(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def fade(t, a, b, fi=0.4, fo=0.3):
    return float(ease((t - a) / fi) * ease((b - t) / fo)) if a <= t <= b else 0.0


# ------------------------------------------------------------------ static plates
P = {}
def build_plates():
    P['s1a'] = plate([("GAJI MINIMUM", 62, WHITE), ("RM2,000", 128, AMBER)])
    P['s1b'] = plate([("RAKYAT UNTUNG ATAU RUGI?", 52, WHITE)])
    P['s2a'] = plate([("KOS GAJI NAIK", 68, WHITE)], icon='up')
    P['s2b'] = plate([("HARGA BARANG BOLEH NAIK", 52, WHITE)], icon='up')
    P['s3'] = plate([("ALIRAN WANG KE LUAR NEGARA", 50, WHITE)])
    P['s4a'] = plate([("KOS SARA HIDUP", 68, WHITE)])
    P['s4b'] = plate([("KUASA BELI TERHAKIS", 56, WHITE)], icon='down')
    P['s5'] = plate([("INFLASI VS PRODUKTIVITI", 52, WHITE)])
    P['s6a'] = plate([("GAJI NAIK,", 84, WHITE), ("KUASA BELI NAIK?", 84, AMBER)])
    P['s6b'] = plate([("APA PENDAPAT ANDA?", 64, WHITE)], cta=True)


# (key, start, end, y)
TL = [('s1a', 0.5, 5.2, 700), ('s1b', 3.4, 9.5, 1070),
      ('s2a', 10.5, 14.9, 760), ('s2b', 14.1, 19.6, 1050),
      ('s3', 20.5, 29.6, 560),
      ('s4a', 30.5, 34.9, 760), ('s4b', 34.1, 39.6, 1050),
      ('s5', 40.5, 49.7, 500),
      ('s6a', 56.0, 59.9, 760), ('s6b', 58.0, 59.9, 1130)]


# ------------------------------------------------------------------ money flow (scene 3)
GOLD = (255, 196, 60)
MINT = (96, 232, 176)
MF = dict(x0=0, y0=760, w=W, h=760)
_MF = {}


def bez(p0, p1, p2, s):
    return ((1 - s) ** 2) * p0[0] + 2 * (1 - s) * s * p1[0] + s * s * p2[0], ((1 - s) ** 2) * p0[1] + 2 * (1 - s) * s * p1[1] + s * s * p2[1]


def mf_static():
    if _MF:
        return _MF
    _MF['rm'] = label("RM", 50)
    _MF['mal'] = label("MALAYSIA", 30)
    _MF['asal'] = label("NEGARA ASAL PEKERJA", 28)
    _MF['bel'] = label("BELANJA DI MALAYSIA", 28, MINT)
    _MF['hant'] = label("KIRIMAN PULANG", 28, GOLD)
    return _MF


def money_flow(t, a=20.5, b=29.6):
    op = fade(t, a, b, 0.8, 0.6)
    if op <= 0:
        return None
    S_ = mf_static()
    lay = np.zeros((MF['h'], MF['w'], 4), np.uint8)
    M = (210, 420); R = 64
    D = [(880, 120), (905, 360), (880, 600)]
    # faint path lines + coins
    def prem(c, a_):
        return (int(c[0] * a_), int(c[1] * a_), int(c[2] * a_), int(255 * a_))
    tt = t - a
    for i, d in enumerate(D):
        ctrl = (560, (M[1] + d[1]) / 2 + (-90 if i == 0 else (0 if i == 1 else 90)))
        pts = np.array([bez(M, ctrl, d, s) for s in np.linspace(0, 1, 60)], np.float32)
        cv2.polylines(lay, [np.round(pts * 16).astype(np.int32)], False, prem(WHITE, 0.22), 3, cv2.LINE_AA, 4)
        for k in range(4):
            s = ((tt * 0.30) + k / 4.0 + i * 0.13) % 1.0
            x, y = bez(M, ctrl, d, s)
            al = np.sin(np.pi * s) ** 0.6
            cv2.circle(lay, (int(x), int(y)), 20, prem(GOLD, 0.16 * al), -1, cv2.LINE_AA)
            cv2.circle(lay, (int(x), int(y)), 11, prem(GOLD, 0.95 * al), -1, cv2.LINE_AA)
    # home loop (spending inside Malaysia)
    for k in range(8):
        ang = tt * 1.1 + k * 2 * np.pi / 8
        x, y = M[0] + 112 * np.cos(ang), M[1] + 112 * np.sin(ang)
        cv2.circle(lay, (int(x), int(y)), 17, prem(MINT, 0.14), -1, cv2.LINE_AA)
        cv2.circle(lay, (int(x), int(y)), 9, prem(MINT, 0.95), -1, cv2.LINE_AA)
    cv2.circle(lay, M, 112, prem(MINT, 0.18), 2, cv2.LINE_AA)
    # nodes
    cv2.circle(lay, M, R, (6, 7, 10, 190), -1, cv2.LINE_AA)
    cv2.circle(lay, M, R, prem(AMBER, 1.0), 5, cv2.LINE_AA)
    for d in D:
        cv2.circle(lay, d, 38, (6, 7, 10, 190), -1, cv2.LINE_AA)
        cv2.circle(lay, d, 38, prem(WHITE, 0.9), 4, cv2.LINE_AA)
        cv2.circle(lay, d, 7, prem(GOLD, 1.0), -1, cv2.LINE_AA)
    out = lay.astype(f32) / 255.0
    # labels (premultiplied layers composited on top)
    full = np.zeros((MF['h'], MF['w'], 4), f32)
    full[:] = out
    def put(l, cx, y):
        over(full, l, cx - l.shape[1] / 2, y)
    put(S_['rm'], M[0], M[1] - 30)
    put(S_['mal'], M[0], M[1] + R + 134)
    put(S_['bel'], M[0] + 20, M[1] + R + 172)
    put(S_['asal'], 760, 20)
    put(S_['hant'], 560, 452)
    return full, op


# ------------------------------------------------------------------ chart (scene 5)
CH = dict(x0=70, y0=600, w=940, h=760)
PX0, PX1, PY0, PY1 = 90, 850, 130, 560     # plot area inside the chart layer
_CH = {}


def sst(a, b, x):
    return ease((x - a) / (b - a))


def infl(x):
    return 0.22 + 0.64 * sst(0.0, 0.52, x) - 0.34 * sst(0.52, 1.0, x)


def prod(x):
    return 0.18 + 0.72 * sst(0.05, 0.98, x)


def to_px(x, y):
    return PX0 + x * (PX1 - PX0), PY1 - y * (PY1 - PY0)


def chart_static():
    if _CH:
        return _CH
    SSS = 2
    w, h = CH['w'], CH['h']
    im = Image.new('RGBA', (w * SSS, h * SSS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w * SSS - 1, h * SSS - 1), 36 * SSS, fill=(8, 10, 14, 178))
    for g in (0.25, 0.5, 0.75, 1.0):
        y = to_px(0, g)[1] * SSS
        d.line((PX0 * SSS, y, PX1 * SSS, y), fill=(255, 255, 255, 34), width=2 * SSS)
    ax = (255, 255, 255, 150)
    d.line((PX0 * SSS, PY0 * SSS - 10, PX0 * SSS, PY1 * SSS), fill=ax, width=4 * SSS)
    d.line((PX0 * SSS, PY1 * SSS, PX1 * SSS + 10, PY1 * SSS), fill=ax, width=4 * SSS)
    d.polygon([(PX1 * SSS + 24, PY1 * SSS), (PX1 * SSS + 4, PY1 * SSS - 12 * SSS), (PX1 * SSS + 4, PY1 * SSS + 12 * SSS)], fill=ax)
    f1 = ImageFont.truetype(FB, 30 * SSS); f2 = ImageFont.truetype(FM, 26 * SSS)
    d.text((PX0 * SSS, 44 * SSS), "TEKANAN HARGA", font=f1, fill=(255, 255, 255, 220))
    d.text((PX1 * SSS - d.textlength("MASA", font=f1) + 6 * SSS, (PY1 + 18) * SSS), "MASA", font=f1, fill=(255, 255, 255, 220))
    # legend
    ly = (PY1 + 90) * SSS
    d.ellipse((PX0 * SSS, ly + 4 * SSS, PX0 * SSS + 26 * SSS, ly + 30 * SSS), fill=(255, 140, 40, 255))
    d.text((PX0 * SSS + 40 * SSS, ly), "INFLASI (HARGA)", font=f1, fill=(255, 255, 255, 240))
    lx2 = (PX0 + 400) * SSS
    d.ellipse((lx2, ly + 4 * SSS, lx2 + 26 * SSS, ly + 30 * SSS), fill=TEAL + (255,))
    d.text((lx2 + 40 * SSS, ly), "PRODUKTIVITI", font=f1, fill=(255, 255, 255, 240))
    d.text((PX0 * SSS, (h - 52) * SSS), "ILUSTRASI KONSEP, BUKAN DATA SEBENAR", font=f2, fill=(255, 255, 255, 140))
    _CH['bg'] = down(premult(im), w, h)
    _CH['tag'] = plate([("KOS TERKAWAL", 38, WHITE)], minw=0)
    return _CH


def chart(t, a=40.5, b=49.7):
    op = fade(t, a, b, 0.6, 0.5)
    if op <= 0:
        return None
    C = chart_static()
    base = C['bg'].copy()
    lay = np.zeros((CH['h'], CH['w'], 4), np.uint8)
    p = float(ease((t - 41.3) / 5.9))
    n = 160
    xs = np.linspace(0, 1, n)
    k = max(2, int(p * n))
    def prem(c, a_):
        return (int(c[0] * a_), int(c[1] * a_), int(c[2] * a_), int(255 * a_))
    for fn, c in ((infl, (255, 140, 40)), (prod, TEAL)):
        pts = np.array([to_px(x, fn(x)) for x in xs[:k]], np.float32)
        cv2.polylines(lay, [np.round(pts * 16).astype(np.int32)], False, prem(c, 0.22), 18, cv2.LINE_AA, 4)
        cv2.polylines(lay, [np.round(pts * 16).astype(np.int32)], False, prem(c, 1.0), 8, cv2.LINE_AA, 4)
        ex, ey = pts[-1]
        cv2.circle(lay, (int(ex), int(ey)), 20, prem(c, 0.25), -1, cv2.LINE_AA)
        cv2.circle(lay, (int(ex), int(ey)), 11, prem(c, 1.0), -1, cv2.LINE_AA)
    out = lay.astype(f32) / 255.0
    full = out + base * (1 - out[..., 3:4])
    tg = fade(t, 47.6, 49.7, 0.5, 0.4)
    if tg > 0:
        x, y = to_px(0.9, infl(0.9))
        over(full, C['tag'], x - C['tag'].shape[1] - 10, y - 95, tg)
    return full, op


# ------------------------------------------------------------------ frame + pipeline
def frame(t):
    cv = np.zeros((H, W, 4), f32)
    r = chart(t)
    if r is not None:
        over(cv, r[0], CH['x0'], CH['y0'], r[1])
    m = money_flow(t)
    if m is not None:
        over(cv, m[0], MF['x0'], MF['y0'], m[1])
    for key, a, b, y in TL:
        op = fade(t, a, b)
        if op > 0:
            lay = P[key]
            sl = (1 - ease((t - a) / 0.45)) * 26
            over(cv, lay, (W - lay.shape[1]) / 2, y + sl, op)
    return cv


def bg_frame():
    yy, xx = np.mgrid[0:H, 0:W].astype(f32)
    g = 0.5 + 0.5 * (yy / H)
    img = np.stack([30 + 36 * g, 38 + 42 * g, 52 + 48 * g], -1) * (1 - 0.35 * (((xx - W / 2) / (W / 2)) ** 2))[..., None]
    return img.astype(f32)


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    os.makedirs(os.path.join(out, 'png'), exist_ok=True)
    build_plates()
    if len(sys.argv) > 3:
        t0, t1 = float(sys.argv[2]), float(sys.argv[3])
        bg = bg_frame()
        for t in np.arange(t0, t1, (t1 - t0) / 6 if t1 - t0 > 1 else 1.0):
            cv_ = frame(t)
            im = cv_[..., :3] + (1 - cv_[..., 3:4]) * bg
            cv2.imwrite(os.path.join(out, f'test_{t:05.1f}.png'), cv2.cvtColor(np.clip(im, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
        return
    for key, a, b, y in TL:   # full-frame transparent PNGs for editors
        cv_ = np.zeros((H, W, 4), f32)
        lay = P[key]
        over(cv_, lay, (W - lay.shape[1]) / 2, y)
        rgb = np.where(cv_[..., 3:4] > 0, cv_[..., :3] / np.maximum(cv_[..., 3:4], 1e-6), 0)
        Image.fromarray(np.dstack([np.clip(rgb * 255, 0, 255), np.clip(cv_[..., 3:4] * 255, 0, 255)]).astype(np.uint8), 'RGBA').save(os.path.join(out, 'png', f'{key}_{a:04.1f}s-{b:04.1f}s.png'))
    bg = bg_frame()
    cmds = [
        ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p',
         '-b:v', '0', '-crf', '22', '-auto-alt-ref', '0', '-row-mt', '1', '-deadline', 'good', '-cpu-used', '4', os.path.join(out, 'overlay_alpha.webm')],
        ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'fast', '-crf', '14', '-pix_fmt', 'yuv420p',
         os.path.join(out, 'overlay_greenscreen.mp4')],
        ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
         os.path.join(out, 'preview_silent.mp4')],
    ]
    ps = [subprocess.Popen(c, stdin=subprocess.PIPE) for c in cmds]
    green = np.array([0, 255, 0], f32)
    for g in range(60 * FPS):
        cv_ = frame(g / FPS)
        a = cv_[..., 3:4]
        rgb = np.where(a > 0.001, cv_[..., :3] / np.maximum(a, 1e-4), 0)
        straight = np.dstack([np.clip(rgb * 255 + .5, 0, 255), np.clip(a * 255 + .5, 0, 255)]).astype(np.uint8)
        ps[0].stdin.write(straight.tobytes())
        ps[1].stdin.write(np.clip(cv_[..., :3] * 255 + (1 - a) * green + .5, 0, 255).astype(np.uint8).tobytes())
        ps[2].stdin.write(np.clip(cv_[..., :3] * 255 + (1 - a) * bg + .5, 0, 255).astype(np.uint8).tobytes())
        if g % 150 == 0:
            print('frame', g, flush=True)
    for p in ps:
        p.stdin.close(); p.wait()
    print('done')


if __name__ == '__main__':
    main()
