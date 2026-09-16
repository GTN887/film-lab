from __future__ import annotations
import json
from dataclasses import asdict, dataclass, field
from typing import Any
@dataclass
class SceneContext:
    scene_id:str; set_id:str=""; location:str=""; time_of_day:str=""; weather:str=""; lighting:str=""
    camera:dict[str,Any]=field(default_factory=dict); characters:list[dict[str,Any]]=field(default_factory=list); objects:list[dict[str,Any]]=field(default_factory=list); blocking:list[dict[str,Any]]=field(default_factory=list)
    continuity_notes:str=""; director_instructions:str=""; prior_take_ids:list[str]=field(default_factory=list); metadata:dict[str,Any]=field(default_factory=dict)
    @classmethod
    def from_dict(cls,raw):
        d=dict(raw or {}); return cls(**{k:d[k] for k in cls.__dataclass_fields__ if k in d})
    def prompt_context(self):
        p=[]
        for label,value in (("Location",self.location),("Time",self.time_of_day),("Weather",self.weather),("Lighting",self.lighting)):
            if value:p.append(f"{label}: {value}")
        if self.characters:p.append("Characters: "+", ".join(str(x.get("name") or x.get("id") or "character") for x in self.characters))
        if self.objects:p.append("Objects: "+json.dumps(self.objects,ensure_ascii=False))
        if self.blocking:p.append("Blocking: "+json.dumps(self.blocking,ensure_ascii=False))
        if self.camera:p.append("Camera: "+json.dumps(self.camera,ensure_ascii=False))
        if self.continuity_notes:p.append(f"Continuity: {self.continuity_notes}")
        if self.director_instructions:p.append(f"Director: {self.director_instructions}")
        return ". ".join(p)
class SceneContextStore:
    def __init__(self,project): self.project=project; project.ensure_dirs(); self.path=project.root/"scene_world.json"
    def _load(self):
        if not self.path.exists():return {"version":1,"scenes":{}}
        try:r=json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError):return {"version":1,"scenes":{}}
        r.setdefault("version",1);r.setdefault("scenes",{});return r
    def _save(self,d):
        t=self.path.with_suffix(".json.tmp");t.write_text(json.dumps(d,indent=2,sort_keys=True)+"\n",encoding="utf-8");t.replace(self.path)
    def get(self,s):
        r=self._load()["scenes"].get(s);return SceneContext.from_dict(r) if r else SceneContext(scene_id=s)
    def save(self,c):
        d=self._load();d["scenes"][c.scene_id]=asdict(c);self._save(d);return c
    def update(self,s,**changes):
        c=self.get(s)
        for k,v in changes.items():
            if k not in SceneContext.__dataclass_fields__ or k=="scene_id":raise ValueError(f"Unknown Scene World field: {k}")
            setattr(c,k,v)
        return self.save(c)
def resolved_character_context(project,scene_id):
    from film_lab.character_state import CharacterStore
    return CharacterStore(project).resolve_scene_characters(SceneContextStore(project).get(scene_id).characters)
def generation_prompt(project,scene_id,shot_prompt):
    w=SceneContextStore(project).get(scene_id).prompt_context(); cs=resolved_character_context(project,scene_id); ct=". ".join(c.prompt_context() for c in cs); s=(shot_prompt or "").strip(); return ". ".join(x for x in (w,ct,f"Shot direction: {s}" if s else "") if x)
