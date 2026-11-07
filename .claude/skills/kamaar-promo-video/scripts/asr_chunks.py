#!/usr/bin/env python3
"""
Transcribe a video phrase by phrase (split at speech pauses) with Whisper via sherpa-onnx.

    python3 -B -I asr_chunks.py INPUT.mp4 MODEL_DIR OUT.json [MIN_PAUSE=0.12]

MODEL_DIR = .../sherpa-onnx-whisper-turbo (see asr_setup.sh). Language is Malay ("ms").
Prints "start-end  text" per phrase; phrase starts/ends come from the audio energy so they
are accurate to ~0.05 s. Text is NOT always right: Whisper hallucinates on noise ("Terima
kasih" on a breath), loops on repeats, and mishears product words ("tilam tutuh" = Tilam
Toto, "kain elok" ~ kain reject). Cross-check with a second model (asr_window.py) and with
the user's own product names before putting anything on screen.
"""
import sys, json, subprocess, numpy as np, sherpa_onnx
V, M, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
MINP = float(sys.argv[4]) if len(sys.argv) > 4 else 0.12
raw=subprocess.run(["ffmpeg","-v","error","-i",V,"-vn","-ac","1","-ar","16000","-f","f32le","-"],capture_output=True,check=True).stdout
a=np.frombuffer(raw,np.float32); sr=16000; hop=int(0.01*sr)
n=len(a)//hop; rms=np.sqrt((a[:n*hop].reshape(n,hop)**2).mean(1)); db=20*np.log10(rms+1e-6)
sm=np.convolve(db,np.ones(5)/5,mode="same"); thr=float(np.percentile(sm,20))+6; quiet=sm<thr
# speech runs separated by quiet >= MINP
runs=[];i=0
while i<n:
    if not quiet[i]:
        j=i; last=i
        while j<n:
            if not quiet[j]: last=j; j+=1; continue
            k=j
            while k<n and quiet[k]: k+=1
            if (k-j)*0.01>=MINP or k>=n: break
            j=k
        runs.append([i*0.01,(last+1)*0.01]); i=max(j,last+1)
    else: i+=1
# merge tiny runs (<1.0 s) into the neighbour that is closer
chunks=[]
for r in runs:
    if chunks and (r[1]-r[0]<1.0 or chunks[-1][1]-chunks[-1][0]<1.0) and r[0]-chunks[-1][1]<0.5 and r[1]-chunks[-1][0]<9:
        chunks[-1][1]=r[1]
    else: chunks.append(r)
import os
P=os.path.basename(M.rstrip("/")).replace("sherpa-onnx-whisper-","")
rec=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f"{M}/{P}-encoder.int8.onnx",decoder=f"{M}/{P}-decoder.int8.onnx",tokens=f"{M}/{P}-tokens.txt",language="ms",task="transcribe",num_threads=4)
out=[]
for s,e in chunks:
    p0=max(0,int((s-0.2)*sr)); p1=min(len(a),int((e+0.2)*sr))
    st=rec.create_stream(); st.accept_waveform(sr,a[p0:p1]); rec.decode_stream(st)
    out.append(dict(start=round(s,2),end=round(e,2),text=st.result.text.strip()))
    print(f"{s:6.2f}-{e:6.2f}  {out[-1]['text']}")
json.dump(out,open(OUT,"w"),ensure_ascii=False,indent=1)
