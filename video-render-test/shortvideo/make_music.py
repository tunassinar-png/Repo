"""Original upbeat 'blue-collar' anthem-style instrumental, D major, 120 BPM, 10 s. Usage: make_music.py out.wav"""
import sys, wave
import numpy as np

SR, T = 48000, 10
N = SR * T
t = np.arange(N) / SR
rng = np.random.default_rng(3)
beat = 0.5


def add(buf, sig, t0):
    i = int(t0 * SR)
    if i >= N or i < 0:
        return
    n = min(len(sig), N - i); buf[i:i + n] += sig[:n]


def kick(a=1.0):
    tt = np.arange(int(0.42 * SR)) / SR
    f = 45 + 95 * np.exp(-tt * 28)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 7.5) * a


def snare(a=1.0):
    L = int(0.25 * SR); tt = np.arange(L) / SR
    n = rng.standard_normal(L); n = np.diff(n, prepend=0)
    return (n * 0.55 + np.sin(2 * np.pi * 190 * tt) * 0.6) * np.exp(-tt * 18) * a


def clap(a=1.0):
    L = int(0.22 * SR); tt = np.arange(L) / SR
    n = np.diff(rng.standard_normal(L), prepend=0)
    e = sum(np.exp(-np.clip(tt - d, 0, None) * 60) * (tt >= d) for d in (0, .012, .025))
    return n * e * np.exp(-tt * 14) * 0.5 * a


def hat(a=1.0, open_=False):
    L = int((0.16 if open_ else 0.05) * SR); tt = np.arange(L) / SR
    return np.diff(rng.standard_normal(L), prepend=0) * np.exp(-tt * (18 if open_ else 70)) * 0.5 * a


def lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); s = 0.0
    for i in range(len(x)):
        s = (1 - a) * x[i] + a * s; y[i] = s
    return y


def saw(f, L, det=0.004):
    tt = np.arange(L) / SR
    return sum(2 * ((tt * f * (1 + d)) % 1) - 1 for d in (-det, 0, det)) / 3


def stab(freqs, dur=0.35, a=1.0):
    L = int(dur * SR); tt = np.arange(L) / SR
    s = sum(saw(f, L) for f in freqs) / len(freqs)
    s = lp(s, 2600)
    return s * np.exp(-tt * 6) * np.minimum(1, tt * 500) * a


def lead(f, dur=0.26, a=1.0):
    L = int(dur * SR); tt = np.arange(L) / SR
    s = np.sin(2 * np.pi * f * tt) + 0.35 * np.sign(np.sin(2 * np.pi * f * tt)) * 0.5 + 0.25 * np.sin(4 * np.pi * f * tt)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 6 * tt)
    s = np.sin(2 * np.pi * f * tt * vib) + 0.3 * np.sin(4 * np.pi * f * tt) + 0.15 * np.sign(np.sin(2 * np.pi * f * tt))
    return s * np.exp(-tt * 5) * np.minimum(1, tt * 400) * a


def bass(f, dur=0.24, a=1.0):
    L = int(dur * SR); tt = np.arange(L) / SR
    return (np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 7) * np.minimum(1, tt * 300) * a


CH = [  # D, A, Bm, G, D
    dict(tri=[293.66, 369.99, 440.0], root=73.42),
    dict(tri=[277.18, 329.63, 440.0], root=55.0),
    dict(tri=[293.66, 369.99, 493.88], root=61.74),
    dict(tri=[293.66, 392.0, 493.88], root=49.0),
    dict(tri=[293.66, 369.99, 440.0], root=73.42),
]
HOOK = {1: [880.0, 739.99, 880.0, 987.77, 880.0, 739.99, 659.25, 0],
        2: [987.77, 880.0, 987.77, 1108.7, 987.77, 880.0, 739.99, 0],
        3: [783.99, 880.0, 987.77, 880.0, 783.99, 739.99, 659.25, 587.33]}
dr = np.zeros(N); bs = np.zeros(N); ch = np.zeros(N); ld = np.zeros(N)
for b in range(5):
    t0 = b * 2.0
    c = CH[b]
    for k in range(4):
        tn = t0 + k * beat
        if b == 4 and k > 0:
            continue
        add(dr, kick(1.0 if k % 2 == 0 else 0.8), tn)
        if k in (1, 3) and b >= 1:
            add(dr, snare(0.9), tn); add(dr, clap(0.7), tn)
        if b >= 1 and b < 4:
            add(dr, hat(0.6), tn); add(dr, hat(0.9, k == 3), tn + beat / 2)
        elif b == 0:
            add(dr, hat(0.35), tn + beat / 2)
    # bass: 8th-note driving pattern
    if b < 4:
        for k in range(8):
            if b == 0 and k < 4:
                f = c['root'] * (2 if k % 2 else 1)
            else:
                f = c['root'] * (2 if k % 4 == 3 else 1)
            add(bs, bass(f, 0.22, 0.9 if k % 2 == 0 else 0.7), t0 + k * beat / 2)
    else:
        add(bs, bass(c['root'], 1.6, 1.0), t0)
    # chord stabs (off-beat) and final hit
    if b < 4:
        for k in (0.75, 1.25, 1.75) if b >= 1 else (1.0, 1.5):
            add(ch, stab(c['tri'], 0.28, 0.9), t0 + k * 1.0 - 0.0)
    else:
        add(ch, stab(c['tri'] + [c['tri'][0] * 2], 1.8, 1.4), t0)
    if b in HOOK:
        for k, f in enumerate(HOOK[b]):
            if f > 0:
                add(ld, lead(f, 0.24, 0.8), t0 + k * beat / 2 + 0.0)
fade = np.minimum(1, (T - t) / 0.7) * np.minimum(1, t / 0.02)
dr *= 0.9; bs *= 0.9; ch *= 0.28; ld *= 0.20
mix = (dr + bs + ch + ld) * fade
# soft limiter
mix = np.tanh(mix * 1.25) / np.tanh(1.25)
mix = mix / np.max(np.abs(mix)) * 0.85
d = int(0.009 * SR)
st = np.stack([mix, np.concatenate([np.zeros(d), mix[:-d]]) * 0.98], 1)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())
print('music ok')
