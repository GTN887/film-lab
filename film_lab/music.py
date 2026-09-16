"""Score cues, imported beds, and a local synth fallback."""

from __future__ import annotations

import math
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from film_lab.project import Project, _unique_dest
from film_lab.util import new_id, read_json, slugify, utc_now, write_json
from film_lab.wavutil import SAMPLE_RATE, mix_signals, sine_tone, write_mono_wav

AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}
MOODS = (
    "intimate lamp",
    "held breath",
    "afterglow",
    "uneasy quiet",
    "neutral bed",
    "warm pulse",
    "night street",
)


@dataclass
class MusicCue:
    id: str
    name: str
    mood: str = "intimate lamp"
    in_s: float = 0.0
    out_s: float = 8.0
    bpm: float = 62.0
    intensity: float = 0.35
    path: str | None = None
    notes: str = ""
    created_at: str = field(default_factory=utc_now)

    def duration(self) -> float:
        return max(0.5, float(self.out_s) - float(self.in_s))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def label(self) -> str:
        return f"{self.id} — {self.name}"


def music_dir(project: Project) -> Path:
    return project.root / "audio" / "music"


def beds_dir(project: Project) -> Path:
    return project.root / "audio" / "beds"


def cues_path(project: Project) -> Path:
    return project.root / "audio" / "cues.json"


def save_cues(project: Project, cues: list[MusicCue]) -> None:
    project.ensure_dirs()
    write_json(cues_path(project), [c.to_dict() for c in cues])


def load_cues(project: Project) -> list[MusicCue]:
    path = cues_path(project)
    if not path.exists():
        return []
    raw = read_json(path)
    cues: list[MusicCue] = []
    if not isinstance(raw, list):
        return cues
    for item in raw:
        if isinstance(item, dict) and "id" in item and "name" in item:
            cues.append(MusicCue(**{k: item[k] for k in MusicCue.__dataclass_fields__ if k in item}))
    return cues


def upsert_cue(project: Project, cue: MusicCue) -> MusicCue:
    cues = [c for c in load_cues(project) if c.id != cue.id]
    cues.append(cue)
    save_cues(project, cues)
    return cue


def import_music(project: Project, sources: list[Path]) -> list[Path]:
    project.ensure_dirs()
    music_dir(project).mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for src in sources:
        if not src.is_file() or src.suffix.lower() not in AUDIO_SUFFIXES:
            continue
        dest = _unique_dest(music_dir(project), src.name)
        shutil.copy2(src, dest)
        written.append(dest)
    return written


def list_music_files(project: Project) -> list[Path]:
    files: list[Path] = []
    for folder in (music_dir(project), beds_dir(project)):
        if folder.exists():
            files.extend(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in AUDIO_SUFFIXES)
    return sorted(files)


def probe_musicgen() -> tuple[bool, str]:
    try:
        import audiocraft  # noqa: F401  # type: ignore[import-not-found]

        return True, "audiocraft is installed. MusicGen-small is optional and tight on 6GB AMD."
    except Exception:
        return False, "audiocraft / MusicGen not installed. Import a bed, or use the local synth."


def score_stack_markdown() -> str:
    return (
        "### Score Desk (this PC)\n"
        "Zero Film Lab credits. No hosted music subscription.\n\n"
        "1. **Import your music (primary)** — drop a WAV/MP3 into `audio/music/`, then mux on Cinema Desk.\n"
        "2. **Local synth bed** — always on. Mood + duration + intensity. Good enough to lock timing.\n"
        "3. **MusicGen-small (AudioCraft)** — optional later if you install weights. "
        "A Radeon RX 5600 XT (~6GB) will often struggle; treat this as off-box or Off.\n"
        "4. Cinema Desk **Assemble reel** muxes the picked score under picture."
    )


