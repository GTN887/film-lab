"""Structured conditioning passed from Film Lab production state to capable generators."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from film_lab.scene_context import SceneContextStore, generation_prompt, resolved_character_context

@dataclass(frozen=True)
class CharacterConditioning:
    character_id: str
    name: str
    reference_images: tuple[str,...]=()
    identity_adapter: str=""
    identity_reference: str=""
    voice_id: str=""
    performance: str=""
    emotional_state: str=""

@dataclass(frozen=True)
class GenerationConditioning:
    scene_id: str
    shot_id: str
    prompt: str
    start_image: str
    end_image: str=""
    set_id: str=""
    camera: dict[str,Any]=field(default_factory=dict)
    blocking: tuple[dict[str,Any],...]=()
    objects: tuple[dict[str,Any],...]=()
    characters: tuple[CharacterConditioning,...]=()
    continuity_notes: str=""
    director_instructions: str=""
    metadata: dict[str,Any]=field(default_factory=dict)

    def to_dict(self): return asdict(self)


def build_conditioning(project, shot, start_path, *, scene_id=None, prompt=None):
    scene=(scene_id or shot.scene_id or "scene_001").strip() or "scene_001"
    world=SceneContextStore(project).get(scene)
    chars=resolved_character_context(project,scene)
    raw_prompt=prompt if prompt is not None else shot.local_prompt()
    return GenerationConditioning(
        scene_id=scene, shot_id=shot.id, prompt=generation_prompt(project,scene,raw_prompt),
        start_image=str(Path(start_path).resolve()), end_image=str(Path(shot.end_frame).resolve()) if shot.end_frame else "",
        set_id=world.set_id, camera=dict(world.camera), blocking=tuple(world.blocking), objects=tuple(world.objects),
        characters=tuple(CharacterConditioning(character_id=c.id,name=c.name,reference_images=tuple(c.reference_images),identity_adapter=c.identity_adapter,identity_reference=c.identity_reference,voice_id=c.voice_id,performance=c.performance,emotional_state=c.emotional_state) for c in chars),
        continuity_notes=world.continuity_notes, director_instructions=world.director_instructions,
        metadata={"scene_world_version":1,"character_state_version":1},
    )


def attach_conditioning(job, conditioning):
    """Attach structured inputs without breaking legacy generators that only read ShotCard."""
    try: setattr(job,"conditioning",conditioning)
    except Exception: pass
    return job
