#!/usr/bin/env python3
"""This script checks the weather feed from the Pi.  python3 ~/np/weathertest.py"""
import requests, sys
LAT, LON, UNIT, TZ = 32.2217, -110.9265  # Tucson, Arizona", "fahrenheit", "America/Phoenix" (Please don't dox me)
try:
    r = requests.get("https://api.open-meteo.com/v1/forecast", timeout=10, params={
        "latitude": LAT, "longitude": LON,
        "current": "temperature_2m,weather_code",
        "temperature_unit": UNIT, "timezone": TZ})
    r.raise_for_status()
    c = r.json()["current"]
    print(f"OK  {round(c['temperature_2m'])}°  code={c['weather_code']}  at {c['time']}")
except Exception as e:
    print("FAILED:", type(e).__name__, e); sys.exit(1)
