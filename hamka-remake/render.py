import sys, os, subprocess, math, argparse
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from common import *

ap = argparse.ArgumentParser()
ap.add_argument('--src', required=True)
ap.add_argument('--out', required=True)
ap.add_argument('--fonts', required=True)
ap.add_argument('--only', default='')          # comma separated frame numbers -> PNG previews
ap.add_argument('--preview-dir', default='')
ap.add_argument('--frames', type=int, default=1122)
a = ap.parse_args()

SW, SH = 1024, 576
W, H = 1920, 1080
BASE = 1920 / 1024.0
TOTAL = a.frames
ONLY = sorted(int(x) for x in a.only.split(',') if x)

# ------------------------------------------------------------------ fonts
def F(name, size):
    return ImageFont.truetype(os.path.join(a.fonts, name), size)
CINZEL = lambda w, s: F(f'cinzel-latin-{w}-normal.woff', s)
CORM_IT = lambda w, s: F(f'cormorant-garamond-latin-{w}-italic.woff', s)

GOLD_STOPS = [(255, 238, 190), (226, 184, 104), (176, 128, 58)]   # RGB top -> bottom
IVORY = (246, 238, 220)

def spaced_width(font, text, track):
    return sum(font.getlength(c) for c in text) + track * (len(text) - 1)

def draw_spaced(draw, xy, text, font, track, fill=255):
    x, y = xy
    for c in text:
        draw.text((x, y), c, font=font, fill=fill)
        x += font.getlength(c) + track

def gradient_rgba(mask_img, stops, y0, y1):
    """Fill an 'L' mask with a vertical multi-stop gradient -> RGBA PIL image"""
    w, h = mask_img.size
    col = np.zeros((h, w, 3), np.float32)
    ys = np.clip((np.arange(h) - y0) / max(1, (y1 - y0)), 0, 1)
    n = len(stops) - 1
    for i in range(h):
        t = ys[i] * n
        k = min(int(t), n - 1)
        f = t - k
        c = [stops[k][j] * (1 - f) + stops[k + 1][j] * f for j in range(3)]
        col[i, :, :] = c
    rgba = np.dstack([col, np.asarray(mask_img, np.float32)])
    return rgba  # float32 RGBA 0..255

def render_text_layer(text, kind, canvas_w, canvas_h, size, track=0, weight=600, gradient=True, glow=True):
    """Return (premultiplied BGRA float32 0..1, text_width_px). Text centred in canvas."""
    if kind == 'cinzel':
        font = CINZEL(weight, size); T = text.upper()
        tw = spaced_width(font, T, track)
    else:
        font = CORM_IT(weight, size); T = text
        tw = font.getlength(T)
    asc, desc = font.getmetrics()
    mask = Image.new('L', (canvas_w, canvas_h), 0)
    d = ImageDraw.Draw(mask)
    x = (canvas_w - tw) / 2
    y = canvas_h / 2 - (asc + desc) / 2 + (size * 0.02)
    if kind == 'cinzel': draw_spaced(d, (x, y), T, font, track)
    else: d.text((x, y), T, font=font, fill=255)
    m = np.asarray(mask, np.float32) / 255.0
    # colour
    if gradient:
        top = y + asc * 0.30; bot = y + asc * 1.02
        col = gradient_rgba(mask, GOLD_STOPS, top, bot)[..., :3]
    else:
        col = np.empty((canvas_h, canvas_w, 3), np.float32); col[:] = IVORY
    col = col / 255.0
    # drop shadow (soft) + glow
    sh = cv2.GaussianBlur(m, (0, 0), max(2.0, size * 0.045))
    sh = np.roll(sh, int(max(2, size * 0.04)), axis=0)
    out_a = np.clip(m + sh * 0.55, 0, 1)
    rgb = (col * m[..., None])            # premultiplied colour of the text itself
    if glow:
        g = cv2.GaussianBlur(m, (0, 0), size * 0.18)
        gc = np.array(GOLD_STOPS[1], np.float32)[None, None, :] / 255.0
        rgb = rgb + g[..., None] * gc * 0.28
        out_a = np.clip(out_a + g * 0.15, 0, 1)
    bgra = np.dstack([rgb[..., 2], rgb[..., 1], rgb[..., 0], out_a]).astype(np.float32)
    return bgra, tw

def shift_layer(layer, dy):
    M = np.float32([[1, 0, 0], [0, 1, dy]])
    return cv2.warpAffine(layer, M, (layer.shape[1], layer.shape[0]), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=0)

