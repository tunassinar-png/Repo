"""
Config: Kulim sale 12 Nov 2026 (Dewan Masjid Al-Fatih) - presenter video "copy_F7E8DC9F" (47.04 s),
4:5 (1080x1350; --width 1440 -> 1440x1800).

Footage = the Ipoh hall video re-edited: the audio is IDENTICAL from 11.5 s on (correlation
0.999 at lag 0), so every price time below is the one measured in video 1; only 0-11 s is new
dialogue, read from the burned-in word-highlighted yellow captions (4 fps, +/-0.12 s) and
confirmed by Whisper turbo + large-v3:
  0.2  Cari bantal dan tilam jom ke              (Cari 0.3, tilam 0.95)
  1.7  Dewan Masjid Al-Fatih                      (Dewan 1.7, Al-Fatih 2.2)
  2.55 Taman Mutiara
  3.25 Sungai Kob, Kulim                          (Kob: caption spelling; Whisper wrote "Kop")
  4.5  pada 12/11/2026 (12 November 2026)         (hari Khamis 6.25)
  7.0  dari 9.00 pagi (7.2) hingga 10 malam (8.0)
  9.0  bantal dan tilam pelbagai corak
  11.0+ same as video 1 (prices, kain, sarung bantal, Tilam Toto, Tilam single, bantal peluk ...)
The burned-in captions of this footage sit at y 1445-1555 of the 1080x1920 frame, so the 4:5
crop window is y 80..1430 (CROP_Y = 80) and the captions are cropped out.
Run: make_music.py IN.mp4 THIS.py DIR ; render_kamaar_popups.py IN.mp4 OUT.mp4 --config THIS.py
     --music DIR/music_ducked.wav --sfx DIR/sfx.wav [--width 1440]
"""
_Y, _R, _W = (255, 212, 0), (225, 20, 30), (255, 255, 255)

H = 1350
CROP_Y = 80
POPUP_CENTER_Y = 1150
LABEL_CY = 62
RAYS_CY = 340
SCRIM_H = 700
OVERLAY_H = 1350
END_CARD_DY = -260
BADGE = None

LABEL_LINES = [("12 NOV 2026", "ExtraBold", 36, "Y"),
               ("DEWAN MASJID AL-FATIH, TAMAN MUTIARA, SUNGAI KOB, KULIM", "Bold", 24, "W")]
LABEL_SHOW = [(0.3, 4.3), (9.0, 47.0)]

END_CARD = dict(date="12 NOVEMBER 2026", day="KHAMIS", time="9 PAGI – 10 MALAM",
                venue=["DEWAN MASJID AL-FATIH", "TAMAN MUTIARA"], place="SUNGAI KOB, KULIM",
                badge="JOM KE SINI!")     # "jom ke ..." is in the dialogue; no "1 hari" claim

# ---- price pop-ups: times from video 1 (same audio) ----
POPUPS = [
    dict(name="BANTAL TIDUR", price="RM5.00", suffix=None, t_in=12.25),
    dict(name="6 BIJI BANTAL", price="RM29.00", suffix=None, t_in=15.80),
    dict(name="KAIN REJECT KILANG", price="RM1", suffix="/ 1 METER", t_in=18.70, opts=dict(price_size=150)),
    dict(name="KAIN REJECT KILANG", price="RM1", suffix="/ 1 METER", t_in=21.10, opts=dict(price_size=150)),
    dict(name=[("SARUNG BANTAL ", 1.0, "W"), ("4", 2.3, "Y"), (" HELAI", 1.0, "W")],
         price="RM10.00", suffix=None, t_in=24.25),
    dict(name="TILAM TOTO", price="RM29.00", suffix=None, t_in=27.05),
    dict(name="TILAM SINGLE", price="RM39.00", suffix=None, t_in=29.55, dur=2.65,
         then=dict(t=30.50, name=[("TILAM SINGLE  ", 1.0, "W"), ("3 BIJI", 2.0, "Y")],
                   price="RM100", suffix=None,
                   opts=dict(price_size=150, max_name_w=840, min_w=700))),
    dict(name="BANTAL PELUK", price="RM15.00", suffix=None, t_in=34.35),
]

# ---- text pops synced to the dialogue (pairs: small yellow line + big white line) ----
def _slam(text, size, fill, glow, t, t_out, cy, stroke=7):
    return dict(kind="slam", text=text, size=size, fill=fill, stroke=stroke, glow=glow, t=t, t_out=t_out, cy=cy)

HOOK = [
    _slam("CARI BANTAL", 112, _Y, _Y, 0.30, 1.60, 250),
    _slam("& TILAM?", 190, _W, _R, 0.95, 1.60, 410, 9),
    _slam("DEWAN MASJID", 104, _Y, _Y, 1.70, 3.20, 250),
    _slam("AL-FATIH", 190, _W, _R, 2.20, 3.20, 410, 9),
    _slam("TAMAN MUTIARA", 84, _W, _Y, 2.55, 3.20, 545, 6),
    _slam("SUNGAI KOB", 108, _Y, _Y, 3.25, 4.40, 250),
    _slam("KULIM", 190, _W, _R, 3.75, 4.40, 410, 9),
    _slam("BANTAL & TILAM", 100, _Y, _Y, 9.00, 10.90, 250),
    _slam("PELBAGAI CORAK!", 112, _W, _Y, 9.75, 10.90, 395),
    _slam("TAK KIRA NIPIS", 96, _Y, _Y, 19.25, 21.20, 235),
    _slam("TAK KIRA TEBAL", 96, _W, _Y, 20.15, 21.20, 350),
    _slam("MACAM-MACAM BARANG!", 100, _Y, _Y, 38.75, 40.40, 270),
    _slam("JANGAN LUPA!", 122, _Y, _Y, 45.05, 46.00, 270, 8),
    dict(kind="chip", text="TUNGGU JANJI KITA", t=45.80, t_out=47.0, cy=145),
]

