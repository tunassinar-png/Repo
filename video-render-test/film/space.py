"""Scenes 1 & 6: Earth from orbit, cloud-layer fly-through, sea."""
import numpy as np, cv2
from lib import *

_S = {}


def build_earth(cov=-0.35, seed=21):
    Hh, Ww = 1024, 2048
    c = fbm(2048, 2.9, seed)[:Hh]
    c2 = fbm(2048, 2.2, seed + 3)[:Hh]
    Y, X = np.mgrid[0:Hh, 0:Ww].astype(f32)
    rng = np.random.default_rng(seed)
    dispx = np.zeros_like(X); dispy = np.zeros_like(X); boost = np.zeros_like(X)
    centers = [(300, 330, 190, 1), (820, 560, 220, -1), (1250, 300, 170, 1), (1650, 650, 230, -1),
               (500, 760, 150, -1), (1000, 200, 150, 1), (1850, 330, 180, 1), (1400, 860, 160, -1)]
    for (cx, cy, rad, sg) in centers:
        dx = (X - cx + Ww / 2) % Ww - Ww / 2; dy = Y - cy
        r = np.hypot(dx, dy) + 1e-3
        g = np.exp(-(r / rad) ** 2)
        ang = sg * 3.4 * g
        ca, sa = np.cos(ang), np.sin(ang)
        dispx += dx * ca - dy * sa - dx; dispy += dx * sa + dy * ca - dy
        th = np.arctan2(dy, dx)
        arms = 0.5 + 0.5 * np.cos(2 * th - sg * 6.0 * np.log(r / rad + 0.08))
        boost += g * (0.7 + 0.9 * arms) + 0.25 * np.exp(-(r / (rad * 2.2)) ** 2)
    cw = cv2.remap(c, (X + dispx) % Ww, np.clip(Y + dispy, 0, Hh - 1), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    q = 0.5 * cw + 0.18 * c2 + 0.85 * boost
    dens = sstep(cov - 0.1, cov + 1.0, q)
    sm = cv2.GaussianBlur(dens, (0, 0), 2.0)
    gy, gx = np.gradient(sm)
    shade = np.clip(0.62 + 4.0 * (-gx * 0.7 - gy * 0.7) + 0.35 * dens, 0, 1.15)
    dark = col(46, 54, 66); light = col(205, 211, 221)
    cloud = dark + (light - dark) * np.clip(shade * (0.55 + 0.5 * sstep(0.1, 1.2, q)), 0, 1)[..., None]
    land_f = fbm(2048, 2.6, seed + 9)[:Hh]
    land = sstep(0.1, 0.35, land_f)[..., None]
    ocean = col(10, 36, 66); lnd = col(40, 62, 30)
    surf = ocean * (1 - land) + lnd * land
    alb = surf * (1 - dens[..., None]) + cloud * dens[..., None]
    return alb.astype(f32)


def stars(seed=3):
    rng = np.random.default_rng(seed)
    im = np.zeros((H, W), f32)
    for _ in range(900):
        im[rng.integers(0, H), rng.integers(0, W)] = rng.uniform(0.15, 1.0) ** 2
    im = cv2.GaussianBlur(im, (0, 0), 0.8) * 7
    return np.clip(im, 0, 1)


def setup():
    if 'earth' in _S:
        return _S
    _S['earth'] = build_earth(-0.75)
    _S['earth2'] = build_earth(0.05)   # clearing: same structure, thinner cover
    _S['stars'] = stars()
    _S['yy'], _S['xx'] = np.mgrid[0:H, 0:W].astype(f32)
    _S['rain'] = RainFx(seed=9)
    return _S


def sphere(cx, cy, R, spin, tilt, sun, tex, clear=0.0, flare=0.0):
    S = setup()
    X, Y = S['xx'], S['yy']
    nx = (X - cx) / R; ny = -(Y - cy) / R
    r2 = nx * nx + ny * ny
    inside = r2 < 1.0
    nz = np.sqrt(np.clip(1 - r2, 0, 1))
    # rotate normal into body frame
    ct, st = np.cos(tilt), np.sin(tilt)
    y1 = ny * ct - nz * st; z1 = ny * st + nz * ct
    cs, ss = np.cos(spin), np.sin(spin)
    x2 = nx * cs + z1 * ss; z2 = -nx * ss + z1 * cs
    lat = np.arcsin(np.clip(y1, -1, 1)); lon = np.arctan2(x2, z2)
    u = (lon / (2 * np.pi) + 0.5) * 2048; v = (0.5 - lat / np.pi) * 1024
    if tex is None:
        tex = S['earth']
    if clear > 0:
        t1 = cv2.remap(S['earth'], u.astype(f32) % 2048, np.clip(v, 0, 1023).astype(f32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        t2 = cv2.remap(S['earth2'], u.astype(f32) % 2048, np.clip(v, 0, 1023).astype(f32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        alb = t1 * (1 - clear) + t2 * clear
    else:
        alb = cv2.remap(tex, u.astype(f32) % 2048, np.clip(v, 0, 1023).astype(f32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    s = np.array(sun, f32); s /= np.linalg.norm(s)
    lam = nx * s[0] + ny * s[1] + nz * s[2]
    day = sstep(-0.08, 0.38, lam)
    twi = np.exp(-(lam / 0.10) ** 2)
    sunset = np.array([1.0, 0.52, 0.22], f32)
    col_ = alb * (0.015 + 0.82 * day[..., None]) + twi[..., None] * sunset * (0.16 + 0.22 * flare) * (0.4 + 0.6 * alb.mean(-1, keepdims=True))
    rim = (1 - nz) ** 3.0
    atm = np.array([0.32, 0.55, 1.0], f32)
    col_ = col_ + atm * (rim * (0.25 + 1.3 * day))[..., None] * 0.9
    out = np.where(inside[..., None], col_, 0.0)
    # outer halo
    r = np.sqrt(r2)
    dirx = nx / (r + 1e-6); diry = ny / (r + 1e-6)
    lit = np.clip(dirx * s[0] + diry * s[1] + 0.35, 0, 1.2)
    halo = np.exp(-np.clip(r - 1, 0, None) / 0.022) * (r >= 1) * (0.2 + 0.9 * lit) * (R / 1400)
    halo2 = np.exp(-np.clip(r - 1, 0, None) / 0.07) * (r >= 1) * lit * 0.12
    out = out + (halo * np.array([0.35, 0.6, 1.0], f32)[..., None].T.reshape(1, 1, 3) if False else halo[..., None] * np.array([0.38, 0.62, 1.0], f32) + halo2[..., None] * np.array([0.4, 0.55, 0.9], f32))
    st_ = S['stars'] * (r >= 1.015)
    out = out + st_[..., None] * 0.9
    # sun bloom at limb (final scene)
    if flare > 0:
        sx = cx + R * s[0] / np.hypot(s[0], s[1]) * 1.0; sy = cy - R * s[1] / np.hypot(s[0], s[1]) * 1.0
        d2 = ((X - sx) ** 2 + (Y - sy) ** 2) / (R * 0.5) ** 2
        out = out + (np.exp(-d2 * 3.0) * 0.9 * flare)[..., None] * np.array([1.0, 0.82, 0.55], f32)
        d3 = ((X - sx) ** 2 + (Y - sy) ** 2) / (R * 1.6) ** 2
        out = out + (np.exp(-d3 * 2.0) * 0.18 * flare)[..., None] * np.array([1.0, 0.7, 0.4], f32)
    return out.astype(f32)


def earth_a(i, n=150):
    S = setup()
    T = i / FPS
    R = 1300 + 40 * T
    img = sphere(540 + 6 * T, 1960 + 10 * T, R, 0.55 + 0.075 * T, 0.38, (-0.62, 0.40, 0.68), S['earth'])
    return grade(img, sat=1.0, contrast=1.12, bloom=0.4, vig=0.25, exposure=0.95)


def earth_b(i, n=150):
    S = setup()
    T = i / FPS
    s = T / 5.0
    e = s * s * (3 - 2 * s)
    R = lerp(1900, 500, e)
    cy = lerp(1560, 1010, e)
    img = sphere(540, cy, R, 1.9 + 0.05 * T, 0.38, (-0.66, 0.42, 0.50), None, clear=sstep(0.0, 1.0, s) * 0.95, flare=sstep(0.2, 1.0, s))
    return grade(img, sat=1.0, contrast=1.1, bloom=0.6, vig=0.22)


# ------------------------------------------------------------ cloud-layer fly-through
def build_cloud():
    f = fbm(1024, 2.6, 41)
    hm = sstep(-1.3, 1.6, f) + 0.25 * sstep(-0.5, 1.5, fbm(1024, 1.9, 42))
    sm = cv2.GaussianBlur(hm, (0, 0), 1.6)
    gy, gx = np.gradient(sm)
    sh = np.clip(0.55 + 7.0 * (-gx * 0.8 - gy * 0.55) + 0.5 * hm, 0, 1)
    shadow = col(95, 108, 130); lit = col(255, 250, 244)
    top = shadow + (lit - shadow) * sh[..., None]
    base_t = fbm(1024, 2.3, 43)
    under = (col(46, 51, 59) * (0.78 + 0.28 * base_t[..., None])).astype(f32)
    under = np.clip(under, 0, 1)
    return top.astype(f32), under, sm


def cloud_setup():
    if 'top' in _S:
        return
    _S['top'], _S['under'], _S['hm'] = build_cloud()
    _S['water'] = WaterSys(seed=31)
    _S['cam'] = Cam()
    _S['sky'] = Sky(7)


def sea_sky(R, tone):
    z = np.clip(R[..., 2], 0, 1)[..., None]
    hor = np.array(tone[0], f32); zen = np.array(tone[1], f32)
    return hor + (zen - hor) * np.clip(z * 2, 0, 1) ** 0.7


def cloudfly(pos, yaw, pitch, T, zb=700., zt=2300., sig=0.0024, warm=0.0, sun=(0.0, 1.0, 0.10), rain_i=1.0, godray=0.0):
    cloud_setup()
    cam = _S['cam'].set(pos, yaw, pitch)
    d = cam.dirs()
    Cz = pos[2]
    dz = d[..., 2]
    hazec = np.array(lerp(np.array([0.34, 0.37, 0.40], f32), np.array([0.95, 0.80, 0.62], f32), warm), f32)
    # ----- world pieces
    below = dz < -1e-4
    # sea
    ts = -Cz / np.where(below, dz, -1e-4)
    Xs = pos[0] + d[..., 0] * ts; Ys = pos[1] + d[..., 1] * ts
    tone = ((0.40, 0.44, 0.48), (0.2, 0.23, 0.28))
    seabase = np.broadcast_to(np.array([0.085, 0.14, 0.17], f32), d.shape)
    sea = _S['water'].shade(Xs, Ys, d, ts, T, seabase, lambda R: sea_sky(R, tone), flow=(3.0, -4.0), L=(160., 22.), amp=(0.7, 0.10),
                            rip=0.0, refl=0.9, foam=0.55, fogc=tuple(hazec), fogk=1 / 3200.)
    sea = np.where(below[..., None], sea, hazec)
    sun_d = np.array([sun[0], sun[1], sun[2]], f32); sun_d /= np.linalg.norm(sun_d)
    cos_s = (d * sun_d).sum(-1)
    def skycol(dzv):
        zen = np.array([0.30, 0.46, 0.80], f32) * (1 - 0.7 * (1 - warm)) + np.array([0.20, 0.22, 0.26], f32) * (1 - warm) * 0.7
        hor = hazec
        g = np.clip(dzv * 2.5, 0, 1)[..., None] ** 0.6
        return hor + (zen - hor) * g
    sky = skycol(np.clip(dz, 0, 1))
    glow = np.exp(-np.clip(1 - cos_s, 0, 2) * 220.)[..., None] * warm
    sky = sky + glow * np.array([1.0, 0.82, 0.6], f32) * 0.9 + (cos_s > 0.99997)[..., None] * warm * 2.5
    # ----- regions
    if Cz >= zt:
        tt = (Cz - zt) / np.where(below, -dz, 1e-4)
        X = pos[0] + d[..., 0] * tt; Y = pos[1] + d[..., 1] * tt
        top = samp(_S['top'], X / 9.0 + 7 * T / 9, Y / 9.0)
        lt = np.array(lerp(np.array([1.0, 1.0, 1.0], f32), np.array([1.04, 0.90, 0.76], f32), warm), f32)
        topc = top * lt
        topc = topc * (1 - warm * 0.15 * (1 - samp(_S['hm'], X / 9.0, Y / 9.0))[..., None])
        fogk = 1 / 9000.
        fg = (1 - np.exp(-tt * fogk))[..., None]
        topc = topc * (1 - fg) + hazec * fg * 1.05
        img = np.where(below[..., None], topc, sky)
    elif Cz > zb:
        a = (Cz - zb) / (zt - zb)
        fogcol = lerp(np.array([0.20, 0.22, 0.25], f32), np.array([0.82, 0.84, 0.88], f32) * (1 + warm * np.array([0.1, -0.05, -0.25], f32)), a ** 1.2)
        nz_ = samp(_S['top'], pos[0] / 9 + d[..., 0] * 90 + 3 * T, pos[1] / 9 + d[..., 1] * 90).mean(-1, keepdims=True)
        fogim = fogcol * (0.9 + 0.2 * nz_)
        Ld = np.where(below, (Cz - zb) / np.maximum(-dz, 1e-3), (zt - Cz) / np.maximum(dz, 1e-3))
        Tr = np.exp(-sig * Ld)[..., None]
        beyond = np.where(below[..., None], sea, sky)
        img = beyond * Tr + fogim * (1 - Tr)
    else:
        up = dz > 1e-4
        tu = (zb - Cz) / np.where(up, dz, 1e-4)
        X = pos[0] + d[..., 0] * tu; Y = pos[1] + d[..., 1] * tu
        und = samp(_S['under'], X / 7.0 + 4 * T / 7, Y / 7.0)
        fgu = (1 - np.exp(-tu / 2600.))[..., None]
        und = und * (1 - fgu) + hazec * fgu
        und = und * (0.55 + 0.9 * np.clip(0.5 + 0.5 * (zb - Cz) / 900., 0, 1)) if False else und
        img = np.where(up[..., None], und, sea)
    img = _S['rain'].apply(img, T, rain_i * (0.7 if Cz > zt else 1.0))
    return img.astype(f32)


def godrays(img, cam, sun, strength):
    sd = np.array(sun, float); sd /= np.linalg.norm(sd)
    xc, yc, zc = sd @ cam.right, sd @ cam.fwd, sd @ cam.up
    if yc <= 0.01 or strength <= 0:
        return img
    u, v = W / 2 + cam.f * xc / yc, H / 2 - cam.f * zc / yc
    small = cv2.resize(img, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    lum = small.mean(-1, keepdims=True)
    br = np.clip(small - 0.55, 0, 4) * (lum > 0.55)
    acc = np.zeros_like(br); cur = br
    cx_, cy_ = u / 2, v / 2
    for k in range(22):
        M = cv2.getRotationMatrix2D((cx_, cy_), 0, 1.0 - 0.018 * (k + 1))
        acc += cv2.warpAffine(br, M, (W // 2, H // 2), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * (0.93 ** k)
    acc = cv2.resize(acc / 7, (W, H), interpolation=cv2.INTER_LINEAR)
    return img + acc * strength * np.array([1.0, 0.82, 0.58], f32)


def descent(i, n=150):
    T = i / FPS; s = T / 5.0
    Cz = 160 + 4340 * (1 - s) ** 2
    pitch = np.radians(lerp(78, 14, sstep(0.0, 1.0, s) ** 0.8))
    img = cloudfly((0, -3000 + 600 * T, Cz), 0.0, pitch, T, rain_i=1.0)
    img = grade(img, sat=0.8, contrast=1.1, bloom=0.2)
    return img


def ascent(i, n=150):
    T = i / FPS; s = T / 5.0
    Cz = 80 + 3350 * s ** 2.1
    pitch = np.radians(lerp(-28, 3.5, sstep(0.1, 1.0, s)))
    warm = sstep(0.55, 0.9, s)
    sun = (0.15, 1.0, 0.09)
    cam = _S['cam'] if 'cam' in _S else None
    img = cloudfly((0, -2000 + 450 * T, Cz), 0.0, pitch, T + 100, warm=warm, sun=sun, rain_i=1.0 - 0.85 * sstep(0.45, 0.85, s))
    cloud_setup()
    cam = _S['cam'].set((0, 0, Cz), 0.0, pitch)
    img = godrays(img, cam, sun, 0.45 * sstep(0.5, 1.0, s))
    img = grade(img, sat=0.9 + 0.05 * warm, contrast=1.08, bloom=0.35 * warm + 0.15, exposure=1 - 0.25 * warm, warm=(1.0 + 0.03 * warm, 1.0, 1.0 - 0.05 * warm))
    return img
