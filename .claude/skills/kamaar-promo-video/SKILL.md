---
name: kamaar-promo-video
description: Build a 9:16 (TikTok / Facebook Reels) promo video for KAMAAR BEDDINGS (Malaysian pillow / mattress / fabric clearance sales) from presenter footage - synchronized price pop-ups on every spoken price, a dramatic intro (big date / time / location, "Kampung Tawas, Ipoh" hook), a minimal persistent date + location label, and an event end card with logo; renders Full HD or 2K. Use when asked for a promo video, price pop-ups, intro or end card for Kamaar / "Jualan Gudang" / "jelajah" sale footage, or to re-render the Ipoh 7-8 Nov 2026 video with changes.
---

# KAMAAR BEDDINGS promo video

Turns presenter footage into a finished vertical promo video. The user writes in
Malay; reply in Malay. Everything below was learned building the Ipoh 7 & 8 Nov 2026
video - see `reference/ipoh-nov-2026.md` for that video's exact timings and wording.

## What it produces
- **Price pop-ups**: one per spoken price, bounce-in, product name (white bold) above
  price (yellow bold, subtle red outline) on a small navy card, lower-middle (y 1385).
- **Intro**: "KEPADA WARGA / KAMPUNG TAWAS / IPOH" slam hook, then big TARIKH & MASA and
  LOKASI banners revealed line by line with the VO, then a "2 HARI SAHAJA!" slam.
  Effects: camera shake, punch zoom, RGB split, flash, speed lines, sparks, shock rings,
  rotating rays, shine sweep.
- **Persistent label**: tiny two-line date + location, top-centre, hidden while the big
  intro banners show the same info.
- **End card**: date, day, time, venue, "2 HARI SAHAJA!", KAMAAR BEDDINGS logo.
- **Output**: 1080x1920 (default) or `--width 1440` for 2K (1440x2560).

## Files
- `scripts/render_kamaar_popups.py` - the renderer. All content is configured by
  constants at the top: `POPUPS`, `INTRO`, `HOOK`, `BADGE`, `EVENTS`, `LABEL_*`,
  `END_CARD_SECONDS`. Needs `ffmpeg`, Pillow, numpy; Inter fonts (falls back to DejaVu).
- `scripts/caption_strips.py` - contact sheet of the burned-in caption strip (word timing).
- `scripts/verify_output.py` - ffprobe + audio level + "does the overlay appear at t?" test.
- `reference/ipoh-nov-2026.md` - the finished video's full config as a worked example.

## Workflow
1. **Understand the footage.** `ffprobe` it (size, audio, fps). Make a 1 fps contact sheet
   (`ffmpeg -vf fps=1,scale=216:384,tile=8x6`) and read it: what is shown, where the
   presenter stands, what is empty (the top wall area is usually free), where the burned-in
   captions are (about y 1595-1705).
2. **Get word-level timing.** No speech-to-text is normally installed. If the footage has
   word-highlighted burned-in captions, use `scripts/caption_strips.py`: first `--fps 4` over
   12 s windows to read every line, then `--fps 10` over ~0.6 s around each price word. A
   pop-up starts **0.05 s before the word that carries the price** (not the product name).
   Cross-check against the audio energy (dips at speech onsets). If there are no captions,
   try to install an ASR, otherwise ask the user for times.
3. **List every price mention** and map each to its product. Show a pop-up for **every**
   spoken price (the same product twice = two pop-ups). Never show a price without its
   product name, never on the wrong product, never a price that was not spoken.
   **Ask the user** when a caption is ambiguous (e.g. "RM tiga seratus" turned out to be
   "3 biji for RM100") instead of guessing or silently skipping.
4. **Edit the config constants** in a copy/branch of the renderer. Keep pop-ups from
   overlapping (the script asserts it); if two prices are < 1.85 s apart, swap the content
   of one card (`then=`) instead of stacking two. Use name parts to enlarge key numbers,
   e.g. `[("SARUNG BANTAL ", 1.0, "W"), ("4", 2.3, "Y"), (" HELAI", 1.0, "W")]`.
5. **Render** with previews:
   `python3 -B -I scripts/render_kamaar_popups.py IN.mp4 OUT.mp4 --preview-dir DIR [--width 1440]`
   (1080 ~50 s; 2K ~3 min for 52 s. Run 2K in the background and poll the log/output dir.)
   Test intro/layout changes first on a trimmed copy (`ffmpeg -t 12.5 -c copy`).
6. **Verify the real output, not just previews**: montage of preview frames; then
   `scripts/verify_output.py OUT.mp4 IN.mp4 --times <just before/after each pop-up> --audio-at ...`
   (region diff ~2 = nothing, >>10 = overlay) and check ffprobe (size, h264, yuv420p, aac).
7. **Deliver**: `SendUserFile` the video (display `attach`), commit and push to the session's
   designated branch, put the user's chosen project folder in the repo if they ask. Give a
   short Malay summary: what changed, what needs their confirmation.

## Rules and gotchas
- Footage is 1080x1920; 2K only upscales it (Lanczos + light sharpen). Graphics are native
  2K. Say so honestly; do not promise more detail.
- Pop-up position: y 1385 (lower-middle). Captions burned into the footage sit at ~y 1650,
  platform UI zones are the top ~150 px and bottom ~250 px. Intro banners live at y 160-640
  because the presenter's head starts ~y 660.
- Keep the **persistent text minimal** (user's request): small, outlined, no box.
- The voice in the footage is the presenter's. This environment cannot generate voice-over;
  the end card is silent unless the user supplies a file (`--vo`). Do not claim otherwise.
- The logo is a typeset stand-in until the user supplies a transparent PNG (`--logo`).
- Caption transcripts have errors ("pantai" = "bantal" in Northern accent). Use the
  items on screen to confirm the product.
- Audio: the footage audio is kept 0 to end of footage with a 0.35 s fade; verify it with
  `volumedetect` (about -6 to -13 dB while speaking). If a user says "no sound", check the
  file first, then explain the end card is silent and some preview players mute video.
- Sharing: 2K at crf 20 is ~78 MB and failed to open for the user; a crf 24 / maxrate 7M
  re-encode (~43 MB) is the safe alternative, and the 1080 file (~36 MB) is the fallback.
- You cannot save to the user's Photos or Downloads (cloud container). Only a connected
  Remote Control computer folder can be written to (`list_computer_folders`). Otherwise tell
  them to download from the chat card or the repo.
- Tooling pitfalls seen: a background command ending with `&` finishes its task
  immediately (use `run_in_background` on the command itself); a wait loop with
  `pgrep -f NAME` matches itself and never ends (use `pgrep -f "[N]AME"` or poll the output
  file); clean `__pycache__` (use `python3 -B -I`) so the repo stays clean for the stop hook.
- Do not open a pull request unless asked; develop on the designated branch.
