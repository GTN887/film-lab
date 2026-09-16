"""Shot-local multi-actor choreography with stable Character IDs.

Choreography coordinates timing and relationships between performers. It is production
intent until a renderer proves a compatible multi-actor temporal/spatial bridge.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class InteractionCue:
    time_s: float
    actor_id: str
    target_id: str = ""
    action: str = ""
    reaction: str = ""
    gaze: str = ""
    spacing: str = ""
    contact: str = ""
    dialogue_beat: str = ""

    def __post_init__(self):
        if float(self.time_s) < 0:
            raise ValueError("Interaction cue time cannot be negative.")
        if not self.actor_id.strip():
            raise ValueError("Interaction cue requires a stable actor Character ID.")
        if self.target_id and self.target_id == self.actor_id:
            raise ValueError("Interaction target must be a different Character ID.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PerformanceChoreography:
    scene_id: str
    shot_id: str
    cues: tuple[InteractionCue, ...]
    status: str = "PROMPT_ONLY"

    def __post_init__(self):
        object.__setattr__(self, "cues", tuple(sorted(self.cues, key=lambda x: float(x.time_s))))

    @property
    def character_ids(self) -> tuple[str, ...]:
        ids=set()
        for cue in self.cues:
            ids.add(cue.actor_id)
            if cue.target_id: ids.add(cue.target_id)
        return tuple(sorted(ids))

    def to_dict(self) -> dict[str, Any]:
        return {"scene_id":self.scene_id,"shot_id":self.shot_id,"cues":[x.to_dict() for x in self.cues],"status":self.status,"character_ids":list(self.character_ids)}

    def prompt(self, names: dict[str,str] | None=None) -> str:
        names=names or {}; rows=[]
        for cue in self.cues:
            actor=names.get(cue.actor_id,cue.actor_id); target=names.get(cue.target_id,cue.target_id) if cue.target_id else ""
            bits=[]
            if cue.action: bits.append(f"action: {cue.action}")
            if cue.reaction: bits.append(f"reaction: {cue.reaction}")
            if cue.gaze: bits.append(f"gaze: {cue.gaze}")
            if cue.spacing: bits.append(f"spacing: {cue.spacing}")
            if cue.contact: bits.append(f"contact: {cue.contact}")
            if cue.dialogue_beat: bits.append(f"dialogue beat: {cue.dialogue_beat}")
            relation=f" toward {target} [{cue.target_id}]" if target else ""
            rows.append(f"{float(cue.time_s):.2f}s {actor} [{cue.actor_id}]{relation} — "+"; ".join(bits))
        return " | ".join(rows)


class PerformanceChoreographyStore:
    def __init__(self, project):
        self.path=Path(project.root)/"performance_choreography.json"

    @staticmethod
    def _key(scene_id:str,shot_id:str)->str: return f"{scene_id}::{shot_id}"

    def _load(self):
        if not self.path.exists(): return {"version":1,"shots":{}}
        try: data=json.loads(self.path.read_text(encoding="utf-8"))
        except Exception: return {"version":1,"shots":{}}
        return data if isinstance(data,dict) else {"version":1,"shots":{}}

    def save(self, choreography:PerformanceChoreography)->PerformanceChoreography:
        data=self._load(); data.setdefault("shots",{})[self._key(choreography.scene_id,choreography.shot_id)]=choreography.to_dict()
        self.path.parent.mkdir(parents=True,exist_ok=True); self.path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        return choreography

    def get(self,scene_id:str,shot_id:str)->PerformanceChoreography|None:
        raw=self._load().get("shots",{}).get(self._key(scene_id,shot_id))
        if not isinstance(raw,dict): return None
        cues=tuple(InteractionCue(**x) for x in raw.get("cues",[]) if isinstance(x,dict))
        return PerformanceChoreography(str(raw.get("scene_id",scene_id)),str(raw.get("shot_id",shot_id)),cues,str(raw.get("status","PROMPT_ONLY")))


def choreography_enforcement(choreography:PerformanceChoreography, *, temporal_wired:bool=False, multi_actor_spatial_wired:bool=False)->dict[str,Any]:
    enforced=bool(temporal_wired and multi_actor_spatial_wired)
    if enforced:
        status="ENFORCED"; reason="Timed multi-actor choreography is wired into proven temporal and actor-specific spatial controls."
    elif temporal_wired or multi_actor_spatial_wired:
        status="PARTIAL"; reason="Only part of the required temporal/spatial multi-actor control path is proven."
    else:
        status="PROMPT_ONLY"; reason="Choreography is production/prompt direction; no proven multi-actor temporal+spatial renderer bridge is wired."
    return {"status":status,"reason":reason,"characters":list(choreography.character_ids),"cues":len(choreography.cues)}
