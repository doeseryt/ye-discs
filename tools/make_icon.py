#!/usr/bin/env python3
"""Generate the 400x400 mod icon: a large disc with era accent stripes."""
import struct
import zlib
import random
import os

W = H = 400
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "src", "main", "resources", "assets", "ye_discs", "icon.png")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# track colors for the ring stripes
STRIPES = [
    (203, 108, 74),  # through the wire
    (216, 176, 92),  # gold digger
    (70, 78, 105),   # stronger
    (88, 96, 128),   # heartless
    (196, 60, 44),   # runaway
    (150, 128, 190), # n** in paris
    (232, 232, 228), # black skinhead
    (240, 128, 176), # famous
    (136, 176, 104), # ghost town
    (18, 100, 130),  # follow god
    (60, 84, 150),   # hurricane
    (120, 108, 96),  # true love
    (168, 156, 130), # carnival
    (34, 34, 38),    # 530
    (196, 157, 106), # bully
]

rng = random.Random(2026)
cx = cy = 200.0

def put(pixels, x, y, rgb, a=255):
    if 0 <= x < W and 0 <= y < H:
        pixels[y * W + x] = rgb + (a,)

pixels = {}
# background: near-black
for y in range(H):
    for x in range(W):
        n = rng.randint(-4, 4)
        pixels[y * W + x] = (16 + n, 15 + n, 14 + n, 255)

# outer disc
outer = 190.0
inner_hole = 22.0
label_r1, label_r2 = 60.0, 95.0

for y in range(H):
    for x in range(W):
        d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        if d > outer:
            continue
        n = rng.randint(-5, 5)
        rgb = (26 + n, 25 + n, 24 + n)
        # stripes: angular sectors on the ring between label and rim
        if label_r2 < d < outer - 8:
            import math
            ang = (math.atan2(y - cy, x - cx) + math.pi) / (2 * math.pi)
            idx = int(ang * len(STRIPES)) % len(STRIPES)
            base = STRIPES[idx]
            fade = rng.randint(-22, 18)
            rgb = (max(0, min(255, base[0] + fade)),
                   max(0, min(255, base[1] + fade)),
                   max(0, min(255, base[2] + fade)))
            # soft vignette toward rim
            if d > outer - 24:
                k = (d - (outer - 24)) / 24.0
                rgb = tuple(int(c * (1 - 0.55 * k) + 20 * k) for c in rgb)
        elif label_r1 <= d <= label_r2:
            # cream label
            n = rng.randint(-10, 10)
            rgb = (214 + n, 202 + n, 184 + n)
        put(pixels, x, y, rgb)

# hole
for y in range(H):
    for x in range(W):
        d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        if d < inner_hole:
            pixels[y * W + x] = (8, 8, 8, 255)

# sheen arc top-left
for y in range(H):
    for x in range(W):
        d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        if label_r2 < d < outer - 8:
            if -2.2 < (x - cx) / (d + 1e-6) < -1.2 and -1.9 < (y - cy) / (d + 1e-6) < -0.9:
                if rng.random() < 0.35:
                    c = pixels[y * W + x]
                    pixels[y * W + x] = (min(255, c[0] + 26), min(255, c[1] + 26), min(255, c[2] + 22), 255)

# write PNG
def png_chunk(typ, data):
    return struct.pack(">I", len(data)) + typ + data + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

with open(OUT, "wb") as f:
    f.write(b"\x89PNG\r\n\x1a\n")
    f.write(png_chunk(b"IHDR", struct.pack(b">IIBBBBB", W, H, 8, 6, 0, 0, 0)))
    raw = b""
    for y in range(H):
        raw += b"\x00"
        for x in range(W):
            p = pixels.get(y * W + x, (0, 0, 0, 0))
            raw += bytes((p[0], p[1], p[2], p[3]))
    f.write(png_chunk(b"IDAT", zlib.compress(raw, 9)))
    f.write(png_chunk(b"IEND", b""))
print("wrote", OUT)
