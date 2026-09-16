"""Copy bundled shot cards, characters, and scenes into a project."""

from __future__ import annotations

from pathlib import Path

from film_lab.characters import CharacterProfile, save_character, seed_alison_bradley
from film_lab.luts import ensure_stock_luts
from film_lab.project import Project
from film_lab.script import Scene, save_scene
from film_lab.shot_card import ShotCard


def examples_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "examples" / "alison_bradley"


def import_example_shots(project: Project, source: Path | None = None) -> list[ShotCard]:
    folder = source or examples_dir()
    imported: list[ShotCard] = []
    if not folder.is_dir():
        return imported
    project.ensure_dirs()
    for path in sorted(folder.glob("*.json")):
        shot = ShotCard.from_json(path)
        dest = project.shots_dir / f"{shot.id}.json"
        if dest.exists():
            continue
        project.save_shot(shot)
        imported.append(shot)
    return imported


def import_example_characters(project: Project) -> list[CharacterProfile]:
    seeded = seed_alison_bradley(project)
    folder = examples_dir() / "characters"
    if not folder.is_dir():
        return seeded
    extra: list[CharacterProfile] = []
    for path in sorted(folder.glob("*.json")):
        profile = _load_character_file(path)
        dest = project.root / "characters" / profile.id / "profile.json"
        if dest.exists():
            continue
        save_character(project, profile)
        extra.append(profile)
    return seeded + extra


def _load_character_file(path: Path) -> CharacterProfile:
    from film_lab.util import read_json

    data = read_json(path)
    return CharacterProfile(**{k: data[k] for k in CharacterProfile.__dataclass_fields__ if k in data})


def import_example_scenes(project: Project) -> list[Scene]:
    folder = examples_dir() / "scenes"
    imported: list[Scene] = []
    if not folder.is_dir():
        return imported
    for path in sorted(folder.glob("*.json")):
        from film_lab.util import read_json

        data = read_json(path)
        scene = Scene(**{k: data[k] for k in Scene.__dataclass_fields__ if k in data})
        dest = project.root / "scenes" / f"{scene.id}.json"
        if dest.exists():
            continue
        save_scene(project, scene)
        imported.append(scene)
    return imported


def import_studio_bundle(project: Project) -> str:
    shots = import_example_shots(project)
    chars = import_example_characters(project)
    scenes = import_example_scenes(project)
    ensure_stock_luts()
    return (
        f"Imported {len(shots)} shot(s), {len(chars)} character(s), {len(scenes)} scene(s). "
        "Stock LUTs are in data/luts/."
    )
