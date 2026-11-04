"""Narration (Malay TTS) + sound bed mix. Usage: audio.py out.wav"""
import sys, os, subprocess, wave, tempfile
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import tts_ms

VO = [
 "Bayangkan hujan turun setiap hari, tanpa henti, di seluruh dunia. Dari angkasa, Bumi diselubungi sistem ribut yang tidak lagi reda.",
 "Dalam beberapa hari, sistem saliran bandar tidak lagi mampu menampung. Sungai melimpah, jalan raya menjadi terusan, dan jutaan penduduk terkepung.",
 "Tanah yang tepu tidak dapat menyerap lagi. Akar tanaman kekurangan oksigen, tuaian reput, dan bekalan makanan mula terancam.",
 "Air meresap ke dalam cerun dan melemahkan tanah. Tanah runtuh menimbus jalan, memusnahkan jambatan, dan memutuskan bekalan.",
 "Habitat ditenggelamkan atau terhakis. Haiwan kehilangan tempat berlindung, dan terumbu karang ditimbus lumpur serta air tawar.",
 "Ini hanyalah senario hipotesis. Namun ia mengingatkan kita: kehidupan bergantung pada keseimbangan kitaran air yang rapuh.",
]
SR = 48000


def read(p):
    with wave.open(p) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32) / 32768
        return x, w.getframerate(), w.getnchannels()


def voice(text, tmp):
    pitch_f = 0.9
    for rate in range(130, 270, 8):
        x = tts_ms.synth(text, voice="ms+m3", rate=rate, pitch=16, rng_=22)
        if len(x) / tts_ms.SR / pitch_f <= 8.6:
            break
    raw = os.path.join(tmp, 'raw.wav')
    with wave.open(raw, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(tts_ms.SR)
        w.writeframes((x * 32767).astype('<i2').tobytes())
    dur = len(x) / tts_ms.SR
    tempo = max(1.0, (dur / pitch_f) / 8.7)
    out = os.path.join(tmp, 'proc.wav')
    af = (f"asetrate={tts_ms.SR * pitch_f},aresample={SR},atempo={tempo:.4f},highpass=f=75,"
          "equalizer=f=150:t=q:w=1:g=4,equalizer=f=2800:t=q:w=1.2:g=-3,lowpass=f=7000,"
          "acompressor=threshold=0.1:ratio=3:attack=5:release=90:makeup=2,aecho=0.8:0.55:60:0.2")
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', raw, '-af', af, '-ar', str(SR), '-ac', '1', out], check=True)
    y, sr, _ = read(out)
    return y, dur, tempo


def main():
    out = sys.argv[1]
    track = np.zeros(SR * 60, np.float32)
    with tempfile.TemporaryDirectory() as tmp:
        for k, text in enumerate(VO):
            y, dur, tempo = voice(text, tmp)
            start = int((k * 10 + 0.6) * SR)
            n = min(len(y), SR * 9 - int(0.6 * SR) + int(0.4 * SR))
            track[start:start + n] += y[:n]
            print(f'scene {k+1}: raw {dur:.1f}s -> {len(y)/SR:.1f}s (tempo x{tempo:.2f})')
    track = track / (np.max(np.abs(track)) + 1e-9) * 0.85
    with wave.open(out, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((track * 32767).astype('<i2').tobytes())


if __name__ == '__main__':
    main()
