"""Persistent Character-bound voice acting direction.

Voice acting direction is production state. Film Lab only calls expressive voice
control ENFORCED when a renderer exposes an explicit Character-bound voice-performance
slot and the selected voice path proves expressive/prosody control.
"""
from __future__ import annotations
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class VoiceActingBeat:
    start_s: float
    character_id: str
    emotion: str = ""
    pace: str = ""
    emphasis: str = ""
    intensity: float | None = None
    delivery: str = ""
    pause_s: float = 0.0
    end_s: float | None = None
    def __post_init__(self):
        if self.start_s < 0 or self.pause_s < 0: raise ValueError("Voice timing cannot be negative.")
        if self.end_s is not None and self.end_s < self.start_s: raise ValueError("Voice end cannot precede start.")
        if not self.character_id.strip(): raise ValueError("Voice acting requires a stable Character ID.")
        if self.intensity is not None and not 0 <= float(self.intensity) <= 1: raise ValueError("Voice intensity must be between 0 and 1.")
    def to_dict(self): return asdict(self)

@dataclass(frozen=True)
class VoiceActingPerformance:
    scene_id: str
    shot_id: str
    beats: tuple[VoiceActingBeat,...]
    def __post_init__(self): object.__setattr__(self,"beats",tuple(sorted(self.beats,key=lambda b:(b.start_s,b.character_id))))
    @property
    def character_ids(self): return tuple(sorted({b.character_id for b in self.beats}))
    def to_dict(self): return {"scene_id":self.scene_id,"shot_id":self.shot_id,"beats":[b.to_dict() for b in self.beats],"character_ids":list(self.character_ids)}
    def prompt(self,names:dict[str,str]|None=None):
        names=names or {}; rows=[]
        for b in self.beats:
            bits=[]
            for label,value in (("emotion",b.emotion),("pace",b.pace),("emphasis",b.emphasis),("delivery",b.delivery)):
                if value: bits.append(f"{label}: {value}")
            if b.intensity is not None: bits.append(f"intensity: {b.intensity:.2f}")
            if b.pause_s: bits.append(f"pause: {b.pause_s:.2f}s")
            if bits: rows.append(f"{b.start_s:.2f}s {names.get(b.character_id,b.character_id)} [{b.character_id}] — "+"; ".join(bits))
        return " | ".join(rows)

class VoiceActingStore:
    def __init__(self,project): self.path=Path(project.root)/"voice_acting.json"
    def _load(self):
        try: d=json.loads(self.path.read_text(encoding="utf-8"))
        except Exception: d={"version":1,"shots":{}}
        return d if isinstance(d,dict) else {"version":1,"shots":{}}
    def save(self,p:VoiceActingPerformance):
        d=self._load(); d.setdefault("shots",{})[f"{p.scene_id}::{p.shot_id}"]=p.to_dict(); self.path.parent.mkdir(parents=True,exist_ok=True); self.path.write_text(json.dumps(d,indent=2,ensure_ascii=False)+"\n",encoding="utf-8"); return p
    def get(self,scene_id,shot_id):
        r=self._load().get("shots",{}).get(f"{scene_id}::{shot_id}")
        if not isinstance(r,dict): return None
        return VoiceActingPerformance(str(r.get("scene_id",scene_id)),str(r.get("shot_id",shot_id)),tuple(VoiceActingBeat(**x) for x in r.get("beats",[]) if isinstance(x,dict)))

def voice_acting_enforcement(performance:VoiceActingPerformance, *, expressive_voice_wired=False, character_voice_wired=False):
    enforced=bool(expressive_voice_wired and character_voice_wired)
    return {"status":"ENFORCED" if enforced else "PROMPT_ONLY","reason":"Character-bound expressive/prosody controls are wired to the voice renderer." if enforced else "Voice acting is production direction; expressive renderer control is not proven.","characters":list(performance.character_ids),"expressive_voice_enforced":enforced}
