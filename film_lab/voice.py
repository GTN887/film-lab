"""Cinematic voice acting desk. Per-character bible voices. Local TTS + imported VO.

Each Character Bible entry owns a Voice profile (TTS id, imported sample, notes).
Dialogue tagged to a character routes to that voice. Alison and Bradley ship
distinct defaults. Cinema Desk muxes every cue. Zero Film Lab credits.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from film_lab.project import Project, _unique_dest
from film_lab.util import new_id, read_json, utc_now, write_json
from film_lab.wavutil import SAMPLE_RATE, sine_tone, wav_duration_seconds, write_mono_wav

REGISTERS = ("whisper", "intimate", "spoken", "projected")
PACES = ("held", "unhurried", "conversational", "urgent")
VOICE_BACKENDS = ("auto", "pyttsx3", "piper", "espeak", "xtts", "placeholder")
AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}

_PAUSE_MARK = re.compile(r"\[(\d+(?:\.\d+)?)s\]")
_SLUG = re.compile(r"[^a-z0-9_-]+")


@dataclass
class VoiceDirection:
    intention: str = "held want"
    breath: str = "close-mic, audible inhale"
    pace: str = "unhurried"
    register: str = "intimate"
    intensity: float = 0.45

    def line(self) -> str:
        return (
            f"intention: {self.intention}; breath: {self.breath}; "
            f"pace: {self.pace}; register: {self.register}; "
            f"intensity {self.intensity:.2f}"
        )


CHARACTER_VOICE: dict[str, VoiceDirection] = {
    "alison": VoiceDirection(
        intention="tender, a little sharp when tired",
        breath="close-mic, unhurried inhale before the line",
        pace="unhurried",
        register="intimate",
        intensity=0.48,
    ),
    "bradley": VoiceDirection(
        intention="steady, watchful warmth",
        breath="low, almost swallowed",
        pace="held",
        register="intimate",
        intensity=0.4,
    ),
}


# Distinct local TTS ids. espeak-ng understands en+f3 / en+m3; pyttsx3 matches gender.
CHARACTER_TTS: dict[str, dict[str, Any]] = {
    "alison": {
        "voice_id": "en+f3",
        "placeholder_hz": 210,
        "gender": "female",
        "pyttsx3_hints": ("zira", "hazel", "samantha", "susan", "female", "woman"),
    },
    "bradley": {
        "voice_id": "en+m3",
        "placeholder_hz": 118,
        "gender": "male",
        "pyttsx3_hints": ("david", "george", "mark", "daniel", "male", "man"),
    },
}


@dataclass
class VoiceProfile:
    """Per-character Voice bible: TTS id, imported sample, performance notes."""

    character_id: str
    backend: str = "auto"
    tts_voice_id: str = ""
    sample: str = ""
    notes: str = ""
    intention: str = ""
    breath: str = ""
    pace: str = "unhurried"
    register: str = "intimate"
    intensity: float = 0.45
    placeholder_hz: int = 160

    def direction(self) -> VoiceDirection:
        return direction_for(
            self.character_id,
            intention=self.intention,
            breath=self.breath,
            pace=self.pace,
            register=self.register,
            intensity=self.intensity,
        )


@dataclass
class VoiceCue:
    id: str
    character_id: str
    text: str
    path: str
    start_s: float = 0.0
    scene_id: str | None = None
    shot_id: str | None = None
    backend: str = ""
    take: int = 1
    intention: str = ""
    breath: str = ""
    pace: str = ""
    register: str = "intimate"
    intensity: float = 0.45
    voice_id: str = ""
    sample: str = ""
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict:
        return asdict(self)


def default_tts_voice_id(character_id: str) -> str:
    spec = CHARACTER_TTS.get((character_id or "").lower())
    if not spec:
        return ""
    return str(spec.get("voice_id") or "")


def default_placeholder_hz(character_id: str) -> int:
    spec = CHARACTER_TTS.get((character_id or "").lower())
    if not spec:
        return 160 + (abs(hash((character_id or "").lower())) % 40)
    return int(spec.get("placeholder_hz") or 160)


def default_voice_profile(character_id: str) -> VoiceProfile:
    cid = (character_id or "").lower()
    direction = direction_for(cid)
    return VoiceProfile(
        character_id=cid,
        backend="auto",
        tts_voice_id=default_tts_voice_id(cid),
        notes="",
        intention=direction.intention,
        breath=direction.breath,
        pace=direction.pace,
        register=direction.register,
        intensity=direction.intensity,
        placeholder_hz=default_placeholder_hz(cid),
    )


def resolve_character_id(project: Project | None, tag: str) -> str:
    """Map ALISON / Alison / alison — Name → bible id."""
    raw = (tag or "").strip()
    if not raw:
        return ""
    slug = _SLUG.sub("", raw.lower().replace(" ", "-"))
    if slug in CHARACTER_TTS or slug in CHARACTER_VOICE:
        return slug
    if project is not None:
        from film_lab.characters import list_characters

        wanted = raw.lower()
        for profile in list_characters(project):
            if profile.id == slug or profile.name.lower() == wanted:
                return profile.id
            if slug and (slug == profile.id or slug in profile.name.lower()):
                return profile.id
    return slug


def voice_profile_from_character(profile: Any) -> VoiceProfile:
    cid = getattr(profile, "id", "") or ""
    base = default_voice_profile(cid)
    backend = (getattr(profile, "voice_backend", "") or "").strip() or "auto"
    voice_id = (getattr(profile, "voice_id", "") or "").strip() or base.tts_voice_id
    sample = (getattr(profile, "voice_sample", "") or "").strip()
    notes = (getattr(profile, "voice_notes", "") or "").strip()
    return VoiceProfile(
        character_id=cid,
        backend=backend if backend in VOICE_BACKENDS else "auto",
        tts_voice_id=voice_id,
        sample=sample,
        notes=notes,
        intention=base.intention,
        breath=base.breath,
        pace=base.pace,
        register=base.register,
        intensity=base.intensity,
        placeholder_hz=base.placeholder_hz,
    )


def resolve_voice_profile(project: Project | None, character_id: str) -> VoiceProfile:
    cid = resolve_character_id(project, character_id)
    if project is not None and cid:
        from film_lab.characters import load_character

        try:
            return voice_profile_from_character(load_character(project, cid))
        except Exception:
            pass
        from film_lab.characters import list_characters

        try:
            for profile in list_characters(project):
                if profile.id == cid:
                    return voice_profile_from_character(profile)
        except Exception:
            pass
    return default_voice_profile(cid)


def probe_voice() -> tuple[str, str]:
    """Return (backend_id, human message)."""
    if _pyttsx3_ok():
        return "pyttsx3", "pyttsx3 is ready (offline system voices)."
    if shutil.which("piper"):
        return "piper", "Piper CLI is on PATH."
    if shutil.which("espeak") or shutil.which("espeak-ng"):
        return "espeak", "espeak is on PATH."
    if _xtts_ok():
        return "xtts", "Coqui XTTS import succeeded (local weights still required)."
    return (
        "placeholder",
        "No TTS engine. Film Lab will write a timed placeholder WAV "
        "(install pyttsx3, Piper, or espeak for real speech). "
        "Import recorded VO anytime. MOSS-TTS is optional later.",
    )


def voice_stack_markdown() -> str:
    return (
        "### Voice Desk (per-character film acting)\n"
        "Zero Film Lab credits. Not a hosted voice shop.\n\n"
        "- **Character Voice profile** — each bible entry owns a TTS voice id, "
        "imported sample, and performance notes. Alison (`en+f3`) and Bradley "
        "(`en+m3`) ship distinct defaults.\n"
        "- **Tagged lines route** — `ALISON: Stay.` speaks as Alison's voice; "
        "`BRADLEY:` never shares that take.\n"
        "- **Directions first** — intention, breath, pace, whisper/intimate, intensity. "
        "Do not generate a flat announcement read.\n"
        "- **Pause markup** — `[2s]` held silence, `...` a short hang, `/` a breath.\n"
        "- **Provider menu** — Local TTS (default). ElevenLabs / Seed Audio / Seed Speech "
        "are pickers only until you set a key — Film Lab will not fake those takes.\n"
        "- **Local TTS / import first** — pyttsx3, then Piper / espeak / XTTS if installed, "
        "else a timed WAV. Recorded VO is the 6GB-safe path.\n"
        "- **Cinema Desk** muxes every character cue at its start time."
    )


def expand_pause_markup(text: str) -> str:
    """Turn desk markup into spoken / timed text. Adults 18+ copy only."""
    spoken = _PAUSE_MARK.sub(lambda m: " " + (". " * max(1, int(round(float(m.group(1)))))) + " ", text)
    spoken = spoken.replace("/", ", ")
    return " ".join(spoken.split())


def direction_for(character_id: str, **overrides: object) -> VoiceDirection:
    base = CHARACTER_VOICE.get((character_id or "").lower(), VoiceDirection())
    data = asdict(base)
    for key, value in overrides.items():
        if key in data and value not in (None, ""):
            data[key] = value
    try:
        data["intensity"] = max(0.0, min(1.0, float(data["intensity"])))
    except (TypeError, ValueError):
        data["intensity"] = 0.45
    if data["register"] not in REGISTERS:
        data["register"] = "intimate"
    if data["pace"] not in PACES:
        data["pace"] = "unhurried"
    return VoiceDirection(**data)


def _pyttsx3_ok() -> bool:
    try:
        import pyttsx3  # type: ignore[import-not-found]

        engine = pyttsx3.init()
        engine.stop()
        return True
    except Exception:
        return False


def _xtts_ok() -> bool:
    try:
        import TTS  # noqa: F401  # type: ignore[import-not-found]

        return True
    except Exception:
        return False


def dialogue_dir(project: Project) -> Path:
    return project.root / "audio" / "dialogue"


def synthesize_line(
    project: Project,
    text: str,
    *,
    character_id: str = "",
    scene_id: str | None = None,
    shot_id: str | None = None,
    start_s: float = 0.0,
    backend: str = "auto",
    direction: VoiceDirection | None = None,
    take: int = 1,
    voice_id: str = "",
    sample: str = "",
) -> VoiceCue:
    project.ensure_dirs()
    cid = resolve_character_id(project, character_id)
    profile = resolve_voice_profile(project, cid)
    if voice_id:
        profile.tts_voice_id = voice_id
    if sample:
        profile.sample = sample
    if backend and backend not in {"", "auto"}:
        profile.backend = backend
    dest = dialogue_dir(project) / f"{new_id()}_{cid or 'line'}_t{take}.wav"
    spoken = expand_pause_markup(text)
    direction = direction or profile.direction()
    used = _render(spoken, dest, backend=profile.backend, direction=direction, profile=profile)
    cue = VoiceCue(
        id=dest.stem.split("_", 1)[0],
        character_id=cid,
        text=text,
        path=str(dest.resolve()),
        start_s=float(start_s),
        scene_id=scene_id,
        shot_id=shot_id,
        backend=used,
        take=int(take),
        intention=direction.intention,
        breath=direction.breath,
        pace=direction.pace,
        register=direction.register,
        intensity=direction.intensity,
        voice_id=profile.tts_voice_id,
        sample=profile.sample,
    )
    write_json(dest.with_suffix(".json"), cue.to_dict())
    return cue


def synthesize_takes(
    project: Project,
    text: str,
    *,
    character_id: str = "",
    scene_id: str | None = None,
    shot_id: str | None = None,
    start_s: float = 0.0,
    direction: VoiceDirection | None = None,
    count: int = 3,
    backend: str = "auto",
    voice_id: str = "",
) -> list[VoiceCue]:
    """Slight pace / intensity variants. Same line, different acting takes."""
    cid = resolve_character_id(project, character_id)
    base = direction or direction_for(cid)
    count = max(1, min(5, int(count)))
    cues: list[VoiceCue] = []
    offsets = (0.0, -0.12, 0.12, -0.2, 0.2)
    paces = (base.pace, "held", "conversational", "unhurried", "urgent")
    for index in range(count):
        variant = VoiceDirection(
            intention=base.intention,
            breath=base.breath,
            pace=paces[index] if paces[index] in PACES else base.pace,
            register=base.register,
            intensity=max(0.05, min(1.0, base.intensity + offsets[index])),
        )
        cues.append(
            synthesize_line(
                project,
                text,
                character_id=cid,
                scene_id=scene_id,
                shot_id=shot_id,
                start_s=start_s,
                direction=variant,
                take=index + 1,
                backend=backend,
                voice_id=voice_id,
            )
        )
    return cues


def speak_tagged_lines(
    project: Project,
    lines: Iterable[Any],
    *,
    scene_id: str | None = None,
    shot_id: str | None = None,
    backend: str = "",
    start_s: float = 0.0,
) -> list[VoiceCue]:
    """Each CHARACTER-tagged line speaks in that character's Voice profile."""
    cues: list[VoiceCue] = []
    cursor = float(start_s)
    for line in lines:
        if hasattr(line, "character") and hasattr(line, "text"):
            tag = str(line.character)
            text = str(line.text)
        elif isinstance(line, (tuple, list)) and len(line) >= 2:
            tag, text = str(line[0]), str(line[1])
        else:
            continue
        if not (text or "").strip():
            continue
        cid = resolve_character_id(project, tag)
        cue = synthesize_line(
            project,
            text.strip(),
            character_id=cid,
            scene_id=scene_id,
            shot_id=shot_id,
            start_s=cursor,
            backend=backend or "auto",
        )
        cues.append(cue)
        cursor += wav_duration_seconds(Path(cue.path)) + 0.35
    return cues


