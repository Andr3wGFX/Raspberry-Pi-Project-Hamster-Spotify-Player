#!/usr/bin/env python3
"""
Why did an open mouth read as a smile? :D -> :) -> me :(

    source ~/np/bin/activate
    python ~/np/jawcheck.py

exprtest.py measured jawOpen = 0.326 at the full 640x480 frame. The filter
runs detection on a downscaled copy. This prints the RAW blendshape scores at
each size so we can see what the downscale actually costs, instead of assuming.

Open and close your mouth repeatedly for six seconds per size. Exaggerate.
"""
import os
import sys
import time
from pathlib import Path

# MediaPipe's C++ logging is deafening and drowns the numbers.
os.environ.setdefault("GLOG_minloglevel", "2")
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")

HOME = Path.home() / "np"
MODEL = HOME / "face_landmarker.task"

import cv2                                            # noqa: E402
import numpy as np                                    # noqa: E402
import mediapipe as mp                                # noqa: E402
from mediapipe.tasks import python as mpp             # noqa: E402
from mediapipe.tasks.python import vision             # noqa: E402

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
for _ in range(5):
    cap.read()

WATCH = ["jawOpen", "mouthSmileLeft", "mouthSmileRight",
         "eyeBlinkLeft", "eyeBlinkRight"]
SIZES = [320, 480, 640]
rows = {}

print("\nOpen and close your mouth, wide, over and over. Three rounds.\n")
for side in SIZES:
    lm = vision.FaceLandmarker.create_from_options(
        vision.FaceLandmarkerOptions(
            base_options=mpp.BaseOptions(model_asset_path=str(MODEL)),
            running_mode=vision.RunningMode.VIDEO, num_faces=1,
            output_face_blendshapes=True))
    for n in (3, 2, 1):
        print(f"\r  next: detection at {side} px   in {n}...", end="", flush=True)
        time.sleep(1)
    print(f"\r  >>> OPEN AND CLOSE, detection at {side} px" + " " * 20)
    got = {k: [] for k in WATCH}
    faces, frames, t0 = 0, 0, time.monotonic()
    while time.monotonic() - t0 < 6.0:
        ok, f = cap.read()
        if not ok:
            continue
        frames += 1
        h, w = f.shape[:2]
        sc = min(1.0, side / max(h, w))
        small = cv2.resize(f, (int(w * sc), int(h * sc))) if sc < 1 else f
        img = mp.Image(image_format=mp.ImageFormat.SRGB,
                       data=cv2.cvtColor(small, cv2.COLOR_BGR2RGB))
        r = lm.detect_for_video(img, int((time.monotonic() - t0) * 1000))
        if not r.face_blendshapes:
            continue
        faces += 1
        c = {b.category_name: b.score for b in r.face_blendshapes[0]}
        for k in WATCH:
            got[k].append(c.get(k, 0.0))
    lm.close()
    rows[side] = (got, faces, frames)
    print(f"      {faces}/{frames} frames with a face")

print("\n" + "=" * 72)
print("  RAW blendshape scores by detection size -- copy this back")
print("=" * 72)
print(f"  {'blendshape':<18}" + "".join(f"{s:>6}px min  max  p90" for s in SIZES))
for k in WATCH:
    line = f"  {k:<18}"
    for s in SIZES:
        v = np.array(rows[s][0][k]) if rows[s][0][k] else np.array([0.0])
        line += f"{v.min():>10.3f}{v.max():>5.2f}{np.percentile(v, 90):>5.2f}"
    print(line)

print("\n  how often jawOpen cleared each candidate threshold:")
print(f"  {'threshold':<18}" + "".join(f"{s:>12}px" for s in SIZES))
for thr in (0.04, 0.08, 0.15, 0.25):
    line = f"  {thr:<18.2f}"
    for s in SIZES:
        v = np.array(rows[s][0]["jawOpen"]) if rows[s][0]["jawOpen"] else np.array([0.0])
        line += f"{(v > thr).mean() * 100:>13.0f}%"
    print(line)
print("\n  (you were open roughly half the time, so ~40-60% is the right answer)")
cap.release()
