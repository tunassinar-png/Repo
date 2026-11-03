# KAMAAR BEDDINGS – product price pop-ups

Synchronized price pop-ups + event-details end card for the Ipoh clearance-sale
video (9:16, 1080 × 1920, TikTok / Facebook Reels).

- `output/kamaar_price_popups.mp4` – final video (52.5 s)
- `render_kamaar_popups.py` – renderer (`ffmpeg`, Pillow, numpy)

```
python3 render_kamaar_popups.py INPUT.mp4 output/kamaar_price_popups.mp4 [--logo logo.png] [--vo vo.mp3]
```

## Intro hook (0 – 3.9 s): "KAMPUNG TAWAS, IPOH"

Synced to "Kepada warga Kampung Tawas, Ipoh dan kawasan sekitar": a red
`KEPADA WARGA` chip (1.00 s), `KAMPUNG TAWAS` slams in (1.72 s), then a huge
`IPOH` (2.47 s), then `& KAWASAN SEKITAR` (3.00 s); all leave at 3.6 s.
Impact effects on the slams: strong camera shake + punch zoom, RGB split, screen
flash, radial speed lines, spark/streak bursts, double shock ring, two
counter-rotating light-ray layers, zoom-trail afterimages and a text shine sweep. A soft dark scrim sits over the
top of the frame (0.9 – 11 s) for legibility. Everything is configured in
`HOOK` / `EVENTS` / `BADGE`.

## Intro banners (4.0 – 10.9 s): big date / time / location

Revealed line by line as the presenter says "Pada 7 dan 8 November, Sabtu dan
Ahad, kami akan berada di Dewan Serba Guna, Kampung Tersusun, Tawas Tambahan,
Ipoh". Placed in the empty wall area above the presenter (y 160–640); each
banner enters with a small flash + spark burst.

| On screen | Appears at |
|---|---|
| TARIKH & MASA: 7 & 8 NOVEMBER 2026 | 4.00 s |
| SABTU & AHAD | 5.95 s |
| 9 PAGI – 10 MALAM (not spoken in the VO – shown with the day) | 6.55 s |
| LOKASI: DEWAN SERBAGUNA | 7.45 s |
| KAMPUNG TERSUSUN | 8.45 s |
| TAWAS TAMBAHAN, IPOH | 9.20 s |
| `2 HARI SAHAJA!` slam badge (VO "2 hari saja") | 10.00 s |

## Price pop-ups – one per price mention in the VO

Each starts 0.05 s before the price word (word-level highlight of the
burned-in captions, cross-checked against the audio, ±0.1 s) and lasts 1.85 s
including a bounce-in and exit. Pop-ups never overlap (enforced by an assertion).

| Pop-up | VO line | Price said at | On screen |
|---|---|---|---|
| BANTAL TIDUR – RM5.00 | "bantal macam ni, harga hanya RM5" | 12.30 s | 12.25 – 14.10 s |
| 6 BIJI BANTAL – RM29.00 | "ambil 6 biji bantal macam ni, ni hanya RM29" | 15.85 s | 15.80 – 17.65 s |
| KAIN REJECT KILANG – RM1.00 / METER | "kain reject kilang, 1m, seringgit" | 18.75 s | 18.70 – 20.55 s |
| KAIN REJECT KILANG – RM1.00 / METER | "kira tebal 1m, seringgit saja" | 21.15 s | 21.10 – 22.95 s |
| SARUNG BANTAL **4** HELAI – RM10.00 (big "4") | "abang akak sarung bantal ni 4 helai, RM10" | 24.30 s | 24.25 – 26.10 s |
| TILAM TOTO – RM29.00 | "Tilam Toto ni harga, dia RM29 saja" | 27.10 s | 27.05 – 28.90 s |
| TILAM SINGLE – RM39.00, then TILAM SINGLE **3 BIJI** / **RM100** (large card) | "Tilam single RM39" → "ambil tiga, seratus" (3 for RM100) | 29.60 s / 30.50 s | 29.55 – 32.20 s (card swaps to the big one at 30.5 s) |
| BANTAL PELUK – RM15.00 | "pantai [bantal] peluk harga paling murah RM15" | 34.40 s | 34.35 – 36.20 s |

Product names are taken from the captions and the items on screen; "SARUNG
BANTAL 4 HELAI" is confirmed, check the "6 BIJI BANTAL" label.

Style: white ExtraBold product name above a yellow Black price with a red
outline, on a small translucent navy card centred at y = 1385 (above the
burned-in captions and the platform UI zone).

## Persistent date / location label

Small two-line text, top-centre (y ≈ 205): `7 & 8 NOV 2026` /
`DEWAN SERBAGUNA KAMPUNG TERSUSUN, TAWAS TAMBAHAN, IPOH`. Visible 0.3 – 3.85 s
and 11.0 – 46.9 s; hidden 3.85 – 10.9 s while the big intro banners (same
information) are on screen, and replaced by the end card afterwards.
Configure in `LABEL_LINES` / `LABEL_SHOW`.

## Audio

The presenter's original audio plays from 0 to 47 s (faded out at the end).
The end card (47 – 52.5 s) is silent unless a voice-over file is passed with
`--vo` (it starts 0.3 s into the end card).

## End card (47.0 – 52.5 s)

7 & 8 NOVEMBER 2026 · SABTU & AHAD · 9 PAGI – 10 MALAM · DEWAN SERBAGUNA
KAMPUNG TERSUSUN · TAWAS TAMBAHAN, IPOH · 2 HARI SAHAJA! · KAMAAR BEDDINGS logo.

The logo is a typeset stand-in. Pass the official file with `--logo` (PNG with
transparent background) and re-render.
