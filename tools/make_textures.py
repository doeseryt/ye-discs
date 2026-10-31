#!/usr/bin/env python3
"""Generate 16x16 music disc textures — one disc per Kanye West album,
styled for that album's most popular track.

Programmatic pixel art: black disc, cream/vinyl-noise ring, each disc gets
its own accent color tied to the track. No copyrighted artwork is
reproduced.
"""
import os
import random
import struct
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "src", "main", "resources", "assets", "ye_discs", "textures", "item")
os.makedirs(TEX, exist_ok=True)

# track palettes
ACCENTS = {
    "through_the_wire":  (203, 108, 74),   # warm chipmunk-soul rust
    "gold_digger":       (216, 176, 92),   # gilded gold
    "stronger":          (70, 78, 105),    # vocoder glacier blue
    "heartless":         (88, 96, 128),    # frozen 808 blue-grey
    "runaway":           (196, 60, 44),    # single-take crimson
    "nias_in_paris":     (150, 128, 190),  # operatic royal purple
    "black_skinhead":    (232, 232, 228),  # brutalist blank white
    "famous":            (240, 128, 176),  # faded scandal pink
    "ghost_town":        (136, 176, 104),  # wyoming sage green
    "follow_god":        (18, 100, 130),   # blue gospel water
    "hurricane":         (60, 84, 150),    # storm blue
    "true_love":         (120, 108, 96),   # muted unfinished tan
    "carnival":          (168, 156, 130),  # dusty funfair bone
    "five_30":           (34, 34, 38),     # slowed stem-player gunmetal
    "bully":             (196, 157, 106),  # washed dusty gold — BULLY
}

DISC = [
    "................",
    "......xxxx......",
    "....xxxxxxxx....",
    "...xxxxxxxxxx...",
    "..xxxxxxxxxxxx..",
    "..xxxxxxxxxxxx..",
    ".xxxxxxxxxxxxxx.",
    ".xxxxxxxxxxxxxx.",
    ".xxxxxxxxxxxxxx.",
    ".xxxxxxxxxxxxxx.",
    "..xxxxxxxxxxxx..",
    "..xxxxxxxxxxxx..",
    "...xxxxxxxxxx...",
    "....xxxxxxxx....",
    "......xxxx......",
    "................",
]

def build(name, accent):
    rng = random.Random(hash(name) & 0xFFFF)
    pixels = {}
    ax, ay, aa = accent
    for y, row in enumerate(DISC):
        for x, ch in enumerate(row):
            if ch == 'x':
                n = rng.randint(-6, 6)
                base = (28 + n, 26 + n, 24 + n)
                d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
                if 4.6 <= d <= 5.9:
                    fade = rng.randint(-24, 18)
                    base = (max(0, min(255, ax + fade)),
                            max(0, min(255, ay + fade)),
                            max(0, min(255, aa + fade)))
                pixels[y * 16 + x] = base + (255,)
    # center hole
    pixels[7 * 16 + 7] = (0, 0, 0, 255)
    pixels[7 * 16 + 8] = (0, 0, 0, 255)
    pixels[8 * 16 + 7] = (0, 0, 0, 255)
    pixels[8 * 16 + 8] = (0, 0, 0, 255)
    # cream ring around hole
    for (x, y) in [(6, 7), (7, 6), (8, 6), (9, 7), (9, 8), (8, 9), (7, 9), (6, 8)]:
        pixels[y * 16 + x] = (222, 214, 196, 255)
    # sheen
    sheen = [(3, 3), (4, 2), (2, 4), (5, 3)]
    for (x, y) in sheen:
        if DISC[y][x] == 'x':
            n = rng.randint(10, 40)
            pixels[y * 16 + x] = (70 + n, 66 + n, 60 + n, 255)
    out = os.path.join(TEX, f"ye_disc_{name}.png")
    with open(out, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        ihdr = struct.pack(b">IIBBBBB", 16, 16, 8, 6, 0, 0, 0)
        f.write(png_chunk(b"IHDR", ihdr))
        raw = b""
        for y in range(16):
            raw += b"\x00"
            for x in range(16):
                p = pixels.get(y * 16 + x, (0, 0, 0, 0))
                raw += bytes((p[0], p[1], p[2], p[3]))
        f.write(png_chunk(b"IDAT", zlib.compress(raw, 9)))
        f.write(png_chunk(b"IEND", b""))
    return out

def png_chunk(typ, data):
    return struct.pack(">I", len(data)) + typ + data + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

if __name__ == "__main__":
    for name, accent in ACCENTS.items():
        out = build(name, accent)
        print("wrote", out)
