"""Mix voice-over clips (vo/NN.wav|mp3|m4a|ogg) over public/music.wav -> public/soundtrack.wav.
Music is ducked automatically while the narrator speaks. Missing clips are skipped; with no clips
the music is copied unchanged. Override the clip folder with VO_DIR=... for testing."""
import json, os, pathlib, shutil, subprocess, sys

root = pathlib.Path(__file__).resolve().parent.parent
tl = json.loads((root / 'src/timeline.json').read_text())
vo_dir = pathlib.Path(os.environ.get('VO_DIR', root / 'vo'))
music, out = root / 'public/music.wav', root / 'public/soundtrack.wav'
if not music.exists(): sys.exit('public/music.wav missing - run tools/make_audio.py first')

def dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)]))

clips = []
for v in tl['vo']:
    f = next((vo_dir / f'{v["id"]}{e}' for e in ('.wav', '.mp3', '.m4a', '.ogg') if (vo_dir / f'{v["id"]}{e}').exists()), None)
    if f: clips.append((v, f))
    else: print(f'skip {v["id"]}: no clip')
if not clips:
    shutil.copy(music, out); print('no VO clips - soundtrack = music only'); sys.exit(0)

args = ['ffmpeg', '-y', '-v', 'error', '-i', str(music)]
filt, labels = [], []
for i, (v, f) in enumerate(clips, 1):
    args += ['-i', str(f)]
    d = dur(f); tempo = 1.0
    if d > v['max']:
        tempo = min(1.3, d / v['max'])
        print(f'WARN {v["id"]}: {d:.1f}s > {v["max"]}s, atempo {tempo:.2f}' + (' (still long!)' if d / tempo > v['max'] + 0.3 else ''))
    ms = int(v['at'] * 1000)
    filt.append(f'[{i}:a]aresample=44100,aformat=channel_layouts=stereo,highpass=f=90,equalizer=f=3200:t=q:w=1:g=3,equalizer=f=220:t=q:w=1:g=-2,acompressor=threshold=0.08:ratio=4:attack=5:release=90:makeup=3,atempo={tempo:.3f},adelay={ms}|{ms},apad=whole_dur={tl["total"]/tl["fps"]}[v{i}]')
    labels.append(f'[v{i}]')
filt.append(''.join(labels) + f'amix=inputs={len(clips)}:normalize=0,volume=1.5,asplit=2[vo][sc]')
filt.append('[0:a]volume=0.95[m]')
filt.append('[m][sc]sidechaincompress=threshold=0.012:ratio=9:attack=10:release=350:makeup=1[duck]')
filt.append(f'[duck][vo]amix=inputs=2:normalize=0,alimiter=limit=0.89:level=0,atrim=0:{tl["total"]/tl["fps"]}[mix]')
args += ['-filter_complex', ';'.join(filt), '-map', '[mix]', '-ar', '44100', '-ac', '2', str(out)]
subprocess.check_call(args)
print('wrote', out, f'with {len(clips)} VO clip(s)')
