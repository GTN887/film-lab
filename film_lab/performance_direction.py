"""Structured per-character performance direction without overstating model enforcement."""
from __future__ import annotations
from dataclasses import asdict, dataclass

@dataclass(frozen=True)
class PerformanceDirection:
    character_id:str; name:str; emotion:str=""; performance:str=""; gaze:str=""; posture:str=""; gesture:str=""; movement:str=""; reaction:str=""; intensity:str=""; status:str="DIRECTED"
    def to_dict(self): return asdict(self)
    def prompt(self):
        bits=[]
        for label,value in (("emotion",self.emotion),("performance",self.performance),("gaze",self.gaze),("posture",self.posture),("gesture",self.gesture),("movement",self.movement),("reaction",self.reaction),("intensity",self.intensity)):
            if value: bits.append(f"{label}: {value}")
        return f"{self.name} [{self.character_id}] performance — "+"; ".join(bits) if bits else ""

def build_performance_directions(conditioning):
    out=[]
    for char in tuple(getattr(conditioning,"characters",()) or ()):
        out.append(PerformanceDirection(
            str(getattr(char,"character_id","") or ""), str(getattr(char,"name","") or ""),
            str(getattr(char,"emotional_state","") or ""), str(getattr(char,"performance","") or ""),
        ))
    return tuple(out)
