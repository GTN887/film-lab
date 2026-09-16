"""Take Board — seed / camera / motion variants from one shot. Local only."""

from __future__ import annotations

import re
from pathlib import Path

from film_lab.constants import CAMERA_MOVES
from film_lab.project import Project
from film_lab.shot_card import ShotCard, new_shot_id

_TAKE_SUFFIX = re.compile(r" · take \d+$")


def expand_takes(
    project: Project,
    source: ShotCard,
    *,
    count: int = 3,
    vary_seed: bool = True,
    vary_camera: bool = True,
    vary_motion: bool = False,
) -> list[ShotCard]:
    """Clone a shot into N local variants. Does not generate video."""
    n = max(2, min(8, int(count)))
    cameras = list(CAMERA_MOVES)
    start_cam = cameras.index(source.camera_move) if source.camera_move in cameras else 0
    base_seed = int(source.seed) if source.seed is not None else 1049
    base_motion = float(source.subject_motion_strength)
    created: list[ShotCard] = []
    for i in range(n):
        data = source.to_dict()
        data["id"] = new_shot_id()
        data["name"] = f"{source.name} · take {i + 1}"
        if vary_camera:
            data["camera_move"] = cameras[(start_cam + i) % len(cameras)]
        if vary_seed:
            data["seed"] = base_seed + (i * 17)
        if vary_motion:
            data["subject_motion_strength"] = min(1.0, max(0.05, base_motion + (i - 1) * 0.12))
        shot = ShotCard.from_dict(data)
        project.save_shot(shot)
        created.append(shot)
    return created


def base_take_name(name: str) -> str:
    return _TAKE_SUFFIX.sub("", (name or "").strip()) or "Untitled shot"


def shot_has_output(project: Project, shot_id: str | None) -> bool:
    if not shot_id:
        return False
    return any(
        c.shot_id == shot_id and Path(c.path).is_file() for c in project.load_gallery()
    )


def fork_take(project: Project, source: ShotCard, *, seed: int | None = None) -> ShotCard:
    """Keep the old take. New shot card + new seed for Regenerate."""
    data = source.to_dict()
    data["id"] = new_shot_id()
    root = base_take_name(source.name)
    n = 1 + sum(1 for s in project.list_shots() if base_take_name(s.name) == root)
    data["name"] = f"{root} · take {n}"
    if seed is not None:
        data["seed"] = int(seed)
    shot = ShotCard.from_dict(data)
    project.save_shot(shot)
    return shot


def take_gallery_items(project: Project) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for clip in project.load_gallery():
        path = Path(clip.path)
        if path.is_file():
            label = clip.shot_name or path.name
            items.append((str(path), label))
    return items
