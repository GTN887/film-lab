"""Structured production conditioning for capable generators."""
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from film_lab.scene_context import SceneContextStore, generation_prompt, resolved_character_context
@dataclass(frozen=True)
class CharacterConditioning:
    character_id:str; name:str; reference_images:tuple[str,...]=(); identity_adapter:str=""; identity_reference:str=""; voice_id:str=""; performance:str=""; emotional_state:str=""
@dataclass(frozen=True)
class GenerationConditioning:
    scene_id:str; shot_id:str; prompt:str; start_image:str; end_image:str=""; set_id:str=""; camera:dict[str,Any]=field(default_factory=dict); blocking:tuple[dict[str,Any],...]=(); objects:tuple[dict[str,Any],...]=(); characters:tuple[CharacterConditioning,...]=(); continuity_notes:str=""; director_instructions:str=""; metadata:dict[str,Any]=field(default_factory=dict)
    def to_dict(self): return asdict(self)
def build_conditioning(project,shot,start_path,*,scene_id=None,prompt=None):
    scene=(scene_id or shot.scene_id or "scene_001").strip() or "scene_001"; world=SceneContextStore(project).get(scene); chars=resolved_character_context(project,scene); raw=prompt if prompt is not None else shot.local_prompt()
    conditioning = GenerationConditioning(scene,shot.id,generation_prompt(project,scene,raw),str(Path(start_path).resolve()),str(Path(shot.end_frame).resolve()) if shot.end_frame else "",world.set_id,dict(world.camera),tuple(world.blocking),tuple(world.objects),tuple(CharacterConditioning(c.id,c.name,tuple(c.reference_images),c.identity_adapter,c.identity_reference,c.voice_id,c.performance,c.emotional_state) for c in chars),world.continuity_notes,world.director_instructions,{"scene_world_version":1,"character_state_version":1,"prior_take_ids":list(world.prior_take_ids)})
    from film_lab.spatial_control import build_spatial_assignments
    from film_lab.performance_direction import build_performance_directions
    conditioning.metadata["spatial_assignments"] = [x.to_dict() for x in build_spatial_assignments(conditioning)]
    conditioning.metadata["performance_directions"] = [x.to_dict() for x in build_performance_directions(conditioning)]
    from film_lab.performance_timeline import PerformanceTimelineStore, timeline_enforcement
    timelines = PerformanceTimelineStore(project).for_shot(scene, shot.id)
    conditioning.metadata["performance_timelines"] = [x.to_dict() for x in timelines]
    conditioning.metadata["performance_timeline_enforcement"] = [timeline_enforcement(x) for x in timelines]
    timeline_prompt = " ".join(x.prompt() for x in timelines if x.prompt())
    if timeline_prompt:
        object.__setattr__(conditioning, "prompt", conditioning.prompt + "\nPerformance over time: " + timeline_prompt)
    from film_lab.performance_choreography import PerformanceChoreographyStore, choreography_enforcement
    choreography = PerformanceChoreographyStore(project).get(scene, shot.id)
    if choreography:
        conditioning.metadata["performance_choreography"] = choreography.to_dict()
        conditioning.metadata["performance_choreography_enforcement"] = choreography_enforcement(choreography)
        names = {c.character_id:c.name for c in conditioning.characters}
        choreography_prompt = choreography.prompt(names)
        if choreography_prompt:
            object.__setattr__(conditioning, "prompt", conditioning.prompt + "\nActor choreography: " + choreography_prompt)
    from film_lab.dialogue_performance import DialoguePerformanceStore, build_from_voice_cues, dialogue_enforcement
    dialogue = DialoguePerformanceStore(project).get(scene, shot.id) or build_from_voice_cues(project, scene, shot.id)
    if dialogue:
        conditioning.metadata["dialogue_performance"] = dialogue.to_dict()
        conditioning.metadata["dialogue_performance_enforcement"] = dialogue_enforcement(dialogue)
        names = {c.character_id:c.name for c in conditioning.characters}
        dialogue_prompt = dialogue.prompt(names)
        if dialogue_prompt:
            object.__setattr__(conditioning, "prompt", conditioning.prompt + "\nDialogue performance: " + dialogue_prompt)
    from film_lab.voice_acting import VoiceActingStore, voice_acting_enforcement
    voice_acting = VoiceActingStore(project).get(scene, shot.id)
    if voice_acting:
        conditioning.metadata["voice_acting"] = voice_acting.to_dict()
        conditioning.metadata["voice_acting_enforcement"] = voice_acting_enforcement(voice_acting)
        names = {c.character_id:c.name for c in conditioning.characters}
        voice_prompt = voice_acting.prompt(names)
        if voice_prompt:
            object.__setattr__(conditioning, "prompt", conditioning.prompt + "\nVoice acting: " + voice_prompt)
    from film_lab.audio_performance_timeline import build_audio_performance_timeline, timeline_sync_status
    unified_timeline = build_audio_performance_timeline(project, scene, shot.id)
    conditioning.metadata["audio_performance_timeline"] = unified_timeline.to_dict()
    conditioning.metadata["audio_performance_timeline_status"] = timeline_sync_status(unified_timeline)
    from film_lab.camera_timeline import CameraTimelineStore, camera_enforcement
    camera_timeline = CameraTimelineStore(project).get(scene, shot.id)
    if camera_timeline:
        conditioning.metadata["camera_timeline"] = camera_timeline.to_dict()
        conditioning.metadata["camera_timeline_enforcement"] = camera_enforcement(camera_timeline)
        camera_prompt = camera_timeline.prompt()
        if camera_prompt:
            object.__setattr__(conditioning, "prompt", conditioning.prompt + "\n" + camera_prompt)
    from film_lab.regional_actor_control import build_regional_actor_controls
    conditioning.metadata["regional_actor_controls"] = [x.to_dict() for x in build_regional_actor_controls(project, conditioning)]
    return conditioning
def attach_conditioning(job,conditioning):
    """Compatibility helper; GenerateJob now has a formal conditioning field."""
    job.conditioning=conditioning
    return job
