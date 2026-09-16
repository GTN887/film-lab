"""Persistent, scene-bound room-tone beds and non-destructive Cinema mixing."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import shutil
from pathlib import Path
from typing import Any

from film_lab.ffmpeg_support import FFmpegError, probe_duration_seconds, probe_has_audio, run_ffmpeg
from film_lab.project import utc_now

AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}


@dataclass(frozen=True)
class SceneRoomTone:
    scene_id: str
    media_path: str
    enabled: bool = True
    gain_db: float = -24.0
    fade_in_s: float = 0.25
    fade_out_s: float = 0.25
    source_name: str = ""
    source_sha256: str = ""
    assigned_at: str = ""
    director_note: str = ""

    def to_dict(self) -> dict[str, Any]: return asdict(self)


class RoomToneStore:
    def __init__(self, project):
        self.project = project; project.ensure_dirs(); self.path = project.root / "scene_room_tones.json"

    def _load(self) -> dict[str, Any]:
        if not self.path.exists(): return {"version": 1, "scenes": {}}
        try: raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError): return {"version": 1, "scenes": {}}
        raw.setdefault("version", 1); raw.setdefault("scenes", {}); return raw

    def _save(self, raw: dict[str, Any]) -> None:
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8"); tmp.replace(self.path)

    def get(self, scene_id: str) -> SceneRoomTone | None:
        item = self._load()["scenes"].get(str(scene_id).strip())
        return SceneRoomTone(**item) if isinstance(item, dict) else None

    def list(self) -> list[SceneRoomTone]:
        return [SceneRoomTone(**x) for x in self._load()["scenes"].values() if isinstance(x, dict)]

    def assign(self, scene_id: str, source: Path | str, *, enabled: bool = True, gain_db: float = -24.0,
               fade_in_s: float = .25, fade_out_s: float = .25, director_note: str = "") -> SceneRoomTone:
        scene_id = str(scene_id or "").strip()
        if not scene_id: raise ValueError("Scene ID is required for room tone.")
        src = Path(source)
        if not src.is_file() or src.suffix.lower() not in AUDIO_SUFFIXES: raise ValueError("A real supported room-tone audio file is required.")
        gain = float(gain_db); fi = float(fade_in_s); fo = float(fade_out_s)
        if not -60.0 <= gain <= 12.0: raise ValueError("Room-tone gain must be between -60 and +12 dB.")
        if not 0.0 <= fi <= 10.0 or not 0.0 <= fo <= 10.0: raise ValueError("Room-tone fades must be between 0 and 10 seconds.")
        folder = self.project.audio_dir / "room_tone" / scene_id; folder.mkdir(parents=True, exist_ok=True)
        digest = sha256(src.read_bytes()).hexdigest(); dest = folder / f"{digest[:12]}{src.suffix.lower()}"
        if src.resolve() != dest.resolve(): shutil.copy2(src, dest)
        state = SceneRoomTone(scene_id, str(dest.resolve()), bool(enabled), gain, fi, fo, src.name, digest, utc_now(), str(director_note or "").strip())
        raw = self._load(); raw["scenes"][scene_id] = state.to_dict(); self._save(raw); return state

    def set_enabled(self, scene_id: str, enabled: bool) -> SceneRoomTone:
        state = self.get(scene_id)
        if state is None: raise KeyError(scene_id)
        raw = self._load(); raw["scenes"][scene_id] = {**state.to_dict(), "enabled": bool(enabled)}; self._save(raw)
        return self.get(scene_id)


def mix_room_tone(picture: Path, state: SceneRoomTone, dest: Path) -> Path:
    """Loop and mix one proven scene bed to picture duration without altering inputs."""
    picture, bed, dest = Path(picture), Path(state.media_path), Path(dest)
    if not picture.is_file(): raise FileNotFoundError(picture)
    if not state.enabled: shutil.copy2(picture, dest); return dest
    if not bed.is_file(): raise FileNotFoundError(f"Missing assigned room tone: {bed}")
    duration = probe_duration_seconds(picture)
    if duration is None or duration <= 0: raise FFmpegError("Could not prove Cinema duration for room-tone mix.")
    fade_out_at = max(0.0, duration - min(state.fade_out_s, duration))
    volume = 10.0 ** (state.gain_db / 20.0)
    bed_chain = f"[1:a]volume={volume:.8f},atrim=0:{duration:.3f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d={min(state.fade_in_s,duration):.3f},afade=t=out:st={fade_out_at:.3f}:d={min(state.fade_out_s,duration):.3f}[bed]"
    has_program = probe_has_audio(picture) is True
    graph = bed_chain + (";[0:a][bed]amix=inputs=2:duration=first:normalize=0[a]" if has_program else "")
    dest.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(["-y", "-i", str(picture), "-stream_loop", "-1", "-i", str(bed), "-filter_complex", graph,
                "-map", "0:v", "-map", "[a]" if has_program else "[bed]", "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(dest)])
    return dest
