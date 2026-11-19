# Sales Growth Infographic (6 s, 4K)

Programmatically rendered corporate infographic: RM1.2M (2025) -> RM1.8M (2026), +50% growth, RM3M target within 3 years.

* `scene.js` / `index.html` - three.js 3D scene (bars drawn strictly proportional to the figures), DOM text overlays, timeline + camera path.
* `audio.py` - numpy-synthesised 6 s instrumental (120 BPM, C - G - F - C), no samples.
* `render.js` - drives headless Chromium frame-by-frame, pipes PNG frames to ffmpeg (H.264, 3840x2160, 30 fps, AAC audio).

```bash
npm install                      # three@0.160
python3 audio.py out/music.wav
NODE_PATH=$(npm root -g) node render.js video out/sales-growth-4k.mp4 30 2 out/music.wav
# stills for layout checks:  node render.js preview out/stills 0.8,3.4,5.97 1
```
