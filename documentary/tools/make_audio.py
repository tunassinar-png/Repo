"""Generate the 60s soundtrack (ambient pad + bells + pop SFX + whooshes) from src/timeline.json."""
import json, wave, numpy as np, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
tl = json.loads((root / 'src/timeline.json').read_text())
SR = 44100
DUR = tl['total'] / tl['fps']
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)
L = np.zeros(N); R = np.zeros(N)

def add(sig, at, pan=0.0, gain=1.0):
    i = int(at * SR); j = min(N, i + len(sig))
    if i >= N or j <= i: return
    s = sig[: j - i] * gain
    L[i:j] += s * (1 - max(0, pan)); R[i:j] += s * (1 + min(0, pan))

def hz(m): return 440.0 * 2 ** ((m - 69) / 12)

# --- pad: Am - F - C - G, 15s each, slow attack, detuned saws smoothed
chords = [[57, 60, 64], [53, 57, 60], [48, 55, 60, 64], [55, 59, 62]]
for k, ch in enumerate(chords):
    d = 15.0; n = int(SR * (d + 2)); tt = np.arange(n) / SR
    env = np.minimum(1, tt / 3.5) * np.minimum(1, (d + 2 - tt) / 3.5)
    sig = np.zeros(n)
    for m in ch:
        for det in (-0.07, 0.0, 0.07):
            f = hz(m) * 2 ** (det / 12)
            sig += np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * 2 * f * tt + 0.7) + 0.12 * np.sin(2 * np.pi * 3 * f * tt)
    sig *= env * 0.045 / len(ch)
    add(sig, k * d, 0.0)
# sub bass root following chord
for k, ch in enumerate(chords):
    d = 15.0; n = int(SR * d); tt = np.arange(n) / SR
    env = np.minimum(1, tt / 2) * np.minimum(1, (d - tt) / 2)
    add(np.sin(2 * np.pi * hz(ch[0] - 24) * tt) * env * 0.10, k * d)

# --- bell arpeggio (sparse, scale-aware)
def bell(m, d=2.4):
    n = int(SR * d); tt = np.arange(n) / SR
    f = hz(m)
    s = (np.sin(2 * np.pi * f * tt) + 0.5 * np.sin(2 * np.pi * 2.76 * f * tt) * np.exp(-tt * 5) + 0.25 * np.sin(2 * np.pi * 5.4 * f * tt) * np.exp(-tt * 9))
    return s * np.exp(-tt * 2.2) * np.minimum(1, tt / 0.004)
arp = [[69, 72, 76, 81], [65, 69, 72, 77], [72, 76, 79, 84], [71, 74, 79, 83]]
for k, notes in enumerate(arp):
    for i in range(8):
        at = k * 15 + 1.0 + i * 1.8
        if at > DUR - 3: continue
        add(bell(notes[(i * 3) % len(notes)]), at, pan=(-0.5 if i % 2 else 0.5), gain=0.045 + 0.012 * (i % 3 == 0))

# --- soft heartbeat pulse in chapters 2-5 (sec 12-52), reinforces tension
def thump(d=0.35):
    n = int(SR * d); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * (52 + 40 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 12)
b = 12.0
while b < 52:
    add(thump(), b, gain=0.16); add(thump(), b + 0.26, gain=0.09); b += 1.0

# --- pop SFX per popup (rising blip + sparkle)
def pop(d=0.5):
    n = int(SR * d); tt = np.arange(n) / SR
    f = 380 + 900 * np.exp(-tt * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-tt * 14)
    s += 0.4 * bell(88, d)[:n] * 2.2
    return s
for p in tl['popups']:
    at = p['at'] / tl['fps']
    add(pop(), at, gain=0.22)
    # pop-out tick
    add(pop(0.25)[::-1] * 0.4, (p['at'] + p['dur']) / tl['fps'], gain=0.08)

# --- whoosh at scene changes (filtered noise sweep)
def whoosh(d=0.9):
    n = int(SR * d); tt = np.arange(n) / SR
    x = rng.standard_normal(n)
    # crude moving-average lowpass sweeping open
    out = np.zeros(n); y = 0.0
    for i in range(n):
        a = 0.02 + 0.45 * (i / n) ** 1.5
        y += a * (x[i] - y); out[i] = y
    env = np.sin(np.pi * tt / d) ** 2
    return out * env
for s in tl['scenes'][1:]:
    add(whoosh(), s['from'] / tl['fps'] - 0.45, gain=0.35)

# --- opening riser + final fade chime
n = int(SR * 2.0); tt = np.arange(n) / SR
add(np.sin(2 * np.pi * (200 + 600 * (tt / 2) ** 2) * tt) * (tt / 2) ** 2 * 0.05, 0.0)
add(bell(81, 4) * 0.08, DUR - 4.2)

# --- master: fades, gentle stereo width, normalise
fade = np.minimum(1, t / 1.5) * np.minimum(1, (DUR - t) / 2.0)
L *= fade; R *= fade
d = int(0.013 * SR)
R2 = np.concatenate([np.zeros(d), R[:-d]]); L2 = np.concatenate([np.zeros(d), L[:-d]])
L = 0.8 * L + 0.2 * R2; R = 0.8 * R + 0.2 * L2
peak = max(np.abs(L).max(), np.abs(R).max())
L = np.tanh(L / peak * 1.1) * 0.85; R = np.tanh(R / peak * 1.1) * 0.85
pcm = (np.stack([L, R], 1) * 32767).astype('<i2')
out = root / 'public/music.wav'
with wave.open(str(out), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('wrote', out, f'{DUR:.1f}s')
