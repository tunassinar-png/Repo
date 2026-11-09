# Apa Akan Jadi Sekiranya Semua Wanita Cantik di Dunia Ni?

Dokumentari pendek 60 saat (1920×1080, 30fps) dengan animasi, teks, pop-up dan runut bunyi. Dibina dengan Remotion.

- `out/apa-jadi-jika-semua-wanita-cantik.mp4` — video siap
- `src/timeline.json` — garis masa bab + semua pop-up (ubah teks/masa di sini)
- `src/scenes.tsx` — 7 babak beranimasi · `src/common.tsx` — pop-up, HUD, teks
- `tools/make_audio.py` — jana muzik bertenaga 120 BPM (`public/music.wav`) + bunyi pop/whoosh daripada garis masa yang sama

```
npm install
python3 tools/make_audio.py          # jana semula audio selepas ubah masa pop-up
npx remotion studio src/index.ts     # pratonton
npm run render                       # render ke out/documentary.mp4
```
Jika muat turun Chrome disekat, tambah `--browser-executable=<chromium> --chrome-mode=chrome-for-testing`.

## Suara latar (VO)
Skrip VO bertanda masa ada dalam `vo/SKRIP.md` (suara lelaki Melayu Malaysia, 40-an). Letak rakaman sebagai `vo/01.wav` … `vo/07.wav`, kemudian:

```
python3 tools/make_vo_edge.py   # jana VO (Edge TTS, bertenaga)
python3 tools/mix_vo.py      # campur VO + muzik (muzik turun automatik semasa VO) -> public/soundtrack.wav
npm run render
```
