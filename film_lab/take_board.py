"""Creator-facing Take Board operations backed by persistent production records."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from film_lab.production import ProductionStore, Take
from film_lab.project import Project
from film_lab.stitch import stitch_clips


class TakeBoardError(RuntimeError):
    pass


def _store(project: Project) -> ProductionStore:
    return ProductionStore(project)


def take_cards(project: Project, *, shot_id: str | None = None) -> list[dict[str, Any]]:
    """Return durable Take Board cards; missing media is reported, never hidden."""
    cards: list[dict[str, Any]] = []
    for take in _store(project).list_takes(shot_id=shot_id):
        row = asdict(take)
        row["media_exists"] = Path(take.media_path).is_file()
        cards.append(row)
    return cards


def select_take(project: Project, take_id: str) -> Take:
    take = _store(project).get_take(take_id)
    if not Path(take.media_path).is_file():
        raise TakeBoardError("Cannot select a Take whose video file is missing.")
    return _store(project).set_status(take_id, "selected")


def review_take(project: Project, take_id: str) -> Take:
    return _store(project).set_status(take_id, "review")


def reject_take(project: Project, take_id: str) -> Take:
    return _store(project).set_status(take_id, "rejected")


def save_take_direction(project: Project, take_id: str, *, director_notes: str, tags: list[str] | None = None) -> Take:
    return _store(project).update_notes(take_id, director_notes=director_notes, tags=tags or [])


def selected_take_for_shot(project: Project, shot_id: str) -> Take | None:
    selected = [t for t in _store(project).list_takes(shot_id=shot_id, existing_media_only=True) if t.status == "selected"]
    return selected[0] if selected else None


def export_selected_to_cinema(project: Project, *, filename: str = "film_lab_cinema.mp4") -> Path:
    """Render selected Takes in deterministic scene/shot order to a real MP4.

    One selected clip is copied without transcoding. Multiple clips use Film Lab's
    existing ffmpeg crossfade stitcher. No output file means no success.
    """
    manifest = _store(project).cinema_manifest()
    if not manifest:
        raise TakeBoardError("Cinema needs at least one Selected Take with existing video media.")
    manifest.sort(key=lambda x: (str(x.get("scene_id", "")), str(x.get("shot_id", "")), str(x.get("take_id", ""))))
    clips = [Path(x["media_path"]) for x in manifest]
    dest = project.outputs_dir / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    if len(clips) == 1:
        import shutil
        shutil.copy2(clips[0], dest)
    else:
        stitch_clips(clips, dest)
    if not dest.is_file() or dest.stat().st_size <= 0:
        raise TakeBoardError("Cinema export did not produce a usable video file.")
    project.register_output(dest, generator="cinema-selected-takes")
    return dest
