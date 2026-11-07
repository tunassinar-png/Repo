"""Add animated pop-up text to a video. Usage: add_popups.py in.mp4 out.mp4
Edit POPS below: (text, start_s, end_s)."""
import sys, subprocess, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

POPS = [("Pagi-pagi makan lasagna", 0.30, 1.85),
        ("Sambil bagi ayam makan,", 2.30, 3.85),
        ("Jangan tanya aku kat mana", 4.30, 5.85),
        ("Tak cari duit macam mana nak makan!", 6.30, 9.55)]
FONT = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
BLUE = (31, 63, 191)
f32 = np.float32


def plate(text, W, size=58):
    SS = 3
    font = ImageFont.truetype(FONT, size * SS)
    tmp = ImageDraw.Draw(Image.new('L', (4, 4)))
    maxw = (W - 120) * SS
    words = text.split(' ')
    lines = [text]
    if tmp.textlength(text, font=font) + 90 * SS > maxw:
        best = None
        for i in range(1, len(words)):
            a, b = ' '.join(words[:i]), ' '.join(words[i:])
            w = max(tmp.textlength(a, font=font), tmp.textlength(b, font=font))
            if best is None or w < best[0]:
                best = (w, [a, b])
        lines = best[1]
    ws = [tmp.textlength(l, font=font) for l in lines]
    lh = int(size * 1.2 * SS)
    padx, pady = 46 * SS, 26 * SS
    w = int(max(ws) + 2 * padx); h = lh * len(lines) + 2 * pady
    sh = 14 * SS
    im = Image.new('RGBA', (w + 2 * sh, h + 2 * sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((sh, sh + 6 * SS, sh + w, sh + h + 6 * SS), 30 * SS, fill=(0, 0, 0, 90))
    d.rounded_rectangle((sh, sh, sh + w, sh + h), 30 * SS, fill=BLUE + (240,))
    d.rounded_rectangle((sh + 22 * SS, sh + h - 10 * SS, sh + w - 22 * SS, sh + h - 4 * SS), 3 * SS, fill=(255, 190, 40, 255))
    for k, l in enumerate(lines):
        d.text((sh + (w - ws[k]) / 2, sh + pady + k * lh - 4 * SS), l, font=font, fill=(255, 255, 255, 255))
    a = np.asarray(im, f32) / 255.0
    a[..., :3] *= a[..., 3:4]
    return cv2.resize(a, (a.shape[1] // SS, a.shape[0] // SS), interpolation=cv2.INTER_AREA)


def pop_scale(t):
    # overshoot spring in, quick shrink out
    if t < 0.28:
        x = t / 0.28
        return 0.55 + 0.6 * x - 0.15 * np.sin(np.pi * x) * 0 + 0.0 if x < 0.7 else 1.12 - 0.12 * ((x - 0.7) / 0.3)
    return 1.0


def main():
    src, dst = sys.argv[1], sys.argv[2]
    pr = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate,nb_frames', '-of', 'json', src]))['streams'][0]
    W, H = pr['width'], pr['height']
    num, den = map(int, pr['r_frame_rate'].split('/')); fps = num / den
    rd = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    wr = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-', '-i', src,
                           '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-c:a', 'copy', '-shortest', '-movflags', '+faststart', dst],
                          stdin=subprocess.PIPE)
    layers = [plate(t, W) for t, _, _ in POPS]
    cy = int(H * 0.875)
    n = 0
    fsz = W * H * 3
    while True:
        buf = rd.stdout.read(fsz)
        if len(buf) < fsz:
            break
        fr = np.frombuffer(buf, np.uint8).reshape(H, W, 3).astype(f32)
        t = n / fps
        for (txt, a, b), lay in zip(POPS, layers):
            if a <= t <= b:
                lt = t - a
                if lt < 0.30:
                    x = lt / 0.30
                    s = 0.5 + 0.62 * (1 - (1 - x) ** 3) if x < 0.75 else 1.12 - 0.12 * ((x - 0.75) / 0.25)
                    op = min(1.0, lt / 0.12)
                else:
                    s = 1.0
                    op = 1.0
                out = (b - t)
                if out < 0.18:
                    s *= 0.9 + 0.1 * (out / 0.18); op = out / 0.18
                h0, w0 = lay.shape[:2]
                sw, sh = max(2, int(w0 * s)), max(2, int(h0 * s))
                L = cv2.resize(lay, (sw, sh), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)
                x0, y0 = (W - sw) // 2, cy - sh // 2 - int((1 - op) * 18)
                X0, Y0, X1, Y1 = max(x0, 0), max(y0, 0), min(x0 + sw, W), min(y0 + sh, H)
                src_ = L[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0] * op
                roi = fr[Y0:Y1, X0:X1]
                fr[Y0:Y1, X0:X1] = src_[..., :3] * 255 + roi * (1 - src_[..., 3:4])
        wr.stdin.write(np.clip(fr + .5, 0, 255).astype(np.uint8).tobytes())
        n += 1
    wr.stdin.close(); wr.wait(); rd.wait()
    print('frames', n)


if __name__ == '__main__':
    main()
