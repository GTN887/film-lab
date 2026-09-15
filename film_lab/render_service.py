"""End-to-end render service: generator output becomes a durable Take."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from film_lab.generators.base import GenerateJob, Generator
from film_lab.production import ProductionStore, Take
from film_lab.project import Project
from film_lab.shot_card import ShotCard

@dataclass(frozen=True)
class RenderResult:
    take: Take
    generated_path: Path
    engine_id: str
    engine_label: str

def generate_take(project: Project, shot: ShotCard, start_path: Path | str, generator: Generator, *, scene_id: str | None = None, prompt: str | None = None, model: str = "", metadata: dict[str, Any] | None = None, output_path: Path | str | None = None) -> RenderResult:
    """Generate one real clip and register it as a Take. Failed renders create no Take."""
    start = Path(start_path)
    if not start.is_file(): raise FileNotFoundError(start)
    scene = (scene_id or shot.scene_id or "scene_001").strip() or "scene_001"
    out = Path(output_path) if output_path else project.outputs_dir / f"{shot.id}_generated.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    job = GenerateJob(shot=shot, start_path=start, end_path=Path(shot.end_frame) if shot.end_frame else None, output_path=out)
    generated = Path(generator.generate(job))
    if not generated.is_file() or generated.stat().st_size <= 0:
        raise RuntimeError("Render engine returned no usable video; no Take was created.")
    engine_id = str(getattr(generator, "id", generator.__class__.__name__))
    engine_label = str(getattr(generator, "label", engine_id))
    meta = dict(metadata or {}); meta.setdefault("engine_label", engine_label); meta.setdefault("source_still", str(start.resolve()))
    take = ProductionStore(project).add_take(generated, shot_id=shot.id, scene_id=scene, name=shot.name, generator=engine_id, model=model, prompt=prompt if prompt is not None else shot.local_prompt(), duration=shot.duration, metadata=meta, copy_media=True)
    return RenderResult(take=take, generated_path=generated, engine_id=engine_id, engine_label=engine_label)

def import_take(project: Project, media_path: Path | str, *, shot_id: str, scene_id: str = "scene_001", name: str = "", director_notes: str = "", tags: list[str] | None = None) -> Take:
    """Import existing video through the same durable Take path as generation."""
    store = ProductionStore(project)
    take = store.add_take(media_path, shot_id=shot_id, scene_id=scene_id, name=name, generator="import", metadata={"source": "creator_import"})
    if director_notes or tags: take = store.update_notes(take.id, director_notes=director_notes, tags=tags or [])
    return take
