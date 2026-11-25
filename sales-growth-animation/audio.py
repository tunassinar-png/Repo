"""Synthesises a 6 s uplifting corporate / motivational instrumental (no samples, pure numpy).
120 BPM, C major:  C | G | F -> C   (hit on the zoom-out at 4.0 s, resolve on the final chord)."""
import numpy as np, wave, sys

import os
SR = 48000; DUR = float(os.environ.get('DUR', 6.0)); LONG = DUR > 7; XL = DUR > 9; HIT = float(os.environ.get('HIT', 4.0)); N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)

def env_adsr(n, a, d, s_, r, sustain_len=None):
    e = np.ones(n)
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, max(na, 1), endpoint=False)
    e[na:na + nd] = np.linspace(1, s_, max(nd, 1), endpoint=False)[:len(e[na:na + nd])]
    e[na + nd:] = s_
    if nr: e[-nr:] *= np.linspace(1, 0, nr)
    return e

def place(buf, sig, start, gain=1.0, pan=0.0):
    i = int(start * SR); sig = np.asarray(sig)
    j = min(N, i + len(sig))
    if j <= i: return
    l = gain * np.cos((pan + 1) * np.pi / 4); r = gain * np.sin((pan + 1) * np.pi / 4)
    buf[0, i:j] += sig[:j - i] * l; buf[1, i:j] += sig[:j - i] * r

def reverb(x, decay=1.7, mix=1.0):
    n = int(SR * decay)
    ir = rng.standard_normal(n) * np.exp(-np.arange(n) / (SR * decay / 4.5))
    ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))
    ir = np.convolve(ir, np.ones(24) / 24, mode='same')            # darker tail
    ir /= np.sqrt(np.sum(ir ** 2))
    L = len(x) + n
    X = np.fft.rfft(x, L); Y = np.fft.rfft(ir, L)
    return np.fft.irfft(X * Y, L)[:len(x)] * mix * 0.30

def saw_add(f, n, nharm_max=18, cutoff=3200):
    tt = np.arange(n) / SR
    out = np.zeros(n)
    for k in range(1, nharm_max + 1):
        if f * k > cutoff: break
        out += np.sin(2 * np.pi * f * k * tt) / k
    return out

pad  = np.zeros((2, N)); pluck = np.zeros((2, N)); bass = np.zeros((2, N))
drum = np.zeros((2, N)); lead  = np.zeros((2, N)); fx   = np.zeros((2, N))

# ---------------- harmony ------------------------------------------------
CH = [  # (start, end, chord midi notes, bass root)
    (0.0, 2.0, [48, 52, 55, 60, 64], 36),   # C
    (2.0, 4.0, [43, 47, 50, 55, 59, 62], 31),  # G
    (4.0, 5.0, [41, 45, 48, 53, 57, 60], 29),  # F
    (5.0, 6.0, [48, 52, 55, 60, 64, 67], 36),  # C (resolve)
]
SHORT = DUR < 5.5
if SHORT:   # 5 s: C | G | C(resolve)
    CH = [(0.0, 2.0, [48, 52, 55, 60, 64], 36), (2.0, 4.0, [43, 47, 50, 55, 59, 62], 31), (4.0, 5.0, [48, 52, 55, 60, 64, 67], 36)]
elif XL:   # 10 s: I - V - vi - IV - I, one bar = 2 s
    CH = [(0.0, 2.0, [48, 52, 55, 60, 64], 36), (2.0, 4.0, [43, 47, 50, 55, 59, 62], 31), (4.0, 6.0, [45, 48, 52, 57, 60, 64], 33), (6.0, 8.0, [41, 45, 48, 53, 57, 60], 29), (8.0, 10.0, [48, 52, 55, 60, 64, 67], 36)]
elif LONG:
    CH = CH[:2] + [(4.0, 6.0, [41, 45, 48, 53, 57, 60], 29), (6.0, 8.0, [48, 52, 55, 60, 64, 67], 36)]
for (a, b, notes, root) in CH:
    n = int((b - a) * SR) + int(0.25 * SR)
    for m in notes:
        for det, pan in ((-7, -0.6), (0, 0.0), (7, 0.6)):
            f = mtof(m) * 2 ** (det / 1200)
            sig = saw_add(f, n)
            e = env_adsr(n, 0.35 if a == 0 else 0.12, 0.2, 0.85, 0.22)
            place(pad, sig * e, a, 0.028, pan)

# ---------------- plucked arpeggio (8ths) --------------------------------
def pluck_note(f, dur=0.55):
    n = int(dur * SR); tt = np.arange(n) / SR
    sig = (np.sin(2*np.pi*f*tt) + .45*np.sin(2*np.pi*2*f*tt)*np.exp(-tt*9) + .25*np.sin(2*np.pi*3*f*tt)*np.exp(-tt*14)
           + .12*np.sin(2*np.pi*4*f*tt)*np.exp(-tt*20))
    return sig * np.exp(-tt * 6.5) * np.minimum(1, tt * 800)
