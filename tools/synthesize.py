#!/usr/bin/env python3
"""Synthesize original instrumental tracks styled after the most popular
track of each Kanye West album — one disc per album.

All audio is generated from scratch (sine/saw/triangle/square oscillators,
noise drums, FM keys, simple envelopes). No samples, melodies, or audio from
any commercial recording are used. Track names identify the popular song
each instrumental evokes.
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

def riser(buf, start, dur, vol):
    n = int(dur * SR)
    prev = 0.0
    for i in range(n):
        t = i / SR
        noise = (random.random() * 2 - 1)
        v = noise - prev
        prev = noise
        env = (t / dur) ** 2
        buf.add(start + i, v * vol * env)

def vinyl(buf, vol=0.012, seed=7):
    rng = random.Random(seed)
    for i in range(len(buf)):
        buf.d[i] += (rng.random() * 2 - 1) * vol
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
# one generator per album's most popular track, original composition in the
# style of that track's production
# ---------------------------------------------------------------------------

def track_through_the_wire():
    """Sped-up soul chipmunk loop, high vocal-ish lead, dusty boom-bap."""
    dur = 98
    buf = Buf(dur)
    bpm = 100
    beat = 60.0 / bpm
    sample_pad(buf, [
        [(60, 0.9, 3.2), (64, 0.7, 3.2), (67, 0.6, 3.2), (72, 0.3, 1.6)],
        [(56, 0.9, 3.2), (60, 0.7, 3.2), (63, 0.6, 3.2), (68, 0.3, 1.6)],
        [(58, 0.9, 3.2), (62, 0.7, 3.2), (65, 0.6, 3.2), (70, 0.3, 1.6)],
        [(53, 0.9, 3.2), (57, 0.7, 3.2), (60, 0.6, 3.2), (65, 0.3, 1.6)],
    ] * 10, bpm, 4, 0.28, lp=1400.0, seed=23)
    # chipmunk vocal-ish lead: triangle + formant AM + vibrato, high register
    lead = [72, 74, 76, 74, 72, 69, 71, 72, 76, 74, 72, 69, 67, 69, 71, 72]
    for rep in range(int(dur / (beat * 4)) + 1):
        t0 = rep * beat * 4
        if t0 < 8:
            continue
        for k, m in enumerate(lead):
            st = t0 + k * beat * 0.5
            if st < dur - 0.3:
                n = int(beat * 0.55 * SR)
                f = nf(m)
                for i in range(n):
                    e = env_ar(i, n, 0.01 * SR, 0.2 * SR)
                    vib = 0.005 * sine(i / SR * 6.0)
                    formant = 0.55 + 0.45 * sine(i / SR * 4.0)
                    v = tri((i * f * (1 + vib)) / SR) * formant
                    buf.add(int(st * SR) + i, v * 0.13 * e)
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if t0 < dur - 0.4:
            kick(buf, int(t0 * SR), vol=0.72)
            snare(buf, int((t0 + beat) * SR), vol=0.44)
            hat(buf, int((t0 + beat * 1.5) * SR), vol=0.11)
    fade_in(buf, 0.8)
    fade_out(buf, 3.0)
    return buf

def track_gold_digger():
    """Sped-up gospel-soul piano stabs on the offbeat, handclap bounce."""
    dur = 100
    buf = Buf(dur)
    bpm = 102
    beat = 60.0 / bpm
    prog = [
        [(48, 0.9), (52, 0.7), (55, 0.6), (58, 0.4)],  # C7
        [(41, 0.9), (45, 0.7), (48, 0.6), (51, 0.4)],  # F7
    ] * 25
    for bi, chord in enumerate(prog):
        t0 = bi * beat * 2
        if t0 >= dur:
            break
        st = t0 + beat * 0.5
        for (note, vel) in chord:
            render_note(buf, int(st * SR), 0.3, nf(note) * 2, 0.16 * vel, saw, a=0.002, r=0.15, lp=2200.0, detune=0.001)
            render_note(buf, int(st * SR), 0.3, nf(note + 12) * 2, 0.05 * vel, sine, a=0.002, r=0.2)
        root = chord[0][0] - 24
        for off in (0, 1.0, 2.5):
            b_st = t0 + off * beat
            if b_st < dur - 0.2:
                render_note(buf, int(b_st * SR), beat * 0.4, nf(root), 0.5, sine, a=0.005, r=0.15)
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if t0 < dur - 0.4:
            kick(buf, int(t0 * SR), vol=0.75)
            snare(buf, int((t0 + beat) * SR), vol=0.5)
    for bi in range(int(dur / (beat * 0.25)) + 1):
        t0 = bi * beat * 0.25
        if t0 < dur - 0.1:
            hat(buf, int(t0 * SR), vol=0.08 if bi % 2 else 0.12, dur=0.03)
    vinyl(buf, vol=0.008, seed=41)
    fade_in(buf, 0.8)
    fade_out(buf, 3.0)
    return buf

def track_stronger():
    """Vocoder-ish electro riff, 4-on-the-floor, filter build and arena drop."""
    dur = 104
    buf = Buf(dur)
    bpm = 104
    beat = 60.0 / bpm
    riff = [45, 45, 45, 48, 47, 45, 43, 45, 45, 45, 50, 48, 47, 45, 43, 40]

    def riff_pass(t0, vol, lp_val):
        for k, m in enumerate(riff):
            st = t0 + k * beat * 0.5
            if st < dur - 0.2:
                n = int(beat * 0.45 * SR)
                f = nf(m)
                for i in range(n):
                    e = env_ar(i, n, 0.004 * SR, 0.10 * SR)
                    formant = 0.6 + 0.4 * sine(i / SR * 5.0)
                    v = square(i * f / SR) * formant
                    buf.add(int(st * SR) + i, v * vol * e)
                render_note(buf, int(st * SR), beat * 0.45, nf(m), 0.55 * vol, saw, a=0.003, r=0.10, detune=0.002, lp=lp_val)

    for rep in range(13):
        t0 = rep * beat * 4
        if t0 >= dur:
            break
        if t0 < 16:
            riff_pass(t0, 0.10, 700.0)
        elif t0 < 24:
            riff_pass(t0, 0.16, 1400.0)
        else:
            riff_pass(t0, 0.24, 2800.0)
    # sub octaves after the drop
    for bi in range(int((dur - 24) / (beat * 0.5)) + 1):
        t0 = 24 + bi * beat * 0.5
        if t0 < dur - 0.2:
            render_note(buf, int(t0 * SR), 0.2, nf(33), 0.5, sine, a=0.004, r=0.08)
    for bi in range(int(dur / beat) + 1):
        t0 = bi * beat
        if t0 < dur - 0.3:
            kick(buf, int(t0 * SR), vol=0.9)
            hat(buf, int((t0 + beat * 0.5) * SR), vol=0.13, dur=0.04)
        if bi % 4 == 2 and t0 < dur - 0.3:
            snare(buf, int(t0 * SR), vol=0.5)
    riser(buf, int(20 * SR), 4.0, 0.10)
    crash(buf, int(24 * SR), vol=0.45)
    # breakdown strip
    a, b = int(68 * SR), int(76 * SR)
    for i in range(a, min(b, len(buf))):
        buf.d[i] *= 0.35
    fade_in(buf, 0.8)
    fade_out(buf, 2.5)
    return buf

def track_heartless():
    """Icy 16th-note minor arp, huge 808, frozen minimalism."""
    dur = 100
    buf = Buf(dur)
    bpm = 82
    beat = 60.0 / bpm
    prog = [
        [(45, 0.9), (48, 0.6), (52, 0.5)],   # A minor
        [(41, 0.9), (45, 0.6), (48, 0.5)],   # F minor
    ] * 18
    bar = beat * 4
    for bi, chord in enumerate(prog):
        t0 = bi * bar
        if t0 >= dur:
            break
        root, third, fifth = chord[0][0], chord[1][0], chord[2][0]
        notes = [root, fifth, root + 12, third + 12, root + 12, fifth, third + 12, root + 12]
        for k in range(16):
            st = t0 + k * beat * 0.25
            m = notes[k % len(notes)]
            if st < dur - 0.1:
                render_note(buf, int(st * SR), 0.13, nf(m), 0.13, sine, a=0.002, r=0.05, fm_depth=0.25, fm_ratio=2.0)
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        root = prog[bi % 2][0][0] - 24
        for off in (0, 1.5):
            st = t0 + off * beat
            if st < dur - 0.5:
                render_note(buf, int(st * SR), beat * 1.4, nf(root), 0.65, sine, a=0.004, r=0.7)
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if t0 < dur - 0.3:
            snare(buf, int((t0 + beat) * SR), vol=0.40)
            hat(buf, int((t0 + beat * 0.75) * SR), vol=0.07, dur=0.03)
    for rep in range(4):
        t0 = 52 + rep * 12
        if t0 < dur - 3:
            render_note(buf, int(t0 * SR), 1.8, nf(76), 0.09, sine, a=0.01, r=1.2, fm_depth=0.4, fm_ratio=3.01)
    fade_in(buf, 1.5)
    fade_out(buf, 4.0)
    return buf

def track_runaway():
    """Sparse dissonant piano cluster, cavernous space, single-note motif."""
    dur = 108
    buf = Buf(dur)
    bpm = 86
    beat = 60.0 / bpm
    prog = [
        [(48, 0.9, 3.6), (55, 0.7, 3.6), (58, 0.5, 3.6)],
        [(46, 0.9, 3.6), (53, 0.7, 3.6), (56, 0.5, 3.6)],
    ] * 12
    for bi, chord in enumerate(prog):
        t0 = bi * beat * 4
        if t0 >= dur:
            break
        for note, vel, hold in chord:
            render_note(buf, int(t0 * SR), hold, nf(note) * 2, 0.10 * vel, tri, a=0.006, r=0.9, detune=0.0008, lp=1600.0)
    motif = [60, 60, 63, 58, 60, 56, 58, 55]
    for rep in range(int(dur / (beat * 4)) + 1):
        t0 = rep * beat * 4
        if t0 < 4 or t0 >= dur - 1:
            continue
        for k, m in enumerate(motif):
            st = t0 + k * beat * 0.5
            if st < dur - 0.3:
                render_note(buf, int(st * SR), beat * 0.5, nf(m) * 2, 0.16, tri, a=0.004, r=0.35, lp=2400.0)
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if 8 < t0 < dur - 1.0:
            kick(buf, int(t0 * SR), vol=0.80)
            snare(buf, int((t0 + beat) * SR), vol=0.30)
    # deep swelling drone under the outro
    for rep in range(int(dur / 24)):
        t0 = rep * 24
        render_note(buf, int((t0 + 16) * SR), 6.0, nf(43), 0.30, sine, a=0.05, r=2.0)
    vinyl(buf, vol=0.010, seed=77)
    fade_in(buf, 2.0)
    fade_out(buf, 5.0)
    return buf

def track_black_skinhead():
    """Distorted industrial stabs, pounding four-on-the-floor, aggressive."""
    dur = 92
    buf = Buf(dur)
    bpm = 155
    beat = 60.0 / bpm
    riff = [38, 38, 45, 38, 41, 38, 44, 43]
    for rep in range(int(dur / (beat * 4)) + 1):
        t0 = rep * beat * 4
        if t0 < dur - 0.5:
            for k, m in enumerate(riff):
                st = t0 + k * beat * 0.5
                if st < dur - 0.1:
                    render_note(buf, int(st * SR), beat * 0.42, nf(m), 0.30, square, a=0.002, r=0.06, detune=0.004, lp=3000.0)
                    render_note(buf, int(st * SR), beat * 0.42, nf(m - 12), 0.42, saw, a=0.002, r=0.08, detune=0.006, lp=900.0)
    for bi in range(int(dur / beat) + 1):
        t0 = bi * beat
        if 4 < t0 < dur - 0.4:
            kick(buf, int(t0 * SR), vol=1.0)
            if bi % 4 == 2:
                crash(buf, int(t0 * SR), vol=0.30)
    for bi in range(int(dur / (beat * 0.5)) + 1):
        t0 = bi * beat * 0.5
        if 4 < t0 < dur - 0.2:
            hat(buf, int(t0 * SR), vol=0.12, dur=0.03)
    riser(buf, int((dur - 12) * SR), 6.0, 0.08)
    fade_in(buf, 1.0)
    fade_out(buf, 2.0)
    return buf

def track_famous():
    """Chopped soul stab loop, heavy trap 808 bounce, stuttering hats."""
    dur = 96
    buf = Buf(dur)
    bpm = 132
    beat = 60.0 / bpm
    stab = [(52, 0.8), (55, 0.6), (59, 0.5), (64, 0.3)]
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if t0 >= dur - 0.2:
            break
        for k in range(4):
            st = t0 + k * beat * 0.25
            if st < dur - 0.1:
                for (note, vel) in stab:
                    render_note(buf, int(st * SR), 0.16, nf(note), 0.12 * vel, saw, a=0.002, r=0.18, detune=0.002, lp=1800.0)
        root = 40 - 12
        render_note(buf, int(t0 * SR), beat * 0.9, nf(root), 0.62, sine, a=0.004, r=0.5)
        render_note(buf, int((t0 + beat) * SR), beat * 0.9, nf(root + 3), 0.62, sine, a=0.004, r=0.5)
    for bi in range(int(dur / (beat * 0.5)) + 1):
        t0 = bi * beat * 0.5
        if 2 < t0 < dur - 0.3:
            hat(buf, int(t0 * SR), vol=0.10 if bi % 2 else 0.16, dur=0.03)
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if 2 < t0 < dur - 0.4:
            kick(buf, int(t0 * SR), vol=0.85)
            snare(buf, int((t0 + beat) * SR), vol=0.35)
    vinyl(buf, vol=0.009, seed=88)
    fade_in(buf, 0.8)
    fade_out(buf, 3.0)
    return buf

def track_ghost_town():
    """Hazy psychedelic groove, washed guitar-like leads, luminous outro."""
    dur = 100
    buf = Buf(dur)
    bpm = 76
    beat = 60.0 / bpm
    prog = [
        [(45, 0.8, 3.4), (52, 0.6, 3.4), (57, 0.5, 3.4)],
        [(43, 0.8, 3.4), (50, 0.6, 3.4), (55, 0.5, 3.4)],
    ] * 10
    sample_pad(buf, prog, bpm, 4, 0.20, wave_fn=saw, lp=900.0, seed=55)
    lead = [69, 72, 71, 69, 67, 64, 67, 69, 72, 74, 72, 69, 67, 64, 62, 64]
    for rep in range(int(dur / (beat * 4)) + 1):
        t0 = rep * beat * 4
        if t0 < 12 or t0 >= dur - 4:
            continue
        for k, m in enumerate(lead):
            st = t0 + k * beat * 0.5
            if st < dur - 0.5:
                n = int(beat * 0.6 * SR)
                f = nf(m)
                for i in range(n):
                    e = env_ar(i, n, 0.02 * SR, 0.25 * SR)
                    vib = 0.006 * sine(i / SR * 5.5)
                    v = saw((i * f * (1 + vib)) / SR)
                    buf.add(int(st * SR) + i, v * 0.10 * e)
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if 8 < t0 < dur - 3:
            kick(buf, int(t0 * SR), vol=0.70)
            snare(buf, int((t0 + beat) * SR), vol=0.38)
            hat(buf, int((t0 + beat * 0.75) * SR), vol=0.08)
    fade_in(buf, 1.2)
    fade_out(buf, 4.0)
    return buf

def track_nias_in_paris():
    """Operatic synth-brass fanfare hits, gilded menace, festival bounce."""
    dur = 96
    buf = Buf(dur)
    bpm = 138
    beat = 60.0 / bpm
    prog = [
        [(33, 0.9), (45, 0.6), (52, 0.7), (57, 0.5), (60, 0.4)],   # Am orchestral
        [(31, 0.9), (43, 0.6), (50, 0.7), (55, 0.5), (58, 0.4)],   # Gm
    ] * 18
    for bi, chord in enumerate(prog):
        t0 = bi * beat * 2
        if t0 >= dur - 0.2:
            break
        # brass stab: detuned saws + square, short and punchy
        for m, vel in [(c[0] + 12, c[1]) for c in chord[:3]]:
            render_note(buf, int(t0 * SR), 0.22, nf(m), 0.14 * vel, saw, a=0.003, r=0.16, detune=0.003, lp=1900.0)
            render_note(buf, int(t0 * SR), 0.22, nf(m + 7), 0.06 * vel, square, a=0.003, r=0.14, lp=1500.0)
        # sub hit on the one
        root = chord[0][0] - 24
        render_note(buf, int(t0 * SR), beat * 0.8, nf(root), 0.62, sine, a=0.004, r=0.4)
    for bi in range(int(dur / (beat * 0.5)) + 1):
        t0 = bi * beat * 0.5
        if 2 < t0 < dur - 0.3:
            hat(buf, int(t0 * SR), vol=0.09 if bi % 2 else 0.14, dur=0.03)
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if 4 < t0 < dur - 0.4:
            kick(buf, int(t0 * SR), vol=0.95)
            snare(buf, int((t0 + beat) * SR), vol=0.42)
    # rising opera "ah" pad into the drop
    for rep in range(3):
        t0 = 14 + rep * 28
        if t0 < dur - 8:
            render_note(buf, int(t0 * SR), 6.0, nf(69), 0.08, saw, a=1.2, r=1.5, detune=0.004, lp=700.0)
            render_note(buf, int(t0 * SR), 6.0, nf(72), 0.07, saw, a=1.2, r=1.5, detune=0.004, lp=700.0)
    fade_in(buf, 0.6)
    fade_out(buf, 2.5)
    return buf

def track_follow_god():
    """Gospel drawbar organ loop, handclaps, choir 'ahs', Sunday-morning drive."""
    dur = 94
    buf = Buf(dur)
    bpm = 88
    beat = 60.0 / bpm
    prog = [
        [(48, 0.9, 3.4), (55, 0.7, 3.4), (60, 0.6, 3.4), (64, 0.4, 3.4)],  # Cmaj
        [(45, 0.9, 3.4), (52, 0.7, 3.4), (57, 0.6, 3.4), (60, 0.4, 3.4)],  # Am
        [(41, 0.9, 3.4), (48, 0.7, 3.4), (53, 0.6, 3.4), (57, 0.4, 3.4)],  # F
        [(43, 0.9, 3.4), (50, 0.7, 3.4), (55, 0.6, 3.4), (59, 0.4, 3.4)],  # G
    ] * 6

    def organ(buf, start, dur_s, freq, vol):
        # drawbar-ish: fundamental + octaves + fifth, sines
        for mult, v in ((1.0, 1.0), (2.0, 0.45), (3.0, 0.22), (4.0, 0.28), (6.0, 0.10)):
            render_note(buf, start, dur_s, freq * mult, vol * v, sine, a=0.01, r=0.12, detune=0.0006)
        render_note(buf, start, dur_s, freq, vol * 0.25, tri, a=0.01, r=0.10, detune=0.002)

    for bi, chord in enumerate(prog):
        t0 = bi * beat * 4
        if t0 >= dur - 0.5:
            break
        for note, vel, hold in chord:
            organ(buf, int(t0 * SR), min(hold, dur - t0), nf(note) * 2, 0.045 * vel)
    # choir aahs
    for bi in range(6):
        t0 = 8 + bi * 14
        if t0 < dur - 10:
            for m in (72, 76, 79):
                n = int(9.0 * SR)
                f = nf(m)
                for i in range(n):
                    e = env_ar(i, n, 1.8 * SR, 2.5 * SR)
                    vib = 0.004 * sine(i / SR * 5.0)
                    v = (saw((i * f * (1 + vib)) / SR) * 0.6 + sine((i * f * (1 + vib)) / SR) * 0.4)
                    buf.add(int(t0 * SR) + i, v * 0.05 * e)
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if 2 < t0 < dur - 0.5:
            kick(buf, int(t0 * SR), vol=0.72)
            snare(buf, int((t0 + beat) * SR), vol=0.30)
            # handclaps layered on the snare
            for k in range(3):
                hat(buf, int((t0 + beat) * SR) + int(0.001 * k * SR), vol=0.14, dur=0.025)
    vinyl(buf, vol=0.007, seed=99)
    fade_in(buf, 0.8)
    fade_out(buf, 3.0)
    return buf

def track_true_love():
    """Melancholic lo-fi piano loop, gaps and dropouts like an unfinished stem."""
    dur = 82
    buf = Buf(dur)
    bpm = 76
    beat = 60.0 / bpm
    prog = [
        [(53, 0.9, 3.2), (57, 0.6, 3.2), (60, 0.7, 3.2)],
        [(51, 0.9, 3.2), (55, 0.6, 3.2), (58, 0.7, 3.2)],
    ] * 11
    for bi, chord in enumerate(prog):
        t0 = bi * beat * 4
        if t0 >= dur - 0.5:
            break
        for note, vel, hold in chord:
            render_note(buf, int(t0 * SR), hold, nf(note) * 2, 0.11 * vel, tri, a=0.004, r=0.6, detune=0.0009, lp=1900.0)
        root = chord[0][0] - 24
        render_note(buf, int(t0 * SR), beat * 3.2, nf(root), 0.42, sine, a=0.01, r=0.8)
    # music-box counter-melody, half-buried
    motif = [77, 76, 72, 74, 72, 69, 72, 76]
    for rep in range(int(dur / (beat * 4)) + 1):
        t0 = rep * beat * 4
        if t0 < 6 or t0 >= dur - 2:
            continue
        for k, m in enumerate(motif):
            st = t0 + k * beat * 0.5
            if st < dur - 0.3:
                render_note(buf, int(st * SR), 0.4, nf(m), 0.07, sine, a=0.002, r=0.35, fm_depth=0.18, fm_ratio=2.0)
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if 4 < t0 < dur - 1.5:
            kick(buf, int(t0 * SR), vol=0.55)
            hat(buf, int((t0 + beat) * SR), vol=0.05, dur=0.025)
    # dropout gaps — the unfinished-stem feel
    for (g0, g1) in [(20.0, 21.4), (47.5, 48.8)]:
        a, b = int(g0 * SR), int(g1 * SR)
        for i in range(a, min(b, len(buf))):
            buf.d[i] *= 0.12
    vinyl(buf, vol=0.014, seed=31)
    fade_in(buf, 1.0)
    fade_out(buf, 3.5)
    return buf

def track_carnival():
    """Haunted funfair: detuned hoover rave riff, booming 808s, hype stabs."""
    dur = 96
    buf = Buf(dur)
    bpm = 146
    beat = 60.0 / bpm
    riff = [38, 38, 38, 41, 38, 38, 44, 43, 38, 38, 38, 41, 46, 44, 43, 41]
    for rep in range(int(dur / (beat * 4)) + 1):
        t0 = rep * beat * 4
        if t0 >= dur - 0.2:
            break
        for k, m in enumerate(riff):
            st = t0 + k * beat * 0.25
            if st < dur - 0.1:
                # hoover: detuned saws, pitch-bend-ish FM, bandpass-ish LP
                render_note(buf, int(st * SR), 0.20, nf(m), 0.16, saw, a=0.002, r=0.12, detune=0.007, lp=2200.0, fm_depth=0.5, fm_ratio=0.5)
                render_note(buf, int(st * SR), 0.20, nf(m + 12) * 1.004, 0.07, square, a=0.002, r=0.10, detune=0.005, lp=1800.0)
        root = riff[0] - 24
        if rep % 2 == 0:
            render_note(buf, int(t0 * SR), beat * 1.2, nf(root), 0.60, sine, a=0.004, r=0.5)
            render_note(buf, int((t0 + beat * 2) * SR), beat * 1.2, nf(root + 5), 0.60, sine, a=0.004, r=0.5)
    for bi in range(int(dur / (beat * 0.5)) + 1):
        t0 = bi * beat * 0.5
        if 2 < t0 < dur - 0.3:
            hat(buf, int(t0 * SR), vol=0.10 if bi % 2 else 0.15, dur=0.03)
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if 2 < t0 < dur - 0.4:
            kick(buf, int(t0 * SR), vol=0.95)
            snare(buf, int((t0 + beat) * SR), vol=0.40)
    # crowd-noise hype swell (filtered noise, no voices)
    riser(buf, int(30 * SR), 4.0, 0.06)
    crash(buf, int(34 * SR), vol=0.28)
    fade_in(buf, 0.8)
    fade_out(buf, 2.5)
    return buf

def track_five_30():
    """Slowed hazy soul loop, pitched-down melancholy, distant drums."""
    dur = 88
    buf = Buf(dur)
    bpm = 66
    beat = 60.0 / bpm
    sample_pad(buf, [
        [(48, 0.9, 5.8), (52, 0.6, 5.8), (55, 0.7, 5.8), (63, 0.3, 5.8)],
        [(46, 0.9, 5.8), (50, 0.6, 5.8), (53, 0.7, 5.8), (61, 0.3, 5.8)],
    ] * 9, bpm, 4, 0.26, wave_fn=tri, lp=800.0, seed=63)
    # pitched-down "vocal" shadow: low triangle phrase
    lead = [60, 58, 55, 53, 55, 58, 60, 62]
    for rep in range(int(dur / (beat * 4)) + 1):
        t0 = rep * beat * 4
        if t0 < 10 or t0 >= dur - 6:
            continue
        for k, m in enumerate(lead):
            st = t0 + k * beat * 0.5
            if st < dur - 0.5:
                render_note(buf, int(st * SR), beat * 0.7, nf(m - 12), 0.10, tri, a=0.02, r=0.4, lp=900.0, fm_depth=0.15, fm_ratio=1.0)
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if 8 < t0 < dur - 4:
            kick(buf, int(t0 * SR), vol=0.60)
            snare(buf, int((t0 + beat) * SR), vol=0.26)
    fade_in(buf, 1.5)
    fade_out(buf, 4.0)
    return buf

def track_bully():
    """Washed-out soul grief: pitched vocal-ish melody, music box, heavy heart."""
    dur = 92
    buf = Buf(dur)
    bpm = 72
    beat = 60.0 / bpm
    sample_pad(buf, [
        [(49, 0.9, 5.4), (52, 0.6, 5.4), (56, 0.7, 5.4)],
        [(47, 0.9, 5.4), (50, 0.6, 5.4), (54, 0.7, 5.4)],
    ] * 10, bpm, 4, 0.24, wave_fn=saw, lp=750.0, seed=19)
    # pitched-up soul "vocal" phrase: triangle with formant AM + vibrato
    lead = [76, 74, 72, 69, 72, 74, 76, 79, 76, 74, 72, 69, 67, 69, 72, 74]
    for rep in range(int(dur / (beat * 4)) + 1):
        t0 = rep * beat * 4
        if t0 < 8 or t0 >= dur - 5:
            continue
        for k, m in enumerate(lead):
            st = t0 + k * beat * 0.5
            if st < dur - 0.5:
                n = int(beat * 0.6 * SR)
                f = nf(m)
                for i in range(n):
                    e = env_ar(i, n, 0.015 * SR, 0.22 * SR)
                    vib = 0.006 * sine(i / SR * 5.5)
                    formant = 0.55 + 0.45 * sine(i / SR * 3.5)
                    v = tri((i * f * (1 + vib)) / SR) * formant
                    buf.add(int(st * SR) + i, v * 0.12 * e)
    # music-box bell doubling, sparse
    for rep in range(int(dur / (beat * 4)) + 1):
        t0 = rep * beat * 4 + beat * 2
        if 12 < t0 < dur - 4:
            for m in (88, 85):
                render_note(buf, int(t0 * SR), 0.6, nf(m), 0.05, sine, a=0.002, r=0.5, fm_depth=0.3, fm_ratio=3.5)
    for bi in range(int(dur / (beat * 2)) + 1):
        t0 = bi * beat * 2
        if 6 < t0 < dur - 3:
            kick(buf, int(t0 * SR), vol=0.66)
            snare(buf, int((t0 + beat) * SR), vol=0.28)
    vinyl(buf, vol=0.012, seed=13)
    fade_in(buf, 1.2)
    fade_out(buf, 4.0)
    return buf

def track_hurricane():
    """Pulsing minor synth arps, bouncy 808, anthemic release."""
    dur = 100
    buf = Buf(dur)
    bpm = 118
    beat = 60.0 / bpm
    prog = [
        [(41, 0.9), (48, 0.6), (53, 0.5), (56, 0.4)],
        [(39, 0.9), (46, 0.6), (51, 0.5), (54, 0.4)],
    ] * 25
    for bi, chord in enumerate(prog):
        t0 = bi * beat
        if t0 >= dur - 0.1:
            break
        notes = [c[0] + 12 for c in chord]
        for k in range(2):
            st = t0 + k * beat * 0.5
            for m in notes:
                render_note(buf, int(st * SR), 0.24, nf(m), 0.09, square, a=0.002, r=0.10, lp=2600.0, detune=0.001)
        root = chord[0][0] - 24
        if bi % 2 == 0:
            render_note(buf, int(t0 * SR), beat * 1.6, nf(root), 0.60, sine, a=0.004, r=0.6)
    for bi in range(int(dur / beat) + 1):
        t0 = bi * beat
        if t0 < dur - 0.3:
            kick(buf, int(t0 * SR), vol=0.88)
            if bi % 4 == 2:
                snare(buf, int(t0 * SR), vol=0.42)
    for bi in range(int(dur / (beat * 0.5)) + 1):
        t0 = bi * beat * 0.5
        if t0 < dur - 0.2:
            hat(buf, int(t0 * SR), vol=0.09 if bi % 2 else 0.13, dur=0.03)
    fade_in(buf, 1.0)
    fade_out(buf, 3.0)
    return buf

TRACKS = [
    ("through_the_wire", track_through_the_wire),
    ("gold_digger", track_gold_digger),
    ("stronger", track_stronger),
    ("heartless", track_heartless),
    ("runaway", track_runaway),
    ("nias_in_paris", track_nias_in_paris),
    ("black_skinhead", track_black_skinhead),
    ("famous", track_famous),
    ("ghost_town", track_ghost_town),
    ("follow_god", track_follow_god),
    ("hurricane", track_hurricane),
    ("true_love", track_true_love),
    ("carnival", track_carnival),
    ("five_30", track_five_30),
    ("bully", track_bully),
]

FFMPEG = r"C:\Users\yaros\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe"

def convert_ogg(name):
    import subprocess
    wav = os.path.join(SND, name + ".wav")
    ogg = os.path.join(SND, name + ".ogg")
    if os.path.exists(ogg):
        os.remove(ogg)
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", wav,
                    "-c:a", "libvorbis", "-qscale:a", "5", "-ar", "44100", "-ac", "1", ogg],
                   check=True)
    return os.path.exists(ogg) and os.path.getsize(ogg) > 1000

def main():
    for name, fn in TRACKS:
        path = os.path.join(SND, name + ".wav")
        print("rendering", path)
        fn().write_wav(path)
    print("converting to ogg")
    ok = 0
    for name, _ in TRACKS:
        if convert_ogg(name):
            ok += 1
        else:
            print("FAILED to convert", name)
    print("done: %d/%d tracks converted to ogg" % (ok, len(TRACKS)))

if __name__ == "__main__":
    main()
