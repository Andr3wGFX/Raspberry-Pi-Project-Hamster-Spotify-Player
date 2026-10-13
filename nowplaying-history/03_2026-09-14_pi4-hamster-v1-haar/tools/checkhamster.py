#!/usr/bin/env python3
"""
This script asks why isn't the hamster filter working?   python3 ~/np/checkhamster.py

This script Walks the chain and, if everything loads, runs the filter on a real photo so
you can see whether it detects and composites. This script doesn't touch GPIO, so it is safe
to run while the display is going. :D
"""
import sys
from pathlib import Path

HOME = Path.home() / "np"
sys.path.insert(0, str(HOME))
ok = True


def good(m):
    print(f"  [ ok ] {m}")


def bad(m, fix=""):
    global ok
    ok = False
    print(f"  [FAIL] {m}")
    if fix:
        print(f"         -> {fix}")


print("\n1. Is the running program the one with the filter in it?")
prog = Path.home() / "nowplaying.py"
if not prog.exists():
    bad(f"{prog} not found")
else:
    src = prog.read_text()
    if "FILTER_ENABLED" in src and "get_filter" in src:
        good(f"nowplaying.py has the filter ({len(src.splitlines())} lines)")
    else:
        bad("nowplaying.py is an OLDER version with no filter",
            "re-copy it. Windows saves repeats as 'nowplaying (3).py' -- "
            "check `dir nowplaying*.py` and take the NEWEST")

print("\n2. hamster.py")
here = [p for p in (Path.home() / "hamster.py", HOME / "hamster.py") if p.exists()]
if not here:
    bad("hamster.py is in neither ~/ nor ~/np/",
        "scp hamster.py andrew@nowplaying.local:~/np/hamster.py")
else:
    good(f"found at {here[0]}")

print("\n3. opencv and the face cascade")
try:
    import cv2
    good(f"cv2 {cv2.__version__}")
except ImportError:
    bad("no cv2", "sudo apt install -y python3-opencv")
    cv2 = None

if cv2:
    try:
        from hamster import find_cascade
        path = find_cascade()
        good(f"cascade at {path}")
        if cv2.CascadeClassifier(path).empty():
            bad("cascade file exists but won't load")
    except ImportError as e:
        bad(f"can't import hamster.py: {e}")
    except Exception as e:
        bad(str(e), "sudo apt install -y opencv-data")

print("\n4. Stickers")
sd = HOME / "stickers"
imgs = sorted(p for p in sd.glob("*") if p.suffix.lower() in
              {".jpg", ".jpeg", ".png", ".webp"}) if sd.is_dir() else []
if not sd.is_dir():
    bad(f"{sd} does not exist",
        "cd ~/np && unzip -o stickers.zip")
elif not (sd / "stickers.json").exists():
    bad("stickers/stickers.json missing", "cd ~/np && unzip -o stickers.zip")
elif len(imgs) < 5:
    bad(f"only {len(imgs)} sticker image(s) found")
else:
    good(f"{len(imgs)} sticker images + manifest")

if not ok:
    print("\nFix the failures above, then re-run.\n")
    sys.exit(1)

print("\n5. Building the filter")
try:
    from hamster import HamsterFilter
    hf = HamsterFilter(sd)
    good(f"loaded {len(hf.stickers)} stickers")
except Exception as e:
    bad(f"{type(e).__name__}: {e}")
    sys.exit(1)

print("\n6. Does it detect and composite?")
shots = sorted((HOME / "captures").glob("*.jpg"))
photos = sorted((HOME / "photos").glob("*.png"))
test = shots[-1] if shots else (photos[0] if photos else None)
if test is None:
    print("  no photo to try it on -- take one in camera mode first")
else:
    img = cv2.imread(str(test))
    if img is None:
        bad(f"couldn't read {test.name}")
    else:
        boxes = hf._detect(img)
        print(f"  using {test.name} ({img.shape[1]}x{img.shape[0]})")
        if not boxes:
            print("  [ ?? ] no faces found in THIS photo. That may just mean")
            print("         the photo has no front-facing face in it -- the")
            print("         detector only finds faces looking at the camera.")
        else:
            good(f"{len(boxes)} face(s) detected")
        out = hf.apply(img)
        dest = HOME / "hamster-test.jpg"
        cv2.imwrite(str(dest), out)
        good(f"wrote {dest} -- copy it to your laptop and look at it:")
        print(f"         scp andrew@nowplaying.local:{dest} .")

print("\nAll good. If the filter still does nothing on the panel, make sure")
print("you pressed PREV *while in camera mode* (hold middle 3 s to enter).")