arp_idx = [0, 1, 2, 3, 2, 1, 2, 3]
step = 0.25
k = 0
for (a, b, notes, root) in CH:
    tri = [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[0] + 24] if a < 4 else [notes[0] + 12, notes[1] + 12, notes[2] + 12, notes[3] + 12]
    tt0 = a
    while tt0 < b - 1e-6:
        note = tri[arp_idx[k % len(arp_idx)] % 4]
        vel = 0.45 + 0.55 * (tt0 / DUR)
        place(pluck, pluck_note(mtof(note)), tt0, 0.22 * vel, pan=-0.5 if k % 2 == 0 else 0.5)
        tt0 += step; k += 1

# ping-pong echo on plucks
echo = np.zeros_like(pluck); d = int(0.375 * SR)
for c, (dly, g) in enumerate(((d, .38), (2 * d, .2))):
    echo[0, dly:] += pluck[1, :-dly] * g; echo[1, dly:] += pluck[0, :-dly] * g
pluck += echo

# ---------------- bass --------------------------------------------------
for (a, b, notes, root) in CH:
    tt0 = a
    while tt0 < b - 1e-6:
        if tt0 >= 1.0:
            n = int(0.24 * SR); tt = np.arange(n) / SR; f = mtof(root)
            sig = (np.sin(2*np.pi*f*tt) + .3*np.sin(2*np.pi*2*f*tt)) * np.exp(-tt * 5) * np.minimum(1, tt * 500)
            place(bass, sig, tt0 + (0.25 if (int(round((tt0 - a) / 0.25)) % 2) else 0.0), 0.34 * min(1, (tt0 - 0.5) / 2))
        tt0 += 0.5

# ---------------- drums -------------------------------------------------
def kick(vel=1.0):
    n = int(0.42 * SR); tt = np.arange(n) / SR
    f = 46 + 110 * np.exp(-tt * 26); ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * np.exp(-tt * 9) + .25 * np.sin(ph * 2) * np.exp(-tt * 30)) * vel
def noise_hp(n, cutoff_k):  # crude high-pass noise = differenced white noise
    x = rng.standard_normal(n)
    for _ in range(cutoff_k): x = np.diff(x, prepend=0)
    return x / (np.max(np.abs(x)) + 1e-9)
def hat(vel=1.0, dec=45):
    n = int(0.09 * SR); tt = np.arange(n) / SR
    return noise_hp(n, 2) * np.exp(-tt * dec) * vel
def clap(vel=1.0):
    n = int(0.3 * SR); tt = np.arange(n) / SR
    x = noise_hp(n, 1) * np.exp(-tt * 22)
    for off in (0.0, 0.012, 0.025): x[int(off*SR):] += 0.6 * noise_hp(n - int(off*SR), 1) * np.exp(-tt[: n - int(off*SR)] * 60)
    return x * vel * 0.7

for beat in np.arange(0, DUR, 0.5):
    if beat >= 1.0 and not (4.0 > beat >= 3.5 and False):
        v = 0.55 if beat < 2.0 else 0.9
        place(drum, kick(v), beat, 0.55)
for beat in np.arange(2.0, DUR, 0.25):            # 8ths hats
    off = (int(round(beat / 0.25)) % 2) == 1
    place(drum, hat(0.55 if off else 0.35), beat, 0.14, pan=0.35)
for beat in (list(np.arange(HIT - 1.5, DUR, 1.0)) if XL else ((3.5, 4.5, 5.5, 6.5, 7.5) if LONG else (3.0, 3.5, 4.5, 5.0, 5.5))):             # backbeat claps
    place(drum, clap(0.8), beat, 0.26)
for tt0 in np.arange(HIT - 0.5, HIT, 0.125):       # snare-roll style build into the big moment
    place(drum, clap(0.4 + (tt0 - (HIT - 0.5)) * 1.2), tt0, 0.13)

# ---------------- FX: riser, impact, crash ------------------------------
n = int(1.0 * SR); tt = np.arange(n) / SR
riser = noise_hp(n, 1) * (tt / 1.0) ** 2.2
place(fx, riser, HIT - 1.0, 0.20, 0.0)
n = int(2.2 * SR); tt = np.arange(n) / SR
crash = noise_hp(n, 1) * np.exp(-tt * 2.4) * np.minimum(1, tt * 300)
place(fx, crash, HIT, 0.24, 0.0)
boom = np.sin(2*np.pi*(34 + 70*np.exp(-tt*6)).cumsum()/SR) * np.exp(-tt * 3.2)
place(fx, boom, HIT, 0.55, 0.0)
place(fx, crash * 0.7, HIT + 1.6 if SHORT else ((8.0 if XL else 6.0) if LONG else 5.0), 0.12 if not LONG else 0.2, 0.0)

