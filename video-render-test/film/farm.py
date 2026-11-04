"""Scene 3: flooded farmland (wide drone + close crop tracking)."""
import numpy as np, cv2
from lib import *
from city import skygrad, cat

_S = {}
MPP = 0.5   # metres per map pixel
N = 2048


def build_map(seed=8):
    rng = np.random.default_rng(seed)
    crop = np.zeros((N, N), f32); hue = np.zeros((N, N), f32); dike = np.zeros((N, N), f32)
    ori = np.zeros((N, N), np.uint8); land = np.zeros((N, N), f32)
    def split(x0, y0, x1, y1, depth=0):
        w, h = x1 - x0, y1 - y0
        if (w < 150 and h < 150) or depth > 6 or (w < 70 or h < 70):
            if w < 20 or h < 20:
                return
            c = rng.choice([1.0, 1.0, 1.0, 0.85, 0.0], p=[.12, .2, .18, .1, .40])
            crop[y0 + 3:y1 - 3, x0 + 3:x1 - 3] = c
            hue[y0 + 3:y1 - 3, x0 + 3:x1 - 3] = rng.uniform(0.0, 1.0)
            ori[y0:y1, x0:x1] = rng.integers(0, 2)
            dike[y0:y0 + 3, x0:x1] = 1; dike[y1 - 3:y1, x0:x1] = 1; dike[y0:y1, x0:x0 + 3] = 1; dike[y0:y1, x1 - 3:x1] = 1
            return
        if w > h:
            m = int(rng.uniform(.35, .65) * w); split(x0, y0, x0 + m, y1, depth + 1); split(x0 + m, y0, x1, y1, depth + 1)
        else:
            m = int(rng.uniform(.35, .65) * h); split(x0, y0, x1, y0 + m, depth + 1); split(x0, y0 + m, x1, y1, depth + 1)
    split(0, 0, N, N)
    # islands for farm clusters
    cl = []
    for _ in range(9):
        cx, cy = rng.integers(200, N - 200, 2)
        r = rng.integers(32, 55)
        cv2.circle(land, (int(cx), int(cy)), int(r), 1.0, -1, cv2.LINE_AA)
        crop[max(0, cy - r - 8):cy + r + 8, max(0, cx - r - 8):cx + r + 8] *= 0
        cl.append((cx, cy, r))
    land = cv2.GaussianBlur(land, (0, 0), 3)
    dike = cv2.GaussianBlur(dike, (0, 0), 0.8)
    m = np.dstack([crop, hue, dike, land]).astype(f32)
    return m, ori, cl, rng