# ---- date / time banner: "pada 12/11/2026 hari Khamis dari 9 pagi hingga 10 malam" ----
INTRO = [
    dict(tag="TARIKH & MASA", t_in=4.45, t_out=8.90, h=210, y=120, lines=[
        ("12 NOVEMBER 2026", "Black", 72, "outline", 70, 4.45),
        ("KHAMIS", "ExtraBold", 44, "pill_w", 150, 6.20),
        ("9 PAGI – 10 MALAM", "Black", 40, "pill_y", 150, 7.15)]),
]

# ---- impact effects ----
_STRONG = dict(flash=0.85, shake=30, punch=0.10, chroma=10, ring=True, lines=True)
_MID = dict(flash=0.55, shake=20, punch=0.06, ring=True)
_CARD = dict(flash=0.25, shake=6)
EVENTS = [
    dict(t=0.30, **_STRONG, burst=(540, 250, 170)),
    dict(t=0.95, **_MID, burst=(540, 410, 110)),
    dict(t=1.70, **_STRONG, burst=(540, 250, 170)),
    dict(t=2.20, flash=0.70, shake=26, punch=0.08, chroma=8, ring=True, burst=(540, 410, 140)),
    dict(t=2.55, flash=0.25, shake=6, burst=(540, 545, 50)),
    dict(t=3.25, **_STRONG, burst=(540, 250, 170)),
    dict(t=3.75, flash=0.90, shake=34, punch=0.11, chroma=12, ring=True, lines=True, burst=(540, 410, 180)),
    dict(t=4.45, flash=0.30, shake=8, burst=(540, 230, 60)),
    dict(t=6.20, flash=0.15, shake=0),
    dict(t=7.15, flash=0.15, shake=0),
    dict(t=9.00, **_STRONG, burst=(540, 250, 170)),
    dict(t=9.75, flash=0.80, shake=28, punch=0.09, chroma=8, ring=True, lines=True, burst=(540, 395, 150)),
    dict(t=12.25, **_CARD, burst=(540, 1150, 50)),
    dict(t=15.80, **_CARD, burst=(540, 1150, 50)),
    dict(t=18.70, **_CARD, burst=(540, 1150, 50)),
    dict(t=19.25, **_MID, burst=(540, 235, 110)),
    dict(t=20.15, **_MID, burst=(540, 350, 110)),
    dict(t=21.10, **_CARD, burst=(540, 1150, 50)),
    dict(t=24.25, **_CARD, burst=(540, 1150, 50)),
    dict(t=27.05, **_CARD, burst=(540, 1150, 50)),
    dict(t=29.55, **_CARD, burst=(540, 1150, 50)),
    dict(t=30.50, flash=0.35, shake=10, burst=(540, 1150, 70)),
    dict(t=34.35, **_CARD, burst=(540, 1150, 50)),
    dict(t=38.75, **_STRONG, burst=(540, 270, 170)),
    dict(t=45.05, **_STRONG, burst=(540, 270, 170)),
    dict(t=45.80, flash=0.20, shake=0),
]
RAYS = [(0.30, 1.60), (1.70, 3.20), (3.25, 4.45), (9.0, 10.9), (45.05, 46.1)]
SCRIM = [(0.0, 11.2), (19.0, 21.4), (38.6, 40.6), (44.9, 47.0)]
SCRIM_STRENGTH = 0.50

# ---- music: drop on the first hit; lighter under the date/time banner; lead for the finish ----
MUSIC_ANCHOR = 0.30
MUSIC_SECTIONS = [(0.0, 4.4, 3), (4.4, 8.9, 2), (8.9, 36.0, 3), (36.0, 45.0, 4), (45.0, 60.0, 3)]
MUSIC_RISERS = [(7.0, 9.0), (42.6, 45.05)]
MUSIC_GAIN_DB = -12
MUSIC_DUCK_DB = -10

PREVIEW_T = {0.45: "a_cari", 1.20: "b_tilam", 1.90: "c_dewan", 2.40: "d_alfatih", 2.70: "e_taman",
             3.50: "f_sungai", 3.95: "g_kulim", 5.20: "h_tarikh", 6.60: "i_khamis", 7.80: "j_masa",
             9.30: "k_bantal", 10.10: "l_corak", 12.60: "m_rm5", 16.30: "n_6biji", 19.00: "o_kain1",
             19.60: "p_nipis", 20.50: "q_tebal", 24.90: "r_sarung", 27.60: "s_toto", 30.00: "t_single",
             31.20: "u_3biji", 34.90: "v_peluk", 39.20: "w_macam", 45.40: "x_jangan", 46.40: "y_janji"}
