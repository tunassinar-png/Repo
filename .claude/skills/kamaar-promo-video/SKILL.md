---
name: kamaar-promo-video
description: Build a 9:16 (TikTok / Facebook Reels) promo video for KAMAAR BEDDINGS (Malaysian pillow / mattress / fabric clearance sales) from presenter footage - synchronized price pop-ups on every spoken price, dialogue-synced text pops, a dramatic intro (logo sting, "Kampung Tawas, Ipoh" hook, big date / time / location banners), minimal persistent date + location label, synthesised background music ducked under the voice with synced sound effects, and an event end card with logo; renders Full HD or 2K. Transcribes footage without captions (Whisper via sherpa-onnx). Use when asked for a promo video, price pop-ups, intro, text pops, background music or end card for Kamaar / "Jualan Gudang" / "jelajah" sale footage, or to re-render the Ipoh 7-8 Nov 2026 videos with changes.
---

# KAMAAR BEDDINGS promo video

Turns presenter footage into a finished vertical promo video. The user writes in
Malay; reply in Malay. Worked examples (exact timings, wording, decisions):
`reference/ipoh-nov-2026.md` (video 1, footage with burned-in captions) and
`reference/ipoh-hari1.md` (video 2, no captions: transcribed with Whisper, with music).

## What it produces
- **Price pop-ups**: one per spoken price, bounce-in, product name (white bold) above
  price (yellow bold, subtle red outline) on a small navy card, lower-middle (y 1385).
- **Text pops synced to the dialogue** (`HOOK` list): slam text (yellow/white, red outline,
  glow), red pills, red chips, logo sting. Each pop has its own start / `t_out`.
- **Banners** (`INTRO` list): TARIKH & MASA / LOKASI cards in the empty wall area (y 160-640),
  lines revealed word-by-word with the VO, each with its own `y`, `t_out`, line `t_end`.
- **Impact FX** (`EVENTS`): camera shake, punch zoom, RGB split, flash, speed lines, sparks,
  shock rings, rotating rays, shine sweep.
- **Persistent label**: tiny two-line date + location, top-centre, hidden while a banner
  shows the same info (`LABEL_SHOW` windows).
- **Music + SFX** (`make_music.py`): synthesised upbeat promo track (126 bpm), ducked under
  the voice, plus boom / whoosh / ding / pop / tick effects placed at the config times.
- **End card**: date, day, time, venue, "2 HARI SAHAJA!", KAMAAR BEDDINGS logo.
- **Output**: 1080x1920 (default) or `--width 1440` for 2K (1440x2560); 30 fps.

## Files
- `scripts/render_kamaar_popups.py` - renderer. Defaults = video 1; override per video with
  `--config configs/<video>.py` (any UPPERCASE constant: `POPUPS`, `HOOK`, `INTRO`, `EVENTS`,
  `BADGE`, `RAYS`, `SCRIM`, `LABEL_SHOW`, `OVERLAY_H`, `PREVIEW_T`, ...). Options: `--width`,
  `--logo`, `--vo`, `--music`, `--sfx`, `--preview-dir`. Needs ffmpeg, Pillow, numpy.
- `scripts/make_music.py` - music + SFX WAVs from the config (needs scipy).
- `scripts/asr_setup.sh`, `asr_chunks.py`, `asr_prefix_scan.py`, `asr_window.py` - Whisper
  transcription and word timing for footage without captions.
- `scripts/caption_strips.py` - contact sheet of burned-in word-highlighted captions.
- `scripts/verify_output.py` - ffprobe + audio level + "does the overlay appear at t?" test.
- `configs/ipoh_hari1.py` - video 2 config (copy it as the starting point for a new video).
- `reference/` - the two worked examples.

## Workflow
1. **Understand the footage.** `ffprobe` it. Phone clips are often stored 1920x1080 with a
   -90 rotation: ffmpeg auto-rotates, so decode normally and it is 1080x1920. Make a 1 fps
   contact sheet (`ffmpeg -vf fps=1,scale=216:384,tile=8x6`) and read it: where the
   presenter stands, what is empty (the top wall area), where burned-in captions are (if any).
2. **Get the dialogue and word timing.**
   - *Burned-in word-highlighted captions*: `scripts/caption_strips.py` (`--fps 4` to read,
     `--fps 10` around each price word).
   - *No captions*: `bash scripts/asr_setup.sh turbo DIR` (and `large-v3` for a second opinion;
     Hugging Face is blocked, GitHub release assets and PyPI work). Then `asr_chunks.py`
     (phrase text + accurate phrase start/end from audio pauses), `asr_window.py` with both
     models on overlapping windows around every price/name, and `asr_prefix_scan.py` to time
     each price word. Whisper has no word timestamps in sherpa-onnx; prefix scanning is the
     work-around.
   A price pop-up starts **0.05 s before the word that carries the price**. Cross-check
   speech onsets with the audio energy.
