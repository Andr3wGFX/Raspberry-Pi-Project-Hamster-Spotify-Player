#!/usr/bin/env python3
"""
This script tests if this Pi read facial expressions, and where my thresholds are?

    python3 ~/np/exprtest.py

OpenCV's smile cascade measured about a coin flip on real photos, so this
tries MediaPipe instead, which returns named "blendshape" (Blender reference??) scores (smile, jaw
open, blink, brows) rather than a yes/no guess.

It runs four five-second phases and prints what my own face actually scores
in each, so the thresholds come from me rather than from an assumption.
"""
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HOME = Path.home() / "np"
MODEL = HOME / "face_landmarker.task"
MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/face_landmarker/"
             "face_landmarker/float16/1/face_landmarker.task")

print("machine :", subprocess.run(["uname", "-m"], capture_output=True,
                                  text=True).stdout.strip())
print("python  :", sys.version.split()[0])

try:
    import cv2
except ImportError:
    sys.exit("no cv2 -- sudo apt install -y python3-opencv")

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mpp
    from mediapipe.tasks.python import vision
    print("mediapipe:", mp.__version__)
except ImportError:
    sys.exit("mediapipe not installed. With the venv active:\n"
             "    pip install mediapipe\n"
             "If pip refuses (no wheel for this python/arch), tell Claude what\n"
             "it printed -- that's the answer we're testing for.")

if not MODEL.exists():
    print(f"downloading the face model (~3 MB) to {MODEL} ...")
    try:
        urllib.request.urlretrieve(MODEL_URL, MODEL)
    except Exception as e:
        sys.exit(f"download failed: {e}")
print(f"model   : {MODEL.stat().st_size // 1024} KB")

lm = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
    base_options=mpp.BaseOptions(model_asset_path=str(MODEL)),
    running_mode=vision.RunningMode.IMAGE,
    num_faces=2, output_face_blendshapes=True))

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
if not cap.isOpened():
    sys.exit("camera didn't open")
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

WATCH = ["mouthSmileLeft", "mouthSmileRight", "jawOpen",
         "eyeBlinkLeft", "eyeBlinkRight", "browInnerUp",
         "browDownLeft", "mouthPucker", "eyeSquintLeft"]

PHASES = [("NEUTRAL  - relaxed face, look at the camera", 5),
          ("SMILE    - grin at it", 5),
          ("MOUTH    - open wide, surprised", 5),
          ("EYES     - close your eyes", 5)]

print("\nFour phases, five seconds each. Stay in frame throughout.\n")
results = {}
frames = 0
t_start = time.monotonic()

for label, secs in PHASES:
    for n in (3, 2, 1):
        print(f"\r  next: {label}   starting in {n}...", end="", flush=True)
        time.sleep(1)
    print(f"\r  >>> {label}" + " " * 24)
    sums, count = {k: 0.0 for k in WATCH}, 0
    t0 = time.monotonic()
    while time.monotonic() - t0 < secs:
        ok, frame = cap.read()
        if not ok:
            continue
        frames += 1
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb))
        if not res.face_blendshapes:
            continue
        count += 1
        scores = {c.category_name: c.score for c in res.face_blendshapes[0]}
        for k in WATCH:
            sums[k] += scores.get(k, 0.0)
    results[label.split()[0]] = ({k: (sums[k] / count if count else 0.0)
                                  for k in WATCH}, count)
    print(f"      {count} frames with a face found")

cap.release()
elapsed = time.monotonic() - t_start
print(f"\nspeed: {frames / elapsed:.1f} fps end to end "
      f"(detection on every frame, 640x480)")

print("\n" + "=" * 68)
print("  blendshape averages -- copy this whole block back to Claude")
print("=" * 68)
head = f"{'blendshape':<20}" + "".join(f"{k:>11}" for k in results)
print(head)
for k in WATCH:
    row = f"{k:<20}" + "".join(f"{results[p][0][k]:>11.3f}" for p in results)
    print(row)
print("-" * 68)
print("faces found per phase: " +
      "  ".join(f"{p}={results[p][1]}" for p in results))
