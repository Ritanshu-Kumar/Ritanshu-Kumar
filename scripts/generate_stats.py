#!/usr/bin/env python3
"""Generate the profile analytics SVGs from GitHub GraphQL.

Outputs:
  assets/stats.svg  - three metric cards + weekly activity line chart
  assets/year.svg   - one-year contribution heatmap

Only the GitHub Actions GITHUB_TOKEN is required.
"""
import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
LOGIN = os.environ.get("GH_LOGIN", "Ritanshu-Kumar")
TOKEN = os.environ.get("GITHUB_TOKEN")

if not TOKEN:
    raise SystemExit("GITHUB_TOKEN is required")

now = datetime.now(timezone.utc)
today = now.date()
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
days = {}
for week in calendar["weeks"]:
    for item in week["contributionDays"]:
        days[item["date"]] = item["contributionCount"]

# Current streak. GitHub's current contribution day counts if it exists;
# otherwise start from yesterday.
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

# Weekly contribution totals for the line chart.
weekly = []
for i in range(16):
    end = today - timedelta(days=(15 - i) * 7)
    weekly.append(sum(days.get(str(end - timedelta(days=j)), 0) for j in range(7)))

PINK = "#a78bfa"        # primary accent (renamed variable, now purple/violet)
PINK_LIGHT = "#c4b5fd"
PINK_DARK = "#4c2d8f"
PURPLE = "#7c5cff"
CYAN = "#55d6d2"
BLUE = "#6aa8ff"
BG = "#0d0d12"
PANEL = "#15151d"
TEXT = "#f5f5f7"
MUTED = "#9a9aa5"
GRID = "#292933"

# ---------- analytics panel ----------
W, H = 1200, 500
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
svg.append(f'<rect width="{W}" height="{H}" rx="26" fill="{BG}"/>')

cards = [
    (30, "TOTAL CONTRIBUTIONS", calendar["totalContributions"], PINK),
    (425, "CURRENT STREAK", current, CYAN),
    (820, "LONGEST STREAK", longest, PURPLE),
]

for x, label, value, accent in cards:
    svg.extend([
        f'<rect x="{x}" y="30" width="350" height="170" rx="20" fill="{PANEL}" stroke="{GRID}"/>',
        f'<circle cx="{x+315}" cy="65" r="8" fill="{accent}"/>',
        f'<text x="{x+28}" y="72" fill="{MUTED}" font-family="Arial,sans-serif" font-size="15" font-weight="700" letter-spacing="1">{label}</text>',
        f'<text x="{x+28}" y="142" fill="{TEXT}" font-family="Arial,sans-serif" font-size="58" font-weight="800">{value}</text>',
    ])

# Circular current-streak ring, inspired by the reference screenshot.
cx, cy, radius = 600, 112, 55
circ = 2 * 3.14159265359 * radius
progress = min(1.0, current / max(1, longest)) if longest else 0
svg.extend([
    f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{GRID}" stroke-width="7"/>',
    f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{PINK}" stroke-width="7" stroke-linecap="round" stroke-dasharray="{circ*progress:.1f} {circ:.1f}" transform="rotate(-90 {cx} {cy})"/>',
])

# Weekly line chart.
sx, sy, sw, sh = 55, 275, 1090, 150
maximum = max(1, max(weekly))
points = []
for i, value in enumerate(weekly):
    x = sx + i * sw / (len(weekly) - 1)
    y = sy + sh - (value / maximum) * (sh - 20)
    points.append((x, y))

svg.append(f'<text x="55" y="245" fill="{TEXT}" font-family="Arial,sans-serif" font-size="18" font-weight="700">weekly activity</text>')
for yoff in (0, 0.5, 1):
    y = sy + sh - yoff * (sh - 20)
    svg.append(f'<line x1="55" y1="{y:.1f}" x2="1145" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')

path = " ".join(("M" if i == 0 else "L") + f" {x:.1f} {y:.1f}" for i, (x, y) in enumerate(points))
area = path + f" L {points[-1][0]:.1f} {sy+sh} L {points[0][0]:.1f} {sy+sh} Z"
svg.extend([
    f'<path d="{area}" fill="{PINK}" opacity="0.08"/>',
    f'<path d="{path}" fill="none" stroke="{PINK}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>',
])
for x, y in points:
    svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{PINK}"/>')

svg.extend([
    f'<text x="55" y="470" fill="{MUTED}" font-family="Arial,sans-serif" font-size="13">last 16 weeks · generated from GitHub</text>',
    "</svg>",
])
(ASSETS / "stats.svg").write_text("\n".join(svg), encoding="utf-8")

# ---------- one-year contribution graph ----------
W, H = 1200, 310
CELL, GAP = 18, 5
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

svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
svg.append(f'<rect width="{W}" height="{H}" rx="26" fill="{BG}"/>')
svg.append(f'<text x="35" y="35" fill="{TEXT}" font-family="Arial,sans-serif" font-size="18" font-weight="700">contribution graph</text>')

# Sunday-aligned 53-week grid.
grid_start = start - timedelta(days=(start.weekday() + 1) % 7)
for col in range(53):
    for row in range(7):
        day = grid_start + timedelta(days=col * 7 + row)
        if start <= day <= today:
            x = GX + col * (CELL + GAP)
            y = GY + row * (CELL + GAP)
            svg.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="4" fill="{heat_color(days.get(str(day), 0))}"/>'
            )

svg.append(f'<text x="35" y="285" fill="{MUTED}" font-family="Arial,sans-serif" font-size="13">less</text>')
for i, color in enumerate(["#1b1b23", "#4b2540", PINK_DARK, PINK_LIGHT, PINK]):
    svg.append(f'<rect x="{70+i*23}" y="273" width="18" height="18" rx="4" fill="{color}"/>')
svg.extend([
    f'<text x="188" y="285" fill="{MUTED}" font-family="Arial,sans-serif" font-size="13">more</text>',
    f'<text x="1010" y="285" fill="{MUTED}" font-family="Arial,sans-serif" font-size="13">{calendar["totalContributions"]} contributions</text>',
    "</svg>",
])
(ASSETS / "year.svg").write_text("\n".join(svg), encoding="utf-8")

print(f"Generated stats.svg and year.svg for {LOGIN}")
