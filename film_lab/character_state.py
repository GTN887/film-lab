from __future__ import annotations
import json,uuid
from dataclasses import asdict,dataclass,field
from typing import Any
@dataclass
class CharacterState:
    id:str; name:str; appearance:str=""; wardrobe:str=""; hair:str=""; makeup:str=""; voice_id:str=""; performance:str=""; emotional_state:str=""; continuity_notes:str=""; reference_images:list[str]=field(default_factory=list); identity_adapter:str=""; identity_reference:str=""; metadata:dict[str,Any]=field(default_factory=dict)
    @classmethod
    def from_dict(cls,r): d=dict(r or {});return cls(**{k:d[k] for k in cls.__dataclass_fields__ if k in d})
    def prompt_context(self):
        p=[f"Character {self.name} [{self.id}]"]
        for l,v in (("Appearance",self.appearance),("Wardrobe",self.wardrobe),("Hair",self.hair),("Makeup",self.makeup),("Performance",self.performance),("Emotion",self.emotional_state),("Character continuity",self.continuity_notes)):
            if v:p.append(f"{l}: {v}")
        return ". ".join(p)
class CharacterStore:
    def __init__(self,p):self.project=p;p.ensure_dirs();self.path=p.root/"character_state.json"
    def _load(self):
        if not self.path.exists():return {"version":1,"characters":{}}
        try:r=json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError):return {"version":1,"characters":{}}
        r.setdefault("version",1);r.setdefault("characters",{});return r
    def _save(self,d):t=self.path.with_suffix(".json.tmp");t.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n",encoding="utf-8");t.replace(self.path)
    def create(self,name,**f):
        c=CharacterState(id=f"char_{uuid.uuid4().hex[:12]}",name=str(name).strip() or "Character")
        for k,v in f.items():
            if k not in CharacterState.__dataclass_fields__ or k in {"id","name"}:raise ValueError(k)
            setattr(c,k,v)
        d=self._load();d["characters"][c.id]=asdict(c);self._save(d);return c
    def get(self,i):
        r=self._load()["characters"].get(i)
        if r is None:raise KeyError(i)
        return CharacterState.from_dict(r)
    def update(self,i,**ch):
        c=self.get(i)
        for k,v in ch.items():
            if k not in CharacterState.__dataclass_fields__ or k=="id":raise ValueError(k)
            setattr(c,k,v)
        d=self._load();d["characters"][c.id]=asdict(c);self._save(d);return c
    def resolve_scene_characters(self,refs):
        out=[]
        for r in refs or []:
            cid=str(r.get("id","")).strip() if isinstance(r,dict) else str(r).strip()
            if cid:
                try:out.append(self.get(cid));continue
                except KeyError:pass
            if isinstance(r,dict) and r.get("name"):out.append(CharacterState(id=cid or "unbound",name=str(r["name"])))
        return out
