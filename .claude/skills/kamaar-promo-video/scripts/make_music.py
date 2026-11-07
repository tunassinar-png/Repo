#!/usr/bin/env python3
"""
Procedural background music + synced sound effects for a KAMAAR promo video.

No music files are needed or copied: an upbeat promo track (kick, clap, hats, bass,
chord stabs, arpeggio, lead, risers) is synthesised with numpy/scipy, so it is
royalty-free. The music is ducked automatically under the presenter's voice, and a
second WAV holds the sound effects (boom / hit / tick / swoosh / ding / pop) placed at
the times in the video's config (EVENTS, POPUPS, INTRO, HOOK).

    python3 -B -I make_music.py INPUT.mp4 CONFIG.py OUT_DIR [--bpm 126] [--end-card 5.5]

writes OUT_DIR/music_ducked.wav and OUT_DIR/sfx.wav (44.1 kHz stereo), then render with
    render_kamaar_popups.py IN.mp4 OUT.mp4 --config CONFIG.py --music .../music_ducked.wav
                            --sfx .../sfx.wav

CONFIG.py may define (all optional):
    MUSIC_ANCHOR   time (s) of a downbeat, normally the first big hit / "drop"  [3.0]
    MUSIC_SECTIONS [(t0, t1, level)]  level 1 pad+hats | 2 +kick+bass | 3 +clap+stabs+arp
                   | 4 +open hat+lead                                          [level 3]
    MUSIC_RISERS   [(t0, t1)]  noise/saw risers ending on a drop
    MUSIC_GAIN_DB  loudness of the un-ducked music (dBFS RMS)                  [-12]
    MUSIC_DUCK_DB  how far the music dips while the voice is speaking          [-11]
"""
import argparse
import runpy
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 44100
RNG = np.random.default_rng(7)


# ---------------------------------------------------------------- helpers
def sos_filter(x, kind, fc, order=2):
    sos = signal.butter(order, fc, btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def mix_in(buf, sig, t, gain=1.0):
    """Add (n,) or (n,2) `sig` into stereo `buf` starting at time t (clipped at 0)."""
    i = int(round(t * SR))
    if sig.ndim == 1:
        sig = np.stack([sig, sig], axis=1)
    j0 = max(0, -i)
    i0 = max(0, i)
    n = min(len(sig) - j0, len(buf) - i0)
    if n > 0:
        buf[i0:i0 + n] += sig[j0:j0 + n] * gain


def midi(m):
    return 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)


def noise(n):
    return RNG.standard_normal(n)


def env_exp(n, rate):
    return np.exp(-np.arange(n) / SR * rate)


# ---------------------------------------------------------------- instruments
def kick():
    n = int(0.36 * SR)
    t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(46 + 120 * np.exp(-t * 30)) / SR
    body = np.sin(ph) * np.exp(-t * 8.5)
    click = noise(n) * np.exp(-t * 260) * 0.25
    return np.tanh(1.6 * (body + click)) * 0.9


def clap():
    n = int(0.28 * SR)
    out = np.zeros(n)
    for off, dec in ((0, 55), (0.011, 55), (0.022, 55), (0.034, 18)):
        i = int(off * SR)
        seg = noise(n - i) * np.exp(-np.arange(n - i) / SR * dec)
        out[i:] += seg
    out = sos_filter(sos_filter(out, "highpass", 900), "lowpass", 4500)
    return out * 0.55


def hat(open_=False):
    n = int((0.30 if open_ else 0.07) * SR)
    x = sos_filter(noise(n), "highpass", 7000, 3) * env_exp(n, 9 if open_ else 70)
    return x * (0.22 if open_ else 0.26)


