"""Malay (ms) speech via bundled espeak-ng. Usage: tts_ms.py "text" out.wav [rate] [pitch]"""
import ctypes, sys, wave
import numpy as np
import espeakng_loader as L

lib = ctypes.CDLL(L.get_library_path())
SR = lib.espeak_Initialize(2, 0, L.get_data_path().encode(), 0)  # SYNCHRONOUS, returns sample rate
CB = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p)
_buf = []

def _cb(wav, n, ev):
    if wav and n > 0:
        _buf.append(np.ctypeslib.as_array(wav, shape=(n,)).copy())
    return 0
_cbref = CB(_cb)
lib.espeak_SetSynthCallback(_cbref)

def synth(text, voice="ms+m3", rate=120, pitch=22, rng_=28):
    _buf.clear()
    lib.espeak_SetVoiceByName(voice.encode())
    lib.espeak_SetParameter(1, rate, 0)   # rate wpm
    lib.espeak_SetParameter(3, pitch, 0)  # pitch base
    lib.espeak_SetParameter(4, rng_, 0)   # pitch range
    data = text.encode()
    lib.espeak_Synth(data, len(data) + 1, 0, 0, 0, 1, None, None)  # espeakCHARS_UTF8=1
    lib.espeak_Synchronize()
    return (np.concatenate(_buf).astype(np.float32) / 32768) if _buf else np.zeros(1, np.float32)

if __name__ == "__main__":
    x = synth(sys.argv[1], rate=int(sys.argv[3]) if len(sys.argv) > 3 else 120,
              pitch=int(sys.argv[4]) if len(sys.argv) > 4 else 22)
    with wave.open(sys.argv[2], "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())
    print(SR, len(x) / SR, "s")
