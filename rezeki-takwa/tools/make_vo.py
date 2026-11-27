"""Narration + timeline builder.
Reads tools/script.json, synthesises every line with Edge TTS (word timings included), lays the lines out on a
timeline with natural gaps, and writes:
  src/timeline.json   (scenes, lines, word timings in frames -> drives the animation)
  public/vo.wav       (narration track)
Re-running reuses cached line audio in vo/ when text+voice settings are unchanged (use --force to redo).
Needs: pip install edge-tts ; network access to speech.platform.bing.com"""
import asyncio, hashlib, json, math, os, pathlib, subprocess, sys, wave
import edge_tts

root = pathlib.Path(__file__).resolve().parent.parent
cfg = json.loads((root / 'tools/script.json').read_text())
FPS = 30
force = '--force' in sys.argv
vo_dir = root / 'vo'; vo_dir.mkdir(exist_ok=True)


def dur(p):
    return float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(p)]))


async def synth(text, key):
    wav, js = vo_dir / f'{key}.wav', vo_dir / f'{key}.json'
    if wav.exists() and js.exists() and not force:
        return json.loads(js.read_text())
    c = edge_tts.Communicate(text.replace('…', ' '), cfg['voice'], rate=cfg['rate'], pitch=cfg['pitch'], volume=cfg['volume'],
                             boundary='WordBoundary', proxy=os.environ.get('HTTPS_PROXY'))
    audio, words = b'', []
    async for m in c.stream():
        if m['type'] == 'audio': audio += m['data']
        elif m['type'] == 'WordBoundary':
            words.append({'w': m['text'], 's': m['offset'] / 1e7, 'd': m['duration'] / 1e7})
    mp3 = vo_dir / f'{key}.mp3'; mp3.write_bytes(audio)
    subprocess.check_call(['ffmpeg', '-y', '-v', 'error', '-i', str(mp3), '-ac', '1', '-ar', '24000', str(wav)])
    mp3.unlink()
    info = {'dur': dur(wav), 'words': words}
    js.write_text(json.dumps(info, ensure_ascii=False))
    return info


async def main():
    t = cfg['first_line_at']
    scenes, placements = [], []
    for si, sc in enumerate(cfg['scenes']):
        lines = []
        for li, text in enumerate(sc['lines']):
            key = hashlib.md5(json.dumps([text, cfg['voice'], cfg['rate'], cfg['pitch'], cfg['volume']]).encode()).hexdigest()[:10]
            info = await synth(text, key)
            ws = [{'w': w['w'], 's': round((t + w['s']) * FPS), 'e': round((t + w['s'] + w['d']) * FPS)} for w in info['words']]
            lines.append({'text': text, 'start': round(t * FPS), 'end': round((t + info['dur']) * FPS), 'words': ws})
            placements.append((vo_dir / f'{key}.wav', t))
            print(f"{si+1}.{li+1} {t:6.2f}s +{info['dur']:.2f}s  {text[:60]}")
            t += info['dur'] + cfg['line_gap']
        scenes.append({'id': sc['id'], 'label': sc['label'], 'lines': lines})
        t += cfg['scene_gap'] - cfg['line_gap']
    end_t = t + cfg['tail']
    total = math.ceil(end_t * FPS)
    for i, sc in enumerate(scenes):
        first = sc['lines'][0]['start']
        sc['from'] = 0 if i == 0 else max(0, first - round(cfg['lead'] * FPS))
    for i, sc in enumerate(scenes):
        sc['dur'] = (scenes[i + 1]['from'] if i + 1 < len(scenes) else total) - sc['from']
    (root / 'src/timeline.json').write_text(json.dumps({'fps': FPS, 'total': total, 'scenes': scenes}, ensure_ascii=False, indent=1))
    # narration track
    args = ['ffmpeg', '-y', '-v', 'error']; filt = []; lab = []
    for i, (f, at) in enumerate(placements):
        ms = int(at * 1000)
        args += ['-i', str(f)]
        filt.append(f'[{i}:a]aresample=44100,aformat=channel_layouts=stereo,highpass=f=90,equalizer=f=3000:t=q:w=1:g=2.5,acompressor=threshold=0.08:ratio=3:attack=5:release=120:makeup=2,adelay={ms}|{ms},apad=whole_dur={end_t:.2f}[v{i}]')
        lab.append(f'[v{i}]')
    filt.append(''.join(lab) + f'amix=inputs={len(placements)}:normalize=0,volume=1.4,atrim=0:{end_t:.2f}[o]')
    args += ['-filter_complex', ';'.join(filt), '-map', '[o]', '-ar', '44100', str(root / 'public/vo.wav')]
    subprocess.check_call(args)
    print(f'total {total} frames = {total/FPS:.1f}s ; wrote src/timeline.json + public/vo.wav')

asyncio.run(main())
