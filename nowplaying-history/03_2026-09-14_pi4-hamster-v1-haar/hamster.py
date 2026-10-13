#!/usr/bin/env python3
"""
Hamster face filter. Funzis time!

This script finds faces, works out where the eyes are, and lays a hamster over each one
that's scaled so the hamster's eye separation matches the person's.

I decided not to have any transparency or rotation in the hamster photos just cause
I thought that'd make it look more like a sticker.
"""
import json
import random
from pathlib import Path

import cv2
import numpy as np

# Measured on real group photos with haarcascade_frontalface_default:
# eye separation is 0.350 of the detection box width (sd 0.035) and the eye
# line sits 0.399 of the way down it (sd 0.011). Guessing 0.45 for the
# separation, as seemed reasonable, made every sticker too big :(.
EYE_SEP_OF_W = 0.350
EYE_Y_OF_H = 0.399

# Expression thresholds were read off my own face with exprtest2.py rather than guessed.
# I looked kinda stupid doing it cause I was just opening and closing my mouth and smiling
# randomly but it lowk worked pretty well :D:
#            neutral          smile           mouth open
#   lift     -0.047 +/-.034   +0.060 +/-.031  +0.099 +/-.014
#   open      0.026 +/-.048    0.038 +/-.023   0.343 +/-.092
# Hysteresis: it takes a clear signal to switch on, and a clear one to drop
# back, so a face sitting near a boundary doesn't flap between hamsters.
OPEN_ON, OPEN_OFF = 0.18, 0.11
SMILE_ON, SMILE_OFF = 0.020, -0.005
# EAR (eye aspect ratio) is deliberately unused. Measured on a real face,
# eyes CLOSED scored higher than neutral (0.230 vs 0.210): the LBF model
# places eye points from a learned prior instead of tracking eyelids, so it
# cannot see a blink. Don't add a blink state on top of this landmark model.


def find_cascade(name="haarcascade_frontalface_default.xml"):
    """pip's opencv exposes cv2.data; Debian's python3-opencv does not, and
    puts the cascades under /usr/share instead."""
    places = []
    try:
        places.append(Path(cv2.data.haarcascades) / name)
    except AttributeError:
        pass
    places += [Path("/usr/share/opencv4/haarcascades") / name,
               Path("/usr/share/opencv/haarcascades") / name,
               Path(cv2.__file__).parent / "data" / name]
    for q in places:
        if q.is_file():
            return str(q)
    raise RuntimeError(
        "couldn't find " + name + ". Looked in: "
        + ", ".join(str(q.parent) for q in places)
        + "\nOn Raspberry Pi OS:  sudo apt install -y opencv-data")