def import_vo(project: Project, sources: list[Path]) -> list[Path]:
    project.ensure_dirs()
    dest_dir = dialogue_dir(project)
    dest_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for src in sources:
        if not src.is_file() or src.suffix.lower() not in AUDIO_SUFFIXES:
            continue
        dest = _unique_dest(dest_dir, src.name)
        shutil.copy2(src, dest)
        written.append(dest)
    return written


def persist_voice_sample(project: Project, character_id: str, source: Path) -> Path:
    """Copy a recorded sample onto the character bible Voice profile."""
    from film_lab.characters import characters_dir, export_to_studio_library, load_character, save_character

    cid = resolve_character_id(project, character_id)
    if not cid:
        raise ValueError("Pick a character before importing a voice sample.")
    if not source.is_file() or source.suffix.lower() not in AUDIO_SUFFIXES:
        raise ValueError("Voice sample must be an audio file (wav / mp3 / m4a / flac / ogg).")
    dest_dir = characters_dir(project) / cid / "voice"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = _unique_dest(dest_dir, source.name)
    shutil.copy2(source, dest)
    profile = load_character(project, cid)
    profile.voice_sample = str(dest.resolve())
    save_character(project, profile)
    export_to_studio_library(profile)
    return dest


def apply_voice_defaults(profile: Any) -> bool:
    """Fill empty bible voice fields with Alison / Bradley distinct defaults."""
    dirty = False
    cid = getattr(profile, "id", "") or ""
    if not (getattr(profile, "voice_id", "") or "").strip():
        vid = default_tts_voice_id(cid)
        if vid:
            profile.voice_id = vid
            dirty = True
    if not (getattr(profile, "voice_backend", "") or "").strip():
        profile.voice_backend = "auto"
        dirty = True
    return dirty


