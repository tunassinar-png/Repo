"""
Config: Ipoh day-1 video in 4:5 (1080x1350; --width 1440 -> 1440x1800).

Same dialogue timings, popups, banners and effects as ipoh_hari1.py (9:16); only the canvas
and the layout change. The 1080x1920 footage is cropped to a 1080x1350 window starting at
CROP_Y = 150 (cuts 150 px of ceiling and 420 px of floor/legs): the presenter's head sits at
y ~ 510 in the crop (it was ~660 in 9:16), so the banners / text pops live in y 60-480 and the
price cards at y 1150. Overlay y positions below are 9:16 design values shifted for the crop.
"""
import os
import runpy

_base = runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "ipoh_hari1.py"))
for _k, _v in _base.items():
    if _k.isupper():
        globals()[_k] = _v

H = 1350            # canvas height at 1080 wide (4:5)
CROP_Y = 150        # footage crop window: y 150..1500 of the 1080x1920 frame
POPUP_CENTER_Y = 1150
LABEL_CY = 62
RAYS_CY = 340
SCRIM_H = 700
OVERLAY_H = 1350
END_CARD_DY = -260  # centre the end card on the shorter canvas

# text pops: chips just under the label, big slams above the presenter's head (~y 510)
_HOOK_CY = {"KAMPUNG TAWAS": 245, "IPOH": 405}
HOOK = []
for _h in _base["HOOK"]:
    _h = dict(_h)
    if _h["kind"] == "chip":
        _h["cy"] = 145
    elif _h["text"] in _HOOK_CY:
        _h["cy"] = _HOOK_CY[_h["text"]]
    else:
        _h["cy"] = 270            # single-line slams / pills / logo sting
    if _h["text"] == "IPOH":
        _h["size"] = 200
    HOOK.append(_h)

# banners: tops at y 120 (9:16: 160), the longest is 290 px high -> bottom 410
INTRO = []
for _b in _base["INTRO"]:
    _b = dict(_b)
    _b["y"] = 120
    INTRO.append(_b)

# effects: bursts follow the text; price-card bursts follow the cards
EVENTS = []
for _e in _base["EVENTS"]:
    _e = dict(_e)
    if "burst" in _e:
        _cx, _cy, _n = _e["burst"]
        _cy = 1150 if _cy > 1000 else (405 if _cy > 560 else max(110, _cy - 160))
        _e["burst"] = (_cx, _cy, _n)
    EVENTS.append(_e)

PREVIEW_T = dict(_base["PREVIEW_T"])
