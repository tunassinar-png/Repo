"""Core procedural rendering library (numpy + OpenCV). All images are float32 RGB 0..1, size H x W."""
import numpy as np
import cv2

W, H, FPS = 1080, 1920, 30
f32 = np.float32
cv2.setNumThreads(1)


# ---------------------------------------------------------------- noise
def fbm(n, beta=2.4, seed=0):
    """Tileable spectral fractal noise, zero mean / unit variance."""
    rng = np.random.default_rng(seed)
    fx = np.fft.fftfreq(n)[:, None]
    fy = np.fft.rfftfreq(n)[None, :]
    f = np.sqrt(fx ** 2 + fy ** 2)
    f[0, 0] = 1
    amp = f ** (-beta / 2)
    amp[0, 0] = 0
    ph = rng.standard_normal((n, n // 2 + 1)) + 1j * rng.standard_normal((n, n // 2 + 1))
    x = np.fft.irfft2(ph * amp, s=(n, n)).astype(f32)
    return ((x - x.mean()) / (x.std() + 1e-9)).astype(f32)


def sstep(a, b, x):
    t = np.clip((x - a) / (b - a + 1e-9), 0, 1)
    return t * t * (3 - 2 * t)


def samp(tex, x, y, interp=cv2.INTER_LINEAR):
    """Sample tileable texture at pixel coords (wrapping)."""
    h, w = tex.shape[:2]
    return cv2.remap(tex, (x % w).astype(f32), (y % h).astype(f32), interp, borderMode=cv2.BORDER_WRAP)


def grad_tile(a, k=1.0):
    gy, gx = np.gradient(a)
    return np.dstack([a, gx * k, gy * k]).astype(f32)


def lerp(a, b, t):
    return a + (b - a) * t


def col(r, g, b):
    return np.array([r, g, b], f32) / 255.0


# ---------------------------------------------------------------- camera
class Cam:
    def __init__(s, w=W, h=H, fov_v=96.0):
        s.w, s.h = w, h
        s.f = (h / 2) / np.tan(np.radians(fov_v / 2))
        u = (np.arange(w) + .5 - w / 2) / s.f
        v = -(np.arange(h) + .5 - h / 2) / s.f
        s.u = np.broadcast_to(u[None, :], (h, w)).astype(f32)
        s.v = np.broadcast_to(v[:, None], (h, w)).astype(f32)

    def set(s, pos, yaw, pitch):
        """yaw: heading rad (0 = +y, clockwise); pitch: rad, positive looks DOWN."""
        s.pos = np.array(pos, np.float64)
        cy, sy, cp, sp = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch)
        s.right = np.array([cy, -sy, 0.0])
        fwdh = np.array([sy, cy, 0.0])
        s.fwd = cp * fwdh + np.array([0, 0, -sp])
        s.up = sp * fwdh + np.array([0, 0, cp])
        return s

    def dirs(s):
        """Unit ray directions (H,W,3) float32."""
        d = (s.u[..., None] * s.right.astype(f32) + s.fwd.astype(f32) + s.v[..., None] * s.up.astype(f32))
        d /= np.sqrt((d * d).sum(-1, keepdims=True))
        return d

    def to_cam(s, P):
        rel = np.asarray(P, np.float64) - s.pos
        return rel @ s.right, rel @ s.fwd, rel @ s.up

    def proj(s, xc, yc, zc):
        yc = np.maximum(yc, 1e-4)
        return s.w / 2 + s.f * xc / yc, s.h / 2 - s.f * zc / yc


# ---------------------------------------------------------------- sky
class Sky:
    def __init__(s, seed=5):
        s.cl = fbm(1024, 2.8, seed)

    def render(s, d, campos, T, zen=(0.20, 0.23, 0.28), hor=(0.52, 0.55, 0.58), cz=2200., drift=(6., 2.), dark=1.0):
        dz = np.clip(d[..., 2], 1e-3, 1)
        zen, hor = np.array(zen, f32), np.array(hor, f32)
        g = np.clip(dz * 2.2, 0, 1)[..., None] ** 0.7
        base = hor + (zen - hor) * g
        t = (cz - campos[2]) / dz
        x = campos[0] + d[..., 0] * t + drift[0] * T
        y = campos[1] + d[..., 1] * t + drift[1] * T
        a = samp(s.cl, x / 25.0, y / 25.0)
        fade = np.clip(dz * 5, 0, 1)
        c = np.clip(0.62 + 0.20 * a, 0.2, 1.0)[..., None]
        out = base * (c * fade[..., None] + (1 - fade[..., None])) * dark
        return out.astype(f32)


# ---------------------------------------------------------------- water
class Ripples:
    """Rain rings on a 512 px tile (tile covers `size` metres)."""
    def __init__(s, n=512, size=6.0, rate=900, life=0.6, seed=2):
        rng = np.random.default_rng(seed)
        s.n, s.size, s.life = n, size, life
        s.N = int(rate * life * 2)
        s.px = rng.uniform(0, n, s.N).astype(f32)
        s.py = rng.uniform(0, n, s.N).astype(f32)
        s.t0 = rng.uniform(0, 1000, s.N)
        s.per = rng.uniform(0.9, 1.1, s.N) * (s.N / rate)  # re-spawn period

    def tile(s, T):
        img = np.zeros((s.n, s.n), f32)
        age = np.mod(T - s.t0, s.per)
        act = np.nonzero(age < s.life)[0]
        for i in act:
            a = age[i] / s.life
            r = 2 + a * 26
            cv2.circle(img, (int(s.px[i]), int(s.py[i])), int(r), float((1 - a) ** 2) * 1.0, 1, cv2.LINE_8)
        img = cv2.GaussianBlur(img, (0, 0), 1.1)
        gy, gx = np.gradient(img)
        return np.dstack([img, gx, gy]).astype(f32)


class WaterSys:
    def __init__(s, seed=11):
        s.t1 = grad_tile(fbm(1024, 2.6, seed), 1.0)
        s.t2 = grad_tile(fbm(1024, 2.0, seed + 1), 1.0)
        s.rp = Ripples()

    def shade(s, X, Y, d, dist, T, base, sky, flow=(0.0, -1.2), L=(90., 11.), amp=(0.02, 0.0025), rip=0.0,
              refl=0.85, foam=0.0, cam=None, fogc=(0.5, 0.52, 0.54), fogk=1 / 700., spec_rain=None):
        """Shade a water plane (z=0). base: HxWx3 body colour; sky: callable(R)->HxWx3 reflection colour."""
        fl = np.array(flow) * T
        s1 = s.t1.shape[0] / L[0]
        s2 = s.t2.shape[0] / L[1]
        a = samp(s.t1, (X + fl[0]) * s1, (Y + fl[1]) * s1)
        b = samp(s.t2, (X + fl[0] * 1.6) * s2, (Y + fl[1] * 1.6) * s2)
        near = np.exp(-dist / 120.)
        far = np.exp(-dist / 400.)
        nx = -(a[..., 1] * amp[0] * s1 * far + b[..., 1] * amp[1] * s2 * near)
        ny = -(a[..., 2] * amp[0] * s1 * far + b[..., 2] * amp[1] * s2 * near)
        if rip > 0:
            rt = s.rp.tile(T)
            rr = samp(rt, X * (512 / s.rp.size), Y * (512 / s.rp.size))
            nr = rip * 0.004 * (512 / s.rp.size) * np.exp(-dist / 35.)
            nx += -rr[..., 1] * nr
            ny += -rr[..., 2] * nr
        nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0.2, 1))
        nxl = np.sqrt(nx * nx + ny * ny + nz * nz)
        nx, ny, nz = nx / nxl, ny / nxl, nz / nxl
        ddn = d[..., 0] * nx + d[..., 1] * ny + d[..., 2] * nz
        R = np.stack([d[..., 0] - 2 * ddn * nx, d[..., 1] - 2 * ddn * ny, np.abs(d[..., 2] - 2 * ddn * nz)], -1)
        cosv = np.clip(-ddn, 0, 1)
        F = 0.03 + 0.97 * (1 - cosv) ** 5
        F = np.clip(F * refl + 0.04, 0, 1)[..., None]
        diff = np.clip(0.62 + 0.55 * (0.3 * nx + 0.2 * ny + 0.93 * nz) - 0.1, 0.3, 1.2)[..., None]
        turb = (0.9 + 0.12 * a[..., :1] * 0.5)
        body = base * diff * turb
        out = body * (1 - F) + sky(R) * F
        if foam > 0:
            fm = sstep(foam, foam + 1.1, a[..., 0] * 0.8 + b[..., 0] * 0.5)[..., None] * np.exp(-dist / 900.)[..., None]
            out = out + fm * 0.55 * np.array([0.8, 0.85, 0.9], f32)
        fg = (1 - np.exp(-dist * fogk))[..., None]
        out = out * (1 - fg) + np.array(fogc, f32) * fg
        return out.astype(f32)