def _render(
    text: str,
    dest: Path,
    *,
    backend: str,
    direction: VoiceDirection | None = None,
    profile: VoiceProfile | None = None,
) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    order = [backend] if backend not in {"", "auto"} else []
    preferred, _ = probe_voice()
    for name in order + [preferred, "pyttsx3", "piper", "espeak", "xtts", "placeholder"]:
        try:
            if name == "pyttsx3" and _try_pyttsx3(text, dest, direction=direction, profile=profile):
                return "pyttsx3"
            if name == "piper" and _try_piper(text, dest, profile=profile):
                return "piper"
            if name == "espeak" and _try_espeak(text, dest, profile=profile):
                return "espeak"
            if name == "xtts" and _try_xtts(text, dest, profile=profile):
                return "xtts"
            if name == "placeholder":
                _placeholder_speech(text, dest, direction=direction, profile=profile)
                return "placeholder"
        except Exception:
            continue
    _placeholder_speech(text, dest, direction=direction, profile=profile)
    return "placeholder"


def _try_pyttsx3(
    text: str,
    dest: Path,
    *,
    direction: VoiceDirection | None = None,
    profile: VoiceProfile | None = None,
) -> bool:
    import pyttsx3  # type: ignore[import-not-found]

    engine = pyttsx3.init()
    direction = direction or VoiceDirection()
    _match_pyttsx3_voice(engine, profile)
    rate = int(engine.getProperty("rate") or 160)
    if direction.pace == "held":
        rate = int(rate * 0.78)
    elif direction.pace == "unhurried":
        rate = int(rate * 0.88)
    elif direction.pace == "urgent":
        rate = int(rate * 1.12)
    if direction.register == "whisper":
        rate = int(rate * 0.9)
    engine.setProperty("rate", max(90, min(220, rate)))
    volume = 0.35 + 0.55 * direction.intensity
    if direction.register == "whisper":
        volume *= 0.55
    elif direction.register == "projected":
        volume = min(1.0, volume * 1.15)
    engine.setProperty("volume", max(0.15, min(1.0, volume)))
    engine.save_to_file(text, str(dest))
    engine.runAndWait()
    return dest.is_file() and dest.stat().st_size > 44