def bass_note(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    saw = 2 * ((f * t) % 1) - 1
    sq = np.sign(np.sin(2 * np.pi * f * t))
    x = 0.55 * np.sin(2 * np.pi * f * t) + 0.25 * saw + 0.12 * sq
    x = sos_filter(x, "lowpass", 420)
    env = np.minimum(1, t / 0.006) * np.exp(-t * 3.2) * np.minimum(1, (dur - t) / 0.03)
    return x * env


def supersaw(freqs, dur, detunes=(-14, -6, 0, 6, 14), side=0):
    """Chord of detuned saws -> stereo (n,2); `side` rotates which detunes go L / R."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros((n, 2))
    for f in freqs:
        for k, c in enumerate(detunes):
            ff = f * 2 ** (c / 1200)
            ph = RNG.random()
            w = 2 * (((ff * t) + ph) % 1) - 1
            pan = ((k + side) % len(detunes)) / (len(detunes) - 1)
            out[:, 0] += w * (1 - pan)
            out[:, 1] += w * pan
    return out / (len(freqs) * len(detunes)) * 2.2


def pluck(freq, dur=0.22, duty=0.3):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.where(((freq * t) % 1) < duty, 1.0, -1.0) * 0.6 + np.sin(2 * np.pi * freq * t) * 0.4
    x = sos_filter(x, "lowpass", 4800)
    return x * np.exp(-t * 14) * np.minimum(1, t / 0.003)


def riser(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    nz = noise(n)
    seg = 24
    edges = np.linspace(0, n, seg + 1).astype(int)
    for k in range(seg):
        fc = 400 * (14000 / 400) ** (k / seg)
        a, b = edges[k], edges[k + 1]
        x[a:b] = sos_filter(sos_filter(nz[a:b], "highpass", fc * 0.6), "lowpass", min(fc * 1.6, 20000))
    ramp = (t / dur) ** 2.2
    tone_f = 200 * 2 ** (3.5 * t / dur)
    tone = np.sin(2 * np.pi * np.cumsum(tone_f) / SR) * 0.25
    return (x * 2.2 + tone) * ramp


# ---------------------------------------------------------------- sound effects
def sfx_boom(strong=1.0):
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(34 + 90 * np.exp(-t * 14)) / SR
    body = np.sin(ph) * np.exp(-t * 3.4)
    crack = sos_filter(noise(n), "lowpass", 2500) * np.exp(-t * 18) * 0.5
    air = sos_filter(noise(n), "highpass", 5000) * np.exp(-t * 30) * 0.18
    return np.tanh(1.4 * (body * 1.0 + crack + air)) * 0.95 * strong


def sfx_whoosh(dur=0.42):
    n = int(dur * SR)
    t = np.arange(n) / SR
    nz = noise(n)
    seg = 14
    edges = np.linspace(0, n, seg + 1).astype(int)
    x = np.zeros(n)
    for k in range(seg):
        fc = 500 * (6000 / 500) ** (k / seg)
        a, b = edges[k], edges[k + 1]
        x[a:b] = sos_filter(sos_filter(nz[a:b], "highpass", fc * 0.5), "lowpass", fc * 1.8)
    return x * 2.0 * (t / dur) ** 1.6 * 0.5


def sfx_tick(f=2000):
    n = int(0.05 * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * f * t) * np.exp(-t * 70) * 0.28


def sfx_ding():
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    mod = np.sin(2 * np.pi * 1568 * 3.5 * t) * 2.2 * np.exp(-t * 9)
    a = np.sin(2 * np.pi * 1568 * t + mod) * np.exp(-t * 4.5)
    b = np.sin(2 * np.pi * 2093 * t) * np.exp(-t * 6) * 0.4
    b = np.concatenate([np.zeros(int(0.06 * SR)), b])[:n]
    return (a + b) * 0.42


def sfx_pop():
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(420 + 900 * (t / 0.09)) / SR
    return np.sin(ph) * np.exp(-t * 38) * 0.5


def sfx_shimmer():
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k, f in enumerate([1046, 1318, 1568, 2093, 2637]):
        d = int(k * 0.07 * SR)
        seg = np.sin(2 * np.pi * f * t[: n - d]) * np.exp(-t[: n - d] * 4.0)
        out[d:] += seg * 0.18
    return out


# ---------------------------------------------------------------- music arrangement
CHORDS = [  # I - V - vi - IV in C major (voicings near middle C), bass roots
    ([60, 64, 67], 36), ([59, 62, 67], 43), ([57, 60, 64], 33 + 12), ([57, 60, 65], 41),
]


def build_music(total, bpm, anchor, sections, risers, voice_env_fn):
    n = int(total * SR)
    beat = 60.0 / bpm
    bar = 4 * beat
    stems = {k: np.zeros((n, 2)) for k in ("kick", "snare", "hats", "bass", "stab", "pad", "arp", "lead", "fx")}
    kick_times = []

    def level(t):
        for a, b, lv in sections:
            if a <= t < b:
                return lv
        return sections[-1][2] if sections else 3

    kk, cl, hh, ho = kick(), clap(), hat(False), hat(True)
    first_bar = int(np.floor((0 - anchor) / bar)) - 1
    last_bar = int(np.ceil((total - anchor) / bar)) + 1
    for bi in range(first_bar, last_bar):
        t0 = anchor + bi * bar
        if t0 + bar < 0 or t0 > total:
            continue
        lv = level(max(t0, 0.0))
        chord, root = CHORDS[bi % 4]
        f_chord = midi(chord)
        # pad: sustained chord, slow attack, every level
        padlen = bar + 0.3
        pad = supersaw(f_chord, padlen, detunes=(-9, 0, 9), side=bi) * 0.55
        env = np.minimum(1, np.arange(len(pad)) / SR / 0.35) * np.minimum(1, (padlen - np.arange(len(pad)) / SR) / 0.3)
        mix_in(stems["pad"], pad * env[:, None], t0, 1.0)
        for s in range(8):  # 8th notes
            ts = t0 + s * beat / 2
            on_beat = s % 2 == 0
            if on_beat and lv >= 2:
                mix_in(stems["kick"], kk, ts)
                kick_times.append(ts)
            if (not on_beat) and lv >= 1:
                mix_in(stems["hats"], hh, ts)
            if lv >= 4 and (not on_beat) and s in (3, 7):
                mix_in(stems["hats"], ho, ts)
            if lv >= 3 and s in (2, 6):
                mix_in(stems["snare"], cl, ts)
            if lv >= 2:  # bass: root on beats, octave on the "and"
                f = midi(root) * (2 if (not on_beat and s in (3, 7)) else 1)
                mix_in(stems["bass"], bass_note(float(f), beat * 0.48), ts, 0.9)
            if lv >= 3 and (not on_beat):  # offbeat chord stabs
                mix_in(stems["stab"], supersaw(f_chord, 0.30, side=bi + s) * np.exp(-np.arange(int(0.30 * SR)) / SR * 9)[:, None], ts)
        if lv >= 3:  # 16th arpeggio, up/down over the chord (octave up)
            arp = [f_chord[0], f_chord[1], f_chord[2], f_chord[1]]
            for s in range(16):
                ts = t0 + s * beat / 4
                f = float(arp[s % 4]) * 2 * (2 if s % 8 >= 4 else 1)
                mix_in(stems["arp"], pluck(f, 0.16), ts, 0.7)
        if lv >= 4:  # lead: simple chord-tone melody
            mel = [2, 2, 1, 2, 3, 2, 1, 0]
            tones = list(f_chord) + [f_chord[0] * 2]
            for s in range(8):
                ts = t0 + s * beat / 2
                f = float(tones[mel[s] % 4]) * 2
                mix_in(stems["lead"], pluck(f, 0.30, duty=0.5), ts, 0.8)
    for a, b in risers:
        r = riser(b - a)
        mix_in(stems["fx"], np.stack([r, r[::-1]], axis=1), a, 0.8)
        mix_in(stems["fx"], sfx_boom(0.7), b, 0.9)  # impact where the riser lands

    # kick side-chain "pump" on the harmonic stems
    pump = np.ones(n)
    for kt in kick_times:
        i = int(kt * SR)
        m = min(int(0.22 * SR), n - i)
        if m > 0 and i >= 0:
            pump[i:i + m] = np.minimum(pump[i:i + m], 1 - 0.55 * np.exp(-np.arange(m) / SR * 14))
    for k in ("stab", "pad", "arp", "lead"):
        stems[k] *= pump[:, None]

    stems["stab"] = sos_filter(stems["stab"], "lowpass", 3800)
    stems["pad"] = sos_filter(stems["pad"], "lowpass", 2400)
    stems["hats"] = sos_filter(stems["hats"], "highpass", 6000)
    mixed = (stems["kick"] * 0.95 + stems["snare"] * 0.8 + stems["hats"] * 0.7 + stems["bass"] * 0.85
             + stems["stab"] * 0.42 + stems["pad"] * 0.40 + stems["arp"] * 0.30 + stems["lead"] * 0.30
             + stems["fx"] * 0.6)
    # simple feedback echo (dotted 8th) on the arp/lead for width
    d = int(beat * 0.75 * SR)
    echo = np.zeros_like(mixed)
    src = (stems["arp"] + stems["lead"]) * 0.25
    echo[d:, 0] = src[:-d, 1]
    echo[d:, 1] = src[:-d, 0]
    mixed += echo
    return mixed


def voice_activity(video, total):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-vn", "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32)
    hop = int(0.02 * SR)
    m = len(a) // hop
    rms = np.sqrt((a[:m * hop].reshape(m, hop) ** 2).mean(1))
    db = 20 * np.log10(rms + 1e-9)
    active = (db > -34).astype(float)           # speech vs ambient hall noise
    # bridge tiny gaps (<0.18 s) so the music does not pump between words
    k = int(0.18 / 0.02)
    active = np.clip(np.convolve(active, np.ones(k), mode="same"), 0, 1)
    env = np.repeat(active, hop)
    out = np.zeros(int(total * SR))
    out[:min(len(out), len(env))] = env[:len(out)]
    return out


def smooth_gain(active, attack=0.04, release=0.40):
    """One-pole follower: fast attack (duck quickly), slow release."""
    g = np.zeros_like(active)
    a_a, a_r = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR))
    y = 0.0
    for i, x in enumerate(active):
        c = a_a if x > y else a_r
        y = c * y + (1 - c) * x
        g[i] = y
    return g


# ---------------------------------------------------------------- sfx scheduling
def build_sfx(total, cfg, footage_end, end_card):
    buf = np.zeros((int(total * SR), 2))
    boom, whoosh, ding, pop, shim = sfx_boom(), sfx_whoosh(), sfx_ding(), sfx_pop(), sfx_shimmer()
    for ev in cfg.get("EVENTS", []):
        t = ev["t"]
        strong = ev.get("flash", 0) >= 0.5 or ev.get("shake", 0) >= 20
        mid = ev.get("flash", 0) >= 0.3 or ev.get("burst", (0, 0, 0))[2] >= 60
        if strong:
            mix_in(buf, whoosh, t - 0.42, 0.9)
            mix_in(buf, boom, t, 0.9)
        elif mid:
            mix_in(buf, whoosh[: int(0.25 * SR)] * np.linspace(0.3, 1, int(0.25 * SR)), t - 0.25, 0.6)
            mix_in(buf, boom[: int(0.6 * SR)] * np.exp(-np.arange(int(0.6 * SR)) / SR * 3), t, 0.45)
        else:
            mix_in(buf, sfx_tick(1500), t, 0.8)
    for p in cfg.get("POPUPS", []):
        mix_in(buf, whoosh[: int(0.2 * SR)], p["t_in"] - 0.2, 0.45)
        mix_in(buf, pop, p["t_in"], 0.9)
        mix_in(buf, ding, p["t_in"] + 0.03, 0.9)
    for entry in cfg.get("INTRO", []):
        lines = entry["lines"] if isinstance(entry, dict) else entry[3]
        for ln in lines:
            mix_in(buf, sfx_tick(2400), ln[5], 0.8)
    for h in cfg.get("HOOK", []):
        if h["kind"] in ("chip", "sub"):
            mix_in(buf, whoosh[: int(0.2 * SR)], h["t"] - 0.15, 0.5)
            mix_in(buf, pop, h["t"], 0.6)
    # end card (matches build_end_card timings: lines at +0.35, +0.65, +0.95, +1.2, ...; badge +2.0; logo +2.6)
    t0 = footage_end
    mix_in(buf, whoosh, t0 - 0.2, 0.7)
    mix_in(buf, boom, t0 + 0.2, 0.7)
    for dt in (0.35, 0.65, 0.95, 1.30, 1.45, 1.65):
        mix_in(buf, sfx_tick(2200), t0 + dt, 0.7)
    mix_in(buf, pop, t0 + 2.0, 0.9)
    mix_in(buf, ding, t0 + 2.02, 0.9)
    mix_in(buf, shim, t0 + 2.6, 0.7)
    return buf


# ---------------------------------------------------------------- main
def to_wav(path, x):
    x = np.clip(x, -1, 1)
    wavfile.write(path, SR, (x * 32767).astype(np.int16))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("config")
    ap.add_argument("out_dir")
    ap.add_argument("--bpm", type=float, default=126)
    ap.add_argument("--end-card", type=float, default=5.5)
    a = ap.parse_args()
    cfg = runpy.run_path(a.config)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                "default=nw=1:nk=1", a.input], capture_output=True, text=True).stdout)
    end_card = cfg.get("END_CARD_SECONDS", a.end_card)
    total = dur + end_card
    anchor = cfg.get("MUSIC_ANCHOR", 3.0)
    sections = cfg.get("MUSIC_SECTIONS", [(0, total, 3)])
    risers = cfg.get("MUSIC_RISERS", [])
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    music = build_music(total, a.bpm, anchor, sections, risers, None)
    # level the music, then duck it under the voice
    gain_db = cfg.get("MUSIC_GAIN_DB", -12)
    duck_db = cfg.get("MUSIC_DUCK_DB", -11)
    rms = np.sqrt(np.mean(music ** 2) + 1e-12)
    music = music / rms * 10 ** (gain_db / 20)
    music = np.tanh(music * 0.9) / 0.9
    duck = smooth_gain(voice_activity(a.input, total))
    g = 1 - duck * (1 - 10 ** (duck_db / 20))
    music = music * g[:, None]
    fade = int(1.4 * SR)                       # fade the whole track out at the very end
    music[-fade:] *= np.linspace(1, 0, fade)[:, None]
    fade_in = int(0.15 * SR)
    music[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    sfx = build_sfx(total, cfg, dur, end_card)
    sfx = np.tanh(sfx * cfg.get("SFX_GAIN", 0.55) * 1.2)  # level + soft limiter (no clipping)
    to_wav(out / "music_ducked.wav", music)
    to_wav(out / "sfx.wav", sfx)
    pk = lambda x: 20 * np.log10(np.abs(x).max() + 1e-9)
    print(f"total {total:.2f}s | music peak {pk(music):.1f} dBFS, rms {20*np.log10(np.sqrt((music**2).mean())):.1f} dBFS | "
          f"sfx peak {pk(sfx):.1f} dBFS")


if __name__ == "__main__":
    main()
