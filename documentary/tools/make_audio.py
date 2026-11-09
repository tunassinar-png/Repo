"""Generate the energetic 60s music bed (120 BPM) + pop/whoosh SFX from src/timeline.json -> public/music.wav.

Arrangement follows the chapters: build -> beat drops -> full drive -> climax -> outro.
Drums: kick / clap / hats. Bass + pad are sidechain-pumped on the kick. Plucked arp + lead on top.
"""
import json, wave, pathlib
import numpy as np
from scipy.signal import butter, lfilter

root = pathlib.Path(__file__).resolve().parent.parent
tl = json.loads((root / 'src/timeline.json').read_text())
SR = 44100
DUR = tl['total'] / tl['fps']
N = int(SR * DUR)
BPM = 120
BEAT = 60 / BPM
rng = np.random.default_rng(11)
L = np.zeros(N); R = np.zeros(N)


def add(sig, at, pan=0.0, gain=1.0):
    i = int(at * SR); j = min(N, i + len(sig))
    if i >= N or j <= i or i < 0: return
    s = sig[: j - i] * gain
    L[i:j] += s * (1 - max(0, pan)); R[i:j] += s * (1 + min(0, pan))


def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def lp(x, f, o=2): b, a = butter(o, f / (SR / 2), 'low'); return lfilter(b, a, x)
def hp(x, f, o=2): b, a = butter(o, f / (SR / 2), 'high'); return lfilter(b, a, x)
def bp(x, f1, f2, o=2): b, a = butter(o, [f1 / (SR / 2), f2 / (SR / 2)], 'band'); return lfilter(b, a, x)
def tt(d): return np.arange(int(SR * d)) / SR


def saw(f, t):
    return 2 * ((f * t) % 1.0) - 1


# ---------- drum + instrument voices ----------
def kick():
    t = tt(0.42)
    f = 46 + 110 * np.exp(-t * 38)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7.5)
    click = np.sin(2 * np.pi * 1800 * t) * np.exp(-t * 90) * 0.25
    return np.tanh((s + click) * 1.6)


def clap():
    t = tt(0.3)
    n = bp(rng.standard_normal(len(t)), 900, 6500)
    env = np.exp(-t * 22) + 0.7 * np.exp(-((t - 0.012) ** 2) / 2e-5) + 0.5 * np.exp(-((t - 0.026) ** 2) / 2e-5)
    return n * env


def hat(open_=False):
    t = tt(0.28 if open_ else 0.07)
    return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t * (14 if open_ else 70))


def crash(d=2.5):
    t = tt(d)
    return hp(rng.standard_normal(len(t)), 4500) * np.exp(-t * 2.0) * np.minimum(1, t / 0.005)


def boom(d=1.6):
    t = tt(d)
    f = 38 + 60 * np.exp(-t * 6)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.4)


def bass_note(m, d):
    t = tt(d)
    s = lp(saw(hz(m), t), 650) * 0.9 + np.sin(2 * np.pi * hz(m) * t) * 0.5
    env = np.minimum(1, t / 0.006) * np.exp(-t * 2.2) * np.minimum(1, (d - t) / 0.02)
    return s * env


def pluck(m, d=0.35):
    t = tt(d)
    f = hz(m)
    s = (saw(f, t) + saw(f * 1.006, t) * 0.8 + 0.5 * np.sign(np.sin(2 * np.pi * f * t))) / 2.3
    s = lp(s, 3200, 2)
    return s * np.exp(-t * 9) * np.minimum(1, t / 0.002)


def lead(m, d):
    t = tt(d)
    f = hz(m) * (1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t / 0.25))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.33 * np.sin(3 * ph) + 0.2 * np.sin(4 * ph)
    env = np.minimum(1, t / 0.01) * np.minimum(1, (d - t) / 0.06) * (0.75 + 0.25 * np.exp(-t * 3))
    return lp(s, 5500) * env


def bell(m, d=2.0):
    t = tt(d); f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t * 5) + 0.25 * np.sin(2 * np.pi * 5.4 * f * t) * np.exp(-t * 9)
    return s * np.exp(-t * 2.4) * np.minimum(1, t / 0.004)


def riser(d):
    t = tt(d)
    n = rng.standard_normal(len(t))
    # sweeping band: stack of progressively brighter filtered noise
    out = np.zeros(len(t))
    k = 6
    for i in range(k):
        seg = bp(n, 300 * (1.7 ** i), 700 * (1.7 ** i))
        w = np.clip((t / d) * k - i, 0, 1) * np.clip(k - (t / d) * k + i + 1, 0, 1)
        out += seg * w
    tone = np.sin(2 * np.pi * np.cumsum(200 + 1800 * (t / d) ** 2) / SR) * 0.25
    return (out * 0.8 + tone) * (t / d) ** 1.6


def pop(d=0.5):
    t = tt(d)
    s = np.sin(2 * np.pi * np.cumsum(380 + 900 * np.exp(-t * 28)) / SR) * np.exp(-t * 14)
    return s + 0.9 * bell(88, d)[: len(t)]


# ---------- arrangement ----------
chords = [[57, 60, 64], [53, 57, 60], [48, 55, 60, 64], [55, 59, 62]]   # Am F C G
roots = [45, 41, 36, 43]
CH = 8 * BEAT   # 4 s per chord
bounds = [s['from'] / tl['fps'] for s in tl['scenes']] + [DUR]   # 0,5,12,22,32,42,52,60


