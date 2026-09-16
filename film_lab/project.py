"""On-disk project layout under ./data/projects/<name>/."""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from film_lab.living import LivingBrief
from film_lab.shot_card import ShotCard

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
VIDEO_SUFFIXES = {".mp4", ".webm", ".mov"}
_PROJECT_NAME = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,62}$")


def default_data_root() -> Path:
    return Path.cwd() / "data" / "projects"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_project_name(name: str) -> str:
    cleaned = name.strip()
    if not _PROJECT_NAME.match(cleaned):
        raise ValueError(
            "Project name must start with a letter or digit and use only "
            "letters, digits, dot, underscore, or hyphen (max 63 chars)."
        )
    return cleaned


@dataclass
class OutputClip:
    path: str
    shot_id: str | None = None
    shot_name: str = ""
    generator: str = ""
    created_at: str = ""
    duration: float | None = None


@dataclass
class Project:
    name: str
    root: Path
    created_at: str = field(default_factory=utc_now)
    description: str = ""
    living: dict = field(default_factory=dict)
    active_cast: list[str] = field(default_factory=lambda: ["alison", "bradley"])
    face_lock_strength: float = 0.55
    active_lighting: str = ""
    filming_mode: str = "18+ Explicit"
    quality: str = "720p"
    aspect: str = "16:9"

    def __post_init__(self) -> None:
        from film_lab.constants import normalize_aspect
        from film_lab.quality import normalize_quality

        self.quality = normalize_quality(self.quality)
        self.aspect = normalize_aspect(self.aspect)

    @property
    def stills_dir(self) -> Path:
        return self.root / "stills"

    @property
    def shots_dir(self) -> Path:
        return self.root / "shots"

    @property
    def outputs_dir(self) -> Path:
        return self.root / "outputs"

    @property
    def meta_path(self) -> Path:
        return self.root / "project.json"

    @property
    def gallery_path(self) -> Path:
        return self.root / "gallery.json"

    @property
    def scenes_dir(self) -> Path:
        return self.root / "scenes"

    @property
    def characters_dir(self) -> Path:
        return self.root / "characters"

    @property
    def audio_dir(self) -> Path:
        return self.root / "audio"

    @property
    def writing_dir(self) -> Path:
        return self.root / "writing"

    @property
    def sets_dir(self) -> Path:
        return self.root / "sets"

    @property
    def takes_dir(self) -> Path:
        return self.root / "takes"

    def ensure_dirs(self) -> None:
        self.stills_dir.mkdir(parents=True, exist_ok=True)
        self.shots_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.scenes_dir.mkdir(parents=True, exist_ok=True)
        self.characters_dir.mkdir(parents=True, exist_ok=True)
        (self.audio_dir / "dialogue").mkdir(parents=True, exist_ok=True)
        (self.audio_dir / "music").mkdir(parents=True, exist_ok=True)
        (self.audio_dir / "beds").mkdir(parents=True, exist_ok=True)
        (self.audio_dir / "room_tone").mkdir(parents=True, exist_ok=True)
        (self.root / "luts").mkdir(parents=True, exist_ok=True)
        self.writing_dir.mkdir(parents=True, exist_ok=True)
        self.sets_dir.mkdir(parents=True, exist_ok=True)
        self.takes_dir.mkdir(parents=True, exist_ok=True)

    def save_meta(self) -> None:
        self.ensure_dirs()
        payload = {
            "name": self.name,
            "created_at": self.created_at,
            "description": self.description,
            "living": self.living_brief().to_dict() if self.living else {},
            "active_cast": list(self.active_cast or ["alison", "bradley"]),
            "face_lock_strength": float(self.face_lock_strength),
            "active_lighting": self.active_lighting or "",
            "filming_mode": self.filming_mode or "18+ Explicit",
            "quality": self.quality or "720p",
            "aspect": self.aspect or "16:9",
        }
        self.meta_path.write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )

    @classmethod
    def create(
        cls,
        name: str,
        *,
        data_root: Path | None = None,
        description: str = "",
    ) -> Project:
        name = validate_project_name(name)
        root = (data_root or default_data_root()) / name
        project = cls(name=name, root=root, description=description)
        if project.meta_path.exists():
            return cls.load(name, data_root=data_root)
        project.save_meta()
        return project

    @classmethod
    def load(cls, name: str, *, data_root: Path | None = None) -> Project:
        name = validate_project_name(name)
        root = (data_root or default_data_root()) / name
        meta_path = root / "project.json"
        if not meta_path.exists():
            raise FileNotFoundError(f"No project named {name!r} under {root.parent}")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        cast = meta.get("active_cast")
        if not isinstance(cast, list) or not cast:
            cast = ["alison", "bradley"]
        try:
            lock = float(meta.get("face_lock_strength", 0.55))
        except (TypeError, ValueError):
            lock = 0.55
        project = cls(
            name=meta.get("name", name),
            root=root,
            created_at=meta.get("created_at", utc_now()),
            description=meta.get("description", ""),
            living=meta.get("living") if isinstance(meta.get("living"), dict) else {},
            active_cast=[str(c).strip() for c in cast if str(c).strip()],
            face_lock_strength=min(1.0, max(0.0, lock)),
            active_lighting=str(meta.get("active_lighting") or ""),
            filming_mode=str(meta.get("filming_mode") or "18+ Explicit"),
            quality=str(meta.get("quality") or "720p"),
            aspect=str(meta.get("aspect") or "16:9"),
        )
        project.ensure_dirs()
        return project

    def living_brief(self) -> LivingBrief:
        return LivingBrief.from_dict(self.living if isinstance(self.living, dict) else {})

    def set_living(self, brief: LivingBrief) -> None:
        self.living = brief.to_dict()
        self.save_meta()

    def set_cast(self, character_ids: list[str], *, face_lock_strength: float | None = None) -> None:
        ids: list[str] = []
        for cid in character_ids or []:
            text = str(cid).strip()
            if text and text not in ids:
                ids.append(text)
        self.active_cast = ids or ["alison", "bradley"]
        if face_lock_strength is not None:
            self.face_lock_strength = min(1.0, max(0.0, float(face_lock_strength)))
        self.save_meta()

    def set_lighting(self, lighting: str) -> None:
        from film_lab.lighting import SKIP_LABEL, is_lighting_skipped

        text = (lighting or "").strip()
        self.active_lighting = "" if is_lighting_skipped(text) or text == SKIP_LABEL else text
        self.save_meta()

    def set_filming_mode(self, mode: str) -> None:
        from film_lab.filming import normalize_mode

        self.filming_mode = normalize_mode(mode)
        self.save_meta()

    def set_quality(self, quality: str) -> None:
        from film_lab.quality import normalize_quality

        self.quality = normalize_quality(quality)
        self.save_meta()

    def set_aspect(self, aspect: str) -> None:
        from film_lab.constants import normalize_aspect

        self.aspect = normalize_aspect(aspect)
        self.save_meta()

    @classmethod
    def list_names(cls, *, data_root: Path | None = None) -> list[str]:
        root = data_root or default_data_root()
        if not root.exists():
            return []
        names = []
        for child in sorted(root.iterdir()):
            if child.is_dir() and (child / "project.json").exists():
                names.append(child.name)
        return names

    def ingest_files(self, sources: list[Path | str]) -> list[Path]:
        """Copy stills into the project. Returns destination paths."""
        self.ensure_dirs()
        written: list[Path] = []
        for raw in sources:
            src = Path(raw)
            if not src.is_file():
                continue
            if src.suffix.lower() not in IMAGE_SUFFIXES:
                continue
            dest = _unique_dest(self.stills_dir, src.name)
            shutil.copy2(src, dest)
            written.append(dest)
        return written

    def list_stills(self) -> list[Path]:
        if not self.stills_dir.exists():
            return []
        return sorted(
            p
            for p in self.stills_dir.iterdir()
            if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
        )

    def still_choices(self) -> list[str]:
        return [p.name for p in self.list_stills()]

    def resolve_still(self, name: str | None) -> Path | None:
        if not name:
            return None
        path = Path(name)
        if path.is_file():
            return path
        candidate = self.stills_dir / Path(name).name
        if candidate.is_file():
            return candidate
        return None

    def save_shot(self, shot: ShotCard) -> Path:
        self.ensure_dirs()
        path = self.shots_dir / f"{shot.id}.json"
        shot.to_json(path)
        return path

    def load_shot(self, shot_id: str) -> ShotCard:
        return ShotCard.from_json(self.shots_dir / f"{shot_id}.json")

    def list_shots(self) -> list[ShotCard]:
        if not self.shots_dir.exists():
            return []
        shots: list[ShotCard] = []
        for path in sorted(self.shots_dir.glob("*.json")):
            try:
                shots.append(ShotCard.from_json(path))
            except (OSError, ValueError, TypeError):
                continue
        shots.sort(key=lambda s: s.updated_at, reverse=True)
        return shots

    def shot_choices(self) -> list[str]:
        return [f"{s.id} — {s.name}" for s in self.list_shots()]

    def register_output(
        self,
        path: Path,
        *,
        shot: ShotCard | None = None,
        generator: str = "",
        duration: float | None = None,
    ) -> OutputClip:
        clip = OutputClip(
            path=str(path.resolve()),
            shot_id=shot.id if shot else None,
            shot_name=shot.name if shot else path.stem,
            generator=generator,
            created_at=utc_now(),
            duration=duration,
        )
        gallery = self.load_gallery()
        gallery = [c for c in gallery if c.path != clip.path]
        gallery.insert(0, clip)
        self._write_gallery(gallery)
        return clip

    def load_gallery(self) -> list[OutputClip]:
        if not self.gallery_path.exists():
            return self._scan_outputs()
        try:
            raw = json.loads(self.gallery_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return self._scan_outputs()
        clips: list[OutputClip] = []
        for item in raw:
            if not isinstance(item, dict) or "path" not in item:
                continue
            if Path(item["path"]).is_file():
                clips.append(
                    OutputClip(
                        path=item["path"],
                        shot_id=item.get("shot_id"),
                        shot_name=item.get("shot_name", ""),
                        generator=item.get("generator", ""),
                        created_at=item.get("created_at", ""),
                        duration=item.get("duration"),
                    )
                )
        known = {c.path for c in clips}
        for extra in self._scan_outputs():
            if extra.path not in known:
                clips.append(extra)
        return clips

    def _scan_outputs(self) -> list[OutputClip]:
        if not self.outputs_dir.exists():
            return []
        clips: list[OutputClip] = []
        for path in sorted(self.outputs_dir.iterdir(), reverse=True):
            if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES:
                clips.append(
                    OutputClip(
                        path=str(path.resolve()),
                        shot_name=path.stem,
                        created_at=utc_now(),
                    )
                )
        return clips

    def _write_gallery(self, clips: list[OutputClip]) -> None:
        payload: list[dict[str, Any]] = [
            {
                "path": c.path,
                "shot_id": c.shot_id,
                "shot_name": c.shot_name,
                "generator": c.generator,
                "created_at": c.created_at,
                "duration": c.duration,
            }
            for c in clips
        ]
        self.gallery_path.write_text(
            json.dumps(payload, indent=2) + "\n", encoding="utf-8"
        )


def _unique_dest(folder: Path, filename: str) -> Path:
    dest = folder / filename
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    n = 2
    while True:
        candidate = folder / f"{stem}_{n}{suffix}"
        if not candidate.exists():
            return candidate
        n += 1
