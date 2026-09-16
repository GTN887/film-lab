"""3D Set desk — virtual set notes, not a 3D engine.

Place Character Bible roles on a set, pick camera orbit / push / aerial,
and fold outdoor plates into World Note + Enhance → Animate. Practical
path: multi-angle set notes → regenerate. Deeper realtime 3D is future
work and is not claimed here. Zero credits.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from film_lab.filming import CAST_ROLES, ROLE_ADULT, normalize_role
from film_lab.project import Project
from film_lab.util import write_json

SET_FILE = "set_notes.json"

SET_CAMERAS: tuple[str, ...] = (
    "orbit",
    "slow push-in",
    "aerial",
    "drone",
    "wide outdoor",
)
DEFAULT_SET_CAMERA = "orbit"

OUTDOOR_PLATES: tuple[str, ...] = (
    "none",
    "street",
    "sky",
    "wide outdoor",
    "bus stop",
    "walk home",
    "drone aerial",
)
DEFAULT_OUTDOOR = "none"

_SET_LINE = r"^SET NOTE \(3D set / camera\):.*$"


class SetDeskError(ValueError):
    """Invalid 3D Set note."""


@dataclass
class CharacterMark:
    character_id: str
    character_name: str
    role: str = ROLE_ADULT
    mark: str = ""

    def bit(self) -> str:
        where = (self.mark or "").strip()
        role = normalize_role(self.role)
        label = f"{self.character_name} ({role})"
        if where:
            return f"{label} at {where}"
        return label


@dataclass
class SetNote:
    camera: str = DEFAULT_SET_CAMERA
    outdoor: str = DEFAULT_OUTDOOR
    set_description: str = ""
    placements: list[CharacterMark] = field(default_factory=list)

    def line(self) -> str:
        cam = (self.camera or DEFAULT_SET_CAMERA).strip() or DEFAULT_SET_CAMERA
        bits = [f"camera {cam}"]
        outdoor = (self.outdoor or "").strip()
        if outdoor and outdoor != "none":
            bits.append(f"outdoor plate {outdoor}")
        desc = " ".join((self.set_description or "").split())
        if desc:
            bits.append(desc)
        marks = [m.bit() for m in self.placements if m.character_id or m.character_name]
        if marks:
            bits.append("marks: " + "; ".join(marks))
        return f"SET NOTE (3D set / camera): {'; '.join(bits)}"

    def is_empty(self) -> bool:
        desc = (self.set_description or "").strip()
        outdoor = (self.outdoor or "").strip()
        marks = [m for m in self.placements if (m.mark or "").strip()]
        return not desc and (not outdoor or outdoor == "none") and not marks

    def to_dict(self) -> dict[str, Any]:
        return {
            "camera": self.camera,
            "outdoor": self.outdoor,
            "set_description": self.set_description,
            "placements": [asdict(m) for m in self.placements],
        }


def set_path(project: Project) -> Path:
    return project.root / SET_FILE


def load_set_note(project: Project) -> SetNote:
    path = set_path(project)
    if not path.is_file():
        return SetNote()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return SetNote()
    if not isinstance(data, dict):
        return SetNote()
    placements: list[CharacterMark] = []
    raw_marks = data.get("placements") or []
    if isinstance(raw_marks, list):
        for item in raw_marks:
            if not isinstance(item, dict):
                continue
            cid = str(item.get("character_id") or "").strip()
            name = str(item.get("character_name") or cid).strip()
            if not cid and not name:
                continue
            placements.append(
                CharacterMark(
                    character_id=cid or name,
                    character_name=name or cid,
                    role=normalize_role(str(item.get("role") or ROLE_ADULT)),
                    mark=str(item.get("mark") or ""),
                )
            )
    camera = str(data.get("camera") or DEFAULT_SET_CAMERA)
    if camera not in SET_CAMERAS:
        camera = DEFAULT_SET_CAMERA
    outdoor = str(data.get("outdoor") or DEFAULT_OUTDOOR)
    if outdoor not in OUTDOOR_PLATES:
        outdoor = DEFAULT_OUTDOOR
    return SetNote(
        camera=camera,
        outdoor=outdoor,
        set_description=str(data.get("set_description") or ""),
        placements=placements,
    )


def save_set_note(project: Project, note: SetNote) -> Path:
    project.ensure_dirs()
    path = set_path(project)
    write_json(path, note.to_dict())
    return path


def set_shot_bits(note: SetNote) -> list[str]:
    if note.is_empty() and note.camera == DEFAULT_SET_CAMERA:
        return []
    text = note.line().replace("SET NOTE (3D set / camera): ", "3D set: ")
    return [text] if text else []


def set_markdown(note: SetNote | None = None) -> str:
    body = (note.line() + "\n\n") if note and not note.is_empty() else ""
    return (
        f"{body}"
        "3D Set Desk builds a **LOCKED Environment from a photo** "
        "(invent missing edges, then look-around / zoom / aerial) "
        "plus virtual set notes — not a realtime 3D engine. "
        "Optional: place Character Bible actors on that plate. "
        "On this PC: `data/projects/<name>/sets/` · `stills/` · `takes/` "
        "(offline, deletable). "
        "Place bible roles (Mom, Dad, Teen, Adult, Child, Infant), pick "
        "**orbit / push / aerial / drone / wide outdoor**, and apply. "
        "Notes fold into Enhance → Pose → Animate, then **Regenerate** for a new angle. "
        "Outdoor plates (street, sky, bus stop, walk home) ride World Note weather too. "
        "Regular / story may include under-18 roles for **non-sexual** everyday filming. "
        "18+ Explicit stays adult-only."
    )


def build_set_note(
    *,
    camera: str,
    outdoor: str,
    set_description: str,
    placements: list[CharacterMark] | None = None,
) -> SetNote:
    cam = (camera or DEFAULT_SET_CAMERA).strip()
    if cam not in SET_CAMERAS:
        raise SetDeskError(f"Camera must be one of: {', '.join(SET_CAMERAS)}.")
    plate = (outdoor or DEFAULT_OUTDOOR).strip() or DEFAULT_OUTDOOR
    if plate not in OUTDOOR_PLATES:
        raise SetDeskError(f"Outdoor plate must be one of: {', '.join(OUTDOOR_PLATES)}.")
    return SetNote(
        camera=cam,
        outdoor=plate,
        set_description=(set_description or "").strip(),
        placements=list(placements or []),
    )


def role_choices() -> list[str]:
    return list(CAST_ROLES)
