"""Shot-local actor performance timelines with truthful enforcement status.

Timelines are production direction. They become ENFORCED only when a renderer later
proves a time-aware control bridge; otherwise they remain PROMPT_ONLY.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PerformanceKeyframe:
    time_s: float
    emotion: str = ""
    expression: str = ""
    gaze: str = ""
    posture: str = ""
    gesture: str = ""
    action: str = ""
    intensity: float | None = None

    def __post_init__(self):
        if float(self.time_s) < 0:
            raise ValueError("Performance keyframe time cannot be negative.")
        if self.intensity is not None and not 0.0 <= float(self.intensity) <= 1.0:
            raise ValueError("Performance intensity must be between 0 and 1.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ActorPerformanceTimeline:
    scene_id: str
    shot_id: str
    character_id: str
    character_name: str
    keyframes: tuple[PerformanceKeyframe, ...]
    status: str = "PROMPT_ONLY"

    def __post_init__(self):
        if not self.character_id.strip():
            raise ValueError("A stable Character ID is required for a performance timeline.")
        ordered=tuple(sorted(self.keyframes, key=lambda x: float(x.time_s)))
        object.__setattr__(self,"keyframes",ordered)

    def to_dict(self) -> dict[str, Any]:
        d=asdict(self); d["keyframes"]=[k.to_dict() for k in self.keyframes]; return d

    def prompt(self) -> str:
        cues=[]
        for k in self.keyframes:
            bits=[]
            for label,value in (("emotion",k.emotion),("expression",k.expression),("gaze",k.gaze),("posture",k.posture),("gesture",k.gesture),("action",k.action)):
                if value: bits.append(f"{label}: {value}")
            if k.intensity is not None: bits.append(f"intensity: {float(k.intensity):.2f}")
            if bits: cues.append(f"{float(k.time_s):.2f}s " + "; ".join(bits))
        return f"{self.character_name} [{self.character_id}] performance timeline — " + " | ".join(cues) if cues else ""


class PerformanceTimelineStore:
    def __init__(self, project):
        self.path=Path(project.root)/"performance_timelines.json"

    def _load(self) -> dict[str, Any]:
        if not self.path.exists(): return {"version":1,"timelines":{}}
        try: data=json.loads(self.path.read_text(encoding="utf-8"))
        except Exception: return {"version":1,"timelines":{}}
        return data if isinstance(data,dict) else {"version":1,"timelines":{}}

    def _save(self,data):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        self.path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")

    @staticmethod
    def _key(scene_id,shot_id,character_id): return f"{scene_id}::{shot_id}::{character_id}"

    def save(self,timeline: ActorPerformanceTimeline) -> ActorPerformanceTimeline:
        data=self._load(); data.setdefault("timelines",{})[self._key(timeline.scene_id,timeline.shot_id,timeline.character_id)]=timeline.to_dict(); self._save(data); return timeline

    def get(self,scene_id:str,shot_id:str,character_id:str) -> ActorPerformanceTimeline | None:
        raw=self._load().get("timelines",{}).get(self._key(scene_id,shot_id,character_id))
        if not isinstance(raw,dict): return None
        keys=tuple(PerformanceKeyframe(**x) for x in raw.get("keyframes",[]) if isinstance(x,dict))
        return ActorPerformanceTimeline(str(raw.get("scene_id",scene_id)),str(raw.get("shot_id",shot_id)),str(raw.get("character_id",character_id)),str(raw.get("character_name","")),keys,str(raw.get("status","PROMPT_ONLY")))

    def for_shot(self,scene_id:str,shot_id:str) -> tuple[ActorPerformanceTimeline,...]:
        prefix=f"{scene_id}::{shot_id}::"; out=[]
        for key,raw in self._load().get("timelines",{}).items():
            if not str(key).startswith(prefix) or not isinstance(raw,dict): continue
            item=self.get(scene_id,shot_id,str(raw.get("character_id","")))
            if item: out.append(item)
        return tuple(sorted(out,key=lambda x:x.character_id))


def timeline_enforcement(timeline: ActorPerformanceTimeline, *, time_control_wired: bool=False) -> dict[str,Any]:
    """Never call prompt timing ENFORCED without a proven time-aware renderer bridge."""
    status="ENFORCED" if time_control_wired else "PROMPT_ONLY"
    reason="Time-aware performance control is wired into the selected render workflow." if time_control_wired else "Timeline is encoded as production/prompt direction; no proven time-aware model control is wired."
    return {"character_id":timeline.character_id,"status":status,"reason":reason,"keyframes":len(timeline.keyframes)}
