"""Character-specific spatial/blocking intent. Enforcement remains capability-evidence based."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any

@dataclass(frozen=True)
class SpatialAssignment:
    character_id:str; name:str; region:str=""; blocking:tuple[dict[str,Any],...]=(); mask_path:str=""; status:str="PROMPT_ONLY"; reason:str=""
    def to_dict(self): return asdict(self)

def _matches(item:dict[str,Any], cid:str, name:str)->bool:
    vals={str(item.get(k,"")).strip().lower() for k in ("character_id","character","id","name","target")}
    return cid.lower() in vals or (name and name.lower() in vals)

def build_spatial_assignments(conditioning, *, regional_supported:bool=False):
    blocking=tuple(getattr(conditioning,"blocking",()) or ()); out=[]
    for char in tuple(getattr(conditioning,"characters",()) or ()):
        cid=str(getattr(char,"character_id","") or ""); name=str(getattr(char,"name","") or "")
        matched=tuple(x for x in blocking if isinstance(x,dict) and _matches(x,cid,name))
        region=""
        for x in matched:
            region=str(x.get("region") or x.get("position") or x.get("area") or region)
        if regional_supported and region:
            status,reason="AVAILABLE_NOT_WIRED","Regional control is available, but no mask/region workflow slot has been proven for this character."
        elif region:
            status,reason="PROMPT_ONLY","Character position/blocking is carried in generation direction; no regional model control is proven."
        else:
            status,reason="PROMPT_ONLY","No explicit character region is defined; identity remains stable but spatial placement is prompt guidance."
        out.append(SpatialAssignment(cid,name,region,matched,"",status,reason))
    return tuple(out)
