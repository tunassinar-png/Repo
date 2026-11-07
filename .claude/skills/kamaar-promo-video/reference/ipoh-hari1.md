# Worked example 2: Ipoh sale, day-1 presenter video (IMG_1401)

Source: `IMG_1401-compressed.mp4`, 44.88 s, stored 1920x1080 with -90 rotation (= 1080x1920),
~60 fps (rendered at 30 fps), mono 48 kHz audio, **no burned-in captions**, presenter alone in
a large shed (hall, bedding stalls behind him, no products held up). Shot on 7 Nov 2026
("hari ini 7 November"). Final: 50.3 s (44.88 s footage + 5.5 s end card).
Config: `configs/ipoh_hari1.py`. Outputs: `promosi-jelajah/ipoh_hari1_1080.mp4` (~30 MB) and
`promosi-jelajah/ipoh_hari1_2k.mp4` (~45 MB).

## Transcript (Whisper turbo + large-v3 consensus; word times by prefix scan, +/-0.1 s)
| t (s) | dialogue | on screen |
|---|---|---|
| 0.15 | (silence) | logo sting (KAMAAR BEDDINGS) + flash/shake |
| 1.23 | Assalamualaikum warga-warga Kampung Tawas, Ipoh | chip ASSALAMUALAIKUM 1.30; chip WARGA-WARGA 2.30; slam KAMPUNG TAWAS 3.12; slam IPOH 3.92 |
| 4.56 | Ok, hari ni kami dah sampai dekat Dewan Serbaguna, Kampung Tersusun, Tawas Tambahan | slam KAMI DAH SAMPAI! 5.35; LOKASI banner 6.30 (Dewan Serbaguna), 7.50 (Kampung Tersusun), 8.30 (Tawas Tambahan, Ipoh) |
| 9.36 | Kita akan berada di sini dua hari | - |
| 11.24 | Bermula pada hari ini 7 November dan juga esok 8 November, hari Sabtu dan Ahad, 9 pagi sampai 10 malam | TARIKH & MASA banner: HARI INI 7 NOVEMBER 12.20; ESOK 8 NOVEMBER 14.40; SABTU & AHAD 15.85; 9 PAGI – 10 MALAM 17.25 |
| 19.29 | Dua hari saja, abang kakak | pill 2 HARI SAHAJA! |
| 20.99 | Kita bawa apa? | slam KITA BAWA APA? 21.00 |
| 22.1 | Kita bawa bantal harga lima ringgit | card BANTAL TIDUR RM5.00 at 23.05 (lima 23.15) |
| 24.41 | Kita bawa Tilam Toto ni dua puluh sembilan ringgit | card TILAM TOTO RM29.00 at 25.80 (RM29 25.9) |
| 27.41 | Kita ada kain (reject kilang) yang harga semeter, seringgit | card KAIN REJECT KILANG RM1.00 / METER at 29.45 (seringgit 29.55) |
| 30.31 | Jadi jangan lupa | slam JANGAN LUPA! 30.40 |
| 31.85 | untuk hari Sabtu dan hari Ahad, 7 dan 8 November | banner TARIKH: SABTU & AHAD 31.85; 7 & 8 NOVEMBER 2026 33.45 |
| 35.33 | Kami akan berada di sini | chip KAMI AKAN BERADA DI SINI 35.40 |
| 37.53 | Jadi mai ramai-ramai di Dewan Serbaguna, Kampung Tersusun, Tawas Tambahan | slam MAI RAMAI-RAMAI! 38.15; LOKASI banner 39.45 / 40.70 / 41.30 (until 43.9) |
| 44.88 | (presenter walks to camera) | end card |

## Music (`make_music.py`, 126 bpm, C major I-V-vi-IV, downbeat anchored on the 3.12 s slam)
Sections: 0-3.12 level 2 (kick + bass + pad + hats, riser 0.75-3.12) -> 3.12 drop (level 3)
-> 11-19 level 2 (lighter under the date/time list) -> 19-35.2 level 3 -> 35.2-38.1 level 2
with a riser into 38.15 -> 38.1-44.88 level 4 (lead) -> end card level 3, faded out. Music is
ducked ~10 dB under the voice (fast attack, 0.4 s release) and SFX (boom + whoosh on strong
events, tick on lines, pop + ding on price cards, end-card boom/ding/shimmer) sit on top.
Final loudness about -12 LUFS, limiter 0.80.

## To confirm with the user
- "KAIN REJECT KILANG": Whisper heard "kain elok/elak/crane yang harga semeter seringgit"; the
  name is the user's own product wording (same product as video 1).
- "MAI RAMAI-RAMAI!": heard "boleh pakai / jadi ... ramai-ramai" (brief wording: "Mai ramai-ramai").
- Venue "Kampung Tersusun, Tawas Tambahan": Whisper wrote "Kampung Tawas Tambahan"; the user's
  brief (and video 1 captions) say Kampung Tersusun.
- Music is synthesised and was not heard by Claude; logo is a stand-in; no VO on the end card.
