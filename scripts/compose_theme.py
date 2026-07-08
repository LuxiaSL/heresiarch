"""Heresiarch theme — "Slime Domain" — procedural chiptune generator.

Composes the looping title/exploration theme and writes it as a 16-bit
mono WAV asset. Deterministic: same script, same bytes (modulo float
rounding). Players never need this — the generated asset is committed;
this script exists so the music is source code like everything else.

    uv run --with numpy python scripts/compose_theme.py

Musical design:
  - A miyako-bushi (in) scale: A Bb D E F — the b2 is the shrine color.
  - Descending lament bass (A G F E) at 116 BPM on a tresillo (3+3+2):
    a funeral progression that swaggers. Grinning while you bleed out.
  - B section lifts through F G to a Neapolitan Bb major gleam → E,
    the "degenerate build comes online" chord, then reprise.
  - NES voicing: 25%-duty pulse lead (+ vibrato), 50%-duty echo ghost
    one eighth behind, triangle bass, noise-channel drums.
  - Anti-aliased: pulse/triangle are band-limited Fourier sums.
  - Seamless: note tails wrap modulo loop length; the seam is silent.
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

SR = 44100
BPM = 116.0
BEAT = 60.0 / BPM
S16 = BEAT / 4.0          # one sixteenth note, seconds
BARS = 16
LOOP_SAMPLES = round(BARS * 16 * S16 * SR)

OUT_PATH = Path(__file__).resolve().parents[1] / (
    "src/heresiarch/tui/assets/heresiarch_theme.wav"
)

# ---------------------------------------------------------------------------
# Pitch table (equal temperament)
# ---------------------------------------------------------------------------

def hz(name: str) -> float:
    """Note name (e.g. 'A4', 'Bb3') → frequency."""
    semis = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2}
    letter, rest = name[0], name[1:]
    offset = semis[letter]
    if rest.startswith("b"):
        offset -= 1
        rest = rest[1:]
    elif rest.startswith("#"):
        offset += 1
        rest = rest[1:]
    octave = int(rest)
    return 440.0 * 2 ** (offset / 12 + (octave - 4))


# ---------------------------------------------------------------------------
# Band-limited oscillators
# ---------------------------------------------------------------------------

def pulse(freq: float, n: int, duty: float, phase_t: float = 0.0) -> np.ndarray:
    """Band-limited pulse wave via Fourier series (harmonics < 12 kHz)."""
    t = (np.arange(n) / SR) + phase_t
    out = np.zeros(n)
    k = 1
    while k * freq < 12000 and k <= 40:
        amp = (2.0 / (k * np.pi)) * np.sin(k * np.pi * duty)
        out += amp * np.sin(2 * np.pi * k * freq * t)
        k += 1
    return out


def pulse_vibrato(
    freq: float, n: int, duty: float,
    vib_hz: float = 5.5, vib_depth: float = 0.004, vib_onset: float = 0.4,
) -> np.ndarray:
    """Pulse with delayed vibrato (phase-integrated so pitch bends smoothly)."""
    t = np.arange(n) / SR
    onset = vib_onset * (n / SR)
    ramp = np.clip((t - onset) / max(1e-9, onset), 0.0, 1.0)
    inst = freq * (1.0 + vib_depth * ramp * np.sin(2 * np.pi * vib_hz * t))
    phase = 2 * np.pi * np.cumsum(inst) / SR
    out = np.zeros(n)
    k = 1
    while k * freq < 12000 and k <= 40:
        amp = (2.0 / (k * np.pi)) * np.sin(k * np.pi * duty)
        out += amp * np.sin(k * phase)
        k += 1
    return out


def triangle(freq: float, n: int) -> np.ndarray:
    """Band-limited triangle (harmonics < 8 kHz)."""
    t = np.arange(n) / SR
    out = np.zeros(n)
    k = 1
    sign = 1.0
    while k * freq < 8000 and k <= 21:
        out += sign * np.sin(2 * np.pi * k * freq * t) / (k * k)
        sign = -sign
        k += 2
    return out * (8 / np.pi**2)


def envelope(n: int, attack_s: float = 0.004, release_s: float = 0.012) -> np.ndarray:
    """Flat sustain with cosine attack/release — closes every note (no clicks)."""
    env = np.ones(n)
    a = min(n // 2, int(attack_s * SR))
    r = min(n // 2, int(release_s * SR))
    if a > 0:
        env[:a] = 0.5 - 0.5 * np.cos(np.pi * np.arange(a) / a)
    if r > 0:
        env[-r:] = 0.5 + 0.5 * np.cos(np.pi * np.arange(r) / r)
    return env


# ---------------------------------------------------------------------------
# Drums (noise channel)
# ---------------------------------------------------------------------------

_rng = np.random.default_rng(0xE1DE)  # fixed seed: deterministic asset


def drum_kick() -> np.ndarray:
    n = int(0.12 * SR)
    t = np.arange(n) / SR
    freq = 45 + 65 * np.exp(-t / 0.03)          # 110 → 45 Hz sweep
    phase = 2 * np.pi * np.cumsum(freq) / SR
    return np.sin(phase) * np.exp(-t / 0.045)


def drum_snare() -> np.ndarray:
    n = int(0.10 * SR)
    t = np.arange(n) / SR
    noise = _rng.uniform(-1, 1, n)
    noise = np.diff(noise, prepend=0.0)          # crude highpass: crack
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.03)
    return (0.7 * noise * np.exp(-t / 0.035) + 0.5 * body)


def drum_hat() -> np.ndarray:
    n = int(0.025 * SR)
    t = np.arange(n) / SR
    noise = np.diff(_rng.uniform(-1, 1, n), prepend=0.0)
    return noise * np.exp(-t / 0.008)


# ---------------------------------------------------------------------------
# Score
# ---------------------------------------------------------------------------

# Lead: (note-or-None, length in 16ths) per bar; each bar must sum to 16.
LEAD_A = [
    [("A4", 3), ("Bb4", 1), ("A4", 2), ("F4", 2), ("E4", 4), (None, 4)],
    [("D4", 2), ("E4", 2), ("F4", 2), ("E4", 2), ("D4", 2), ("Bb4", 2), ("A4", 4)],
    [(None, 2), ("F4", 2), ("E4", 2), ("D4", 2), ("F4", 2), ("A4", 2), ("D5", 4)],
    [("E5", 3), ("F5", 1), ("E5", 2), ("D5", 2), ("Bb4", 2), ("A4", 2), (None, 4)],
]
LEAD_A2 = [
    [("A4", 3), ("Bb4", 1), ("A4", 2), ("F4", 2), ("E4", 2), ("F4", 2), ("E4", 2), ("D4", 2)],
    [("D5", 4), ("Bb4", 2), ("A4", 2), ("F4", 2), ("E4", 2), ("D4", 2), (None, 2)],
    [("F4", 2), ("A4", 2), ("D5", 2), ("F5", 2), ("E5", 4), ("D5", 2), ("Bb4", 2)],
    [("E5", 2), (None, 2), ("E4", 2), (None, 2), ("E5", 1), ("F5", 1), ("E5", 1), ("D5", 1), ("Bb4", 2), ("A4", 2)],
]
LEAD_B = [
    [("F5", 6), ("E5", 2), ("D5", 6), ("Bb4", 2)],
    [("D5", 6), ("E5", 2), ("F5", 4), ("E5", 2), ("D5", 2)],
    [("Bb4", 4), ("D5", 4), ("F5", 6), ("E5", 2)],
    [("E5", 3), ("F5", 1), ("E5", 2), ("Bb4", 2), ("A4", 2), ("E4", 2), (None, 4)],
]
LEAD_OUT = [
    LEAD_A[0],
    LEAD_A[1],
    LEAD_A[2],
    [("E5", 2), ("D5", 2), ("Bb4", 2), ("A4", 2), ("E4", 2), ("F4", 1), ("E4", 1), (None, 4)],
]
LEAD_SCORE = LEAD_A + LEAD_A2 + LEAD_B + LEAD_OUT

# Bass roots per bar (lament ×2, Neapolitan turn, lament reprise).
BASS_ROOTS = (
    ["A2", "G2", "F2", "E2"] * 2
    + ["F2", "G2", "Bb2", "E2"]
    + ["A2", "G2", "F2", "E2"]
)
# Double tresillo per bar: (start_16th, length_16ths, voicing)
# voicing: 'r' root, 'o' octave up, '5' fifth up.
BASS_PATTERN = [
    (0, 3, "r"), (3, 3, "r"), (6, 2, "o"),
    (8, 3, "r"), (11, 3, "5"), (14, 2, "o"),
]

FILL_BARS = {7, 15}  # 0-indexed bars with a snare fill


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def place(master: np.ndarray, clip: np.ndarray, start_sample: int, gain: float) -> None:
    """Add clip into master at start, wrapping past the loop seam."""
    n = len(clip)
    idx = (start_sample + np.arange(n)) % LOOP_SAMPLES
    np.add.at(master, idx, clip * gain)


def sixteenth_to_sample(bar: int, sixteenth: float) -> int:
    return round((bar * 16 + sixteenth) * S16 * SR)


def render() -> np.ndarray:
    master = np.zeros(LOOP_SAMPLES)

    # --- Lead + echo ghost ---
    for bar, phrase in enumerate(LEAD_SCORE):
        assert sum(d for _, d in phrase) == 16, f"bar {bar + 1} sums wrong"
        pos = 0.0
        for note, dur in phrase:
            if note is not None:
                n = int(dur * S16 * SR) - int(0.006 * SR)  # micro-gap articulation
                f = hz(note)
                tone = (
                    pulse_vibrato(f, n, duty=0.25)
                    if dur >= 3 else pulse(f, n, duty=0.25)
                )
                tone *= envelope(n)
                start = sixteenth_to_sample(bar, pos)
                place(master, tone, start, 0.21)
                # Echo ghost: one eighth behind, rounder timbre, quieter.
                ghost = pulse(f, n, duty=0.5) * envelope(n)
                place(master, ghost, start + round(2 * S16 * SR), 0.075)
            pos += dur

    # --- Bass (triangle, double tresillo) ---
    for bar, root in enumerate(BASS_ROOTS):
        rf = hz(root)
        for start16, dur16, voicing in BASS_PATTERN:
            f = rf * {"r": 1.0, "o": 2.0, "5": 1.5}[voicing]
            n = int(dur16 * S16 * SR) - int(0.008 * SR)
            tone = triangle(f, n) * envelope(n, release_s=0.02)
            place(master, tone, sixteenth_to_sample(bar, start16), 0.30)

    # --- Drums ---
    kick, snare, hat = drum_kick(), drum_snare(), drum_hat()
    for bar in range(BARS):
        for s16 in (0, 8):
            place(master, kick, sixteenth_to_sample(bar, s16), 0.34)
        for s16 in (4, 12):
            if bar in FILL_BARS and s16 == 12:
                continue  # fill replaces backbeat
            place(master, snare, sixteenth_to_sample(bar, s16), 0.20)
        for s16 in range(0, 16, 2):
            if bar in FILL_BARS and s16 >= 12:
                continue
            gain = 0.075 if s16 % 4 == 2 else 0.05  # offbeat accent
            place(master, hat, sixteenth_to_sample(bar, s16), gain)
        if bar in FILL_BARS:
            for i, s16 in enumerate((12, 13, 14, 15)):
                place(master, snare, sixteenth_to_sample(bar, s16),
                      0.10 + 0.045 * i)

    # --- Master ---
    peak = float(np.max(np.abs(master)))
    master *= 0.89 / max(peak, 1e-9)
    return master


def write_wav(samples: np.ndarray, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        wav.writeframes(pcm.tobytes())


def main() -> None:
    samples = render()
    write_wav(samples, OUT_PATH)
    seam = abs(float(samples[-1]) - float(samples[0]))
    print(f"wrote {OUT_PATH}")
    print(f"  {len(samples)} samples @ {SR} Hz = {len(samples)/SR:.2f}s loop")
    print(f"  peak {np.max(np.abs(samples)):.3f}  rms {np.sqrt(np.mean(samples**2)):.3f}")
    print(f"  loop seam delta {seam:.4f} (0 = perfectly seamless)")


if __name__ == "__main__":
    main()
