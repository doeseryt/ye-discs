#!/usr/bin/env python3
"""Generate a gallery image: the 15 track discs in a grid 5x3, upscaled from 16x16 textures."""
import struct
import zlib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX = os.path.join(ROOT, "src", "main", "resources", "assets", "ye_discs", "textures", "item")
OUT = os.path.join(ROOT, ".media", "gallery_discs.png")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

TRACKS = [
    "through_the_wire", "gold_digger", "stronger", "heartless", "runaway",
    "nias_in_paris", "black_skinhead", "famous", "ghost_town", "follow_god",
    "hurricane", "true_love", "carnival", "five_30", "bully",
]

SCALE = 6
COLS, ROWS = 5, 3
PAD = 12
W = COLS * 16 * SCALE + (COLS + 1) * PAD
H = ROWS * 16 * SCALE + (ROWS + 1) * PAD

def read_png(path):
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    idat = b""
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos+4])[0]
        typ = data[pos+4:pos+8]
        chunk = data[pos+8:pos+8+ln]
        if typ == b"IDAT":
            idat += chunk
        pos += 12 + ln
    raw = zlib.decompress(idat)
    # 16x16 RGBA with filter bytes
    pixels = []
    stride = 16 * 4 + 1
    for y in range(16):
        row_start = y * stride + 1
        row = []
        for x in range(16):
            off = row_start + x * 4
            row.append((raw[off], raw[off+1], raw[off+2], raw[off+3]))
        pixels.append(row)
    return pixels

def png_chunk(typ, data):
    return struct.pack(">I", len(data)) + typ + data + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

# background near-black
img = {}
import random
rng = random.Random(7)
for y in range(H):
    for x in range(W):
        n = rng.randint(-3, 3)
        img[y * W + x] = (16 + n, 15 + n, 14 + n, 255)

for idx, track in enumerate(TRACKS):
    tex = read_png(os.path.join(TEX, f"ye_disc_{track}.png"))
    col = idx % COLS
    row = idx // COLS
    ox = PAD + col * (16 * SCALE + PAD)
    oy = PAD + row * (16 * SCALE + PAD)
    for y in range(16 * SCALE):
        for x in range(16 * SCALE):
            t = tex[y // SCALE][x // SCALE]
            img[(oy + y) * W + (ox + x)] = t

with open(OUT, "wb") as f:
    f.write(b"\x89PNG\r\n\x1a\n")
    f.write(png_chunk(b"IHDR", struct.pack(b">IIBBBBB", W, H, 8, 6, 0, 0, 0)))
    raw = b""
    for y in range(H):
        raw += b"\x00"
        for x in range(W):
            p = img[y * W + x]
            raw += bytes((p[0], p[1], p[2], p[3]))
    f.write(png_chunk(b"IDAT", zlib.compress(raw, 9)))
    f.write(png_chunk(b"IEND", b""))
print("wrote", OUT, W, "x", H)
