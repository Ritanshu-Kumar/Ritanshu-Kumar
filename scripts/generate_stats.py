#!/usr/bin/env python3
"""Generate GitHub profile analytics as PNG files.

Outputs:
  assets/stats.png - analytics cards + weekly activity
  assets/year.png  - one-year contribution heatmap

Uses GitHub GraphQL and Pillow. The workflow supplies GITHUB_TOKEN.
"""
import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
LOGIN = os.environ.get("GH_LOGIN", "Ritanshu-Kumar")
TOKEN = os.environ.get("GITHUB_TOKEN")

if not TOKEN:
    raise SystemExit("GITHUB_TOKEN is required")

ASSETS.mkdir(parents=True, exist_ok=True)

today = datetime.now(timezone.utc).date()
start = today - timedelta(days=364)

QUERY = """
query($login:String!, $from:DateTime!, $to:DateTime!) {
  user(login:$login) {
    contributionsCollection(from:$from, to:$to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": QUERY,
    "variables": {
        "login": LOGIN,
        "from": f"{start}T00:00:00Z",
        "to": f"{today}T23:59:59Z",
    },
}).encode()

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "ritanshu-github-profile",
    },
    method="POST",
)

with urllib.request.urlopen(request, timeout=30) as response:
    result = json.load(response)

if result.get("errors"):
    raise RuntimeError(result["errors"])

calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
days = {
    item["date"]: item["contributionCount"]
    for week in calendar["weeks"]
    for item in week["contributionDays"]
}

# Current streak.
cursor = today if days.get(str(today), 0) else today - timedelta(days=1)
current = 0
while days.get(str(cursor), 0) > 0:
    current += 1
    cursor -= timedelta(days=1)

# Longest streak.
longest = 0
run = 0
for key in sorted(days):
    if days[key] > 0:
        run += 1
        longest = max(longest, run)
    else:
        run = 0

# Weekly totals.
weekly = []
for i in range(16):
    end = today - timedelta(days=(15 - i) * 7)
    weekly.append(
        sum(days.get(str(end - timedelta(days=j)), 0) for j in range(7))
    )

BG = "#0d0d12"
PANEL = "#15151d"
TEXT = "#f5f5f7"
MUTED = "#9a9aa5"
GRID = "#292933"
PINK = "#a78bfa"
CYAN = "#55d6d2"
PURPLE = "#7c5cff"
PINK_LIGHT = "#c4b5fd"
PINK_DARK = "#4c2d8f"

def font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

# ---------- analytics PNG ----------
W, H = 1200, 500
img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

cards = [
    (30, "TOTAL CONTRIBUTIONS", calendar["totalContributions"], PINK),
    (425, "CURRENT STREAK", current, CYAN),
    (820, "LONGEST STREAK", longest, PURPLE),
]

for x, label, value, accent in cards:
    draw.rounded_rectangle((x, 30, x + 350, 200), radius=20,
                           fill=PANEL, outline=GRID, width=1)
    draw.ellipse((x + 307, 57, x + 323, 73), fill=accent)
    draw.text((x + 28, 58), label, font=font(15, True), fill=MUTED)
    draw.text((x + 28, 105), str(value), font=font(58, True), fill=TEXT)

# Current streak ring.
cx, cy, radius = 720, 135, 40
bbox = (cx-radius, cy-radius, cx+radius, cy+radius)
draw.ellipse(bbox, outline=GRID, width=7)

if longest:
    extent = int(360 * min(1, current / longest))
    draw.arc(
        bbox,
        start=-90,
        end=-90 + extent,
        fill=PINK,
        width=7,
    )

# Weekly activity.
sx, sy, sw, sh = 55, 275, 1090, 150
draw.text((55, 235), "weekly activity", font=font(18, True), fill=TEXT)
for frac in (0, 0.5, 1):
    y = sy + sh - frac * (sh - 20)
    draw.line((55, y, 1145, y), fill=GRID, width=1)

maximum = max(1, max(weekly))
points = []
for i, value in enumerate(weekly):
    x = sx + i * sw / (len(weekly) - 1)
    y = sy + sh - (value / maximum) * (sh - 20)
    points.append((int(x), int(y)))

if len(points) > 1:
    draw.line(points, fill=PINK, width=4, joint="curve")
for x, y in points:
    draw.ellipse((x-4, y-4, x+4, y+4), fill=PINK)

draw.text(
    (55, 462),
    "last 16 weeks · generated from GitHub",
    font=font(13),
    fill=MUTED,
)

img.save(ASSETS / "stats.png", "PNG", optimize=True)

# ---------- one-year contribution PNG ----------
W, H = 1200, 310
img = Image.new("RGB", (W, H), BG)
draw = ImageDraw.Draw(img)

draw.rounded_rectangle((0, 0, W, H), radius=26, fill=BG)
draw.text((35, 18), "contribution graph", font=font(18, True), fill=TEXT)

CELL, GAP = 17, 4
GX, GY = 35, 60
maximum = max(1, max(days.values()))

def heat_color(value):
    if value <= 0:
        return "#1b1b23"
    ratio = value / maximum
    if ratio < 0.20:
        return "#4b2540"
    if ratio < 0.40:
        return PINK_DARK
    if ratio < 0.70:
        return PINK_LIGHT
    return PINK

grid_start = start - timedelta(days=(start.weekday() + 1) % 7)
for col in range(53):
    for row in range(7):
        day = grid_start + timedelta(days=col * 7 + row)
        if start <= day <= today:
            x = GX + col * (CELL + GAP)
            y = GY + row * (CELL + GAP)
            draw.rounded_rectangle(
                (x, y, x + CELL, y + CELL),
                radius=4,
                fill=heat_color(days.get(str(day), 0)),
            )

draw.text((35, 272), "less", font=font(13), fill=MUTED)
legend = ["#1b1b23", "#4b2540", PINK_DARK, PINK_LIGHT, PINK]
for i, color in enumerate(legend):
    x = 70 + i * 23
    draw.rounded_rectangle((x, 270, x + 18, 288), radius=4, fill=color)
draw.text((188, 272), "more", font=font(13), fill=MUTED)

total = calendar["totalContributions"]
text = f"{total} contributions"
tw = draw.textbbox((0, 0), text, font=font(13))[2]
draw.text((1165 - tw, 272), text, font=font(13), fill=MUTED)

img.save(ASSETS / "year.png", "PNG", optimize=True)

print(f"Generated stats.png and year.png for {LOGIN}")
print(f"Total contributions: {calendar['totalContributions']}")
print(f"Current streak: {current}")
print(f"Longest streak: {longest}")