def setup():
    if 'm' in _S:
        return _S
    m, ori, cl, rng = build_map()
    _S.update(m=m, ori=ori, cl=cl, water=WaterSys(seed=17), sky=Sky(3), rain=RainFx(seed=12), cam=Cam(), camh=Cam(W // 2, H // 2))
    # houses and trees on islands (world coords: map px * MPP)
    cx, cy, w, d, h, r, g, b, rr, rg, rb = ([] for _ in range(11))
    tx, ty, tw, th, tr, tg, tb = ([] for _ in range(7))
    roofs = [col(120, 125, 130), col(150, 70, 55), col(90, 110, 130), col(170, 165, 150)]
    walls = [col(200, 195, 180), col(170, 150, 120), col(185, 185, 175), col(150, 160, 150)]
    for (mx, my, mr) in cl:
        X0, Y0 = mx * MPP, my * MPP
        for _ in range(rng.integers(3, 6)):
            a = rng.uniform(0, 6.28); rad = rng.uniform(0, mr * MPP * 0.6)
            cx.append(X0 + rad * np.cos(a)); cy.append(Y0 + rad * np.sin(a))
            w.append(rng.uniform(5, 8)); d.append(rng.uniform(6, 10)); h.append(rng.uniform(3.2, 4.6))
            c = walls[rng.integers(4)]; r.append(c[0]); g.append(c[1]); b.append(c[2])
            c = roofs[rng.integers(4)]; rr.append(c[0]); rg.append(c[1]); rb.append(c[2])
        for _ in range(rng.integers(8, 14)):
            a = rng.uniform(0, 6.28); rad = rng.uniform(0, mr * MPP * 0.95)
            tx.append(X0 + rad * np.cos(a)); ty.append(Y0 + rad * np.sin(a)); tw.append(rng.uniform(4, 8)); th.append(rng.uniform(7, 13))
            tr.append(rng.uniform(0.1, 0.18)); tg.append(rng.uniform(0.24, 0.34)); tb.append(rng.uniform(0.07, 0.12))
    nb, nt = len(cx), len(tx)
    _S['B'] = dict(cx=np.array(cx), cy=np.array(cy), w=np.array(w), d=np.array(d), h=np.array(h), r=np.array(r), g=np.array(g), b=np.array(b),
                   rr=np.array(rr), rg=np.array(rg), rb=np.array(rb), kind=np.zeros(nb, int))
    _S['T'] = dict(cx=np.array(tx), cy=np.array(ty), w=np.array(tw), d=np.ones(nt), h=np.array(th), r=np.array(tr), g=np.array(tg), b=np.array(tb), kind=np.ones(nt, int))
    return _S


def plants(pos, yaw, T, hue_boost):
    """3D rice/corn plants near camera as short line strokes. Returns list of (p0,p1,color,dist) arrays."""
    S = setup()
    sp = 0.55
    fx, fy = np.sin(yaw), np.cos(yaw)
    gx0 = int((pos[0] - 18) / sp); gx1 = int((pos[0] + 18) / sp)
    gy0 = int((pos[1] - 4) / sp); gy1 = int((pos[1] + 34) / sp)
    gx, gy = np.meshgrid(np.arange(gx0, gx1), np.arange(gy0, gy1))
    hsh = (gx * 73856093 ^ gy * 19349663) & 0xffff
    jx = ((hsh % 97) / 97.0 - 0.5) * 0.3; jy = (((hsh // 97) % 89) / 89.0 - 0.5) * 0.3
    X = (gx * sp + jx).ravel(); Y = (gy * sp + jy).ravel()
    mx = ((X / MPP).astype(int)) % N; my = ((Y / MPP).astype(int)) % N
    crop = S['m'][my, mx, 0]; hue = S['m'][my, mx, 1]; dk = S['m'][my, mx, 2]; ld = S['m'][my, mx, 3]
    ori = S['ori'][my, mx]
    ok = (crop > 0.5) & (dk < 0.3) & (ld < 0.3)
    # row structure: skip plants between rows
    rowc = np.where(ori > 0, X, Y)
    ok &= (np.cos(2 * np.pi * rowc / 0.42) > -0.2)
    return X[ok], Y[ok], hue[ok], hsh.ravel()[ok]


def render(pos, yaw, pitch, T, close=False, rain_i=1.0, yellow=0.0):
    S = setup()
    cam = S['cam'].set(pos, yaw, pitch)
    d = cam.dirs()
    below = d[..., 2] < -1e-4
    t = -cam.pos[2] / np.where(below, d[..., 2], -1e-4)
    X = cam.pos[0] + d[..., 0] * t; Y = cam.pos[1] + d[..., 1] * t
    fogc = (0.52, 0.55, 0.56)
    haze = 1 / (1100. if not close else 220.)
    sky = S['sky'].render(d, cam.pos, T, zen=(0.34, 0.37, 0.42), hor=fogc)
    base = np.broadcast_to(np.array([0.44, 0.33, 0.21], f32), d.shape)
    wat = S['water'].shade(X, Y, d, t, T, base, skygrad, flow=(0.3, -0.5), rip=1.0, fogc=fogc, fogk=haze, L=(90., 11.), amp=(0.012, 0.0025))
    mp = samp(S['m'], X / MPP, Y / MPP)
    ori = samp(S['ori'], X / MPP, Y / MPP, cv2.INTER_NEAREST)
    crop, hue, dike, land = mp[..., 0], mp[..., 1], mp[..., 2], mp[..., 3]
    coord = np.where(ori > 0, X, Y)
    fade = np.exp(-t / (45. if close else 90.))
    stripe = 0.5 + 0.5 * np.cos(2 * np.pi * coord / 0.42)
    stripe = stripe * fade + 0.5 * (1 - fade)
    hh = np.clip(hue * 0.5 + yellow, 0, 1)[..., None]
    green = np.array([0.20, 0.36, 0.11], f32); yel = np.array([0.50, 0.42, 0.16], f32); rot = np.array([0.30, 0.24, 0.12], f32)
    cc = green + (yel - green) * hh
    cc = cc + (rot - cc) * np.clip(yellow * 1.3 - 0.2, 0, 1)
    va = (crop * (0.05 + 0.45 * stripe))[..., None]
    cc = cc * (0.7 + 0.5 * stripe)[..., None]
    img = wat * (1 - va) + cc * va
    dk = (dike * 0.85)[..., None]
    img = img * (1 - dk) + np.array([0.36, 0.29, 0.19], f32) * dk
    ld_ = land[..., None]
    img = img * (1 - ld_) + np.array([0.22, 0.30, 0.12], f32) * (0.85 + 0.3 * samp(S['water'].t1[..., 0], X * 2, Y * 2)[..., None] * 0.3) * ld_
    fg = (1 - np.exp(-t * haze))[..., None]
    img = img * (1 - 0.0) * (1 - fg * 0) ; img = img * (1 - fg) + np.array(fogc, f32) * fg
    img = np.where(below[..., None], img, sky)
    can = np.clip(img * 255, 0, 255).astype(np.uint8)
    if close:
        px, py, hu, hs = plants(pos, yaw, T, yellow)
        dist = np.hypot(px - pos[0], py - pos[1])
        o = np.argsort(-dist)
        gcol = np.array([0.18, 0.32, 0.10], f32); ycol = np.array([0.42, 0.36, 0.14], f32)
        fgc = np.array(fogc, f32)
        # vectorised projection of base and tip(s)
        for k in range(3):
            ang = (hs % 628) / 100.0 + k * 2.1
            ht = 0.32 + ((hs >> 4) % 40) / 100.0 + 0.05 * k
            bend = 0.18 + 0.1 * np.sin(T * 1.7 + px * 0.7 + k)
            P0 = np.stack([px, py, np.zeros_like(px)], 1)
            P1 = np.stack([px + np.cos(ang) * bend, py + np.sin(ang) * bend, ht], 1)
            xc0, yc0, zc0 = cam.to_cam(P0); xc1, yc1, zc1 = cam.to_cam(P1)
            ok = (yc0 > 0.6) & (yc1 > 0.6)
            u0 = cam.w / 2 + cam.f * xc0 / np.maximum(yc0, .01); v0 = cam.h / 2 - cam.f * zc0 / np.maximum(yc0, .01)
            u1 = cam.w / 2 + cam.f * xc1 / np.maximum(yc1, .01); v1 = cam.h / 2 - cam.f * zc1 / np.maximum(yc1, .01)
            hh_ = np.clip(hu * 0.5 + yellow, 0, 1)[:, None]
            cols = (gcol + (ycol - gcol) * hh_) * (0.75 + 0.5 * ((hs >> 3) % 10)[:, None] / 10.0)
            fgp = (1 - np.exp(-dist * haze))[:, None]
            cols = np.clip(cols * (1 - fgp) + fgc * fgp, 0, 1) * 255
            for j in o:
                if ok[j] and -50 < u0[j] < cam.w + 50 and -50 < v0[j] < cam.h + 50:
                    th = max(1, int(cam.f * 0.03 / yc0[j]))
                    cv2.line(can, (int(u0[j]), int(v0[j])), (int(u1[j]), int(v1[j])), tuple(float(c) for c in cols[j]), th, cv2.LINE_AA)
    Bs = cat(S['B'], S['T'])
    draw_boxes(can, cam, Bs, T, fog=fogc, fogk=haze, maxd=1000)
    img = can.astype(f32) / 255.0
    img = S['rain'].apply(img, T + 3, rain_i)
    return grade(img, sat=0.8, contrast=1.1)


def shot_a(i, n=150):
    T = i / FPS
    return render((20 + 2 * np.sin(T * .6), 20 + 18 * T, 95 - 5 * T), 0.05 * np.sin(T * .4) + 0.2, np.radians(52), T, close=False, yellow=0.1)


def shot_b(i, n=150):
    T = i / FPS
    return render((40 + 0.8 * T, 180 + 2.6 * T, 2.6), 0.0 + 0.02 * np.sin(T), np.radians(10 + 0.4 * T), T + 5, close=True, yellow=0.3)
