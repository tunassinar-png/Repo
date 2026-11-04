"""Mix sound bed + narration with ducking. Usage: mix.py bed.wav vo.wav out.wav"""
import sys, wave
import numpy as np, cv2


def rd(p):
    with wave.open(p) as w:
        n, ch = w.getnframes(), w.getnchannels()
        x = np.frombuffer(w.readframes(n), '<i2').astype(np.float32) / 32768
        return x.reshape(-1, ch), w.getframerate()


bed, sr = rd(sys.argv[1]); vo, _ = rd(sys.argv[2])
n = min(len(bed), len(vo))
bed, vo = bed[:n], vo[:n, 0]
env = np.abs(vo)
k = int(0.05 * sr)
env = np.convolve(env, np.ones(k) / k, 'same')
act = np.clip(env / (np.percentile(env, 97) + 1e-9) * 3, 0, 1)
act = cv2.GaussianBlur(act.astype(np.float32).reshape(1, -1), (0, 0), sigmaX=0.18 * sr).ravel()
act = np.clip(act * 1.6, 0, 1)
duck = 1 - 0.62 * act
out = bed * duck[:, None] + vo[:, None] * 1.15
out = out / max(1.0, np.max(np.abs(out)) / 0.89)
with wave.open(sys.argv[3], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((out * 32767).astype('<i2').tobytes())
print('mixed', n / sr, 's')
