"""Original documentary underscore, A minor, 72 BPM, 60 s. Low-level, serious. Usage: make_music.py out.wav"""
import sys, wave
import numpy as np

SR, T = 48000, 60
N = SR * T
t = np.arange(N) / SR
rng = np.random.default_rng(11)
BPM = 72; beat = 60 / BPM; bar = 4 * beat


def env(pts):
    xs, ys = zip(*pts)
    return np.interp(t, xs, ys)


def add(buf, sig, t0):
    i = int(t0 * SR)
    if i >= N:
        return
    n = min(len(sig), N - i)
    buf[i:i + n] += sig[:n]


def pluck(f, dur=1.4, amp=1.0):
    tt = np.arange(int(dur * SR)) / SR
    s = np.sin(2 * np.pi * f * tt) + .45 * np.sin(4 * np.pi * f * tt) + .2 * np.sin(6 * np.pi * f * tt)
    return s * np.exp(-tt * 4.2) * amp * np.minimum(1, tt * 400)


def kick(amp=1.0):
    tt = np.arange(int(0.5 * SR)) / SR
    f = 42 + 70 * np.exp(-tt * 24)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 7) * amp


def hat(amp=1.0):
    L = int(0.05 * SR)
    x = rng.standard_normal(L)
    x = np.diff(x, prepend=0)
    return x * np.exp(-np.arange(L) / (0.012 * SR)) * amp


CH = {
    'Am': [110.0, 164.81, 220.0, 261.63], 'F': [87.31, 130.81, 174.61, 220.0], 'C': [130.81, 196.0, 261.63, 329.63],
    'G': [98.0, 146.83, 196.0, 246.94], 'Dm': [146.83, 220.0, 293.66, 349.23], 'E': [82.41, 123.47, 164.81, 207.65],
}
prog = [(0, ['Am', 'F', 'Am', 'F']), (10, ['Am', 'F', 'C', 'G']), (20, ['Am', 'F', 'C', 'G']), (30, ['Dm', 'F', 'Am', 'E']),
        (40, ['Am', 'F', 'C', 'G']), (50, ['C', 'G', 'Am', 'F'])]


def chord_at(tm):
    for st, ch in reversed(prog):
        if tm >= st:
            k = int((tm - st) / bar) % len(ch)
            return ch[k]
    return 'Am'


pad = np.zeros(N); pl = np.zeros(N); kk = np.zeros(N); hh = np.zeros(N)
nbars = int(T / bar) + 1
for b in range(nbars):
    t0 = b * bar
    name = chord_at(t0 + 0.01)
    fr = CH[name]
    L = int((bar + 0.6) * SR)
    tt = np.arange(L) / SR
    sg = np.zeros(L)
    for j, f in enumerate(fr):
        sg += (np.sin(2 * np.pi * f * tt) + .3 * np.sin(4 * np.pi * f * tt * 1.001) + .12 * np.sin(6 * np.pi * f * tt)) * (0.9 if j == 0 else 0.6)
    sg *= np.minimum(1, tt / 0.9) * np.minimum(1, (L / SR - tt) / 0.7)
    add(pad, sg, t0)
    # arpeggio plucks (8th notes) from 10 s
    if t0 >= 9.9:
        seq = [fr[1] * 2, fr[2] * 2, fr[3] * 2, fr[2] * 2, fr[1] * 2, fr[3] * 2, fr[2] * 2, fr[3] * 2 * (1.0)]
        for k, f in enumerate(seq):
            tn = t0 + k * beat / 2
            add(pl, pluck(f, 1.1, 0.5 + 0.15 * (k % 2 == 0)), tn)
    else:
        # sparse piano-like notes in scene 1
        for k, f in enumerate([fr[3] * 2, fr[2] * 2]):
            add(pl, pluck(f, 2.0, 0.7), t0 + k * 2 * beat)
    # pulse and hats
    for k in range(4):
        tn = t0 + k * beat
        if 10 <= tn < 58:
            add(kk, kick(0.7 if k % 2 == 0 else 0.45), tn)
        if 20 <= tn < 56:
            add(hh, hat(0.5), tn + beat / 2)
            if tn >= 40:
                add(hh, hat(0.3), tn + beat / 4); add(hh, hat(0.3), tn + 3 * beat / 4)

# riser into scene 6 and tension swell in scene 5
nz = rng.standard_normal(N)
X = np.fft.rfft(nz); f_ = np.fft.rfftfreq(N, 1 / SR)
X *= 1 / (1 + (800 / np.maximum(f_, 1)) ** 4) / (1 + (f_ / 6000) ** 4)
riser = np.fft.irfft(X, N); riser /= np.max(np.abs(riser))
riser *= env([(0, 0), (44, 0), (49.6, .9), (50, 0), (60, 0)]) * 0.25
# resolution: soft bell notes in scene 6
bells = np.zeros(N)
for k, (tm, f) in enumerate([(52.0, 523.25), (54.0, 659.25), (56.0, 783.99), (58.0, 523.25)]):
    add(bells, pluck(f, 3.0, 0.5) , tm)

pad *= env([(0, 0), (1.5, .8), (40, 1.0), (49, 1.3), (50.5, 1.0), (58.5, .6), (60, 0)]) * 0.16
pl *= env([(0, .6), (10, .6), (20, .8), (40, 1.0), (50, .6), (60, .3)]) * 0.20
kk *= 0.5 * 0.35
hh *= 0.10
mix = pad + pl + kk + hh + riser + bells * 0.16
mix *= env([(0, 0), (0.6, 1), (58.5, 1), (60, 0)])
mix = mix / np.max(np.abs(mix)) * 0.55
d = int(0.011 * SR)
st = np.stack([mix, np.concatenate([np.zeros(d), mix[:-d]]) * 0.98], 1)
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype('<i2').tobytes())
print('music ok')
