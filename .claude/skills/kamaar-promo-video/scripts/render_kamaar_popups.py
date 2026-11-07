#!/usr/bin/env python3
"""
KAMAAR BEDDINGS - promo video renderer (9:16).

Takes presenter footage (1080x1920) and adds: one bounce-in price pop-up per spoken
price, a dramatic intro (hook, big date/time/location banners, "2 HARI SAHAJA!" slam),
a minimal persistent date + location label, and an animated event end card ending with
the KAMAAR BEDDINGS logo. All content/timings are constants at the top of this file.

Usage:
    python3 -B -I render_kamaar_popups.py INPUT.mp4 OUTPUT.mp4 [--width 1440]
        [--logo logo.png] [--vo vo.mp3] [--preview-dir DIR]
    --width 1080 (default) = Full HD, 1440 = 2K (1440x2560). See ../SKILL.md.

Requires: ffmpeg, Pillow, numpy. Fonts: Inter (falls back to DejaVu Sans Bold).
"""
import argparse
import math
import random
import runpy
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
# Everything is laid out in 1080x1920 "design units". K scales the whole render to
# the output size (K = 4/3 -> 1440x2560, "2K"); sprites are built natively at K.
K = 1.0
OW, OH = W, H


def set_output_width(width):
    global K, OW, OH
    K = width / W
    OW, OH = int(round(W * K)) // 2 * 2, int(round(H * K)) // 2 * 2
SS = 2  # supersampling factor for sprites

YELLOW = (255, 212, 0)
RED = (225, 20, 30)
NAVY = (9, 16, 44)
WHITE = (255, 255, 255)

# --------------------------------------------------------------------------
# TIMELINE (seconds, in the source footage)
# Times come from the word-level highlight of the burned-in captions
# (cross-checked against the audio energy envelope, +/- 0.1 s). A pop-up
# starts 0.05 s before the word that carries the PRICE is spoken, so the
# bounce-in lands on the word. One pop-up per price mention in the VO.
#   12.30  "bantal macam ni, harga hanya RM5"
#   15.85  "kalau hangpa ambil 6 biji bantal macam ni, ni hanya RM29"
#   18.75  "kain reject kilang, 1m, seringgit"
#   21.15  "tak kira nipis tak, kira tebal 1m, seringgit saja"
#   24.30  "abang akak sarung bantal ni 4 helai, RM10"
#   27.10  "Tilam Toto ni harga, dia RM29 saja"
#   29.60  "Tilam single RM39"
#   34.40  "bantal peluk harga paling murah RM15"
#   30.50  "ambil RM tiga seratus" = 3 for RM100 -> same Tilam Single card, the
#          price swaps in place (no second pop-up, so nothing overlaps)
# --------------------------------------------------------------------------
POPUP_DURATION = 1.85  # total on-screen time incl. bounce-in and exit
POPUPS = [
    dict(name="BANTAL TIDUR", price="RM5.00", suffix=None, t_in=12.25),
    dict(name="6 BIJI BANTAL", price="RM29.00", suffix=None, t_in=15.80),
    dict(name="KAIN REJECT KILANG", price="RM1.00", suffix="/ METER", t_in=18.70),
    dict(name="KAIN REJECT KILANG", price="RM1.00", suffix="/ METER", t_in=21.10),
    dict(name=[("SARUNG BANTAL ", 1.0, "W"), ("4", 2.3, "Y"), (" HELAI", 1.0, "W")],
         price="RM10.00", suffix=None, t_in=24.25),
    dict(name="TILAM TOTO", price="RM29.00", suffix=None, t_in=27.05),
    dict(name="TILAM SINGLE", price="RM39.00", suffix=None, t_in=29.55, dur=2.65,
         then=dict(t=30.50, name=[("TILAM SINGLE  ", 1.0, "W"), ("3 BIJI", 2.0, "Y")],
                   price="RM100", suffix=None,
                   opts=dict(price_size=150, max_name_w=840, min_w=700))),
    dict(name="BANTAL PELUK", price="RM15.00", suffix=None, t_in=34.35),
]
# Intro: big date / time / location banners, revealed line by line as the
# presenter says "Pada 7 dan 8 November, Sabtu dan Ahad, kami akan berada di
# Dewan Serba Guna, Kampung Tersusun, Tawas Tambahan, Ipoh, 2 hari saja".
# Placed in the empty wall/ceiling area (y 160-640), above the presenter.
INTRO_TOP = 160
INTRO_OUT = 10.90   # all banners leave before "bantal macam ni" (11.0 s)
# (tag, banner t_in, height, [(text, weight, size, style, centre_y, t_line)])
# styles: "outline" = yellow text, red outline; "plain" = white text;
#         "plain_y" = yellow text; "pill_w" / "pill_y" = pills sharing one row
INTRO = [
    ("TARIKH & MASA", 4.00, 214, [
        ("7 & 8 NOVEMBER 2026", "Black", 76, "outline", 70, 4.00),
        ("SABTU & AHAD", "ExtraBold", 38, "pill_w", 156, 5.95),
        ("9 PAGI – 10 MALAM", "Black", 38, "pill_y", 156, 6.55)]),
    ("LOKASI", 7.45, 246, [
        ("DEWAN SERBAGUNA", "ExtraBold", 58, "plain", 70, 7.45),
        ("KAMPUNG TERSUSUN", "ExtraBold", 58, "plain", 136, 8.45),
        ("TAWAS TAMBAHAN, IPOH", "Black", 52, "outline", 204, 9.20)]),
]
# "Hook": VO says "Kepada warga Kampung Tawas, Ipoh dan kawasan sekitar" (1.0 - 3.8 s).
# kind: chip = red pill, slam = huge impact text, sub = small line
HOOK_OUT = 3.60
HOOK = [
    dict(kind="chip", text="KEPADA WARGA", t=1.00, cy=300),
    dict(kind="slam", text="KAMPUNG TAWAS", size=104, fill=YELLOW, stroke=7,
         glow=YELLOW, t=1.72, cy=420),
    dict(kind="slam", text="IPOH", size=210, fill=WHITE, stroke=9,
         glow=RED, t=2.47, cy=602),
    dict(kind="sub", text="& KAWASAN SEKITAR", t=3.00, cy=716),
]
BADGE = dict(text="2 HARI SAHAJA!", t=10.00, cx=840, cy=692, angle=-5)  # VO "2 hari saja"
# Impact events: screen flash, camera shake (px) and spark burst (cx, cy, n)
EVENTS = [
    dict(t=0.00, flash=0.60, shake=10),
    dict(t=1.72, flash=0.85, shake=32, punch=0.10, chroma=10, ring=True, lines=True,
         burst=(540, 420, 170)),
    dict(t=2.10, flash=0.35, shake=14, punch=0.04, burst=(720, 420, 60)),   # "Tawas" beat
    dict(t=2.47, flash=0.95, shake=42, punch=0.13, chroma=14, ring=True, lines=True,
         burst=(540, 595, 220)),
    dict(t=3.00, flash=0.25, shake=8),
    dict(t=4.00, flash=0.40, shake=10, punch=0.03, burst=(540, 267, 70)),
    dict(t=6.55, flash=0.30, shake=8, burst=(760, 316, 50)),
    dict(t=7.45, flash=0.40, shake=12, punch=0.03, burst=(540, 509, 70)),
    dict(t=10.00, flash=0.80, shake=34, punch=0.10, chroma=10, ring=True, lines=True,
         burst=(840, 692, 150)),
]
RAYS = [(1.72, 3.85)]    # (start, end) windows of the rotating light rays
SCRIM = [(0.9, 11.0)]    # windows of the dark top gradient behind intro text
SCRIM_STRENGTH = 0.55
PREVIEW_T = None         # {seconds: name} frames dumped with --preview-dir (None = defaults)
# Persistent minimal label: date + location, small, top-centre. Hidden while the
# big intro banners (same info) are on screen, and replaced by the end card.
LABEL_LINES = [("7 & 8 NOV 2026", "ExtraBold", 36, "Y"),
               ("DEWAN SERBAGUNA KAMPUNG TERSUSUN, TAWAS TAMBAHAN, IPOH", "Bold", 24, "W")]
