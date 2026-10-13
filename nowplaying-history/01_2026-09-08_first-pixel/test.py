# First-pixel test, copied verbatim from the "First Boot to First Pixel"
# https://learn.adafruit.com/adafruit-2-8-color-tft-touch-shield-v2/first-boot-to-first-pixel
# This was just to check if my cheap display from Aliexpress was working, and basically just put rectangles on the display to see the color

import time
from PIL import Image, ImageDraw
from st7789 import ST7789

disp = ST7789(
    port=0, cs=0,        # chip select on pin 24
    dc=25,                # pin 22
    rst=27,               # pin 13
    backlight=18,         # pin 12
    width=320, height=240,
    rotation=0,
    invert=True,
    spi_speed_hz=32000000,
)

disp.reset()     # the library leaves RST low — this releases it
disp._init()     # re-run init now the controller is actually awake

img = Image.new("RGB", (320, 240), (0, 0, 0))
d = ImageDraw.Draw(img)
d.rectangle((0, 0, 106, 240), fill=(220, 50, 50))
d.rectangle((107, 0, 213, 240), fill=(50, 200, 120))
d.rectangle((214, 0, 320, 240), fill=(60, 110, 230))
d.text((120, 115), "IT WORKS", fill=(255, 255, 255))

disp.display(img)
print("frame sent — look at the screen")
time.sleep(60)
