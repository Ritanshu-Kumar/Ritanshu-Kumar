#!/usr/bin/env python3
from pathlib import Path
import html
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "portrait-source.jpg"
OUTPUT = ROOT / "assets" / "portrait.svg"

img = Image.open(SOURCE).convert("RGB")
w, h = img.size
img = img.crop((0, 0, int(w * 0.88), int(h * 0.93)))
gray = ImageEnhance.Contrast(
    ImageOps.grayscale(img).filter(ImageFilter.GaussianBlur(0.35))
).enhance(1.16)

cols = 92
rows = max(1, int(cols * gray.height / gray.width * 0.47))
gray = gray.resize((cols, rows))
ramp = " .`:-=+*cs#%@"
pixels = list(gray.getdata())

lines = []
for y in range(rows):
    line = []
    for x in range(cols):
        value = pixels[y * cols + x]
        index = min(len(ramp)-1, int((255-value) / 256 * len(ramp)))
        line.append(ramp[index])
    lines.append("".join(line).rstrip())

line_height = 12.5
font_size = 12.9
width = cols * 7.74
height = rows * line_height + 10
clips, texts = [], []

for i, line in enumerate(lines):
    y = 10 + (i+1) * line_height
    clips.append(
        '<clipPath id="c{}"><rect x="0" y="{:.1f}" width="0" height="{:.1f}">'
        '<animate attributeName="width" from="0" to="{:.1f}" dur="0.75s" '
        'begin="{:.2f}s" fill="freeze"/></rect></clipPath>'.format(
            i, i*line_height, line_height+1, width, i*0.055
        )
    )
    texts.append(
        '<text x="0" y="{:.1f}" class="r" clip-path="url(#c{})">{}</text>'.format(
            y, i, html.escape(line)
        )
    )

svg = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="{:.0f}" height="{:.0f}" '
    'viewBox="0 0 {:.1f} {:.1f}">'.format(width, height, width, height)
    + '<defs>' + ''.join(clips) + '</defs>'
    + '<style>.r{{font-family:"DejaVu Sans Mono",monospace;font-size:{}px;'
      'white-space:pre;fill:#f4f4f5;}}</style>'.format(font_size)
    + '<g>' + ''.join(texts) + '</g></svg>'
)

OUTPUT.write_text(svg, encoding="utf-8")
print("wrote", OUTPUT)
