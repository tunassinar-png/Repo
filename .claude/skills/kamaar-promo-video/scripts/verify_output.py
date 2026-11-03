#!/usr/bin/env python3
"""
Verify a rendered promo video: format, audio level, and that overlays appear and
disappear at the expected times.

    python3 -B -I verify_output.py OUTPUT.mp4 SOURCE.mp4 --times 11.9 12.3 13.5 14.5 \
        [--audio-at 2 31 46 49] [--region X0 Y0 X1 Y1]    # region in 1080x1920 units

For each time, prints the mean abs difference between OUTPUT and SOURCE inside the
region (default: the pop-up card area). Encode noise is ~2; a visible overlay is
>> 10. Output of any resolution is accepted (it is resized to 1080x1920 first).
Audio: mean volume near -6..-13 dB = speech present, about -91 dB = silence.
"""
import argparse
import subprocess

import numpy as np
from PIL import Image


def frame(path, t):
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(t), "-i", path, "-frames:v", "1",
         "-vf", "scale=1080:1920", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(1920, 1080, 3).astype(int)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("output")
    ap.add_argument("source")
    ap.add_argument("--times", type=float, nargs="*", default=[])
    ap.add_argument("--audio-at", type=float, nargs="*", default=[])
    ap.add_argument("--region", type=int, nargs=4, default=[200, 1270, 880, 1500])
    a = ap.parse_args()
    print(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size,bit_rate:stream=codec_type,codec_name,width,height,pix_fmt,channels",
         "-of", "default=nw=1", a.output], capture_output=True, text=True).stdout)
    x0, y0, x1, y1 = a.region
    for t in a.times:
        d = np.abs(frame(a.output, t)[y0:y1, x0:x1] - frame(a.source, t)[y0:y1, x0:x1]).mean()
        print(f"t={t:6.2f}s  region diff vs source = {d:7.2f}")
    for t in a.audio_at:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", str(t), "-t", "1.2",
                            "-i", a.output, "-vn", "-af", "volumedetect", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        mv = [l.split("mean_volume:")[1].strip() for l in r.splitlines() if "mean_volume" in l]
        print(f"audio @{t:5.1f}s: {mv[0] if mv else 'n/a'}")


if __name__ == "__main__":
    main()
