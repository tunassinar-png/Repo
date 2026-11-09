"""Synthesise the narration offline (sherpa-onnx + Piper id_ID model) into vo/NN.wav.
Usage: python3 tools/make_vo.py <model_dir> [speed]   (speed < 1.0 = faster; default 1.0)"""
import json, pathlib, sys, wave
import numpy as np, sherpa_onnx

root = pathlib.Path(__file__).resolve().parent.parent
md = pathlib.Path(sys.argv[1]); speed = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
tl = json.loads((root / 'src/timeline.json').read_text())
cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(vits=sherpa_onnx.OfflineTtsVitsModelConfig(
    model=str(next(md.glob('*.onnx'))), tokens=str(md / 'tokens.txt'), data_dir=str(md / 'espeak-ng-data'),
    noise_scale=0.6, noise_scale_w=0.7, length_scale=speed), num_threads=4), max_num_sentences=1)
tts = sherpa_onnx.OfflineTts(cfg)
out = root / 'vo'; out.mkdir(exist_ok=True)
for v in tl['vo']:
    a = tts.generate(v['text'].replace('…', ','), sid=0, speed=1.0)
    x = np.asarray(a.samples, dtype=np.float32)
    x = x / max(1e-6, np.abs(x).max()) * 0.9
    with wave.open(str(out / f"{v['id']}.wav"), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(a.sample_rate)
        w.writeframes((x * 32767).astype('<i2').tobytes())
    print(v['id'], f"{len(x)/a.sample_rate:.1f}s (slot {v['max']}s)")
