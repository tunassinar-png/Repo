"""Scene 5: flooded forest with fleeing wildlife; river mouth with sediment plume over reef."""
import numpy as np, cv2
from lib import *
from city import skygrad, cat

_S = {}


def setup_forest():
    if 'F' in _S:
        return
    rng = np.random.default_rng(31)
    n = 3400
    tx = rng.uniform(-130, 130, n); ty = rng.uniform(-50, 520, n)
    h = rng.uniform(9, 23, n); w = rng.uniform(6, 13, n)
    hue = rng.uniform(0, 1, n)
    dead = rng.random(n) < 0.10
    r = 0.07 + 0.12 * hue + dead * 0.15; g = 0.20 + 0.16 * hue - dead * 0.04; b = 0.06 + 0.04 * hue + dead * 0.0
    _S['F'] = dict(cx=tx, cy=ty, w=w, d=np.ones(n), h=h, r=r, g=g, b=b, kind=np.ones(n, int))
    _S['water'] = WaterSys(seed=47); _S['sky'] = Sky(13); _S['rain'] = RainFx(seed=21)
    _S['cam'] = Cam(); _S['camh'] = Cam(W // 2, H // 2)
    _S['bphase'] = rng.uniform(0, 6.28, 40)
    _S['bpos'] = np.stack([rng.uniform(-22, 22, 40), rng.uniform(20, 70, 40), rng.uniform(14, 28, 40)], 1)


def draw_birds(can, cam, T, base_y, fogc, fogk):
    P0 = _S['bpos']; ph = _S['bphase']
    for i in range(len(P0)):
        vel = np.array([0.6 * np.sin(i), 9.5 + (i % 5) * 0.4, 1.4])
        c = P0[i] + vel * T + np.array([0, base_y * 0.0, 0])
        flap = np.sin(T * 2 * np.pi * 3.2 + ph[i])
        pts3 = [c + np.array([0, 0.55, 0]), c + np.array([0, -0.55, 0]), c + np.array([1.05, -0.1, 0.55 * flap]), c + np.array([-1.05, -0.1, 0.55 * flap])]
        xc, yc, zc = cam.to_cam(np.array(pts3))
        if (yc < 1).any():
            continue
        u, v = cam.proj(xc, yc, zc)
        dist = np.linalg.norm(c - cam.pos)
        fg = 1 - np.exp(-dist * fogk)
        col_ = np.clip(np.array([0.93, 0.94, 0.95], f32) * (1 - fg) + np.array(fogc, f32) * fg, 0, 1) * 255
        colt = tuple(float(x) for x in col_)
        wing_l = np.array([[u[0], v[0]], [u[3], v[3]], [u[1], v[1]]]); wing_r = np.array([[u[0], v[0]], [u[2], v[2]], [u[1], v[1]]])
        for wing in (wing_l, wing_r):
            cv2.fillConvexPoly(can, np.round(wing * 16).astype(np.int32), colt, cv2.LINE_AA, 4)
        cv2.line(can, (int(u[0]), int(v[0])), (int(u[1]), int(v[1])), tuple(float(x) * 0.8 for x in colt), max(1, int(cam.f * 0.16 / yc[0])), cv2.LINE_AA)


def draw_deer(can, cam, T, fogc, fogk):
    c0 = np.array([-34.0 + 1.5 * T, 38.0 + 8.0 * T, 0.0])
    head = c0 + np.array([0.6, 0, 0.55]); back = c0 + np.array([-0.5, 0, 0.12])
    xc, yc, zc = cam.to_cam(np.array([head, back, c0 + np.array([-1.0, 0, 0.1])]))
    if (yc < 1).any():
        return
    u, v = cam.proj(xc, yc, zc)
    r = max(2, int(cam.f * 0.22 / yc[0]))
    cv2.ellipse(can, (int(u[1]), int(v[1])), (int(r * 2.2), int(r * 0.8)), 0, 0, 360, (92, 70, 48), -1, cv2.LINE_AA)
    cv2.line(can, (int(u[0]), int(v[0])), (int(u[1]), int(v[1])), (96, 74, 50), max(2, int(r * 0.9)), cv2.LINE_AA)
    cv2.circle(can, (int(u[0]), int(v[0])), r, (104, 80, 56), -1, cv2.LINE_AA)
    for sg in (-1, 1):
        w = c0 + np.array([-3.5, sg * 2.2, 0.0])
        xw, yw, zw = cam.to_cam(np.array([c0 + np.array([-0.9, 0, 0.0]), w]))
        uw, vw = cam.proj(xw, yw, zw)
        cv2.line(can, (int(uw[0]), int(vw[0])), (int(uw[1]), int(vw[1])), (205, 205, 200), max(1, int(r * 0.25)), cv2.LINE_AA)


def forest(pos, yaw, pitch, T, rain_i=1.0):
    setup_forest()
    S = _S
    cam = S['cam'].set(pos, yaw, pitch)
    d = cam.dirs()
    below = d[..., 2] < -1e-4
    t = -cam.pos[2] / np.where(below, d[..., 2], -1e-4)
    X = cam.pos[0] + d[..., 0] * t; Y = cam.pos[1] + d[..., 1] * t
    fogc = (0.50, 0.54, 0.54); haze = 1 / 420.
    sky = S['sky'].render(d, cam.pos, T, zen=(0.32, 0.36, 0.40), hor=fogc)
    base = np.broadcast_to(np.array([0.30, 0.24, 0.15], f32), d.shape)
    wat = S['water'].shade(X, Y, d, t, T, base, skygrad, flow=(0.4, 0.2), rip=1.0, fogc=fogc, fogk=haze, amp=(0.012, 0.003))
    # canopy shade on water
    camh = S['camh'].set(pos, yaw, pitch)
    sh = np.zeros((H // 2, W // 2), np.uint8)
    F = S['F']
    near = np.nonzero(np.hypot(F['cx'] - pos[0], F['cy'] - pos[1]) < 260)[0]
    P = np.stack([F['cx'][near], F['cy'][near], np.zeros(len(near))], 1)
    xc, yc, zc = camh.to_cam(P)
    ok = yc > 1
    u, v = camh.proj(xc[ok], yc[ok], zc[ok])
    rad = camh.f * F['w'][near][ok] * 0.55 / yc[ok]
    for a, b, r_ in zip(u, v, rad):
        if -50 < a < camh.w + 50 and -50 < b < camh.h + 50:
            cv2.circle(sh, (int(a), int(b)), max(1, int(r_)), 255, -1, cv2.LINE_AA)
    sh = cv2.GaussianBlur(sh, (0, 0), 5).astype(f32) / 255.0
    sh = cv2.resize(sh, (W, H))[..., None]
    wat = wat * (1 - 0.38 * sh)
    img = np.where(below[..., None], wat, sky)
    can = np.clip(img * 255, 0, 255).astype(np.uint8)
    draw_boxes(can, cam, F, T, fog=fogc, fogk=haze, maxd=300)
    can = cv2.GaussianBlur(can, (0, 0), 1.7)
    draw_deer(can, cam, T, fogc, haze)
    draw_birds(can, cam, T, 0, fogc, haze)
    img = can.astype(f32) / 255.0
    leaf = cv2.GaussianBlur(np.random.default_rng(3).standard_normal((H, W)).astype(f32), (0, 0), 0.9) * 0.55
    img = img * (1 + 0.16 * leaf[..., None] * (~below[..., None]).astype(f32) * 0 + 0.16 * leaf[..., None] * below[..., None])
    img = S['rain'].apply(img, T + 1, rain_i)
    return grade(img, sat=0.85, contrast=1.1)


def shot_a(i, n=150):
    T = i / FPS
    return forest((3 * np.sin(T * .4), -40 + 8.0 * T, 36 - 0.5 * T), 0.03 * np.sin(T * .6), np.radians(36 - 0.8 * T), T)


# ---------------------------------------------------------------- estuary
MPP = 0.8
NN = 2048


def build_est():
    rng = np.random.default_rng(77)
    Y, X = np.mgrid[0:NN, 0:NN].astype(f32)
    n1 = fbm(NN, 2.6, 71); hf = fbm(NN, 1.1, 72); n2 = fbm(NN, 2.0, 73)
    coast = 1150 + 110 * np.sin(X / 260.0) + 50 * np.sin(X / 85.0 + 1) + 25 * n1
    xc = 1000 + 150 * np.sin(Y / 220.0) + 40 * np.sin(Y / 70.0)
    wr = 16 + 110 * sstep(coast - 500, coast + 20, Y)
    river = sstep(wr, wr * 0.7, np.abs(X - xc)) * (Y < coast + 60)
    land = sstep(coast + 3, coast - 3, Y) * (1 - river)
    depth = np.clip((Y - coast) / 520.0, 0, 1) + 0.04 * n1
    shallow = col(46, 126, 118); deep = col(10, 44, 78)
    sea = shallow + (deep - shallow) * sstep(0.05, 0.65, depth)[..., None]
    reefm = sstep(0.35, 0.8, n2 * 0.7 + hf * 0.35) * sstep(0.08, 0.2, depth) * sstep(0.7, 0.4, depth)
    reefc = col(34, 78, 60) * (0.75 + 0.35 * hf[..., None] * 0.5)
    ring = sstep(0.0, 0.35, reefm) * (1 - sstep(0.35, 0.9, reefm))
    sea = sea * (1 - reefm[..., None]) + reefc * reefm[..., None]
    sea = sea + col(40, 90, 80) * (ring[..., None] * 0.2)
    # land colours: mangrove belt + inland
    dc = np.clip((coast - Y) / 160.0, 0, 1)
    mang = col(14, 38, 16) + (col(38, 70, 26) - col(14, 38, 16)) * sstep(-1.0, 1.3, hf)[..., None]
    inl = col(48, 78, 32) + (col(86, 98, 50) - col(48, 78, 32)) * sstep(-0.8, 1.2, n2)[..., None]
    landc = mang * (1 - sstep(0.7, 1.0, dc)[..., None]) + inl * sstep(0.7, 1.0, dc)[..., None]
    landc = landc * (0.85 + 0.25 * hf[..., None] * 0.5)
    sandbar = sstep(2.0, 0.0, np.abs(Y - coast - 6)) * (1 - river)
    landc = landc * (1 - sandbar[..., None] * 0.7) + col(150, 140, 108) * sandbar[..., None] * 0.7
    return dict(sea=sea.astype(f32), landc=landc.astype(f32), land=land.astype(f32), river=river.astype(f32),
                coast=coast.astype(f32), xc=xc.astype(f32), n2=n2, hf=hf)


def setup_est():
    if 'E' in _S:
        return
    _S['E'] = build_est()
    _S['Em'] = np.dstack([_S['E']['sea'], _S['E']['land'], _S['E']['river'], _S['E']['landc']]).astype(f32)  # 3+1+1+3 = 8 ch
    _S['water2'] = WaterSys(seed=57); _S['sky2'] = Sky(19); _S['rain2'] = RainFx(seed=26)
    _S['cam2'] = Cam()


def gulls(can, cam, T, fogc, fogk):
    rng = np.random.default_rng(5)
    for i in range(16):
        c = np.array([rng.uniform(-30, 30), rng.uniform(40, 160), rng.uniform(35, 75)]) + np.array([2.0 * np.sin(T * .8 + i), 7 * T, 0.0])
        c = c + cam.pos * np.array([1, 0, 0]) * 0
        flap = np.sin(T * 2 * np.pi * 2.6 + i * 1.3)
        pts3 = [c + np.array([0, 0.5, 0]), c + np.array([0, -0.5, 0]), c + np.array([0.95, 0.0, 0.5 * flap]), c + np.array([-0.95, 0.0, 0.5 * flap])]
        xc, yc, zc = cam.to_cam(np.array(pts3) + np.array([cam.pos[0], 0, 0]))
        if (yc < 1).any():
            continue
        u, v = cam.proj(xc, yc, zc)
        dist = np.linalg.norm(c - cam.pos)
        fg = 1 - np.exp(-dist * fogk)
        col_ = tuple(float(x) * 255 for x in np.clip(np.array([0.9, 0.9, 0.92], f32) * (1 - fg) + np.array(fogc, f32) * fg, 0, 1))
        for wing in ([[u[0], v[0]], [u[3], v[3]], [u[1], v[1]]], [[u[0], v[0]], [u[2], v[2]], [u[1], v[1]]]):
            cv2.fillConvexPoly(can, np.round(np.array(wing) * 16).astype(np.int32), col_, cv2.LINE_AA, 4)


def estuary(pos, yaw, pitch, T, plume_T, rain_i=1.0):
    setup_est()
    S = _S; E = S['E']
    cam = S['cam2'].set(pos, yaw, pitch)
    d = cam.dirs()
    below = d[..., 2] < -1e-4
    t = -cam.pos[2] / np.where(below, d[..., 2], -1e-4)
    X = cam.pos[0] + d[..., 0] * t; Y = cam.pos[1] + d[..., 1] * t
    mx, my = X / MPP, Y / MPP
    m = samp(S['Em'], mx, my)
    sea, land, river, landc = m[..., 0:3], m[..., 3:4], m[..., 4:5], m[..., 5:8]
    # plume
    Mx, My = 1000 + 0.0, 1150 + 20
    dx = (mx - Mx) * 0.62; dy = (my - My)
    wn = samp(E['n2'], mx * 0.9 + plume_T * 12, my * 0.9 - plume_T * 9)
    wn2 = samp(E['hf'], mx * 2.2 - plume_T * 20, my * 2.2)
    dist = np.sqrt(dx * dx + dy * dy) + 85 * wn + 22 * wn2
    R = lerp(70, 520, sstep(0.0, 1.0, plume_T / 5.0) ** 0.8)
    P = sstep(R, R * 0.35, dist)[..., None]
    P = P * (1 - land)
    brown = np.array([0.40, 0.29, 0.18], f32) * (0.94 + 0.05 * wn2[..., None] + 0.06 * wn[..., None])
    bodyc = sea * (1 - P * 0.93) + brown * P * 0.93
    bodyc = bodyc * (1 - river) + brown * river
    fogc = (0.56, 0.60, 0.62); haze = 1 / 1500.
    sky = S['sky2'].render(d, cam.pos, T, zen=(0.36, 0.40, 0.45), hor=fogc)
    wat = S['water2'].shade(X, Y, d, t, T, bodyc, skygrad, flow=(0.5, 1.0), rip=0.8, fogc=fogc, fogk=haze, L=(70., 9.), amp=(0.012, 0.003), refl=0.7)
    lnd = landc * (0.8 + 0.2 * wn2[..., None] * 0.5)
    img = wat * (1 - land) + lnd * land
    fg = (1 - np.exp(-t * haze))[..., None]
    img = np.where(land > 0.5, img * (1 - fg) + np.array(fogc, f32) * fg, img)
    img = np.where(below[..., None], img, sky)
    can = np.clip(img * 255, 0, 255).astype(np.uint8)
    gulls(can, cam, T, fogc, haze)
    img = can.astype(f32) / 255.0
    img = S['rain2'].apply(img, T + 2, rain_i * 0.8)
    return grade(img, sat=0.95, contrast=1.08)


def shot_b(i, n=150):
    T = i / FPS
    return estuary((1000 * MPP + 4 * np.sin(T * .4), 780 + 11 * T, 105 - 2 * T), 0.0 + 0.015 * np.sin(T * .5), np.radians(44 + 0.8 * T), T + 5, T)
