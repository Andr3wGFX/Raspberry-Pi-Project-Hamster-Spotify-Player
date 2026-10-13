#!/usr/bin/env python3
"""
Expression calibration, take two -- OpenCV 68-point landmarks.

    python3 ~/np/exprtest2.py

Can't use MediaPipe since its aarch64 build assumes ARMv8 crypto instructions the
Pi 4's Cortex-A72 doesn't have, so it dies with SIGILL. This uses OpenCV's
facemark LBF instead -- pure CPU, no special instructions, and it came in
with opencv-contrib already.

Four five-second phases, then a table of what my face scores, so the
thresholds are read from my silly faces rather than from an assumption.
"""
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np

HOME = Path.home() / "np"
MODEL = HOME / "lbfmodel.yaml"
MODEL_URL = ("https://raw.githubusercontent.com/kurnianggoro/GSOC2017/"
             "master/data/lbfmodel.yaml")

print("machine :", subprocess.run(["uname", "-m"], capture_output=True,
                                  text=True).stdout.strip())
try:
    import cv2
except ImportError:
    sys.exit("no cv2")
print("cv2     :", cv2.__version__, "|", cv2.__file__.split("/")[-4])

if not hasattr(cv2, "face") or not hasattr(cv2.face, "createFacemarkLBF"):
    sys.exit("this cv2 has no facemark. With the venv active:\n"
             "    pip install opencv-contrib-python")

if not MODEL.exists():
    print(f"downloading the landmark model (~56 MB) to {MODEL} ...")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL)
    except Exception as e:
        sys.exit(f"download failed: {e}")
print(f"model   : {MODEL.stat().st_size // (1024*1024)} MB")

sys.path.insert(0, str(HOME))
from hamster import HamsterFilter, find_cascade      # noqa: E402

hf = HamsterFilter(HOME / "stickers")
fm = cv2.face.createFacemarkLBF()
fm.loadModel(str(MODEL))


def metrics(pts):
    d = lambda a, b: float(np.linalg.norm(pts[a] - pts[b]))      # noqa: E731
    eye = float(np.linalg.norm(pts[42:48].mean(0) - pts[36:42].mean(0)))
    if eye < 1:
        return None
    mouth_w = d(48, 54)
    lipline = (pts[51][1] + pts[57][1]) / 2
    return {
        # mouth corners lifted above the lip midline -> smiling
        "lift": float(lipline - (pts[48][1] + pts[54][1]) / 2) / eye,
        # inner lip gap over mouth width -> mouth open
        "open": d(62, 66) / max(mouth_w, 1),
        # mouth width over eye separation -> grin stretch
        "width": mouth_w / eye,
        # eye aspect ratio, the standard blink measure -> eyes shut
        "ear": ((d(37, 41) + d(38, 40)) / (2 * d(36, 39))
                + (d(43, 47) + d(44, 46)) / (2 * d(42, 45))) / 2,
    }


cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
if not cap.isOpened():
    sys.exit("camera didn't open -- is nowplaying still running? "
             "sudo systemctl stop nowplaying")
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

KEYS = ["lift", "open", "width", "ear"]
PHASES = [("NEUTRAL - relaxed, look at the camera", 5),
          ("SMILE   - grin at it", 5),
          ("MOUTH   - open wide, surprised", 5),
          ("EYES    - close your eyes", 5)]

print("\nFour phases, five seconds each. Keep your face in shot.\n")
results, frames, t_start = {}, 0, time.monotonic()

for label, secs in PHASES:
    for n in (3, 2, 1):
        print(f"\r  next: {label}   in {n}...", end="", flush=True)
        time.sleep(1)
    print(f"\r  >>> {label}" + " " * 26)
    vals, hits = {k: [] for k in KEYS}, 0
    t0 = time.monotonic()
    while time.monotonic() - t0 < secs:
        ok, frame = cap.read()
        if not ok:
            continue
        frames += 1
        boxes = [tuple(int(v) for v in b) for b in hf._detect(frame)]
        if not boxes:
            continue
        ok2, marks = fm.fit(frame, np.array(boxes, dtype=np.int32))
        if not ok2 or not len(marks):
            continue
        m = metrics(np.squeeze(np.asarray(marks[0])))
        if m:
            hits += 1
            for k in KEYS:
                vals[k].append(m[k])
    results[label.split()[0]] = (vals, hits)
    print(f"      {hits} frames with landmarks")

cap.release()
print(f"\nspeed: {frames / (time.monotonic() - t_start):.1f} fps end to end "
      "(detect + landmarks on every frame, 640x480)")

print("\n" + "=" * 72)
print("  paste this whole block back to Claude")
print("=" * 72)
print(f"{'metric':<8}" + "".join(f"{p:>16}" for p in results))
for k in KEYS:
    row = f"{k:<8}"
    for p in results:
        v = results[p][0][k]
        row += (f"{np.median(v):>10.3f}±{np.std(v):<5.3f}" if v else f"{'-':>16}")
    print(row)
print("-" * 72)
print("frames with landmarks: " +
      "  ".join(f"{p}={results[p][1]}" for p in results))
print("(median ± standard deviation)")