LABEL_CY = 205
LABEL_SHOW = [(0.3, 3.85), (11.0, 46.9)]
POPUP_CENTER_Y = 1385  # lower-middle: above the burned-in captions (~y1650)
END_CARD_SECONDS = 5.5


FONT_DIR = Path("/usr/share/fonts/opentype/inter")
FALLBACK = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(weight, size):
    p = FONT_DIR / f"Inter-{weight}.otf"
    return ImageFont.truetype(str(p if p.exists() else FALLBACK), size)


# --------------------------------------------------------------------------
# sprite helpers
# --------------------------------------------------------------------------
def downscale(img):
    """Sprites are drawn at SS px per design unit -> resize to K px per unit."""
    return img.resize((max(1, round(img.width * K / SS)), max(1, round(img.height * K / SS))),
                      Image.LANCZOS)


def lu(sprite):
    """Sprite width in design units."""
    return sprite.width / K


def popup_sprite(name, price, suffix, min_w=560, price_size=118, max_name_w=640):
    """Rounded navy card: product name (white) above price (yellow, red outline).

    `name` is a string or a list of (text, size_factor, "W"|"Y") parts drawn on one
    baseline, so a number can be made much bigger than the words around it.
    """
    parts = [(name, 1.0, "W")] if isinstance(name, str) else list(name)
    colors = {"W": WHITE, "Y": YELLOW}
    nsize = 50
    while True:  # shrink the name line until it fits
        fonts = [font("ExtraBold" if c == "W" else "Black", int(nsize * f * SS))
                 for _, f, c in parts]
        name_w = sum(fn.getlength(t) for (t, _, _), fn in zip(parts, fonts))
        if name_w <= max_name_w * SS or nsize <= 30:
            break
        nsize -= 2
    name_cap = int(nsize * max(f for _, f, _ in parts) * 0.73)
    # shrink the price font until the content fits comfortably
    size = price_size
    while True:
        f_price = font("Black", size * SS)
        f_suf = font("Black", int(size * 0.42) * SS)
        gap = 22 * SS
        pw = f_price.getlength(price)
        sw = f_suf.getlength(suffix) if suffix else 0
        price_w = pw + (gap + sw if suffix else 0)
        if price_w <= max(600, price_size * 4.4) * SS or size <= 90:
            break
        size -= 2
    price_cap = int(size * 0.73)
    pad_x = 56 * SS
    card_w = int(max(name_w, price_w) + 2 * pad_x)
    card_w = max(card_w, min_w * SS)
    base1_off = 42 + name_cap                  # baseline of the name line (1x px)
    base2_off = base1_off + 26 + price_cap     # baseline of the price line
    card_h = (base2_off + 32) * SS
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

    base1 = m + base1_off * SS
    x = cx - name_w / 2
    for (text, f, c), fn in zip(parts, fonts):
        kw = dict(stroke_width=4 * SS, stroke_fill=RED) if c == "Y" else {}
        d.text((x, base1), text, font=fn, fill=colors[c], anchor="ls", **kw)
        x += fn.getlength(text)

    base2 = m + base2_off * SS
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
    pxk, pyk = round(px * K), round(py * K)
    w, h = t.width + 2 * pxk, t.height + 2 * pyk
    img = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), (h // 2) * SS, fill=fill,
                        outline=outline, width=round(3 * K * SS) if outline else 0)
    img = img.resize((w, h), Image.LANCZOS)
    img.alpha_composite(t, (pxk, pyk))
    return img