def section(t):
    for i in range(len(bounds) - 1):
        if bounds[i] <= t < bounds[i + 1]: return i
    return len(bounds) - 2


pump = np.ones(N)   # kick-driven sidechain envelope for bass/pad
beat_t = np.arange(0, DUR, BEAT)
bt = np.arange(N) / SR
ph = (bt % BEAT) / BEAT
pump_curve = 1 - 0.75 * np.exp(-ph * 7)          # dips on every beat, recovers

# pads (bright detuned saws, pumped)
pad_L = np.zeros(N); pad_R = np.zeros(N)
for k in range(int(np.ceil(DUR / CH))):
    ch = chords[k % 4]; d = CH + 0.6; t = tt(d)
    sig = np.zeros(len(t))
    for m in ch:
        for det in (-0.09, 0.0, 0.09):
            sig += saw(hz(m) * 2 ** (det / 12), t)
    env = np.minimum(1, t / 0.5) * np.minimum(1, (d - t) / 0.6)
    sig = lp(sig, 2400) * env * 0.05 / len(ch)
    i = int(k * CH * SR); j = min(N, i + len(sig))
    if i < N: pad_L[i:j] += sig[: j - i]; pad_R[i:j] += sig[: j - i]
L += pad_L * pump_curve * 1.0; R += pad_R * pump_curve * 1.0

# per-beat events
for bi, t0 in enumerate(beat_t):
    sec = section(t0)
    ci = int(t0 // CH) % 4
    ch, rt = chords[ci], roots[ci]
    kick_on = t0 >= 2.0 and t0 < 57.0 and not (sec == 0 and t0 < 4.0 and bi % 2)
    if kick_on: add(kick(), t0, gain=0.95 if t0 >= 5 else 0.6)
    if sec >= 1 and t0 < 57:
        # off-beat hats (8ths); 16ths in drive sections
        add(hat(), t0 + BEAT / 2, pan=0.3, gain=0.22)
        if sec in (4, 5):
            add(hat(), t0 + BEAT / 4, pan=-0.3, gain=0.12); add(hat(), t0 + 3 * BEAT / 4, pan=0.3, gain=0.12)
        if bi % 4 == 3: add(hat(True), t0 + BEAT / 2, gain=0.16)
        # bass: root 8ths with octave jumps
        for h in range(2):
            m = rt + (12 if (bi + h) % 4 == 3 else 0)
            add(bass_note(m, BEAT / 2 * 0.92), t0 + h * BEAT / 2, gain=0.55 if sec != 6 else 0.4)
    if sec >= 2 and t0 < 57 and bi % 2 == 1:
        add(clap(), t0, gain=0.5)
    # plucked 16th arp
    if sec >= 1 and t0 < 56:
        seq = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 24 if sec >= 4 else ch[1] + 12]
        for q in range(4):
            n = seq[(q + bi) % 4]
            add(pluck(n), t0 + q * BEAT / 4, pan=(-0.45 if q % 2 else 0.45), gain=(0.13 if sec in (1, 6) else 0.19))
    # lead melody in sections 3 and 5 (and light echo in 4)
    if sec in (3, 5) and bi % 2 == 0:
        mel = [ch[2] + 12, ch[1] + 12, ch[0] + 24, ch[1] + 12]
        n = mel[(bi // 2) % 4]
        add(lead(n, BEAT * 1.8), t0, pan=0.1, gain=0.10)
        add(lead(n, BEAT * 1.8), t0 + BEAT * 0.75, pan=-0.35, gain=0.04)

# opening hit + title riser
add(boom(), 0.0, gain=0.7); add(crash(3), 0.0, gain=0.22)
add(riser(2.0), 3.0, gain=0.35)
# chapter transitions: riser into impact (boom + crash) on the boundary
for b in bounds[1:-1]:
    add(riser(1.5), b - 1.5, gain=0.30)
    add(boom(1.4), b, gain=0.55)
    add(crash(2.2), b, gain=0.20)
# pop SFX on pop-ups
for p in tl['popups']:
    at = p['at'] / tl['fps']
    add(pop(), at, gain=0.20)
    add(pop(0.25)[::-1] * 0.4, (p['at'] + p['dur']) / tl['fps'], gain=0.07)
# final chime + crash
add(bell(81, 4) * 0.10, DUR - 3.2)
add(crash(3), DUR - 3.0, gain=0.18)

# ---------- master ----------
# kick-sidechain on everything except drums is already in pads; apply gentle global pump (light)
fade = np.minimum(1, bt / 0.3) * np.minimum(1, (DUR - bt) / 2.4)
L *= fade; R *= fade
d = int(0.012 * SR)
R2 = np.concatenate([np.zeros(d), R[:-d]]); L2 = np.concatenate([np.zeros(d), L[:-d]])
L = 0.82 * L + 0.18 * R2; R = 0.82 * R + 0.18 * L2
peak = max(np.abs(L).max(), np.abs(R).max())
L = np.tanh(L / peak * 1.8) * 0.9; R = np.tanh(R / peak * 1.8) * 0.9   # glue + loudness
pcm = (np.stack([L, R], 1) * 32767).astype('<i2')
out = root / 'public/music.wav'
with wave.open(str(out), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('wrote', out, f'{DUR:.1f}s @ {BPM} BPM')
