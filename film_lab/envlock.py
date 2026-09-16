"""Environment / Set lock — World Note + 3D Set reuse one locked plate.

Lock a set still (and optional style/scene ref). Img2vid seeds from that
still when the shot has no start frame. Regenerate keeps the World lock.
ControlNet depth/canny/softedge and IP-Adapter scene refs are probed
stubs on the RX 5600 XT — never a fake rewrite. Zero credits.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from film_lab.project import Project
from film_lab.util import write_json

ENV_FILE = "env_lock.json"
ENV_REFS = "env_refs"

GEO_DEPTH = "depth"
GEO_CANNY = "canny"
GEO_SOFTEDGE = "softedge"
GEO_NONE = "none"
ENV_GEOMETRY: tuple[str, ...] = (GEO_DEPTH, GEO_CANNY, GEO_SOFTEDGE, GEO_NONE)
DEFAULT_GEOMETRY = GEO_DEPTH
DEFAULT_ENV_STRENGTH = 0.45

_ENV_LINE_PREFIX = "ENV LOCK (set / world):"


@dataclass
class EnvLock:
    still: str = ""
    style_ref: str = ""
    geometry: str = DEFAULT_GEOMETRY
    strength: float = DEFAULT_ENV_STRENGTH
    note: str = ""
    locked: bool = False

    def __post_init__(self) -> None:
        geo = (self.geometry or DEFAULT_GEOMETRY).strip()
        self.geometry = geo if geo in ENV_GEOMETRY else DEFAULT_GEOMETRY
        try:
            self.strength = float(self.strength)
        except (TypeError, ValueError):
            self.strength = DEFAULT_ENV_STRENGTH
        self.strength = min(1.0, max(0.0, self.strength))
        self.still = (self.still or "").strip()
        self.style_ref = (self.style_ref or "").strip()
        self.note = (self.note or "").strip()
        self.locked = bool(self.locked) and bool(self.still or self.note)

    def line(self) -> str:
        if not self.locked:
            return ""
        bits = ["hold the same set"]
        if self.still:
            bits.append(f"locked still {self.still}")
        if self.style_ref:
            bits.append(f"style ref {self.style_ref}")
        if self.geometry != GEO_NONE:
            bits.append(f"geometry {self.geometry}")
        bits.append(f"env strength {self.strength:.2f}")
        if self.note:
            bits.append(self.note)
        return f"{_ENV_LINE_PREFIX} {'; '.join(bits)}"

    def is_empty(self) -> bool:
        return not self.locked

    def to_dict(self) -> dict[str, Any]:
        return {
            "still": self.still,
            "style_ref": self.style_ref,
            "geometry": self.geometry,
            "strength": self.strength,
            "note": self.note,
            "locked": self.locked,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> EnvLock:
        raw = data if isinstance(data, dict) else {}
        return cls(
            still=str(raw.get("still") or ""),
            style_ref=str(raw.get("style_ref") or ""),
            geometry=str(raw.get("geometry") or DEFAULT_GEOMETRY),
            strength=raw.get("strength", DEFAULT_ENV_STRENGTH),
            note=str(raw.get("note") or ""),
            locked=bool(raw.get("locked")),
        )


def env_path(project: Project) -> Path:
    return project.root / ENV_FILE


def env_refs_dir(project: Project) -> Path:
    return project.root / ENV_REFS


def load_env_lock(project: Project) -> EnvLock:
    path = env_path(project)
    if not path.is_file():
        return EnvLock()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return EnvLock()
    return EnvLock.from_dict(data if isinstance(data, dict) else {})


def save_env_lock(project: Project, lock: EnvLock) -> Path:
    project.ensure_dirs()
    env_refs_dir(project).mkdir(parents=True, exist_ok=True)
    path = env_path(project)
    write_json(path, lock.to_dict())
    return path


def resolve_env_still(project: Project, lock: EnvLock | None = None) -> Path | None:
    lock = lock or load_env_lock(project)
    if not lock.locked or not lock.still:
        return None
    for folder in (project.stills_dir, env_refs_dir(project)):
        path = folder / lock.still
        if path.is_file():
            return path
    resolved = project.resolve_still(lock.still)
    return resolved if resolved and resolved.is_file() else None


def pin_env_file(project: Project, source: Path | str, *, kind: str = "still") -> str:
    src = Path(source)
    if not src.is_file():
        raise ValueError(f"Missing {kind} file: {src}")
    dest_dir = env_refs_dir(project)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name
    if src.resolve() != dest.resolve():
        shutil.copy2(src, dest)
    ingested = project.ingest_files([dest])
    return ingested[0].name if ingested else dest.name


def apply_env_lock(
    project: Project,
    *,
    still: Path | str | None = None,
    style_ref: Path | str | None = None,
    geometry: str = DEFAULT_GEOMETRY,
    strength: float = DEFAULT_ENV_STRENGTH,
    note: str = "",
) -> EnvLock:
    lock = load_env_lock(project)
    if still:
        lock.still = pin_env_file(project, still, kind="set still")
    if style_ref:
        lock.style_ref = pin_env_file(project, style_ref, kind="style ref")
    lock.geometry = geometry
    lock.strength = strength
    if note:
        lock.note = note
    lock.locked = bool(lock.still or lock.note)
    if not lock.locked:
        raise ValueError("Drop a set still (or write a set note) before Apply Environment lock.")
    save_env_lock(project, lock)
    return lock


def env_shot_bits(lock: EnvLock) -> list[str]:
    line = lock.line()
    if not line:
        return []
    return [line.replace(f"{_ENV_LINE_PREFIX} ", "environment lock: ")]


def env_gallery_items(project: Project, lock: EnvLock | None = None) -> list[tuple[str, str]]:
    lock = lock or load_env_lock(project)
    items: list[tuple[str, str]] = []
    for name, label in ((lock.still, "Set still"), (lock.style_ref, "Style ref")):
        if not name:
            continue
        path = resolve_env_still(project, EnvLock(still=name, locked=True)) if name == lock.still else None
        if path is None:
            for folder in (project.stills_dir, env_refs_dir(project)):
                candidate = folder / name
                if candidate.is_file():
                    path = candidate
                    break
        if path and path.is_file():
            items.append((str(path), label))
    return items


def env_markdown(lock: EnvLock | None = None) -> str:
    body = (lock.line() + "\n\n") if lock and lock.locked else ""
    return (
        f"{body}"
        "Environment / Set lock: one locked plate reused by **World Note** and **3D Set**. "
        "Img2vid seeds from that still when the shot has no start frame. "
        "**Regenerate** keeps the World lock. "
        "IP-Adapter scene + ControlNet depth/canny/softedge stay stubs until Comfy lists those nodes — "
        "Film Lab will not fake a rewrite. RX 5600 XT: lightweight first; OOM → drop Quality."
    )
