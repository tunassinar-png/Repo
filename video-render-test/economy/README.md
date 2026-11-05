# Kit grafik: "Gaji Minimum RM2,000 — Rakyat makin senang atau barang makin mahal?"

Reel 60 saat, 9:16 (1080×1920, 30 fps). Footage Malaysia dijana di Grok (lihat prompt di bawah); kit ini menyediakan grafik, teks, muzik dan panduan masa.

## Fail dalam `out/`
| Fail | Kegunaan |
|---|---|
| `overlay_alpha.webm` | Semua teks + animasi (VP9 alfa lutsinar, 60 s). Letak di atas klip dalam DaVinci/Premiere/Final Cut. |
| `overlay_greenscreen.mp4` | Versi skrin hijau jika aplikasi tidak menyokong alfa (guna *Chroma Key*, warna 00FF00). |
| `png/*.png` | Setiap plat teks sebagai PNG lutsinar 1080×1920 (nama fail = masa mula-tamat). Sesuai untuk CapCut/TikTok. |
| `preview_dengan_bunyi.mp4` | Pratonton: overlay atas latar ruang letak + muzik + panduan suara. Hanya untuk semak masa. |
| `musik_latar.mp3` | Muzik latar asal (A minor, 72 BPM), tahap rendah, tiada vokal. |
| `panduan_suara_tts.mp3` | Suara TTS sintetik untuk panduan masa SAHAJA. Gantikan dengan rakaman penutur Malaysia. |

Jana semula: `python3 build_overlay.py out`, `python3 make_music.py out/music_bed.wav`, `python3 make_vo_guide.py out/vo_guide.wav`.

## Garis masa (naratif dan teks)
| Masa | Naratif | Teks skrin |
|---|---|---|
| 0:00–0:10 | Gaji minimum naik kepada dua ribu ringgit. Adakah rakyat akan hidup lebih selesa? Atau harga barang pula yang akan meningkat? | GAJI MINIMUM RM2,000 (0:00.5) / RAKYAT UNTUNG ATAU RUGI? (0:03.4) |
| 0:10–0:20 | Bagi pekerja, ini berita baik. Tetapi bagi majikan, kos pengeluaran meningkat. Sebahagian kos mungkin dipindahkan kepada pengguna melalui kenaikan harga barang. | KOS GAJI NAIK (0:10.5) / HARGA BARANG BOLEH NAIK (0:14.1) |
| 0:20–0:30 | Pekerja asing juga menerima manfaat. Sebahagian pendapatan tambahan mungkin dihantar ke negara asal. Namun, mereka turut berbelanja dan menyumbang kepada ekonomi Malaysia. | ALIRAN WANG KE LUAR NEGARA + animasi aliran wang (0:20.5–0:29.6) |
| 0:30–0:40 | Bagaimana pula mereka yang tidak mendapat kenaikan gaji? Apabila harga makanan dan perkhidmatan meningkat, kuasa beli mereka boleh semakin terhakis. | KOS SARA HIDUP (0:30.5) / KUASA BELI TERHAKIS (0:34.1) |
| 0:40–0:50 | Namun, kenaikan gaji tidak semestinya menyebabkan inflasi berpanjangan. Peningkatan produktiviti dan kecekapan perniagaan boleh membantu mengawal kos. | INFLASI VS PRODUKTIVITI + graf beranimasi (0:40.5–0:49.7) |
| 0:50–1:00 | Akhirnya, yang penting bukan sekadar berapa tinggi gaji kita. Tetapi berapa banyak barang yang mampu kita beli. Gaji naik penting, kuasa beli rakyat lebih penting. | GAJI NAIK, KUASA BELI NAIK? (0:56.0) → APA PENDAPAT ANDA? (0:58.0) |

Naratif babak 6 mesti mula pada ~0:50.2 dan tamat sebelum 0:58.

## Nota ketepatan
- Graf babak 5 ialah **ilustrasi konsep** (berlabel "BUKAN DATA SEBENAR"), tiada nombor.
- Semak status RM2,000 (berkuat kuasa atau cadangan) sebelum menyiarkan. Jika cadangan, ubah naratif kepada "Jika gaji minimum naik…".
- Gambarkan pekerja asing secara neutral dan bermaruah; animasi tidak menyebut negara tertentu.

## Prompt Grok (12 klip × 5 s, 9:16)
Tampal blok gaya ini di hujung setiap prompt:
> Photorealistic Malaysian documentary footage, cinematic 4K look, natural lighting, smooth camera movement, authentic Malaysian setting and diverse Malaysian people (Malay, Chinese, Indian, indigenous), professional news-documentary colour grade. No readable text, no signage text, no logos, no watermarks, no subtitles, no cartoon.

1A. Wide cinematic shot of Kuala Lumpur morning rush hour, motorbikes and cars on a busy street, office workers walking, glass towers in the background, soft golden light.
1B. Factory workers in uniforms walking through a factory gate at shift start, then a close-up of hands holding colourful Malaysian Ringgit banknotes, shallow depth of field, a busy hypermarket aisle softly blurred behind.
2A. Smooth tracking shot along rows of Malaysian women and men operating sewing machines in a textile factory, fabric moving through the machines, bright fluorescent lighting.
2B. A Malaysian business owner in a small office reviewing printed payroll sheets and a calculator, worried and thoughtful expression, close-up of the pen on the paper, a production floor visible through the glass behind.
3A. Diverse workers in a manufacturing plant operating machinery and assembling products, wearing helmets and uniforms, dignified and professional documentary style.
3B. Workers on a Malaysian construction site with scaffolding and cranes at golden hour, then a worker walking out of a small shop with groceries, neutral and respectful tone.
4A. A Malaysian mother in a hypermarket picking up groceries, comparing price tags on shelves with a concerned expression, her child sitting in the trolley, handheld documentary feel.
4B. Close-up of a customer at a traditional Malaysian wet market checking a long shopping receipt, then a vendor weighing vegetables, vibrant colours, shallow depth of field.
5A. Modern automated factory with robotic arms and conveyor belts producing goods, bright clean lighting, slow tracking shot.
5B. Malaysian technicians in uniforms using tablets and computers to monitor an efficient production line, clean modern workplace, smooth push-in shot.
6A. Slow-motion emotional montage: a Malaysian street food hawker serving customers, a smiling worker leaving a factory, a family walking together in a city park at dusk, warm light.
6B. Slow dolly-in down a long Malaysian supermarket aisle full of products, soft lighting, nobody in focus, ending on a still wide shot, calm and reflective mood.
