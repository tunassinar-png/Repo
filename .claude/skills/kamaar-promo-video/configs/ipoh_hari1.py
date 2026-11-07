"""
Config: Ipoh clearance sale 7 & 8 Nov 2026 - DAY-1 presenter video (IMG_1401, 44.9 s).

Dialogue (Whisper large-v3 + turbo, word times from prefix-decoding, +/-0.1 s):
  1.23 Assalamualaikum warga-warga Kampung Tawas, Ipoh   (Kampung 3.15, Ipoh 3.95)
  4.56 Ok, hari ni kami dah sampai dekat Dewan Serbaguna, Kampung Tersusun, Tawas Tambahan
       (kami dah sampai 5.35, Dewan 6.3, Kampung 7.55, Tawas 8.3)
  9.36 Kita akan berada di sini dua hari
 11.24 Bermula pada hari ini 7 November dan juga esok 8 November (7: 12.3, 8: 14.5),
       hari Sabtu dan Ahad (15.9), 9 pagi sampai 10 malam (17.3)
 19.29 Dua hari saja, abang kakak
 20.99 Kita bawa apa? Kita bawa bantal harga lima ringgit        (RM5 23.15)
 24.41 Kita bawa Tilam Toto ni dua puluh sembilan ringgit        (RM29 25.9)
 27.41 Kita ada kain (reject kilang) yang harga semeter, seringgit (seringgit 29.55) - user's wording: KAIN ELA 1 METER RM1
 30.31 Jadi jangan lupa / 31.85 untuk hari Sabtu dan hari Ahad / 33.47 7 dan 8 November
 35.33 Kami akan berada di sini / 37.53 Jadi mai ramai-ramai di Dewan Serbaguna Kampung
       Tersusun, Tawas Tambahan (42.1)
Run:  make_music.py IN.mp4 configs/ipoh_hari1.py OUT_DIR
      render_kamaar_popups.py IN.mp4 OUT.mp4 --config configs/ipoh_hari1.py \
          --music OUT_DIR/music_ducked.wav --sfx OUT_DIR/sfx.wav [--width 1440]
"""
_Y, _R, _W = (255, 212, 0), (225, 20, 30), (255, 255, 255)

# ---- price pop-ups (one per spoken price; start 0.05 s before the price word) ----
POPUPS = [
    dict(name="BANTAL TIDUR", price="RM5.00", suffix=None, t_in=23.05),
    dict(name="TILAM TOTO", price="RM29.00", suffix=None, t_in=25.80),
    # user: "kain ela 1 meter RM1" (Whisper heard "kain elok/elak"); big 1 METER + RM1
    dict(name=[("KAIN ELA  ", 1.0, "W"), ("1 METER", 2.0, "Y")], price="RM1", suffix=None,
         t_in=29.45, dur=2.0, opts=dict(price_size=150, max_name_w=840, min_w=700)),
]

# ---- text pops synced to the dialogue ----
HOOK_OUT = 5.2
HOOK = [
    dict(kind="logo", text="", t=0.15, t_out=1.15, cy=430),                      # brand sting
    dict(kind="chip", text="ASSALAMUALAIKUM", t=1.30, t_out=2.20, cy=300),
    dict(kind="chip", text="WARGA-WARGA", t=2.30, t_out=5.2, cy=300),
    dict(kind="slam", text="KAMPUNG TAWAS", size=104, fill=_Y, stroke=7, glow=_Y, t=3.12, t_out=5.2, cy=420),
    dict(kind="slam", text="IPOH", size=210, fill=_W, stroke=9, glow=_R, t=3.92, t_out=5.2, cy=602),
    dict(kind="slam", text="KAMI DAH SAMPAI!", size=100, fill=_W, stroke=7, glow=_Y, t=5.35, t_out=6.2, cy=430),
    dict(kind="pill", text="2 HARI SAHAJA!", size=66, t=19.30, t_out=20.7, cy=430),
    dict(kind="slam", text="KITA BAWA APA?", size=110, fill=_W, stroke=7, glow=_Y, t=21.00, t_out=22.4, cy=430),
    dict(kind="slam", text="JANGAN LUPA!", size=122, fill=_Y, stroke=8, glow=_Y, t=30.40, t_out=31.6, cy=430),
    dict(kind="chip", text="KAMI AKAN BERADA DI SINI", t=35.40, t_out=37.4, cy=300),
    dict(kind="slam", text="MAI RAMAI-RAMAI!", size=104, fill=_Y, stroke=7, glow=_Y, t=38.15, t_out=39.4, cy=430),
]
BADGE = None

