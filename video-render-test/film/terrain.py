"""Scene 4: rain-saturated slope, landslide, collapsed bridge. Heightfield raymarch at half resolution."""
import numpy as np, cv2
from lib import *

_S = {}
N = 2048
TEX = 1.5   # m per texel
ZR = 38.0   # river level


def xr(y):
    return 1500 + 230 * np.sin(y / 520.0) + 90 * np.sin(y / 190.0)


def build():
    rng = np.random.default_rng(5)
    f = fbm(N, 3.1, 61); f2 = fbm(N, 2.3, 62); hf = fbm(N, 1.1, 63)
    Y, X = np.mgrid[0:N, 0:N].astype(f32)
    wx, wy = X * TEX, Y * TEX
    rx = xr(wy)
    dxr = (wx - rx + 1500) % 3000 - 1500
    valley = 0.5 - 0.5 * np.cos(2 * np.pi * dxr / 3000.0)
    hgt = ZR + 380 * valley ** 1.15 + 38 * f * (0.3 + valley) + 9 * f2
    river = np.exp(-(dxr / 48.0) ** 2)
    hgt = hgt * (1 - river) + (ZR - 2 + 3 * f2) * river
    hgt = np.maximum(hgt, ZR - 4)
    hgt = cv2.GaussianBlur(hgt, (0, 0), 1.2)
    gy, gx = np.gradient(hgt)
    G = np.dstack([gx / TEX, gy / TEX]).astype(f32)
    # albedo (forest) + river mask in alpha
    dens = sstep(-1.2, 1.4, 0.55 * f2 + 0.9 * hf)
    forest = col(11, 26, 9) + (col(46, 74, 22) - col(11, 26, 9)) * dens[..., None]
    low = sstep(0.12, 0.0, valley)[..., None]
    forest = forest * (1 - low * 0.5) + col(70, 88, 40) * low * 0.5
    steep = np.clip(np.hypot(gx, gy) / TEX * 1.6 - 0.35, 0, 1)[..., None]
    forest = forest * (1 - steep * 0.35) + col(70, 62, 40) * steep * 0.35
    alb = np.dstack([forest, np.clip(river * 1.4 - 0.2, 0, 1)]).astype(f32)
    # road
    pts = []
    for y, off in [(1000, 760), (1250, 600), (1500, 470), (1700, 335), (1800, 160), (1900, 0), (2000, -150), (2150, -420), (2300, -700)]:
        pts.append((xr(y) + off, y))
    ys = np.linspace(1000, 2300, 160)
    offs = np.interp(ys, [p[1] for p in pts], [p[0] - xr(p[1]) for p in pts])
    line = np.array([[(xr(yy) + oo) / TEX, yy / TEX] for yy, oo in zip(ys, offs)])
    rd = np.zeros((N, N), f32)
    cv2.polylines(rd, [line.astype(np.int32)], False, 1.0, 4, cv2.LINE_AA)
    rd = cv2.GaussianBlur(rd, (0, 0), 0.8)
    alb[..., :3] = alb[..., :3] * (1 - rd[..., None] * 0.9) + col(92, 88, 82) * rd[..., None] * 0.9
    return hgt.astype(f32), G, alb, hf