# ---------------------------------------------------------------- rain / post
class RainFx:
    def __init__(s, seed=4, w=W, h=H):
        rng = np.random.default_rng(seed)
        s.w, s.h = w, h
        s.layers = []
        for (n, ln, wd, sp, br) in [(260, 70, 1, 2300, 0.20), (160, 130, 1, 3200, 0.28), (60, 220, 2, 4200, 0.30)]:
            img = np.zeros((h * 2, w), f32)
            for _ in range(n * 2):
                x = rng.integers(0, w); y = rng.integers(0, h * 2)
                cv2.line(img, (x, y), (int(x - ln * 0.08), int(y + ln)), float(rng.uniform(0.4, 1)), wd, cv2.LINE_AA)
            s.layers.append((img, sp, br))

    def apply(s, im, T, intensity=1.0, tint=(0.85, 0.9, 0.95)):
        acc = np.zeros((s.h, s.w), f32)
        for img, sp, br in s.layers:
            off = int(T * sp) % s.h
            acc += img[off:off + s.h] * br
        acc = cv2.GaussianBlur(acc, (0, 0), 0.7)
        return im + acc[..., None] * np.array(tint, f32) * intensity


def vignette(w=W, h=H, k=0.35):
    y, x = np.mgrid[0:h, 0:w].astype(f32)
    r = ((x - w / 2) / (w / 2)) ** 2 * 0.6 + ((y - h / 2) / (h / 2)) ** 2 * 0.5
    return (1 - k * r)[..., None].astype(f32)


