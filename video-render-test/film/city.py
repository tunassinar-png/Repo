"""Scene 2: flooded city (aerial + low tracking)."""
import numpy as np, cv2
from lib import *

_STATE = {}
PAL = [col(150,150,146), col(176,160,132), col(204,200,190), col(158,100,84), col(112,128,142), col(96,96,102), col(186,178,160), col(140,134,120)]
ROOF = [col(110,110,112), col(120,95,85), col(160,160,156), col(90,104,118), col(140,70,55), col(70,70,74)]


def build(seed=3):
    rng = np.random.default_rng(seed)
    xs = [0.0]; wx = [36.0]
    for sgn in (1, -1):
        p = 0.0
        while abs(p) < 520:
            p += sgn * rng.uniform(78, 125)
            xs.append(p); wx.append(rng.uniform(14, 24))
    o = np.argsort(xs); xs = np.array(xs)[o]; wx = np.array(wx)[o]
    ys = [-200.0]; wy = [16.0]
    while ys[-1] < 1500:
        ys.append(ys[-1] + rng.uniform(80, 130)); wy.append(rng.uniform(14, 24))
    ys = np.array(ys); wy = np.array(wy)
    cx, cy, bw, bd, bh, cr = [], [], [], [], [], []
    rr = []
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            x0, x1 = xs[i] + wx[i] / 2 + 1, xs[i + 1] - wx[i + 1] / 2 - 1
            y0, y1 = ys[j] + wy[j] / 2 + 1, ys[j + 1] - wy[j + 1] / 2 - 1
            if x1 - x0 < 12 or y1 - y0 < 12:
                continue
            nxs = rng.integers(1, 4); nys = rng.integers(1, 4)
            ex = np.sort(np.r_[x0, rng.uniform(x0, x1, nxs - 1), x1]); ey = np.sort(np.r_[y0, rng.uniform(y0, y1, nys - 1), y1])
            for a in range(nxs):
                for b in range(nys):
                    if rng.random() < 0.07:
                        continue
                    ins = rng.uniform(1.5, 5)
                    lx0, lx1, ly0, ly1 = ex[a] + ins, ex[a + 1] - ins, ey[b] + ins, ey[b + 1] - ins
                    if lx1 - lx0 < 6 or ly1 - ly0 < 6:
                        continue
                    h = float(np.clip(rng.lognormal(np.log(13), 0.5), 4, 42))
                    if rng.random() < 0.07:
                        h = rng.uniform(55, 115)
                    cx.append((lx0 + lx1) / 2); cy.append((ly0 + ly1) / 2); bw.append(lx1 - lx0); bd.append(ly1 - ly0); bh.append(h)
                    c = PAL[rng.integers(len(PAL))] * rng.uniform(0.85, 1.1)
                    cr.append(c)
                    r = ROOF[rng.integers(len(ROOF))] * rng.uniform(0.9, 1.15)
                    rr.append(r)
    cr = np.array(cr, f32); rr = np.array(rr, f32)
    B = dict(cx=np.array(cx), cy=np.array(cy), w=np.array(bw), d=np.array(bd), h=np.array(bh),
             r=cr[:, 0], g=cr[:, 1], b=cr[:, 2], rr=rr[:, 0], rg=rr[:, 1], rb=rr[:, 2], kind=np.zeros(len(cx), int))
    # trees (crowns above water along street edges)
    tx, ty = [], []
    for _ in range(260):
        if rng.random() < 0.5:
            k = rng.integers(len(xs)); tx.append(xs[k] + rng.uniform(-1, 1) * wx[k] * 0.45); ty.append(rng.uniform(-150, 1400))
        else:
            k = rng.integers(len(ys)); ty.append(ys[k] + rng.uniform(-1, 1) * wy[k] * 0.45); tx.append(rng.uniform(-500, 500))
    n = len(tx)
    T_ = dict(cx=np.array(tx), cy=np.array(ty), w=rng.uniform(5, 9, n), d=np.ones(n), h=rng.uniform(5, 9, n),
              r=rng.uniform(0.12, 0.2, n), g=rng.uniform(0.22, 0.30, n), b=rng.uniform(0.1, 0.14, n), kind=np.ones(n, int))
    # cars + debris floating on avenues/streets
    items = []
    for _ in range(170):
        if rng.random() < 0.6:  # along y streets
            k = rng.integers(len(xs)); items.append(dict(ax=0, c=xs[k] + rng.uniform(-.35, .35) * wx[k], s=rng.uniform(-200, 1400), v=1.4, kind='car'))
        else:
            k = rng.integers(len(ys)); items.append(dict(ax=1, c=ys[k] + rng.uniform(-.35, .35) * wy[k], s=rng.uniform(-520, 520), v=-1.2, kind='car'))
    for _ in range(420):
        if rng.random() < 0.6:
            k = rng.integers(len(xs)); items.append(dict(ax=0, c=xs[k] + rng.uniform(-.45, .45) * wx[k], s=rng.uniform(-200, 1400), v=1.4 * rng.uniform(.7, 1.2), kind='deb'))
        else:
            k = rng.integers(len(ys)); items.append(dict(ax=1, c=ys[k] + rng.uniform(-.45, .45) * wy[k], s=rng.uniform(-520, 520), v=-1.2 * rng.uniform(.7, 1.2), kind='deb'))
    return B, T_, items, rng


