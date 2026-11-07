#!/usr/bin/env python3
"""
Decode arbitrary windows of the audio (second opinion / different boundaries).

    python3 -B -I asr_window.py INPUT.mp4 MODEL_DIR START,END [START,END ...]

Run it with both turbo and large-v3 on the same overlapping windows around every price or
name that will be displayed; use the consensus.
"""
import sys, subprocess, numpy as np, sherpa_onnx, os
V, M = sys.argv[1], sys.argv[2]
wins=[tuple(map(float,w.split(","))) for w in sys.argv[3:]]
raw=subprocess.run(["ffmpeg","-v","error","-i",V,"-vn","-ac","1","-ar","16000","-f","f32le","-"],capture_output=True,check=True).stdout
a=np.frombuffer(raw,np.float32); sr=16000
P=os.path.basename(M.rstrip("/")).replace("sherpa-onnx-whisper-","")
rec=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{M}/{P}-encoder.int8.onnx",decoder=f"{M}/{P}-decoder.int8.onnx",tokens=f"{M}/{P}-tokens.txt",language="ms",task="transcribe",num_threads=4)
for s,e in wins:
    st=rec.create_stream(); st.accept_waveform(sr,a[int(s*sr):int(e*sr)]); rec.decode_stream(st)
    print(f"[{P}] {s:6.2f}-{e:6.2f}  {st.result.text.strip()}")
