"""Animated infographic layers (numbers, icons, text) for the documentary overlay. 1920x1080."""
import numpy as np, cv2
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont

f32 = np.float32
FB = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
FM = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'
AMBER = (255, 190, 60); WHITE = (255, 255, 255); TEAL = (80, 225, 195); PINK = (255, 125, 175)
VIOLET = (165, 145, 255); RED = (255, 100, 100); SKY = (115, 195, 255)
PX, PY, PW, PH = 1190, 140, 640, 640
SS = 3


def ease(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


def seg(t, a, b):
    return float(ease((t - a) / (b - a)))


def fade(t, a, b, fi=0.4, fo=0.35):
    return float(ease((t - a) / fi) * ease((b - t) / fo)) if a <= t <= b else 0.0


def pop(t, a, d=0.38):
    """overshoot scale 0..1.12..1"""
    x = (t - a) / d
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    return float(1.12 * (1 - (1 - x / 0.75) ** 3) if x < 0.75 else 1.12 - 0.12 * (x - 0.75) / 0.25)


def over(canvas, layer, x, y, op=1.0):
    h, w = layer.shape[:2]
    x0, y0 = int(round(x)), int(round(y))
    X0, Y0, X1, Y1 = max(x0, 0), max(y0, 0), min(x0 + w, canvas.shape[1]), min(y0 + h, canvas.shape[0])
    if X1 <= X0 or Y1 <= Y0: return
    src = layer[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] * op
    canvas[Y0:Y1, X0:X1] = src + canvas[Y0:Y1, X0:X1] * (1 - src[..., 3:4])


@lru_cache(maxsize=600)
def txt(text, size, color=WHITE, bold=True, track=0):
    font = ImageFont.truetype(FB if bold else FM, size * SS)
    d0 = ImageDraw.Draw(Image.new('L', (4, 4)))
    tr = track * SS
    w = int(sum(d0.textlength(c, font=font) + tr for c in text) + 8 * SS)
    h = int(size * 1.4 * SS)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = 4 * SS
    for c in text:
        d.text((x, int(size * 0.12 * SS)), c, font=font, fill=tuple(color) + (255,)); x += d.textlength(c, font=font) + tr
    a = np.asarray(im, f32) / 255.0; a[..., :3] *= a[..., 3:4]
    return cv2.resize(a, (w // SS, h // SS), interpolation=cv2.INTER_AREA)


def put_txt(panel, layer, cx=None, x=None, y=0, op=1.0):
    w = layer.shape[1]
    over(panel, layer, (cx - w / 2) if cx is not None else x, y, op)


def prem(c, a=1.0):
    return (int(c[0] * a), int(c[1] * a), int(c[2] * a), int(255 * a))


# ---------------------------------------------------------------- icons (draw into uint8 premult layer)
def person(L, cx, cy, s, c, a=1.0):
    col = prem(c, a)
    cv2.circle(L, (int(cx), int(cy - 0.62 * s)), max(1, int(0.30 * s)), col, -1, cv2.LINE_AA)
    cv2.ellipse(L, (int(cx), int(cy + 0.55 * s)), (int(0.50 * s), int(0.78 * s)), 0, 180, 360, col, -1, cv2.LINE_AA)


def sparkle(L, cx, cy, r, c, a=1.0, rot=0.0):
    pts = []
    for k in range(8):
        ang = rot + k * np.pi / 4
        rr = r if k % 2 == 0 else r * 0.26
        pts.append((cx + rr * np.cos(ang), cy + rr * np.sin(ang)))
    cv2.fillPoly(L, [np.round(np.array(pts) * 16).astype(np.int32)], prem(c, a), cv2.LINE_AA, 4)


def heart(L, cx, cy, s, c, a=1.0):
    tt = np.linspace(0, 2 * np.pi, 80)
    x = 16 * np.sin(tt) ** 3; y = -(13 * np.cos(tt) - 5 * np.cos(2 * tt) - 2 * np.cos(3 * tt) - np.cos(4 * tt))
    pts = np.stack([cx + x * s / 17, cy + y * s / 17], 1)
    cv2.fillPoly(L, [np.round(pts * 16).astype(np.int32)], prem(c, a), cv2.LINE_AA, 4)


def mirror(L, cx, cy, s, c, a=1.0):
    col = prem(c, a)
    cv2.ellipse(L, (int(cx), int(cy - 0.2 * s)), (int(0.62 * s), int(0.82 * s)), 0, 0, 360, col, max(2, int(0.13 * s)), cv2.LINE_AA)
    cv2.line(L, (int(cx), int(cy + 0.62 * s)), (int(cx), int(cy + 1.25 * s)), col, max(2, int(0.17 * s)), cv2.LINE_AA)
    sparkle(L, cx - 0.12 * s, cy - 0.3 * s, 0.3 * s, c, a * 0.9)


def check(L, cx, cy, s, c, a=1.0):
    pts = np.array([(cx - 0.62 * s, cy + 0.0 * s), (cx - 0.15 * s, cy + 0.5 * s), (cx + 0.72 * s, cy - 0.5 * s)])
    cv2.polylines(L, [np.round(pts * 16).astype(np.int32)], False, prem(c, a), max(2, int(0.3 * s)), cv2.LINE_AA, 4)


def book(L, cx, cy, s, c, a=1.0):
    col = prem(c, a)
    for sg in (-1, 1):
        pts = np.array([(cx, cy - 0.45 * s), (cx + sg * 0.95 * s, cy - 0.7 * s), (cx + sg * 0.95 * s, cy + 0.55 * s), (cx, cy + 0.8 * s)])
        cv2.fillPoly(L, [np.round(pts * 16).astype(np.int32)], col, cv2.LINE_AA, 4)
    cv2.line(L, (int(cx), int(cy - 0.45 * s)), (int(cx), int(cy + 0.8 * s)), (0, 0, 0, 255 if a >= 1 else int(255 * a)) if False else prem((20, 20, 30), 0.55 * a), max(1, int(0.07 * s)), cv2.LINE_AA)


def two_people(L, cx, cy, s, c, a=1.0):
    person(L, cx - 0.55 * s, cy + 0.1 * s, s * 0.8, c, a); person(L, cx + 0.55 * s, cy + 0.1 * s, s * 0.8, c, a)


def fingerprint(L, cx, cy, s, c, a=1.0):
    col = prem(c, a)
    for r in (0.25, 0.5, 0.75, 1.0):
        cv2.ellipse(L, (int(cx), int(cy)), (int(r * s * 0.8), int(r * s)), 0, 190, 350, col, max(2, int(0.1 * s)), cv2.LINE_AA)
    for r in (0.38, 0.63, 0.88):
        cv2.ellipse(L, (int(cx), int(cy + 0.1 * s)), (int(r * s * 0.8), int(r * s)), 0, 20, 160, col, max(2, int(0.1 * s)), cv2.LINE_AA)


def magnifier(L, cx, cy, s, c, a=1.0):
    col = prem(c, a)
    cv2.circle(L, (int(cx), int(cy)), int(0.55 * s), col, max(2, int(0.14 * s)), cv2.LINE_AA)
    cv2.line(L, (int(cx + 0.4 * s), int(cy + 0.4 * s)), (int(cx + 0.95 * s), int(cy + 0.95 * s)), col, max(3, int(0.2 * s)), cv2.LINE_AA)


def ring(L, cx, cy, r, p, c, th=14):
    cv2.circle(L, (int(cx), int(cy)), r, prem(WHITE, 0.16), th, cv2.LINE_AA)
    if p > 0.003:
        cv2.ellipse(L, (int(cx), int(cy)), (r, r), -90, 0, 360 * p, prem(c, 1.0), th, cv2.LINE_AA)


def bar(L, x, y, w, h, p, c):
    cv2.line(L, (int(x + h / 2), int(y)), (int(x + w - h / 2), int(y)), prem(WHITE, 0.16), int(h), cv2.LINE_AA)
    ww = max(0, (w - h) * p)
    if ww > 1:
        cv2.line(L, (int(x + h / 2), int(y)), (int(x + h / 2 + ww), int(y)), prem(c, 1.0), int(h), cv2.LINE_AA)
    else:
        cv2.circle(L, (int(x + h / 2), int(y)), int(h / 2), prem(c, 1.0), -1, cv2.LINE_AA)


# ---------------------------------------------------------------- panel
_BG = {}


def panel_bg():
    if 'bg' not in _BG:
        im = Image.new('RGBA', (PW * SS, PH * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, PW * SS - 1, PH * SS - 1), 34 * SS, fill=(8, 10, 22, 150), outline=(255, 255, 255, 46), width=2 * SS)
        a = np.asarray(im, f32) / 255.0; a[..., :3] *= a[..., 3:4]
        _BG['bg'] = cv2.resize(a, (PW, PH), interpolation=cv2.INTER_AREA)
    return _BG['bg'].copy()


def finish(L, panel):
    over(panel, L.astype(f32) / 255.0, 0, 0, 1.0)


def foot(panel, text, op=1.0):
    put_txt(panel, txt(text, 21, (255, 255, 255), False), cx=PW / 2, y=PH - 46, op=0.55 * op)


# ---------------------------------------------------------------- scenes
def s1(t):
    P = panel_bg(); L = np.zeros((PH, PW, 4), np.uint8)
    put_txt(P, txt("PENDUDUK DUNIA", 24, (255, 255, 255), True, 4), x=44, y=38, op=0.75 * seg(t, 1.0, 1.5))
    v1 = 8.2 * seg(t, 1.2, 3.2)
    put_txt(P, txt(f"≈ {v1:.1f} BILION", 62, WHITE, True), x=40, y=64, op=seg(t, 1.1, 1.5))
    put_txt(P, txt("WANITA", 24, (255, 255, 255), True, 4), x=44, y=170, op=0.75 * seg(t, 3.4, 3.9))
    v2 = 4.1 * seg(t, 3.6, 5.4)
    put_txt(P, txt(f"≈ {v2:.1f} BILION", 62, AMBER, True), x=40, y=196, op=seg(t, 3.5, 3.9))
    for i in range(20):
        r, c = divmod(i, 10)
        cx, cy = 64 + c * 57, 372 + r * 92
        women = i < 10
        a = 0.35
        col = WHITE
        if women:
            k = seg(t, 3.9 + i * 0.12, 4.4 + i * 0.12)
            col = tuple(int(WHITE[j] + (AMBER[j] - WHITE[j]) * k) for j in range(3)); a = 0.35 + 0.65 * k
        person(L, cx, cy, 25, col, a)
        if women:
            sp = seg(t, 6.3 + i * 0.2, 6.9 + i * 0.2) * (1 - seg(t, 8.4, 8.9))
            if sp > 0.01:
                sparkle(L, cx + 17, cy - 30 - 4 * sp, 13 * sp, WHITE, sp, rot=sp)
    put_txt(P, txt("SEMUA WANITA CANTIK", 22, AMBER, True, 3), cx=PW / 2, y=PH - 112, op=seg(t, 6.2, 6.9) * (1 - seg(t, 8.6, 9.0)))
    finish(L, P); foot(P, "Anggaran PBB, bilangan kira-kira · ilustrasi")
    return P


def s2(t):
    P = panel_bg(); L = np.zeros((PH, PW, 4), np.uint8)
    lab1 = seg(t, 10.9, 11.3) * (1 - seg(t, 15.2, 15.6)); lab2 = seg(t, 15.7, 16.2)
    put_txt(P, txt("TERPESONA", 44, AMBER, True, 6), cx=PW / 2, y=62, op=lab1)
    put_txt(P, txt("BIASA SAHAJA", 44, WHITE, True, 6), cx=PW / 2, y=62, op=lab2)
    n = 12
    for i in range(n):
        cx, cy = 52 + i * 49.5, 250
        on = seg(t, 11.2 + i * 0.33, 11.6 + i * 0.33)
        off = seg(t, 15.8 + i * 0.12, 16.6 + i * 0.12)
        k = on * (1 - off)
        col = tuple(int(WHITE[j] + (AMBER[j] - WHITE[j]) * k) for j in range(3))
        person(L, cx, cy, 20, col, 0.45 + 0.5 * k)
        if k > 0.02:
            sparkle(L, cx + 12, cy - 27, 11 * k, WHITE, k, rot=t * 2 + i)
    put_txt(P, txt("KEISTIMEWAAN", 26, (255, 255, 255), True, 4), x=48, y=372, op=0.85 * seg(t, 10.9, 11.4))
    p = 1.0 - 0.82 * seg(t, 15.6, 18.6)
    pc = tuple(int(AMBER[j] + (SKY[j] - AMBER[j]) * seg(t, 15.6, 18.6)) for j in range(3))
    bar(L, 48, 450, 544, 26, p * seg(t, 10.9, 11.6) if t < 11.6 else p, pc)
    put_txt(P, txt("TINGGI", 20, (255, 255, 255), False), x=48, y=482, op=0.6 * seg(t, 11, 11.5) * (1 - seg(t, 16.5, 17.0)))
    put_txt(P, txt("SAMA SEPERTI SEMUA ORANG", 22, WHITE, True, 2), cx=PW / 2, y=520, op=seg(t, 17.6, 18.3))
    finish(L, P); foot(P, "Ilustrasi konsep")
    return P


def s3(t):
    P = panel_bg(); L = np.zeros((PH, PW, 4), np.uint8)
    put_txt(P, txt("MENCARI SESUATU YANG LAIN", 28, WHITE, True, 3), cx=PW / 2, y=44, op=seg(t, 21.0, 21.5) * (1 - seg(t, 25.0, 25.5)))
    cols = [AMBER, TEAL, PINK, VIOLET, SKY, AMBER, TEAL, PINK]
    mx = 60 + 520 * seg(t, 21.3, 24.6)
    for i in range(8):
        cx, cy = 64 + i * 73, 190
        k = seg(t, 21.3 + (i / 7) * 3.3 - 0.1, 21.3 + (i / 7) * 3.3 + 0.35)
        col = tuple(int(WHITE[j] + (cols[i][j] - WHITE[j]) * k) for j in range(3))
        person(L, cx, cy, 24, col, 0.4 + 0.6 * k)
    mo = seg(t, 21.0, 21.4) * (1 - seg(t, 24.7, 25.1))
    if mo > 0.02:
        magnifier(L, mx, 200 + 8 * np.sin(t * 5), 34, WHITE, mo)
    chips = [("GAYA", AMBER, 25.4, 'spark'), ("PERSONALITI", PINK, 26.3, 'heart'), ("KEYAKINAN", TEAL, 27.2, 'check'), ("KEUNIKAN DIRI", VIOLET, 28.0, 'finger')]
    for k, (name, c, ta, ic) in enumerate(chips):
        sc = pop(t, ta)
        if sc <= 0: continue
        r, cc = divmod(k, 2)
        cx, cy = 170 + cc * 300, 360 + r * 130
        w, h = 270 * sc, 100 * sc
        cv2.rectangle(L, (int(cx - w / 2), int(cy - h / 2)), (int(cx + w / 2), int(cy + h / 2)), prem(c, 0.18), -1, cv2.LINE_AA)
        cv2.rectangle(L, (int(cx - w / 2), int(cy - h / 2)), (int(cx + w / 2), int(cy + h / 2)), prem(c, 0.9), 3, cv2.LINE_AA)
        s_ = 26 * sc; ix = cx - w / 2 + 44 * sc
        {'spark': lambda: sparkle(L, ix, cy, 26 * sc, c), 'heart': lambda: heart(L, ix, cy, 40 * sc, c),
         'check': lambda: check(L, ix, cy, 26 * sc, c), 'finger': lambda: fingerprint(L, ix, cy, 24 * sc, c)}[ic]()
    finish(L, P)
    for k, (name, c, ta, ic) in enumerate(chips):
        sc = pop(t, ta)
        if sc <= 0.6: continue
        r, cc = divmod(k, 2)
        cx, cy = 170 + cc * 300, 360 + r * 130
        put_txt(P, txt(name, 22 if len(name) > 9 else 26, WHITE, True), x=cx - 108 * 0 - 82 + 40, y=cy - 18, op=min(1, (sc - 0.6) / 0.4))
    foot(P, "Ilustrasi konsep")
    return P


def s4(t):
    P = panel_bg(); L = np.zeros((PH, PW, 4), np.uint8)
    a1 = seg(t, 30.9, 31.4)
    mirror(L, 140, 150, 50, AMBER, a1); heart(L, 500, 150, 92, PINK, a1)
    put_txt(P, txt("CANTIK", 28, AMBER, True, 4), cx=140, y=232, op=a1)
    put_txt(P, txt("BAHAGIA", 28, PINK, True, 4), cx=500, y=232, op=a1)
    eq = seg(t, 31.4, 31.9)
    for dy in (-12, 12):
        cv2.line(L, (292, 150 + dy), (348, 150 + dy), prem(WHITE, eq), 9, cv2.LINE_AA)
    sl = seg(t, 32.3, 32.9)
    if sl > 0:
        cv2.line(L, (300, int(190 - 80 * sl) + 0), (340, 190), prem(RED, 1.0), 0 + 1, cv2.LINE_AA)
        x0, y0 = 342, 108; x1, y1 = 298, 192
        cv2.line(L, (int(x0), int(y0)), (int(x0 + (x1 - x0) * sl), int(y0 + (y1 - y0) * sl)), prem(RED, 1.0), 10, cv2.LINE_AA)
    rows = [("KEBAHAGIAAN", 34.0), ("KEJAYAAN", 35.4), ("HUBUNGAN SEMPURNA", 36.8)]
    for k, (name, ta) in enumerate(rows):
        sc = ease((t - ta) / 0.4)
        if sc <= 0: continue
        y = 330 + k * 82
        cv2.rectangle(L, (40, y - 30), (PW - 40, y + 30), prem(WHITE, 0.10 * sc), -1, cv2.LINE_AA)
        cv2.circle(L, (74, y), 14, prem(RED, sc), 3, cv2.LINE_AA)
        cv2.line(L, (67, y - 7), (81, y + 7), prem(RED, sc), 3, cv2.LINE_AA); cv2.line(L, (81, y - 7), (67, y + 7), prem(RED, sc), 3, cv2.LINE_AA)
    finish(L, P)
    for k, (name, ta) in enumerate(rows):
        sc = ease((t - ta) / 0.4)
        if sc <= 0: continue
        y = 330 + k * 82
        put_txt(P, txt(name, 28 if len(name) < 14 else 24, WHITE, True), x=104, y=y - 19, op=sc)
        put_txt(P, txt("TIDAK DIJAMIN", 18, AMBER, True, 2), x=PW - 190, y=y - 12, op=sc)
    foot(P, "Ilustrasi konsep")
    return P


def s5(t):
    P = panel_bg(); L = np.zeros((PH, PW, 4), np.uint8)
    items = [("KEBIJAKSANAAN", SKY, 41.4, 'book'), ("KEJUJURAN", TEAL, 43.3, 'check'), ("KEBAIKAN HATI", PINK, 45.2, 'heart'), ("CARA MELAYAN", AMBER, 47.0, 'two')]
    for k, (name, c, t0, ic) in enumerate(items):
        r, cc = divmod(k, 2)
        cx, cy = 170 + cc * 300, 190 + r * 235
        p = seg(t, t0, t0 + 1.6)
        vis = seg(t, t0 - 0.4, t0)
        ring(L, cx, cy, 70, p * vis, c, 15)
        if vis > 0.02:
            col = tuple(int(WHITE[j] + (c[j] - WHITE[j]) * p) for j in range(3))
            {'book': lambda: book(L, cx, cy, 26, col, vis), 'check': lambda: check(L, cx, cy, 28, col, vis),
             'heart': lambda: heart(L, cx, cy + 2, 54, col, vis), 'two': lambda: two_people(L, cx, cy + 6, 24, col, vis)}[ic]()
    finish(L, P)
    for k, (name, c, t0, ic) in enumerate(items):
        r, cc = divmod(k, 2)
        cx, cy = 170 + cc * 300, 190 + r * 235
        put_txt(P, txt(name, 22, WHITE, True, 1), cx=cx, y=cy + 88, op=seg(t, t0 - 0.2, t0 + 0.4))
    foot(P, "Ilustrasi konsep")
    return P


SCENE_PANELS = [(s1, 0.9, 9.3), (s2, 10.8, 19.3), (s3, 20.8, 29.3), (s4, 30.8, 39.3), (s5, 40.8, 49.3)]


def panel(t):
    for fn, a, b in SCENE_PANELS:
        op = fade(t, a, b)
        if op > 0:
            return fn(t), op, (1 - ease((t - a) / 0.5)) * 40
    return None


# ---------------------------------------------------------------- floating question marks (scene 6)
_Q = None


def floaters(t, W=1920, H=1080):
    global _Q
    if not (50.3 <= t <= 59.95):
        return None
    if _Q is None:
        rng = np.random.default_rng(8)
        n = 16
        side = rng.integers(0, 2, n)
        x = np.where(side == 0, rng.uniform(70, 520, n), rng.uniform(1400, 1850, n))
        _Q = dict(x=x, y0=rng.uniform(600, 1000, n), size=rng.integers(70, 170, n), t0=50.5 + np.sort(rng.uniform(0, 6.0, n)),
                  life=rng.uniform(3.6, 5.0, n), amber=rng.random(n) < 0.35, rot=rng.uniform(-0.3, 0.3, n))
    cv = np.zeros((H, W, 4), f32)
    for i in range(len(_Q['x'])):
        u = (t - _Q['t0'][i]) / _Q['life'][i]
        if u <= 0 or u >= 1: continue
        a = np.sin(np.pi * u) ** 1.2 * 0.55
        col = AMBER if _Q['amber'][i] else WHITE
        lay = txt("?", int(_Q['size'][i]), col, True)
        over(cv, lay, _Q['x'][i] - lay.shape[1] / 2 + 14 * np.sin(u * 5 + i), _Q['y0'][i] - 480 * u, a)
    return cv
