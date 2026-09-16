"""Review-first continuity planning for Film Lab.

This module never mutates production state while planning.  It describes what the
next shot should preserve, what the Director explicitly requested to change, and
which selected Take anchors continuity.  Applying the Director plan can then pin
that prior Take into Scene World without rewriting Character Bible state.
"""
from __future__ import annotations

from typing import Any

from film_lab.character_state import CharacterStore
from film_lab.production import ProductionStore
from film_lab.scene_context import SceneContextStore


def _selected_prior_take(project, scene_id: str, shot_id: str):
    takes = [
        t for t in ProductionStore(project).selected_takes(existing_media_only=False)
        if t.scene_id == scene_id and t.shot_id != shot_id
    ]
    takes.sort(key=lambda t: t.created_at)
    return takes[-1] if takes else None


def build_continuity_report(project, *, scene_id: str, shot_id: str, instruction: str, scene_changes: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a serializable continuity proposal for Creator review."""
    world = SceneContextStore(project).get(scene_id)
    chars = CharacterStore(project).resolve_scene_characters(world.characters)
    prior = _selected_prior_take(project, scene_id, shot_id)
    changes = dict(scene_changes or {})

    preserve: list[dict[str, Any]] = []
    for label, value in (
        ("set_id", world.set_id), ("location", world.location),
        ("time_of_day", world.time_of_day), ("weather", world.weather),
        ("lighting", world.lighting), ("camera", world.camera),
        ("blocking", world.blocking), ("objects", world.objects),
    ):
        if value not in ("", None, [], {}):
            preserve.append({"field": label, "value": value})

    character_locks = []
    for c in chars:
        character_locks.append({
            "id": c.id, "name": c.name, "appearance": c.appearance,
            "wardrobe": c.wardrobe, "hair": c.hair, "makeup": c.makeup,
            "reference_images": list(c.reference_images),
            "continuity_notes": c.continuity_notes,
        })

    requested_changes = []
    for field in ("time_of_day", "weather", "lighting", "location", "set_id"):
        if field in changes and changes[field] not in ("", None):
            old = getattr(world, field, "")
            if changes[field] != old:
                requested_changes.append({"field": field, "from": old, "to": changes[field]})
    if instruction.strip():
        requested_changes.append({"field": "director_instructions", "from": world.director_instructions, "to": instruction.strip()})

    prior_summary = None
    if prior:
        cond = prior.metadata.get("conditioning", {}) if isinstance(prior.metadata, dict) else {}
        prior_summary = {
            "take_id": prior.id, "shot_id": prior.shot_id,
            "director_notes": prior.director_notes, "tags": list(prior.tags),
            "conditioning": cond if isinstance(cond, dict) else {},
        }

    warnings = []
    if world.characters and not chars:
        warnings.append("Scene character references could not be resolved to stable Character IDs.")
    if prior is None:
        warnings.append("No previous Selected Take is available to anchor shot-to-shot visual continuity.")

    return {
        "scene_id": scene_id,
        "shot_id": shot_id,
        "anchor_take": prior_summary,
        "preserve": preserve,
        "character_locks": character_locks,
        "requested_changes": requested_changes,
        "warnings": warnings,
        "creator_review_required": True,
    }


def apply_continuity_anchor(project, *, scene_id: str, report: dict[str, Any]) -> list[str]:
    """Pin the reviewed prior Take to Scene World; do not rewrite Character state."""
    world = SceneContextStore(project).get(scene_id)
    ids = list(dict.fromkeys(str(x) for x in world.prior_take_ids if str(x)))
    anchor = report.get("anchor_take") if isinstance(report, dict) else None
    if isinstance(anchor, dict) and anchor.get("take_id"):
        tid = str(anchor["take_id"])
        if tid not in ids:
            ids.append(tid)
    SceneContextStore(project).update(scene_id, prior_take_ids=ids)
    return ids
