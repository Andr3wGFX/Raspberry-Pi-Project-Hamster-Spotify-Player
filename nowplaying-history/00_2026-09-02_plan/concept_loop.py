#This was for inspiration (copied from a reel I saw that used a Raspberry Pi Zero for a spotify deck that ran on a cheap display)
#I never actually ran this on my own device but the API system they had was inspiration for my system
import time, io, requests
from PIL import Image, ImageDraw, ImageFont
from displayhatmini import DisplayHATMini
import spotipy
from spotipy.oauth2 import SpotifyOAuth

W, H = 320, 240
buf = Image.new("RGB", (W, H))
hat = DisplayHATMini(buf)
hat.set_backlight(1.0)                # the step everyone forgets

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope="user-read-currently-playing user-read-playback-state"))

POLL = 3.0
last_poll, track_id, art = 0.0, None, None
progress = duration = 0
playing = False
title = artist = ""

while True:
    now = time.monotonic()

    # --- network: slow, every POLL seconds ---
    if now - last_poll >= POLL:
        last_poll = now
        cur = sp.current_playback()
        if cur and cur.get("item"):
            item     = cur["item"]
            playing  = cur["is_playing"]
            progress = cur["progress_ms"] / 1000
            duration = item["duration_ms"] / 1000
            title    = item["name"]
            artist   = ", ".join(a["name"] for a in item["artists"])
            if item["id"] != track_id:          # cache art per TRACK, not per URL
                track_id = item["id"]
                url = item["album"]["images"][-1]["url"]
                raw = requests.get(url, timeout=5).content
                art = Image.open(io.BytesIO(raw)).convert("RGB") \
                           .resize((120, 120), Image.LANCZOS)
        else:
            playing, track_id, art = False, None, None

    # --- local: fake the clock forward between polls ---
    elif playing:
        progress = min(progress + 0.2, duration)

    draw_frame(buf, art, title, artist, progress, duration, playing)
    hat.display()
    time.sleep(0.2)
