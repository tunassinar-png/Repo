# KAMAAR BEDDINGS – product price pop-ups

Synchronized price pop-ups + event-details end card for the Ipoh clearance-sale
video (9:16, 1080 × 1920, TikTok / Facebook Reels).

- `output/kamaar_price_popups.mp4` – final video (52.5 s)
- `render_kamaar_popups.py` – renderer (`ffmpeg`, Pillow, numpy)

```
python3 render_kamaar_popups.py INPUT.mp4 output/kamaar_price_popups.mp4 [--logo logo.png]
```

## Pop-up timing

Triggered on the word that carries the **price** (taken from the word-level
highlight of the burned-in captions, cross-checked against the audio, ±0.1 s).
Each pop-up lasts 1.85 s including a ~0.4 s bounce-in and 0.18 s exit, and is
fully removed before the next one starts (enforced by an assertion).

| Product | Spoken line | Price said at | Pop-up on screen |
|---|---|---|---|
| BANTAL TIDUR – RM5.00 | "harga hanya RM5" | 12.3 s | 12.25 – 14.10 s |
| KAIN REJECT KILANG – RM1.00 / METER | "seringgit saja" | 21.15 s | 21.10 – 22.95 s |
| TILAM TOTO – RM29.00 | "dia RM29 saja" | 27.1 s | 27.05 – 28.90 s |

Other prices in the footage (RM29 quilt at ~15 s, RM10 pillow at ~24 s, RM39
single mattress, RM15 bolster) are intentionally **not** given pop-ups, so a
price can never appear on the wrong product.

Style: white ExtraBold product name above a yellow Black price with a red
outline, on a small translucent navy card centred at y = 1385 (above the
burned-in captions and the platform UI zone).

## End card (47.0 – 52.5 s)

7 & 8 NOVEMBER 2026 · SABTU & AHAD · 9 PAGI – 10 MALAM · DEWAN SERBAGUNA
KAMPUNG TERSUSUN · TAWAS TAMBAHAN, IPOH · 2 HARI SAHAJA! · KAMAAR BEDDINGS logo.

The logo is a typeset stand-in. Pass the official file with `--logo` (PNG with
transparent background) and re-render.
