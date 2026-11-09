# Apa Akan Jadi Jika Semua Wanita Dalam Dunia Ini Cantik?

Dokumentari pendek 60 saat, 16:9 (1920×1080, 30 fps). Footage dijana di Grok (prompt di bawah); kit ini menyediakan overlay teks, sarikata, muzik dan panduan masa.

## Fail dalam `out/`
| Fail | Kegunaan |
|---|---|
| `overlay_alpha.webm` | Teks kecil setiap babak + sarikata + soalan penutup (VP9 alfa lutsinar, 60 s). Letak di atas klip dalam DaVinci/Premiere/Final Cut. |
| `overlay_greenscreen.mp4` | Versi skrin hijau jika aplikasi tidak menyokong alfa (*Chroma Key*, warna 00FF00). |
| `subtitles.srt` | Sarikata Melayu (boleh diimport ke CapCut, Premiere, Facebook). Masa dianggar daripada panjang ayat; selaraskan semula selepas naratif sebenar dirakam. |
| `musik_latar.mp3` | Muzik 60 saat: misteri (A minor) hingga 0:40, bertukar kepada inspirasi (C/G major) 0:40–1:00. Tahap rendah, tiada vokal. |
| `panduan_suara_tts.mp3` | Suara TTS sintetik untuk panduan masa SAHAJA. Gantikan dengan rakaman lelaki Malaysia yang sebenar. |
| `preview_dengan_bunyi.mp4` | Pratonton overlay + muzik + panduan suara atas latar ruang letak. |

Jana semula: `python3 build_overlay.py out`, `python3 make_music.py out/music_bed.wav`, `python3 make_vo_guide.py out/vo_guide.wav`.

## Naratif dan teks (masa)
| Masa | Naratif | Teks kecil |
|---|---|---|
| 0:00–0:10 | Pernah tak anda terfikir… apa akan jadi kalau semua wanita dalam dunia ini cantik? Adakah dunia akan menjadi lebih indah? | BAGAIMANA JIKA SEMUA WANITA CANTIK? |
| 0:10–0:20 | Pada mulanya, mungkin semua orang akan terpesona. Tetapi apabila semua orang cantik, kecantikan mungkin tidak lagi dianggap sesuatu yang luar biasa. | KECANTIKAN MENJADI NORMAL |
| 0:20–0:30 | Manusia mungkin mula mencari sesuatu yang lain untuk membezakan seseorang. Gaya, personaliti, keyakinan dan keunikan diri menjadi perhatian. | STANDARD KECANTIKAN BERUBAH |
| 0:30–0:40 | Tetapi adakah semua wanita akan lebih bahagia? Tidak semestinya. Kerana kecantikan tidak menjamin kebahagiaan, kejayaan ataupun hubungan yang sempurna. | CANTIK TIDAK SEMESTINYA BAHAGIA |
| 0:40–0:50 | Akhirnya, manusia mungkin semakin menghargai perkara yang lebih mendalam. Kebijaksanaan, kejujuran, kebaikan hati dan cara seseorang melayan orang lain. | NILAI DIRI LEBIH DARIPADA RUPA |
| 0:50–1:00 | Jadi, jika semua wanita di dunia ini cantik… mungkin yang berubah bukan dunia, tetapi cara kita menilai kecantikan. Apakah sebenarnya yang membuat seseorang itu cantik? | APA PENDAPAT ANDA? (0:56.6) + "Tulis pendapat anda di ruang komen" |

**Pelarasan:** naratif babak 6 asalnya 28 patah perkataan (terlalu panjang untuk 10 saat bersama soalan penutup). Saya buang "Persoalannya," supaya muat. Jika mahu teks asal penuh, naratif perlu dibaca lebih laju atau video jadi sekitar 62 saat.

## Prompt Grok (12 klip × 5 s, 16:9)
Tampal blok gaya di hujung setiap prompt:
> Photorealistic cinematic documentary footage, 16:9 landscape, shot on a cinema camera, shallow depth of field, natural cinematic lighting, smooth professional camera movement, natural human faces and hands, realistic anatomy and natural movement, diverse adult women of many ethnicities and ages, dignified and respectful, no text, no logos, no watermarks, no subtitles, no cartoon.

1A. Planet Earth seen from orbit, slow rotation, sunrise glowing along the edge of the atmosphere, faint city lights on the night side, deep space, slow cinematic camera drift.
1B. Camera descends through clouds toward a modern city at golden hour and ends over a busy plaza where adult women of many ethnicities walk, wide shot, slow motion.
2A. Wide tracking shot along a busy city street, crowds of women of different backgrounds walking in everyday clothes (some with hijab, some in business wear), ordinary daily life, soft daylight.
2B. Inside a modern shopping mall and on a university campus: women chatting, queueing for coffee, students walking with books, relaxed atmosphere, medium shots with a steady glide.
3A. Over-the-shoulder view of a woman scrolling a social media feed on her phone (screen blurred, no readable text), fashion shop windows with no text behind her, soft bokeh.
3B. Fashion photoshoot and runway: women of different styles, hair and clothing, each with a distinct personality, laughing and confident, slow motion.
4A. A woman sitting alone by a café window, thoughtful and quiet, rain outside, holding a cup of tea, medium shot, shallow depth of field, soft light.
4B. Quick cutaways of women facing everyday challenges: working late on a laptop in an office, a student studying in a library, a woman carrying shopping bags up stairs, empathetic mood.
5A. Women in professions: a doctor in a hospital corridor, an engineer in a hard hat on a site, a teacher in a bright classroom, a small-business owner in her shop, dignified smooth tracking shots.
5B. Warm moments: a mother hugging her child, friends laughing together, a woman helping an elderly person, genuine smiles, soft golden light.
6A. Slow-motion cinematic montage of adult women of many backgrounds at medium distance, looking toward the sun, wind in hair and hijab, warm golden light, tasteful and dignified.
6B. Camera pulls away from a city and up into space until the whole Earth is visible, sunrise glowing across the atmosphere, hopeful mood.

### Petua elak wajah dan tangan cacat
- Utamakan syot sederhana dan lebar; elak syot dekat tangan.
- Jana 2–3 percubaan setiap klip dan pilih yang terbaik.
- Tambah "natural skin texture, symmetrical faces, five fingers" jika wajah atau tangan kelihatan pelik.
- Wanita berhijab dan tidak berhijab, pelbagai bangsa dan usia dewasa, untuk menggambarkan kepelbagaian dengan hormat.

## Gabungan akhir
1. Susun 12 klip (5 s setiap satu) pada garis masa 60 saat dengan silang pudar 0.4 s.
2. Tindihkan `overlay_alpha.webm`.
3. Letak naratif sebenar, kemudian muzik pada kira-kira −20 dB di bawah suara supaya tidak mengganggu narator.
4. Eksport 1920×1080 H.264. Tiada watermark.
