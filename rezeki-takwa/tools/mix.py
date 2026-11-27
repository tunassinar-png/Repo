"""public/music.wav + public/vo.wav -> public/soundtrack.wav (music ducks under the narration)."""
import json, pathlib, subprocess
root = pathlib.Path(__file__).resolve().parent.parent
tl = json.loads((root / 'src/timeline.json').read_text()); dur = tl['total'] / tl['fps']
filt = ('[0:a]volume=0.9[m];[1:a]asplit=2[vo][sc];[m][sc]sidechaincompress=threshold=0.012:ratio=8:attack=15:release=450:makeup=1[d];'
        f'[d][vo]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=9,alimiter=limit=0.89:level=0,atrim=0:{dur:.2f}[o]')
subprocess.check_call(['ffmpeg', '-y', '-v', 'error', '-i', str(root / 'public/music.wav'), '-i', str(root / 'public/vo.wav'),
                       '-filter_complex', filt, '-map', '[o]', '-ar', '44100', '-ac', '2', str(root / 'public/soundtrack.wav')])
subprocess.check_call(['ffmpeg','-y','-v','error','-i',str(root/'public/soundtrack.wav'),'-b:a','224k',str(root/'public/soundtrack.mp3')])
print('wrote public/soundtrack.mp3', f'{dur:.1f}s')
