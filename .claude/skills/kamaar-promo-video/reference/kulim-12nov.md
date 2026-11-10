# Worked example 3: Kulim sale 12 Nov 2026 (re-edit of the Ipoh hall footage)

Source: `copy_F7E8DC9F-...-compressed.mp4`, 47.04 s, 1080x1920, 60 fps (rendered at 30), stereo.
The user sent it with **no instruction**; the established recipe was applied (4:5, dahsyat intro,
dialogue pop-ups, price cards, music) and the assumptions were stated in the reply.
It is the **same recording as video 1** with new burned-in yellow word-highlighted captions and a
new intro voice: audio correlation with video 1 is 0.999 at lag 0 from 11.5 s on (and ~0.03 before),
so all price times of video 1 are valid; only 0-11 s needed new timing.
Check with `numpy` cross-correlation of 2 s windows (+/-1 s lag) before re-transcribing anything.

Event, **confirmed by the user**: "Promosi bantal & tilam di Dewan Masjid Al Fateh, Taman Mutiara, Sungai Kob,
Kulim. Pada 12 Nov 2026 hari Khamis jam 9 pagi hingga 10 malam." (captions spell it "Fatih", Whisper "Kop":
the user's spelling wins). One date only: NO "2 hari" / "1 hari sahaja" claim; end-card badge =
"PROMOSI BANTAL & TILAM" (the user's headline).

Captions of this footage: two yellow lines at y 1445-1555 of the 1080x1920 frame -> 4:5 crop
`CROP_Y = 80` (window y 80..1430) hides them. Config: `configs/kulim_12nov_4x5.py`.
Outputs: `promosi-jelajah/kulim_12nov_4x5_1080.mp4` (1080x1350), `..._2k.mp4` (1440x1800).

| t (s) | dialogue | on screen |
|---|---|---|
| 0.2 | Cari bantal dan tilam jom ke | slam CARI BANTAL 0.30 + & TILAM? 0.95 |
| 1.7 | Dewan Masjid Al-Fateh, Taman Mutiara | DEWAN MASJID 1.70, AL-FATEH 2.20, TAMAN MUTIARA 2.55 |
| 3.25 | Sungai Kob, Kulim | SUNGAI KOB 3.25, KULIM 3.75 |
| 4.5 | pada 12/11/2026 hari Khamis, dari 9.00 pagi hingga 10 malam | banner TARIKH & MASA: 12 NOVEMBER 2026 4.45, KHAMIS 6.20, 9 PAGI – 10 MALAM 7.15 |
| 9.0 | Bantal dan tilam pelbagai corak | BANTAL & TILAM 9.00, PELBAGAI CORAK! 9.75 |
| 12.3-34.4 | (same as video 1) | 8 price cards; kain card = KAIN REJECT KILANG RM1 / 1 METER (twice); 4 HELAI; 3 BIJI RM100 |
| 19.3 | tak kira nipis tak kira tebal | slams TAK KIRA NIPIS 19.25 / TAK KIRA TEBAL 20.15 |
| 38.75 | macam-macam barang kita bawa | slam MACAM-MACAM BARANG! |
| 45.05 | jadi jangan lupa, tunggu janji kita | slam JANGAN LUPA! 45.05, chip TUNGGU JANJI KITA 45.80 |

## To confirm with the user
format (4:5 chosen because it was the user's last
format; 9:16 = same config with `H=1920`, no `CROP_Y`, positions from `ipoh_hari1.py`); kain card
wording (video 2's "KAIN ELA" was NOT used here because this audio clearly says "kain reject kilang");
music is synthesised and was not heard by Claude; logo is a stand-in.
