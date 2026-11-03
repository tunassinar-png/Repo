#!/usr/bin/env python3
"""
Contact sheet of the burned-in caption strip, one labelled tile per frame.

The captions in presenter footage are word-highlighted (cyan box on the word being
spoken), so they give word-level timing without any speech-to-text. Read the sheet
in order (left to right, then down); tile label = seconds in the source video.

    python3 -B -I caption_strips.py INPUT.mp4 T0 T1 OUT.png [--fps 10] [--cols 3]
                                    [--crop X Y W H]   # default 140 1590 800 110

Tips: --fps 4 over 12 s windows to read the whole video, then --fps 10 over ~0.6 s
around each price word to get its start time to +/-0.05 s.
"""
import argparse
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("t0", type=float)
    ap.add_argument("t1", type=float)
    ap.add_argument("out")
    ap.add_argument("--fps", type=float, default=10)
    ap.add_argument("--cols", type=int, default=3)
    ap.add_argument("--crop", type=int, nargs=4, default=[140, 1590, 800, 110],
                    metavar=("X", "Y", "W", "H"))
    a = ap.parse_args()
    x, y, w, h = a.crop
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(a.t0), "-t", str(a.t1 - a.t0), "-i", a.input,
         "-vf", f"fps={a.fps},crop={w}:{h}:{x}:{y}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True).stdout
    n = len(raw) // (w * h * 3)
    fr = np.frombuffer(raw, np.uint8).reshape(n, h, w, 3)
    rows = (n + a.cols - 1) // a.cols
    sheet = Image.new("RGB", (a.cols * w, rows * h))
    font = ImageFont.load_default(size=34)
    for i in range(n):
        im = Image.fromarray(fr[i])
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 130, 38), fill=(0, 0, 0))
        d.text((4, 2), f"{a.t0 + i / a.fps:.2f}", fill=(255, 255, 0), font=font)
        sheet.paste(im, ((i % a.cols) * w, (i // a.cols) * h))
    sheet.resize((sheet.width // 2, sheet.height // 2)).save(a.out)
    print(f"{n} tiles -> {a.out}")


if __name__ == "__main__":
    main()