def _match_pyttsx3_voice(engine: Any, profile: VoiceProfile | None) -> None:
    voices = engine.getProperty("voices") or []
    if not voices:
        return
    wanted = (profile.tts_voice_id if profile else "").lower()
    cid = (profile.character_id if profile else "").lower()
    spec = CHARACTER_TTS.get(cid, {})
    hints = tuple(spec.get("pyttsx3_hints") or ())
    gender = str(spec.get("gender") or "")

    def score(voice: Any) -> int:
        name = (getattr(voice, "name", "") or "").lower()
        vid = (getattr(voice, "id", "") or "").lower()
        blob = f"{name} {vid}"
        points = 0
        if wanted and wanted in blob:
            points += 100
        for hint in hints:
            if hint and hint in blob:
                points += 20
        if gender == "female" and any(tok in blob for tok in ("female", "zira", "hazel", "samantha", "woman")):
            points += 10
        if gender == "male" and any(tok in blob for tok in ("male", "david", "george", "mark", "man")):
            points += 10
        return points

    best = max(voices, key=score)
    if score(best) > 0:
        engine.setProperty("voice", best.id)


def _try_cli(cmd: list[str], dest: Path) -> bool:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode == 0 and dest.is_file() and dest.stat().st_size > 44


def _try_piper(text: str, dest: Path, *, profile: VoiceProfile | None = None) -> bool:
    if not shutil.which("piper"):
        return False
    cmd = ["piper", "--text", text, "--output_file", str(dest)]
    model = (profile.tts_voice_id if profile else "") or ""
    if model and Path(model).is_file():
        cmd.extend(["--model", model])
    return _try_cli(cmd, dest)