_VIG = None


def grade(im, sat=0.82, contrast=1.08, lift=0.015, bloom=0.0, warm=(1.0, 1.0, 1.0), vig=0.32, exposure=1.0):
    global _VIG
    if _VIG is None or _VIG.shape[0] != im.shape[0]:
        _VIG = vignette(im.shape[1], im.shape[0], vig)
    im = im * exposure
    if bloom > 0:
        br = np.clip(im - 0.62, 0, 1)
        sm = cv2.GaussianBlur(br, (0, 0), 22)
        im = im + sm * bloom
    lum = (im * np.array([0.299, 0.587, 0.114], f32)).sum(-1, keepdims=True)
    im = lum + (im - lum) * sat
    im = np.clip(im, 0, 4)
    im = im / (1 + 0.18 * im)  # soft shoulder
    im = im * 1.18
    im = np.clip((im - 0.5) * contrast + 0.5, 0, 1)
    im = im * (1 - lift) + lift
    im = im * np.array(warm, f32)
    return np.clip(im * _VIG, 0, 1)


# ---------------------------------------------------------------- 3D boxes (painter's algorithm)
def _clip_near(poly, near=0.5):
    out = []
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        ina, inb = a[1] >= near, b[1] >= near
        if ina:
            out.append(a)
        if ina != inb:
            t = (near - a[1]) / (b[1] - a[1])
            out.append(a + (b - a) * t)
    return out


