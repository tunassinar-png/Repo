"""Warm, reflective score that follows the chapters in src/timeline.json -> public/music.wav
tension (struggle/night) -> reverence (verse) -> lift (formula) -> gentle resolve (end).
Needs numpy + scipy."""
import json, pathlib, wave
import numpy as np
from scipy.signal import butter, lfilter, fftconvolve

root = pathlib.Path(__file__).resolve().parent.parent
tl = json.loads((root / 'src/timeline.json').read_text())
FPS = tl['fps']; SR = 44100; DUR = tl['total'] / FPS; N = int(SR * DUR)
BPM = 72; BEAT = 60 / BPM
rng = np.random.default_rng(5)
L = np.zeros(N); R = np.zeros(N)
bt = np.arange(N) / SR

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def lp(x, f, o=2): b, a = butter(o, f / (SR / 2), 'low'); return lfilter(b, a, x)
def hp(x, f, o=2): b, a = butter(o, f / (SR / 2), 'high'); return lfilter(b, a, x)
def tt(d): return np.arange(int(SR * d)) / SR
def saw(f, t): return 2 * ((f * t) % 1.0) - 1
def add(sig, at, pan=0.0, gain=1.0, bus=None):
    i = int(at * SR); j = min(N, i + len(sig))
    if i >= N or j <= i or i < 0: return
    s = sig[: j - i] * gain
    L[i:j] += s * (1 - max(0, pan)); R[i:j] += s * (1 + min(0, pan))

# scene intensity envelope (smooth between chapters)
INT = {'hook': .65, 'struggle': .7, 'night': .5, 'prayer': .8, 'verse': .6, 'myth': .8, 'balance': .85, 'formula': 1.0, 'end': .75}
pts_t, pts_v = [0.0], [INT[tl['scenes'][0]['id']]]
for s in tl['scenes'][1:]:
    t0 = s['from'] / FPS
    pts_t += [t0 - 0.8, t0 + 0.8]; pts_v += [pts_v[-1], INT[s['id']]]
pts_t.append(DUR); pts_v.append(pts_v[-1])
inten = np.interp(bt, pts_t, pts_v)
def scene_at(t):
    cur = tl['scenes'][0]
    for s in tl['scenes']:
        if s['from'] / FPS <= t: cur = s
    return cur['id']

# --- chords (Dm Bb F C), 8 beats each
chords = [[50, 53, 57], [46, 50, 53], [53, 57, 60], [48, 52, 55]]
roots = [38, 34, 41, 36]
CH = 8 * BEAT
nch = int(np.ceil(DUR / CH)) + 1

# pad
for k in range(nch):
    ch = chords[k % 4]; d = CH + 1.2; t = tt(d); sig = np.zeros(len(t))
    for m in ch + [ch[0] + 12]:
        for det in (-0.1, 0.0, 0.1):
            sig += saw(hz(m) * 2 ** (det / 12), t)
    env = np.minimum(1, t / 1.6) * np.minimum(1, (d - t) / 1.4)
    sig = lp(sig, 1500) * env * 0.045 / 4
    i = int(k * CH * SR); j = min(N, i + len(sig))
    if i < N:
        seg = sig[: j - i] * inten[i:j]
        L[i:j] += seg; R[i:j] += seg
    # drone
    t2 = tt(CH + 0.5); dr = np.sin(2 * np.pi * hz(roots[k % 4]) * t2) * np.minimum(1, t2 / 1.2) * np.minimum(1, (CH + 0.5 - t2) / 1.0)
    j2 = min(N, i + len(dr))
    if i < N:
        seg = dr[: j2 - i] * 0.11 * inten[i:j2]; L[i:j2] += seg; R[i:j2] += seg

def pluck(m, d=1.4):
    t = tt(d); f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 6) + 0.15 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 9)
    return s * np.exp(-t * 3.2) * np.minimum(1, t / 0.003)
def bell(m, d=2.6):
    t = tt(d); f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t * 5) + 0.25 * np.sin(2 * np.pi * 5.4 * f * t) * np.exp(-t * 9)
    return s * np.exp(-t * 2.0) * np.minimum(1, t / 0.004)
def thump(d=0.4):
    t = tt(d); return np.sin(2 * np.pi * (48 + 40 * np.exp(-t * 28)) * t) * np.exp(-t * 11)
def rain(d):
    t = tt(d); return hp(lp(rng.standard_normal(len(t)), 7000), 1800) * np.minimum(1, t / 1.0) * np.minimum(1, (d - t) / 1.0)

