#!/usr/bin/env python3
"""
Word timing without word timestamps: decode growing prefixes of a phrase and note when each
word first appears (the word starts ~0.1-0.2 s before it shows up).

    python3 -B -I asr_prefix_scan.py INPUT.mp4 MODEL_DIR START,SCAN_FROM,SCAN_TO,STEP [...]

e.g. a phrase starting at 20.99 s: "20.99,22.6,23.9,0.15" prints the text decoded up to 22.6,
22.75, ... 23.9 s. Used to time every price word to about +/-0.1 s (RM5 lima 23.15 s, RM29
25.9 s, seringgit 29.55 s in the Ipoh day-1 video). ~1 s per decode with turbo on 4 cores.
"""
"""Decode growing prefixes of a phrase to see when each word first appears (timing)."""
import sys, subprocess, numpy as np, sherpa_onnx, os
V, M = sys.argv[1], sys.argv[2]
specs=[tuple(map(float,w.split(","))) for w in sys.argv[3:]]   # start,scan_from,scan_to,step
raw=subprocess.run(["ffmpeg","-v","error","-i",V,"-vn","-ac","1","-ar","16000","-f","f32le","-"],capture_output=True,check=True).stdout
a=np.frombuffer(raw,np.float32); sr=16000
P=os.path.basename(M.rstrip("/")).replace("sherpa-onnx-whisper-","")
rec=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{M}/{P}-encoder.int8.onnx",decoder=f"{M}/{P}-decoder.int8.onnx",tokens=f"{M}/{P}-tokens.txt",language="ms",task="transcribe",num_threads=4)
for s,f,t,step in specs:
    print(f"--- phrase starts {s}")
    x=f
    while x<=t+1e-6:
        st=rec.create_stream(); st.accept_waveform(sr,a[int(max(0,s-0.2)*sr):int(x*sr)]); rec.decode_stream(st)
        print(f"  upto {x:6.2f}: {st.result.text.strip()}")
        x+=step
