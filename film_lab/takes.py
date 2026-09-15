"""Persistent Scene -> Shot -> Take records for Film Lab.

This module is deliberately engine-agnostic. Motion generators and imports hand a real
video file to :class:`TakeStore`; Take Board and Cinema consume the persisted record.
"""
from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from film_lab.project import Project, VIDEO_SUFFIXES, utc_now

TakeStatus = Literal["Review", "Selected", "Rejected"]
_VALID_STATUSES = {"Review", "Selected", "Rejected"}


@dataclass
class Take:
    id: str
    scene_id: str
    shot_id: str
    media_path: str
    status: TakeStatus = "Review"
    created_at: str = field(default_factory=utc_now)
    notes: str = ""
    tags: list[str] = field(default_factory=list)
    generator: str = ""
    model: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Take":
        status = str(raw.get("status") or "Review")
        if status not in _VALID_STATUSES:
            status = "Review"
        return cls(
            id=str(raw["id"]), scene_id=str(raw["scene_id"]), shot_id=str(raw["shot_id"]),
            media_path=str(raw["media_path"]), status=status, created_at=str(raw.get("created_at") or utc_now()),
            notes=str(raw.get("notes") or ""), tags=[str(x) for x in raw.get("tags", []) if str(x).strip()],
            generator=str(raw.get("generator") or ""), model=str(raw.get("model") or ""),
            metadata=dict(raw.get("metadata") or {}),
        )


class TakeStore:
    """JSON persistence with exactly-one-selected-Take semantics per shot."""

    def __init__(self, project: Project):
        self.project = project
        self.project.ensure_dirs()
        self.index_path = self.project.takes_dir / "takes.json"

    def list(self, *, scene_id: str | None = None, shot_id: str | None = None) -> list[Take]:
        takes = self._load()
        if scene_id is not None:
            takes = [t for t in takes if t.scene_id == scene_id]
        if shot_id is not None:
            takes = [t for t in takes if t.shot_id == shot_id]
        return sorted(takes, key=lambda t: t.created_at, reverse=True)

    def get(self, take_id: str) -> Take:
        for take in self._load():
            if take.id == take_id:
                return take
        raise KeyError(f"Unknown Take: {take_id}")

    def add_video(self, source: Path | str, *, scene_id: str, shot_id: str,
                  generator: str = "import", model: str = "", notes: str = "",
                  tags: list[str] | None = None, metadata: dict[str, Any] | None = None,
                  copy_media: bool = True) -> Take:
        src = Path(source)
        if not src.is_file() or src.suffix.lower() not in VIDEO_SUFFIXES:
            raise ValueError("A real supported video file is required to create a Take.")
        if not scene_id.strip() or not shot_id.strip():
            raise ValueError("scene_id and shot_id are required.")
        take_id = uuid.uuid4().hex[:12]
        if copy_media:
            media_dir = self.project.takes_dir / "media" / scene_id / shot_id
            media_dir.mkdir(parents=True, exist_ok=True)
            dest = media_dir / f"{take_id}{src.suffix.lower()}"
            shutil.copy2(src, dest)
        else:
            dest = src.resolve()
        take = Take(
            id=take_id, scene_id=scene_id.strip(), shot_id=shot_id.strip(), media_path=str(dest.resolve()),
            notes=notes.strip(), tags=self._clean_tags(tags or []), generator=generator.strip(), model=model.strip(),
            metadata=dict(metadata or {}),
        )
        takes = self._load(); takes.append(take); self._save(takes)
        return take

    def update(self, take_id: str, *, status: TakeStatus | None = None, notes: str | None = None,
               tags: list[str] | None = None) -> Take:
        takes = self._load()
        target = next((t for t in takes if t.id == take_id), None)
        if target is None:
            raise KeyError(f"Unknown Take: {take_id}")
        if status is not None:
            if status not in _VALID_STATUSES:
                raise ValueError(f"Invalid Take status: {status}")
            if status == "Selected":
                for other in takes:
                    if other.id != target.id and other.scene_id == target.scene_id and other.shot_id == target.shot_id and other.status == "Selected":
                        other.status = "Review"
            target.status = status
        if notes is not None:
            target.notes = notes.strip()
        if tags is not None:
            target.tags = self._clean_tags(tags)
        self._save(takes)
        return target

    def selected(self, *, scene_id: str, shot_id: str) -> Take | None:
        return next((t for t in self._load() if t.scene_id == scene_id and t.shot_id == shot_id and t.status == "Selected"), None)

    def cinema_manifest(self, *, scene_id: str | None = None) -> list[dict[str, str]]:
        """Return selected real media for Cinema; this does not pretend to render/export."""
        selected = [t for t in self._load() if t.status == "Selected" and (scene_id is None or t.scene_id == scene_id)]
        selected.sort(key=lambda t: (t.scene_id, t.shot_id, t.created_at))
        return [{"take_id": t.id, "scene_id": t.scene_id, "shot_id": t.shot_id, "media_path": t.media_path} for t in selected if Path(t.media_path).is_file()]

    def _load(self) -> list[Take]:
        if not self.index_path.exists():
            return []
        try:
            raw = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return [Take.from_dict(item) for item in raw if isinstance(item, dict) and {"id", "scene_id", "shot_id", "media_path"} <= item.keys()]

    def _save(self, takes: list[Take]) -> None:
        self.project.ensure_dirs()
        tmp = self.index_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps([asdict(t) for t in takes], indent=2) + "\n", encoding="utf-8")
        tmp.replace(self.index_path)

    @staticmethod
    def _clean_tags(tags: list[str]) -> list[str]:
        out: list[str] = []
        for tag in tags:
            value = str(tag).strip()
            if value and value not in out:
                out.append(value)
        return out