class HamsterFilter:
    def __init__(self, sticker_dir, cover_w=3.0, cover_h=3.3,
                 detect_every=2, ease=0.5, max_side=320,
                 min_face=0.10, min_neighbors=7, max_miss=2,
                 confirm=2, match_radius=1.1, merge_dist=0.7,
                 expr_model=None, expr_every=3, expr_smooth=0.45):
        """cover_w/h: how much of the sticker to take, in multiples of its own
        eye separation.

        detect_every : run the detector every few (N) frame
        ease         : how fast the overlay glides to the detected position,
                       applied EVERY frame so motion stays smooth between
                       detections rather than jumping on detection frames
        max_miss     : drop a face after this many missed DETECTIONS (not
                       frames). Too high and departed faces hang around.
        confirm      : a face must be seen this many times before it gets a
                       hamster, which throws away single-frame false positives
        match_radius : how far a face may move between detections and still be
                       recognised as the same one. Too small and a fast head
                       turn spawns a second hamster beside the first.
        """
        self.dir = Path(sticker_dir)
        self.cover_w, self.cover_h = cover_w, cover_h
        self.detect_every, self.ease = detect_every, ease
        self.max_side = max_side          # detect on a downscaled copy
        self.min_face = min_face          # smallest face, as a fraction of width
        self.min_neighbors = min_neighbors
        self.max_miss, self.confirm = max_miss, confirm
        self.match_radius, self.merge_dist = match_radius, merge_dist
        self.expr_every, self.expr_smooth = expr_every, expr_smooth
        self.frame_no = 0
        self.tracks = []
        self._small = None          # the downscaled frame the detector used
        self._scale = 1.0

        self.cascade = cv2.CascadeClassifier(find_cascade())
        if self.cascade.empty():
            raise RuntimeError("face cascade failed to load")

        man = json.loads((self.dir / "stickers.json").read_text())
        self.stickers = []
        for s in man["stickers"]:
            img = cv2.imread(str(self.dir / s["file"]), cv2.IMREAD_COLOR)
            if img is None:
                continue
            lx, ly = s["eye_left"]
            rx, ry = s["eye_right"]
            self.stickers.append({
                "img": img, "name": s["file"],
                "expr": s.get("expr", "neutral"),
                "mid": ((lx + rx) / 2.0, (ly + ry) / 2.0),
                "sep": max(abs(rx - lx), 1.0),
            })
        if not self.stickers:
            raise RuntimeError(f"no sticker images found in {self.dir}")
        self.by_expr = {}
        for i, st in enumerate(self.stickers):
            self.by_expr.setdefault(st["expr"], []).append(i)

        # Landmarks are optional: without the model the filter still runs, it
        # just keeps one hamster per face instead of reacting.
        self.facemark = None
        if expr_model:
            model = Path(expr_model)
            if model.is_file() and hasattr(cv2, "face"):
                try:
                    fm = cv2.face.createFacemarkLBF()
                    fm.loadModel(str(model))
                    self.facemark = fm
                except Exception as e:
                    print(f"hamster: landmarks unavailable ({e})")

    # ---------------------------------------------------------------- faces
    def _detect(self, bgr):
        h, w = bgr.shape[:2]
        scale = min(1.0, self.max_side / max(h, w))
        small = cv2.resize(bgr, (int(w * scale), int(h * scale))) if scale < 1 else bgr
        self._small, self._scale = small, scale
        # No equalizeHist here. It seems like the obvious thing to do, but
        # measured across real photos it LOST faces (5 found vs 7 raw): a large
        # flat background dominates the histogram and crushes the face's own
        # contrast. Haar's own normalisation is enough :D.
        grey = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        found = self.cascade.detectMultiScale(
            grey, scaleFactor=1.15, minNeighbors=self.min_neighbors,
            minSize=(int(small.shape[1] * self.min_face),
                     int(small.shape[1] * self.min_face)))
        return [(x / scale, y / scale, bw / scale, bh / scale)
                for (x, y, bw, bh) in found]

    def _track(self, boxes):
        """Match detections to existing faces one-to-one, so a face that moved
        updates its own track instead of spawning a second one."""
        unmatched = list(self.tracks)
        for (x, y, bw, bh) in boxes:
            cx, cy = x + bw / 2, y + bh / 2
            best, best_d = None, 1e9
            for t in unmatched:
                d = ((t["tcx"] - cx) ** 2 + (t["tcy"] - cy) ** 2) ** 0.5
                if d < best_d and d < max(bw, t["tw"]) * self.match_radius:
                    best, best_d = t, d
            if best is None:
                self.tracks.append({
                    "cx": cx, "cy": cy, "w": bw, "h": bh,       # drawn
                    "tcx": cx, "tcy": cy, "tw": bw, "th": bh,   # detected
                    "sticker": self._free_sticker("neutral"),
                    "expr": "neutral", "lift": None, "open": None,
                    "seed": random.random(), "miss": 0, "seen": 1})
            else:
                unmatched.remove(best)      # one detection claims one track
                best["tcx"], best["tcy"] = cx, cy
                best["tw"], best["th"] = bw, bh
                best["miss"] = 0
                best["seen"] += 1

        for t in unmatched:
            t["miss"] += 1
        self.tracks = [t for t in self.tracks if t["miss"] <= self.max_miss]
        self._merge()

    def _merge(self):
        """Two tracks on one face can still happen when the detector wobbles.
        Keep the better-established one."""
        keep = []
        for t in sorted(self.tracks, key=lambda t: (-t["seen"], t["miss"])):
            dup = False
            for k in keep:
                d = ((k["tcx"] - t["tcx"]) ** 2 + (k["tcy"] - t["tcy"]) ** 2) ** 0.5
                if d < max(k["tw"], t["tw"]) * self.merge_dist:
                    dup = True
                    break
            if not dup:
                keep.append(t)
        self.tracks = keep

    def _free_sticker(self, expr="neutral", seed=None):
        """This function makes it so that a hamster from the right mood that nobody else is wearing is more likely to appear (no same outfit shenanigans :D)"""
        pool = self.by_expr.get(expr) or list(range(len(self.stickers)))
        taken = {t["sticker"] for t in self.tracks}
        free = [i for i in pool if i not in taken] or pool
        if seed is None:
            return random.choice(free)
        return free[int(seed * 9973) % len(free)]   # stable for this face

    # ----------------------------------------------------------- expression
    @staticmethod
    def _metrics(pts):
        def d(a, b):
            return float(np.linalg.norm(pts[a] - pts[b]))
        eye = float(np.linalg.norm(pts[42:48].mean(0) - pts[36:42].mean(0)))
        if eye < 1:
            return None
        mouth_w = max(d(48, 54), 1.0)
        lipline = (pts[51][1] + pts[57][1]) / 2
        return ((lipline - (pts[48][1] + pts[54][1]) / 2) / eye,   # lift
                d(62, 66) / mouth_w)                               # open

    def _read_expressions(self):
        """Fit 68 landmarks on the frame the detector already downscaled --
        the metrics are ratios, so the smaller image costs nothing but time."""
        live = [t for t in self.tracks if t["seen"] >= self.confirm]
        if not live or self.facemark is None or self._small is None:
            return
        sc = self._scale
        boxes = np.array(
            [[int((t["cx"] - t["w"]/2) * sc), int((t["cy"] - t["h"]/2) * sc),
              int(t["w"] * sc), int(t["h"] * sc)] for t in live],
            dtype=np.int32)
        h, w = self._small.shape[:2]
        boxes[:, 0] = np.clip(boxes[:, 0], 0, w - 2)
        boxes[:, 1] = np.clip(boxes[:, 1], 0, h - 2)
        boxes[:, 2] = np.clip(boxes[:, 2], 8, w - boxes[:, 0])
        boxes[:, 3] = np.clip(boxes[:, 3], 8, h - boxes[:, 1])
        try:
            ok, marks = self.facemark.fit(self._small, boxes)
        except Exception:
            return
        if not ok:
            return
        for t, m in zip(live, marks):
            got = self._metrics(np.squeeze(np.asarray(m)))
            if got is None:
                continue
            lift, opn = got
            k = self.expr_smooth
            t["lift"] = lift if t["lift"] is None else t["lift"]*k + lift*(1-k)
            t["open"] = opn if t["open"] is None else t["open"]*k + opn*(1-k)

            was = t["expr"]
            if t["open"] > (OPEN_OFF if was == "open" else OPEN_ON):
                now = "open"                       # mouth wins over smile:
            elif t["lift"] > (SMILE_OFF if was == "happy" else SMILE_ON):
                now = "happy"                      # opening wide lifts the
            else:                                  # corners too
                now = "neutral"
            if now != was:
                t["expr"] = now
                t["sticker"] = self._free_sticker(now, t["seed"])


    def _paste(self, frame, track):
        st = self.stickers[track["sticker"] % len(self.stickers)]
        fh, fw = frame.shape[:2]

        # where the person's eyes are
        want_sep = track["w"] * EYE_SEP_OF_W
        eye_x = track["cx"]
        eye_y = track["cy"] - track["h"] / 2 + track["h"] * EYE_Y_OF_H

        # crop a window around the hamster's eyes, in its own eye-sep units
        k = want_sep / st["sep"]                     # source px -> frame px
        mx, my = st["mid"]
        half_w = st["sep"] * self.cover_w / 2
        half_h = st["sep"] * self.cover_h / 2
        sx0, sx1 = mx - half_w, mx + half_w
        sy0, sy1 = my - half_h, my + half_h

        # target rectangle in the frame
        tx0 = eye_x - (mx - sx0) * k
        ty0 = eye_y - (my - sy0) * k
        tw = int(round((sx1 - sx0) * k))
        th = int(round((sy1 - sy0) * k))
        if tw < 8 or th < 8:
            return

        # take the crop, padding with edge pixels if it runs off the sticker
        sh, sw = st["img"].shape[:2]
        ix0, iy0 = int(np.floor(sx0)), int(np.floor(sy0))
        ix1, iy1 = int(np.ceil(sx1)), int(np.ceil(sy1))
        pad_l, pad_t = max(0, -ix0), max(0, -iy0)
        pad_r, pad_b = max(0, ix1 - sw), max(0, iy1 - sh)
        crop = st["img"][max(0, iy0):min(sh, iy1), max(0, ix0):min(sw, ix1)]
        if crop.size == 0:
            return
        if pad_l or pad_t or pad_r or pad_b:
            crop = cv2.copyMakeBorder(crop, pad_t, pad_b, pad_l, pad_r,
                                      cv2.BORDER_REPLICATE)
        patch = cv2.resize(crop, (tw, th), interpolation=cv2.INTER_AREA
                           if k < 1 else cv2.INTER_LINEAR)

        # clip to the frame and copy
        px0, py0 = int(round(tx0)), int(round(ty0))
        cx0, cy0 = max(0, px0), max(0, py0)
        cx1, cy1 = min(fw, px0 + tw), min(fh, py0 + th)
        if cx1 <= cx0 or cy1 <= cy0:
            return
        frame[cy0:cy1, cx0:cx1] = patch[cy0 - py0:cy1 - py0, cx0 - px0:cx1 - px0]

    # ----------------------------------------------------------------- main
    def apply(self, frame):
        """BGR in, BGR out (modified in place). Detection runs every Nth
        frame; the tracks carry the overlay in between."""
        if self.frame_no % self.detect_every == 0:
            self._track(self._detect(frame))
        if self.facemark is not None and self.frame_no % self.expr_every == 0:
            self._read_expressions()
        self.frame_no += 1

        # glide toward the detected position every frame, not just on the
        # frames the detector ran -- this is what makes it feel responsive
        e = self.ease
        for t in self.tracks:
            for now, want in (("cx", "tcx"), ("cy", "tcy"),
                              ("w", "tw"), ("h", "th")):
                t[now] += (t[want] - t[now]) * e

        # nearer faces (bigger boxes) paste last, so they sit in front
        for t in sorted(self.tracks, key=lambda t: t["w"]):
            if t["seen"] >= self.confirm:      # ignore one-frame phantoms
                self._paste(frame, t)
        return frame

    def reshuffle(self):
        for t in self.tracks:
            t["seed"] = random.random()
            t["sticker"] = self._free_sticker(t["expr"], t["seed"])