def _try_espeak(text: str, dest: Path, *, profile: VoiceProfile | None = None) -> bool:
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if not exe:
        return False
    cmd = [exe, "-w", str(dest)]
    voice = (profile.tts_voice_id if profile else "") or ""
    if voice and not Path(voice).is_file():
        cmd.extend(["-v", voice])
    cmd.append(text)
    return _try_cli(cmd, dest)


def _try_xtts(text: str, dest: Path, *, profile: VoiceProfile | None = None) -> bool:
    # Soft hook only — requires local Coqui weights the user installed.
    from TTS.api import TTS as Coqui  # type: ignore[import-not-found]

    model = Coqui(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
    kwargs: dict[str, Any] = {"text": text, "file_path": str(dest), "language": "en"}
    sample = (profile.sample if profile else "") or ""
    if sample and Path(sample).is_file():
        kwargs["speaker_wav"] = sample
    model.tts_to_file(**kwargs)
    return dest.is_file() and dest.stat().st_size > 44


def _placeholder_speech(
    text: str,
    dest: Path,
    *,
    direction: VoiceDirection | None = None,
    profile: VoiceProfile | None = None,
) -> None:
    """Timed word-beeps so the timeline still has a WAV without a TTS engine."""
    direction = direction or VoiceDirection()
    words = [w for w in text.split() if w] or ["…"]
    samples: list[float] = []
    amp = 0.08 + 0.12 * direction.intensity
    if direction.register == "whisper":
        amp *= 0.55
    gap = 0.1 if direction.pace == "urgent" else 0.16 if direction.pace == "conversational" else 0.22
    base = profile.placeholder_hz if profile else 170
    for index, word in enumerate(words):
        if word in {".", "..."}:
            samples.extend([0.0] * int(0.35 * SAMPLE_RATE))
            continue
        freq = int(base) + (abs(hash(word)) % 36)
        dur = min(0.5, 0.11 + 0.03 * len(word))
        if direction.pace == "held":
            dur *= 1.15
        samples.extend(sine_tone(dur, freq, amplitude=amp))
        samples.extend([0.0] * int(gap * SAMPLE_RATE))
        if index > 40:
            break
    write_mono_wav(dest, samples)


def list_dialogue(project: Project) -> list[Path]:
    folder = dialogue_dir(project)
    if not folder.exists():
        return []
    return sorted(p for p in folder.glob("*.wav") if p.is_file())


def list_cues(project: Project) -> list[VoiceCue]:
    folder = dialogue_dir(project)
    if not folder.exists():
        return []
    cues: list[VoiceCue] = []
    for path in sorted(folder.glob("*.json")):
        data = read_json(path)
        if not isinstance(data, dict) or "path" not in data:
            continue
        try:
            cues.append(VoiceCue(**{k: data[k] for k in VoiceCue.__dataclass_fields__ if k in data}))
        except (TypeError, ValueError):
            continue
    return cues


def cues_for_entry(project: Project, entry: Any) -> list[VoiceCue]:
    """All Voice cues tagged to this reel row's shot / scene, plus attached WAV."""
    found: list[VoiceCue] = []
    seen: set[str] = set()
    shot_id = getattr(entry, "shot_id", None) or ""
    scene_id = getattr(entry, "scene_id", None) or ""

    def add(cue: VoiceCue) -> None:
        key = str(Path(cue.path).resolve()) if cue.path else ""
        if not key or key in seen:
            return
        if not Path(cue.path).is_file():
            return
        seen.add(key)
        found.append(cue)

    for cue in list_cues(project):
        if shot_id and cue.shot_id == shot_id:
            add(cue)
        elif scene_id and cue.scene_id == scene_id and (not cue.shot_id or cue.shot_id == shot_id):
            add(cue)
    attached = getattr(entry, "dialogue_wav", None) or ""
    if attached:
        add(
            VoiceCue(
                id="reel-attached",
                character_id="",
                text="",
                path=str(Path(attached)),
                start_s=0.0,
            )
        )
    found.sort(key=lambda c: (float(c.start_s or 0), c.character_id, c.take))
    return found