def _fill(canvas, cam, cpts, color, aa=True):
    """cpts: list of (xc,yc,zc) camera-space points."""
    if min(p[1] for p in cpts) < 0.5:
        cpts = _clip_near([np.array(p) for p in cpts])
        if len(cpts) < 3:
            return
    pts = np.array([[cam.w / 2 + cam.f * p[0] / p[1], cam.h / 2 - cam.f * p[2] / p[1]] for p in cpts])
    if pts[:, 0].max() < 0 or pts[:, 0].min() > cam.w or pts[:, 1].max() < 0 or pts[:, 1].min() > cam.h:
        return
    pts = np.clip(pts, -4000, 6000)
    cv2.fillConvexPoly(canvas, np.round(pts * 16).astype(np.int32), color, cv2.LINE_AA, 4)


def draw_boxes(canvas, cam, B, T=0.0, mirror=False, fog=(0.5, 0.52, 0.54), fogk=1 / 700., maxd=900.,
               light=(0.35, -0.25, 0.9), scale=1.0):
    """B: dict arrays cx,cy,w,d,h,r,g,b (colour 0..1), optional 'roof' (r,g,b). Canvas uint8 BGR? -> RGB here."""
    cx, cy, w, dd, h = B['cx'], B['cy'], B['w'], B['d'], B['h']
    campos = cam.pos
    dist = np.hypot(cx - campos[0], cy - campos[1])
    ok = np.nonzero(dist < maxd)[0]
    ok = ok[np.argsort(-dist[ok])]
    fogc = np.array(fog, f32)
    zs = -1.0 if mirror else 1.0
    kind = B.get('kind')
    for i in ok:
        if kind is not None and kind[i] == 1:
            _tree(canvas, cam, B, i, zs, dist[i], fogc, fogk, mirror)
            continue
        x0, x1 = cx[i] - w[i] / 2, cx[i] + w[i] / 2
        y0, y1 = cy[i] - dd[i] / 2, cy[i] + dd[i] / 2
        zb = float(B['z0'][i]) if 'z0' in B else 0.0
        z1 = zb + h[i] * zs
        base = np.array([B['r'][i], B['g'][i], B['b'][i]], f32)
        fg = 1 - np.exp(-dist[i] * fogk)
        V = {}
        def cv(x, y, z):
            key = (x, y, z)
            if key not in V:
                V[key] = (np.dot([x - campos[0], y - campos[1], z - campos[2]], cam.right),
                          np.dot([x - campos[0], y - campos[1], z - campos[2]], cam.fwd),
                          np.dot([x - campos[0], y - campos[1], z - campos[2]], cam.up))
            return V[key]
        faces = []
        # side faces: (normal xy test, corner list, shade)
        if campos[0] > x1: faces.append(((x1, y0), (x1, y1), 0.78))
        if campos[0] < x0: faces.append(((x0, y1), (x0, y0), 0.62))
        if campos[1] > y1: faces.append(((x1, y1), (x0, y1), 0.70))
        if campos[1] < y0: faces.append(((x0, y0), (x1, y0), 0.55))
        for (pa, pb, sh) in faces:
            q = [cv(pa[0], pa[1], zb), cv(pb[0], pb[1], zb), cv(pb[0], pb[1], z1), cv(pa[0], pa[1], z1)]
            c = base * sh * (0.85 if mirror else 1.0)
            c = c * (1 - fg) + fogc * fg
            _fill(canvas, cam, q, tuple(float(v) * 255 for v in c))
            if not mirror and dist[i] < 520 and z1 > 6 and 'z0' not in B:
                _windows(canvas, cam, cv, pa, pb, z1, base * sh, fog_c=fogc, fg=fg)
        if not mirror and campos[2] > z1:
            q = [cv(x0, y0, z1), cv(x1, y0, z1), cv(x1, y1, z1), cv(x0, y1, z1)]
            rc = np.array([B['rr'][i], B['rg'][i], B['rb'][i]], f32) if 'rr' in B else base * 1.1
            rc = rc * (1 - fg) + fogc * fg
            _fill(canvas, cam, q, tuple(float(v) * 255 for v in np.clip(rc, 0, 1)))