def over(roi, layer, alpha):
    """roi BGR float [0..1] (h,w,3); layer premultiplied BGRA same size"""
    a_ = layer[..., 3:4] * alpha
    roi[:] = roi * (1 - a_) + layer[..., :3] * alpha
    return roi

def smooth(t):
    t = min(1.0, max(0.0, t)); return t * t * (3 - 2 * t)

# ------------------------------------------------------------------ pill (frosted glass plate)
def pill_masks(w, h):
    pad = 6
    m = np.zeros((h + pad * 2, w + pad * 2), np.uint8)
    r = h // 2
    cv2.rectangle(m, (pad + r, pad), (pad + w - r, pad + h), 255, -1, cv2.LINE_AA)
    cv2.circle(m, (pad + r, pad + r), r, 255, -1, cv2.LINE_AA)
    cv2.circle(m, (pad + w - r, pad + r), r, 255, -1, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 0.8).astype(np.float32) / 255.0
    inner = cv2.erode((m > 0.5).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    ring = np.clip(m - cv2.GaussianBlur(inner.astype(np.float32), (0, 0), 0.8), 0, 1)
    return m, ring

GOLD_BGR = np.array([98, 175, 212], np.float32) / 255.0
def draw_pill(img, cx, cy, w, h, alpha):
    if alpha <= 0.003: return
    w = int(w); h = int(h)
    m, ring = pill_masks(w, h)
    pad = 6
    x0 = int(round(cx - w / 2)) - pad; y0 = int(round(cy - h / 2)) - pad
    x1 = x0 + m.shape[1]; y1 = y0 + m.shape[0]
    cx0, cy0 = max(0, x0), max(0, y0); cx1, cy1 = min(W, x1), min(H, y1)
    if cx1 <= cx0 or cy1 <= cy0: return
    sl = (slice(cy0 - y0, cy1 - y0), slice(cx0 - x0, cx1 - x0))
    mm = m[sl][..., None]; rr = ring[sl][..., None]
    roi = img[cy0:cy1, cx0:cx1]
    # blur a padded region so the blur does not darken at the edge
    by0, by1, bx0, bx1 = max(0, cy0 - 30), min(H, cy1 + 30), max(0, cx0 - 30), min(W, cx1 + 30)
    bl = cv2.GaussianBlur(img[by0:by1, bx0:bx1], (0, 0), 13)[cy0 - by0:cy1 - by0, cx0 - bx0:cx1 - bx0]
    lum = bl.mean(axis=2, keepdims=True)
    glass = bl * (0.60 - 0.40 * lum) + np.array([0.030, 0.026, 0.022], np.float32) * 0.9
    k = mm * alpha
    roi[:] = roi * (1 - k) + glass * k
    roi[:] = roi * (1 - rr * alpha * 0.55) + GOLD_BGR * rr * alpha * 0.55

# ------------------------------------------------------------------ static overlays
def make_frame_overlay():
    ov = np.zeros((H, W, 4), np.float32)    # BGRA straight alpha
    col = (98 / 255, 175 / 255, 212 / 255)
    def rect(inset, t, a_):
        layer = np.zeros((H, W), np.uint8)
        cv2.rectangle(layer, (inset, inset), (W - 1 - inset, H - 1 - inset), 255, t, cv2.LINE_AA)
        return layer.astype(np.float32) / 255 * a_
    A = np.maximum(rect(34, 1, 0.55), rect(46, 1, 0.22))
    # corner brackets
    br = np.zeros((H, W), np.uint8); L = 74; i0 = 34
    for (sx, sy, dx, dy) in [(i0, i0, 1, 1), (W - 1 - i0, i0, -1, 1), (i0, H - 1 - i0, 1, -1), (W - 1 - i0, H - 1 - i0, -1, -1)]:
        cv2.line(br, (sx, sy), (sx + dx * L, sy), 255, 3, cv2.LINE_AA)
        cv2.line(br, (sx, sy), (sx, sy + dy * L), 255, 3, cv2.LINE_AA)
    A = np.maximum(A, br.astype(np.float32) / 255 * 0.85)
    for c in range(3): ov[..., c] = col[c]
    ov[..., 3] = A
    return ov
FRAME_OV = make_frame_overlay()

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r2 = ((xx - W / 2) / (W / 2)) ** 2 * 0.85 + ((yy - H / 2) / (H / 2)) ** 2
VIG = (1.0 - 0.55 * np.clip(r2 - 0.25, 0, 1) ** 1.2)[..., None].astype(np.float32)

# ------------------------------------------------------------------ grade
def grade(frame_u8, warm=1.0):
    x = frame_u8.astype(np.float32) / 255.0                      # BGR
    luma = (0.114 * x[..., 0] + 0.587 * x[..., 1] + 0.299 * x[..., 2])
    sh = ((1 - luma) ** 2)[..., None]; hi = (luma ** 2)[..., None]
    x = x * 1.12 + 0.020
    x[..., 0:1] += 0.018 * sh * warm          # gentle blue lift in shadows
    x[..., 1:2] += 0.010 * sh * warm
    x[..., 2:3] *= (1 + 0.07 * hi * warm)      # warm highlights
    x[..., 0:1] *= (1 - 0.08 * hi * warm)
    x = np.clip(x, 0, 1)
    x = x * 0.6 + (x * x * (3 - 2 * x)) * 0.4                    # gentle S-curve
    g = (0.114 * x[..., 0] + 0.587 * x[..., 1] + 0.299 * x[..., 2])[..., None]
    x = g + (x - g) * 1.10                                        # saturation
    # bloom
    br = np.clip(x - 0.60, 0, 1)
    small = cv2.resize(br, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), 9)
    bloom = cv2.resize(small, (W, H), interpolation=cv2.INTER_LINEAR)
    x = x + bloom * np.array([0.30, 0.46, 0.60], np.float32)     # warm (BGR) glow
    return np.clip(x, 0, 1)

