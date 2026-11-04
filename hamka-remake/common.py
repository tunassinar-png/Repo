import cv2, numpy as np
FPS=30
# (start_frame, end_frame_exclusive, text, kind, x1_of_original_text)   kind: q = quote, l = lyric
SEGS=[
 (0,   49, 'jangan takut jatuh',                 'q', 685),
 (54,  89, 'kerana yang tidak pernah',           'q', 746),
 (89, 161, 'memanjatlah yang tidak pernah jatuh','q', 869),
 (173,219, 'jangan takut gagal',                 'q', 685),
 (234,288, 'kerana yang tidak pernah gagal',     'q', 806),
 (301,333, 'hanyalah orang-orang',               'q', 715),
 (333,384, 'yang tidak pernah melangkah',        'q', 793),
 (397,444, 'jangan takut salah',                 'q', 686),
 (453,520, 'karena dengan kesalahan yang pertama','q', 885),
 (529,564, 'kita dapat menambah',                'q', 712),
 (564,619, 'pengetahuan untuk mencari',          'q', 778),
 (619,654, 'Jalan yang benar',                   'q', 669),
 (662,708, 'pada langkah yang ke-2',             'q', 733),
 (710,818, 'Cinta kan selalu abadi',             'l', 705),
 (827,921, 'walau takdir tak pasti',             'l', 705),
]
ATTR_END=708          # original "- Buya Hamka -" present until here
TITLE_START=964       # film title card begins (frame idx)
LOGO_TL_END=150       # tiktok watermark top-left until this frame, bottom-right afterwards
K11=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(11,11))
E5=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(5,5))
E9=cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9))
def seg_at(n):
    for s in SEGS:
        if s[0]-3<=n<s[1]+3: return s
    return None
def _strokes(g, box, thr=38, lum=175):
    x0,y0,x1,y1=box
    sub=g[y0:y1,x0:x1]
    th=cv2.morphologyEx(sub,cv2.MORPH_TOPHAT,K11)
    m=np.zeros(g.shape,np.uint8)
    m[y0:y1,x0:x1]=((th>thr)&(sub>lum)).astype(np.uint8)*255
    return m
def clean_frame(img, n):
    """remove burnt-in subtitle + tiktok watermark from 1024x576 BGR frame"""
    g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    mask=np.zeros(g.shape,np.uint8)
    s=seg_at(n)
    if s is not None:
        x1=s[4]+10; x0=1024-x1
        m=_strokes(g,(x0,258,x1,330))
        cnt=cv2.boxFilter((m>0).astype(np.float32),-1,(41,41))
        keep=cv2.dilate(((cnt>0.035)).astype(np.uint8)*255,E9)
        mask|=cv2.bitwise_and(m,keep)
    if n<=ATTR_END+2:
        mask|=_strokes(g,(405,355,625,392),thr=34,lum=165)
    # tiktok watermark (stroke-based so we do not smear a whole rectangle)
    if n<LOGO_TL_END+2: mask|=_strokes(g,(6,4,132,102),thr=30,lum=150)
    if n>=LOGO_TL_END-1: mask|=_strokes(g,(900,472,1022,572),thr=30,lum=150)
    if mask.any():
        mask=cv2.dilate(mask,E9); mask=cv2.dilate(mask,E5)
        img=cv2.inpaint(img,mask,4,cv2.INPAINT_TELEA)
    return img
