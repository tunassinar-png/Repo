"""Documentary underscore: mysterious (A minor) -> inspiring (C/G major). 60 s. Usage: make_music.py out.wav"""
import sys, wave
import numpy as np

SR, T = 48000, 60
N = SR * T
t = np.arange(N) / SR
rng = np.random.default_rng(21)
BPM = 66; beat = 60 / BPM; bar = 4 * beat


def env(pts):
    xs, ys = zip(*pts); return np.interp(t, xs, ys)


def add(buf, sig, t0):
    i = int(t0 * SR)
    if 0 <= i < N:
        n = min(len(sig), N - i); buf[i:i + n] += sig[:n]


def bell(f, dur=3.0, a=1.0):
    tt = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f * tt) + .5 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt * 3) + .25 * np.sin(2 * np.pi * f * 5.4 * tt) * np.exp(-tt * 5)
    return s * np.exp(-tt * 1.6) * np.minimum(1, tt * 500) * a


def pluck(f, dur=1.2, a=1.0):
    tt = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f * tt) + .4 * np.sin(4 * np.pi * f * tt) + .15 * np.sin(6 * np.pi * f * tt)
    return s * np.exp(-tt * 4) * np.minimum(1, tt * 400) * a


def padnote(f, dur, a=1.0):
    tt = np.arange(int(dur * SR)) / SR
    s = (np.sin(2 * np.pi * f * tt) + .35 * np.sin(2 * np.pi * f * 2.003 * tt) + .15 * np.sin(2 * np.pi * f * 3 * tt)) * (1 + 0.1 * np.sin(2 * np.pi * 0.2 * tt))
    return s * np.minimum(1, tt / (dur * 0.35)) * np.minimum(1, (dur - tt) / (dur * 0.35)) * a


def kick(a=1.0):
    tt = np.arange(int(0.45 * SR)) / SR
    return np.sin(2 * np.pi * np.cumsum(40 + 80 * np.exp(-tt * 26)) / SR) * np.exp(-tt * 6) * a


CH = {'Am': [110.0, 164.81, 220.0, 261.63], 'F': [87.31, 130.81, 174.61, 220.0], 'Dm': [73.42, 146.83, 220.0, 293.66], 'E': [82.41, 164.81, 207.65, 246.94],
      'C': [65.41, 130.81, 196.0, 261.63, 329.63], 'G': [98.0, 146.83, 196.0, 246.94, 293.66], 'Am2': [110.0, 164.81, 220.0, 261.63, 329.63], 'F2': [87.31, 130.81, 174.61, 220.0, 261.63]}
prog = [(0, ['Am'] * 2 + ['F'] * 2), (16, ['Am', 'F', 'Dm', 'E']), (32, ['Dm', 'F', 'Am', 'E']), (40, ['F2', 'C', 'G', 'Am2']), (50, ['F2', 'C', 'G', 'C'])]


def chord_at(tm):
    for st, ch in reversed(prog):
        if tm >= st:
            return ch[int((tm - st) / bar) % len(ch)]


pad = np.zeros(N); pl = np.zeros(N); bl = np.zeros(N); kk = np.zeros(N); lead = np.zeros(N)
nb = int(T / bar) + 1
for b in range(nb):
    t0 = b * bar; name = chord_at(t0 + 0.01); fr = CH[name]
    for j, f in enumerate(fr):
        add(pad, padnote(f * (1 if j else 1), bar + 1.2, 0.9 if j == 0 else 0.55), t0)
    # arpeggio: sparse and dark early, flowing and bright late
    dens = 2 if t0 < 10 else (4 if t0 < 40 else 8)
    steps = fr[1:] if t0 < 40 else fr
    for k in range(dens):
        tn = t0 + k * bar / dens
        f = steps[k % len(steps)] * (4 if t0 < 40 else 4)
        add(pl, pluck(f, 1.4 if dens < 8 else 0.9, 0.6 if t0 < 40 else 0.7), tn)
    if 10 <= t0 < 40:
        for k in range(4):
            add(kk, kick(0.5 if k % 2 == 0 else 0.3), t0 + k * beat)
    if t0 >= 40 and t0 < 58:
        for k in (0, 2):
            add(kk, kick(0.55), t0 + k * beat)
# mysterious bells
for tm, f in [(1.0, 880.0), (3.5, 659.25), (6.0, 987.77), (8.2, 523.25), (14.0, 880.0), (22.0, 659.25), (28.5, 783.99), (34.0, 622.25)]:
    add(bl, bell(f, 3.5, 0.55), tm)
# inspiring lead (major pentatonic) from 50 s
mel = [(50.0, 659.25), (51.4, 783.99), (52.8, 880.0), (54.8, 783.99), (56.2, 987.77), (57.6, 1046.5)]
for tm, f in mel:
    tt = np.arange(int(1.9 * SR)) / SR
    s = (np.sin(2 * np.pi * f * tt * (1 + 0.003 * np.sin(2 * np.pi * 5.5 * tt))) + .3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 1.3) * np.minimum(1, tt * 30)
    add(lead, s, tm)
# dark noise swell (whisper) in first 40 s, riser into 40 s
nz = rng.standard_normal(N); X = np.fft.rfft(nz); fq = np.fft.rfftfreq(N, 1 / SR)
X *= 1 / (1 + (500 / np.maximum(fq, 1)) ** 4) / (1 + (fq / 4000) ** 4)
air = np.fft.irfft(X, N); air /= np.max(np.abs(air))
air *= env([(0, 0.0), (3, .5), (10, .25), (30, .35), (39.5, .9), (40.2, 0), (60, 0)]) * 0.12
pad *= env([(0, 0), (2, .5), (10, .6), (30, .75), (39.5, 1.0), (41, .9), (50, 1.15), (58.5, 1.0), (60, 0)]) * 0.12
pl *= env([(0, .6), (10, .8), (40, 1.0), (50, 1.1), (60, .5)]) * 0.17
bl *= 0.17; kk *= 0.25 * 1.0; lead *= 0.17
sub = np.sin(2 * np.pi * 41.2 * t) * env([(0, 0), (4, .5), (30, .5), (40, .3), (45, 0), (60, 0)]) * 0.12
mix = pad + pl + bl + kk + lead + air + sub
mix *= env([(0, 0), (1.5, 1), (58.5, 1), (60, 0)])
mix = mix / np.max(np.abs(mix)) * 0.6
d = int(0.012 * SR)
st = np.stack([mix, np.concatenate([np.zeros(d), mix[:-d]]) * 0.97], 1)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype('<i2').tobytes())
print('music ok')
