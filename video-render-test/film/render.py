"""Full film renderer: 6 scenes x 2 shots, 4K 9:16, overlays + grain, piped to ffmpeg."""
import sys, os, time, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from lib import W, H, FPS, f32

OW, OH = 2160, 3840
DUR = 150      # frames per shot
XF = 8         # crossfade frames
FONT_B = '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'
FONT_M = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'

_SH = None
_OV = None
_GR = None


def shots():
    global _SH
    if _SH is None:
        import space, city, farm, terrain, wildlife
        _SH = [space.earth_a, space.descent, city.shot_a, city.shot_b, farm.shot_a, farm.shot_b,
               terrain.shot_a, terrain.shot_b, wildlife.shot_a, wildlife.shot_b, space.ascent, space.earth_b]
    return _SH


def tracked(draw, xy, text, font, fill, tracking):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return x


def text_layer(lines, size, font_path, tracking, cx, y, line_gap=1.25, w=OW):
    font = ImageFont.truetype(font_path, size)
    tmp = ImageDraw.Draw(Image.new('L', (8, 8)))
    widths = [sum(tmp.textlength(c, font=font) + tracking for c in ln) - tracking for ln in lines]
    hh = int(size * line_gap * len(lines)) + 40
    mask = Image.new('L', (w, hh), 0)
    d = ImageDraw.Draw(mask)
    for k, ln in enumerate(lines):
        tracked(d, ((w - widths[k]) / 2 if cx is None else cx, 10 + k * size * line_gap), ln, font, 255, tracking)
    a = np.asarray(mask, f32) / 255.0
    sh = np.asarray(mask.filter(ImageFilter.GaussianBlur(size * 0.12)), f32) / 255.0
    return dict(y=y, a=a, sh=sh)


def overlays():
    global _OV
    if _OV is None:
        _OV = {}
        _OV['title'] = text_layer(["APA JADI JIKA", "SETIAP HARI HUJAN", "TURUN DI SELURUH DUNIA?"], 108, FONT_B, 8, None, 1420, 1.3)
        _OV['hyp'] = text_layer(["SENARIO HIPOTESIS"], 46, FONT_M, 12, 150, 560, 1.2)
        for n in (1, 7, 30, 60, 90):
            _OV[f'day{n}'] = text_layer([f"HARI {n}"], 118, FONT_M, 18, None, 2660, 1.2)
        _OV['final'] = text_layer(["Kitaran air: seimbang,", "bukan berlebihan."], 104, FONT_M, 3, None, 2640, 1.3)
    return _OV


def fade(g, a, b, f=14):
    if g < a or g > b:
        return 0.0
    return float(min(1.0, (g - a) / f, (b - g) / f))


TIMELINE = [('title', 15, 140, 1.0), ('hyp', 20, 1790, 0.55), ('day1', 160, 275, 1.0), ('day7', 365, 485, 1.0), ('day30', 665, 785, 1.0),
            ('day60', 965, 1085, 1.0), ('day90', 1265, 1385, 1.0), ('final', 1610, 1785, 1.0)]


def grain():
    global _GR
    if _GR is None:
        rng = np.random.default_rng(99)
        _GR = [np.clip(cv2.GaussianBlur(rng.standard_normal((OH // 2, OW // 2)).astype(f32), (0, 0), 0.5) * 3.2, -12, 12).astype(np.int8) for _ in range(6)]
    return _GR


def base_frame(g):
    k, i = divmod(g, DUR)
    S = shots()
    img = S[k](i)
    if k < 11 and i >= DUR - XF:
        a = (i - (DUR - XF) + 1) / (XF + 1)
        img = img * (1 - a) + S[k + 1](i - (DUR - XF)) * a
    return img


def make_frame(g):
    img = base_frame(g)
    u8 = np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)
    big = cv2.resize(u8, (OW, OH), interpolation=cv2.INTER_CUBIC)
    # film grain (half-res tile upscaled -> soft grain), different offset each frame
    gr = grain()[g % 6]
    gr = np.roll(gr, (g * 37) % (OH // 2), axis=0)
    gr = cv2.resize(gr, (OW, OH), interpolation=cv2.INTER_NEAREST)
    big = np.clip(big.astype(np.int16) + gr[..., None], 0, 255).astype(np.uint8)
    ov = overlays()
    for name, a, b, mx in TIMELINE:
        op = fade(g, a, b) * mx
        if op <= 0.003:
            continue
        L = ov[name]
        y0 = L['y']; hh = L['a'].shape[0]
        roi = big[y0:y0 + hh].astype(f32)
        roi = roi * (1 - L['sh'][..., None] * op * 0.55)
        roi = roi * (1 - L['a'][..., None] * op) + 245.0 * L['a'][..., None] * op
        big[y0:y0 + hh] = np.clip(roi, 0, 255).astype(np.uint8)
    # fade in/out
    f = min(1.0, g / 12.0, (1799 - g) / 15.0)
    if f < 1.0:
        big = (big.astype(f32) * max(f, 0)).astype(np.uint8)
    return g, big.tobytes()


def main():
    out = sys.argv[1]
    g0 = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    g1 = int(sys.argv[3]) if len(sys.argv) > 3 else 1800
    import multiprocessing as mp
    cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{OW}x{OH}', '-r', str(FPS), '-i', '-',
           '-c:v', 'libx264', '-preset', 'fast', '-crf', '15', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709',
           '-color_trc', 'bt709', '-movflags', '+faststart', out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    with mp.Pool(4) as pool:
        for n, (g, b) in enumerate(pool.imap(make_frame, range(g0, g1), chunksize=3)):
            p.stdin.write(b)
            if n % 20 == 0:
                el = time.time() - t0
                print(f'frame {g}/{g1}  {el:.0f}s  eta {el / (n + 1) * (g1 - g0 - n - 1):.0f}s', flush=True)
    p.stdin.close(); p.wait()
    print('done', time.time() - t0, flush=True)


if __name__ == '__main__':
    main()