def logo_sprite(logo_path):
    if logo_path and Path(logo_path).exists():
        lg = Image.open(logo_path).convert("RGBA")
        scale = min(620 * K / lg.width, 260 * K / lg.height)
        return lg.resize((int(lg.width * scale), int(lg.height * scale)), Image.LANCZOS)
    # typeset stand-in (thin, wide-tracked caps like the shirt logo)
    k = text_sprite("KAMAAR", "Light", 104, WHITE, tracking=26, pad=6)
    b = text_sprite("BEDDINGS", "Regular", 36, (214, 178, 96), tracking=30, pad=6)
    out = Image.new("RGBA", (max(k.width, b.width) + round(20 * K), k.height + b.height + round(4 * K)),
                    (0, 0, 0, 0))
    out.alpha_composite(k, ((out.width - k.width) // 2, 0))
    out.alpha_composite(b, ((out.width - b.width) // 2, k.height - round(4 * K)))
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


def popup_state(t, dur=POPUP_DURATION):
    """t = seconds since pop-up start -> (scale, opacity) or None when off."""
    if t < 0 or t >= dur:
        return None
    s = spring(t)
    a = min(1.0, t / 0.10)
    out_start = dur - 0.18
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
    frame.paste(sp.convert("RGB"), (int(cx * K - w / 2), int((cy + dy) * K - h / 2)), alpha)


# --------------------------------------------------------------------------
# persistent date / location label
# --------------------------------------------------------------------------
def build_label():
    colors = {"Y": YELLOW, "W": WHITE}
    parts = []
    for text, weight, size, col in LABEL_LINES:
        while True:
            sp = text_sprite(text, weight, size, colors[col], stroke=3,
                             stroke_fill=(0, 0, 0, 255), tracking=1, pad=8)
            if lu(sp) <= 1000 or size < 16:
                break
            size -= 1
        parts.append(sp)
    gap = -round(6 * K)
    w = max(p.width for p in parts)
    h = sum(p.height for p in parts) + gap * (len(parts) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for sp in parts:
        out.alpha_composite(sp, ((w - sp.width) // 2, y))
        y += sp.height + gap
    # soft dark shadow for legibility on bright backgrounds
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    a = out.getchannel("A").filter(ImageFilter.GaussianBlur(5 * K)).point(lambda v: int(v * 0.6))
    sh.putalpha(a)
    return Image.alpha_composite(sh, out)


def label_alpha(t):
    best = 0.0
    for start, end in LABEL_SHOW:
        best = max(best, min(1.0, max(0.0, (t - start) / 0.3)) *
                   min(1.0, max(0.0, (end - t) / 0.3)))
    return best


# --------------------------------------------------------------------------
# intro banners
# --------------------------------------------------------------------------
BANNER_W = 1000
BANNER_GAP = 12
BANNER_M = 44  # shadow margin (1x px)


def banner_bg(h):
    w, m = BANNER_W * SS, BANNER_M * SS
    hh = h * SS
    sprite = Image.new("RGBA", (w + 2 * m, hh + 2 * m), (0, 0, 0, 0))
    sh = Image.new("RGBA", sprite.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((m, m + 8 * SS, m + w, m + hh + 8 * SS),
                                         34 * SS, fill=(0, 0, 0, 150))
    sprite = Image.alpha_composite(sprite, sh.filter(ImageFilter.GaussianBlur(16 * SS)))
    ImageDraw.Draw(sprite).rounded_rectangle((m, m, m + w, m + hh), 34 * SS,
                                             fill=NAVY + (222,), outline=YELLOW + (255,),
                                             width=3 * SS)
    return downscale(sprite)


def build_intro():
    """-> list of banners: dict(bg, cy, t_in, t_out, lines=[(sprite, rel_y, t_line, dx, t_end)])

    INTRO entries are (tag, t_in, h, lines) tuples stacked from INTRO_TOP, or dicts with
    keys tag, t_in, h, lines and optional y (top, design units) and t_out.
    A line is (text, weight, size, style, centre_y, t_line[, t_end]).
    """
    banners, y = [], INTRO_TOP
    for entry in INTRO:
        if isinstance(entry, dict):
            tag, t_in, h, lines = entry["tag"], entry["t_in"], entry["h"], entry["lines"]
            top, t_out = entry.get("y", y), entry.get("t_out", INTRO_OUT)
        else:
            (tag, t_in, h, lines), top, t_out = entry, y, INTRO_OUT
        bg = banner_bg(h)
        if tag:
            chip = pill_sprite(tag, "Black", 24, WHITE, RED + (255,), px=22, py=8, tracking=3)
            bg.alpha_composite(chip, (round((BANNER_M + 34) * K), round(BANNER_M * K) - chip.height // 2))
        ls = []
        for ln in lines:
            text, weight, size, style, cy, t_line = ln[:6]
            t_end = ln[6] if len(ln) > 6 else None
            if style == "pill_w":
                sp = pill_sprite(text, weight, size, WHITE, (255, 255, 255, 30),
                                 outline=YELLOW + (255,), px=26, py=14, tracking=0)
            elif style == "pill_y":
                sp = pill_sprite(text, weight, size, NAVY, YELLOW + (255,),
                                 px=26, py=14, tracking=0)
            else:
                kw = dict(stroke=4, stroke_fill=RED) if style == "outline" else {}
                col = WHITE if style == "plain" else YELLOW
                while True:
                    sp = text_sprite(text, weight, size, col, tracking=1, **kw)
                    if lu(sp) <= BANNER_W - 80 + 48 or size < 30:
                        break
                    size -= 2
            ls.append([sp, cy, t_line, 0, style, t_end])
        # pills that share a row are centred as a group
        pills = [l for l in ls if l[4].startswith("pill")]
        if pills:
            gap = round(28 * K)
            total = sum(l[0].width for l in pills) + gap * (len(pills) - 1)
            x = -total / 2
            for l in pills:
                l[3] = int(x + l[0].width / 2)
                x += l[0].width + gap
        banners.append(dict(bg=bg, cy=top + h / 2, h=h, t_in=t_in, t_out=t_out,
                            lines=[(l[0], l[1], l[2], l[3], l[5]) for l in ls]))
        y = top + h + BANNER_GAP
    return banners


def intro_layers(banners, t):
    """-> [(sprite, cx, cy, scale, opacity)] for the banners visible at time t."""
    out = []
    for b in banners:
        lt, t_out = t - b["t_in"], b["t_out"]
        if lt < 0 or t >= t_out:
            continue
        scale = 0.86 + 0.14 * spring(lt)     # gentle bounce, never wider than the frame
        alpha = min(1.0, lt / 0.12)
        if t > t_out - 0.2:
            k = (t - (t_out - 0.2)) / 0.2
            scale *= 1 - 0.08 * k
            alpha *= 1 - k
        sp = b["bg"].copy()
        top = round(BANNER_M * K)
        for lsp, rel_y, t_line, dx, t_end in b["lines"]:
            k = ease_out_cubic((t - t_line) / 0.30)
            if t_end is not None and t > t_end - 0.15:
                k *= max(0.0, (t_end - t) / 0.15)
            if k <= 0:
                continue
            layer = lsp
            if k < 1:
                layer = lsp.copy()
                layer.putalpha(lsp.getchannel("A").point(lambda v, k=k: int(v * k)))
            sp.alpha_composite(layer, (sp.width // 2 - layer.width // 2 + dx,
                                       int(top + (rel_y + (1 - k) * 14) * K - layer.height / 2)))
        out.append((sp, W / 2, b["cy"], scale, alpha))
    return out


# --------------------------------------------------------------------------
# intro FX: hook text, flash, shake, sparks, rays, scrim
# --------------------------------------------------------------------------
SPARK_COLORS = [YELLOW, WHITE, RED, (255, 160, 0), (255, 235, 150)]
SCRIM_H = 950
OVERLAY_H = 1300


def with_glow(sp, color, radius=22, strength=0.9):
    """Soft coloured glow sprite (same centre as sp, bigger canvas)."""
    radius = radius * K
    pad = int(radius * 3)
    a = Image.new("L", (sp.width + 2 * pad, sp.height + 2 * pad), 0)
    a.paste(sp.getchannel("A"), (pad, pad))
    a = a.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: min(255, int(v * 1.9 * strength)))
    g = Image.new("RGBA", a.size, color + (0,))
    g.putalpha(a)
    return g


def shine(sp, pos):
    """White diagonal highlight band sweeping over the text (pos -0.2 .. 1.2)."""
    arr = np.asarray(sp).astype(np.float32)
    h, w = arr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    u = (xx + 0.35 * yy) / (w + 0.35 * h)
    band = np.exp(-(((u - pos) / 0.07) ** 2))[..., None] * 0.9
    arr[..., :3] += (255 - arr[..., :3]) * band
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def paste_rot(frame, sprite, cx, cy, scale, opacity, angle):
    paste(frame, sprite.rotate(angle, resample=Image.BICUBIC, expand=True), cx, cy, scale, opacity)


def build_rays(color=(255, 220, 70), step=20, width=9):
    n = 1500
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = n / 2
    for i in range(360 // step):
        a0 = math.radians(i * step)
        a1 = math.radians(i * step + width)
        d.polygon([(c, c), (c + c * 1.5 * math.cos(a0), c + c * 1.5 * math.sin(a0)),
                   (c + c * 1.5 * math.cos(a1), c + c * 1.5 * math.sin(a1))],
                  fill=color + (255,))
    yy, xx = np.mgrid[0:n, 0:n]
    rad = np.clip(1 - np.hypot(xx - c, yy - c) / c, 0, 1) ** 1.2
    a = np.asarray(img.getchannel("A")).astype(np.float32) * rad
    img.putalpha(Image.fromarray(a.astype(np.uint8)))
    return img


def build_hook(logo_path=None):
    """Text pops from HOOK: kind chip | sub (slide up) or slam | pill | logo (impact slam)."""
    items = []
    for h in HOOK:
        kind = h["kind"]
        if kind == "chip":
            sp, glow = pill_sprite(h["text"], "Black", 34, WHITE, RED + (255,),
                                   px=36, py=14, tracking=5), None
        elif kind == "sub":
            sp, glow = text_sprite(h["text"], "ExtraBold", 42, WHITE, stroke=3,
                                   stroke_fill=(0, 0, 0, 255), tracking=6), None
        elif kind == "pill":
            sp = pill_sprite(h["text"], "Black", h.get("size", 56), WHITE, RED + (255,),
                             px=44, py=20, tracking=2)
            glow = with_glow(sp, RED, radius=20)
        elif kind == "logo":
            sp = logo_sprite(logo_path)
            glow = with_glow(sp, WHITE, radius=20, strength=0.6)
        else:
            size = h["size"]
            sf = h.get("stroke_fill") or (RED + (255,) if h["fill"] != RED else NAVY + (255,))
            while True:
                sp = text_sprite(h["text"], "Black", size, h["fill"], stroke=h["stroke"],
                                 stroke_fill=sf, tracking=1)
                if lu(sp) <= 1000 or size < 40:
                    break
                size -= 2
            glow = with_glow(sp, h["glow"], radius=26, strength=1.15)
        items.append((h, sp, glow))
    badge = bglow = None
    if BADGE:
        badge = pill_sprite(BADGE["text"], "Black", 46, WHITE, RED + (255,), px=38, py=16, tracking=2)
        bglow = with_glow(badge, RED, radius=18)
    return dict(items=items, badge=(badge, bglow), rays=build_rays(),
                rays2=build_rays((255, 70, 50), step=30, width=12))


def slam_state(lt):
    """Huge -> normal scale, wobble and settle. -> (scale, opacity, angle_deg)."""
    if lt < 0:
        return None
    if lt < 0.14:
        s = 1.0 + 2.0 * (1 - ease_out_cubic(lt / 0.14))
    else:
        s = 1.0 + 0.10 * math.exp(-(lt - 0.14) * 10) * math.sin((lt - 0.14) * 40)
    ang = 5.0 * math.exp(-lt * 10) * math.sin(lt * 45)
    if lt > 0.45:  # heartbeat while the text holds
        s *= 1 + 0.022 * math.sin((lt - 0.45) * 15)
    return s, min(1.0, lt / 0.04), ang


def hook_exit(t, t_out=None):
    t_out = HOOK_OUT if t_out is None else t_out
    if t <= t_out:
        return 1.0, 1.0
    k = min(1.0, (t - t_out) / 0.25)
    return 1 + 0.3 * k, 1 - k


def shake_frame(img, t):
    """Camera shake + punch zoom + RGB split on impact events."""
    dx = dy = amp = punch = chroma = 0.0
    for ev in EVENTS:
        lt = t - ev["t"]
        if lt < 0:
            continue
        if ev.get("shake") and lt < 0.6:
            a = ev["shake"] * math.exp(-lt * 7)
            dx += a * math.sin(lt * 66)
            dy += a * math.cos(lt * 53 + 1)
            amp += a
        if ev.get("punch") and lt < 0.5:
            punch += ev["punch"] * math.exp(-lt * 9)
        if ev.get("chroma") and lt < 0.3:
            chroma = max(chroma, ev["chroma"] * math.exp(-lt * 12))
    if amp >= 0.5 or punch >= 0.003:
        z = 1 + punch + 0.0021 * amp  # zoom margin always >= the shake offset
        img = img.transform((OW, OH), Image.AFFINE,
                            (1 / z, 0, OW / 2 * (1 - 1 / z) + dx * K, 0, 1 / z, OH / 2 * (1 - 1 / z) + dy * K),
                            resample=Image.BICUBIC)
    if chroma >= 1:
        sh = max(1, int(chroma * K))
        arr = np.array(img.convert("RGB"))
        arr[..., 0] = np.roll(arr[..., 0], sh, axis=1)
        arr[..., 2] = np.roll(arr[..., 2], -sh, axis=1)
        img = Image.fromarray(arr)
    return img


def scrim_frame(img, t):
    a = 0.0
    for t0, t1 in SCRIM:
        a = max(a, min(1.0, max(0.0, (t - t0) / 0.4)) * min(1.0, max(0.0, (t1 - t) / 0.4)))
    a *= SCRIM_STRENGTH
    if a < 0.005:
        return img
    n = int(SCRIM_H * K)
    grad = ((1 - np.arange(n) / n) ** 1.4)[:, None, None]
    arr = np.array(img)
    arr[:n] = (arr[:n] * (1 - a * grad)).astype(np.uint8)
    return Image.fromarray(arr)


def flash_alpha(t):
    a = 0.0
    for ev in EVENTS:
        lt = t - ev["t"]
        if 0 <= lt < 0.35:
            a = max(a, ev["flash"] * math.exp(-lt / 0.07))
    return a


def spark_layer(t):
    """Sparks (dots + streaks), double shock ring and radial speed lines."""
    ov, d = None, None
    for ev in EVENTS:
        if "burst" not in ev:
            continue
        lt = t - ev["t"]
        if lt < 0 or lt > 1.1:
            continue
        if ov is None:
            ov = Image.new("RGBA", (W, OVERLAY_H), (0, 0, 0, 0))
            d = ImageDraw.Draw(ov)
        cx, cy, n = ev["burst"]
        rng = random.Random(int(ev["t"] * 1000))
        life = 1.0
        if ev.get("lines") and lt < 0.30:  # radial speed lines
            kk = lt / 0.30
            r_in = 140 + 520 * ease_out_cubic(kk)
            for _ in range(80):
                ang = rng.uniform(0, 2 * math.pi)
                length = rng.uniform(260, 700)
                dth = rng.uniform(0.006, 0.014)
                pts = [(cx + r_in * math.cos(ang), cy + r_in * math.sin(ang)),
                       (cx + (r_in + length) * math.cos(ang - dth), cy + (r_in + length) * math.sin(ang - dth)),
                       (cx + (r_in + length) * math.cos(ang + dth), cy + (r_in + length) * math.sin(ang + dth))]
                d.polygon(pts, fill=(255, 255, 255, int(230 * (1 - kk))))
        if ev.get("ring"):
            for delay, col, wmax, rmax in ((0.0, (255, 235, 140), 14, 430), (0.08, (255, 90, 60), 9, 340)):
                ll = lt - delay
                if 0 <= ll < 0.5:
                    kk = ll / 0.5
                    rad = 50 + rmax * ease_out_cubic(kk)
                    d.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), outline=col + (int(220 * (1 - kk)),),
                              width=max(1, int(wmax * (1 - kk))))
        for _ in range(n):
            ang = rng.uniform(0, 2 * math.pi)
            v = rng.uniform(300, 1400)
            r0 = rng.uniform(7, 17)
            col = rng.choice(SPARK_COLORS)
            kind = rng.random()
            spin = rng.uniform(-9, 9)
            if lt > life:
                continue

            def pos(tt):
                dist = v * (1 - math.exp(-tt * 3.2)) / 3.2
                return (cx + math.cos(ang) * dist, cy + math.sin(ang) * dist + 0.5 * 520 * tt * tt)

            x, y = pos(lt)
            k = 1 - lt / life
            r = r0 * k ** 0.6
            if r < 0.8:
                continue
            fill = col + (int(255 * min(1.0, k * 1.6)),)
            if kind < 0.45:      # streak with a tail
                x0, y0 = pos(max(0.0, lt - 0.05))
                d.line((x0, y0, x, y), fill=fill, width=max(2, int(r * 0.9)))
            elif kind < 0.75:    # spinning diamond
                th = spin * lt
                pts = [(x + rr * math.cos(th + q), y + rr * math.sin(th + q))
                       for q, rr in ((0, 1.8 * r), (math.pi / 2, 0.8 * r),
                                     (math.pi, 1.8 * r), (3 * math.pi / 2, 0.8 * r))]
                d.polygon(pts, fill=fill)
            else:
                d.ellipse((x - r, y - r, x + r, y + r), fill=fill)
    return ov


def fx_base(img, t, hook):
    """Shake / punch zoom / RGB split, scrim, light rays, flash and sparks (under the overlays)."""
    img = shake_frame(img, t)
    img = scrim_frame(img, t)
    for a, b in RAYS:  # two counter-rotating light-ray layers
        if a <= t <= b:
            ra = min(1.0, (t - a) / 0.25) * min(1.0, (b - t) / 0.25)
            paste(img, hook["rays"].rotate(-(t - a) * 40, resample=Image.BILINEAR), W / 2, 500, K, ra * 0.38)
            paste(img, hook["rays2"].rotate((t - a) * 28, resample=Image.BILINEAR), W / 2, 500, K, ra * 0.22)
    fa = flash_alpha(t)
    if fa > 0.01:
        img = Image.blend(img.convert("RGB"), Image.new("RGB", img.size, (255, 246, 215)), min(fa, 0.92))
    ov = spark_layer(t)
    if ov is not None:
        if K != 1.0:
            ov = ov.resize((OW, round(OVERLAY_H * K)), Image.BILINEAR)
        img.paste(ov.convert("RGB"), (0, 0), ov.getchannel("A"))
    return img


def fx_overlays(img, t, banners, hook):
    """Text pops (HOOK), date/time/location banners and the optional BADGE slam."""
    for h, sp, glow in hook["items"]:
        t_out = h.get("t_out", HOOK_OUT)
        lt = t - h["t"]
        if lt < 0 or t > t_out + 0.3:
            continue
        ex_s, ex_a = hook_exit(t, t_out)
        if h["kind"] in ("chip", "sub"):
            k = ease_out_cubic(lt / 0.35)
            paste(img, sp, W / 2, h["cy"], ex_s, k * ex_a, dy=(1 - k) * 30)
            continue
        sc0, op0, ang = slam_state(lt)
        sc, op = sc0 * ex_s, op0 * ex_a
        if glow is not None:
            paste_rot(img, glow, W / 2, h["cy"], sc, op * 0.95, ang)
        if lt < 0.14:  # zoom-trail afterimages on the slam
            for mult, al in ((1.28, 0.30), (1.6, 0.14)):
                paste_rot(img, sp, W / 2, h["cy"], sc * mult, op * al, ang)
        layer = shine(sp, -0.2 + (lt - 0.30) * 2.0) if 0.30 <= lt <= 1.0 else sp
        paste_rot(img, layer, W / 2, h["cy"], sc, op, ang)
    for sp, cx, cy, sc, op in intro_layers(banners, t):
        paste(img, sp, cx, cy, sc, op)
    if BADGE:  # "2 HARI SAHAJA!" slam
        lt = t - BADGE["t"]
        b_out = BADGE.get("t_out", INTRO_OUT)
        if 0 <= lt and t < b_out:
            sc0, op0, ang = slam_state(lt)
            out_k = min(1.0, max(0.0, (t - (b_out - 0.2)) / 0.2))
            sc, op = sc0 * (1 - 0.1 * out_k), op0 * (1 - out_k)
            badge, bglow = hook["badge"]
            a2 = BADGE["angle"] + ang
            paste_rot(img, bglow, BADGE["cx"], BADGE["cy"], sc, op * 0.8, a2)
            if lt < 0.14:
                paste_rot(img, badge, BADGE["cx"], BADGE["cy"], sc * 1.3, op * 0.3, a2)
            paste_rot(img, shine(badge, -0.2 + (lt - 0.3) * 2.0) if 0.3 <= lt <= 1.0 else badge,
                      BADGE["cx"], BADGE["cy"], sc, op, a2)
    return img


# --------------------------------------------------------------------------
# end card
# --------------------------------------------------------------------------
def build_end_card(last_frame, logo_path):
    bg = last_frame.filter(ImageFilter.GaussianBlur(26 * K))
    bg = Image.blend(bg, Image.new("RGB", bg.size, (14, 30, 84)), 0.78)
    # subtle vignette
    yy, xx = np.mgrid[0:OH, 0:OW]
    v = 1 - 0.30 * (((xx - OW / 2) / (OW / 2)) ** 2 + ((yy - OH / 2) / (OH / 2)) ** 2) / 2
    bg = Image.fromarray((np.asarray(bg) * v[..., None]).astype(np.uint8))

    def fit(text, weight, size, fill, max_w=940, **kw):
        while True:
            s = text_sprite(text, weight, size, fill, **kw)
            if lu(s) <= max_w + 48 or size < 30:
                return s
            size -= 2

    els = []  # (sprite, center_y, start_time, kind)
    els.append((fit("7 & 8 NOVEMBER 2026", "Black", 92, YELLOW, stroke=4,
                    stroke_fill=RED, tracking=1), 430, 0.35, "slide"))
    els.append((fit("SABTU & AHAD", "ExtraBold", 74, WHITE, tracking=4), 575, 0.65, "slide"))
    els.append((pill_sprite("9 PAGI – 10 MALAM", "ExtraBold", 58, WHITE,
                            (255, 255, 255, 30), outline=YELLOW + (255,), tracking=3),
                715, 0.95, "slide"))
    dw, dh = round(200 * K), round(8 * K)
    div = Image.new("RGBA", (dw, dh), (0, 0, 0, 0))
    ImageDraw.Draw(div).rounded_rectangle((0, 0, dw - 1, dh - 1), dh // 2, fill=YELLOW + (255,))
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
    ap.add_argument("--width", type=int, default=1080,
                    help="output width (1080 = Full HD 1080x1920, 1440 = 2K 1440x2560)")
    ap.add_argument("--config", help="python file overriding the constants (POPUPS, INTRO, HOOK, ...)")
    ap.add_argument("--music", help="background music WAV (already ducked under the voice)")
    ap.add_argument("--sfx", help="sound-effects WAV mixed on top")
    ap.add_argument("--logo", help="optional official logo PNG (transparent background)")
    ap.add_argument("--vo", help="optional voice-over audio file played on the end card")
    ap.add_argument("--preview-dir", help="also dump key frames as PNG here")
    args = ap.parse_args()

    if args.config:
        for k, v in runpy.run_path(args.config).items():
            if k.isupper() and not k.startswith("_"):
                globals()[k] = v
    set_output_width(args.width)

    # sanity: pop-ups must never overlap (previous one is removed first)
    for a, b in zip(POPUPS, POPUPS[1:]):
        assert a["t_in"] + a.get("dur", POPUP_DURATION) <= b["t_in"], "pop-ups overlap"

    sprites = []  # per pop-up: [(start offset in s, sprite), ...]
    for p in POPUPS:
        phases = [(0.0, p)]
        if "then" in p:
            phases.append((p["then"]["t"] - p["t_in"], p["then"]))
        sprites.append([(off, popup_sprite(ph["name"], ph["price"], ph["suffix"],
                                           **ph.get("opts", {}))) for off, ph in phases])
    intro = build_intro()
    hook = build_hook(args.logo)
    label = build_label()
    src_dur = probe_duration(args.input)
    video_tmp = str(Path(args.output).with_suffix(".video.mp4"))
    fbytes = OW * OH * 3
    # footage is upscaled with Lanczos (+ a light sharpen) when OW != W; overlays are native
    vf = f"fps={FPS}" + (f",scale={OW}:{OH}:flags=lanczos+accurate_rnd,unsharp=5:5:0.45:5:5:0.0" if OW != W else "")

    dec = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", args.input, "-an", "-vf", vf,
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
         "-preset", "medium" if OW <= W else "slow", "-crf", "23" if OW <= W else "22",
         "-maxrate", "6M" if OW <= W else "9M", "-bufsize", "12M" if OW <= W else "18M",
         "-pix_fmt", "yuv420p",
         "-movflags", "+faststart", video_tmp], stdin=subprocess.PIPE)

    preview_t = {0.07: "00_open_flash", 1.77: "20_impact1", 2.00: "21_after1", 2.50: "22_impact2", 10.07: "23_impact_badge", 1.3: "00a_chip", 1.80: "00b_slam1", 2.1: "00c_slam1_settled",
                 2.55: "00d_slam2", 3.2: "00e_hook_full", 4.15: "00f_banner1_burst",
                 10.15: "00g_badge", 4.6: "01_intro_date", 6.4: "02_intro_day", 7.9: "03_intro_loc",
                 9.7: "04_intro_full", 11.2: "05_intro_gone",
                 12.1: "06_before_bantal", 12.6: "07_bantal", 14.3: "08_removed",
                 16.3: "09_6biji", 19.1: "10_kain1", 21.5: "11_kain2",
                 24.9: "12_sarung", 27.4: "13_toto", 30.0: "14_single", 34.9: "15_peluk",
                 31.0: "16_single3for100", 1.5: "17_label_start", 41.0: "18_label_late",
                 3.6: "19_label_fadeout"}
    preview_frames = {round(t * FPS): n for t, n in (PREVIEW_T or preview_t).items()}
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
        img = Image.frombuffer("RGB", (OW, OH), buf, "raw", "RGB", 0, 1)
        img = fx_base(img, t, hook)
        for p, phases in zip(POPUPS, sprites):
            lt = t - p["t_in"]
            st = popup_state(lt, p.get("dur", POPUP_DURATION))
            if st:
                sp = [x for off, x in phases if lt >= off][-1]
                scale = st[0]
                if len(phases) > 1:  # bounce when the card swaps to the bigger one
                    k = lt - phases[1][0]
                    if 0 <= k < 0.45:
                        scale *= 0.74 + 0.26 * spring(k)
                paste(img, sp, W / 2, POPUP_CENTER_Y, scale, st[1])
                break
        img = fx_overlays(img, t, intro, hook)
        la = label_alpha(t)
        if la > 0.003:
            paste(img, label, W / 2, LABEL_CY, 1.0, la)
        out = img.tobytes()
        if pdir and n in preview_frames:
            Image.frombytes("RGB", (OW, OH), out).save(pdir / f"{preview_frames[n]}.png")
        enc.stdin.write(out)
        last = buf
        n += 1
    dec.wait()
    if last is None:
        sys.exit("no frames decoded")

    # end card
    last_img = Image.frombytes("RGB", (OW, OH), last)
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
    # mux the footage audio (fade at the end of the footage, padded with silence) with an
    # optional --vo on the end card, --music (pre-ducked) and --sfx
    fade_st = max(0.0, n / FPS - 0.35)
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", video_tmp, "-i", args.input]
    fmt = "aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo"
    vol = "volume=0.72," if (args.music or args.sfx) else ""   # head-room for the music + sfx
    flt = (f"[1:a]{fmt},{vol}afade=t=out:st={fade_st:.3f}:d=0.35,apad=whole_dur={total:.3f}[a0]")
    labels, nxt = ["[a0]"], 2
    if args.vo:
        d = int(n / FPS * 1000) + 300
        cmd += ["-i", args.vo]
        flt += f";[{nxt}:a]{fmt},adelay={d}|{d},apad=whole_dur={total:.3f}[v]"
        labels.append("[v]"); nxt += 1
    for opt, lab in ((args.music, "[m]"), (args.sfx, "[s]")):
        if opt:
            cmd += ["-i", opt]
            flt += f";[{nxt}:a]{fmt},apad=whole_dur={total:.3f}{lab}"
            labels.append(lab); nxt += 1
    if len(labels) > 1:
        flt += f";{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=first,alimiter=limit=0.80:level=0:attack=5:release=70[a]"
    else:
        flt = flt.replace("[a0]", "[a]")
    cmd += ["-filter_complex", flt, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
            "-t", f"{total:.3f}", "-movflags", "+faststart", args.output]
    subprocess.run(cmd, check=True)
    Path(video_tmp).unlink()
    print(f"footage frames: {n} ({src_dur:.2f}s)  end card: {total_end} frames  total: {total:.2f}s")


if __name__ == "__main__":
    main()