# ---------------- lead / bell melody (target reveal) -------------------
def bell(f, dur):
    n = int(dur * SR); tt = np.arange(n) / SR
    sig = (np.sin(2*np.pi*f*tt) + .5*np.sin(2*np.pi*2.0*f*tt)*np.exp(-tt*4) + .3*np.sin(2*np.pi*3.01*f*tt)*np.exp(-tt*6) + .15*np.sin(2*np.pi*4.2*f*tt)*np.exp(-tt*9))
    return sig * np.exp(-tt * (2.2 if dur > 0.6 else 5)) * np.minimum(1, tt * 600)
mel = [(4.0, 84, .5), (4.25, 81, .4), (4.5, 84, .4), (4.75, 89, .4), (5.0, 88, .45), (5.25, 91, .45), (5.5, 96, 0.5)]
if SHORT and HIT > 3.5: mel = [(HIT, 84, .35), (HIT + .3, 88, .35), (HIT + .6, 96, 0.7)]
elif SHORT: mel = [(HIT, 84, .4), (HIT + .35, 88, .4), (HIT + .7, 91, .4), (HIT + 1.05, 96, 0.9)]
elif XL: mel = [(5.0, 84, .5), (5.5, 81, .5), (6.0, 84, .5), (6.5, 89, .5), (7.0, 88, .5), (7.5, 91, .6), (8.0, 96, 1.2)]
elif LONG: mel = [(4.0, 84, .5), (4.5, 81, .5), (5.0, 84, .5), (5.5, 89, .5), (6.0, 88, .5), (6.5, 91, .6), (7.0, 96, 0.9)]
for (st, m, dd) in mel:
    place(lead, bell(mtof(m), dd + .6), st, 0.19 if st < ((8.0 if XL else 7.0) if LONG else 5.5) else 0.22, pan=0.15 if m % 2 else -0.15)
# soft chime motif in the first scenes
for (st, m) in ((0.5, 76), (1.0, 79), (2.5, 83), (3.0, 79)):
    place(lead, bell(mtof(m), 0.8), st, 0.09, pan=-0.3)

# ---------------- sidechain-ish pump on pads/bass from the kick ---------
duck = np.ones(N)
for beat in np.arange(1.0, DUR, 0.5):
    i = int(beat * SR); m = int(0.22 * SR)
    duck[i:i + m] *= 1 - 0.45 * np.exp(-np.arange(min(m, N - i)) / (SR * 0.07))
pad *= duck; bass *= duck

# ---------------- mix ---------------------------------------------------
wet = np.zeros((2, N))
for ch in range(2):
    wet[ch] = reverb(pad[ch] * 1.0 + pluck[ch] * 0.8 + lead[ch] * 1.2, 1.7, 1.0)
mix = pad + pluck * 1.1 + bass * 1.2 + drum + lead * 1.1 + fx + wet * 0.8

if '--report' in sys.argv:
    for nm,b in (('pad',pad),('pluck',pluck),('bass',bass),('drum',drum),('lead',lead),('fx',fx),('wet',wet)):
        print(f'{nm:6s} rms={np.sqrt((b**2).mean()):.4f} peak={np.abs(b).max():.3f}')
    print('mix rms', np.sqrt((mix**2).mean()), 'peak', np.abs(mix).max())
# master: intro swell, outro fade, soft clip, normalise
swell = np.clip(t / 0.5, 0, 1) ** 0.5 * 0.3 + 0.7 * np.clip(t / 2.0, 0, 1)
mix *= np.where(t < 2.0, swell, 1.0)
fade_out = np.clip((DUR - t) / (0.9 if LONG else 0.55), 0, 1) ** 1.2
mix *= fade_out
mix *= np.clip(t / 0.01, 0, 1)
mix = np.tanh(mix * 1.2) / 1.2
# loudness-match to ~ -14 LUFS (streaming-friendly) then catch peaks with a soft limiter
rms = np.sqrt((mix ** 2).mean()); mix *= 0.14 / rms
mix = np.tanh(mix * 1.1) / 1.1
mix *= 0.89 / max(0.89, np.max(np.abs(mix)))

out = (np.clip(mix.T, -1, 1) * 32767).astype('<i2')
with wave.open(sys.argv[1] if len(sys.argv) > 1 else 'music.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes())
print('wrote', sys.argv[1] if len(sys.argv) > 1 else 'music.wav')