3. **List every spoken price** and map it to its product. One pop-up per mention. Never show a
   price without its product name, on the wrong product, or one that was not spoken.
   **Ask the user** (or flag clearly) when the transcript is uncertain: Whisper mishears
   product words (see Rules). Use the user's own product names/wording for the cards.
4. **Write a config** (copy `configs/ipoh_hari1.py`): popups, text pops (`HOOK`), banners
   (`INTRO`), `EVENTS` (one per slam/banner/price card so flash/shake/SFX line up), `RAYS`,
   `SCRIM`, `LABEL_SHOW`, music sections/risers. If two prices are < 1.85 s apart, swap the
   card content (`then=`). Enlarge key numbers with name parts, e.g.
   `[("SARUNG BANTAL ", 1.0, "W"), ("4", 2.3, "Y"), (" HELAI", 1.0, "W")]`.
5. **Preview**: render with `--preview-dir` (config `PREVIEW_T` names the frames), montage the
   frames and read them. Test big layout changes on a trimmed copy (`ffmpeg -t 12.5 -c copy`).
6. **Music + SFX**: `python3 -B -I scripts/make_music.py IN.mp4 CONFIG.py DIR` then render with
   `--music DIR/music_ducked.wav --sfx DIR/sfx.wav`. Check levels (voice -8 dBFS RMS, music
   ~10 dB under the voice, ~ -12 dBFS in pauses, final about -12 LUFS).
7. **Render the finals**: 1080 (~1.7 min) and `--width 1440` (~5 min; start it with
   `run_in_background` on the script itself and poll the log; the 1080 + 2K encodes are tuned to
   ~30 MB / ~45 MB so they open in the app).
8. **Verify the real output**: `scripts/verify_output.py OUT.mp4 IN.mp4 --times ... --audio-at ...`,
   ffprobe, and `ffmpeg -af ebur128=peak=true` (true peak must stay below 0 dBTP).
9. **Deliver**: `SendUserFile` (display `attach`), commit and push to the session's designated
   branch (outputs go in `promosi-jelajah/` unless told otherwise). Short Malay summary: what
   was added, what needs confirming. Do not open a PR unless asked.

## Rules and gotchas
- Footage is 1080x1920; 2K only upscales it (Lanczos + light sharpen). Graphics are native 2K.
- Positions: price cards y 1385; burned-in captions (video 1) ~y 1650; platform UI zones are the
  top ~150 px and bottom ~250 px; banners/text pops live at y 160-640 because the presenter's
  head starts ~y 660 (check each new footage; a presenter who walks toward the camera needs the
  banner gone before his head rises).
- Keep persistent text minimal (small, outlined, no box).
- **Voice**: the voice is the presenter's. This environment cannot generate voice-over; the end
  card has no VO unless the user supplies a file (`--vo`).
- **Music**: it is synthesised here (royalty-free, no copyrighted track copied). Claude cannot
  listen to audio: say so, verify only by numbers, and tell the user to check it and that a
  WAV of their own track can replace it (`--music`). Never claim it was heard.
- Logo is a typeset stand-in until the user supplies a transparent PNG (`--logo`).
- Whisper errors seen: "tilam tutuh/tutur" = Tilam Toto; "kain elok/elak/crane" ~ kain reject;
  "pantai" = bantal (Northern accent); "Dewan Surbaguna" = Dewan Serbaguna; "Kampung Tawas
  Tambahan" = Kampung Tersusun, Tawas Tambahan; a breath became "Terima kasih"; turbo looped
  "7 dan 8 November" three times. Prefer agreement of two models + the user's own wording.
- Venue/brand wording comes from the user's brief: "DEWAN SERBAGUNA KAMPUNG TERSUSUN, TAWAS
  TAMBAHAN, IPOH"; products BANTAL TIDUR, TILAM TOTO, KAIN REJECT KILANG (RM1.00 / METER).
- Audio mix: voice x0.72, `alimiter=limit=0.80` (AAC overshoots ~+2 dB; limit 0.89 gave
  +1.2 dBTP). The phone voice is already very hot (-8 dBFS RMS, peaks 0 dB).
- Sharing: a 78 MB 2K file failed to open for the user; keep 2K ~45 MB (crf 22, maxrate 9M).
- You cannot save to the user's Photos or Downloads (cloud container); only a connected Remote
  Control computer folder can be written (`list_computer_folders`). Otherwise tell them to
  download from the chat card or the repo.
- Tooling pitfalls: a background command ending with `&` finishes its task immediately (use
  `run_in_background` on the command itself); `pgrep -f NAME` in a wait loop matches itself
  (poll the output file or use `pgrep -f "[N]AME"`); use `python3 -B -I` and delete
  `__pycache__` so the repo stays clean for the stop hook; the shell cwd may change, so use
  absolute paths.