# arpeggio / bells / heartbeat per beat
nbeats = int(DUR / BEAT)
for bi in range(nbeats):
    t0 = bi * BEAT; sid = scene_at(t0); ci = int(t0 // CH) % 4; ch = chords[ci]
    v = float(inten[min(N - 1, int(t0 * SR))])
    if t0 > DUR - 3: continue
    if sid in ('struggle', 'night'):
        if bi % 2 == 0: add(thump(), t0, gain=0.34 * v); add(thump(), t0 + 0.28, gain=0.18 * v)
        if sid == 'night' and bi % 2 == 1: add(pluck(ch[(bi // 2) % 3] + 24, 2.0), t0, pan=0.3, gain=0.10)
        if sid == 'struggle' and bi % 4 == 0: add(pluck(ch[0] + 12, 2.0), t0, pan=-0.2, gain=0.09)
    elif sid in ('hook', 'prayer', 'balance', 'myth'):
        for q in range(2):
            n = ch[(bi + q) % 3] + 12 + (12 if (bi + q) % 4 == 3 else 0)
            add(pluck(n), t0 + q * BEAT / 2, pan=(0.35 if q else -0.35), gain=0.10 * v)
        if sid in ('balance', 'myth') and bi % 2 == 0: add(thump(), t0, gain=0.22 * v)
    elif sid == 'verse':
        if bi % 4 == 0: add(bell(ch[2] + 24, 3.0), t0, pan=0.25, gain=0.075)
        if bi % 4 == 2: add(bell(ch[0] + 24, 3.0), t0, pan=-0.25, gain=0.055)
    elif sid in ('formula', 'end'):
        for q in range(4):
            n = ch[(bi * 2 + q) % 3] + 24 + (12 if q == 3 else 0)
            add(pluck(n, 1.2), t0 + q * BEAT / 4 * 1, pan=(0.4 if q % 2 else -0.4), gain=(0.12 if sid == 'formula' else 0.075) * v)
        if sid == 'formula' and bi % 2 == 0: add(thump(0.5), t0, gain=0.30)

# rain during the myth chapter
for s in tl['scenes']:
    if s['id'] == 'myth':
        d = s['dur'] / FPS; r = rain(d); add(r, s['from'] / FPS, gain=0.05); add(r[::-1], s['from'] / FPS, pan=0.5, gain=0.03)

# chapter transitions: soft bell + swell
for s in tl['scenes'][1:]:
    t0 = s['from'] / FPS
    add(bell(74 if s['id'] != 'night' else 69, 2.4), t0, gain=0.10)
    sw = hp(lp(rng.standard_normal(int(SR * 1.2)), 3500), 400) * np.linspace(0, 1, int(SR * 1.2)) ** 2
    add(sw, t0 - 1.2, gain=0.05)
# opening + the "keberkatan" lift + final chime
add(bell(62, 4.0), 0.3, gain=0.12)
fs = [s for s in tl['scenes'] if s['id'] == 'formula'][0]
kw = [w for w in fs['lines'][1]['words'] if w['w'].lower().startswith('keberkatan')]
t_k = (kw[0]['s'] if kw else fs['lines'][1]['start']) / FPS
for i, m in enumerate([74, 78, 81, 86, 90]):
    add(bell(m, 3.0), t_k - 0.1 + i * 0.12, pan=(-0.4 + i * 0.2), gain=0.07)
add(bell(62, 5.0), DUR - 4.8, gain=0.10); add(bell(69, 5.0), DUR - 4.5, gain=0.07)

# --- reverb bus (wet 28%)
ir_t = tt(2.6)
irL = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 2.4); irR = rng.standard_normal(len(ir_t)) * np.exp(-ir_t * 2.4)
irL = lp(irL, 5500); irR = lp(irR, 5500)
irL /= np.abs(irL).sum() ** 0.5 * 18; irR /= np.abs(irR).sum() ** 0.5 * 18
wetL = fftconvolve(L, irL)[:N]; wetR = fftconvolve(R, irR)[:N]
L = L * 0.78 + wetL * 0.9; R = R * 0.78 + wetR * 0.9

fade = np.minimum(1, bt / 1.0) * np.minimum(1, (DUR - bt) / 2.6)
L *= fade; R *= fade
peak = max(np.abs(L).max(), np.abs(R).max())
L = np.tanh(L / peak * 1.4) * 0.8; R = np.tanh(R / peak * 1.4) * 0.8
pcm = (np.stack([L, R], 1) * 32767).astype('<i2')
with wave.open(str(root / 'public/music.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('wrote public/music.wav', f'{DUR:.1f}s')
