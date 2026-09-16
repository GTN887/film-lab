"""Fountain-ish scene desk: heading, action, dialogue, director notes."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from film_lab.project import Project
from film_lab.util import new_id, read_json, slugify, utc_now, write_json

LINE_KINDS = ("dialogue",)
REEL_STATUSES = ("idea", "blocked", "generated", "locked")


@dataclass
class DialogueLine:
    character: str
    parenthetical: str = ""
    text: str = ""

    def to_fountain(self) -> str:
        chunks = [self.character.strip().upper()]
        if self.parenthetical.strip():
            chunks.append(f"({self.parenthetical.strip()})")
        chunks.append(self.text.rstrip())
        return "\n".join(chunks)


@dataclass
class Scene:
    id: str
    heading: str = "INT. BEDROOM - NIGHT"
    action: str = ""
    lines: list[DialogueLine] = field(default_factory=list)
    director_notes: str = ""
    shot_ids: list[str] = field(default_factory=list)
    status: str = "idea"
    primary_genre: str = "Romance"
    secondary_genres: list[str] = field(default_factory=list)
    custom_genre_tags: list[str] = field(default_factory=list)
    tropes_checklist: str = ""
    living: dict = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        parsed: list[DialogueLine] = []
        for line in self.lines:
            if isinstance(line, DialogueLine):
                parsed.append(line)
            elif isinstance(line, dict):
                parsed.append(
                    DialogueLine(
                        character=str(line.get("character", "")),
                        parenthetical=str(line.get("parenthetical", "")),
                        text=str(line.get("text", "")),
                    )
                )
        self.lines = parsed
        if self.status not in REEL_STATUSES:
            self.status = "idea"
        if not isinstance(self.living, dict):
            self.living = {}

    def living_brief(self):
        from film_lab.living import LivingBrief

        return LivingBrief.from_dict(self.living)

    def set_living(self, brief) -> None:
        self.living = brief.to_dict() if brief is not None else {}

    def touch(self) -> None:
        self.updated_at = utc_now()

    def label(self) -> str:
        return f"{self.id} — {self.heading}"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload

    def to_fountain(self, *, title: str = "") -> str:
        blocks: list[str] = []
        if title:
            blocks.append(f"Title: {title}")
            blocks.append("Credit: private local study")
            blocks.append("")
        blocks.append(self.heading.strip().upper())
        blocks.append("")
        if self.action.strip():
            blocks.append(self.action.strip())
            blocks.append("")
        for line in self.lines:
            if not line.character.strip() and not line.text.strip():
                continue
            blocks.append(line.to_fountain())
            blocks.append("")
        if self.director_notes.strip():
            blocks.append(f"= DIRECTOR NOTES")
            blocks.append(self.director_notes.strip())
            blocks.append("")
        genre_bits = []
        if self.primary_genre:
            genre_bits.append(self.primary_genre)
        genre_bits.extend(s for s in self.secondary_genres if s and s != self.primary_genre)
        genre_bits.extend(self.custom_genre_tags)
        if genre_bits:
            blocks.append("= GENRE")
            blocks.append(" | ".join(genre_bits))
            if self.tropes_checklist.strip():
                blocks.append(self.tropes_checklist.strip())
            blocks.append("")
        return "\n".join(blocks).rstrip() + "\n"

    def to_plain_text(self) -> str:
        return self.to_fountain()


def scenes_dir(project: Project) -> Path:
    return project.root / "scenes"


def save_scene(project: Project, scene: Scene) -> Path:
    project.ensure_dirs()
    scene.touch()
    path = scenes_dir(project) / f"{scene.id}.json"
    write_json(path, scene.to_dict())
    return path


def load_scene(project: Project, scene_id: str) -> Scene:
    data = read_json(scenes_dir(project) / f"{scene_id}.json")
    if not isinstance(data, dict):
        raise ValueError(f"Scene {scene_id} is not a JSON object")
    return Scene(**{k: data[k] for k in Scene.__dataclass_fields__ if k in data})


def list_scenes(project: Project) -> list[Scene]:
    folder = scenes_dir(project)
    if not folder.exists():
        return []
    scenes: list[Scene] = []
    for path in sorted(folder.glob("*.json")):
        try:
            scenes.append(load_scene(project, path.stem))
        except (OSError, TypeError, ValueError):
            continue
    return scenes


def scene_choices(project: Project) -> list[str]:
    return [s.label() for s in list_scenes(project)]


def link_shot(project: Project, scene_id: str, shot_id: str) -> Scene:
    scene = load_scene(project, scene_id)
    if shot_id not in scene.shot_ids:
        scene.shot_ids.append(shot_id)
    save_scene(project, scene)
    return scene


def export_scene(project: Project, scene: Scene, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    suffix = dest.suffix.lower()
    if suffix in {".fountain", ".txt"}:
        dest.write_text(scene.to_fountain(title=project.name), encoding="utf-8")
        return dest
    if suffix == ".pdf":
        from film_lab.pdf_export import write_simple_pdf

        write_simple_pdf(scene.to_fountain(title=project.name), dest)
        return dest
    raise ValueError("Export must be .fountain, .txt, or .pdf")


def lines_from_table(rows: list[list[Any]] | None) -> list[DialogueLine]:
    lines: list[DialogueLine] = []
    if rows is None:
        return lines
    if hasattr(rows, "values"):
        rows = rows.values.tolist()
    if not rows:
        return lines
    for row in rows:
        if not row:
            continue
        character = str(row[0] or "").strip()
        parenthetical = str(row[1] or "").strip() if len(row) > 1 else ""
        text = str(row[2] or "").strip() if len(row) > 2 else ""
        if character or text:
            lines.append(DialogueLine(character=character, parenthetical=parenthetical, text=text))
    return lines


def lines_to_table(lines: list[DialogueLine]) -> list[list[str]]:
    if not lines:
        return [["", "", ""]]
    return [[ln.character, ln.parenthetical, ln.text] for ln in lines]


def new_scene(heading: str = "INT. BEDROOM - NIGHT") -> Scene:
    return Scene(id=new_id(), heading=heading)
