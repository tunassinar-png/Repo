"""Overlay kit for 'Apa Akan Jadi Jika Semua Wanita Dalam Dunia Ini Cantik?' (1920x1080, 30 fps, 60 s).
Outputs: overlay_alpha.webm, overlay_greenscreen.mp4, preview_silent.mp4, subtitles.srt. Usage: build_overlay.py OUTDIR"""
import os, sys, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from content import SCENES, LABEL_WIN, sub_cues, write_srt
import graphics as G

W, H, FPS = 1920, 1080, 30
f32 = np.float32
FB = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
FM = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'
AMBER = (255, 190, 60)
SS = 3


def premult(img):
    a = np.asarray(img, f32) / 255.0
    a[..., :3] *= a[..., 3:4]
    return a


def down(a, w, h):
    return cv2.resize(a, (w, h), interpolation=cv2.INTER_AREA)


def tw(font, text, track=0):
    d = ImageDraw.Draw(Image.new('L', (4, 4)))
    return sum(d.textlength(c, font=font) + track for c in text) - track if track else d.textlength(text, font=font)


def wrap(text, font, maxw):
    words = text.split(' '); lines = []; cur = ''
    for w_ in words:
        t = (cur + ' ' + w_).strip()
        if tw(font, t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur); cur = w_
    lines.append(cur)
    return lines


