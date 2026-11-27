# Rezeki & Takwa — animasi + infografik (9:16, ~103 saat)

Video pendek menegak (1080×1920) berdasarkan jalan cerita sebuah video motivasi tentang rezeki dan takwa
(Surah At-Talaq 65:2–3). Visual, ayat skrip, suara VO dan muzik semuanya dibuat baharu; tiada audio/visual asal digunakan.

- `out/rezeki-dan-takwa.mp4` — video siap
- `tools/script.json` — skrip VO + tetapan suara (Edge TTS `ms-MY-OsmanNeural`)
- `src/scenes*.tsx` — 9 babak animasi/infografik · `src/common.tsx` — latar, sari kata karaoke, watak, ikon
- `src/scenes3.tsx` → `CREDIT` — baris kredit pada kad akhir (kosongkan `''` untuk buang)

```
npm install
python3 tools/make_vo.py       # VO + masa setiap perkataan -> src/timeline.json (animasi ikut masa ini)
python3 tools/make_music.py    # muzik latar ikut babak
python3 tools/mix.py           # campur VO + muzik (muzik turun semasa VO, -16 LUFS)
npm run render
```
Perlukan `pip install edge-tts numpy scipy` dan capaian ke `speech.platform.bing.com` untuk VO.
Teks Arab: Amiri Quran (OFL). Terjemahan ayat dalam VO ialah terjemahan ringkas — rujuk terjemahan Al-Quran yang diiktiraf sebelum disiarkan.