def sharpen(u8):
    bl = cv2.GaussianBlur(u8, (0, 0), 1.3)
    return cv2.addWeighted(u8, 1.55, bl, -0.55, 0)

rng = np.random.default_rng(7)
def grain(x, n):
    r = np.random.default_rng(1000 + n)
    g = r.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    g = cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR)
    lum = x.mean(axis=2, keepdims=True)
    amp = 0.030 * (1.0 - 0.5 * lum)
    return x + g[..., None] * amp

# ------------------------------------------------------------------ captions
ATT_TEXT = 'BUYA HAMKA'
def render_attr():
    ch = 110
    lay, tw = render_text_layer(ATT_TEXT, 'cinzel', W, ch, 30, track=11, weight=500, gradient=True, glow=False)
    # side ornaments: thin gold lines with diamond end
    gold = np.array([98, 175, 212], np.float32) / 255
    lines = np.zeros((ch, W), np.float32)
    cy = ch // 2 + 1
    for sgn in (-1, 1):
        x_in = int(W / 2 + sgn * (tw / 2 + 28)); x_out = int(W / 2 + sgn * (tw / 2 + 28 + 96))
        cv2.line(lines, (x_in, cy), (x_out, cy), 1.0, 1, cv2.LINE_AA)
        d = np.array([[x_out, cy - 4], [x_out + sgn * 5, cy], [x_out, cy + 4], [x_out - sgn * 5, cy]], np.int32)
        cv2.fillConvexPoly(lines, d, 1.0, cv2.LINE_AA)
    lay[..., :3] += lines[..., None] * gold * 0.85
    lay[..., 3] = np.clip(lay[..., 3] + lines * 0.9, 0, 1)
    return lay, tw
ATT_LAYER, ATT_W = render_attr()

CAP_CACHE = {}
def caption_layer(i):
    if i in CAP_CACHE: return CAP_CACHE[i]
    s0, s1, text, kind, x1 = SEGS[i]
    ch = 240
    if kind == 'q':
        size = 66; track = 7
        while True:
            f = CINZEL(600, size)
            if spaced_width(f, text.upper(), track) <= 1500 or size <= 40: break
            size -= 2; track = max(3, int(size * 0.105))
        lay, tw = render_text_layer(text, 'cinzel', W, ch, size, track=track, weight=600)
    else:
        size = 104
        while CORM_IT(600, size).getlength(text) > 1300 and size > 60: size -= 4
        lay, tw = render_text_layer(text, 'corm', W, ch, size, weight=600, gradient=False)
    CAP_CACHE[i] = (lay, tw)
    return CAP_CACHE[i]

def seg_index_at(n):
    for i, s in enumerate(SEGS):
        if s[0] - 2 <= n < s[1] + 2: return i
    return None

def cap_alpha(n, s):
    a_in = smooth((n - (s[0] - 2)) / 7.0)
    a_out = 1 - smooth((n - (s[1] - 5)) / 7.0)
    return min(a_in, a_out)

