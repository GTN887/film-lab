"""Mark & Direct regeneration service.

A directing pass always forks a new Take. The source Take is preserved. Regional
marks are folded into the Shot prompt and the selected frame becomes the new
start reference for the configured generator.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from film_lab.generators.base import Generator
from film_lab.mark import ProjectMarks, fold_marks_into_seed, load_marks, still_from_source
from film_lab.production import ProductionStore, Take
from film_lab.project import Project
from film_lab.queue import GenerationQueue
from film_lab.shot_card import ShotCard


class MarkDirectRegenerationError(RuntimeError):
    pass


def regenerate_take(
    project: Project,
    *,
    source_take_id: str,
    generator: Generator,
    director_instruction: str = "",
    character_id: str = "",
    region_id: str = "",
    source_time_s: float = 0.0,
    repair_bbox: tuple[float, float, float, float] | None = None,
) -> Take:
    """Regenerate a source Take as a new Take using current Mark & Direct state."""
    store = ProductionStore(project)
    source = store.get_take(source_take_id)
    source_media = Path(source.media_path)
    if not source_media.is_file():
        raise MarkDirectRegenerationError("Source Take media is missing.")

    try:
        original = project.load_shot(source.shot_id)
        shot = deepcopy(original)
    except (OSError, ValueError, TypeError):
        shot = ShotCard(id=source.shot_id, name=source.name or "Directed take")
    shot.scene_id = source.scene_id

    frame = project.stills_dir / f"mark_direct_{source.id}.png"
    if float(source_time_s or 0) > 0:
        still_from_source(source_media, frame, seconds=source_time_s)
    else:
        still_from_source(source_media, frame)
    shot.start_frame = frame.name

    instruction = (director_instruction or "").strip()
    seed = shot.director_intent or source.prompt or ""
    if instruction:
        seed = f"{seed}\n{instruction}".strip()
    marks = load_marks(project)
    actor_id = (character_id or "").strip()
    selected_region = (region_id or "").strip()
    if actor_id or selected_region:
        chosen = [r for r in marks.regions if (not actor_id or r.character_id == actor_id) and (not selected_region or r.id == selected_region)]
        if not chosen:
            raise MarkDirectRegenerationError("No saved Mark & Direct region matches the requested Character/region.")
        if any(not r.character_id for r in chosen):
            raise MarkDirectRegenerationError("Actor-isolated regeneration requires a mark bound to a stable Character ID.")
        marks = ProjectMarks(regions=chosen)
    shot.director_intent = fold_marks_into_seed(seed, marks)
    project.save_shot(shot)

    before = {t.id for t in store.list_takes(shot_id=shot.id)}
    queue = GenerationQueue()
    queue.enqueue(shot)
    queue.run(project, generator)
    item = queue.items[0]
    if item.status != "done":
        raise MarkDirectRegenerationError(item.message or "Mark & Direct regeneration failed.")

    created = [t for t in store.list_takes(shot_id=shot.id) if t.id not in before]
    if not created:
        raise MarkDirectRegenerationError("Renderer completed but no persistent Take was created.")
    new_take = created[0]
    # Keep provenance explicit for audit/debugging without changing source Take.
    data = store._load()
    raw = data["takes"][new_take.id]
    raw.setdefault("metadata", {})["source"] = "mark_direct_regeneration"
    raw["metadata"]["source_take_id"] = source.id
    raw["metadata"]["director_instruction"] = instruction
    if source_time_s or repair_bbox:
        raw["metadata"]["localized_repair_source"] = {"time_s": float(source_time_s or 0), "bbox": list(repair_bbox) if repair_bbox else None, "status": "PREPARED", "truth": "The generation start frame/region was localized; temporal-only video patching is not implied."}
    if actor_id or selected_region:
        route = raw.get("metadata", {}).get("generator_route") or {}
        wired = set(route.get("wired_capabilities") or (route.get("conditioning_bridge") or {}).get("wired_capabilities") or [])
        raw["metadata"]["regional_actor_control"] = {
            "character_id": actor_id, "region_id": selected_region,
            "status": "ENFORCED" if "mask_regeneration" in wired else "NOT_ENFORCED",
            "truth": "Actor isolation is ENFORCED only when the selected validated workflow wired mask_regeneration.",
        }
    store._save(data)
    return store.get_take(new_take.id)
