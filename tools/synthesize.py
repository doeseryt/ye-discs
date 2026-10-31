#!/usr/bin/env python3
"""Synthesize original instrumental tracks inspired by the eras of Kanye
West's discography — one disc per album.

All audio is generated from scratch (sine/saw/triangle/square oscillators,
noise drums, FM keys, simple envelopes). No samples of any commercial
recording are used. Track names identify the era of each album.
"""
import math
import os
import struct
import wave
import random

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SND = os.path.join(ROOT, "assets", "ye_discs", "sounds")
os.makedirs(SND, exist_ok=True)

PI2 = math.pi * 2.0

# note frequency helper: midi -> Hz
def nf(m):
    return 440.0 * (2.0 ** ((m - 69) / 12.0))

def clamp(x, lo=-1.0, hi=1.0):
    return lo if x < lo else (hi if x > hi else x)

class Buf:
    def __init__(self, dur):
        self.n = int(dur * SR)
        self.d = [0.0] * self.n

    def __len__(self):
        return self.n

    def add(self, i, v):
        if 0 <= i < self.n:
            self.d[i] += v

    def normalize(self, peak=0.92):
        m = max((abs(x) for x in self.d), default=0.0)
        if m > 1e-9:
            k = peak / m
            self.d = [x * k for x in self.d]

    def write_wav(self, path):
        self.normalize()
        with wave.open(path, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            frames = bytearray()
            for x in self.d:
                xi = int(clamp(x) * 32767.0)
                frames += struct.pack("<h", xi)
            w.writeframes(bytes(frames))

def env_ar(i, n, a, r):
    if i < a and a > 0:
        return i / a
    if i >= n - r and r > 0:
        return max(0.0, (n - i) / r)
    return 1.0

def sine(p):
    return math.sin(PI2 * p)

def saw(p):
    p = p % 1.0
    return 2.0 * p - 1.0

def tri(p):
    p = p % 1.0
    if p < 0.5:
        return 4.0 * p - 1.0
    return 3.0 - 4.0 * p

def square(p, duty=0.5):
    p = p % 1.0
    return 1.0 if p < duty else -1.0

def lp_step(x, y_prev, cutoff):
    a = 1.0 - math.exp(-PI2 * cutoff / SR)
    return y_prev + a * (x - y_prev)

def render_note(buf, start, dur, freq, vol, wave_fn, a=0.004, r=0.05,
                detune=0.0, fm_depth=0.0, fm_ratio=1.0, lp=None):
    n = int(dur * SR)
    ph = 0.0
    ph2 = 0.0
    y = 0.0
    inc = freq / SR
    inc2 = freq * fm_ratio / SR
    for i in range(n):
        e = env_ar(i, n, a * SR, r * SR)
        mod = sine(ph2) * fm_depth
        v = wave_fn(ph + mod + detune * (i / SR))
        if lp:
            y = lp_step(v, y, lp)
            v = y
        buf.add(start + i, v * vol * e)
        ph += inc
        ph2 += inc2
    return

def kick(buf, start, vol=0.9, dur=0.30):
    n = int(dur * SR)
    ph = 0.0
    for i in range(n):
        t = i / SR
        f = 42.0 + 110.0 * math.exp(-t * 26.0)
        ph += f / SR
        e = math.exp(-t * 9.0)
        click = (random.random() * 2 - 1) * 0.4 * math.exp(-t * 900.0)
        buf.add(start + i, (sine(ph) * 0.95 + click) * vol * e)

def snare(buf, start, vol=0.55, dur=0.18):
    n = int(dur * SR)
    ph = 0.0
    for i in range(n):
        t = i / SR
        noise = (random.random() * 2 - 1)
        tone = sine(ph) * 0.5
        ph += (190.0 / SR)
        e = math.exp(-t * 34.0)
        buf.add(start + i, (noise * 0.8 + tone) * vol * e)

def hat(buf, start, vol=0.22, dur=0.06, hp=True):
    n = int(dur * SR)
    prev = 0.0
    for i in range(n):
        t = i / SR
        noise = (random.random() * 2 - 1)
        if hp:
            v = noise - prev
            prev = noise
            noise = v * 1.2
        e = math.exp(-t * 90.0)
        buf.add(start + i, noise * vol * e)

def crash(buf, start, vol=0.4, dur=2.2):
    n = int(dur * SR)
    prev = 0.0
    for i in range(n):
        t = i / SR
        noise = (random.random() * 2 - 1)
        v = noise - prev
        prev = noise
        e = math.exp(-t * 2.2)
        buf.add(start + i, v * 0.7 * vol * e)

def vinyl(buf, vol=0.012, seed=7):
    rng = random.Random(seed)
    for i in range(len(buf)):
        buf.d[i] += (rng.random() *2 - 1) * vol
    for _ in range(int(len(buf) / SR * 3)):
        p = rng.randrange(len(buf))
        ln = int(0.003 * SR)
        for j in range(ln):
            buf.add(p + j, (rng.random() * 2 - 1) * 0.05 * math.exp(-j / (0.001 * SR)))

def fade_out(buf, seconds):
    n = int(seconds * SR)
    for i in range(n):
        idx = len(buf) - n + i
        if 0 <= idx < len(buf):
            buf.d[idx] *= 1.0 - i / n

def fade_in(buf, seconds):
    n = int(seconds * SR)
    for i in range(min(n, len(buf))):
        buf.d[i] *= i / n

def sample_pad(buf, prog, bpm, bar_len, pad_vol, wave_fn=saw, lp=1200.0, seed=11):
    """detuned soul-sample pad with vinyl noise."""
    beat = 60.0 / bpm
    bar = beat * bar_len
    for bi, chords in enumerate(prog):
        t0 = bi * bar
        if t0 >= len(buf) / SR:
            break
        for note, vel, hold in chords:
            render_note(buf, int(t0 * SR), min(hold, len(buf) / SR - t0), nf(note), pad_vol * vel,
                        wave_fn, a=0.03, r=0.4, detune=0.0015, lp=lp)
            render_note(buf, int(t0 * SR), min(hold, len(buf) / SR - t0) * 0.7, nf(note + 12) * 1.003,
                        pad_vol * vel * 0.35, sine, a=0.05, r=0.5)
    vinyl(buf, seed=seed)

# ---------------------------------------------------------------------------
# track generators — one per album era, original composition in that style
# ---------------------------------------------------------------------------

def track_college_dropout():
    """Speed-up soul chipmunk loop, dusty, backpack warmth."""
    dur = 100
    buf = Buf(dur)
    bpm = 94
    beat = 60.0 / bpm
    sample_pad(buf, [
        [(57, 0.9, 3.6), (61, 0.7, 3.6), (64, 0.6, 3.6), (69, 0.3, 1.8)],
        [(53, 0.9, 3.6), (57, 0.7, 3.6), (60, 0.6, 3.6), (65, 0.3, 1.8)],
        [(55, 0.9, 3.6), (59, 0.7, 3.6), (62, 0.6, 3.6), (67, 0.3, 1.8)],
        [(50, 0.9, 3.6), (54, 0.7, 3.6), (57, 0.6, 3.6), (62, 0.3, 1.8)],
    ] * 10, bpm, 4, 0.30, lp=1100.0, seed=21)
    # pitched-up "chipmunk" lead doubles the top note
    for rep in range(int(dur / (beat * 4)) + 1):
        t0 = rep * beat * 4
        lead = [69, 72, 69, 67, 69, 71, 69, 66, 64, 66, 69, 71, 72, 71, 69, 67]
        for k, m in enumerate(lead):
            st = t0 + k * beat * 0.5
            if st < dur - 0.2:
                render_note(buf, int(st * SR), beat * 0.5, nf(m) * 2, 0.06, saw, a=0.004, r=0.12, lp=3400.0)
    # dusty boom-bap drums
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if t0 < dur - 0.4:
            kick(buf, int(t0 * SR), vol=0.7)
            snare(buf, int((t0 + beat) * SR), vol=0.42)
            hat(buf, int((t0 + beat * 1.5) * SR), vol=0.10)
    fade_in(buf, 1.0)
    fade_out(buf, 3.0)
    return buf

def track_late_registration():
    """Soul + strings: Juno melancholy, orchestral swells over hip-hop drums."""
    dur = 106
    buf = Buf(dur)
    bpm = 87
    beat = 60.0 / bpm
    sample_pad(buf, [
        [(53, 0.9, 3.8), (57, 0.7, 3.8), (60, 0.6, 3.8), (65, 0.35, 1.9)],
        [(55, 0.9, 3.8), (59, 0.7, 3.8), (62, 0.6, 3.8), (67, 0.35, 1.9)],
        [(48, 0.9, 3.8), (52, 0.7, 3.8), (55, 0.6, 3.8), (60, 0.35, 1.9)],
        [(50, 0.9, 3.8), (54, 0.7, 3.8), (57, 0.6, 3.3), (62, 0.35, 1.9)],
    ] * 10, bpm, 4, 0.26, lp=1000.0, seed=33)
    # string swells (detuned saw ensemble, slow attack)
    prog = [53, 55, 48, 50]
    for rep in range(int(dur / (beat * 4)) + 1):
        t0 = rep * beat * 4
        root = prog[rep % 4]
        for note in [root + 12, root + 16, root + 19, root + 24]:
            render_note(buf, int(t0 * SR), beat * 4.0, nf(note), 0.06, saw, a=0.6, r=1.0, detune=0.002, lp=1500.0)
    # congas-ish percussion accents
    for bi in range(int(dur / (beat * 0.5)) + 1):
        t0 = bi * beat * 0.5
        if bi % 4 == 2 and t0 < dur - 0.2:
            n = int(0.14 * SR)
            ph = 0.0
            for i in range(n):
                t = i / SR
                f = 160 * math.exp(-t * 8) + 95
                ph += f / SR
                buf.add(int(t0 * SR) + i, sine(ph) * 0.22 * math.exp(-t * 18))
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if t0 < dur - 0.4:
            kick(buf, int(t0 * SR), vol=0.68)
            snare(buf, int((t0 + beat) * SR), vol=0.38)
    fade_in(buf, 1.5)
    fade_out(buf, 4.0)
    return buf

def track_graduation():
    """Electro-house stomp: filtered synth riff, four-on-floor, arena size."""
    dur = 104
    buf = Buf(dur)
    bpm = 126
    beat = 60.0 / bpm
    # main electro riff — single-note square pulse with filter opening
    riff = [45, 45, 45, 45, 48, 48, 47, 45]
    for rep in range(int(dur / (beat * 2)) + 1):
        for k, note in enumerate(riff):
            st = rep * beat * 2 + k * beat * 0.5
            if st < dur - 0.1:
                render_note(buf, int(st * SR), beat * 0.45, nf(note), 0.26, square, a=0.002, r=0.08, lp=900 + 2200 * min(1.0, st / dur))
    # octave-up arp layer
    for rep in range(int(dur / (beat * 2)) + 1):
        for k, note in enumerate([57, 60, 59, 57, 60, 62, 59, 57]):
            st = rep * beat * 2 + k * beat * 0.5 + beat * 0.25
            if st < dur - 0.1:
                render_note(buf, int(st * SR), 0.12, nf(note), 0.08, saw, a=0.002, r=0.05, lp=3000.0)
    # four-on-floor
    for bi in range(int(dur / (beat * 0.5)) + 1):
        t0 = bi * beat * 0.5
        if t0 < dur - 0.4 and bi % 2 == 0:
            kick(buf, int(t0 * SR), vol=0.9)
        if t0 < dur - 0.3 and bi % 2 == 1:
            hat(buf, int(t0 * SR), vol=0.14, dur=0.05)
    for bi in range(int(dur / (beat * 4)) + 1):
        snare(buf, int((bi * beat * 4 + beat * 2) * SR), vol=0.5)
    crash(buf, 0, vol=0.4)
    fade_in(buf, 0.8)
    fade_out(buf, 2.5)
    return buf

def track_808s():
    """Frozen 808 minimalism: icy keys, huge sub, v vocoder-ish pads, no snare warmth."""
    dur = 108
    buf = Buf(dur)
    bpm = 75
    beat = 60.0 / bpm
    # icy FM keys arpeggio (tragic two-chord)
    prog = [
        [(52, 0.8), (55, 0.6), (59, 0.5), (64, 0.35)],
        [(50, 0.8), (53, 0.6), (57, 0.5), (62, 0.35)],
    ] * 15
    bar = beat * 4
    for bi, chord in enumerate(prog):
        t0 = bi * bar
        if t0 >= dur:
            break
        for (note, vel) in chord:
            render_note(buf, int(t0 * SR), min(bar, dur - t0), nf(note), 0.13 * vel, sine,
                        a=0.02, r=0.9, fm_depth=0.6, fm_ratio=2.0)
    # massive 808 sub on roots, long decay
    roots = [28, 26]
    for bi in range(int(dur / bar) + 1):
        t0 = bi * bar
        r = roots[bi % 2]
        for off in [0, 2.5]:
            st = t0 + off * beat
            if st < dur - 0.5:
                render_note(buf, int(st * SR), beat * 2.2, nf(r), 0.65, sine, a=0.004, r=1.2)
    # frozen hats, skeletal
    for bi in range(int(dur / (beat * 0.5)) + 1):
        t0 = bi * beat * 0.5
        if t0 < dur - 0.1 and bi % 2 == 1:
            hat(buf, int(t0 * SR), vol=0.08, dur=0.04)
    # sparse kick
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if t0 < dur - 0.4:
            kick(buf, int(t0 * SR), vol=0.55, dur=0.35)
    # vocoder-ish pad shimmer
    for i in range(len(buf)):
        t = i / SR
        if t > 8:
            v = (sine(i * nf(64) / SR) * 0.5 + sine(i * nf(67) / SR) * 0.3) * 0.05
            v *= 0.5 + 0.5 * sine(i / SR * 0.25)
            buf.d[i] += v
    fade_in(buf, 2.0)
    fade_out(buf, 5.0)
    return buf

def track_mbdtf():
    """Maximalist pomp: distorted piano riff, huge drums, King Crimson-ish odd stabs."""
    dur = 110
    buf = Buf(dur)
    bpm = 87
    beat = 60.0 / bpm
    # hammered piano riff (FM bright) — dark ostinato
    riff = [50, 57, 50, 55, 50, 57, 50, 53, 50, 57, 50, 55, 50, 57, 51, 54]
    for rep in range(int(dur / (beat * 4)) + 1):
        t0 = rep * beat * 4
        for k, m in enumerate(riff):
            st = t0 + k * beat * 0.5
            if st < dur - 0.2:
                render_note(buf, int(st * SR), beat * 0.5, nf(m), 0.20, sine, a=0.001, r=0.25, fm_depth=0.4, fm_ratio=2.0)
    # huge orchestral chords every 2 bars
    for rep in range(int(dur / (beat * 2)) + 1):
        t0 = rep * beat * 2
        chords = [
            [(45, 0.8), (52, 0.6), (57, 0.5), (61, 0.4)],
            [(43, 0.8), (50, 0.6), (55, 0.5), (59, 0.4)],
        ]
        for (note, vel) in chords[rep % 2]:
            render_note(buf, int(t0 * SR), beat * 1.9, nf(note), 0.12 * vel, saw, a=0.08, r=0.6, detune=0.003, lp=1600.0)
    # giant drums
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if t0 < dur - 0.5:
            kick(buf, int(t0 * SR), vol=0.95)
            snare(buf, int((t0 + beat) * SR), vol=0.5)
    for bi in range(int(dur / (beat * 0.5)) + 1):
        t0 = bi * beat * 0.5
        if t0 < dur - 0.1:
            hat(buf, int(t0 * SR), vol=0.08, dur=0.03)
    # early treble alarm motif enters at half
    st0 = int(dur * 0.5 * SR)
    for rep in range(4):
        st = st0 + int(rep * beat * 4 * SR)
        for note in [76, 74, 71, 69]:
            render_note(buf, st, beat * 1.6, nf(note), 0.12, saw, a=0.01, r=0.4, lp=2800.0, detune=0.001)
    crash(buf, 0, vol=0.5)
    crash(buf, int(dur * 0.5 * SR), vol=0.4)
    fade_in(buf, 1.2)
    fade_out(buf, 3.5)
    return buf

def track_watch_the_throne():
    """Operatic soul-trap: brass fanfare, huge 808s, haughty strings."""
    dur = 102
    buf = Buf(dur)
    bpm = 96
    beat = 60.0 / bpm
    # brass fanfare motif
    fanfare = [(57, 0), (60, 0.5), (62, 1.0), (57, 1.5), (60, 2.0), (64, 2.5), (62, 3.0), (57, 3.5)]
    for rep in range(int(dur / (beat * 4)) + 1):
        t0 = rep * beat * 4
        for (m, k) in fanfare:
            st = t0 + k * beat
            if st < dur - 0.3:
                render_note(buf, int(st * SR), beat * 0.7, nf(m), 0.18, saw, a=0.01, r=0.25, detune=0.003, lp=1900.0)
                render_note(buf, int(st * SR), beat * 0.7, nf(m - 12), 0.12, saw, a=0.01, r=0.25, detune=0.004, lp=900.0)
    # haughty strings pad
    prog = [
        [(53, 0.9), (60, 0.7), (65, 0.5)],
        [(55, 0.9), (62, 0.7), (67, 0.5)],
        [(50, 0.9), (57, 0.7), (62, 0.5)],
        [(53, 0.9), (60, 0.40), (64, 0.5)],
    ] * 10
    bar = beat * 4
    for bi, chord in enumerate(prog):
        t0 = bi * bar
        if t0 >= dur:
            break
        for (note, vel) in chord:
            render_note(buf, int(t0 * SR), min(bar, dur - t0), nf(note), 0.10 * vel, saw, a=0.3, r=0.8, detune=0.002, lp=1400.0)
    # huge 808 trap bass
    bassline = [29, 29, 31, 29, 26, 26, 29, 28]
    for rep in range(int(dur / (beat * 2)) + 1):
        for k, b in enumerate(bassline):
            st = rep * beat * 2 + k * beat * 0.5
            if st < dur - 0.2:
                render_note(buf, int(st * SR), beat * 0.9, nf(b), 0.55, sine, a=0.005, r=0.3)
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if t0 < dur - 0.4:
            kick(buf, int(t0 * SR), vol=0.85)
            snare(buf, int((t0 + beat) * SR), vol=0.45)
    for bi in range(int(dur / (beat * 0.5)) + 1):
        t0 = bi * beat * 0.5
        if t0 < dur - 0.1 and bi % 2 == 1:
            hat(buf, int(t0 * SR), vol=0.10, dur=0.03)
    crash(buf, 0, vol=0.45)
    fade_in(buf, 1.0)
    fade_out(buf, 3.0)
    return buf

def track_yeezus():
    """Industrial brutality: acid bass, drill kicks, screams of noise, minimal."""
    dur = 96
    buf = Buf(dur)
    bpm = 140
    beat = 60.0 / bpm
    # acid bassline (square with FM self-feedback feel)
    acidline = [33, 33, 36, 33, 40, 33, 33, 36, 31, 33, 33, 36, 38, 33, 33, 30]
    for rep in range(int(dur / (beat * 2)) + 1):
        for k, note in enumerate(acidline):
            st = rep * beat * 2 + k * beat * 0.25
            if st < dur - 0.1:
                render_note(buf, int(st * SR), 0.14, nf(note), 0.38, square, a=0.001, r=0.06, fm_depth=0.8, fm_ratio=1.5, lp=1400.0)
    # drill kick pattern
    for bi in range(int(dur / (beat * 0.5)) + 1):
        t0 = bi * beat * 0.5
        if t0 < dur - 0.3:
            kick(buf, int(t0 * SR), vol=0.95, dur=0.18)
        if bi % 8 == 6:
            kick(buf, int((t0 + beat * 0.25) * SR), vol=0.7, dur=0.15)
    # metallic hats
    for bi in range(int(dur / (beat * 0.5)) + 1):
        t0 = bi * beat * 0.5 + beat * 0.25
        if t0 < dur - 0.1:
            hat(buf, int(t0 * SR), vol=0.12, dur=0.02)
    # distorted scream-noise layer in second half
    for i in range(int(len(buf) * 0.5)):
        idx = len(buf) - int(len(buf) * 0.5) + i
        t = i / SR
        a = 0.04 * min(1.0, t / 20.0)
        v = clamp((sine(idx * nf(69) / SR) + square(idx * nf(62) / SR) * 0.5) * 3.0, -1, 1)
        buf.d[idx] += v * a
    fade_in(buf, 0.5)
    fade_out(buf, 2.0)
    return buf

def track_tlop():
    """Gospel-edged maximal collage: choir-ish pads, sudden soul chops, chaos under control."""
    dur = 104
    buf = Buf(dur)
    bpm = 105
    beat = 60.0 / bpm
    # choir-ish pad (stacked fifths)
    prog = [
        [(53, 0.9), (60, 0.7), (64, 0.5), (69, 0.3)],
        [(55, 0.9), (62, 0.7), (66, 0.5), (71, 0.3)],
        [(48, 0.9), (55, 0.7), (60, 0.5), (65,0.30)],
        [(50, 0.9), (57, 0.7), (62, 0.5), (67, 0.3)],
    ] * 10
    bar = beat * 4
    for bi, chord in enumerate(prog):
        t0 = bi * bar
        if t0 >= dur:
            break
        for (note, vel) in chord:
            render_note(buf, int(t0 * SR), min(bar, dur - t0), nf(note), 0.12 * vel, sine, a=0.15, r=0.7)
            render_note(buf, int(t0 * SR), min(bar, dur - t0), nf(note + 7), 0.05 * vel, sine, a=0.15, r=0.7)
    # sudden soul chops
    chop_notes = [74, 76, 79, 76, 74, 71, 74, 76]
    for rep in range(int(dur / (beat * 4)) + 1):
        t0 = rep * beat * 4
        for k, m in enumerate(chop_notes):
            if k in (0, 2, 3, 6):  # stutter placements
                st = t0 + k * beat * 0.5
                if st < dur - 0.2:
                    render_note(buf, int(st * SR), 0.18, nf(m) * 2, 0.16, saw, a=0.003, r=0.1, lp=2400.0)
    # trap drums
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if t0 < dur - 0.4:
            kick(buf, int(t0 * SR), vol=0.88)
            snare(buf, int((t0 + beat) * SR), vol=0.44)
    for bi in range(int(dur / (beat * 0.25)) + 1):
        t0 = bi * beat * 0.25
        if t0 < dur - 0.05:
            hat(buf, int(t0 * SR), vol=0.09, dur=0.025)
    fade_in(buf, 1.0)
    fade_out(buf, 3.0)
    return buf

def track_ye():
    """Wyoming stillness: two-chord confession, then break of drums and fuzz guitar-ish shimmer."""
    dur = 100
    buf = Buf(dur)
    bpm = 80
    beat = 60.0 / bpm
    prog = [
        [(51, 0.9), (58, 0.7), (62, 0.5)],
        [(49, 0.9), (56, 0.7), (60, 0.5)],
    ] * 14
    bar = beat * 4
    for bi, chord in enumerate(prog):
        t0 = bi * bar
        if t0 >= dur:
            break
        for (note, vel) in chord:
            render_note(buf, int(t0 * SR), min(bar * 1.05, dur - t0), nf(note), 0.16 * vel, sine, a=0.25, r=0.9)
    # dusty kick/snare enters second third
    for bi in range(int((dur - 30) / (beat * 2)) + 1):
        t0 = 30 + bi * beat * 2
        if t0 < dur - 0.4:
            kick(buf, int(t0 * SR), vol=0.6)
            snare(buf, int((t0 + beat) * SR), vol=0.3)
    # fuzz shimmer high notes (Ghost Town-ish euphoria break at end)
    st0 = int((dur - 22) * SR)
    lead = [74, 76, 78, 81, 78, 76, 74, 76, 78, 81, 83, 81, 78, 76, 74, 72]
    for k, m in enumerate(lead):
        st = st0 + int(k * beat * 0.5 * SR)
        render_note(buf, st, beat * 1.0, nf(m), 0.13, saw, a=0.01, r=0.4, detune=0.004, lp=2600.0)
    vinyl(buf, vol=0.010, seed=91)
    fade_in(buf, 2.0)
    fade_out(buf, 4.0)
    return buf

def track_jik():
    """Sunday service: organ chords, gospel 6/8 feel, handclaps-ish snares, choir hum."""
    dur = 98
    buf = Buf(dur)
    bpm = 72
    beat = 60.0 / bpm
    # organ chords in 6/8-ish: bar = 6 eighth-beats
    prog = [
        [(53, 0.9), (57, 0.7), (60, 0.6), (64, 0.4)],
        [(48, 0.9), (52, 0.7), (55, 0.6), (60, 0.4)],
        [(55, 0.9), (59, 0.7), (62, 0.6), (66, 0.4)],
        [(53, 0.9), (57, 0.7), (60, 0.6), (62, 0.4)],
    ] * 9
    bar = beat * 3  # 6/8 compound feel
    for bi, chord in enumerate(prog):
        t0 = bi * bar
        if t0 >= dur:
            break
        for (note, vel) in chord:
            render_note(buf, int(t0 * SR), min(bar, dur - t0), nf(note), 0.14 * vel, sine, a=0.08, r=0.5)
            render_note(buf, int(t0 * SR), min(bar, dur - t0), nf(note) * 0.5, 0.10 * vel, tri, a=0.10, r=0.5)
    # choir hum (octave fifth drones)
    for i in range(len(buf)):
        t = i / SR
        if t > 6:
            v = (sine(i * nf(65) / SR) + 0.6 * sine(i * nf(72) / SR) + 0.4 * sine(i * nf(69) / SR)) * 0.045
            v *= 0.6 + 0.4 * sine(i / SR * 0.35)
            buf.d[i] += v
    # handclap-ish snare on 2 and 4 of compound bar
    for bi in range(int(dur / (bar * 2)) + 1):
        t0 = bi * bar * 2
        if t0 < dur - 0.3:
            snare(buf, int((t0 + bar) * SR), vol=0.30)
            snare(buf, int((t0 + bar * 1.5) * SR), vol=0.22)
    for bi in range(int(dur / (bar)) + 1):
        t0 = bi * bar
        if t0 < dur - 0.3:
            kick(buf, int(t0 * SR), vol=0.55)
    fade_in(buf, 2.0)
    fade_out(buf, 4.5)
    return buf

def track_donda():
    """Stadium lament: booming 808 behind, mournful choir strings, off-beat pulse."""
    dur = 108
    buf = Buf(dur)
    bpm = 85
    beat = 60.0 / bpm
    # mournful strings (minor add9 pad, high register)
    prog = [
        [(50, 0.9), (57, 0.7), (62, 0.5), (65, 0.4)],
        [(48, 0.9), (55, 0.7), (60, 0.5), (62, 0.4)],
        [(46, 0.9), (53, 0.7), (58, 0.5), (62, 0.4)],
        [(48, 0.9), (55, 0.7), (59, 0.5), (64, 0.4)],
    ] * 10
    bar = beat * 4
    for bi, chord in enumerate(prog):
        t0 = bi * bar
        if t0 >= dur:
            break
        for (note, vel) in chord:
            render_note(buf, int(t0 * SR), min(bar * 1.1, dur - t0), nf(note), 0.13 * vel, saw, a=0.5, r=1.0, detune=0.002, lp=1300.0)
    # stadium 808 boom on half notes
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if t0 < dur - 0.5:
            render_note(buf, int(t0 * SR), beat * 1.8, nf(24 + (bi % 4) // 2), 0.7, sine, a=0.003, r=0.9)
    # offbeat pulse hats
    for bi in range(int(dur / beat) + 1):
        t0 = bi * beat + beat * 0.5
        if t0 < dur - 0.1:
            hat(buf, int(t0 * SR), vol=0.10, dur=0.03)
    # distant kick
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if t0 < dur - 0.4:
            kick(buf, int(t0 * SR), vol=0.6, dur=0.4)
    fade_in(buf, 2.5)
    fade_out(buf, 5.0)
    return buf

def track_donda2():
    """Incomplete sketch: unfinished-stem feel, loop tighter, drum machine skeletal, gaps."""
    dur = 96
    buf = Buf(dur)
    bpm = 100
    beat = 60.0 / bpm
    # tight loop: only 2 bars material, repeated with gaps
    prog = [
        [(51, 0.9), (55, 0.7), (58, 0.5)],
        [(49, 0.9), (53, 0.7), (56, 0.5)],
    ] * 12
    bar = beat * 4
    for bi, chord in enumerate(prog):
        t0 = bi * bar
        if t0 >= dur:
            break
        # every other bar drops the pad for a "gapped" feel
        if bi % 4 == 3:
            continue
        for (note, vel) in chord:
            render_note(buf, int(t0 * SR), min(bar, dur - t0), nf(note), 0.14 * vel, saw, a=0.03, r=0.4, detune=0.001, lp=1500.0)
    # skeletal drum machine
    for bi in range(int(dur / (beat * 0.5)) + 1):
        t0 = bi * beat * 0.5
        if t0 < dur - 0.3 and bi % 4 == 0:
            kick(buf, int(t0 * SR), vol=0.75)
        if t0 < dur - 0.2 and bi % 4 == 2:
            snare(buf, int(t0 * SR), vol=0.35)
    # gaps: silence before drop at thirds
    for gapstart in (32, 64):
        a = int(gapstart * SR)
        b = int((gapstart + 1.5) * SR)
        for i in range(a, min(b, len(buf))):
            buf.d[i] *= 0.15
    fade_in(buf, 1.5)
    fade_out(buf, 3.0)
    return buf

def track_vultures1():
    """Carnival swagger: sinister bass hum, wheezing organ, hip-hop stomp."""
    dur = 100
    buf = Buf(dur)
    bpm = 92
    beat = 60.0 / bpm
    # sinister bass hum loop
    bassline = [31, 31, 34, 31, 29, 29, 31, 28]
    for rep in range(int(dur / (beat * 2)) + 1):
        for k, b in enumerate(bassline):
            st = rep * beat * 2 + k * beat * 0.5
            if st < dur - 0.2:
                render_note(buf, int(st * SR), beat * 0.8, nf(b), 0.55, sine, a=0.005, r=0.25)
                render_note(buf, int(st * SR), beat * 0.8, nf(b) * 1.008, 0.25, saw, a=0.005, r=0.25, lp=500.0)
    # wheezing organ stabs
    for rep in range(int(dur / (beat * 4)) + 1):
        t0 = rep * beat * 4
        for (m, off) in [(61, 0), (63, 1.5), (60, 2), (58, 3)]:
            st = t0 + off * beat
            if st < dur - 0.3:
                render_note(buf, int(st * SR), beat * 0.8, nf(m), 0.14, sine, a=0.02, r=0.3, fm_depth=0.5, fm_ratio=1.5)
    # hip-hop stomp
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if t0 < dur - 0.4:
            kick(buf, int(t0 * SR), vol=0.85)
            snare(buf, int((t0 + beat) * SR), vol=0.42)
    for bi in range(int(dur / (beat * 0.5)) + 1):
        t0 = bi * beat * 0.5
        if t0 < dur - 0.1:
            hat(buf, int(t0 * SR), vol=0.09, dur=0.03)
    fade_in(buf, 1.0)
    fade_out(buf, 3.0)
    return buf

def track_vultures2():
    """Hollowed sequel: thinner, more space, jazzy keys, slowed-melancholy tail."""
    dur = 102
    buf = Buf(dur)
    bpm = 82
    beat = 60.0 / bpm
    # jazzy electric keys: extended chords
    prog = [
        [(51, 0.8), (55, 0.6), (58, 0.5), (62, 0.35), (65, 0.25)],
        [(49, 0.8), (53, 0.6), (56, 0.5), (60, 0.35), (63, 0.25)],
        [(52, 0.80), (56, 0.6), (59, 0.5), (62, 0.35), (66, 0.25)],
        [(50, 0.8), (54, 0.6), (57, 0.90), (61, 0.35), (64, 0.25)],
    ] * 9
    bar = beat * 4
    for bi, chord in enumerate(prog):
        t0 = bi * bar
        if t0 >= dur:
            break
        for (note, vel) in chord:
            render_note(buf, int(t0 * SR), min(beat * 3.6, dur - t0), nf(note), 0.15 * vel, sine,
                        a=0.004, r=0.6, fm_depth=0.25, fm_ratio=1.004)
    # more space: drums half-time, sparse
    for bi in range(int(dur / (beat * 4)) + 1):
        t0 = bi * beat * 4
        if t0 < dur - 0.5:
            kick(buf, int(t0 * SR), vol=0.65)
            snare(buf, int((t0 + beat * 2) * SR), vol=0.32)
    for bi in range(int(dur / (beat * 0.5)) + 1):
        t0 = bi * beat * 0.5
        if t0 < dur - 0.1 and bi % 2 == 0:
            hat(buf, int(t0 * SR), vol=0.07, dur=0.04)
    # slowed melancholy tail: pitch droop in last 10s
    n = len(buf)
    for i in range(int(n * 0.1)):
        idx = n - int(n * 0.1) + i
        buf.d[idx] = buf.d[max(0, idx - int(0.02 * SR))]
    fade_in(buf, 1.5)
    fade_out(buf, 5.0)
    return buf

def track_bully_era():
    """BULLY-era mood: washed-out soul grief over industrial grief, music-box griefs."""
    dur = 104
    buf = Buf(dur)
    bpm = 88
    beat = 60.0 / bpm
    sample_pad(buf, [
        [(57, 0.9, 3.8), (60, 0.7, 3.8), (64, 0.6, 3.8)],
        [(53, 0.9, 3.8), (57, 0.7, 3.8), (60, 0.6, 3.8)],
    ] * 14, bpm, 4, 0.28, lp=850.0, seed=131)
    # music-box motif overlay
    motif = [(76, 0), (79, 0.5), (83, 1), (81, 1.5), (79, 2), (76, 2.5), (74, 3), (76, 3.5)]
    for rep in range(int(dur / (beat * 4)) + 1):
        t0 = rep * beat * 4
        for (m, k) in motif:
            st = t0 + k * beat
            if st < dur - 0.3:
                render_note(buf, int(st * SR), beat * 1.2, nf(m), 0.14, sine, a=0.001, r=0.5, fm_depth=0.5, fm_ratio=2.0)
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if t0 < dur - 0.4:
            kick(buf, int(t0 * SR), vol=0.7)
            snare(buf, int((t0 + beat) * SR), vol=0.30)
    fade_in(buf, 2.0)
    fade_out(buf, 4.0)
    return buf

TRACKS = {
    "college_dropout": track_college_dropout,
    "late_registration": track_late_registration,
    "graduation": track_graduation,
    "808s": track_808s,
    "mbdtf": track_mbdtf,
    "watch_the_throne": track_watch_the_throne,
    "yeezus": track_yeezus,
    "tlop": track_tlop,
    "ye": track_ye,
    "jik": track_jik,
    "donda": track_donda,
    "donda2": track_donda2,
    "vultures1": track_vultures1,
    "vultures2": track_vultures2,
    "bully_era": track_bully_era,
}

def main():
    only = os.environ.get("YE_TRACK")
    for name, fn in TRACKS.items():
        if only and name != only:
            continue
        path = os.path.join(SND, f"ye_discs_{name}.wav")
        if os.path.exists(path):
            print(f"skip {name} (exists)")
            convert_ogg(path)
            continue
        print(f"rendering {name} ...", flush=True)
        buf = fn()
        buf.write_wav(path)
        convert_ogg(path)
        print(f"  -> {path} ({len(buf)/SR:.1f}s)")

def convert_ogg(path):
    import subprocess
    ffmpeg = r"C:\Users\yaros\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"
    ogg = path.replace(".wav", ".ogg")
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", path, "-c:a", "libvorbis", "-qscale:a", "5", "-ar", "44100", "-ac", "1", ogg], check=True)

if __name__ == "__main__":
    main()