def render_bed(project: Project, cue: MusicCue) -> Path:
    """Always-available ambient bed. Optional MusicGen is documented, not required."""
    project.ensure_dirs()
    beds_dir(project).mkdir(parents=True, exist_ok=True)
    dest = beds_dir(project) / f"{cue.id}_{slugify(cue.name, 'cue')}.wav"
    generated = try_musicgen(dest, cue)
    if generated is None:
        samples = _synth_bed(cue.duration(), cue.mood, cue.bpm, intensity=cue.intensity)
        write_mono_wav(dest, samples)
    cue.path = str(dest.resolve())
    upsert_cue(project, cue)
    return dest


def try_musicgen(dest: Path, cue: MusicCue) -> Path | None:
    """Optional AudioCraft path. Fail soft. Never required on 6GB AMD."""
    import os

    if os.environ.get("FILM_LAB_MUSICGEN", "").strip() not in {"1", "true", "yes"}:
        return None
    ok, _ = probe_musicgen()
    if not ok:
        return None
    try:
        from audiocraft.models import MusicGen  # type: ignore[import-not-found]

        model = MusicGen.get_pretrained("facebook/musicgen-small")
        model.set_generation_params(duration=min(12.0, max(2.0, cue.duration())))
        prompt = f"{cue.mood} cinematic underscore, no vocals, intensity {cue.intensity:.2f}"
        wav = model.generate([prompt])
        import numpy as np  # type: ignore[import-not-found]
        from film_lab.wavutil import write_mono_wav as _write

        audio = wav[0, 0].cpu().numpy().astype(np.float32)
        _write(dest, [float(x) for x in audio.tolist()[: int(cue.duration() * SAMPLE_RATE)]])
        if dest.is_file() and dest.stat().st_size > 44:
            return dest
    except Exception:
        return None
    return None


def _synth_bed(
    duration: float, mood: str, bpm: float, *, intensity: float = 0.35
) -> list[float]:
    pulse = max(40.0, min(140.0, bpm))
    gain = 0.55 + 0.9 * max(0.0, min(1.0, intensity))
    if mood == "held breath":
        roots = (98.0, 147.0, 196.0)
        amp = (0.07, 0.05, 0.03)
    elif mood == "afterglow":
        roots = (110.0, 165.0, 220.0)
        amp = (0.06, 0.045, 0.035)
    elif mood == "uneasy quiet":
        roots = (82.0, 123.0, 185.0)
        amp = (0.08, 0.04, 0.025)
    elif mood == "neutral bed":
        roots = (130.0, 196.0, 261.0)
        amp = (0.05, 0.04, 0.02)
    elif mood == "warm pulse":
        roots = (98.0, 123.5, 196.0)
        amp = (0.08, 0.05, 0.03)
    elif mood == "night street":
        roots = (73.4, 110.0, 174.6)
        amp = (0.07, 0.04, 0.028)
    else:  # intimate lamp
        roots = (110.0, 138.6, 164.8)
        amp = (0.075, 0.05, 0.03)
    amp = (amp[0] * gain, amp[1] * gain, amp[2] * gain)

    layers = [
        sine_tone(duration, roots[0], amplitude=amp[0]),
        sine_tone(duration, roots[1], amplitude=amp[1]),
        sine_tone(duration, roots[2], amplitude=amp[2]),
    ]
    mixed = mix_signals(*layers)
    # Slow amplitude breathe locked to BPM (one swell every two beats).
    period = 2.0 * 60.0 / pulse
    out: list[float] = []
    for i, value in enumerate(mixed):
        t = i / SAMPLE_RATE
        lfo = 0.72 + 0.28 * (0.5 + 0.5 * math.sin(2 * math.pi * t / period))
        out.append(value * lfo)
    return out


def new_cue(
    name: str,
    mood: str = "intimate lamp",
    bpm: float = 62.0,
    length: float = 8.0,
    *,
    intensity: float = 0.35,
) -> MusicCue:
    return MusicCue(
        id=new_id(),
        name=name.strip() or "untitled cue",
        mood=mood,
        out_s=length,
        bpm=bpm,
        intensity=max(0.0, min(1.0, float(intensity))),
    )
