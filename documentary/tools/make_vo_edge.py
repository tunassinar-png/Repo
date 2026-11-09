"""Synthesise narration with Microsoft Edge TTS (ms-MY-YasminNeural, female Malaysian Malay) into vo/NN.wav.
Usage: python3 tools/make_vo_edge.py [voice] [rate] [pitch] [volume]
       default energetic read: ms-MY-YasminNeural +22% +3Hz +20%
Needs: pip install edge-tts  and network access to speech.platform.bing.com"""
import asyncio, json, os, pathlib, subprocess, sys, tempfile
import edge_tts

root = pathlib.Path(__file__).resolve().parent.parent
voice = sys.argv[1] if len(sys.argv) > 1 else 'ms-MY-YasminNeural'
rate = sys.argv[2] if len(sys.argv) > 2 else '+22%'
pitch = sys.argv[3] if len(sys.argv) > 3 else '+3Hz'
volume = sys.argv[4] if len(sys.argv) > 4 else '+20%'
tl = json.loads((root / 'src/timeline.json').read_text())
out = root / 'vo'; out.mkdir(exist_ok=True)

async def main():
    for v in tl['vo']:
        mp3 = pathlib.Path(tempfile.gettempdir()) / f"vo_{v['id']}.mp3"
        await edge_tts.Communicate(v['text'].replace('…', ''), voice, rate=rate, pitch=pitch, volume=volume, proxy=os.environ.get('HTTPS_PROXY')).save(str(mp3))
        wav = out / f"{v['id']}.wav"
        subprocess.check_call(['ffmpeg', '-y', '-v', 'error', '-i', str(mp3), '-ac', '1', '-ar', '24000', str(wav)])
        d = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(wav)]))
        print(v['id'], f"{d:.1f}s (slot {v['max']}s)")
asyncio.run(main())