# ------------------------------------------------------------------ title card (end)
def build_title_layers():
    L = []
    def full(text, kind, size, track, weight, cy, grad=True, glow=True):
        ch = 400
        lay, tw = render_text_layer(text, kind, W, ch, size, track=track, weight=weight, gradient=grad, glow=glow)
        big = np.zeros((H, W, 4), np.float32)
        y0 = int(cy - ch / 2)
        big[y0:y0 + ch] = lay
        return big
    L.append((full('Hamka', 'cinzel', 238, 34, 700, 392), 8))
    L.append((full('Awal Mula Vol. 3', 'cinzel', 46, 24, 500, 528, grad=False, glow=False), 24))
    # ornament
    orn = np.zeros((H, W), np.float32)
    cy = 598
    cv2.line(orn, (W // 2 - 330, cy), (W // 2 - 26, cy), 1.0, 2, cv2.LINE_AA)
    cv2.line(orn, (W // 2 + 26, cy), (W // 2 + 330, cy), 1.0, 2, cv2.LINE_AA)
    d = np.array([[W // 2, cy - 11], [W // 2 + 11, cy], [W // 2, cy + 11], [W // 2 - 11, cy]], np.int32)
    cv2.fillConvexPoly(orn, d, 1.0, cv2.LINE_AA)
    gold = np.array([98, 175, 212], np.float32) / 255
    ol = np.dstack([orn[..., None] * gold, orn]).astype(np.float32)
    L.append((ol, 32))
    L.append((full('19 November 2026', 'cinzel', 80, 15, 600, 700), 42))
    L.append((full('Di Bioskop', 'cinzel', 38, 34, 500, 790, grad=False, glow=False), 58))
    return L
TITLE_LAYERS = None

def title_particles(n, t0):
    """small drifting gold bokeh dots, additive"""
    r = np.random.default_rng(42)
    N = 34
    px = r.uniform(0, W, N); py = r.uniform(0, H, N); sp = r.uniform(6, 22, N); rad = r.uniform(3, 9, N)
    ph = r.uniform(0, 6.28, N); br = r.uniform(0.35, 1.0, N)
    t = (n - t0) / 30.0
    cv_ = np.zeros((H // 2, W // 2), np.float32)
    for i in range(N):
        x = (px[i] + 14 * math.sin(t * 0.8 + ph[i])) / 2
        y = ((py[i] - sp[i] * t * 4) % H) / 2
        tw = 0.6 + 0.4 * math.sin(t * 2.0 + ph[i])
        cv2.circle(cv_, (int(x), int(y)), int(rad[i] / 2) + 1, float(br[i] * tw), -1, cv2.LINE_AA)
    cv_ = cv2.GaussianBlur(cv_, (0, 0), 2.4)
    return cv2.resize(cv_, (W, H), interpolation=cv2.INTER_LINEAR)

# ------------------------------------------------------------------ main loop
cmd_in = ['ffmpeg', '-v', 'error', '-i', a.src, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-']
dec = subprocess.Popen(cmd_in, stdout=subprocess.PIPE)
enc = None
if not ONLY:
    cmd_out = ['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
               '-i', a.src, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17',
               '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-c:a', 'copy', '-t', f'{TOTAL / 30:.3f}', '-movflags', '+faststart', a.out]
    enc = subprocess.Popen(cmd_out, stdin=subprocess.PIPE)

prev_small = None; shot_start = 0; shot_idx = 0
held_bg = None
title_t0 = TITLE_START
last_n = (ONLY[-1] if ONLY else TOTAL - 1)

def kb_params(n):
    """Ken-Burns zoom / pan for current shot"""
    p = min(1.0, (n - shot_start) / 90.0)
    z0, z1 = (1.15, 1.27) if shot_idx % 2 == 0 else (1.27, 1.15)
    z = z0 + (z1 - z0) * p
    dirx = 1 if (shot_idx % 3 != 1) else -1
    panx = dirx * (-14 + 28 * p)
    pany = (-6 + 12 * p) * (1 if shot_idx % 2 == 0 else -1)
    return z, panx, pany

def warp(srcimg, z, panx, pany):
    s = BASE * z
    cx = SW / 2 + panx; cy = SH / 2 + pany
    M = np.float32([[s, 0, W / 2 - s * cx], [0, s, H / 2 - s * cy]])
    return cv2.warpAffine(srcimg, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE), s, cx, cy

for n in range(0, last_n + 1):
    raw = dec.stdout.read(SW * SH * 3)
    if len(raw) < SW * SH * 3: break
    src = np.frombuffer(raw, np.uint8).reshape(SH, SW, 3).copy()
    small = cv2.resize(cv2.cvtColor(src, cv2.COLOR_BGR2GRAY), (64, 36), interpolation=cv2.INTER_AREA).astype(np.float32)
    if prev_small is not None and n < TITLE_START:
        if np.abs(small - prev_small).mean() > 20: shot_start = n; shot_idx += 1
    prev_small = small
    if n == 1004:
        held_bg = cv2.GaussianBlur(clean_frame(src, n), (0, 0), 20)
    if ONLY and n not in ONLY:
        continue

    if n < TITLE_START:
        base = clean_frame(src, n)
        z, panx, pany = kb_params(n)
        big, s, cx, cy = warp(base, z, panx, pany)
        big = sharpen(big)
        x = grade(big)
        # --- caption plates
        ycx = W / 2 - s * (cx - SW / 2)
        y_main = H / 2 + s * (292 - cy)
        y_att = H / 2 + s * (373 - cy)
        si = seg_index_at(n)
        if si is not None:
            sg = SEGS[si]; al = cap_alpha(n, sg)
            lay, tw = caption_layer(si)
            orig_w = 2 * (sg[4] + 12 - SW / 2) * s
            pw = min(W - 140, max(orig_w + 64, tw + 170))
            ph = 178
            draw_pill(x, ycx, y_main, pw, ph, al * 0.97)
            ty = 1 - smooth((n - (sg[0] - 2)) / 9.0)
            L = shift_layer(lay, 12 * ty)
            y0 = int(round(y_main - lay.shape[0] / 2)); y1 = y0 + lay.shape[0]
            roi = x[y0:y1]
            over(roi, L, al)
        if n <= ATTR_END + 2:
            aal = smooth((n - 6) / 10.0) * (1 - smooth((n - (ATTR_END - 8)) / 8.0))
            if aal > 0:
                draw_pill(x, ycx, y_att, (ATT_W + 2 * 129 + 70), 98, aal * 0.92)
                y0 = int(round(y_att - ATT_LAYER.shape[0] / 2)); y1 = y0 + ATT_LAYER.shape[0]
                over(x[y0:y1], ATT_LAYER, aal)
        held_src = None
    else:
        # ---------- title card: blurred golden bokeh of the film's own title frame + new typography
        k = n - TITLE_START
        if n <= 1004:
            bg = cv2.GaussianBlur(clean_frame(src, n), (0, 0), 20)
        else:
            bg = held_bg
        z = 1.20 + 0.06 * min(1.0, k / 90.0)
        big, s, cx, cy = warp(bg, z, 0, 0)
        x = grade(big, warm=1.2) * 0.92
        x = x + title_particles(n, title_t0)[..., None] * np.array([0.10, 0.22, 0.34], np.float32)
        if TITLE_LAYERS is None: TITLE_LAYERS = build_title_layers()
        for (lay, st) in TITLE_LAYERS:
            al = smooth((k - st) / 14.0)
            if al <= 0: continue
            L = shift_layer(lay, 18 * (1 - al))
            ys = np.where(L[..., 3].max(axis=1) > 0.002)[0]
            if len(ys) == 0: continue
            y0, y1 = max(0, ys[0] - 2), min(H, ys[-1] + 3)
            over(x[y0:y1], L[y0:y1], al)

    # ------------- finishing (all shots)
    x = x * VIG
    flick = 1.0 + 0.012 * math.sin(n * 0.7) + 0.006 * math.sin(n * 2.3)
    x = x * flick
    fa = FRAME_OV[..., 3:4] * smooth(min(1.0, n / 20.0))
    x = x * (1 - fa) + FRAME_OV[..., :3] * fa
    x = grain(x, n)
    if n < 9: x *= smooth(n / 9.0)
    if n > TOTAL - 14: x *= 1 - smooth((n - (TOTAL - 14)) / 13.0)
    out = np.clip(x * 255 + 0.5, 0, 255).astype(np.uint8)
    if ONLY:
        os.makedirs(a.preview_dir, exist_ok=True)
        cv2.imwrite(os.path.join(a.preview_dir, f'p_{n:04d}.png'), out)
    else:
        enc.stdin.write(out.tobytes())
        if n % 100 == 0: print('frame', n, flush=True)

dec.kill()
if enc:
    enc.stdin.close(); enc.wait()
    print('done', a.out)
