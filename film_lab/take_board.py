"""Creator-facing Take Board operations backed by persistent production records."""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from film_lab.production import ProductionStore, Take
from film_lab.project import Project
from film_lab.cinema_export import export_selected


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


def save_audio_cut_intent(project: Project, take_id: str, *, style: str, j_cut_lead_s: float = 0.0, l_cut_tail_s: float = 0.0, picture_in_s: float = 0.0, picture_out_s: float = 0.0) -> Take:
    """Persist explicit Director timing on the incoming Take for its prior cut."""
    style = str(style or "HARD_CUT").upper()
    if style not in {"HARD_CUT", "J_CUT", "L_CUT", "J_L_CUT"}:
        raise TakeBoardError("Audio cut style must be Hard, J, L, or J+L.")
    def bounded(value: float) -> float:
        try: seconds = float(value)
        except (TypeError, ValueError): raise TakeBoardError("Audio cut timing must be numeric.")
        if not 0.0 <= seconds <= 2.0:
            raise TakeBoardError("Audio cut timing must be between 0 and 2 seconds.")
        return seconds
    def source_time(value: float) -> float:
        try: seconds = float(value)
        except (TypeError, ValueError): raise TakeBoardError("Picture source timing must be numeric.")
        if not 0.0 <= seconds <= 86400.0:
            raise TakeBoardError("Picture source timing must be between 0 and 86400 seconds.")
        return seconds
    intent = {
        "j_cut": style in {"J_CUT", "J_L_CUT"},
        "l_cut": style in {"L_CUT", "J_L_CUT"},
        "j_cut_lead_s": bounded(j_cut_lead_s),
        "l_cut_tail_s": bounded(l_cut_tail_s),
        "picture_in_s": source_time(picture_in_s),
        "picture_out_s": source_time(picture_out_s) if float(picture_out_s or 0.0) else None,
        "director_explicit": True,
    }
    return _store(project).update_metadata(take_id, patch={"audio_cut_intent": intent})


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
    export_selected(project, dest)
    if not dest.is_file() or dest.stat().st_size <= 0:
        raise TakeBoardError("Cinema export did not produce a usable video file.")
    project.register_output(dest, generator="cinema-selected-takes")
    return dest