def _tree(canvas, cam, B, i, zs, dist, fogc, fogk, mirror):
    rel = np.array([B['cx'][i], B['cy'][i], B['h'][i] * zs]) - cam.pos
    xc, yc, zc = rel @ cam.right, rel @ cam.fwd, rel @ cam.up
    if yc < 1.0:
        return
    u, v = cam.w / 2 + cam.f * xc / yc, cam.h / 2 - cam.f * zc / yc
    rad = cam.f * B['w'][i] / 2 / yc
    if u + rad < 0 or u - rad > cam.w or v + rad < 0 or v - rad > cam.h or rad < 0.6:
        return
    fg = 1 - np.exp(-dist * fogk)
    base = np.array([B['r'][i], B['g'][i], B['b'][i]], f32)
    ext = 4 if canvas.shape[2] == 4 else 3
    def C(k):
        c = np.clip(base * k, 0, 1) * (1 - fg) + fogc * fg
        c = tuple(float(x) * 255 for x in c)
        return c + (255.0,) if ext == 4 else c
    b0 = rel * 0
    rel0 = np.array([B['cx'][i], B['cy'][i], 0.0]) - cam.pos
    xb, yb, zb = rel0 @ cam.right, rel0 @ cam.fwd, rel0 @ cam.up
    if yb > 1.0:
        ub, vb = cam.w / 2 + cam.f * xb / yb, cam.h / 2 - cam.f * zb / yb
        cv2.line(canvas, (int(ub), int(vb)), (int(u), int(v)), C(0.35), max(1, int(rad * 0.12)), cv2.LINE_AA)
    if rad < 7:
        cv2.circle(canvas, (int(u), int(v + rad * 0.1)), int(rad), C(0.55), -1, cv2.LINE_AA)
        cv2.circle(canvas, (int(u - rad * 0.2), int(v - rad * 0.2)), max(1, int(rad * 0.65)), C(1.0), -1, cv2.LINE_AA)
        return
    cv2.circle(canvas, (int(u), int(v + rad * 0.1)), int(rad * 0.95), C(0.42), -1, cv2.LINE_AA)
    rs = np.random.default_rng(int(B['cx'][i] * 131 + B['cy'][i] * 17) & 0xffffff)
    nb = 26
    ang = rs.uniform(0, 6.283, nb); rr = np.sqrt(rs.uniform(0, 1, nb)) * 0.72
    for k in range(nb):
        ox, oy = np.cos(ang[k]) * rr[k], np.sin(ang[k]) * rr[k]
        lit = np.clip(0.55 + 0.55 * (-ox * 0.6 - oy * 0.8) + rs.uniform(-0.15, 0.15), 0.35, 1.3)
        cv2.circle(canvas, (int(u + ox * rad), int(v + oy * rad)), max(1, int(rad * rs.uniform(0.13, 0.23))), C(lit), -1, cv2.LINE_AA)
    for k in range(14):
        ang2 = rs.uniform(0, 6.283); r2 = rs.uniform(0.15, 0.55)
        ox, oy = np.cos(ang2) * r2 - 0.12, np.sin(ang2) * r2 - 0.2
        cv2.circle(canvas, (int(u + ox * rad), int(v + oy * rad)), max(1, int(rad * 0.09)), C(rs.uniform(1.1, 1.45)), -1, cv2.LINE_AA)