def subtitle(text):
    font = ImageFont.truetype(FM, 40 * SS)
    lines = wrap(text, font, 1500 * SS)
    if len(lines) == 2 and abs(tw(font, lines[0]) - tw(font, lines[1])) > 400 * SS:   # balance
        words = text.split(' '); best = None
        for i in range(1, len(words)):
            a, b = ' '.join(words[:i]), ' '.join(words[i:]); m = max(tw(font, a), tw(font, b))
            if best is None or m < best[0]:
                best = (m, [a, b])
        lines = best[1]
    ws = [tw(font, l) for l in lines]
    lh = int(40 * 1.35 * SS); padx, pady = 34 * SS, 16 * SS
    w = int(max(ws) + 2 * padx); h = lh * len(lines) + 2 * pady
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 22 * SS, fill=(0, 0, 0, 125))
    for k, l in enumerate(lines):
        d.text(((w - ws[k]) / 2, pady + k * lh - 2 * SS), l, font=font, fill=(255, 255, 255, 255))
    return down(premult(im), w // SS, h // SS)


def label(text):
    font = ImageFont.truetype(FB, 28 * SS); track = 5 * SS
    w_t = tw(font, text, track)
    padx, pady = 30 * SS, 18 * SS
    w = int(w_t + 2 * padx + 18 * SS); h = int(28 * 1.25 * SS + 2 * pady)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 18 * SS, fill=(0, 0, 0, 120))
    d.rounded_rectangle((0, 12 * SS, 7 * SS, h - 12 * SS), 3 * SS, fill=AMBER + (255,))
    x = padx + 10 * SS
    for c in text:
        d.text((x, pady - 2 * SS), c, font=font, fill=(255, 255, 255, 255)); x += d.textlength(c, font=font) + track
    return down(premult(im), w // SS, h // SS)


def big(text, size, color=(255, 255, 255), bold=True):
    font = ImageFont.truetype(FB if bold else FM, size * SS); track = 6 * SS
    w_t = tw(font, text, track); sh = 40 * SS
    w = int(w_t + 2 * sh); h = int(size * 1.3 * SS + 2 * sh)
    im = Image.new('L', (w, h), 0); d = ImageDraw.Draw(im)
    x = sh
    for c in text:
        d.text((x, sh), c, font=font, fill=255); x += d.textlength(c, font=font) + track
    a = np.asarray(im, f32) / 255.0
    shadow = cv2.GaussianBlur(a, (0, 0), size * SS * 0.08) * 0.8
    rgba = np.zeros((h, w, 4), f32)
    rgba[..., 3] = np.clip(a + shadow * (1 - a), 0, 1)
    col = np.array(color, f32) / 255.0
    rgba[..., :3] = (col * a[..., None])
    return down(rgba, w // SS, h // SS)


def over(canvas, layer, x, y, op=1.0):
    h, w = layer.shape[:2]
    x0, y0 = int(round(x)), int(round(y))
    X0, Y0, X1, Y1 = max(x0, 0), max(y0, 0), min(x0 + w, canvas.shape[1]), min(y0 + h, canvas.shape[0])
    if X1 <= X0 or Y1 <= Y0:
        return
    src = layer[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] * op
    canvas[Y0:Y1, X0:X1] = src + canvas[Y0:Y1, X0:X1] * (1 - src[..., 3:4])


def ease(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def fade(t, a, b, fi=0.35, fo=0.3):
    return float(ease((t - a) / fi) * ease((b - t) / fo)) if a <= t <= b else 0.0


def build():
    L = {'labels': [], 'subs': [], 'end': None, 'end2': None}
    for s, win in zip(SCENES[:5], LABEL_WIN):
        L['labels'].append((label(s['label']), win))
    for a, b, x in sub_cues():
        L['subs'].append((subtitle(x), a, b))
    L['end'] = big("APA PENDAPAT ANDA?", 112)
    L['end2'] = big("Tulis pendapat anda di ruang komen", 44, AMBER, bold=False)
    return L


def frame(L, t):
    fl = G.floaters(t)
    cv = fl.copy() if fl is not None else np.zeros((H, W, 4), f32)
    r = G.panel(t)
    if r is not None:
        over(cv, r[0], G.PX + r[2], G.PY, r[1])
    for lay, (a, b) in L['labels']:
        op = fade(t, a, b)
        if op > 0:
            over(cv, lay, 96, 78 + (1 - ease((t - a) / 0.4)) * 14, op)
    for lay, a, b in L['subs']:
        op = fade(t, a, b, 0.18, 0.18)
        if op > 0:
            over(cv, lay, (W - lay.shape[1]) / 2, H - 108 - lay.shape[0] + (1 - op) * 8, op)
    op = fade(t, 56.6, 59.95, 0.5, 0.2)
    if op > 0:
        sl = (1 - ease((t - 56.6) / 0.6)) * 24
        over(cv, L['end'], (W - L['end'].shape[1]) / 2, 330 + sl, op)
    op = fade(t, 57.6, 59.95, 0.5, 0.2)
    if op > 0:
        over(cv, L['end2'], (W - L['end2'].shape[1]) / 2, 330 + L['end'].shape[0] - 40, op)
    return cv


def bg_frame():
    yy, xx = np.mgrid[0:H, 0:W].astype(f32)
    g = 0.5 + 0.5 * (yy / H)
    img = np.stack([34 + 40 * g, 36 + 36 * g, 54 + 46 * g], -1) * (1 - 0.3 * (((xx - W / 2) / (W / 2)) ** 2))[..., None]
    return img.astype(f32)


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    write_srt(os.path.join(out, 'subtitles.srt'))
    L = build()
    if len(sys.argv) > 2:           # test: write PNG composites at given times
        bg = bg_frame()
        for ts in sys.argv[2:]:
            t = float(ts); cv_ = frame(L, t)
            im = cv_[..., :3] * 255 + (1 - cv_[..., 3:4]) * bg
            cv2.imwrite(os.path.join(out, f'test_{t:05.1f}.png'), cv2.cvtColor(np.clip(im, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
        return
    bg = bg_frame()
    cmds = [
        ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p',
         '-b:v', '0', '-crf', '24', '-auto-alt-ref', '0', '-row-mt', '1', '-deadline', 'good', '-cpu-used', '5', os.path.join(out, 'overlay_alpha.webm')],
        ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'fast', '-crf', '15', '-pix_fmt', 'yuv420p',
         os.path.join(out, 'overlay_greenscreen.mp4')],
        ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
         os.path.join(out, 'preview_silent.mp4')],
    ]
    ps = [subprocess.Popen(c, stdin=subprocess.PIPE) for c in cmds]
    green = np.array([0, 255, 0], f32)
    for g in range(60 * FPS):
        cv_ = frame(L, g / FPS)
        a = cv_[..., 3:4]
        rgb = np.where(a > 0.001, cv_[..., :3] / np.maximum(a, 1e-4), 0)
        ps[0].stdin.write(np.dstack([np.clip(rgb * 255 + .5, 0, 255), np.clip(a * 255 + .5, 0, 255)]).astype(np.uint8).tobytes())
        ps[1].stdin.write(np.clip(cv_[..., :3] * 255 + (1 - a) * green + .5, 0, 255).astype(np.uint8).tobytes())
        ps[2].stdin.write(np.clip(cv_[..., :3] * 255 + (1 - a) * bg + .5, 0, 255).astype(np.uint8).tobytes())
        if g % 300 == 0:
            print('frame', g, flush=True)
    for p in ps:
        p.stdin.close(); p.wait()
    print('done')


if __name__ == '__main__':
    main()
