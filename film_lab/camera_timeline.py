"""Persistent shot-local camera direction timeline.

Camera cues are real production state. They are not called renderer-enforced unless a
compatible camera/time-control bridge proves the requested controls are wired.
"""
from __future__ import annotations
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class CameraKeyframe:
    time_s: float
    move: str = ""
    framing: str = ""
    lens: str = ""
    focus_target: str = ""
    follow_character_id: str = ""
    speed: float | None = None
    note: str = ""
    def __post_init__(self):
        if float(self.time_s) < 0: raise ValueError("Camera keyframe time cannot be negative.")
        if self.speed is not None and not 0 <= float(self.speed) <= 1: raise ValueError("Camera speed must be between 0 and 1.")
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class CameraTimeline:
    scene_id: str
    shot_id: str
    keyframes: tuple[CameraKeyframe,...]
    status: str = "DIRECTED"
    def __post_init__(self): object.__setattr__(self,"keyframes",tuple(sorted(self.keyframes,key=lambda k:float(k.time_s))))
    def to_dict(self): return {"scene_id":self.scene_id,"shot_id":self.shot_id,"keyframes":[k.to_dict() for k in self.keyframes],"status":self.status}
    def prompt(self):
        rows=[]
        for k in self.keyframes:
            bits=[f"{n}: {v}" for n,v in (("move",k.move),("framing",k.framing),("lens",k.lens),("focus",k.focus_target),("follow",k.follow_character_id),("note",k.note)) if v]
            if k.speed is not None: bits.append(f"speed: {float(k.speed):.2f}")
            if bits: rows.append(f"{float(k.time_s):.2f}s "+"; ".join(bits))
        return "Camera timeline — "+" | ".join(rows) if rows else ""

class CameraTimelineStore:
    def __init__(self,project): self.path=Path(project.root)/"camera_timelines.json"
    def _load(self):
        try: d=json.loads(self.path.read_text(encoding="utf-8"))
        except Exception: d={"version":1,"shots":{}}
        return d if isinstance(d,dict) else {"version":1,"shots":{}}
    def save(self,t:CameraTimeline):
        d=self._load(); d.setdefault("shots",{})[f"{t.scene_id}::{t.shot_id}"]=t.to_dict(); self.path.parent.mkdir(parents=True,exist_ok=True); self.path.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); return t
    def get(self,scene_id,shot_id):
        r=self._load().get("shots",{}).get(f"{scene_id}::{shot_id}")
        if not isinstance(r,dict): return None
        return CameraTimeline(str(r.get("scene_id",scene_id)),str(r.get("shot_id",shot_id)),tuple(CameraKeyframe(**x) for x in r.get("keyframes",[]) if isinstance(x,dict)),str(r.get("status","DIRECTED")))

def camera_enforcement(timeline:CameraTimeline, *, temporal_camera_wired=False):
    return {"status":"ENFORCED" if temporal_camera_wired else "PROMPT_ONLY","reason":"Time-aware camera controls are wired." if temporal_camera_wired else "Camera timeline is production direction; renderer camera keyframes are not proven.","keyframes":len(timeline.keyframes)}
