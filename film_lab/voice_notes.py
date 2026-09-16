"""Voice notes — type or speak into the same Director / Mark note.

Mic audio transcribes into the text box already on the desk (actor beats,
prop / object / clothing region notes). Apply / Regenerate is unchanged.
Local STT first (vosk / faster-whisper / whisper). Optional user-owned
cloud STT if a writing-studio key is set. No Film Lab credits.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from film_lab.ffmpeg_support import FFmpegError, run_ffmpeg
from film_lab.wavutil import wav_duration_seconds

AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".webm", ".opus"}
MIN_SECONDS = 0.35
VOSK_DIR_ENV = "FILM_LAB_VOSK_MODEL"
DEFAULT_VOSK_DIR = Path("data") / "models" / "vosk-model-small-en-us-0.15"

NOTE_HELP = (
    "Type or speak into the **same note**. Mic transcribes, then **Apply / Regenerate**. "
    "Actor beats on Director Note. Prop / object / clothing on Mark & Direct. "
    "Local STT if installed; otherwise a writing-studio key you own. No Film Lab credits."
)


class VoiceNoteError(ValueError):
    """Missing audio, no speech, or no transcriber."""


_OVERRIDE: Callable[[Path], str] | None = None


def set_transcribe_override(fn: Callable[[Path], str] | None) -> None:
    global _OVERRIDE
    _OVERRIDE = fn


def merge_note(typed: str | None, spoken: str | None) -> str:
    """Fold spoken words into the typed note. Same box. No duplicate append."""
    existing = " ".join((typed or "").split())
    voice = " ".join((spoken or "").split())
    if not voice:
        return existing
    if not existing:
        return voice
    if voice.lower() in existing.lower():
        return existing
    joiner = "" if existing.endswith((" ", "\n")) else " "
    return f"{existing}{joiner}{voice}".strip()


def audio_path(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, dict):
        raw = raw.get("path") or raw.get("name") or raw.get("audio") or ""
    text = str(raw or "").strip()
    if not text:
        return ""
    path = Path(text)
    return str(path) if path.is_file() else ""


def vosk_model_dir() -> Path | None:
    env = (os.environ.get(VOSK_DIR_ENV) or "").strip()
    candidates = []
    if env:
        candidates.append(Path(env))
    candidates.append(DEFAULT_VOSK_DIR)
    root = Path("data") / "models"
    if root.is_dir():
        candidates.extend(sorted(root.glob("vosk-model*")))
    for path in candidates:
        if path.is_dir() and (path / "am" / "final.mdl").is_file():
            return path
    return None


def list_backends() -> list[str]:
    found: list[str] = []
    if _OVERRIDE is not None:
        found.append("override")
    try:
        import vosk  # noqa: F401

        if vosk_model_dir() is not None:
            found.append("vosk")
        else:
            found.append("vosk-no-model")
    except ImportError:
        pass
    try:
        import faster_whisper  # noqa: F401

        found.append("faster-whisper")
    except ImportError:
        pass
    try:
        import whisper  # noqa: F401

        found.append("whisper")
    except ImportError:
        pass
    from film_lab.llm import get_openai_key

    if get_openai_key():
        found.append("cloud-key")
    return found


def usable_backends() -> list[str]:
    return [b for b in list_backends() if b != "vosk-no-model"]


def probe_stt() -> tuple[str, str]:
    usable = usable_backends()
    listed = list_backends()
    if usable:
        return "Ready", f"Voice notes via {', '.join(usable)}. Type still works. Zero credits."
    if "vosk-no-model" in listed:
        return (
            "Model missing",
            "vosk is installed. Drop the small English model in "
            f"`{DEFAULT_VOSK_DIR}` or set {VOSK_DIR_ENV}. Typed notes still work.",
        )
    return (
        "Type only",
        "No local transcriber yet. Type the note, or `pip install vosk` "
        "and add the small English model, or set a writing-studio key you own. "
        "No Film Lab credits.",
    )


def voice_note_markdown() -> str:
    status, detail = probe_stt()
    return f"### Voice notes — typed or spoken\n\n**STT:** {status}. {detail}\n\n{NOTE_HELP}"


def transcribe(raw: Any) -> str:
    """Speech → text. Never invents words if the backend is missing."""
    path = audio_path(raw)
    if not path:
        raise VoiceNoteError("Record or drop a mic take first. Typed notes still work.")
    src = Path(path)
    suffix = src.suffix.lower()
    if suffix and suffix not in AUDIO_SUFFIXES:
        raise VoiceNoteError("Voice notes need a mic take (wav / webm / mp3).")
    if _OVERRIDE is not None:
        text = _OVERRIDE(src).strip()
        if not text:
            raise VoiceNoteError("No speech heard. Speak again, or type the note.")
        return text
    wav = _pcm16(src)
    if wav_duration_seconds(wav) < MIN_SECONDS:
        raise VoiceNoteError("That take is too short. Speak the note, or type it.")
    errors: list[str] = []
    for name, runner in (
        ("vosk", _transcribe_vosk),
        ("faster-whisper", _transcribe_faster),
        ("whisper", _transcribe_whisper),
        ("cloud-key", _transcribe_cloud),
    ):
        try:
            text = runner(wav).strip()
        except VoiceNoteError as exc:
            errors.append(f"{name}: {exc}")
            continue
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{name}: {exc}")
            continue
        if text:
            return text
        errors.append(f"{name}: empty")
    status, detail = probe_stt()
    extra = f" Tried: {'; '.join(errors)}." if errors else ""
    raise VoiceNoteError(f"{detail}{extra} STT={status}.")


def _pcm16(source: Path) -> Path:
    dest = Path(tempfile.mkdtemp(prefix="fl-note-")) / "note.wav"
    try:
        run_ffmpeg(
            [
                "-y",
                "-i",
                str(source),
                "-ac",
                "1",
                "-ar",
                "16000",
                "-c:a",
                "pcm_s16le",
                str(dest),
            ]
        )
    except FFmpegError as exc:
        raise VoiceNoteError(f"Could not read the mic take. {exc}") from exc
    if not dest.is_file():
        raise VoiceNoteError("Could not read the mic take.")
    return dest


def _transcribe_vosk(wav: Path) -> str:
    try:
        import vosk
    except ImportError as exc:
        raise VoiceNoteError("vosk is not installed.") from exc
    model_dir = vosk_model_dir()
    if model_dir is None:
        raise VoiceNoteError("vosk model folder is missing.")
    model = vosk.Model(str(model_dir))
    rec = vosk.KaldiRecognizer(model, 16000)
    rec.SetWords(True)
    import wave

    with wave.open(str(wav), "rb") as handle:
        while True:
            chunk = handle.readframes(4000)
            if not chunk:
                break
            rec.AcceptWaveform(chunk)
    try:
        payload = json.loads(rec.FinalResult() or "{}")
    except json.JSONDecodeError as exc:
        raise VoiceNoteError("vosk returned unreadable text.") from exc
    return str(payload.get("text") or "").strip()


def _transcribe_faster(wav: Path) -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise VoiceNoteError("faster-whisper is not installed.") from exc
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    segments, _info = model.transcribe(str(wav), beam_size=1)
    return " ".join(seg.text.strip() for seg in segments if getattr(seg, "text", "")).strip()


def _transcribe_whisper(wav: Path) -> str:
    try:
        import whisper
    except ImportError as exc:
        raise VoiceNoteError("whisper is not installed.") from exc
    model = whisper.load_model("tiny", device="cpu")
    result = model.transcribe(str(wav), fp16=False)
    return str((result or {}).get("text") or "").strip()


def _transcribe_cloud(wav: Path) -> str:
    from film_lab.llm import get_openai_key, openai_base

    key = get_openai_key()
    if not key:
        raise VoiceNoteError("No writing-studio key set.")
    boundary = "----FilmLabNote"
    header = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="model"\r\n\r\n'
        "whisper-1\r\n"
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="note.wav"\r\n'
        "Content-Type: audio/wav\r\n\r\n"
    ).encode("utf-8")
    footer = f"\r\n--{boundary}--\r\n".encode("utf-8")
    body = header + wav.read_bytes() + footer
    req = Request(
        f"{openai_base()}/audio/transcriptions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:240]
        raise VoiceNoteError(f"Cloud STT refused the take. {detail}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise VoiceNoteError(f"Cloud STT failed. {exc}") from exc
    return str(payload.get("text") or "").strip()