def setup():
    if 'h' in _S:
        return _S
    h, G, alb, hf = build()
    _S.update(h=h, G=G, alb=alb, hf=hf, water=WaterSys(seed=23), sky=Sky(9), rain=RainFx(seed=14),
              camh=Cam(W // 2, H // 2), cam=Cam())
    yA = 1650.0; yB = 1760.0
    _S['A'] = np.array([xr(yA) + 560, yA]); _S['B'] = np.array([xr(yB) + 115, yB])
    return _S


def psamp(tex, x, y):
    """Sample texture (pixel coords, wrapping) at a flat list of points."""
    K = len(x)
    P = (-K) % 1024
    xx = np.pad(x.astype(f32), (0, P)).reshape(-1, 1024) % tex.shape[1]
    yy = np.pad(y.astype(f32), (0, P)).reshape(-1, 1024) % tex.shape[0]
    r = cv2.remap(tex, xx, yy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    return r.reshape(-1, *tex.shape[2:])[:K] if tex.ndim == 3 else r.ravel()[:K]


def hsamp(S, x, y):
    return psamp(S['h'], x / TEX, y / TEX)


def raymarch(S, cam, steps=120):
    d = cam.dirs().reshape(-1, 3)
    K = d.shape[0]
    O = cam.pos
    tt = np.full(K, np.inf, f32)
    act = np.nonzero(d[:, 2] < 0.22)[0]
    t_prev = np.full(K, 4.0, f32)
    g = np.exp(np.log(3600.0 / 4.0) / steps)
    t = 4.0
    prev_ok = np.ones(K, bool)
    for k in range(steps):
        t_next = t * g
        da = d[act]
        x = O[0] + da[:, 0] * t_next; y = O[1] + da[:, 1] * t_next; z = O[2] + da[:, 2] * t_next
        hh = hsamp(S, x, y)
        hit = z < hh
        if hit.any():
            ia = act[hit]
            lo = np.full(len(ia), t, f32); hi = np.full(len(ia), t_next, f32)
            dd = d[ia]
            for _ in range(6):
                mid = (lo + hi) / 2
                zm = O[2] + dd[:, 2] * mid
                hm = hsamp(S, O[0] + dd[:, 0] * mid, O[1] + dd[:, 1] * mid)
                below = zm < hm
                hi = np.where(below, mid, hi); lo = np.where(below, lo, mid)
            tt[ia] = (lo + hi) / 2
            act = act[~hit]
        t = t_next
        if len(act) == 0:
            break
    return d, tt


def slide(S, x, y, T):
    A, B = S['A'], S['B']
    ab = B - A; L = np.hypot(*ab); ab = ab / L
    px, py = x - A[0], y - A[1]
    u = (px * ab[0] + py * ab[1]) / L
    v = -px * ab[1] + py * ab[0]
    front = sstep(0.0, 1.0, T / 4.2) * 1.12
    w = 14 + 70 * np.sin(np.pi * np.clip(u, 0, 1)) ** 0.7
    nz = psamp(S['hf'], x / 6.0, y / 6.0) * 6
    inside = (u > 0) & (u < front) & (np.abs(v) < w + nz) & (u < 1.15)
    return inside, u, np.abs(v) / np.maximum(w, 1)


def render(cam_pos, look, T, slide_T, bridge=False, rain_i=1.0):
    S = setup()
    camh = S['camh']
    fwd = np.array(look) - np.array(cam_pos)
    yaw = np.arctan2(fwd[0], fwd[1]); pitch = np.arctan2(-fwd[2], np.hypot(fwd[0], fwd[1]))
    camh.set(cam_pos, yaw, pitch)
    d, tt = raymarch(S, camh)
    hitm = np.isfinite(tt)
    Hh, Wh = camh.h, camh.w
    img = np.zeros((Hh * Wh, 3), f32)
    # sky
    sky = S['sky'].render(camh.dirs(), camh.pos, T, zen=(0.34, 0.37, 0.42), hor=(0.52, 0.55, 0.57)).reshape(-1, 3)
    img[:] = sky
    ih = np.nonzero(hitm)[0]
    t = tt[ih]; dd = d[ih]
    x = camh.pos[0] + dd[:, 0] * t; y = camh.pos[1] + dd[:, 1] * t; z = camh.pos[2] + dd[:, 2] * t
    k = (1, -1)
    a = psamp(S['alb'], x / TEX, y / TEX)
    gg = psamp(S['G'], x / TEX, y / TEX)
    alb = a[:, :3].copy(); riv = a[:, 3:4]
    ins, u, vv = slide(S, x, y, slide_T)
    soil = col(118, 80, 50); mud = col(76, 52, 36)
    nz = (psamp(S['hf'], x / 3.0, y / 3.0) * 0.12)[:, None]
    sc = np.where((u < 0.55)[:, None], soil, mud) * (0.85 + nz) * (1 - 0.25 * vv[:, None])
    alb = np.where(ins[:, None], sc, alb)
    # tree-fall streaks at scar edge
    edge = ins & (vv > 0.8)
    alb = np.where(edge[:, None], col(40, 30, 20) * (0.8 + nz), alb)
    # river: muddy turbulent
    foam = sstep(0.55, 1.2, psamp(np.ascontiguousarray(S['water'].t1[..., 0]), x / 4.0 - 3 * T, y / 4.0 - 7 * T))[:, None]
    rivc = col(86, 62, 42) * (0.8 + 0.5 * psamp(np.ascontiguousarray(S['water'].t2[..., 0]), x / 3.0, y / 3.0 + 4 * T)[:, None] * 0.2)
    rivc = rivc + foam * 0.25
    alb = alb * (1 - riv) + rivc * riv
    # shading
    n = np.stack([-gg[:, 0], -gg[:, 1], np.ones_like(gg[:, 0])], 1); n /= np.linalg.norm(n, axis=1, keepdims=True)
    Ld = np.array([-0.45, -0.25, 0.86], f32)
    sh = 0.38 + 0.75 * np.clip(n @ Ld, 0, 1)
    detail = 0.88 + 0.28 * psamp(S['hf'], x / 1.5, y / 1.5)[:, None] * 0.5
    c = alb * sh[:, None] * detail
    fg = (1 - np.exp(-t / 950.0))[:, None]
    fogc = np.array([0.50, 0.53, 0.55], f32)
    c = c * (1 - fg) + fogc * fg
    img[ih] = c
    img = img.reshape(Hh, Wh, 3)
    out = cv2.resize(img, (W, H), interpolation=cv2.INTER_CUBIC)
    # bridge (painter on top)
    cam = S['cam'].set(cam_pos, yaw, pitch)
    can = np.clip(out * 255, 0, 255).astype(np.uint8)
    if bridge:
        yb = 1900.0; xb = xr(yb)
        zd = ZR + 15.0
        Bx = dict(
            cx=np.array([xb - 52, xb + 52, xb - 15, xb + 15, xb - 8, xb + 4]),
            cy=np.full(6, yb), w=np.array([60, 60, 6, 6, 22, 14]), d=np.array([10, 10, 3.5, 3.5, 9, 9]),
            h=np.array([1.6, 1.6, 15, 15, 1.2, 1.2]), z0=np.array([zd, zd, ZR - 2, ZR - 2, ZR - 0.5, ZR + 3.0]),
            r=np.array([.42, .42, .5, .5, .38, .38]), g=np.array([.42, .42, .5, .5, .38, .38]), b=np.array([.40, .40, .48, .48, .36, .36]))
        Bx['rr'], Bx['rg'], Bx['rb'] = Bx['r'], Bx['g'], Bx['b']
        draw_boxes(can, cam, Bx, T, fog=(0.5, 0.53, 0.55), fogk=1 / 950., maxd=2000)
    out = can.astype(f32) / 255.0
    out = S['rain'].apply(out, T, rain_i)
    return grade(out, sat=0.85, contrast=1.1)


def shot_a(i, n=150):
    S = setup()
    T = i / FPS
    C = (S['A'] + S['B']) / 2
    zc = float(hsamp(S, np.array([C[0]]), np.array([C[1]]))[0])
    ang = np.radians(-35 + 8.0 * T)
    R = 340
    cam = (C[0] + R * np.sin(ang + 2.4), C[1] + R * np.cos(ang + 2.4), zc + 150 - 3 * T)
    return render(cam, (C[0], C[1], zc), T, 0.7 + T * 0.78)


def shot_b(i, n=150):
    S = setup()
    T = i / FPS
    yb = 1900.0; xb = xr(yb)
    s = T / 5.0
    cam = (xb + lerp(260, 120, s), yb - lerp(330, 150, s), ZR + lerp(150, 60, s))
    return render(cam, (xb - 5, yb, ZR + 8), T + 5, 5.0, bridge=True)
