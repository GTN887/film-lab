"""End-to-end render service: production conditioning + truthful generator capability checks + durable Take."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from film_lab.conditioning import attach_conditioning, build_conditioning
from film_lab.generator_capabilities import require_generator, requirements_from_conditioning
from film_lab.generators.base import GenerateJob, Generator
from film_lab.production import ProductionStore, Take
from film_lab.project import Project
from film_lab.scene_context import SceneContextStore, resolved_character_context
from film_lab.shot_card import ShotCard

@dataclass(frozen=True)
class RenderResult:
    take: Take; generated_path: Path; engine_id: str; engine_label: str

def generate_take(project: Project, shot: ShotCard, start_path: Path | str, generator: Generator, *, scene_id: str | None = None, prompt: str | None = None, model: str = "", metadata: dict[str, Any] | None = None, output_path: Path | str | None = None) -> RenderResult:
    start=Path(start_path)
    if not start.is_file(): raise FileNotFoundError(start)
    scene=(scene_id or shot.scene_id or "scene_001").strip() or "scene_001"
    out=Path(output_path) if output_path else project.outputs_dir/f"{shot.id}_generated.mp4"; out.parent.mkdir(parents=True,exist_ok=True)
    raw_prompt=prompt if prompt is not None else shot.local_prompt()
    world=SceneContextStore(project).get(scene); characters=resolved_character_context(project,scene)
    conditioning=build_conditioning(project,shot,start,scene_id=scene,prompt=raw_prompt)
    capability_decision=require_generator(generator,requirements_from_conditioning(conditioning))
    original_prompt=shot.prompt; shot.prompt=conditioning.prompt
    try:
        job=GenerateJob(shot=shot,start_path=start,end_path=Path(shot.end_frame) if shot.end_frame else None,output_path=out)
        attach_conditioning(job,conditioning); generated=Path(generator.generate(job))
    finally: shot.prompt=original_prompt
    if not generated.is_file() or generated.stat().st_size<=0: raise RuntimeError("Render engine returned no usable video; no Take was created.")
    engine_id=str(getattr(generator,"id",generator.__class__.__name__)); engine_label=str(getattr(generator,"label",engine_id))
    meta=dict(metadata or {}); meta.setdefault("engine_label",engine_label); meta.setdefault("source_still",str(start.resolve()))
    meta["scene_world"]=asdict(world); meta["characters"]=[asdict(c) for c in characters]; meta["character_ids"]=[c.id for c in characters]
    meta["conditioning"]=conditioning.to_dict(); meta["generator_capabilities"]={"missing_required":list(capability_decision.missing_required),"unsupported_optional":list(capability_decision.unsupported_optional),"score":capability_decision.score}
    meta["shot_prompt"]=raw_prompt; meta["generation_prompt"]=conditioning.prompt; meta["scene_world_version"]=1; meta["character_state_version"]=1
    take=ProductionStore(project).add_take(generated,shot_id=shot.id,scene_id=scene,name=shot.name,generator=engine_id,model=model,prompt=conditioning.prompt,duration=shot.duration,metadata=meta,copy_media=True)
    return RenderResult(take=take,generated_path=generated,engine_id=engine_id,engine_label=engine_label)

def import_take(project: Project, media_path: Path | str, *, shot_id: str, scene_id: str = "scene_001", name: str = "", director_notes: str = "", tags: list[str] | None = None) -> Take:
    store=ProductionStore(project); take=store.add_take(media_path,shot_id=shot_id,scene_id=scene_id,name=name,generator="import",metadata={"source":"creator_import"})
    if director_notes or tags: take=store.update_notes(take.id,director_notes=director_notes,tags=tags or [])
    return take
