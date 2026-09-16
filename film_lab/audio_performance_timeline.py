"""Unified shot audio/performance timeline for Film Lab.

This is editable production state, not a claim that a renderer visually enforces every
lane. It coordinates Character-bound dialogue, voice acting, actor performance and
reaction events on one time axis while preserving stable Character IDs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TimelineEvent:
    lane: str
    character_id: str
    start_s: float
    end_s: float | None = None
    event_id: str = ""
    label: str = ""
    payload: dict[str, Any] | None = None

    def __post_init__(self):
        if not self.character_id.strip():
            raise ValueError("Timeline events require a stable Character ID.")
        if float(self.start_s) < 0:
            raise ValueError("Timeline event start cannot be negative.")
        if self.end_s is not None and float(self.end_s) < float(self.start_s):
            raise ValueError("Timeline event end cannot precede start.")
        if self.lane not in {"dialogue", "voice_acting", "performance", "reaction"}:
            raise ValueError(f"Unsupported timeline lane: {self.lane}")

    def to_dict(self): return asdict(self)


@dataclass(frozen=True)
class AudioPerformanceTimeline:
    scene_id: str
    shot_id: str
    events: tuple[TimelineEvent, ...]

    def __post_init__(self):
        object.__setattr__(self, "events", tuple(sorted(self.events, key=lambda e:(float(e.start_s), e.lane, e.character_id, e.event_id))))

    @property
    def character_ids(self): return tuple(sorted({e.character_id for e in self.events}))
    @property
    def duration_s(self):
        return max((float(e.end_s if e.end_s is not None else e.start_s) for e in self.events), default=0.0)
    def lane(self, name:str): return tuple(e for e in self.events if e.lane == name)
    def for_character(self, character_id:str): return tuple(e for e in self.events if e.character_id == character_id)
    def to_dict(self):
        return {"scene_id":self.scene_id,"shot_id":self.shot_id,"duration_s":self.duration_s,"character_ids":list(self.character_ids),"events":[e.to_dict() for e in self.events]}


def build_audio_performance_timeline(project, scene_id:str, shot_id:str) -> AudioPerformanceTimeline:
    """Merge persistent shot direction into one deterministic edit/review timeline."""
    from film_lab.dialogue_performance import DialoguePerformanceStore, build_from_voice_cues
    from film_lab.voice_acting import VoiceActingStore
    from film_lab.performance_timeline import PerformanceTimelineStore
    from film_lab.performance_choreography import PerformanceChoreographyStore

    events=[]
    dialogue=DialoguePerformanceStore(project).get(scene_id,shot_id) or build_from_voice_cues(project,scene_id,shot_id)
    if dialogue:
        for i,b in enumerate(dialogue.beats):
            events.append(TimelineEvent("dialogue",b.character_id,b.start_s,b.end_s,b.cue_id or f"dialogue_{i:03d}",b.text,b.to_dict()))
    voice=VoiceActingStore(project).get(scene_id,shot_id)
    if voice:
        for i,b in enumerate(voice.beats):
            end=b.end_s if b.end_s is not None else (b.start_s+b.pause_s if b.pause_s else None)
            events.append(TimelineEvent("voice_acting",b.character_id,b.start_s,end,f"voice_{i:03d}",b.delivery or b.emotion,b.to_dict()))
    for tl in PerformanceTimelineStore(project).for_shot(scene_id,shot_id):
        for i,k in enumerate(tl.keyframes):
            label=k.action or k.expression or k.emotion
            events.append(TimelineEvent("performance",tl.character_id,k.time_s,None,f"performance_{i:03d}",label,k.to_dict()))
    choreo=PerformanceChoreographyStore(project).get(scene_id,shot_id)
    if choreo:
        for i,b in enumerate(choreo.cues):
            # Choreography is relational; put the event on the initiating actor's lane.
            cid=b.actor_id
            if cid:
                label=b.action or b.reaction or b.dialogue_beat
                events.append(TimelineEvent("reaction",cid,b.time_s,None,f"reaction_{i:03d}",label,b.to_dict()))
    return AudioPerformanceTimeline(scene_id,shot_id,tuple(events))


def move_dialogue_beat(project, scene_id:str, shot_id:str, beat_index:int, new_start_s:float):
    """Non-destructively retime a dialogue beat while preserving its duration/Character."""
    from film_lab.dialogue_performance import DialoguePerformanceStore, DialoguePerformance, DialogueBeat
    store=DialoguePerformanceStore(project); perf=store.get(scene_id,shot_id)
    if perf is None: raise ValueError("No saved dialogue performance for this shot.")
    if beat_index < 0 or beat_index >= len(perf.beats): raise IndexError("Dialogue beat index out of range.")
    old=perf.beats[beat_index]; start=float(new_start_s)
    if start < 0: raise ValueError("Dialogue start time cannot be negative.")
    end=start+(float(old.end_s)-float(old.start_s)) if old.end_s is not None else None
    replacement=DialogueBeat(start,old.character_id,old.text,old.cue_id,old.audio_path,end,old.emotion,old.intention,old.reaction_to)
    beats=list(perf.beats); beats[beat_index]=replacement
    return store.save(DialoguePerformance(scene_id,shot_id,tuple(beats),perf.status))


def timeline_sync_status(timeline:AudioPerformanceTimeline, *, audio_timing_wired=True, lip_sync_wired=False, performance_time_wired=False):
    """Report coordination separately from renderer enforcement."""
    coordinated=bool(timeline.events)
    enforced=bool(coordinated and audio_timing_wired and lip_sync_wired and performance_time_wired)
    if enforced:
        status="ENFORCED"; reason="Timed audio, Character-bound lip sync, and time-aware performance controls are all wired."
    elif coordinated:
        status="PARTIAL"; reason="Timeline coordination is real production state, but one or more renderer enforcement paths are not proven."
    else:
        status="NOT TESTED"; reason="No timeline events exist for this shot."
    return {"status":status,"reason":reason,"events":len(timeline.events),"characters":list(timeline.character_ids),"renderer_enforced":enforced}
