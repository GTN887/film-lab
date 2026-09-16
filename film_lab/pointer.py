"""Pointer / Go-to — Actor A walks to a locked room.

Click Actor A, point at a destination environment (bathroom, kitchen,
or any locked set), generate the go-to take, record it on Take Board.

Local stills + ffmpeg Ken Burns start→end. Not SVD. Not a 3D engine.
Stored under takes/ on this PC. Zero credits.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from film_lab.characters import (
    CharacterError,
    CharacterProfile,
    assert_adult_cast,
    load_selected_characters,
    resolve_refs,
)
from film_lab.envlock import load_env_lock, resolve_env_still
from film_lab.filming import is_explicit_mode
from film_lab.project import Project
from film_lab.setbuild import (
    BuiltSet,
    list_built_sets,
    place_actors_on_plate,
    resolve_built_set,
)
from film_lab.shot_card import ShotCard
from film_lab.util import new_id, slugify

ROOMS: tuple[str, ...] = (
    "bathroom",
    "kitchen",
    "bedroom",
    "hallway",
    "living room",
    "porch",
    "street",
    "bus stop",
)


class PointerError(RuntimeError):
    """Could not point Actor A at a room or generate the go-to take."""


@dataclass
class PointerTake:
    actor_id: str
    actor_name: str
    destination: str
    start: Path
    end: Path
    take: Path
    shot_id: str


def guess_room(*texts: str) -> str:
    blob = " ".join(t or "" for t in texts).lower()
    for room in ROOMS:
        if room in blob:
            return room
    return ""


def destination_choices(project: Project) -> list[str]:
    """Locked sets / rooms on this PC. Bathroom etc. come from set titles."""
    choices: list[str] = []
    seen: set[str] = set()
    for built in list_built_sets(project):
        room = guess_room(built.title, built.note, built.id)
        tag = f"{room} — " if room else ""
        label = f"{built.id} — {tag}{built.title}".strip()
        if label not in seen:
            choices.append(label)
            seen.add(label)
    lock = load_env_lock(project)
    if lock.locked and lock.still:
        room = guess_room(lock.note, lock.still)
        tag = f"{room} — " if room else ""
        label = f"lock:{lock.still} — {tag}current locked set"
        if label not in seen:
            choices.append(label)
    for still in project.list_stills():
        room = guess_room(still.stem)
        if not room:
            continue
        label = f"still:{still.name} — {room}"
        if label not in seen:
            choices.append(label)
            seen.add(label)
    return choices


def pointer_markdown() -> str:
    return (
        "**Pointer / Go-to:** click **Actor A**, point at a destination "
        "(bathroom or any locked set / room on this PC), then **Generate go-to take**. "
        "The walk-over records on **Take Board**. "
        "Uses locked plates in `data/projects/<name>/sets/` plus `takes/`. "
        "Local only. Zero credits. Not a 3D engine."
    )


def generate_go_to(
    project: Project,
    actor_choice: str | None,
    dest_choice: str | None,
    *,
    filming_mode: str = "",
    start_choice: str | None = None,
) -> PointerTake:
    actor = _resolve_actor(project, actor_choice)
    dest_plate, dest_label = _resolve_destination(project, dest_choice)
    start_plate = _resolve_start(project, start_choice, dest_plate, dest_choice)
    mode = filming_mode or getattr(project, "filming_mode", "")
    if is_explicit_mode(mode):
        try:
            assert_adult_cast(
                [actor],
                intimacy_mode="explicit sex" if is_explicit_mode(mode) else "",
                context="Pointer / Go-to",
            )
        except CharacterError as exc:
            raise PointerError(str(exc)) from exc

    refs = resolve_refs(project, actor)
    if not refs:
        raise PointerError(
            f"{actor.name} has no pinned still. Pin a Character Bible ref first."
        )
    figure = Image.open(refs[0])
    start_img = place_actors_on_plate(Image.open(start_plate).convert("RGB"), [figure])
    end_img = place_actors_on_plate(Image.open(dest_plate).convert("RGB"), [figure])

    project.ensure_dirs()
    pid = new_id()[:10]
    work = project.sets_dir / f"pointer-{pid}"
    work.mkdir(parents=True, exist_ok=True)
    start_path = work / "go-from.png"
    end_path = work / "go-to.png"
    start_img.save(start_path)
    end_img.save(end_path)
    for path in (start_path, end_path):
        copy = project.stills_dir / f"pointer-{pid}-{path.name}"
        shutil.copy2(path, copy)

    dest_mp4 = project.takes_dir / f"pointer-{pid}-{slugify(actor.name)}-to-{slugify(dest_label)}.mp4"
    _render_walk(start_path, end_path, dest_mp4, project)

    shot = ShotCard(
        name=f"{actor.name} → {dest_label}",
        start_frame=start_path.name,
        end_frame=end_path.name,
        duration=5.0,
        camera_move="orbit",
        director_intent=f"Pointer / Go-to: {actor.name} walks to {dest_label}.",
        body_motion_notes=f"{actor.name} goes to {dest_label}",
        character_ids=[actor.id],
    )
    project.save_shot(shot)
    return PointerTake(
        actor_id=actor.id,
        actor_name=actor.name,
        destination=dest_label,
        start=start_path,
        end=end_path,
        take=dest_mp4,
        shot_id=shot.id,
    )


def _resolve_actor(project: Project, choice: str | None) -> CharacterProfile:
    from film_lab.characters import list_characters

    text = (choice or "").strip()
    if not text:
        raise PointerError("Click Actor A (Character Bible) first.")
    cid = text.split(" — ", 1)[0].strip()
    profiles = load_selected_characters(project, [cid])
    if profiles:
        return profiles[0]
    rows = list_characters(project)
    if "actor a" in text.lower() and rows:
        return rows[0]
    for profile in rows:
        if profile.id == cid or profile.name.lower() in text.lower():
            return profile
    raise PointerError("Click Actor A — pick a Character Bible person.")


def _resolve_destination(project: Project, choice: str | None) -> tuple[Path, str]:
    text = (choice or "").strip()
    if not text:
        raise PointerError(
            "Point at a destination environment (bathroom or any locked set / room)."
        )
    if text.startswith("still:"):
        name = text.split(" — ", 1)[0].split(":", 1)[1].strip()
        path = project.resolve_still(name)
        if path and path.is_file():
            return path, guess_room(text) or Path(name).stem
        raise PointerError(f"Still `{name}` is missing.")
    if text.startswith("lock:"):
        lock = load_env_lock(project)
        path = resolve_env_still(project, lock)
        if path and path.is_file():
            return path, guess_room(lock.note, text) or "locked set"
        raise PointerError("No current locked set. Build one on 3D Set first.")
    built = resolve_built_set(project, text)
    if built is None:
        # title-only match (bathroom)
        room = guess_room(text) or text.lower()
        for item in list_built_sets(project):
            if room and room in f"{item.title} {item.note} {item.id}".lower():
                built = item
                break
    if built is None:
        raise PointerError(
            "That room is not on this PC yet. Build a locked set (bathroom, kitchen, …) on 3D Set."
        )
    path = _set_plate(project, built)
    label = guess_room(built.title, built.note, text) or built.title
    return path, label


def _resolve_start(
    project: Project,
    start_choice: str | None,
    dest_plate: Path,
    dest_choice: str | None,
) -> Path:
    if (start_choice or "").strip() and (start_choice or "").strip() != (dest_choice or "").strip():
        path, _ = _resolve_destination(project, start_choice)
        if path.resolve() != dest_plate.resolve():
            return path
    lock = resolve_env_still(project)
    if lock and lock.is_file() and lock.resolve() != dest_plate.resolve():
        return lock
    for built in list_built_sets(project):
        path = _set_plate(project, built)
        if path.resolve() != dest_plate.resolve():
            return path
    # Same room: leave from a look-left crop so the take still travels.
    image = Image.open(dest_plate).convert("RGB")
    width, height = image.size
    crop = image.crop((0, 0, max(8, int(width * 0.72)), height))
    leave = dest_plate.parent / "go-leave.png"
    crop.save(leave)
    return leave


def _set_plate(project: Project, built: BuiltSet) -> Path:
    folder = project.sets_dir / built.id
    for name in (built.expanded, "expanded.png", f"{built.id}-plate.png"):
        path = folder / name
        if path.is_file():
            return path
    if built.views:
        path = folder / built.views[0]
        if path.is_file():
            return path
    raise PointerError(f"Locked set `{built.id}` has no plate on this PC.")


def _render_walk(start: Path, end: Path, dest: Path, project: Project) -> Path:
    from film_lab.generators.base import GenerateJob, GeneratorUnavailable
    from film_lab.generators.ken_burns import KenBurnsGenerator

    dest.parent.mkdir(parents=True, exist_ok=True)
    shot = ShotCard(
        name="go-to",
        duration=5.0,
        camera_move="orbit",
        subject_motion_strength=0.45,
    )
    try:
        KenBurnsGenerator().generate(
            GenerateJob(
                shot=shot,
                start_path=start,
                end_path=end,
                output_path=dest,
            )
        )
    except GeneratorUnavailable as exc:
        raise PointerError(
            f"Go-to take needs ffmpeg on this PC. {exc}"
        ) from exc
    if not dest.is_file():
        raise PointerError("Go-to take did not write a clip.")
    copy = project.outputs_dir / dest.name
    if dest.resolve() != copy.resolve():
        shutil.copy2(dest, copy)
    project.register_output(dest, generator="pointer-go-to", duration=5.0)
    return dest