# ---- date / time / location banners (top wall area, y 160-640) ----
INTRO = [
    dict(tag="LOKASI", t_in=6.30, t_out=9.30, h=240, y=160, lines=[
        ("DEWAN SERBAGUNA", "ExtraBold", 58, "plain", 66, 6.30),
        ("KAMPUNG TERSUSUN", "ExtraBold", 58, "plain", 130, 7.50),
        ("TAWAS TAMBAHAN, IPOH", "Black", 52, "outline", 196, 8.30)]),
    dict(tag="TARIKH & MASA", t_in=12.20, t_out=18.95, h=290, y=160, lines=[
        ("HARI INI: 7 NOVEMBER", "Black", 64, "outline", 70, 12.20),
        ("ESOK: 8 NOVEMBER", "Black", 64, "outline", 140, 14.40),
        ("SABTU & AHAD", "ExtraBold", 40, "pill_w", 226, 15.85),
        ("9 PAGI – 10 MALAM", "Black", 40, "pill_y", 226, 17.25)]),
    dict(tag="TARIKH", t_in=31.85, t_out=35.25, h=200, y=160, lines=[
        ("SABTU & AHAD", "ExtraBold", 56, "plain", 68, 31.85),
        ("7 & 8 NOVEMBER 2026", "Black", 72, "outline", 138, 33.45)]),
    dict(tag="LOKASI", t_in=39.45, t_out=43.90, h=240, y=160, lines=[
        ("DEWAN SERBAGUNA", "ExtraBold", 58, "plain", 66, 39.45),
        ("KAMPUNG TERSUSUN", "ExtraBold", 58, "plain", 130, 40.70),
        ("TAWAS TAMBAHAN, IPOH", "Black", 52, "outline", 196, 41.30)]),
]

# ---- impact effects: flash / shake / punch zoom / RGB split / speed lines / sparks ----
_STRONG = dict(flash=0.85, shake=30, punch=0.10, chroma=10, ring=True, lines=True)
EVENTS = [
    dict(t=0.15, flash=0.70, shake=18, punch=0.08, ring=True, burst=(540, 430, 110)),   # logo sting
    dict(t=3.12, **_STRONG, burst=(540, 420, 170)),                                    # KAMPUNG TAWAS
    dict(t=3.92, flash=0.95, shake=40, punch=0.13, chroma=14, ring=True, lines=True, burst=(540, 595, 220)),
    dict(t=5.35, flash=0.60, shake=22, punch=0.07, ring=True, burst=(540, 430, 110)),
    dict(t=6.30, flash=0.30, shake=8, burst=(540, 280, 60)),
    dict(t=12.20, flash=0.30, shake=8, burst=(540, 305, 60)),
    dict(t=19.30, **_STRONG, burst=(540, 430, 170)),                                   # 2 HARI SAHAJA
    dict(t=21.00, flash=0.55, shake=20, punch=0.06, ring=True, burst=(540, 430, 110)),  # KITA BAWA APA?
    dict(t=23.05, flash=0.25, shake=6, burst=(540, 1385, 50)),                         # price cards
    dict(t=25.80, flash=0.25, shake=6, burst=(540, 1385, 50)),
    dict(t=29.45, flash=0.25, shake=6, burst=(540, 1385, 50)),
    dict(t=30.40, flash=0.80, shake=28, punch=0.09, chroma=8, ring=True, lines=True, burst=(540, 430, 150)),
    dict(t=31.85, flash=0.30, shake=8, burst=(540, 260, 60)),
    dict(t=38.15, flash=0.90, shake=34, punch=0.11, chroma=12, ring=True, lines=True, burst=(540, 430, 200)),
    dict(t=39.45, flash=0.30, shake=8, burst=(540, 280, 60)),
]
OVERLAY_H = 1920                      # sparks also fire at the price cards (y 1385)
RAYS = [(3.12, 5.45), (38.15, 39.55)]
SCRIM = [(0.6, 44.6)]
SCRIM_STRENGTH = 0.50

# ---- minimal persistent label: hidden while a big banner shows the same info ----
LABEL_SHOW = [(1.3, 6.0), (9.5, 12.0), (19.2, 31.7), (35.3, 39.3)]

# ---- music: drop on the KAMPUNG TAWAS slam, lighter under the date/time list, big finish ----
MUSIC_ANCHOR = 3.12
MUSIC_SECTIONS = [(0.0, 3.12, 2), (3.12, 11.0, 3), (11.0, 19.0, 2), (19.0, 35.2, 3),
                  (35.2, 38.1, 2), (38.1, 44.88, 4), (44.88, 60.0, 3)]
MUSIC_RISERS = [(0.75, 3.12), (35.5, 38.15)]
MUSIC_GAIN_DB = -12
MUSIC_DUCK_DB = -10

PREVIEW_T = {0.30: "a_logo", 1.50: "b_assalam", 3.20: "c_kampung", 4.05: "d_ipoh", 4.70: "e_hook",
             5.55: "f_kami", 7.00: "g_lokasi", 8.70: "h_lokasi_full", 12.60: "i_tarikh",
             15.00: "j_esok", 17.80: "k_masa", 19.60: "l_2hari", 21.30: "m_kitabawa",
             23.50: "n_bantal", 26.30: "o_tilam", 29.90: "p_kain", 30.70: "q_jangan",
             33.90: "r_tarikh2", 36.00: "s_kami_disini", 38.50: "t_mai", 41.60: "u_lokasi",
             44.00: "v_last"}
