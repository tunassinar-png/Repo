"""Procedural placeholder sound bed (rain, drone, score) for the 60 s animatic.
Original synthesis, no samples. Usage: python3 make_audio.py out.wav"""
import sys, wave
import numpy as np

SR, T = 48000, 60
N = SR * T
t = np.arange(N) / SR
rng = np.random.default_rng(7)

def env(points):
    xs, ys = zip(*points)
    return np.interp(t, xs, ys)

def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if lo: m *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)   # high-pass
    if hi: m *= 1 / (1 + (f / hi) ** 4)                   # low-pass
    return np.fft.irfft(X * m, len(x))

def norm(x):
    return x / (np.max(np.abs(x)) + 1e-9)

# --- rain: hiss + droplet texture, intensity follows the scenes ---
hiss = norm(fft_filter(rng.standard_normal(N), lo=1500, hi=9000))
drops = np.zeros(N)
idx = rng.integers(0, N, 9000)
drops[idx] = rng.uniform(0.3, 1, len(idx))
drops = norm(fft_filter(drops, lo=800, hi=6000))
rain_env = env([(0, .02), (5, .05), (8, .35), (12, .75), (30, .9), (45, .85), (50, .55), (57, .08), (60, 0)])
rain = (0.8 * hiss + 0.5 * drops) * rain_env

# distant wind in orbit scene
wind = norm(fft_filter(rng.standard_normal(N), lo=60, hi=500)) * env([(0, .25), (6, .2), (10, 0), (60, 0)])

# --- thunder rumbles ---
thunder = np.zeros(N)
for s in (21, 33.5, 44):
    i = int(s * SR); L = 4 * SR
    seg = norm(fft_filter(rng.standard_normal(L), hi=120)) * np.exp(-np.arange(L) / (1.3 * SR))
    thunder[i:i + L] += seg[:N - i]

# --- score: D minor tension, resolves to D major at 50 s ---
def tone(freq, harm=(1, .5, .25), vib=0.0):
    ph = 2 * np.pi * freq * t + vib * np.sin(2 * np.pi * 5 * t)
    return sum(a * np.sin(ph * (k + 1)) for k, a in enumerate(harm))

drone = (tone(73.42) + 0.7 * tone(110.0, (1, .3)) + 0.5 * tone(146.83, (1, .3), vib=.3))
drone *= env([(0, 0), (5, .2), (12, .45), (30, 1), (49, 1), (51, 0), (60, 0)]) * 0.25
drone *= 1 + 0.08 * np.sin(2 * np.pi * 0.11 * t)

bpm = 68; beat = 60 / bpm
pulse = np.sin(2 * np.pi * 36.71 * t) * (0.5 + 0.5 * np.cos(2 * np.pi * t / beat)) ** 3
pulse *= env([(0, 0), (10, 0), (14, .5), (30, .8), (48, .9), (50, 0), (60, 0)]) * 0.3

piano = np.zeros(N)                      # single pedal note, D4, bars of 4 beats
for s in np.arange(1, 10, 4 * beat):
    i = int(s * SR); L = 3 * SR
    tt = np.arange(L) / SR
    piano[i:i + L] += (np.sin(2 * np.pi * 293.66 * tt) + .3 * np.sin(2 * np.pi * 587.3 * tt)) * np.exp(-tt * 1.4)
piano *= 0.12

ost = np.zeros(N)                        # low ostinato, 8ths, 30-50 s
notes = [146.83, 220.0, 174.61, 220.0]   # D3 A3 F3 A3
step = beat / 2
for n, s in enumerate(np.arange(30, 50, step)):
    i = int(s * SR); L = int(step * 1.6 * SR)
    tt = np.arange(L) / SR
    f = notes[n % 4]
    ost[i:i + L] += (np.sin(2 * np.pi * f * tt) + .4 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 5)
ost *= env([(30, .0), (36, .5), (49, .9), (50, 0), (60, 0)]) * 0.14

resolve = sum(tone(f, (1, .35, .15), vib=.25) for f in (146.83, 185.0, 220.0, 293.66))
resolve *= env([(0, 0), (50, 0), (52.5, .8), (56, .7), (59.5, 0), (60, 0)]) * 0.1

mix = (rain * 0.5 + wind * 0.25 + thunder * 0.5 + drone + pulse + piano + ost + resolve)
fade = env([(0, 0), (.4, 1), (59.4, 1), (60, 0)])
mix *= fade
mix = mix / np.max(np.abs(mix)) * 0.7

# slight stereo width via tiny delay on right channel
d = int(0.012 * SR)
left = mix
right = np.concatenate([np.zeros(d), mix[:-d]]) * 0.98
st = np.stack([left, right], 1)
pcm = (st * 32767).astype('<i2')
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('ok')
