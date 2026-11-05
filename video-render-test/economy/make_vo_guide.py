"""Scratch narration (Malay TTS) for timing only. Usage: make_vo_guide.py out.wav"""
import sys, os, subprocess, tempfile, wave
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'film'))
import tts_ms

VO = [
 (0.4, 8.8, "Gaji minimum naik kepada dua ribu ringgit. Adakah rakyat akan hidup lebih selesa? Atau harga barang pula yang akan meningkat?"),
 (10.4, 8.8, "Bagi pekerja, ini berita baik. Tetapi bagi majikan, kos pengeluaran meningkat. Sebahagian kos mungkin dipindahkan kepada pengguna melalui kenaikan harga barang."),
 (20.4, 8.8, "Pekerja asing juga menerima manfaat. Sebahagian pendapatan tambahan mungkin dihantar ke negara asal. Namun, mereka turut berbelanja dan menyumbang kepada ekonomi Malaysia."),
 (30.4, 8.8, "Bagaimana pula mereka yang tidak mendapat kenaikan gaji? Apabila harga makanan dan perkhidmatan meningkat, kuasa beli mereka boleh semakin terhakis."),
 (40.4, 8.8, "Namun, kenaikan gaji tidak semestinya menyebabkan inflasi berpanjangan. Peningkatan produktiviti dan kecekapan perniagaan boleh membantu mengawal kos."),
 (50.2, 7.8, "Akhirnya, yang penting bukan sekadar berapa tinggi gaji kita. Tetapi berapa banyak barang yang mampu kita beli. Gaji naik penting, kuasa beli rakyat lebih penting."),
]
SR = 48000


def voice(text, maxdur, tmp):
    pf = 0.9
    for rate in range(130, 300, 8):
        x = tts_ms.synth(text, voice="ms+m3", rate=rate, pitch=16, rng_=22)
        if len(x) / tts_ms.SR / pf <= maxdur - 0.1:
            break
    raw = os.path.join(tmp, 'r.wav'); out = os.path.join(tmp, 'p.wav')
    with wave.open(raw, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(tts_ms.SR); w.writeframes((x * 32767).astype('<i2').tobytes())
    tempo = max(1.0, len(x) / tts_ms.SR / pf / (maxdur - 0.1))
    af = (f"asetrate={tts_ms.SR * pf},aresample={SR},atempo={tempo:.4f},highpass=f=75,equalizer=f=150:t=q:w=1:g=4,"
          "equalizer=f=2800:t=q:w=1.2:g=-3,lowpass=f=7000,acompressor=threshold=0.1:ratio=3:attack=5:release=90:makeup=2,aecho=0.8:0.55:60:0.2")
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', raw, '-af', af, '-ar', str(SR), '-ac', '1', out], check=True)
    with wave.open(out) as w:
        return np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32) / 32768


track = np.zeros(SR * 60, np.float32)
with tempfile.TemporaryDirectory() as tmp:
    for k, (st, md, text) in enumerate(VO):
        y = voice(text, md, tmp)
        i = int(st * SR)
        n = min(len(y), len(track) - i)
        track[i:i + n] += y[:n]
        print(f'scene {k+1}: starts {st:.1f}s, length {len(y)/SR:.1f}s')
track = track / (np.max(np.abs(track)) + 1e-9) * 0.85
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((track * 32767).astype('<i2').tobytes())
