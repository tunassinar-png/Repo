"""Shared content: narration, subtitle chunks, labels. Times in seconds."""
SCENES = [
 dict(a=0.4, b=9.4, label="BAGAIMANA JIKA SEMUA WANITA CANTIK?",
      vo="Pernah tak anda terfikir… apa akan jadi kalau semua wanita dalam dunia ini cantik? Adakah dunia akan menjadi lebih indah?",
      subs=["Pernah tak anda terfikir… apa akan jadi kalau semua wanita dalam dunia ini cantik?", "Adakah dunia akan menjadi lebih indah?"]),
 dict(a=10.4, b=19.4, label="KECANTIKAN MENJADI NORMAL",
      vo="Pada mulanya, mungkin semua orang akan terpesona. Tetapi apabila semua orang cantik, kecantikan mungkin tidak lagi dianggap sesuatu yang luar biasa.",
      subs=["Pada mulanya, mungkin semua orang akan terpesona.", "Tetapi apabila semua orang cantik, kecantikan mungkin tidak lagi dianggap sesuatu yang luar biasa."]),
 dict(a=20.4, b=29.4, label="STANDARD KECANTIKAN BERUBAH",
      vo="Manusia mungkin mula mencari sesuatu yang lain untuk membezakan seseorang. Gaya, personaliti, keyakinan dan keunikan diri menjadi perhatian.",
      subs=["Manusia mungkin mula mencari sesuatu yang lain untuk membezakan seseorang.", "Gaya, personaliti, keyakinan dan keunikan diri menjadi perhatian."]),
 dict(a=30.4, b=39.4, label="CANTIK TIDAK SEMESTINYA BAHAGIA",
      vo="Tetapi adakah semua wanita akan lebih bahagia? Tidak semestinya. Kerana kecantikan tidak menjamin kebahagiaan, kejayaan ataupun hubungan yang sempurna.",
      subs=["Tetapi adakah semua wanita akan lebih bahagia? Tidak semestinya.", "Kerana kecantikan tidak menjamin kebahagiaan, kejayaan ataupun hubungan yang sempurna."]),
 dict(a=40.4, b=49.4, label="NILAI DIRI LEBIH DARIPADA RUPA",
      vo="Akhirnya, manusia mungkin semakin menghargai perkara yang lebih mendalam. Kebijaksanaan, kejujuran, kebaikan hati dan cara seseorang melayan orang lain.",
      subs=["Akhirnya, manusia mungkin semakin menghargai perkara yang lebih mendalam.", "Kebijaksanaan, kejujuran, kebaikan hati dan cara seseorang melayan orang lain."]),
 # Scene 6 trimmed ("Persoalannya," removed) so the narration fits 10 s together with the end question.
 dict(a=50.0, b=59.0, label=None,
      vo="Jadi, jika semua wanita di dunia ini cantik… mungkin yang berubah bukan dunia, tetapi cara kita menilai kecantikan. Apakah sebenarnya yang membuat seseorang itu cantik?",
      subs=["Jadi, jika semua wanita di dunia ini cantik… mungkin yang berubah bukan dunia,", "tetapi cara kita menilai kecantikan.", "Apakah sebenarnya yang membuat seseorang itu cantik?"]),
]
LABEL_WIN = [(0.6, 9.4), (10.6, 19.4), (20.6, 29.4), (30.6, 39.4), (40.6, 49.4)]


def sub_cues():
    """Subtitle cues (start, end, text); time split proportional to text length inside each scene window."""
    cues = []
    for s in SCENES:
        tot = sum(len(x) for x in s['subs'])
        t = s['a']
        span = s['b'] - s['a'] - 0.12 * (len(s['subs']) - 1)
        for x in s['subs']:
            d = span * len(x) / tot
            cues.append((t, t + d, x))
            t += d + 0.12
    return cues


def srt_time(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(path):
    with open(path, 'w', encoding='utf-8') as f:
        for i, (a, b, x) in enumerate(sub_cues(), 1):
            f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{x}\n\n")
