#!/usr/bin/env python3
"""
KAMAAR BEDDINGS - product price pop-ups + event end card.

Takes the presenter footage (1080x1920, 9:16), overlays three synchronized
price pop-ups (bounce-in, ~1.85 s each) and appends an animated event-details
end card ending with the KAMAAR BEDDINGS logo.

Usage:
    python3 render_kamaar_popups.py INPUT.mp4 OUTPUT.mp4 [--logo logo.png]
                                    [--preview-dir DIR]

Requires: ffmpeg, Pillow, numpy. Fonts: Inter (falls back to DejaVu Sans Bold).
"""
import argparse
import math
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
SS = 2  # supersampling factor for sprites

# --------------------------------------------------------------------------
# TIMELINE (seconds, in the source footage)
# Times come from the word-level highlight of the burned-in captions
# (cross-checked against the audio energy envelope, +/- 0.1 s): the pop-up
# starts on the word that carries the PRICE, not the product name.
#   Bantal ........ "harga hanya RM5"     RM5 spoken ~12.3 s
#   Kain reject ... "seringgit saja"      "seringgit" spoken ~21.15 s
#   Tilam Toto .... "dia RM29 saja"       RM29 spoken ~27.1 s
# --------------------------------------------------------------------------
POPUP_DURATION = 1.85  # total on-screen time incl. bounce-in and exit
POPUPS = [
    dict(name="BANTAL TIDUR", price="RM5.00", suffix=None, t_in=12.25),
    dict(name="KAIN REJECT KILANG", price="RM1.00", suffix="/ METER", t_in=21.10),
    dict(name="TILAM TOTO", price="RM29.00", suffix=None, t_in=27.05),
]
POPUP_CENTER_Y = 1385  # lower-middle: above the burned-in captions (~y1650)
END_CARD_SECONDS = 5.5

YELLOW = (255, 212, 0)
RED = (225, 20, 30)
NAVY = (9, 16, 44)
WHITE = (255, 255, 255)

FONT_DIR = Path("/usr/share/fonts/opentype/inter")
FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(weight, size):
    p = FONT_DIR / f"Inter-{weight}.otf"
    return ImageFont.truetype(str(p if p.exists() else FALLBACK), size)