def setup():
    if 'B' in _STATE:
        return _STATE
    B, TR, items, rng = build()
    _STATE.update(B=B, TR=TR, items=items, water=WaterSys(), sky=Sky(), rain=RainFx(),
                  cam=Cam(), camh=Cam(W // 2, H // 2), ph=rng.uniform(0, 6.28, len(items)))
    carcols = [col(190,190,190), col(60,60,70), col(150,40,40), col(210,210,200), col(40,70,120), col(180,150,60)]
    _STATE['carcols'] = [carcols[i % len(carcols)] * rng.uniform(.8, 1.1) for i in range(len(items))]
    return _STATE


def skygrad(R, dark=1.0):
    z = np.clip(R[..., 2], 0, 1)[..., None]
    hor = np.array([0.55, 0.57, 0.59], f32); zen = np.array([0.24, 0.27, 0.32], f32)
    return (hor + (zen - hor) * np.clip(z * 2.0, 0, 1) ** 0.7) * 0.8 * dark


def dyn_boxes(S, T):
    items = S['items']
    n = len(items)
    cx = np.zeros(n); cy = np.zeros(n); w = np.zeros(n); d = np.zeros(n); h = np.zeros(n)
    r = np.zeros(n); g = np.zeros(n); b = np.zeros(n)
    for i, it in enumerate(items):
        s = it['s'] + it['v'] * T
        L = 1700.0 if it['ax'] == 0 else 1040.0
        base = -200.0 if it['ax'] == 0 else -520.0
        s = base + (s - base) % L
        car = it['kind'] == 'car'
        if it['ax'] == 0:
            cx[i], cy[i] = it['c'], s; w[i], d[i] = (2.0, 4.6) if car else (0.7, 0.6 + 2.2 * (S['ph'][i] > 5))
        else:
            cx[i], cy[i] = s, it['c']; w[i], d[i] = (4.6, 2.0) if car else (0.6 + 2.2 * (S['ph'][i] > 5), 0.7)
        h[i] = 1.0 if car else 0.28
        c = S['carcols'][i] if car else col(95, 78, 55) * (0.7 + 0.6 * (S['ph'][i] % 1))
        r[i], g[i], b[i] = c
    return dict(cx=cx, cy=cy, w=w, d=d, h=h, r=r, g=g, b=b, kind=np.zeros(n, int))


def cat(*Ds):
    keys = set.intersection(*[set(D) for D in Ds])
    return {k: np.concatenate([np.asarray(D[k]) for D in Ds]) for k in keys}


def frame(pos, yaw, pitch, T, rain_i=1.0, haze=1 / 520.):
    S = setup()
    cam = S['cam'].set(pos, yaw, pitch)
    d = cam.dirs()
    dz = d[..., 2]
    below = dz < -1e-4
    t = -cam.pos[2] / np.where(below, dz, -1e-4)
    X = cam.pos[0] + d[..., 0] * t; Y = cam.pos[1] + d[..., 1] * t
    fogc = (0.53, 0.55, 0.57)
    sky = S['sky'].render(d, cam.pos, T, zen=(0.36, 0.39, 0.44), hor=fogc) * 1.0
    base = np.broadcast_to(np.array([0.46, 0.335, 0.20], f32), d.shape)
    wat = S['water'].shade(X, Y, d, t, T, base, skygrad, flow=(0.0, -1.4), rip=1.0, fogc=fogc, fogk=haze)
    img = np.where(below[..., None], wat, sky)
    # --- geometry
    Bs = cat(S['B'], S['TR'], dyn_boxes(S, T))
    # reflections (half res, RGBA premultiplied-ish)
    camh = S['camh'].set(pos, yaw, pitch)
    rc = np.zeros((H // 2, W // 2, 4), np.uint8)
    draw_boxes(rc, camh, Bs, T, mirror=True, fog=fogc, fogk=haze, maxd=520)
    rc = cv2.GaussianBlur(rc, (0, 0), 3.0).astype(f32) / 255.0
    rc = cv2.resize(rc, (W, H), interpolation=cv2.INTER_LINEAR)
    A = rc[..., 3:4]
    k = 0.24
    img = img * (1 - k * A) + k * rc[..., :3] * 0.7
    # contact shadows (ambient occlusion on water around footprints)
    ao = np.zeros((H // 2, W // 2), np.uint8)
    nb = len(S['B']['cx'])
    for i in np.nonzero(np.hypot(S['B']['cx'] - pos[0], S['B']['cy'] - pos[1]) < 420)[0]:
        x0, x1 = S['B']['cx'][i] - S['B']['w'][i] / 2 - 2, S['B']['cx'][i] + S['B']['w'][i] / 2 + 2
        y0, y1 = S['B']['cy'][i] - S['B']['d'][i] / 2 - 2, S['B']['cy'][i] + S['B']['d'][i] / 2 + 2
        P = np.array([[x0, y0, 0], [x1, y0, 0], [x1, y1, 0], [x0, y1, 0]])
        xc, yc, zc = camh.to_cam(P)
        if yc.min() < 1:
            continue
        u, v = camh.proj(xc, yc, zc)
        cv2.fillConvexPoly(ao, np.round(np.c_[u, v]).astype(np.int32), 255)
    ao = cv2.GaussianBlur(ao, (0, 0), 4.5).astype(f32) / 255.0
    ao = cv2.resize(ao, (W, H))[..., None]
    img = img * (1 - 0.38 * ao)
    can = np.clip(img * 255, 0, 255).astype(np.uint8)
    draw_boxes(can, cam, Bs, T, mirror=False, fog=fogc, fogk=haze, maxd=1100)
    img = can.astype(f32) / 255.0
    img = S['rain'].apply(img, T, rain_i)
    return grade(img, sat=0.78, contrast=1.1, bloom=0.0)


def shot_a(i, n=150):
    T = i / FPS
    pos = (-6 + 3 * np.sin(T * .7), -30 + 24 * T, 150 - 3 * T)
    return frame(pos, 0.04 * np.sin(T * .5), np.radians(44 + 1.2 * T), T)


def shot_b(i, n=150):
    T = i / FPS
    pos = (2.5 * np.sin(T * .5), 40 + 12 * T, 27 - 0.8 * T)
    return frame(pos, 0.015 * np.sin(T * .8), np.radians(13 - 0.2 * T), T + 5)
