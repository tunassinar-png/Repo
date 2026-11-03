# Worked example: Ipoh clearance sale, 7 & 8 Nov 2026

Event: 7 & 8 NOVEMBER 2026 (Sabtu & Ahad), 9 PAGI - 10 MALAM, DEWAN SERBAGUNA
KAMPUNG TERSUSUN, TAWAS TAMBAHAN, IPOH. "2 HARI SAHAJA!" Brand: KAMAAR BEDDINGS.
Source footage: 47.04 s, 1080x1920, 30 fps, male presenter, burned-in word-highlighted
captions at y ~1595-1705. Final video 52.47 s (47.04 s footage + 5.5 s end card).

## Intro timeline (VO: "Assalamualaikum, kepada warga Kampung Tawas, Ipoh dan kawasan
sekitar, pada 7 dan 8 November ni hari Sabtu dan Ahad, kami akan berada di Dewan Serba
Guna, Kampung Tersusun, Tawas Tambahan, Ipoh, 2 hari saja")

| t (s) | element |
|---|---|
| 1.00 | chip KEPADA WARGA |
| 1.72 | KAMPUNG TAWAS slam (shake 32, punch 0.10, RGB split, speed lines, sparks, rings) |
| 2.10 | small "Tawas" beat |
| 2.47 | IPOH slam (shake 42, punch 0.13) |
| 3.00 | & KAWASAN SEKITAR; whole hook leaves at 3.60 |
| 4.00 | banner TARIKH & MASA: 7 & 8 NOVEMBER 2026 |
| 5.95 | SABTU & AHAD pill |
| 6.55 | 9 PAGI - 10 MALAM pill (not spoken; shown with the day) |
| 7.45 / 8.45 / 9.20 | LOKASI: DEWAN SERBAGUNA / KAMPUNG TERSUSUN / TAWAS TAMBAHAN, IPOH |
| 10.00 | "2 HARI SAHAJA!" slam badge (VO "2 hari saja"); all banners leave at 10.90 |

## Price pop-ups (price word start -> pop-up start = -0.05 s, 1.85 s each)

| price said | pop-up | VO |
|---|---|---|
| 12.30 | BANTAL TIDUR / RM5.00 (12.25) | "bantal macam ni, harga hanya RM5" |
| 15.85 | 6 BIJI BANTAL / RM29.00 (15.80) | "ambil 6 biji bantal macam ni, ni hanya RM29" |
| 18.75 | KAIN REJECT KILANG / RM1.00 / METER (18.70) | "kain reject kilang, 1m, seringgit" |
| 21.15 | same card again (21.10) | "kira tebal 1m, seringgit saja" |
| 24.30 | SARUNG BANTAL **4** HELAI / RM10.00 (24.25), big yellow 4 | "abang akak sarung bantal ni 4 helai, RM10" |
| 27.10 | TILAM TOTO / RM29.00 (27.05) | "Tilam Toto ni harga, dia RM29 saja" |
| 29.60 | TILAM SINGLE / RM39.00 (29.55, dur 2.65) | "Tilam single RM39" |
| 30.50 | same card swaps to TILAM SINGLE **3 BIJI** / **RM100** (large) | "ambil tiga, seratus" = 3 for RM100 (confirmed by user) |
| 34.40 | BANTAL PELUK / RM15.00 (34.35) | "pantai [bantal] peluk harga paling murah RM15" |

Persistent label (top-centre, y 205): "7 & 8 NOV 2026" / "DEWAN SERBAGUNA KAMPUNG TERSUSUN,
TAWAS TAMBAHAN, IPOH"; visible 0.3-3.85 s and 11.0-46.9 s.

## Outputs made
- `output/kamaar_price_popups.mp4` - 1080x1920, ~36 MB
- `promosi-jelajah/kamaar_price_popups_2k.mp4` - 1440x2560, ~78 MB (crf 20)
- `promosi-jelajah/kamaar_price_popups_2k_ringan.mp4` - 1440x2560, ~43 MB (crf 24, lighter)

## Open items at the time of writing
- Logo is a typeset stand-in; waiting for the official transparent PNG (`--logo`).
- Label "6 BIJI BANTAL" not yet confirmed by the user ("SARUNG BANTAL 4 HELAI" confirmed).
- End card has no voice-over (no female Northern-accent VO could be generated; `--vo` ready).
