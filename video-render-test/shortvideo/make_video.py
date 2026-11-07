"""10 s vertical (1080x1920) photo video with slow camera moves and beat-synced cuts.
Usage: make_video.py out_silent.mp4 img1 img2 img3 img4 img5"""
import sys, subprocess
import numpy as np, cv2
from PIL import Image, ImageOps

W, H, FPS, N = 1080, 1920, 30, 300
CLIP = 60          # frames per photo (= 1 bar at 120 BPM)
XF = 7             # crossfade frames
# per photo: base centre x (fraction), focal point (fx, fy), zoom range
CFG = [dict(cx=.62, f=(.58, .22), z=(1.00, 1.14)),
       dict(cx=.45, f=(.47, .16), z=(1.02, 1.16)),
       dict(cx=.55, f=(.70, .24), z=(1.14, 1.00)),
       dict(cx=.40, f=(.42, .22), z=(1.00, 1.13)),
       dict(cx=.50, f=(.49, .27), z=(1.12, 1.00))]


def load(p):
    im = ImageOps.exif_transpose(Image.open(p)).convert('RGB')
    return np.asarray(im, np.float32) / 255.0


def kb(img, cfg, t):
    h, w = img.shape[:2]
    e = t * t * (3 - 2 * t)
    z = cfg['z'][0] + (cfg['z'][1] - cfg['z'][0]) * e
    cw = h * 9 / 16 / z; ch = h / z
    cx = cfg['cx'] * w
    fx, fy = cfg['f'][0] * w, cfg['f'][1] * h
    pull = (z - 1.0) * 1.6
    cx = cx + (fx - cx) * min(pull, 0.8)
    cy = h / 2 + (fy - h / 2) * min(pull, 0.8) * (ch < h)
    x0 = float(np.clip(cx - cw / 2, 0, w - cw)); y0 = float(np.clip(cy - ch / 2, 0, h - ch))
    sx, sy = W / cw, H / ch
    M = np.array([[sx, 0, -x0 * sx], [0, sy, -y0 * sy]], np.float32)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def vignette():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = ((x - W / 2) / (W / 2)) ** 2 * 0.55 + ((y - H / 2) / (H / 2)) ** 2 * 0.45
    return (1 - 0.28 * r)[..., None]


def main():
    out = sys.argv[1]
    imgs = [load(p) for p in sys.argv[2:7]]
    vig = vignette()
    p = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'slow', '-crf', '14', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709',
                          '-color_trc', 'bt709', out], stdin=subprocess.PIPE)
    rng = np.random.default_rng(1)
    for f in range(N):
        k = min(f // CLIP, 4); loc = f - k * CLIP
        a = kb(imgs[k], CFG[k], loc / CLIP)
        if k < 4 and loc >= CLIP - XF:
            m = (loc - (CLIP - XF) + 1) / (XF + 1)
            b = kb(imgs[k + 1], CFG[k + 1], 0.0)
            a = a * (1 - m) + b * m
        # gentle grade: contrast, warmth, vignette, beat pulse on each downbeat
        a = np.clip((a - 0.5) * 1.07 + 0.5, 0, 1)
        a = a * np.array([1.02, 1.0, 0.98], np.float32)
        pulse = 0.06 * np.exp(-((f % CLIP) / 5.0))
        a = a * vig * (1 + pulse)
        a = a + rng.standard_normal((H, W, 1)).astype(np.float32) * 0.008
        if f > N - 12:
            a = a * (N - 1 - f) / 11.0
        p.stdin.write(np.clip(a * 255 + .5, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()


if __name__ == '__main__':
    main()
