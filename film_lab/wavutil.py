"""Write 16-bit mono WAV files without extra audio libraries."""

from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 22050


def write_mono_wav(path: Path, samples: list[float], *, sample_rate: int = SAMPLE_RATE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        frames = bytearray()
        for sample in samples:
            clamped = max(-1.0, min(1.0, sample))
            frames.extend(struct.pack("<h", int(clamped * 32767)))
        wav.writeframes(bytes(frames))
    return path


def sine_tone(
    duration: float,
    freq: float,
    *,
    amplitude: float = 0.18,
    sample_rate: int = SAMPLE_RATE,
) -> list[float]:
    n = max(1, int(duration * sample_rate))
    out: list[float] = []
    for i in range(n):
        t = i / sample_rate
        env = 1.0
        fade = min(0.04, duration / 4)
        if t < fade:
            env = t / fade
        elif t > duration - fade:
            env = max(0.0, (duration - t) / fade)
        out.append(amplitude * env * math.sin(2 * math.pi * freq * t))
    return out


def wav_duration_seconds(path: Path) -> float:
    """Length of a WAV in seconds. 0.0 if the file cannot be read."""
    try:
        with wave.open(str(path), "rb") as wav:
            frames = wav.getnframes()
            rate = wav.getframerate() or SAMPLE_RATE
            if rate <= 0:
                return 0.0
            return frames / float(rate)
    except Exception:
        return 0.0


def mix_signals(*signals: list[float]) -> list[float]:
    length = max((len(s) for s in signals), default=0)
    mixed = [0.0] * length
    for signal in signals:
        for i, value in enumerate(signal):
            mixed[i] += value
    peak = max((abs(v) for v in mixed), default=1.0)
    if peak > 0.95:
        scale = 0.95 / peak
        mixed = [v * scale for v in mixed]
    return mixed
