"""Fit real narration (one audio file per scene) into the 60 s timeline.
 - trims silence, places each scene's voice at its start time, reports overflow,
 - rewrites subtitles.srt from the REAL durations, ducks the music, normalises to -14 LUFS.
Usage: fit_vo.py music_bed.wav OUTDIR scene1.mp3 scene2.mp3 ... scene6.mp3"""
import sys, os, subprocess, tempfile, wave
import numpy as np
from content import SCENES, srt_time

SR = 48000


def load(path, tmp):
    wav = os.path.join(tmp, os.path.basename(path) + '.wav')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-c:a', 'pcm_s16le', wav], check=True)
    with wave.open(wav) as w:
        return np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32) / 32768


def trim(x, db=-45, pad=0.06):
    thr = 10 ** (db / 20)
    env = np.convolve(np.abs(x), np.ones(480) / 480, 'same')
    idx = np.nonzero(env > thr)[0]
    if len(idx) == 0:
        return x
    a, b = max(0, idx[0] - int(pad * SR)), min(len(x), idx[-1] + int(pad * SR))
    return x[a:b]


def main():
    music_path, out = sys.argv[1], sys.argv[2]
    files = sys.argv[3:]
    assert len(files) == len(SCENES), f"perlu {len(SCENES)} fail suara (satu setiap babak), diberi {len(files)}"
    os.makedirs(out, exist_ok=True)
    track = np.zeros(SR * 60, np.float32)
    cues = []
    with tempfile.TemporaryDirectory() as tmp:
        for k, (p, s) in enumerate(zip(files, SCENES)):
            x = trim(load(p, tmp)); d = len(x) / SR; win = s['b'] - s['a']
            note = ''
            if d > win:
                note = f'  <-- LEBIH {d - win:.1f}s daripada tetingkap {win:.1f}s: pendekkan teks atau percepatkan bacaan'
            i = int(s['a'] * SR); n = min(len(x), len(track) - i); track[i:i + n] += x[:n]
            tot = sum(len(c) for c in s['subs']); t = s['a']
            for c in s['subs']:
                dd = d * len(c) / tot
                cues.append((t, t + dd - 0.05, c)); t += dd
            print(f'babak {k+1}: mula {s["a"]:.1f}s, panjang {d:.1f}s (tetingkap {win:.1f}s){note}')
    with open(os.path.join(out, 'subtitles_ikut_suara.srt'), 'w', encoding='utf-8') as f:
        for i, (a, b, c) in enumerate(cues, 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{c}\n\n")
    with wave.open(music_path) as w:
        m = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32).reshape(-1, w.getnchannels()) / 32768
    n = min(len(m), len(track)); m, v = m[:n], track[:n]
    env = np.convolve(np.abs(v), np.ones(int(0.05 * SR)) / int(0.05 * SR), 'same')
    act = np.clip(env / (np.percentile(env, 97) + 1e-9) * 3, 0, 1)
    k = int(0.35 * SR); act = np.convolve(act, np.hanning(k) / np.hanning(k).sum(), 'same')
    duck = 1 - 0.62 * np.clip(act * 1.6, 0, 1)
    mix = m * duck[:, None] + (v / (np.max(np.abs(v)) + 1e-9) * 0.85)[:, None] * 1.1
    mix = mix / max(1.0, np.max(np.abs(mix)) / 0.89)
    raw = os.path.join(out, 'audio_akhir_raw.wav')
    with wave.open(raw, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype('<i2').tobytes())
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', raw, '-af', 'loudnorm=I=-14:TP=-1.5:LRA=9', '-ar', '48000', os.path.join(out, 'audio_akhir.wav')], check=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', os.path.join(out, 'audio_akhir.wav'), '-c:a', 'libmp3lame', '-b:a', '256k', os.path.join(out, 'audio_akhir.mp3')], check=True)
    os.remove(raw)
    print('siap: audio_akhir.mp3, audio_akhir.wav, subtitles_ikut_suara.srt dalam', out)


if __name__ == '__main__':
    main()