# --------------------------------------------------------------------------
# sprite helpers
# --------------------------------------------------------------------------
def downscale(img):
    return img.resize((img.width // SS, img.height // SS), Image.LANCZOS)


def popup_sprite(name, price, suffix):
    """Rounded navy card: product name (white) above price (yellow, red outline)."""
    f_name = font("ExtraBold", 50 * SS)
    # shrink the price font until the content fits comfortably
    size = 118
    while True:
        f_price = font("Black", size * SS)
        f_suf = font("Black", int(size * 0.42) * SS)
        gap = 22 * SS
        pw = f_price.getlength(price)
        sw = f_suf.getlength(suffix) if suffix else 0
        price_w = pw + (gap + sw if suffix else 0)
        if price_w <= 600 * SS or size <= 90:
            break
        size -= 2
    name_w = f_name.getlength(name)
    pad_x = 56 * SS
    card_w = int(max(name_w, price_w) + 2 * pad_x)
    card_w = max(card_w, 560 * SS)
    card_h = 222 * SS
    m = 44 * SS  # margin for shadow
    sprite = Image.new("RGBA", (card_w + 2 * m, card_h + 2 * m), (0, 0, 0, 0))

    # soft shadow
    sh = Image.new("RGBA", sprite.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle(
        (m, m + 8 * SS, m + card_w, m + card_h + 8 * SS), 38 * SS, fill=(0, 0, 0, 150))
    sprite = Image.alpha_composite(sprite, sh.filter(ImageFilter.GaussianBlur(16 * SS)))

    d = ImageDraw.Draw(sprite)
    d.rounded_rectangle((m, m, m + card_w, m + card_h), 38 * SS,
                        fill=NAVY + (216,), outline=YELLOW + (255,), width=3 * SS)
    # small red accent tab on the top edge
    cx = m + card_w // 2
    d.rounded_rectangle((cx - 62 * SS, m - 5 * SS, cx + 62 * SS, m + 5 * SS),
                        5 * SS, fill=RED + (255,))

    base1 = m + 78 * SS
    d.text((cx, base1), name, font=f_name, fill=WHITE, anchor="ms")

    base2 = base1 + 26 * SS + int(size * 0.73) * SS
    stroke = 4 * SS
    x0 = cx - price_w / 2
    d.text((x0, base2), price, font=f_price, fill=YELLOW, anchor="ls",
           stroke_width=stroke, stroke_fill=RED)
    if suffix:
        d.text((x0 + pw + gap, base2), suffix, font=f_suf, fill=YELLOW, anchor="ls",
               stroke_width=int(stroke * 0.8), stroke_fill=RED)
    return downscale(sprite)


def text_sprite(text, weight, size, fill, stroke=0, stroke_fill=None, tracking=0, pad=24):
    """Single-line text with optional letter-spacing, supersampled."""
    f = font(weight, size * SS)
    chars = list(text)
    adv = [f.getlength(c) + tracking * SS for c in chars]
    width = int(sum(adv) - tracking * SS)
    asc, desc = f.getmetrics()
    img = Image.new("RGBA", (width + 2 * pad * SS, asc + desc + 2 * pad * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = pad * SS
    for c, a in zip(chars, adv):
        d.text((x, pad * SS + asc), c, font=f, fill=fill, anchor="ls",
               stroke_width=stroke * SS, stroke_fill=stroke_fill)
        x += a
    return downscale(img)


def pill_sprite(text, weight, size, text_fill, fill, outline=None, px=44, py=22, tracking=0):
    t = text_sprite(text, weight, size, text_fill, tracking=tracking, pad=2)
    w, h = t.width + 2 * px, t.height + 2 * py
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), (h // 2) * SS, fill=fill,
                        outline=outline, width=3 * SS if outline else 0)
    img = downscale(img)
    img.alpha_composite(t, (px, py))
    return img


def logo_sprite(logo_path):
    if logo_path and Path(logo_path).exists():
        lg = Image.open(logo_path).convert("RGBA")
        scale = min(620 / lg.width, 260 / lg.height)
        return lg.resize((int(lg.width * scale), int(lg.height * scale)), Image.LANCZOS)
    # typeset stand-in (thin, wide-tracked caps like the shirt logo)
    k = text_sprite("KAMAAR", "Light", 104, WHITE, tracking=26, pad=6)
    b = text_sprite("BEDDINGS", "Regular", 36, (214, 178, 96), tracking=30, pad=6)
    out = Image.new("RGBA", (max(k.width, b.width) + 20, k.height + b.height + 4), (0, 0, 0, 0))
    out.alpha_composite(k, ((out.width - k.width) // 2, 0))
    out.alpha_composite(b, ((out.width - b.width) // 2, k.height - 4))
    return out


# --------------------------------------------------------------------------
# animation curves
# --------------------------------------------------------------------------
def spring(t):
    """Damped spring 0 -> 1 with ~12 % overshoot (bounce-in)."""
    return 1.0 - math.exp(-9.0 * t) * math.cos(13.0 * t) if t > 0 else 0.0


def ease_out_cubic(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def popup_state(t):
    """t = seconds since pop-up start -> (scale, opacity) or None when off."""
    if t < 0 or t >= POPUP_DURATION:
        return None
    s = spring(t)
    a = min(1.0, t / 0.10)
    out_start = POPUP_DURATION - 0.18
    if t > out_start:
        k = (t - out_start) / 0.18
        s *= 1 - 0.12 * k
        a *= 1 - k
    return s, a


def paste(frame, sprite, cx, cy, scale=1.0, opacity=1.0, dy=0):
    if scale < 0.03 or opacity <= 0.003:
        return
    w, h = max(2, int(sprite.width * scale)), max(2, int(sprite.height * scale))
    sp = sprite if (w, h) == sprite.size else sprite.resize((w, h), Image.LANCZOS)
    alpha = sp.getchannel("A")
    if opacity < 1:
        alpha = alpha.point(lambda v: int(v * opacity))
    frame.paste(sp.convert("RGB"), (int(cx - w / 2), int(cy - h / 2 + dy)), alpha)


# --------------------------------------------------------------------------
# end card
# --------------------------------------------------------------------------
def build_end_card(last_frame, logo_path):
    bg = last_frame.filter(ImageFilter.GaussianBlur(26))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (14, 30, 84)), 0.78)
    # subtle vignette
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.30 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2) / 2
    bg = Image.fromarray((np.asarray(bg) * v[..., None]).astype(np.uint8))

    def fit(text, weight, size, fill, max_w=940, **kw):
        while True:
            s = text_sprite(text, weight, size, fill, **kw)
            if s.width <= max_w + 48 or size < 30:
                return s
            size -= 2

    els = []  # (sprite, center_y, start_time, kind)
    els.append((fit("7 & 8 NOVEMBER 2026", "Black", 92, YELLOW, stroke=4,
                    stroke_fill=RED, tracking=1), 430, 0.35, "slide"))
    els.append((fit("SABTU & AHAD", "ExtraBold", 74, WHITE, tracking=4), 575, 0.65, "slide"))
    els.append((pill_sprite("9 PAGI – 10 MALAM", "ExtraBold", 58, WHITE,
                            (255, 255, 255, 30), outline=YELLOW + (255,), tracking=3),
                715, 0.95, "slide"))
    div = Image.new("RGBA", (200, 8), (0, 0, 0, 0))
    ImageDraw.Draw(div).rounded_rectangle((0, 0, 199, 7), 4, fill=YELLOW + (255,))
    els.append((div, 835, 1.20, "slide"))
    els.append((fit("DEWAN SERBAGUNA", "ExtraBold", 66, WHITE, tracking=2), 925, 1.30, "slide"))
    els.append((fit("KAMPUNG TERSUSUN", "ExtraBold", 66, WHITE, tracking=2), 1010, 1.45, "slide"))
    els.append((fit("TAWAS TAMBAHAN, IPOH", "Bold", 54, YELLOW, tracking=3), 1115, 1.65, "slide"))
    els.append((pill_sprite("2 HARI SAHAJA!", "Black", 68, WHITE, RED + (255,),
                            px=64, py=26, tracking=2), 1255, 2.00, "pop"))
    logo = logo_sprite(logo_path)
    els.append((logo, 1450, 2.60, "fade"))

    def render(t):
        # background fades in over the last footage frame
        a = ease_out_cubic(t / 0.5)
        frame = Image.blend(last_frame, bg, a)
        for sp, cy, t0, kind in els:
            lt = t - t0
            if lt < 0:
                continue
            if kind == "slide":
                k = ease_out_cubic(lt / 0.5)
                paste(frame, sp, W / 2, cy, 1.0, k, dy=(1 - k) * 36)
            elif kind == "pop":
                s = spring(lt)
                pulse = 1 + 0.025 * math.sin((lt - 0.5) * 5.0) if lt > 0.5 else 1
                paste(frame, sp, W / 2, cy, s * pulse, min(1.0, lt / 0.12))
            else:
                k = ease_out_cubic(lt / 0.7)
                paste(frame, sp, W / 2, cy, 1.0, k, dy=(1 - k) * 20)
        return frame

    return render


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
         "default=nw=1:nk=1", path], capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--logo", help="optional official logo PNG (transparent background)")
    ap.add_argument("--preview-dir", help="also dump key frames as PNG here")
    args = ap.parse_args()

    # sanity: pop-ups must never overlap (previous one is removed first)
    for a, b in zip(POPUPS, POPUPS[1:]):
        assert a["t_in"] + POPUP_DURATION <= b["t_in"], "pop-ups overlap"

    sprites = [popup_sprite(p["name"], p["price"], p["suffix"]) for p in POPUPS]
    src_dur = probe_duration(args.input)
    video_tmp = str(Path(args.output).with_suffix(".video.mp4"))
    fbytes = W * H * 3

    dec = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", args.input, "-an", "-vf", f"fps={FPS}",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
         "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", video_tmp], stdin=subprocess.PIPE)

    preview_t = {12.1: "a_before_bantal", 12.5: "b_bantal", 13.4: "c_bantal_hold",
                 14.3: "d_removed", 21.4: "e_kain", 27.4: "f_toto"}
    preview_frames = {round(t * FPS): n for t, n in preview_t.items()}
    pdir = Path(args.preview_dir) if args.preview_dir else None
    if pdir:
        pdir.mkdir(parents=True, exist_ok=True)

    n = 0
    last = None
    while True:
        buf = dec.stdout.read(fbytes)
        if len(buf) < fbytes:
            break
        t = n / FPS
        arr = None
        for p, sp in zip(POPUPS, sprites):
            st = popup_state(t - p["t_in"])
            if st:
                if arr is None:
                    arr = Image.frombuffer("RGB", (W, H), buf, "raw", "RGB", 0, 1)
                paste(arr, sp, W / 2, POPUP_CENTER_Y, st[0], st[1])
                break
        if arr is not None:
            out = arr.tobytes()
        else:
            out = buf
        if pdir and n in preview_frames:
            Image.frombytes("RGB", (W, H), out).save(pdir / f"{preview_frames[n]}.png")
        enc.stdin.write(out)
        last = buf
        n += 1
    dec.wait()
    if last is None:
        sys.exit("no frames decoded")

    # end card
    last_img = Image.frombytes("RGB", (W, H), last)
    render = build_end_card(last_img, args.logo)
    total_end = int(END_CARD_SECONDS * FPS)
    end_prev = {int(1.0 * FPS): "g_end_1s", int(2.2 * FPS): "h_end_2s",
                int(total_end - 2): "i_end_final"}
    for i in range(total_end):
        fr = render(i / FPS)
        if pdir and i in end_prev:
            fr.save(pdir / f"{end_prev[i]}.png")
        enc.stdin.write(fr.tobytes())
    enc.stdin.close()
    enc.wait()

    total = (n + total_end) / FPS
    # mux original audio, fade it out at the end of the footage, pad with silence
    fade_st = max(0.0, n / FPS - 0.35)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", video_tmp, "-i", args.input,
         "-filter_complex",
         f"[1:a]afade=t=out:st={fade_st:.3f}:d=0.35,apad=whole_dur={total:.3f}[a]",
         "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
         "-t", f"{total:.3f}", "-movflags", "+faststart", args.output], check=True)
    Path(video_tmp).unlink()
    print(f"footage frames: {n} ({src_dur:.2f}s)  end card: {total_end} frames  total: {total:.2f}s")


if __name__ == "__main__":
    main()
